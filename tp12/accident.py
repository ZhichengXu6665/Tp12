import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import json

# 读取事故数据
data_path = 'bar_chart/accident_severity.json'
with open(data_path, 'r') as file:
    accident_data = json.load(file)

# 将 JSON 数据转换为 Pandas DataFrame
df = pd.DataFrame(accident_data)

# 读取 GeoJSON 文件
geojson_path = 'map/accident_lga.geojson'
with open(geojson_path, 'r') as f:
    geojson_data = json.load(f)

# 数据预处理：按地区和严重性聚合事故数量
agg_data = df.groupby(['LGA_NAME', 'SEVERITY'])['ACCIDENT_NO'].sum().reset_index()

# 创建地图和图表
def create_accident_page():
    # 使用 Plotly Express 生成条形图
    bar_fig = px.bar(
        agg_data,
        x='LGA_NAME',
        y='ACCIDENT_NO',
        color='SEVERITY',
        title='Accident Severity by LGA',
        labels={'ACCIDENT_NO': 'Number of Accidents', 'LGA_NAME': 'Local Government Area'},
        barmode='stack'
    )
    
    # 创建 choropleth 地图
    map_fig = px.choropleth_mapbox(
        agg_data,
        geojson=geojson_data,
        locations='LGA_NAME',
        featureidkey='properties.LGA_NAME',  # 这需要与你的 GeoJSON 文件中的属性名称匹配
        color='ACCIDENT_NO',
        mapbox_style='carto-positron',
        zoom=6,
        center={"lat": -37.8136, "lon": 144.9631},  # 设置地图中心，例如墨尔本的坐标
        opacity=0.5,
        title='Geospatial Accident Mapping by LGA',
        hover_name='LGA_NAME',
        hover_data={'ACCIDENT_NO': True, 'SEVERITY': True}
    )

    return html.Div([
        html.H2('Geospatial Accident Mapping'),
        dcc.Graph(figure=bar_fig),  # 插入条形图
        dcc.Graph(figure=map_fig),  # 插入地图
        html.P("This page displays accident severity mapping for various LGAs.")
    ])
