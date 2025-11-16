import dash
from dash import html, dcc, callback, Input, Output, dash_table, State, ALL
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import logging
from dashboard_app import app

logger = logging.getLogger(__name__)

def layout():
    """Layout de la página de Inteligencia de Precios."""
    return dmc.Container(
        [
            dmc.Title("Análisis de Precios y Oportunidades", order=2, className="mb-4"),
            dmc.Text(
                "Esta sección utiliza un modelo de Machine Learning para predecir precios y detectar anomalías.",
                size="md", className="mb-5"
            ),
            
            dmc.Grid(
                gutter="xl",
                children=[
                    dmc.GridCol(
                        dbc.Card(
                            dbc.CardBody([
                                html.H4("Tabla de Predicciones por Producto", className="card-title"),
                                dash_table.DataTable(
                                    id='predictions-table',
                                    page_size=20,
                                    style_table={'overflowX': 'auto'},
                                    style_cell={'textAlign': 'left', 'padding': '5px', 'whiteSpace': 'normal', 'height': 'auto'},
                                    style_header={'fontWeight': 'bold'},
                                    filter_action='native',
                                    sort_action='native',
                                    sort_mode='multi'
                                )
                            ])
                        ),
                        span=6
                    ),
                    
                    dmc.GridCol(
                        [
                            dbc.Card(
                                dbc.CardBody(dcc.Graph(id='overvalued-products-chart')),
                                className="mb-4"
                            ),
                            dbc.Card(
                                dbc.CardBody(dcc.Graph(id='undervalued-products-chart'))
                            ),
                        ],
                        span=6
                    ),
                ],
            ),
            dmc.Space(h=40),
            
            dbc.Card(
                dbc.CardBody([
                    html.H4("Simulador de Precio Óptimo", className="card-title mb-4"),
                    dmc.Text(
                        "Ingrese las características del producto para obtener una predicción del precio óptimo.",
                        className="mb-4"
                    ),
                    dmc.NumberInput(
                        id='real-price-input',
                        label="Ingrese su Precio de Venta Actual ($)",
                        description="Este precio se usará para calcular las diferencias.",
                        value=100.00,
                        decimalScale=2,
                        min=0,
                        step=1,
                        style={"width": "300px"},
                        className="mb-4",
                        leftSection=DashIconify(icon="tabler:cash")
                    ),
                    
                    dmc.Divider(label="Características del Modelo", labelPosition="center", className="mb-4"),
                    dmc.SimpleGrid(
                        id='prediction-inputs-container',
                        cols=3,
                        spacing="lg",
                        verticalSpacing="lg"
                    ),
                    dmc.Button(
                        "Predecir Precio",
                        id='predict-button',
                        variant="gradient",
                        gradient={"from": "teal", "to": "blue"},
                        className="mt-4"
                    ),
                    dmc.Modal(
                        id="modal-simple",
                        title="",
                        zIndex=10000,
                        children=[
                            html.Div(id="modal-prediction-content"),
                        ],
                    )
                ])
            )
        ],
        fluid=True,
        className="mt-4"
    )

@callback(
    [Output('overvalued-products-chart', 'figure'),
     Output('undervalued-products-chart', 'figure'),
     Output('predictions-table', 'data'),
     Output('predictions-table', 'columns')],
    Input('url', 'pathname')
)
def update_price_intelligence_page(pathname):
    """Callback para actualizar los gráficos y la tabla de predicciones en la página de Inteligencia de Precios."""
    if pathname != '/price-intelligence':
        return dash.no_update

    central_analyzer = app.server.config.get('CENTRAL_ANALYZER')
    if not central_analyzer or central_analyzer.products_df is None:
        return [go.Figure(layout={'title': 'Datos no disponibles'}) for _ in range(2)] + [[], []]

    df = central_analyzer.get_price_intelligence_data()

    if df.empty:
        return [go.Figure(layout={'title': 'Datos no disponibles'}) for _ in range(2)] + [[], []]

    sobrevalorados = df.nlargest(10, 'diferencia_precio_vs_sugerido')
    subvalorados = df.nsmallest(10, 'diferencia_precio_vs_sugerido')

    fig_over = px.bar(sobrevalorados, x='diferencia_precio_vs_sugerido', y='name', orientation='h',
                      title='Top 10 Productos Sobrevalorados',
                      labels={'diferencia_precio_vs_sugerido': 'Diferencia ($)', 'name': 'Producto'},
                      color='diferencia_precio_vs_sugerido', color_continuous_scale=px.colors.sequential.Reds,
                      hover_name='name',
                      custom_data=['precio_promedio_real', 'precio_promedio_sugerido'])
    fig_over.update_layout(yaxis={'categoryorder':'total ascending'})
    fig_over.update_traces(hovertemplate="<b>%{hovertext}</b><br>Diferencia: $%{x:.2f}<br>Precio Real: $%{customdata[0]:.2f}<br>Precio Predicho: $%{customdata[1]:.2f}")


    fig_under = px.bar(subvalorados, x='diferencia_precio_vs_sugerido', y='name', orientation='h',
                       title='Top 10 Productos Infravalorados',
                       labels={'diferencia_precio_vs_sugerido': 'Diferencia ($)', 'name': 'Producto'},
                       color='diferencia_precio_vs_sugerido', color_continuous_scale=px.colors.sequential.Blues_r,
                       hover_name='name',
                       custom_data=['precio_promedio_real', 'precio_promedio_sugerido'])
    fig_under.update_layout(yaxis={'categoryorder':'total descending'})
    fig_under.update_traces(hovertemplate="<b>%{hovertext}</b><br>Diferencia: $%{x:.2f}<br>Precio Real: $%{customdata[0]:.2f}<br>Precio Predicho: $%{customdata[1]:.2f}")

    competitor_cols = ['precio_competencia_1', 'precio_competencia_2', 'precio_competencia_3']
    df_table = df.copy()
    
    def format_price(price):
        if pd.isna(price) or price == 0:
            return "Sin datos"
        return f"${price:,.2f}"

    cols_to_format = ['precio_promedio_real', 'precio_promedio_sugerido'] + competitor_cols
    for col in cols_to_format:
        if col in df_table.columns:
            df_table[col] = df_table[col].apply(format_price)

    cols_to_show = [
        'name', 
        'precio_promedio_real', 
        'precio_promedio_sugerido',
    ] + competitor_cols
    
    final_cols = [col for col in cols_to_show if col in df_table.columns]
    df_table_final = df_table[final_cols]
    
    table_data = df_table_final.to_dict('records')
    
    column_map = {
        'name': 'Nombre Producto',
        'precio_promedio_real': 'Precio Actual ($)',
        'precio_promedio_sugerido': 'Precio Óptimo Sugerido ($)',
        'precio_competencia_1': 'Competidor 1 ($)',
        'precio_competencia_2': 'Competidor 2 ($)',
        'precio_competencia_3': 'Competidor 3 ($)',
    }
    table_columns = [{"name": column_map.get(i, i), "id": i} for i in final_cols]
    
    return fig_over, fig_under, table_data, table_columns

@callback(
    Output('prediction-inputs-container', 'children'),
    Input('url', 'pathname')
)
def generate_prediction_inputs(pathname):
    """Callback para generar dinámicamente los campos de entrada basados en las características del modelo."""
    if pathname != '/price-intelligence':
        return dash.no_update

    central_analyzer = app.server.config.get('CENTRAL_ANALYZER')
    if not central_analyzer or not central_analyzer.feature_names_for_model:
        return dmc.Alert("El modelo de predicción no está cargado. No se pueden generar los campos de entrada.", color="orange")
    feature_dict_map = {
        'comp1_diff': 'Precio Competidor 1 ($)',
        'comp2_diff': 'Precio Competidor 2 ($)',
        'comp3_diff': 'Precio Competidor 3 ($)',}
    feature_names = central_analyzer.feature_names_for_model
    
    inputs = [
        dmc.NumberInput(
            id={'type': 'dynamic-input', 'index': feature},
            label=feature_dict_map.get(feature, feature.replace('_', ' ').title()),
            value=0,
            decimalScale=2,
            min=0,
            step=0.01,
            style={"width": "100%"}
        ) for feature in feature_names
    ]
    
    return inputs


@callback(
    [Output('modal-simple', 'opened'),
     Output('modal-simple', 'title'),
     Output('modal-prediction-content', 'children')],
    Input('predict-button', 'n_clicks'),
    [
        State('real-price-input', 'value'),
        State({'type': 'dynamic-input', 'index': ALL}, 'value'),
        State({'type': 'dynamic-input', 'index': ALL}, 'id')
    ],
    prevent_initial_call=True
)
def run_prediction(n_clicks, real_price, feature_values, feature_ids):
    """Callback para ejecutar la predicción de precio óptimo y mostrar el resultado en un modal."""
    central_analyzer = app.server.config.get('CENTRAL_ANALYZER')

    if not central_analyzer or not central_analyzer.model:
        alert = dmc.Alert("Error: El modelo no está cargado.", color="red", title="Error de Predicción")
        return True, "Error de Predicción", alert

    if real_price is None or real_price <= 0:
        alert = dmc.Alert("Por favor, ingrese un 'Precio de Venta Actual' válido y mayor a cero.", color="yellow", title="Datos Incompletos")
        return True, "Datos Incompletos", alert

    if any(value is None for value in feature_values):
        alert = dmc.Alert("Por favor, ingrese un valor para todas las características del modelo.", color="yellow", title="Datos Incompletos")
        return True, "Datos Incompletos", alert
    
    try:
        feature_names = [item['index'] for item in feature_ids]
        input_features = {name: value for name, value in zip(feature_names, feature_values)}
        
        predicted_price, error = central_analyzer.predict_price(input_features, real_price)
        
        if error:
            alert = dmc.Alert(f"Error de predicción: {error}", color="red", title="Error")
            return True, "Error", alert

        def create_comparison_item(title, value, difference, positive_is_good=True):
            if difference > 0:
                color = "green" if positive_is_good else "red"
                icon = "tabler:arrow-up"
                text = f"por ${abs(difference):.2f}"
            elif difference < 0:
                color = "red" if positive_is_good else "green"
                icon = "tabler:arrow-down"
                text = f"por ${abs(difference):.2f}"
            else:
                color = "gray"
                icon = "tabler:arrows-right-left"
                text = "igual"
            
            return dmc.ListItem(
                dmc.Group([
                    dmc.Text(f"{title}: ${value:.2f}", fw=500),
                    dmc.Badge(text, color=color, variant="light", leftSection=DashIconify(icon=icon))
                ]),
                icon=dmc.ThemeIcon(DashIconify(icon="tabler:point-filled"), size=16)
            )

        items = []
        diff_vs_optimal = real_price - predicted_price
        items.append(create_comparison_item("Precio Óptimo Sugerido", predicted_price, diff_vs_optimal, positive_is_good=False))
        
        for i in range(1, 4):
            competitor_key = f'precio_competidor_{i}'
            if competitor_key in input_features and input_features[competitor_key] > 0:
                comp_price = input_features[competitor_key]
                diff_vs_comp = real_price - comp_price
                items.append(create_comparison_item(f"Competidor {i}", comp_price, diff_vs_comp, positive_is_good=False))

        # El componente Alert completo es ahora el contenido del modal
        modal_content = html.Div([
            dmc.Text("El precio óptimo sugerido para este producto es:"),
            dmc.Text(f"${predicted_price:,.2f}", size="xl", fw=700, className="my-2", c="blue"),
            dmc.Divider(className="my-3"),
            dmc.Text("Análisis comparativo con su precio actual:", fw=500, className="mb-2"),
            dmc.List(children=items, spacing="xs")
        ])
        
        modal_title = "Análisis de Predicción Completado"

        return True, modal_title, modal_content

    except Exception as e:
        logger.error(f"Error durante la predicción manual: {e}", exc_info=True)
        alert = dmc.Alert(f"Ocurrió un error al procesar la predicción: {e}", color="red", title="Error Inesperado")
        return True, "Error Inesperado", alert