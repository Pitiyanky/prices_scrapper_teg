import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, dcc, callback, Input, Output, State, no_update, ctx, dash_table
from dash_iconify import DashIconify
from datetime import datetime
import time
import logging
from database_manager import PostgresManager
from config import DB_CONFIG
from shared_context import app_context

logger = logging.getLogger(__name__)

def build_user_management_section():
    return dbc.Card(
        dbc.CardBody([
            html.H4("Gestión de Usuarios", className="card-title"),
            html.P("Crear nuevos usuarios y asignarles un rol en el sistema."),
            dmc.Grid(
                align="flex-end",
                gutter="lg",
                children=[
                    dmc.GridCol(dmc.TextInput(
                        id="new-username-input",
                        label="Nombre de Usuario",
                        placeholder="ej: javier.perez",
                        leftSection=DashIconify(icon="mdi:account-plus-outline"),
                        required=True,
                    ), span=6),
                    
                    dmc.GridCol(dmc.PasswordInput(
                        id="new-password-input",
                        label="Contraseña",
                        placeholder="Contraseña segura",
                        leftSection=DashIconify(icon="mdi:key-plus"),
                        required=True,
                    ), span=6),
                    
                    dmc.GridCol(dmc.Select(
                        id="new-user-role-select",
                        label="Rol del Usuario",
                        data=[
                            {'value': 'admin', 'label': 'Administrador'},
                            {'value': 'analista_precios', 'label': 'Analista de Precios'},
                            {'value': 'data_analyst', 'label': 'Analista de Datos'}
                        ],
                        placeholder="Seleccione un rol",
                        leftSection=DashIconify(icon="mdi:account-group-outline"),
                        required=True,
                    ), span=8),

                    dmc.GridCol(dmc.Button(
                        "Crear Usuario",
                        id="create-user-button",
                        variant="gradient",
                        gradient={"from": "indigo", "to": "cyan"},
                    ), span=4),
                ]
            ),
            html.Div(id="create-user-status-message", className="mt-3")
        ]),
        className="mt-4"
    )

def build_edit_user_section():
    return dbc.Card(dbc.CardBody([
        html.H4("Editar o Eliminar Usuario", className="card-title"),
        dmc.Select(
            id="edit-user-select",
            label="Seleccionar Usuario",
            placeholder="Elige un usuario para modificar...",
            data=[],
            className="mb-3"
        ),
        dmc.Grid(align="flex-end", gutter="lg", children=[
            dmc.GridCol(dmc.TextInput(id="edit-username-input", label="Nuevo Nombre de Usuario (Opcional)"), span=6),
            dmc.GridCol(dmc.PasswordInput(id="edit-password-input", label="Nueva Contraseña (Opcional)"), span=6),
        ]),
        dmc.Space(h="lg"),
        dmc.Group([
            dmc.Button("Actualizar Usuario", id="update-user-button", variant="outline", color="blue"),
            dmc.Button("Eliminar Usuario", id="delete-user-button", variant="outline", color="red"),
        ]),
        html.Div(id="edit-user-status-message", className="mt-3"),
        dmc.Modal(
            title="Confirmar Eliminación",
            id="delete-confirm-modal",
            zIndex=10000,
            children=[
                html.P("¿Estás seguro de que quieres eliminar a este usuario? Esta acción es irreversible."),
                dmc.Group([
                    dmc.Button("Cancelar", id="cancel-delete-button", variant="outline"),
                    dmc.Button("Confirmar Eliminación", id="confirm-delete-button", color="red"),
                ], justify="flex-end", className="mt-3")
            ],
        )
    ]), className="mt-4")

def build_config_section():
    """
    Crea la sección de gestión de parámetros con una tabla interactiva.
    """
    return dbc.Card(
        dbc.CardBody([
            html.H4("Parámetros del Sistema", className="card-title"),
            html.P("Visualiza, edita y crea parámetros de configuración del sistema."),
            
            dmc.Text("Parámetros Actuales (haz clic en una fila para editar):", className="mb-2"),
            dash_table.DataTable(
                id='config-params-table',
                columns=[
                    {"name": "Clave", "id": "config_key"},
                    {"name": "Valor", "id": "config_value"},
                    {"name": "Descripción", "id": "description"},
                    {"name": "Última Actualización", "id": "last_updated"},
                ],
                data=[],
                row_selectable='single',
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '5px', 'whiteSpace': 'normal', 'height': 'auto'},
                style_header={'fontWeight': 'bold'},
                page_size=5,
            ),
            
            dmc.Divider(className="my-4"),

            dmc.Grid(
                align="flex-end",
                children=[
                    dmc.GridCol(dmc.TextInput(
                        id="config-param-key-input",
                        label="Clave del Parámetro",
                        placeholder="Ej: MAIN_JOB_SCHEDULE_TIME",
                        required=True,
                    ), span=4),
                    dmc.GridCol(dmc.TextInput(
                        id="config-param-value-input",
                        label="Valor del Parámetro",
                        required=True,
                    ), span=4),
                    dmc.GridCol(dmc.TextInput(
                        id="config-param-desc-input",
                        label="Descripción (Opcional)",
                    ), span=4),
                ]
            ),
            dmc.Space(h="md"),
            dmc.Group([
                dmc.Button("Limpiar Campos", id="clear-config-button", variant="outline"),
                dmc.Button("Guardar Cambios", id="save-config-button", color="green"),
            ]),
            html.Div(id="config-status-message", className="mt-3")
        ]),
        className="mt-4"
    )

def layout():
    return dbc.Container([
        dmc.Title("Panel de Administración", order=2, className="mb-4"),
        build_user_management_section(),
        build_edit_user_section(),
        build_config_section()
    ], fluid=True)

@callback(
    Output('create-user-status-message', 'children'),
    Input('create-user-button', 'n_clicks'),
    [State('new-username-input', 'value'),
     State('new-password-input', 'value'),
     State('new-user-role-select', 'value')],
    prevent_initial_call=True
)
def manage_user_creation(n_clicks, username, password, role):
    """
    Maneja la creación de un nuevo usuario en el sistema.
    Args:
        n_clicks (int): Número de clics en el botón de creación.
        username (str): Nombre de usuario para el nuevo usuario.
        password (str): Contraseña para el nuevo usuario.
        role (str): Rol asignado al nuevo usuario.
    Returns:
        dmc.Alert: Mensaje de estado sobre el resultado de la creación.
    """

    if not all([username, password, role]):

        return dmc.Alert(
            "Todos los campos son requeridos para crear un usuario.",
            title="Datos Incompletos", color="yellow", withCloseButton=True
        )

    logger.info(f"Intentando crear usuario '{username}' con rol '{role}'.")
    with PostgresManager(DB_CONFIG) as db:

        if not db.conn:
            return dmc.Alert("Error de conexión con la base de datos.", title="Error Crítico", color="red")

        success = db.create_user(username, password, role)

    if success:
        
        return dmc.Alert(
            f"¡Éxito! El usuario '{username}' ha sido creado con el rol '{role}'.",
            title="Usuario Creado", color="green", withCloseButton=True
        )
    else:
        
        return dmc.Alert(
            f"No se pudo crear el usuario '{username}'. Es posible que el nombre de usuario ya exista.",
            title="Error en la Creación", color="red", withCloseButton=True
        )
    
@callback(
    Output('edit-user-select', 'data'),
    [Input('url', 'pathname'), Input('create-user-button', 'n_clicks'), Input('confirm-delete-button', 'n_clicks')]
)
def populate_user_dropdown(pathname, create_clicks, delete_clicks):
    """
    Carga los usuarios en el dropdown de selección de usuario para edición/eliminación.
    """
    with PostgresManager(DB_CONFIG) as db:
        users = db.get_all_users()
    return [{'value': str(user['id']), 'label': user['username']} for user in users]

@callback(
    Output('edit-username-input', 'value'),
    Input('edit-user-select', 'value'),
    State('edit-user-select', 'data')
)
def fill_username_on_select(user_id, user_data):
    """
    Llena el campo de nombre de usuario al seleccionar un usuario del dropdown.
    Args:
        user_id (str): ID del usuario seleccionado.
        user_data (list): Lista de usuarios disponibles.
    Returns:
        str: Nombre de usuario del usuario seleccionado.
    """
    if not user_id or not user_data:
        return ""
    selected_user = next((user['label'] for user in user_data if user['value'] == user_id), None)
    return selected_user or ""

@callback(
    Output('delete-confirm-modal', 'opened'),
    [Input('delete-user-button', 'n_clicks'),
     Input('confirm-delete-button', 'n_clicks'),
     Input('cancel-delete-button', 'n_clicks')],
    [State('delete-confirm-modal', 'opened'),
     State('edit-user-select', 'value')],
    prevent_initial_call=True,
)
def manage_delete_modal(n_delete, n_confirm, n_cancel, is_opened, user_id):
    """
    Maneja la apertura y cierre del modal de confirmación de eliminación de usuario.
    """
    button_id = ctx.triggered_id
    if button_id == 'delete-user-button' and user_id:
        return not is_opened
    return False

@callback(
    Output('edit-user-status-message', 'children'),
    [Input('update-user-button', 'n_clicks'),
     Input('confirm-delete-button', 'n_clicks')],
    [State('edit-user-select', 'value'),
     State('edit-username-input', 'value'),
     State('edit-password-input', 'value'),
     State('session-store', 'data')]
)
def handle_update_or_delete(update_clicks, delete_clicks, user_id, new_username, new_password, session_data):
    """
    Maneja la actualización o eliminación de un usuario según el botón presionado.
    Args:
        update_clicks (int): Número de clics en el botón de actualización.
        delete_clicks (int): Número de clics en el botón de confirmación de eliminación.
        user_id (str): ID del usuario seleccionado.
        new_username (str): Nuevo nombre de usuario (opcional).
        new_password (str): Nueva contraseña (opcional).
        session_data (dict): Datos de la sesión actual.
    Returns:
        dmc.Alert: Mensaje de estado sobre el resultado de la operación.
    """

    if not ctx.triggered_id:
        return no_update
        
    if not user_id:
        return dmc.Alert("Por favor, selecciona un usuario primero.", color="yellow")

    with PostgresManager(DB_CONFIG) as db:
        all_users = db.get_all_users()
        user_to_modify = next((user for user in all_users if user['id'] == int(user_id)), None)
        
        if not user_to_modify:
             return dmc.Alert("El usuario seleccionado ya no existe.", color="orange")
        
        current_admin_username = session_data.get('username')

        if ctx.triggered_id == 'update-user-button':
            if not new_username and not new_password:
                return dmc.Alert("Debes proporcionar un nuevo nombre o una nueva contraseña para actualizar.", color="yellow")
            
            if user_to_modify['username'] == current_admin_username and new_username != current_admin_username:
                return dmc.Alert("No puedes cambiar tu propio nombre de usuario.", color="red")

            success = db.update_user(user_id, new_username, new_password)
            if success:
                return dmc.Alert(f"Usuario '{user_to_modify['username']}' actualizado exitosamente.", color="green")
            else:
                return dmc.Alert("Error al actualizar. El nuevo nombre de usuario podría ya estar en uso.", color="red")

        if ctx.triggered_id == 'confirm-delete-button':
            if user_to_modify['username'] == current_admin_username:
                return dmc.Alert("No puedes eliminar tu propia cuenta.", color="red")

            success = db.delete_user(user_id)
            if success:
                return dmc.Alert(f"Usuario '{user_to_modify['username']}' ha sido eliminado.", color="green")
            else:
                return dmc.Alert("Error al eliminar el usuario.", color="red")
    
    return no_update

@callback(
    Output('config-params-table', 'data'),
    [Input('url', 'pathname'),
     Input('save-config-button', 'n_clicks')]
)
def update_config_table(pathname, save_clicks):
    """
    Actualiza los datos de la tabla de parámetros de configuración.
    Args:
        pathname (str): Ruta actual de la página.
        save_clicks (int): Número de clics en el botón de guardar configuración.
    Returns:
        list: Lista de diccionarios con los parámetros de configuración.
    """
    with PostgresManager(DB_CONFIG) as db:
        params = db.get_all_config_parameters()
    
    for p in params:
        if 'last_updated' in p and p['last_updated']:
            p['last_updated'] = p['last_updated'].strftime('%Y-%m-%d %H:%M:%S')
    
    return params

@callback(
    [Output('config-param-key-input', 'value'),
     Output('config-param-value-input', 'value'),
     Output('config-param-desc-input', 'value')],
    Input('config-params-table', 'selected_rows'),
    State('config-params-table', 'data')
)
def fill_config_inputs_on_select(selected_rows, table_data):
    """
    Llena los campos de entrada de parámetros al seleccionar una fila en la tabla.
    Args:
        selected_rows (list): Índices de las filas seleccionadas en la tabla.
        table_data (list): Datos actuales de la tabla.
    Returns:
        tuple: (clave, valor, descripción) del parámetro seleccionado.
    """
    if not selected_rows:
        return no_update

    selected_row_index = selected_rows[0]
    selected_param = table_data[selected_row_index]
    
    return (
        selected_param.get('config_key', ''),
        selected_param.get('config_value', ''),
        selected_param.get('description', '')
    )

@callback(
    [Output('config-status-message', 'children'),
     Output('config-param-key-input', 'value', allow_duplicate=True),
     Output('config-param-value-input', 'value', allow_duplicate=True),
     Output('config-param-desc-input', 'value', allow_duplicate=True),
     Output('config-params-table', 'selected_rows', allow_duplicate=True)],
    [Input('save-config-button', 'n_clicks'),
     Input('clear-config-button', 'n_clicks')],
    [State('config-param-key-input', 'value'),
     State('config-param-value-input', 'value'),
     State('config-param-desc-input', 'value')],
    prevent_initial_call=True
)
def save_or_clear_config(save_clicks, clear_clicks, key, value, desc):
    """
    Maneja la lógica para guardar un nuevo parámetro de configuración o limpiar los campos.
    Args:
        save_clicks (int): Número de clics en el botón de guardar.
        clear_clicks (int): Número de clics en el botón de limpiar.
        key (str): Clave del parámetro.
        value (str): Valor del parámetro.
        desc (str): Descripción del parámetro.
    Returns:
        tuple: (mensaje de estado, clave, valor, descripción, filas seleccionadas)
    """
    triggered_id = ctx.triggered_id
    
    if triggered_id == 'clear-config-button':
        return dmc.Alert("Campos limpiados.", color="blue", duration=3000), "", "", "", []

    if triggered_id == 'save-config-button':
        if not key or not value:
            return dmc.Alert("La 'Clave' y el 'Valor' del parámetro son obligatorios.", color="yellow"), no_update, no_update, no_update, no_update
        
        with PostgresManager(DB_CONFIG) as db:
            success = db.upsert_config_parameter(key, value, desc)
        
        if success:
            if key == "MAIN_JOB_SCHEDULE_TIME":
                logger.info(f"DASH_APP: Parámetro de schedule actualizado. Notificando al scheduler a través del contexto.")
                app_context.scheduler_event.set()
            return dmc.Alert(f"Parámetro '{key}' guardado exitosamente.", color="green"), "", "", "", []
        else:
            return dmc.Alert(f"Error al guardar el parámetro '{key}'.", color="red"), no_update, no_update, no_update, no_update

    return no_update