import dash
import dash_leaflet as dl
import dash_bootstrap_components as dbc
from dash import dcc, html, Dash, Output, Input, State, no_update, callback
import googlemaps
import pandas as pd
import polyline
import json
import networkx as nx
from geopy.geocoders import GoogleV3


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

# google client
gmaps = googlemaps.Client(key="AIzaSyCyhpFnBG-cTL87RZ5rfSbKVa6KEFZd8wQ")

# access the google map direction api 
# and decode the polyline
def create_google_direction(origin, destination):
    direction_result = gmaps.directions(
        origin =origin,
        destination = destination,
        mode= "bicycling"
    )
    direction_steps = direction_result[0]['legs'][0]["steps"]
    a = []
    for step in direction_steps:
        l = step['polyline']['points']
        polyline_decoded = polyline.decode(l)
        a = a + polyline_decoded
    return a


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
        #html.Button('Show Green Paths', id='show-green-btn', n_clicks=0, style={'marginLeft': '10px'}),
        #html.Button('Show Blue Paths', id='show-blue-btn', n_clicks=0, style={'marginLeft': '10px'}),
        dl.Map(id='map', children=[
            dl.TileLayer(),
            *generate_bike_routes(routes_df),  # Display all routes by default
        ], style={'width': '100%', 'height': '600px'}, center=(-37.8136, 144.9631), zoom=13),
        html.Div(id='route-info', style={'marginTop': '20px'})
    ])
    

# Define callback for route finding
@callback(
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
        try:
            path = create_google_direction(start_address, end_address)
            if path:
                # Display the path on the map
                path_layer = dl.Polyline(positions=path, color='red', weight=4)
                return [dl.TileLayer(), *generate_bike_routes(routes_df), path_layer], f"Found route from {start_address} to {end_address}"
            else:
                return dash.no_update, "No path found between the specified points."
        except Exception as e:
            return dash.no_update, f"Error: {str(e)}"
    return no_update, ""


if __name__ == '__main__':
    # Initialize the Dash app
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = create_map_page()
    app.run_server(debug=True)

    