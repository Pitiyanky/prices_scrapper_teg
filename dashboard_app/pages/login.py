import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, dcc, callback, Input, Output, State, no_update
from dash_iconify import DashIconify
from werkzeug.security import check_password_hash
from database_manager import PostgresManager
from config import DB_CONFIG
from ..app import PAGE_PERMISSIONS 

def layout():
    return dmc.Container(
        [
            dmc.Paper(
                shadow="xl",
                p="xl",
                withBorder=True,
                style={"maxWidth": "500px", "margin": "auto", "marginTop": "100px"},
                children=[
                    dmc.Title("Inicio de Sesión", order=2, className="mb-4"),
                    html.Div(id="login-error-message", className="mb-3"),
                    dmc.TextInput(
                        id="username-input",
                        label="Usuario",
                        placeholder="Ingrese su nombre de usuario",
                        required=True,
                        leftSection=DashIconify(icon="mdi:account"),
                        className="mb-3",
                    ),
                    dmc.PasswordInput(
                        id="password-input",
                        label="Contraseña",
                        placeholder="Ingrese su contraseña",
                        required=True,
                        leftSection=DashIconify(icon="mdi:lock"),
                        className="mb-3",
                    ),
                    dmc.Button(
                        "Ingresar",
                        id="login-button",
                        fullWidth=True,
                        variant="gradient",
                        gradient={"from": "blue", "to": "cyan"},
                    ),
                ],
            )
        ],
        fluid=True,
    )

@callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('session-store', 'data'),
     Output('login-error-message', 'children')],
    Input('login-button', 'n_clicks'),
    [State('username-input', 'value'),
     State('password-input', 'value')],
    prevent_initial_call=True
)
def handle_login(n_clicks, username, password):
    """
    Maneja el proceso de inicio de sesión del usuario.
    Args:
        n_clicks (int): Número de clics en el botón de inicio de sesión.
        username (str): Nombre de usuario ingresado.
        password (str): Contraseña ingresada.
    Returns:
        tuple: (redirect_path, session_data, error_message)
    """
    if not n_clicks or not username or not password:
        return no_update

    with PostgresManager(DB_CONFIG) as db_manager:
        user_data = db_manager.get_user(username)

    if user_data and check_password_hash(user_data['password_hash'], password):

        session_data = {'username': user_data['username'], 'role': user_data['role']}
        user_role = user_data['role']
        allowed_paths = PAGE_PERMISSIONS.get(user_role, [])
        redirect_path = allowed_paths[0] if allowed_paths else '/'
        
        return redirect_path, session_data, None
    else:
        error_alert = dmc.Alert(
            "Usuario o contraseña incorrectos.",
            title="Error de Autenticación",
            color="red", withCloseButton=True,
            icon=DashIconify(icon="mdi:alert-circle-outline"),
        )
        return no_update, no_update, error_alert