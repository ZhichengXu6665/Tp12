import dash_leaflet as dl
import dash_bootstrap_components as dbc
from dash import dcc, html, Dash, Output, Input, State, no_update
import pandas as pd
import json
import networkx as nx
from geopy.geocoders import GoogleV3

# Initialize the Google Geocoding API
geolocator = GoogleV3(api_key='AIzaSyCnbw-OeDr5P5qsEtokjbX1QwCJulnFkgE')  # Replace with your API key

# Create a directed graph for route calculation
G = nx.DiGraph()

# Parse the Geo Shape field and generate routes
def parse_geo_shape(geo_shape_str):
    """Parse coordinate data from GeoJSON"""
    try:
        geo_shape = json.loads(geo_shape_str.replace('""', '"'))  # Replace doubled quotes with single quotes for correct parsing
        coordinates = geo_shape['coordinates'][0]
        return coordinates
    except json.JSONDecodeError as e:
        print(f"Error parsing GeoJSON: {e}")
        return []

# Load bicycle route data
routes_df = pd.read_csv('bicycle_routes.csv')

# Initialize graph nodes and edges
def initialize_graph(routes_df):
    for _, row in routes_df.iterrows():
        coordinates = parse_geo_shape(row['Geo Shape'])
        for i in range(len(coordinates) - 1):
            start = tuple(coordinates[i][::-1])  # Reverse to (lat, lon)
            end = tuple(coordinates[i + 1][::-1])
            G.add_edge(start, end, weight=1)  # Adjust weight as needed
            print(f"Added edge from {start} to {end}")

# Initialize the graph with actual data
initialize_graph(routes_df)

# Define some fake data coordinates for testing
fake_coordinates = [
    (-37.8182711, 144.9670618),  # Example coordinate 1 (near Flinders Street Station)
    (-37.8172711, 144.9675618),  # Example coordinate 2
    (-37.8162711, 144.9680618),  # Example coordinate 3
    (-37.8152711, 144.9685618),  # Example coordinate 4
    (-37.8142711, 144.9690618),  # Example coordinate 5
    (-37.8132711, 144.9695618),  # Example coordinate 6
    (-37.8123652, 144.9623382)   # Example coordinate 7 (near Melbourne Central)
]

# Add these fake coordinates to the graph
for i in range(len(fake_coordinates) - 1):
    start = fake_coordinates[i]
    end = fake_coordinates[i + 1]
    G.add_edge(start, end, weight=1)  # Add edge to the graph
    print(f"Added fake edge from {start} to {end}")

def generate_bike_routes(routes_df, route_type=None):
    """Generate map layers for specified route types"""
    layers = []
    for _, row in routes_df.iterrows():
        if route_type and row['name'] != route_type:
            continue  # Only display specified route types
        coordinates = parse_geo_shape(row['Geo Shape'])
        polyline = dl.Polyline(
            positions=[[lat, lon] for lon, lat in coordinates],  # Swap latitude and longitude order
            color='green' if row['name'] == 'On-Road Bike Lane' else 'blue',
            weight=3,
            children=[
                dl.Tooltip(f"{row['name']} - {row['direction']}"),
                dl.Popup(f"{row['name']}, Status: {row['status']}")
            ]
        )
        layers.append(polyline)
    return layers

def calculate_shortest_path(start, end):
    """Calculate shortest path using coordinates"""
    try:
        print(f"Calculating path from {start} to {end}")
        path = nx.shortest_path(G, source=start, target=end, weight='weight')
        print(f"Path found: {path}")
        return path
    except nx.NetworkXNoPath:
        print(f"No path exists between {start} and {end}")
        return None
    except nx.NodeNotFound as e:
        print(f"Node not found: {e}")
        return None

def geocode_address(address):
    """Convert an address to coordinates using Google Geocoding API"""
    try:
        location = geolocator.geocode(address)
        if location:
            print(f"Geocoded Address: {address}, Coordinates: ({location.latitude}, {location.longitude})")
            return (location.latitude, location.longitude)
        else:
            print(f"Address: {address} could not be geocoded.")
    except Exception as e:
        print(f"Error geocoding address {address}: {e}")
    return None

def create_map_page():
    """Generate the map page layout"""
    return html.Div([
        html.H1('Melbourne Cycling Map'),
        dcc.Input(
            id='start-address',
            type='text',
            placeholder='Enter start address',
            value='',  # Initialize with an empty string to make it controlled
            style={'marginRight': '10px'}
        ),
        dcc.Input(
            id='end-address',
            type='text',
            placeholder='Enter end address',
            value='',  # Initialize with an empty string to make it controlled
        ),
        html.Button('Find Route', id='find-route-btn', n_clicks=0, style={'marginLeft': '10px'}),
        html.Button('Show Green Paths', id='show-green-btn', n_clicks=0, style={'marginLeft': '10px'}),
        html.Button('Show Blue Paths', id='show-blue-btn', n_clicks=0, style={'marginLeft': '10px'}),
        dl.Map(id='map', children=[
            dl.TileLayer(),
            *generate_bike_routes(routes_df),  # Display all routes by default
        ], style={'width': '100%', 'height': '600px'}, center=(-37.8136, 144.9631), zoom=13),
        html.Div(id='route-info', style={'marginTop': '20px'})
    ])

# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = create_map_page()

# Define callback for route finding
@app.callback(
    Output('map', 'children', allow_duplicate=True),
    Output('route-info', 'children'),
    Input('find-route-btn', 'n_clicks'),
    State('start-address', 'value'),
    State('end-address', 'value'),
    prevent_initial_call='initial_duplicate'
)
def update_map(n_clicks, start_address, end_address):
    if n_clicks > 0:
        print(f"Start Address: {start_address}, End Address: {end_address}")
        
        start_coords = geocode_address(start_address)
        end_coords = geocode_address(end_address)
        
        # Manually add start and end coordinates to the graph to ensure they exist
        if start_coords not in G:
            G.add_node(start_coords)
            # Create an edge from start_coords to the first fake coordinate
            G.add_edge(start_coords, fake_coordinates[0], weight=1)
            print(f"Manually added start node {start_coords} and edge to graph.")
            
        if end_coords not in G:
            G.add_node(end_coords)
            # Create an edge from the last fake coordinate to end_coords
            G.add_edge(fake_coordinates[-1], end_coords, weight=1)
            print(f"Manually added end node {end_coords} and edge to graph.")
        
        if start_coords and end_coords:
            print(f"Start Coordinates: {start_coords}, End Coordinates: {end_coords}")
            
            # Validate node existence in graph
            if validate_nodes_in_graph(start_coords, end_coords):
                path = calculate_shortest_path(start_coords, end_coords)
                if path:
                    path_coordinates = [[lat, lon] for lat, lon in path]
                    polyline = dl.Polyline(
                        positions=path_coordinates,
                        color='red',
                        weight=5,
                        children=[dl.Tooltip(f"Path from {start_address} to {end_address}")]
                    )
                    route_info = f"Shortest path from {start_address} to {end_address}: {path}"
                    
                    return [dl.TileLayer(), *generate_bike_routes(routes_df), polyline], route_info
                else:
                    print("No path found.")
                    return no_update, f"No path found from {start_address} to {end_address}. Please check the addresses."
            else:
                print(f"Start or end node not in graph: {start_coords}, {end_coords}")
                return no_update, f"No path found from {start_address} to {end_address}. Please check the addresses."
        else:
            print("Invalid coordinates for addresses.")
            return no_update, f"Invalid address(es) entered. Please try again: {start_address}, {end_address}"
    
    return no_update, ""

def validate_nodes_in_graph(start, end):
    """Validate if the nodes exist in the graph"""
    start_node_exists = start in G.nodes
    end_node_exists = end in G.nodes
    if not start_node_exists:
        print(f"Start node {start} not found in graph.")
    if not end_node_exists:
        print(f"End node {end} not found in graph.")
    return start_node_exists and end_node_exists

if __name__ == '__main__':
    app.run_server(debug=True)
