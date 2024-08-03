import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import dash_leaflet as dl
import dash_bootstrap_components as dbc
import pandas as pd
import json
import networkx as nx

# Create a Dash application and add Bootstrap styling
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Load bicycle route data
routes_df = pd.read_csv('bicycle_routes.csv')

# Create a directed graph for route calculation
G = nx.DiGraph()

# Initialize graph nodes and edges
def initialize_graph(routes_df):
    for _, row in routes_df.iterrows():
        coordinates = parse_geo_shape(row['Geo Shape'])
        for i in range(len(coordinates) - 1):
            start = tuple(coordinates[i][::-1])  # Reverse to (lat, lon)
            end = tuple(coordinates[i+1][::-1])
            G.add_edge(start, end, weight=1)  # Adjust weight as needed

# Parse the Geo Shape field and generate routes
def parse_geo_shape(geo_shape_str):
    """Parse coordinate data from GeoJSON"""
    geo_shape = json.loads(geo_shape_str.replace("'", '"'))  # Replace single quotes with double quotes for correct parsing
    return geo_shape['coordinates'][0]  # Get the first coordinate sequence (assumed to be route coordinates)

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

# Calculate shortest path
def calculate_shortest_path(start, end):
    try:
        # Use Dijkstra's algorithm to calculate the shortest path
        path = nx.shortest_path(G, source=start, target=end, weight='weight')
        return path
    except nx.NetworkXNoPath:
        return None

# Initialize the graph
initialize_graph(routes_df)

# Application layout
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("Melbourne Cycling Navigation", className="ms-2"),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink("Home", href="/", active="exact")),
                        dbc.NavItem(dbc.NavLink("Map", href="/map", active="exact")),
                    ],
                    className="ms-auto",
                    navbar=True,
                ),
                id="navbar-collapse",
                navbar=True,
            ),
        ]),
        color="light",
        dark=False,
        className="mb-4"
    ),
    html.Div(id='page-content'),
    html.Div([
        html.P("© 2024 Melbourne Cycling Initiative"),
        html.P("Follow us on social media!"),
        html.P("Contact us at info@melbcycling.org")
    ], className='footer')
], fluid=True)

@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/map':
        return html.Div([
            html.H1('Melbourne Cycling Map'),
            dcc.Input(id='start-point', type='text', placeholder='Enter start coordinates', style={'marginRight': '10px'}),
            dcc.Input(id='end-point', type='text', placeholder='Enter end coordinates'),
            html.Button('Find Route', id='find-route-btn', n_clicks=0, style={'marginLeft': '10px'}),
            html.Button('Show Green Paths', id='show-green-btn', n_clicks=0, style={'marginLeft': '10px'}),
            html.Button('Show Blue Paths', id='show-blue-btn', n_clicks=0, style={'marginLeft': '10px'}),
            dl.Map(id='map', children=[
                dl.TileLayer(),
                *generate_bike_routes(routes_df),  # Display all routes by default
            ], style={'width': '100%', 'height': '600px'}, center=(-37.8136, 144.9631), zoom=13),
            html.Div(id='route-info', style={'marginTop': '20px'})
        ])
    else:
        # Handle '/' and other undefined paths with a default page
        return html.Div(className="content", children=[
            html.Div(className="text-section", children=[
                html.H1('WiseCycle'),
                html.P('Designed to improve bicycle safety and navigation for cyclists in Melbourne.')
            ]),
            html.Div(className="image-section", children=[
                html.Img(src='assets/bike1.webp', style={'max-width': '100%', 'height': 'auto'})
            ])
        ])

# Handle path finding
@app.callback(
    Output('map', 'children', allow_duplicate=True),
    Output('route-info', 'children'),
    Input('find-route-btn', 'n_clicks'),
    State('start-point', 'value'),
    State('end-point', 'value'),
    prevent_initial_call=True
)
def update_route(n_clicks, start_value, end_value):
    if n_clicks > 0:
        try:
            # Convert user-input start and end points to coordinates
            start_coords = tuple(map(float, start_value.split(',')))
            end_coords = tuple(map(float, end_value.split(',')))
            # Calculate the shortest path
            path = calculate_shortest_path(start_coords, end_coords)
            if path:
                # Display the path on the map
                path_layer = dl.Polyline(positions=path, color='red', weight=4)
                return [dl.TileLayer(), *generate_bike_routes(routes_df), path_layer], f"Found route from {start_coords} to {end_coords}"
            else:
                return dash.no_update, "No path found between the specified points."
        except Exception as e:
            return dash.no_update, f"Error: {str(e)}"
    return dash.no_update, ""

# Handle toggling path display buttons callback
@app.callback(
    Output('map', 'children', allow_duplicate=True),
    [Input('show-green-btn', 'n_clicks'),
     Input('show-blue-btn', 'n_clicks')],
    prevent_initial_call='initial_duplicate'
)
def toggle_paths(green_clicks, blue_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == 'show-green-btn':
        return [dl.TileLayer(), *generate_bike_routes(routes_df, route_type='On-Road Bike Lane')]
    elif button_id == 'show-blue-btn':
        return [dl.TileLayer(), *generate_bike_routes(routes_df, route_type='Off-Road Bike Route')]
    return dash.no_update

# Callback for navbar toggle (for mobile devices)
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")]
)
def toggle_navbar(n, is_open):
    if n:
        return not is_open
    return is_open

# Run the application
if __name__ == '__main__':
    app.run_server(debug=True)
