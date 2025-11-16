import dash
import dash_bootstrap_components as dbc

PAGE_PERMISSIONS = {
    'admin': ['/', '/products', '/price-intelligence', '/model-analysis','/config', ],
    'analista_precios': ['/', '/products', '/price-intelligence'],
    'data_analyst': ['/', '/products','/price-intelligence', '/model-analysis']
}

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)
app.title = "Dashboard de Productos"
server = app.server