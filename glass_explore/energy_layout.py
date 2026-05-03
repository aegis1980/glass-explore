#(c)2026 Jon Robinson. All Rights Reserved.

import dash
from dash import html, dcc
from dash import dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np

from glass_explore import EnergyLayoutID,  igdb, OG_DESCRIPTION, ALL_MANUFACTURERS, DF_GLASS_TABLE

FITC_LOGO = 'balloon_white_h30px.png'
COFFEE = 'coffee.svg'
LINK_COFFEE = "https://www.buymeacoffee.com/fitc"

LINK_GLASSMODEL = "https://github.com/aegis1980/glass-model"



table_header = [
    html.Thead(html.Tr([html.Th("Parameter"), html.Th("Value")]))
]

row_u = html.Tr([html.Td(["U-value (W/m²K)"]), html.Td(id = EnergyLayoutID.TABLE_CELL_UVALUE)])
row_shgc = html.Tr(children=[
    html.Td(id = EnergyLayoutID.TABLE_CELL_SHGC_LABEL),
    html.Td(id = EnergyLayoutID.TABLE_CELL_SHGC)
    ])

row_vlt = html.Tr(children = [
    html.Td(id = EnergyLayoutID.TABLE_CELL_TVIS_LABEL),
    html.Td(id = EnergyLayoutID.TABLE_CELL_TVIS)
    ])
row_rout = html.Tr([html.Td(["Reflection (ext), R",html.Sub("out")]), html.Td(id = EnergyLayoutID.TABLE_CELL_ROUT)])
row_rin = html.Tr([html.Td(["Reflection (int), R",html.Sub("in")]), html.Td(id = EnergyLayoutID.TABLE_CELL_RIN)])
row_color1 = html.Tr([html.Td("Transmitted colour"), html.Td(id = EnergyLayoutID.TABLE_CELL_COLOR_TRANS)])
row_color2 = html.Tr([html.Td("Reflected colour"), html.Td(id = EnergyLayoutID.TABLE_CELL_COLOR_REFL)])

table_body = [html.Tbody([row_u, row_shgc,row_vlt,row_rout,row_rin,row_color1,row_color2])]

results_table = dbc.Table(
    table_header + table_body, 
    bordered=True)


manufacturers = np.sort(DF_GLASS_TABLE.Manufacturer.unique())
manufacturers = np.insert(manufacturers,0,ALL_MANUFACTURERS)


def navbar():

    nav = dbc.Nav(
        
        [
            dbc.NavItem(dbc.NavLink( "About",id = EnergyLayoutID.NAVLINK_ABOUT)),
            dbc.NavItem(dbc.NavLink( "GLASS EXPLORE | Structure",id = EnergyLayoutID.NAVLINK_STRUCTURE)),
            dbc.Popover(
                [
                    html.Strong("Glass Explore | Structure"),
                    html.Br(),
                    "Coming at some point...and...",
                    html.Br(),
                    html.Strong("Maths Explore"),
                    " too."
                ],
                target=EnergyLayoutID.NAVLINK_STRUCTURE,
                body=True,
                trigger="hover",
                placement="bottom"
            ),
        ],
        className="g-0 ms-auto flex-nowrap mt-3 mt-md-0",
    )

    return dbc.Navbar(
            [
                html.A(
                    # Use row and col to control vertical alignment of logo / brand
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src=dash.get_asset_url(FITC_LOGO), height="30px")),
                            dbc.Col(dbc.NavbarBrand(
                                [
                                    "GLASS EXPLORE | ", 
                                    html.B("Energy")
                                ],
                                className="ms-2"
                            )),
                        ],
                        align="center",
                        className="g-0",
                    ),
                    href="https://floatingintheclouds.com",
                    style={"textDecoration": "none"},
                ),
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                    dbc.Collapse(
                        nav,
                        id="navbar-collapse",
                        is_open=False,
                        navbar=True,
                    ),
            ],
        color="dark",
        dark=True,
    )



def select_manufacturer(
    select_id:str = EnergyLayoutID.SELECT_COATED_MANUFACTURER,
    formtext_id:str = EnergyLayoutID.FORMTEXT_SELECT_COATED_MANUFACTURER
):

    return html.Div([
        dbc.Label("Manufacturer:"),
        dbc.Select(
            id=select_id, value = ALL_MANUFACTURERS,
            options=[{"label": m, "value": m} for m in manufacturers]
        ),
        dbc.FormText(id = formtext_id,color='red'),
    ])


def select_thickness(
    select_id:str = EnergyLayoutID.SELECT_COATED_THICKNESS
):

    return html.Div([
        dbc.Label("Substrate thickness:"),
        dbc.Select(
            options=[
                {"label": "4mm", "value": 4},
                {"label": "6mm", "value": 6},
                {"label": "8mm", "value": 8},
                {"label": "10mm", "value": 10},
                {"label": "12mm", "value": 12}
            ],
            value=6,
            id=select_id,
        ),
    ]
)

def modal_about():
    return dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("GLASS EXPLORE | Energy")),
        dbc.ModalBody([
            html.P([OG_DESCRIPTION +f" using coatings and substrate data in the ",
                html.A("IGDB database", href="https://windows.lbl.gov/igdb-downloads", className="alert-link", target="_blank"),
                f" (Current database version running in app: IGDB v{igdb.db_version()})."]),
            html.P(["This app is only intended as a playground - consult manufacturer's published data or use a tool such as LBNL Window to verify."]),
            dbc.Row([
                dbc.Col([
                    html.A(
                        html.Img(src=dash.get_asset_url(COFFEE), height="60px"), 
                        href=LINK_COFFEE, className="alert-link", target="_blank"
                    ),
                ],
                width="auto"
                ),
                dbc.Col([
                    html.P([
                        "Glass Explore took me a fair while to write (and check!). Server costs are not free either. If you do find this app useful, please consider ", 
                        html.A("buying me a coffee", href=LINK_COFFEE, className="alert-link", target="_blank")
                    ]),
                    html.P([
                        "I have a few bits and bobs I want to add, but if you have suggestions, contact me on ", 
                        html.A("linkedin", href="https://www.linkedin.com/in/jon-robinson-nz/", className="alert-link", target="_blank")
                    ])
                ]),
            ]),
            html.P(["The source code for this webapp is available on request, under the AGPL-3.0 license. If you want to use any of the code, or have suggestions for improvements, please get in touch."]),
        ]),
        dbc.ModalFooter(
            dbc.Button(
                "Close", id=EnergyLayoutID.MODAL_ABOUT_CLOSE, className="ms-auto", n_clicks=0
            )
        ),
    ],
    id=EnergyLayoutID.MODAL_ABOUT,
    is_open=False,
)


def modal_glass_search():
    return dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("GLASS EXPLORE | Energy")),
        dbc.ModalBody([
            html.P(["Search by LBNL ID or product name."]),
            dbc.Row([
                dbc.Col([
                  dbc.Input(
                        id=EnergyLayoutID.MODAL_SEARCH_INPUT_GLASS_SEARCH,
                        type="search",
                        placeholder="Search IGDB" ,
                        debounce=False,
                    )
                ],className="mb-3")
            ]),
            dbc.Row([
                dbc.Col([
                    select_manufacturer(
                        EnergyLayoutID.MODAL_SEARCH_SELECT_COATED_MANUFACTURER, 
                        EnergyLayoutID.MODAL_SEARCH_FORMTEXT_SELECT_COATED_MANUFACTURER
                    )
                ],width=6),
                dbc.Col([
                    select_thickness(EnergyLayoutID.MODAL_SEARCH_SELECT_COATED_THICKNESS)
                ],width=6)
            ],className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dash_table.DataTable(
                        id=EnergyLayoutID.MODAL_SEARCH_DATATABLE,
                        page_action='none', # Disable Pagination
                        virtualization=True,
                        fixed_rows={'headers': True},
                        row_selectable="single",  # Enables the selection logic
                        selected_rows=[],         # Initial state
                        css=[
                            {
                                'selector': '.dash-select-header input, .dash-select-cell input',
                                'rule': 'display: none;',
                            },
                            {
                                'selector': '.dash-select-header, .dash-select-cell',
                                'rule': 'width: 1px; min-width: 1px; max-width: 1px; padding: 0;',
                            },
                        ],
                        style_data_conditional=[
                            {
                                'if': {'state': 'selected'}, # This highlights the entire row
                                'backgroundColor': 'rgba(0, 116, 217, 0.2)',
                                'border': '1px solid #0074D9'
                            },
                            # 2. Force the active cell to look exactly like the selected row
                            # This removes the unique 'active cell' highlight
                            {
                                'if': {'state': 'active'},
                                'backgroundColor': 'rgba(0, 116, 217, 0.2)',
                                'border': '1px solid #0074D9'
                            }
                        ],

                        columns=[
                            {"name": "ID", "id": "ID"},
                            {"name": "Name", "id": "Name"},
                            {"name": "Product Name", "id": "ProductName"},
                            {"name": "Manufacturer", "id": "Manufacturer"},
                            {"name": "Thickness (mm)", "id": "Thickness"},
                        ],
                        data=[], # Starts empty

                        # 1. Compact Styling
                        style_cell={
                            'fontSize': '10px',      # Smaller text
                            'fontFamily': 'sans-serif',
                            'padding': '2px 5px',    # Tighten vertical/horizontal padding
                            'textAlign': 'left',
                            'minWidth': '40px',      # Minimum width for stability
                            'maxWidth': '150px',     # Prevent columns from growing too wide
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis', # Add '...' to long text
                        },

                        # 2. Specific Column Adjustments
                        style_cell_conditional=[
                            {'if': {'column_id': 'ID'}, 'width': '50px'},
                            {'if': {'column_id': 'Thickness'}, 'width': '60px'},
                            {'if': {'column_id': 'Manufacturer'}, 'width': '100px'},
                        ],

                        # 3. Overall Table Constraints
                        style_table={
                            'overflowX': 'auto',
                            'overflowY': 'auto', 
                            'maxHeight': '400px',
                            'maxWidth': '100%'
                        },

                        # 4. Header Styling
                        style_header={
                            'fontWeight': 'bold',
                            'fontSize': '10px'
                        },


                        # Add filtering/sorting if required
                        sort_action="native",
                    )
                ])
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button(
                "Ok", id=EnergyLayoutID.MODAL_SEARCH_IGDB_OK, n_clicks=0, color="success",outline=True, disabled=True
            ),           
            dbc.Button(
                "Cancel", id=EnergyLayoutID.MODAL_SEARCH_IGDB_CLOSE, className="ms-auto", color="danger",n_clicks=0
            )
        ]),
    ],
    id=EnergyLayoutID.MODAL_SEARCH_IGDB,
    size="lg",
    is_open=False,
)


def modal_share():
    return dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Share IGU buildup ")),
        dbc.ModalBody([
            html.P(["Using the URL below to share"]),
            dbc.Alert(
                [dcc.Link(
                    '',
                    id = EnergyLayoutID.LINK_GSTR,
                    target='_blank',
                    href = ''
                ),
                dcc.Clipboard(
                    target_id=EnergyLayoutID.LINK_GSTR,
                    title="Copy URL to clipboard",
                    style={
                        "display": "inline-block",
                        "fontSize": 18,
                        "verticalAlign": "right",
                        "float":"right"
                    },
                )],color = "light"
            ),
        ]),
        dbc.ModalFooter(
            dbc.Button(
                "Close", id=EnergyLayoutID.MODAL_SHARE_CLOSE, className="ms-auto", n_clicks=0
            )
        ),
    ],
    id=EnergyLayoutID.MODAL_SHARE,
    is_open=False,
)

def card_gas_layer():
    return dbc.Card([
        dbc.CardHeader("Gas cavity"),
        dbc.CardBody(   
            dbc.Form(
                dbc.Row(
                    [
                        dbc.Label("Gas", width="auto"),
                        dbc.Col(
                            dbc.Select(
                                id=EnergyLayoutID.SELECT_GAS, 
                                value = 'air',
                                options=[{"label": k, "value": k} for k in igdb.GASES_NFRC_LOOKUP],
                            ),
                            className="me-3",
                        ),
                        dbc.Label("Gap width (mm)", width="auto"),
                        dbc.Col(
                            dbc.Input(
                                id=EnergyLayoutID.INPUT_GAP,
                                type="number", 
                                value="12"
                            ),
                            
                            className="me-3",
                        )
                    ],
                    className="g-2"
                )
            ))],
            className="mb-2",
        )

def card_coated_layer():
    return dbc.Card([
        dbc.CardHeader("Coated outer glass layer", id = EnergyLayoutID.CARD_HEADER_COATED),
        dbc.CardBody([
            dbc.Form(
                dbc.Row(
                    [
                        dbc.Col([
                            html.A([], 
                                id = EnergyLayoutID.LINK_COATED_LITE_ID,
                                style={
                                    "color": "blue", 
                                    "textDecoration": "underline", 
                                    "cursor": "pointer"
                                }
                            ),
                            html.Br(),
                            html.Div(id=EnergyLayoutID.DIV_COATED_LITE_PRODUCT)
                        ],width=8),
                        dbc.Col(
                            dbc.Checkbox(
                                id=EnergyLayoutID.CHECKBOX_FLIP_COATEDLAYER,
                                label="Flip layer",
                                value=False,
                            ),
                            width=4,
                        )
                    ]
                )
            )
        ])],
        className="mb-2",
    )


def card_results():
    return dbc.Card([
        dbc.CardHeader("Glass properties"),
                dbc.CardBody(   
                    dbc.Form(
                        [dbc.Row([
                            dbc.Label("Standard", width="auto"),
                            dbc.Col(
                               dbc.Select(
                                        id=EnergyLayoutID.SELECT_STANDARD, 
                                        value = "en",
                                        options=[
                                                {"label": "USA: NFRC 100-2010", "value": "nfrc"},
                                                {"label": "Europe: EN410 (optical/ solar) and EN673 (thermal)", "value": "en"},
                                        ],
                                    )
                            , className="me-3",)
                        ], className="mb-3"),
                        dbc.Row(
                            dbc.Col(
                                [dbc.Spinner(results_table, color="dark", type="grow")]
                            )
                        )]
                    )
                )]
            )

def card_noncoated_layer():
    return dbc.Card([
        dbc.CardHeader(["Non-coated inner glass layer"],id = EnergyLayoutID.CARD_HEADER_NONCOATED),
        dbc.CardBody(   
            dbc.Form(
                dbc.Row(
                    [
                        dbc.Label("Thickness", width="auto"),
                        dbc.Col(
                            dbc.Select(
                                id=EnergyLayoutID.SELECT_UNCOATED_THICKNESS, 
                                value = 6,
                                options=[{"label" : f"{t}mm", "value" : t} for t in igdb.CLEAR_LOOKUP]
                            )
                        ),
                        dbc.Label("Substrate", width="auto"),
                        dbc.Col(
                            dbc.Select(
                                id=EnergyLayoutID.SELECT_UNCOATED_SUBSTRATE, 
                                value = 'clear',
                                options=[
                                    {"label": "clear", "value": 'clear'},
                                    {"label": "ultraclear (low iron)", "value": 'ultraclear'},
                                ],
                            ),
                            className="me-3",
                        )
                    ]
                )
            )
        )],
        className="mb-2",
    )


div_buttons = html.Div([
            dbc.Button("Share buildup", id= EnergyLayoutID.BUTTON_SHARE, size='sm',outline=True, color="secondary",className="me-1"),
            dbc.Button("Export report", size='sm',id= EnergyLayoutID.BUTTON_REPORT, outline=True, color="secondary",className="me-1"),
        ],className="mb-2"
    )



def init_graph():

    fig = go.Figure()
    fig.update_layout(
        height = 800,
    )
    return html.Div(
        dbc.Spinner(
            dcc.Graph(
                id = EnergyLayoutID.GRAPH_IGDB, 
                figure = fig,
                #style={'width': '100%', 'height': '90vh'}
            ), color="secondary", type="grow",spinner_style={"width": "10rem", "height": "10rem"}),
        id= EnergyLayoutID.DIV_GRAPH_IGDB
    )


def graph_tabs():
    return html.Div(
    [
        dbc.Tabs(
            [
                dbc.Tab(label="Tsolar vs Tvis", tab_id=EnergyLayoutID.TAB_GRAPH_TS_TV),
                dbc.Tab(label="Lab colour space", tab_id=EnergyLayoutID.TAB_GRAPH_LAB),
                dbc.Tab(label="RGB colour space", tab_id= EnergyLayoutID.TAB_GRAPH_RGB),
            ],
            id=EnergyLayoutID.TABS,
            active_tab=EnergyLayoutID.TAB_GRAPH_TS_TV,
        ),
        html.Div([init_graph()],id=EnergyLayoutID.TAB_CONTENT)
    ],className="mt-auto"
)

