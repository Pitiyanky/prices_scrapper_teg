import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table, callback, Input, Output, State
import pandas as pd
from dash_iconify import DashIconify
import logging
logger = logging.getLogger(__name__)

def build_products_table_section():
    return dbc.Card(
        id="products-table-card",
        className="mb-4 animated-card",
        children=[
            dbc.CardBody([
                html.Div([
                    DashIconify(icon="mdi:table-large", width=25, className="me-2 text-primary"),
                    html.H4("Lista de Productos Filtrados", className="card-title d-inline-block align-middle")
                ], className="d-flex align-items-center mb-3"),

                html.Div(id='loading-products-table-output', className="mb-2 text-muted small"),

                dbc.Button(
                    [DashIconify(icon="mdi:file-excel-outline", className="me-1"), "Exportar a Excel"],
                    id="export-table-button",
                    color="success",
                    className="mb-3",
                    size="sm"
                ),

                dash_table.DataTable(
                    id='products-table-page',
                    columns=[],
                    data=[],  
                    page_size=20,
                    style_table={'overflowX': 'auto', 'width': '100%'},
                    style_cell={
                        'height': 'auto',
                        'whiteSpace': 'normal',
                        'textAlign': 'left',
                    },
                    filter_action='native',
                    filter_options={'case': 'insensitive'},
                    sort_action='native',
                    sort_mode='multi',
                    export_format='none',
                    persistence=True,
                    persisted_props=['filter_query', 'sort_by'],
                )
            ])
        ]
    )

def layout():
    return dbc.Container([
        build_products_table_section(),
        dcc.Download(id="download-table-xlsx")
    ], fluid=True)


@callback(
    Output('products-table-page', 'data'),
    Output('products-table-page', 'columns'),
    Output('loading-products-table-output', 'children'),
    Output('products-table-page', 'style_header'),
    Output('products-table-page', 'style_cell'),
    Output('products-table-page', 'style_data'),
    Output('products-table-page', 'style_filter'),
    Output('products-table-page', 'style_data_conditional'),
    Input('store-filtered-data', 'data'),
)
def update_products_table(filtered_data_json):
    """Callback para actualizar la tabla de productos filtrados."""
    loading_message = ""
    if not filtered_data_json:
        data_to_show = []
        columns_to_show = [{"name": "Mensaje", "id": "message"}]
        data_to_show.append({"message": "No hay datos filtrados para mostrar."})
        loading_message = "No hay datos filtrados para mostrar en la tabla."
    else:
        df_to_display = pd.DataFrame(filtered_data_json)
        if df_to_display.empty:
            data_to_show = []
            columns_to_show = [{"name": "Mensaje", "id": "message"}]
            data_to_show.append({"message": "Los filtros no arrojaron resultados."})
            loading_message = "Los filtros aplicados no arrojaron resultados para la tabla."
        else:
            
            df_to_display['scrape_timestamp'] = pd.to_datetime(df_to_display['scrape_timestamp']).dt.strftime('%d/%m/%Y')

            column_display_names = {
                "name": "Nombre", "price": "Precio", "currency": "Moneda",
                "scrape_timestamp": "Fecha", "extracted_quantity": "Cantidad",
                "website_table_name": "Fuente", "product_type": "Tipo de Producto",
                "udm_name": "UDM",
            }
            cols_to_exclude = ['website_id', 'X_tfidf', 'cleaned_name', 'cluster_id', 'cluster_label','product_type']
            
            dynamic_cols = []
            for original_col_name in df_to_display.columns:
                if original_col_name not in cols_to_exclude:
                    display_name = column_display_names.get(original_col_name, original_col_name.replace("_", " ").title())
                    dynamic_cols.append({"name": display_name, "id": original_col_name, "deletable": False, "selectable": True})
            
            columns_to_show = dynamic_cols
            data_to_show = df_to_display.to_dict('records')
            loading_message = f"Mostrando {len(df_to_display)} productos."

   

    header_bg = '#f8f9fa'     
    header_text = '#212529'   
    cell_bg = '#ffffff'       
    cell_text = '#212529'      
    border_color = '#dee2e6'  
    filter_bg = '#ffffff'     
    filter_text = '#495057'   
    filter_border = '#ced4da'  
    odd_row_bg = 'rgb(248, 248, 248)' 

    style_header_props = {
        'backgroundColor': header_bg,
        'color': header_text,
        'fontWeight': 'bold',
        'borderBottom': f'2px solid {border_color}',
        'borderTop': f'1px solid {border_color}',
        'borderLeft': f'1px solid {border_color}',
        'borderRight': f'1px solid {border_color}',
        'textAlign': 'left',
        'padding': '12px 10px',
    }
    
    style_cell_props = {
        'height': 'auto',
        'minWidth': '100px', 'width': '150px', 'maxWidth': '250px', 
        'whiteSpace': 'normal',
        'textAlign': 'left',
        'padding': '10px 8px',
        'fontFamily': 'inherit',
        'fontSize': '0.875rem', 
        'border': f'1px solid {border_color}',
    }
    
    style_data_props = {
        'backgroundColor': cell_bg,
        'color': cell_text,
    }
    
    style_filter_props = {
        'backgroundColor': filter_bg,
        'color': filter_text,
        'borderLeft': f'1px solid {border_color}', 
        'borderRight': f'1px solid {border_color}',
        'borderBottom': f'1px solid {border_color}', 
    }
    style_data_conditional_props = [
        {'if': {'row_index': 'odd'}, 'backgroundColor': odd_row_bg},
    ]

    return (data_to_show, columns_to_show, loading_message,
            style_header_props, style_cell_props, style_data_props,
            style_filter_props, style_data_conditional_props)

@callback(
    Output("download-table-xlsx", "data"),
    Input("export-table-button", "n_clicks"),
    State("products-table-page", "derived_virtual_data"),
    State("products-table-page", "derived_virtual_selected_rows"),
    State("products-table-page", "columns"),
    prevent_initial_call=True,
)
def download_table_as_xlsx(n_clicks, virtual_data, selected_rows, table_columns):
    """Callback para exportar la tabla a un xlsx."""
    if not virtual_data:
        return dash.no_update

    df_to_export = pd.DataFrame(virtual_data)
    if df_to_export.empty:
        return dash.no_update
    
    columns_ids = [col['id'] for col in table_columns]
    df_to_export = df_to_export[columns_ids]
    
        
    column_names_map = {col['id']: col['name'] for col in table_columns}
    df_to_export.rename(columns=column_names_map, inplace=True)


    return dcc.send_data_frame(df_to_export.to_excel, "productos_filtrados.xlsx", sheet_name="Productos", index=False)