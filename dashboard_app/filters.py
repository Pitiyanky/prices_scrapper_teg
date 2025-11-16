from dash import html, dcc, callback, Input, Output
from dash_iconify import DashIconify
import dash_mantine_components as dmc
from datetime import datetime, timedelta, date

def build_filters_section():
     return dmc.Container(
        fluid=True,
        children=[

            html.Div(
                [
                    DashIconify(icon="mdi:filter-variant", width=30, className="me-2 text-primary"),
                    html.H4("Filtros y Búsqueda", className="card-title d-inline-block align-middle")
                ],
                className="d-flex align-items-center mb-4"
            ),

            dmc.Grid(
                align="flex-end",
                gutter="lg",
                children=[
                    dmc.GridCol(
                        [
                            html.Label("Rango de Fechas:", className="form-label fw-bold"),
                            dmc.DatePickerInput(
                                id="date-picker-range",
                                value=[datetime.now().date() - timedelta(days=7), datetime.now().date()],
                                type="range",
                                style={"width": "100%"}
                            ),
                        ],
                        span=6
                    ),
                    dmc.GridCol(
                        [
                            html.Label("Buscar nombre de producto:", className="form-label fw-bold"),
                            dmc.TextInput(
                                id="search-term-input",
                                placeholder="Ej: leche, pan, arroz...",
                                rightSection=dmc.ActionIcon(
                                    DashIconify(icon="mdi:magnify"),
                                    id="search-button",
                                    variant="transparent",
                                    color="gray",
                                ),
                                style={"width": "100%"}
                            ),
                        ],
                        span=6
                    ),

                    dmc.GridCol(
                        [
                            html.Label("Filtrar por Tipo de Producto:", className="form-label fw-bold"),
                            dmc.MultiSelect(
                                id='product-type-dropdown',
                                placeholder="Seleccionar tipo(s) de producto...",
                                clearable=True,
                                searchable=True,
                                style={"width": "100%"}
                            )
                        ],
                        span=6
                    ),

                    dmc.GridCol(
                        [
                            html.Label("Filtrar por Retailer:", className="form-label fw-bold"),
                            dmc.MultiSelect(
                                id='retailer-dropdown',
                                placeholder="Seleccionar Retailers...",
                                clearable=True,
                                searchable=True,
                                style={"width": "100%"}
                            )
                        ],
                        span=6
                    ),

                    dmc.GridCol(html.Hr(className="my-4"), span=12),

                    dmc.GridCol(
                        html.Div(id='loading-feedback-main', className="text-center"),
                        span=12
                    )
                ]
            )
        ]
    )


@callback(
    Output('store-search-term', 'data'),
    Input('search-term-input', 'value'),
    prevent_initial_call=True
)
def sync_search_input_to_store(search_value):
    return search_value if search_value is not None else ''

@callback(
    Output('store-date-range', 'data'),
    [Input('date-picker-range', 'value')],
    prevent_initial_call=True
)
def sync_date_picker_to_store(date):
    return {'start_date': date[0], 'end_date': date[1]}