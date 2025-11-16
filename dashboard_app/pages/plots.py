# Importaciones actualizadas
import dash_mantine_components as dmc
from dash import html, dcc, callback, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def layout():
    """
    Layout de los gráficos usando dmc.Grid para un sistema de columnas robusto.
    """
    return dmc.Container([
        dmc.Grid(
            gutter="xl",
            children=[
                    dmc.GridCol(dcc.Graph(id='price-per-retailer-graph'), span=6),
                    dmc.GridCol(dcc.Graph(id='price-trends-graph'),span=6),
                    
                    dmc.GridCol(dcc.Graph(id='most-expensive-products'),span=6),
                    dmc.GridCol(dcc.Graph(id='cheapest-products'),span=6),
                    dmc.GridCol(
                        dcc.Graph(id='price-distribution-violin-plot'),
                        span=12,)
                ]
        )
    ], fluid=True, className="graphics-container mt-4") 


@callback(
    Output('price-per-retailer-graph', 'figure'),
    Input('store-filtered-data', 'data'),
)
def update_price_per_retailer_graph(filtered_data_json):
    """
    Callback para actualizar el gráfico de precios (minimo, maximo y promedio) por retailer.
    Args: 
        filtered_data_json (list): Datos filtrados en formato JSON.
    Returns:
        fig (plotly.graph_objs._figure.Figure): Gráfico de barras actualizado.
    """
    layout_updates = {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'legend_title_text': 'Métricas de Precio'
    }

    if not filtered_data_json:
        fig = px.bar(title="Precios por Retailer (Sin datos)")
        fig.update_layout(**layout_updates)
        return fig

    df = pd.DataFrame(filtered_data_json)
    if df.empty or 'price' not in df.columns or 'website_table_name' not in df.columns:
        fig = px.bar(title="Precios por Retailer (Datos insuficientes)")
        fig.update_layout(**layout_updates)
        return fig

    df_agg = df.groupby('website_table_name')['price'].agg(['mean', 'min', 'max']).reset_index()
    df_agg.columns = ['Retailer', 'Precio Promedio', 'Precio Mínimo', 'Precio Máximo']

    color_map = {
        'Precio Promedio': '#636EFA', 'Precio Mínimo': '#00CC96', 'Precio Máximo': '#EF553B'
    }

    fig = px.bar(df_agg, x='Retailer', y=['Precio Promedio', 'Precio Mínimo', 'Precio Máximo'],
                 title="Precios por Retailer (Promedio, Mínimo y Máximo)",
                 labels={'value': 'Precio', 'variable': 'Métrica'},
                 barmode='group',
                 color_discrete_map=color_map)
    
    fig.update_layout(**layout_updates)
    return fig

@callback(
    Output('price-trends-graph', 'figure'),
    Input('store-filtered-data', 'data'),
)
def update_price_trends_graph(filtered_data_json):
    """
    Callback para actualizar el gráfico de tendencias de precios a lo largo del tiempo.
    Args:
        filtered_data_json (list): Datos filtrados en formato JSON.
    Returns:
        fig (plotly.graph_objs._figure.Figure): Gráfico de líneas actualizado.
    """
    layout_updates = {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'legend_title_text': 'Métricas de Precio'
    }

    if not filtered_data_json:
        fig = px.line(title="Historico de Precios (Sin datos)")
        fig.update_layout(**layout_updates)
        return fig

    df = pd.DataFrame(filtered_data_json)
    if df.empty or 'price' not in df.columns or 'scrape_timestamp' not in df.columns:
        fig = px.line(title="Historico de Precios (Datos insuficientes)")
        fig.update_layout(**layout_updates)
        return fig

    df['scrape_timestamp'] = pd.to_datetime(df['scrape_timestamp'])
    df_trend = df.groupby(df['scrape_timestamp'].dt.date)['price'].agg(['mean', 'min', 'max']).reset_index()
    df_trend.columns = ['Fecha', 'Precio Promedio', 'Precio Mínimo', 'Precio Máximo']

    color_map = {
        'Precio Promedio': '#636EFA', 'Precio Mínimo': '#00CC96', 'Precio Máximo': '#EF553B'
    }

    fig = px.line(df_trend, x='Fecha', y=['Precio Promedio', 'Precio Mínimo', 'Precio Máximo'],
                  title="Historico de Precios (Promedio, Mínimo y Máximo)",
                  labels={'value': 'Precio', 'variable': 'Métrica'},
                  markers=True,
                  color_discrete_map=color_map)
                  
    fig.update_layout(**layout_updates)
    return fig

@callback(
    Output('most-expensive-products', 'figure'),
    Input('store-filtered-data', 'data'),
)
def update_most_expensive_products(filtered_data_json):
    """
    Callback para actualizar el gráfico de los productos más caros.
    Args:
        filtered_data_json (list): Datos filtrados en formato JSON.
    Returns:
        fig (plotly.graph_objs._figure.Figure): Gráfico de barras actualizado.
    """
    layout_updates = {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'yaxis': {'categoryorder': 'total ascending'}
    }

    if not filtered_data_json:
        fig = px.bar(title="Productos Más Caros (Sin datos)")
        fig.update_layout(**layout_updates)
        return fig
    
    df = pd.DataFrame(filtered_data_json)
    if df.empty or 'price' not in df.columns or 'name' not in df.columns:
        fig = px.bar(title="Productos Más Caros (Datos insuficientes)")
        fig.update_layout(**layout_updates)
        return fig
    idx_of_max_price = df.groupby(['name','website_table_name'])['price'].idxmax()
    
    top_expensive = df.loc[idx_of_max_price]
    top_expensive = top_expensive.nlargest(10, 'price')
    fig = px.bar(top_expensive, x='price', y='name', orientation='h',
                 title='Productos Más Caros',
                 labels={'price': 'Precio', 'name': 'Producto'},
                 color='price')
    
    fig.update_layout(**layout_updates)
    fig.update_traces(customdata=top_expensive[['website_table_name']],
                      hovertemplate="<b>%{y}</b><br>Precio: $%{x:.2f}<br>Retailer: %{customdata[0]}")
    return fig

@callback(
    Output('cheapest-products', 'figure'),
    Input('store-filtered-data', 'data'),
)
def update_cheapest_products(filtered_data_json):
    """
    Callback para actualizar el gráfico de los productos más baratos.
    Args:
        filtered_data_json (list): Datos filtrados en formato JSON.
    Returns:
        fig (plotly.graph_objs._figure.Figure): Gráfico de barras actualizado.
    """
    layout_updates = {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'yaxis': {'categoryorder': 'total ascending'}
    }

    if not filtered_data_json:
        fig = px.bar(title="Productos Más Baratos (Sin datos)")
        fig.update_layout(**layout_updates)
        return fig
    
    df = pd.DataFrame(filtered_data_json)
    if df.empty or 'price' not in df.columns or 'name' not in df.columns:
        fig = px.bar(title="Productos Más Baratos (Datos insuficientes)")
        fig.update_layout(**layout_updates)
        return fig
    
    valid_prices = df[df['price'] > 0]
    if valid_prices.empty:
        fig = px.bar(title="Productos Más Baratos (No hay precios válidos)")
        fig.update_layout(**layout_updates)
        return fig
    idx_of_max_price = valid_prices.groupby(['name','website_table_name'])['price'].idxmin()
    
    top_cheapest = valid_prices.loc[idx_of_max_price]
    top_cheapest = top_cheapest.nsmallest(10, 'price')
    fig = px.bar(top_cheapest, x='price', y='name', orientation='h',
                 title='Productos Más Baratos',
                 labels={'price': 'Precio', 'name': 'Producto'},
                 color='price')
    
    fig.update_layout(**layout_updates)
    fig.update_traces(customdata=top_cheapest[['website_table_name']],
                      hovertemplate="<b>%{y}</b><br>Precio: $%{x:.2f}<br>Retailer: %{customdata[0]}")
    return fig

@callback(
    Output('price-distribution-violin-plot', 'figure'),
    Input('store-filtered-data', 'data')
)
def update_price_distribution_plot(data):
    """
    Callback para actualizar el gráfico de violin.
    Args:
        filtered_data_json (list): Datos filtrados en formato JSON.
    Returns:
        fig (plotly.graph_objs._figure.Figure): Gráfico de barras actualizado.
    """
    if not data:
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[{
                "text": "Filtra datos para ver la distribución de precios.",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 16}
            }],
        )
        return fig

    df = pd.DataFrame(data)

    if df.empty or 'price' not in df.columns or 'website_table_name' not in df.columns:
        return go.Figure().update_layout(title_text="Datos insuficientes para generar el gráfico")

    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df.dropna(subset=['price', 'website_table_name'], inplace=True)
    fig = px.violin(
        df,
        x='website_table_name',
        y='price',
        color='website_table_name', 
        box=True,
        points=False,
        title="Distribución de Precios por Retailer",
        labels={
            "price": "Precio (Moneda)",
            "website_table_name": "Retailer"
        }
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(l=40, r=40, t=60, b=40),
        title_x=0.5
    )
    
    return fig