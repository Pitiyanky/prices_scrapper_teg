import dash
from dash import html, dcc, callback, Input, Output, State,dash_table
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import logging
import numpy as np
import scipy.stats as stats
from dashboard_app import app
from sklearn.inspection import PartialDependenceDisplay
from scipy.stats import gaussian_kde
from plotly.subplots import make_subplots
import io
import base64

logger = logging.getLogger(__name__)

def layout():
    """Layout de la página de Análisis de Modelo para Analistas de Datos."""
    central_analyzer = app.server.config.get('CENTRAL_ANALYZER')
    product_options = []
    feature_options = []
    if central_analyzer and central_analyzer.products_df is not None:
        df = central_analyzer.products_df
        df_sorted = df.sort_values('name')
        product_options = [{'label': row['name'], 'value': str(row['product_id'])} for index, row in df_sorted.iterrows()]
        if central_analyzer.X_reconstructed is not None:
             feature_options = [{'label': col, 'value': col} for col in central_analyzer.X_reconstructed.columns]
    
    return dmc.Container(
        [
            dmc.Modal(
                id='train-model-modal',
                title=dmc.Title("Re-entrenar Modelo con Nuevos Datos", order=3),
                opened=False,
                zIndex=10000,
                children=[
                    dmc.Text("Suba un archivo CSV con el formato especificado para re-entrenar el modelo de predicción de precios.", className="mb-3"),
                    dcc.Upload(
                        id='upload-training-data-modal', # ID actualizado para el modal
                        children=html.Div(['Arrastre y suelte o ', html.A('Seleccione un Archivo CSV')]),
                        style={
                            'width': '100%', 'height': '60px', 'lineHeight': '60px',
                            'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                            'textAlign': 'center', 'margin': '10px 0'
                        },
                        multiple=False
                    ),
                    dmc.Button(
                        "Iniciar Entrenamiento",
                        id="train-model-button-modal", # ID actualizado para el modal
                        leftSection=DashIconify(icon="tabler:rocket"),
                        variant="filled",
                        disabled=True,
                        className="mt-2",
                        fullWidth=True
                    ),
                    html.Div(id='training-status-output-modal', className="mt-3") # ID actualizado para el modal
                ]
            ),
            dmc.Title("Análisis Profundo del Modelo de Machine Learning", order=2, className="mb-4"),
            dmc.Text(
                "Esta sección ofrece una vista detallada del conjunto de datos, el rendimiento del modelo y su interpretabilidad.",
                size="md", className="mb-5"
            ),
            dbc.Card(dbc.CardBody([
                dmc.Group(
                    [
                        html.H4("Análisis Exploratorio de Datos (EDA)", className="card-title"),

                        dmc.Group(
                            [
                                dmc.Button(
                                    "Descargar Dataset",
                                    id="download-dataset-button",
                                    leftSection=DashIconify(icon="tabler:download"),
                                    variant="light"
                                ),
                                dmc.Button(
                                    "Re-entrenar Modelo",
                                    id="open-train-modal-button",
                                    leftSection=DashIconify(icon="tabler:brain"),
                                    variant="outline"
                                )
                            ],
                            gap="sm"
                        )
                    ],
                    justify="space-between",
                    align="center",
                    className="mb-3"
                ),
                dcc.Download(id="download-analysis-dataset"),
                dmc.Tabs(
                    [
                        dmc.TabsList(
                            [
                                dmc.TabsTab("Descripción del Dataset", value="describe"),
                                dmc.TabsTab("Distribuciones de Variables", value="dist"),
                                dmc.TabsTab("Matriz de Correlación", value="corr"),
                            ]
                        ),
                        dmc.TabsPanel(
                            [
                                dmc.Text("Estadísticas descriptivas del dataset final usado para el entrenamiento.", className="mb-3"),
                                dcc.Loading(dash_table.DataTable(id='dataset-describe-table', style_table={'overflowX': 'auto'}))
                            ],
                            value="describe", className="mt-4"
                        ),
                        dmc.TabsPanel(dcc.Loading(dcc.Graph(id='distributions-graph')), value="dist", className="mt-4"),
                        dmc.TabsPanel(dcc.Loading(dcc.Graph(id='correlation-heatmap')), value="corr", className="mt-4"),
                    ],
                    value="describe",
                    variant="outline",
                ),
            ]), className="mb-4"),

            # --- Sección 2: Métricas y Evaluación del Modelo ---
            dbc.Card(dbc.CardBody([
                html.H4("Evaluación del Rendimiento del Modelo", className="card-title"),
                dmc.SimpleGrid(id='model-metrics-grid', cols=3, spacing="lg", className="mb-4"),
                dmc.Tabs(
                    [
                        dmc.TabsList([
                            dmc.TabsTab("Actual vs. Predicho", value="avp"),
                            dmc.TabsTab("Distribución de Errores (Residuos)", value="residuals"),
                            dmc.TabsTab("Gráfico Q-Q de Residuos", value="qq"),
                        ]),
                        dmc.TabsPanel(dcc.Loading(dcc.Graph(id='actual-vs-predicted-graph')), value="avp", className="mt-4"),
                        dmc.TabsPanel(dcc.Loading(dcc.Graph(id='residuals-distribution-graph')), value="residuals", className="mt-4"),
                        dmc.TabsPanel(dcc.Loading(dcc.Graph(id='residuals-qq-graph')), value="qq", className="mt-4"),
                    ],
                    value="avp",
                    variant="outline",
                ),
            ]), className="mb-4"),

            # --- Sección 3: Interpretabilidad del Modelo (XAI) ---
            dbc.Card(dbc.CardBody([
                html.H4("Interpretabilidad del Modelo (Explainable AI)", className="card-title"),
                dmc.Tabs(
                    [
                        dmc.TabsList([
                            dmc.TabsTab("Importancia de Variables (SHAP)", value="shap"),
                            dmc.TabsTab("Dependencia Parcial (PDP)", value="pdp"),
                            dmc.TabsTab("Análisis de Predicción Individual", value="individual"),
                        ]),
                        dmc.TabsPanel(
                            dcc.Loading(dcc.Graph(id='shap-summary-plot')), 
                            value="shap", className="mt-4"
                        ),
                        dmc.TabsPanel(
                            [
                                dmc.Select(
                                    id='pdp-feature-select',
                                    label="Seleccionar Característica para Analizar:",
                                    data=feature_options,
                                    value=feature_options[0]['value'] if feature_options else None,
                                    className="mb-4",
                                    style={"maxWidth": "400px"}
                                ),
                                dcc.Loading(dcc.Graph(id='partial-dependence-plot-graph'))
                            ],
                            value="pdp", className="mt-4"
                        ),
                        dmc.TabsPanel(
                            [
                                dmc.Select(
                                    id='individual-shap-product-select',
                                    label="Seleccionar Producto para Analizar:",
                                    data=product_options,
                                    placeholder="Busque un producto...",
                                    searchable=True,
                                    clearable=True,
                                    className="mb-4",
                                    style={"maxWidth": "600px"}
                                ),
                                dcc.Loading(html.Div(id='individual-shap-waterfall-container'))
                            ],
                            value="individual", className="mt-4"
                        ),
                    ],
                    value="shap",
                    variant="outline",
                )
            ]), className="mb-4"),
        ],
        fluid=True,
        className="mt-4"
    )

def create_metric_card(title, value, icon):
    """
    Función helper para crear tarjetas de métricas.
    Args:
        title (str): Título de la métrica.
        value (float): Valor de la métrica.
        icon (str): Icono para la tarjeta.
    """
    return dmc.Paper(
        p="md",
        shadow="sm",
        withBorder=True,
        children=[
            dmc.Group([
                dmc.ThemeIcon(DashIconify(icon=icon, width=24), size=48, radius="xl", variant="light"),
                html.Div([
                    dmc.Text(title, size="sm", c="dimmed"),
                    dmc.Text(f"{value:.4f}", size="xl", fw=700)
                ])
            ])
        ]
    )


def generate_describe_table(df_desc: pd.DataFrame):
    """
    Prepara los datos y las columnas para la tabla de estadísticas descriptivas.

    Args:
        df_desc (pd.DataFrame): El DataFrame resultante de .describe().

    Returns:
        tuple: Una tupla conteniendo (datos_para_tabla, columnas_para_tabla).
    """
    if df_desc is None or df_desc.empty:
        return [], []
    
    df_desc_reset = df_desc.reset_index()
    df_desc_reset = df_desc_reset.round(4)
    data = df_desc_reset.to_dict('records')
    columns = [{"name": i, "id": i} for i in df_desc_reset.columns]
    return data, columns


def create_distributions_histogram(df: pd.DataFrame):
    """
    Crea una figura con subgráficos, mostrando un histograma para cada 
    variable numérica en el DataFrame.

    Args:
        df (pd.DataFrame): El conjunto de datos completo.

    Returns:
        go.Figure: Una figura de Plotly con múltiples subgráficos.
    """
    if df is None or df.empty:
        return go.Figure(layout={"title": "Datos no disponibles"})
    numeric_cols = df.select_dtypes(include=np.number).columns
    
    if len(numeric_cols) == 0:
        return go.Figure(layout={"title": "No hay columnas numéricas para mostrar"})

    num_cols = min(len(numeric_cols), 2)
    num_rows = (len(numeric_cols) + 1) // num_cols

    fig = make_subplots(
        rows=num_rows, 
        cols=num_cols,
        subplot_titles=numeric_cols
    )

    current_row = 1
    current_col = 1
    for col_name in numeric_cols:
        fig.add_trace(
            go.Histogram(x=df[col_name], name=col_name, nbinsx=50),
            row=current_row, 
            col=current_col
        )
        
        current_col += 1
        if current_col > num_cols:
            current_col = 1
            current_row += 1

    fig.update_layout(
        title_text="Distribución de Variables Numéricas",
        height=250 * num_rows,
        showlegend=False
    )
    fig.update_xaxes(showgrid=True, gridcolor='lightgray')
    fig.update_yaxes(title_text="Frecuencia", showgrid=True, gridcolor='lightgray')

    return fig


def create_correlation_heatmap(df_corr: pd.DataFrame):
    """
    Crea un mapa de calor para la matriz de correlación.

    Args:
        df_corr (pd.DataFrame): La matriz de correlación.

    Returns:
        go.Figure: Una figura de Plotly.
    """
    if df_corr is None or df_corr.empty:
        return go.Figure(layout={"title": "Datos no disponibles"})

    fig = go.Figure(data=go.Heatmap(
        z=df_corr.values,
        x=df_corr.columns,
        y=df_corr.index,
        colorscale='Viridis',
        zmin=-1, zmax=1 # Asegura una escala de color consistente
    ))
    fig.update_layout(title='Matriz de Correlación de Variables')
    return fig


def generate_metric_cards(metrics: dict, create_card_func):
    """
    Genera una lista de tarjetas de métricas del modelo.

    Args:
        metrics (dict): Un diccionario con las métricas del modelo.
        create_card_func (function): La función usada para crear cada tarjeta individual.

    Returns:
        list: Una lista de componentes de Dash (tarjetas).
    """
    if not metrics:
        return [dmc.Alert("Métricas no disponibles.", color="orange")]

    metric_cards = [
        create_card_func("R² Score", metrics.get('r2', 0), "tabler:chart-arcs"),
        create_card_func("Mean Absolute Error (MAE)", metrics.get('mae', 0), "tabler:calculator"),
        create_card_func("Mean Squared Error (MSE)", metrics.get('mse', 0), "tabler:sum"),
    ]
    return metric_cards


def create_actual_vs_predicted_scatter(df_preds: pd.DataFrame):
    """
    Crea un gráfico de dispersión de valores reales vs. predichos.

    Args:
        df_preds (pd.DataFrame): DataFrame con las columnas 'precio_promedio_real' y 'precio_promedio_sugerido'.

    Returns:
        go.Figure: Una figura de Plotly.
    """
    if df_preds is None or df_preds.empty:
        return go.Figure(layout={"title": "Datos no disponibles"})

    fig = px.scatter(
        df_preds, x='precio_promedio_real', y='precio_promedio_sugerido',
        title='Valor Real vs. Valor Predicho',
        labels={'precio_promedio_real': 'Precio Real ($)', 'precio_promedio_sugerido': 'Precio Predicho ($)'},
        trendline='ols', trendline_color_override='red',
        hover_data={'name': True} if 'name' in df_preds.columns else None
    )
    return fig


def create_residuals_histogram(df_preds: pd.DataFrame):
    """
    Crea un histograma de la distribución de los errores (residuos).

    Args:
        df_preds (pd.DataFrame): DataFrame con la columna 'residuals'.

    Returns:
        go.Figure: Una figura de Plotly.
    """
    if df_preds is None or df_preds.empty or 'residuals' not in df_preds.columns:
        return go.Figure(layout={"title": "Datos no disponibles"})

    fig = px.histogram(df_preds, x='residuals', nbins=50, title='Distribución del Error de Predicción (Residuos)')
    fig.update_layout(xaxis_title="Error (Real - Predicho)", yaxis_title="Frecuencia")
    return fig


def create_qq_plot(df_preds: pd.DataFrame):
    """
    Crea un gráfico Q-Q para verificar la normalidad de los residuos.

    Args:
        df_preds (pd.DataFrame): DataFrame con la columna 'residuals'.

    Returns:
        go.Figure: Una figura de Plotly.
    """
    if df_preds is None or df_preds.empty or 'residuals' not in df_preds.columns:
        return go.Figure(layout={"title": "Datos no disponibles"})

    residuals = df_preds['residuals'].dropna()
    if residuals.empty:
        return go.Figure(layout={"title": "No hay datos de residuos para el gráfico Q-Q"})
        
    qq_data = stats.probplot(residuals, dist="norm")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=qq_data[0][0], y=qq_data[0][1], mode='markers', name='Cuantiles de Residuos'))
    fig.add_trace(go.Scatter(x=qq_data[0][0], y=qq_data[1][0] * qq_data[0][0] + qq_data[1][1], mode='lines', name='Línea de Normalidad', line=dict(color='red')))
    fig.update_layout(
        title='Gráfico Q-Q de Residuos vs. Distribución Normal',
        xaxis_title='Cuantiles Teóricos (Normal)',
        yaxis_title='Cuantiles de la Muestra (Residuos)'
    )
    return fig

@callback(
    [
        Output('dataset-describe-table', 'data'),
        Output('dataset-describe-table', 'columns'),
        Output('distributions-graph', 'figure'),
        Output('correlation-heatmap', 'figure'),
        Output('model-metrics-grid', 'children'),
        Output('actual-vs-predicted-graph', 'figure'),
        Output('residuals-distribution-graph', 'figure'),
        Output('residuals-qq-graph', 'figure'),
    ],
    Input('url', 'pathname')
)
def update_model_analysis_page(pathname):
    """
    Orquesta la actualización de todos los componentes estáticos en la página de análisis del modelo.
    """
    if pathname != '/model-analysis':
        return dash.no_update

    central_analyzer = app.server.config.get('CENTRAL_ANALYZER')
    if not central_analyzer:
        empty_fig = go.Figure()
        return [], [], empty_fig, empty_fig, [], empty_fig, empty_fig, empty_fig

    analysis_data = central_analyzer.get_model_analysis_data()
    if not analysis_data:
        return [dash.no_update] * 8

    desc_data, desc_cols = generate_describe_table(analysis_data.get("description"))
    dist_fig = create_distributions_histogram(analysis_data.get("full_dataset"))
    corr_fig = create_correlation_heatmap(analysis_data.get("correlation"))

    metric_cards = generate_metric_cards(analysis_data.get("metrics"), create_metric_card)
    avp_fig = create_actual_vs_predicted_scatter(analysis_data.get("predictions"))
    residuals_fig = create_residuals_histogram(analysis_data.get("predictions"))
    qq_fig = create_qq_plot(analysis_data.get("predictions"))
    
    return desc_data, desc_cols, dist_fig, corr_fig, metric_cards, avp_fig, residuals_fig, qq_fig


@callback(
    Output('shap-summary-plot', 'figure'),
    Input('url', 'pathname')
)
def update_shap_summary_plot(pathname):
    """
    Genera el resumen de SHAP
    """
    if pathname != '/model-analysis':
        return dash.no_update

    central_analyzer = app.server.config.get('CENTRAL_ANALYZER')
    analysis_data = central_analyzer.get_model_analysis_data()
    
    if not analysis_data or 'shap_values_obj' not in analysis_data:
        return go.Figure(layout={"title": "Datos SHAP no disponibles"})

    shap_values = analysis_data['shap_values_obj']
    
    mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
    feature_order_indices = np.argsort(mean_abs_shap)
    sorted_feature_names = [shap_values.feature_names[i] for i in feature_order_indices]
    sorted_shap_values = shap_values.values[:, feature_order_indices]
    sorted_feature_data = shap_values.data[:, feature_order_indices]

    custom_colorscale = [
        [0.0, 'blue'],
        [0.5, 'purple'],
        [1.0, 'red']
    ]
    
    fig = go.Figure()

    for i in range(len(sorted_feature_names)):
        feature_name = sorted_feature_names[i]
        shap_vals_for_feature = sorted_shap_values[:, i]
        feature_vals_for_feature = sorted_feature_data[:, i]
        
        shap_vals_jittered = shap_vals_for_feature + np.random.normal(0, 1e-6, len(shap_vals_for_feature))
        kde = gaussian_kde(shap_vals_jittered)
        density = kde(shap_vals_for_feature)
        
        density_norm = density / np.max(density) if np.max(density) > 0 else np.zeros_like(density)
        
        y_jitter = (np.random.uniform(-0.4, 0.4, len(shap_vals_for_feature))) * density_norm
        

        fig.add_trace(go.Scatter(
            x=shap_vals_for_feature,
            y=np.full(len(shap_vals_for_feature), i) + y_jitter,
            mode='markers',
            marker=dict(
                color=feature_vals_for_feature,
                colorscale=custom_colorscale,
                showscale=(i == len(sorted_feature_names) - 1),
                colorbar=dict(
                    title="Valor de la Característica<br>(Alto -> Rojo, Bajo -> Azul)"
                ),
                size=5,
                opacity=0.7
            ),
            customdata=np.stack((feature_vals_for_feature, [feature_name] * len(feature_vals_for_feature)), axis=-1),
            hovertemplate=(
                "<b>%{customdata[1]}</b><br>"
                "<b>Contribución SHAP</b>: %{x:,.4f}<br>"
                "<b>Valor de la Característica</b>: %{customdata[0]:,.4f}"
                "<extra></extra>"
            ),
            showlegend=False
        ))

    fig.add_vline(x=0, line_width=1.5, line_dash="dot", line_color="black")
    fig.update_layout(
        title="Impacto de las Características en la Predicción (SHAP Summary Plot)",
        xaxis_title="Contribución SHAP al precio predicho",
        yaxis_title=None,
        plot_bgcolor='white',
        yaxis=dict(
            tickmode='array',
            tickvals=list(range(len(sorted_feature_names))),
            ticktext=sorted_feature_names,
            showgrid=True,
            gridcolor='lightgray'
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='lightgray'
        )
    )

    return fig


@callback(
    Output('partial-dependence-plot-graph', 'figure'),
    Input('pdp-feature-select', 'value')
)
def update_pdp_graph(selected_feature):
    """
    Genera el grafico de dependencia parcial (PDP) para la característica seleccionada.
    Args:
        selected_feature (str): La característica seleccionada para el PDP.
    Returns:
        go.Figure: La figura del PDP.
    """
    if not selected_feature:
        return go.Figure(layout={"title": "Por favor, seleccione una característica"})

    central_analyzer = app.server.config.get('CENTRAL_ANALYZER')
    if not central_analyzer or not hasattr(central_analyzer, 'model') or central_analyzer.X_reconstructed is None:
        return go.Figure(layout={"title": "Modelo o datos no disponibles"})

    model = central_analyzer.model
    X = central_analyzer.X_reconstructed

    try:
        pdp_display = PartialDependenceDisplay.from_estimator(model, X, features=[selected_feature])
        
        pdp_data = pdp_display.lines_[0][0].get_xydata()
        x_values = pdp_data[:, 0]
        y_values = pdp_data[:, 1]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x_values, y=y_values, mode='lines', name='Dependencia Promedio'))
        
        fig.update_layout(
            title=f"Gráfico de Dependencia Parcial para '{selected_feature}'",
            xaxis_title=f"Valor de '{selected_feature}'",
            yaxis_title="Impacto en el Precio Predicho"
        )
        return fig
    except Exception as e:
        logger.error(f"Error al generar PDP para '{selected_feature}': {e}")
        return go.Figure(layout={"title": f"No se pudo generar el gráfico para '{selected_feature}'"})



@callback(
    Output('individual-shap-waterfall-container', 'children'),
    Input('individual-shap-product-select', 'value')
)
def update_individual_shap_waterfall(selected_product_id):
    """
    Genera el gráfico de cascada SHAP para la predicción individual del producto seleccionado.
    Args:
        selected_product_id (str): El ID del producto seleccionado.
    Returns:
        html.Div: Un contenedor HTML con el gráfico y el resumen.
    """
    if not selected_product_id:
        return dmc.Alert("Por favor, seleccione un producto para ver el análisis de su predicción.", color="blue")
    
    central_analyzer = app.server.config.get('CENTRAL_ANALYZER')
    analysis_data = central_analyzer.get_model_analysis_data()

    if not analysis_data or 'shap_values_obj' not in analysis_data:
        return dmc.Alert("Los datos de análisis no están disponibles.", color="red")
        
    try:
        df_preds = analysis_data['predictions']
        shap_values_obj = analysis_data['shap_values_obj']
        X_df = analysis_data['X_reconstructed']
        
        base_value = float(central_analyzer.explainer.expected_value)
        
        selected_product_id_int = int(selected_product_id)
        product_index = df_preds[df_preds['product_id'] == selected_product_id_int].index[0]
        
        product_shap_values = shap_values_obj.values[product_index]
        product_feature_values = X_df.iloc[product_index]
        product_predicted_price = df_preds.loc[product_index, 'precio_promedio_sugerido']
        product_real_price = df_preds.loc[product_index, 'precio_promedio_real']

        contribuciones = pd.DataFrame({
            'feature': X_df.columns,
            'value': product_feature_values.values,
            'shap': product_shap_values
        })
        contribuciones['abs_shap'] = contribuciones['shap'].abs()
        contribuciones_sorted = contribuciones.sort_values(by='abs_shap', ascending=False)

        measures = ['absolute'] + ['relative'] * len(contribuciones_sorted) + ['absolute']

        y_labels = ['Valor Base'] + [f"{row.feature} = {row.value:,.2f}" for idx, row in contribuciones_sorted.iterrows()] + ['Predicción Final']
        

        x_values = [base_value] + list(contribuciones_sorted['shap']) + [product_predicted_price]
        
        fig = go.Figure(go.Waterfall(
            orientation="h",
            measure=measures,
            y=y_labels,
            x=x_values,
            increasing={"marker": {"color": "#FF0051"}},
            decreasing={"marker": {"color": "#008BFB"}},
            totals={"marker": {"color": "gray"}},
            connector={"line": {"color": "gray", "width": 1}},
            text=[f"{v:+.2f}" for v in x_values[1:-1]],
            textposition="outside",
        ))

        fig.update_layout(
            title=f"Desglose de la Predicción para '{df_preds.loc[product_index, 'name']}'",
            xaxis_title="Precio ($)",
            yaxis_title="Contribución de la Característica",
            yaxis=dict(
                autorange="reversed"
            ),
            showlegend=False,
            height=400 + len(contribuciones_sorted) * 25
        )

        summary_text = html.Div([
            dmc.Text(f"Precio Base del Modelo (promedio de todas las predicciones): ${base_value:,.2f}", className="mb-2"),
            dmc.Text(f"Precio Final Predicho por el Modelo: ${product_predicted_price:,.2f}",  className="mb-2"),
            dmc.Text(f"Precio Real del Producto: ${product_real_price:,.2f}", className="mb-4"),
        ])

        return html.Div([summary_text, dcc.Graph(figure=fig)])

    except (IndexError, KeyError, ValueError) as e:
        logger.error(f"Error al buscar producto ID '{selected_product_id}': {e}", exc_info=True)
        return dmc.Alert(f"No se pudieron encontrar los datos para el producto seleccionado.", color="orange")
    


@callback(
    Output("download-analysis-dataset", "data"),
    Input("download-dataset-button", "n_clicks"),
    prevent_initial_call=True,
)
def download_dataset(n_clicks):
    """
    Se activa al hacer clic en el botón de descarga y envía el dataset
    completo del análisis como un archivo CSV.
    """
    if not n_clicks:
        return dash.no_update

    logger.info("Solicitud de descarga del dataset de análisis recibida.")
    
    central_analyzer = app.server.config.get('CENTRAL_ANALYZER')
    if not central_analyzer:
        logger.error("No se pudo descargar: CentralAnalyzer no encontrado.")
        return dash.no_update

    analysis_data = central_analyzer.get_model_analysis_data()
    if not analysis_data or "full_dataset" not in analysis_data:
        logger.error("No se pudo descargar: El dataset de análisis no está disponible.")
        return dash.no_update

    df_to_download = analysis_data["full_dataset"]
    
    return dcc.send_data_frame(
        df_to_download.to_csv, 
        "model_analysis_dataset.csv", 
        index=False
    )

@callback(
    Output('train-model-modal', 'opened'),
    Input('open-train-modal-button', 'n_clicks'),
    prevent_initial_call=True,
)
def open_modal(n_clicks):
    """Abre el modal al hacer clic en el botón 'Re-entrenar Modelo'."""
    return True

@callback(
    Output('train-model-button-modal', 'disabled'),
    Input('upload-training-data-modal', 'filename')
)
def enable_train_button_modal(filename):
    """Habilita el botón de entrenamiento dentro del modal solo si se ha seleccionado un archivo."""
    return filename is None

@callback(
    Output('training-status-output-modal', 'children'),
    Input('train-model-button-modal', 'n_clicks'),
    State('upload-training-data-modal', 'contents'),
    State('upload-training-data-modal', 'filename'),
    prevent_initial_call=True
)
def handle_model_training_modal(n_clicks, contents, filename):
    """Maneja la lógica de carga de archivo y entrenamiento del modelo desde el modal."""
    if contents is None:
        return dmc.Alert("Por favor, suba un archivo primero.", color="orange", title="Advertencia")

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        if 'csv' not in filename:
            return dmc.Alert("El archivo debe tener formato CSV.", color="red", title="Error de Archivo")
        
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        
        required_columns = [
            'product_id', 
            'name', 
            'precio_promedio',
            'total_ganancia'
        ]
        if not all(col in df.columns for col in required_columns):
             missing_cols = [col for col in required_columns if col not in df.columns]
             return dmc.Alert(f"El archivo CSV no es válido. Faltan las siguientes columnas esenciales: {', '.join(missing_cols)}", color="red", title="Error de Formato")

        central_analyzer = app.server.config.get('CENTRAL_ANALYZER')
        if not central_analyzer:
            return dmc.Alert("Error interno: El analizador central no está disponible.", color="red", title="Error del Servidor")
        
        logger.info(f"Iniciando entrenamiento con el archivo: {filename}")
        central_analyzer.run_training_from_df(df)
        logger.info("Pipeline de entrenamiento finalizado con éxito.")

        return dmc.Alert(
            "¡Entrenamiento completado exitosamente! El modelo ha sido actualizado. "
            "Por favor, refresque la página para ver los nuevos análisis.",
            color="green",
            title="Éxito",
            withCloseButton=True
        )

    except Exception as e:
        logger.error(f"Error durante el entrenamiento del modelo desde CSV: {e}", exc_info=True)
        return dmc.Alert(f"Ocurrió un error al procesar el archivo o entrenar el modelo: {e}", color="red", title="Error Crítico")