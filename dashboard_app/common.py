from dash import Input, Output, State, html, no_update, ctx, callback, dcc, clientside_callback, _dash_renderer
import dash_bootstrap_components as dbc
from datetime import datetime, date
from dash_iconify import DashIconify
import logging
import pandas as pd
from .app import app, PAGE_PERMISSIONS
from .pages import plots, product_table, configurator, price_intelligence, login, model_analysis
from .filters import build_filters_section
import dash_mantine_components as dmc

_dash_renderer._set_react_version("18.2.0")
logger = logging.getLogger(__name__)



PAGES_WITH_FILTERS = ['/', '/products']

def create_navbar():
    """Crea la barra de navegación superior. Ahora es más simple."""
    return dbc.NavbarSimple(
        children=[
            html.Div(id='nav-links-container', className="d-flex"),
            html.Div(style={'flex': '1'}), 
            dmc.ActionIcon(
                DashIconify(icon="mdi:logout", width=20),
                id="logout-button", variant="filled", color="indigo"
            )
        ],
        brand="Análisis de Precios Competitivos", brand_href="/",
        color="#4c6ef5", dark=True, sticky="top", className="mb-4" 
    )

@callback(
    [Output('session-store', 'data', allow_duplicate=True),
     Output('logout-redirector', 'href')],
    Input('logout-button', 'n_clicks'),
    prevent_initial_call=True
)
def handle_logout(n_clicks):
    """
    Maneja el cierre de sesión. Borra los datos de la sesión y
    le dice al redirector del lado del cliente que navegue a /login.
    """
    if n_clicks and n_clicks > 0:
        logging.info("Cerrando sesión de usuario. Instruyendo al cliente para redirigir.")
        return None, '/login'

    return no_update, no_update

@callback(
    [Output('page-content', 'children'),
     Output('navbar-container', 'children')],
    [Input('url', 'pathname')],
    [State('session-store', 'data')]
)
def route_and_protect_page(pathname, session_data):
    """
    
    """
    if session_data and 'username' in session_data:
        user_role = session_data.get('role')
        navbar = create_navbar()

        if pathname == '/login':
            return dcc.Location(pathname="/", id="redirect-home"), navbar

        if user_role and pathname in PAGE_PERMISSIONS.get(user_role, []):
            if pathname == '/products': return product_table.layout(), navbar
            if pathname == '/config': return configurator.layout(), navbar
            if pathname == '/price-intelligence': return price_intelligence.layout(), navbar
            if pathname == '/model-analysis': return model_analysis.layout(), navbar
            if pathname == '/': return plots.layout(), navbar
        
        access_denied = dmc.Container(dmc.Alert(
            "Acceso Denegado: No tienes permiso para ver esta página.",
            title="Acceso Restringido", color="orange",
        ), className="mt-5")
        return access_denied, navbar

    else:
        if pathname != '/login':
            return dcc.Location(pathname="/login", id="redirect-login"), None
        return login.layout(), None

@callback(
    [Output('date-picker-range', 'min_date_allowed'),
     Output('date-picker-range', 'max_date_allowed'),
     Output('date-picker-range', 'initial_visible_month'),
     Output('date-picker-range', 'start_date'),
     Output('date-picker-range', 'end_date'),
     Output('product-type-dropdown', 'data'),
     Output('retailer-dropdown', 'data')
    ],
    Input('url', 'pathname') 
)
def initialize_filters(pathname):

    if pathname != '/':
        return no_update
        
    central_analyzer = app.server.config.get('CENTRAL_ANALYZER')
    if not central_analyzer:
        logger.error("Analyzer no disponible para inicializar filtros.")
        today = date.today().isoformat()
        return today, today, today, today, today, []

    metadata = central_analyzer.get_initial_filter_options()
    if not metadata:
        today = date.today().isoformat()
        return today, today, today, today, today, []

    min_date_db, max_date_db, unique_types, unique_retailers = metadata
    
    min_date_iso = min_date_db.isoformat()
    max_date_iso = max_date_db.isoformat()
    
    product_type_options = [{'label': t, 'value': t} for t in unique_types]
    retailer_options = [{'label': r, 'value': r} for r in unique_retailers]

    return (min_date_iso, max_date_iso, max_date_iso, 
            min_date_iso, max_date_iso,
            product_type_options, retailer_options)

@callback(
    [Output('store-filtered-data', 'data'),
     Output('loading-feedback-main', 'children'),
    ],
    [Input('search-button', 'n_clicks'),
     Input('date-picker-range', 'value'),  
     Input('product-type-dropdown', 'value'),
     Input('retailer-dropdown', 'value')
    ],
    [State('search-term-input', 'value')],
    prevent_initial_call=True
)

def update_shared_filtered_data(
    search_clicks, date,
    selected_product_types, selected_retailers,search_term
):
    """
    Callback para actualizar los datos filtrados compartidos según los filtros aplicados.
    Args:
        search_clicks (int): Número de clics en el botón de búsqueda.
        date (dict): Diccionario con 'start_date' y 'end_date'.
        selected_product_types (list): Lista de tipos de productos seleccionados.
        selected_retailers (list): Lista de minoristas seleccionados.
        search_term (str): Término de búsqueda ingresado.
    Returns:
        tuple: (datos_filtrados_en_formato_json, mensaje_de_retroalimentación)
    """
    triggered_id = ctx.triggered_id
    logger.info(f"Dashboard update triggered by: {triggered_id}")

    central_analyzer = app.server.config.get('CENTRAL_ANALYZER')
    if not central_analyzer:
        return None, "Error: Analizador no disponible."

    active_search_term = search_term if triggered_id == 'search-button' else None
    
    df_filtered = central_analyzer.fetch_data(
        start_date=date[0] if date else None,
        end_date=date[1] if date else None,
        product_types=selected_product_types,
        search_term=active_search_term,
        retailers=selected_retailers
    )

    feedback_parts = []
    if df_filtered.empty:
        feedback_parts.append("No se encontraron datos para la combinación de filtros seleccionada.")
        if active_search_term:
            feedback_parts.append(f" Específicamente para la búsqueda: '{active_search_term}'.")
        return None, " ".join(feedback_parts)

    feedback_parts.append(f"Mostrando {len(df_filtered)} productos.")
    if date and date[0] and date[1]:
        feedback_parts.append(f"Entre {date[0]} y {date[1]}.")
    if selected_product_types:
        feedback_parts.append(f"De {len(selected_product_types)} tipo(s).")
    if active_search_term:
        feedback_parts.append(f"Coincidiendo con '{active_search_term}'.")

    if 'price' in df_filtered.columns:
        df_filtered['price'] = pd.to_numeric(df_filtered['price'], errors='coerce')
        df_filtered.dropna(subset=['price'], inplace=True)

    final_feedback_msg = " ".join(feedback_parts)
    logger.info(f"Datos filtrados listos para el store: {len(df_filtered)} filas.")
    
    return df_filtered.to_dict('records'), final_feedback_msg

@callback(
    Output('filters-container', 'children'),
    [Input('url', 'pathname')],
    [State('session-store', 'data')]
)
def toggle_filters_visibility(pathname, session_data):
    if session_data and pathname in PAGES_WITH_FILTERS:
        return build_filters_section()
    return None

@callback(
    [Output('nav-links-container', 'children'),
     Output('logout-button', 'style')],
    Input('session-store', 'data')
)
def update_navbar_links(session_data):
    """
    Actualiza los enlaces de la barra de navegación según el rol del usuario.
    Args:
        session_data (dict): Datos de la sesión del usuario.
    Returns:
        tuple: (lista_de_enlaces, estilo_del_boton_de_cierre_de_sesión)
    """
    if not session_data: return [], {'display': 'none'}

    role = session_data.get('role')
    links = []
    link_map = {
        '/': ("Dashboard Histórico", "bi:bar-chart-line-fill"),
        '/price-intelligence': ("Análisis de Precios", "bi:robot"),
        '/products': ("Tabla de Productos", "bi:table"),
        '/model-analysis': ("Análisis del Modelo", "carbon:machine-learning-model"),
        '/config': ("Configuración", "mdi:cog"),
    }
    allowed_paths = PAGE_PERMISSIONS.get(role, [])
    for path in allowed_paths:
        if path in link_map:
            label, icon = link_map[path]
            links.append(dmc.NavLink(
                label=label, href=path, leftSection=DashIconify(icon=icon, width=20),
                variant="filled", active=True, color="indigo", className="text-white"
            ))
    return links, {'display': 'block'}

app.layout = dmc.MantineProvider(
    children=[
        dcc.Location(id='url', refresh=False),
        dcc.Store(id='session-store', storage_type='session'),
        
        dcc.Location(id='logout-redirector', refresh=True),
        dcc.Store(id='store-filtered-data'),
        dcc.Store(id='store-search-term', data=''),
        dcc.Store(id='store-date-range', data={'start_date': None, 'end_date': None}),

        html.Div(id='navbar-container'),
        
        dbc.Container(id='page-wrapper', fluid=True, children=[
            html.Div(id='filters-container'),
            html.Div(id='page-content')
        ])
    ]
)