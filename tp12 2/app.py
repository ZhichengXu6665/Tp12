import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from map import create_map_page
# 创建 Dash 应用并添加 Bootstrap 样式
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# 图像文件名
right_image_filename = '/assets/picture1.jpeg'  # 第一项的现有图像
new_image_1 = '/assets/map1.png'  # 新功能的图像
new_image_2 = '/assets/bike3.png'
mission_image = '/assets/bike2.jpg'  # 任务图片

# 应用布局
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("WiseCycle", className="ms-2"),
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
    html.Div(id='page-content')
], fluid=True)

@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/choropleth':
        # 确保此路径指向你的index2.html页面
        return html.Iframe(src="http://localhost:8001/index2.html", style={"height": "100vh", "width": "100%"})
    elif pathname == '/map':
        # 这里需要调用map.py中的create_map_page函数，假设该函数存在
        
        return create_map_page()
    else:
        return dbc.Container([
            dbc.Row([
                dbc.Col(html.Div([
                    html.H1('Navigate Melbourne Safely with WiseCycle', style={'fontSize': '1.5rem', 'textAlign': 'center'}),
                    html.P('Your Ultimate Companion for Safe and Efficient Cycling Routes', style={'fontSize': '1rem', 'textAlign': 'center'}),
                    dbc.Button("Plan Your Route", color="success", href="/map", className="button", style={'fontSize': '0.8rem', 'borderRadius': '20px', 'padding': '4px 8px'})
                ], style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center', 'height': '100%', 'marginRight': '10%'}), width=6, className="d-flex align-items-center"),
                dbc.Col(html.Img(src=right_image_filename, style={'width': '100%', 'height': 'auto'}), width=6)
            ], style={'marginBottom': '50px'}),  # 调整行间距
            dbc.Row([
                dbc.Col(html.Div([
                    html.H2('OUR MISSION', style={'fontSize': '1.5rem', 'textAlign': 'center'}),
                    html.P('Save the environment by cycling safely with WiseCycle', style={'fontSize': '1rem', 'textAlign': 'center'}),
                    html.Img(
                        src=mission_image, 
                        style={
                            'width': '100%',  # 防止宽度超过容器
                            'height': '200px',  # 设定高度为固定值，或根据需要调整
                            'objectFit': 'cover',  # 保持宽高比
                            'display': 'block', 
                            'margin': '0 auto'  # 水平居中
                        }
                    )
                ]))
            ], style={'marginBottom': '50px', 'textAlign': 'center'}),  # 新增的内容
            dbc.Row([
                dbc.Col(html.Img(src=new_image_1, style={'width': '100%', 'height': 'auto'}), width=6),
                dbc.Col(html.Div([
                    html.H1('Geospatial Accident Mapping', style={'fontSize': '1.5rem', 'textAlign': 'center'}),
                    html.P('Avoid high-risk areas with our detailed accident mapping. See where accidents are most frequent and plan your routes to stay safe.', style={'fontSize': '1rem', 'textAlign': 'center'}),
                    dbc.Button("Get Started", color="primary", href="/choropleth", className="button", style={'fontSize': '0.8rem', 'borderRadius': '20px', 'padding': '4px 8px'})
                ], style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center', 'alignItems': 'center', 'height': '100%', 'marginLeft': '10%'}), width=6, className="d-flex align-items-center")
            ], style={'marginBottom': '30px'}),
            dbc.Row([
                dbc.Col(html.Div([
                    html.H1('Route Planning and Optimization', style={'fontSize': '1.5rem', 'textAlign': 'center'}),
                    html.P('Plan the safest and most efficient routes with our easy-to-use route planner', style={'fontSize': '1rem', 'textAlign': 'center'}),
                ], style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center', 'alignItems': 'center', 'height': '100%'}), width=6, className="d-flex align-items-center"),
                dbc.Col(html.Img(src=new_image_2, style={'width': '100%', 'height': 'auto'}), width=6)
            ])
        ])

# Navbar的回调函数（用于移动设备）
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")]
)
def toggle_navbar(n, is_open):
    if n:
        return not is_open
    return is_open

# 运行应用程序
if __name__ == '__main__':
    app.run_server(debug=True)
