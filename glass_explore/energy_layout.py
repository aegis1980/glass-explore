#(c)2026 Jon Robinson. All Rights Reserved.

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

import glass_explore
from glass_explore import EnergyLayoutID, callback_helpers, igdb, OG_DESCRIPTION

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
row_rout = html.Tr([html.Td(["R",html.Sub("out")]), html.Td(id = EnergyLayoutID.TABLE_CELL_ROUT)])
row_rin = html.Tr([html.Td(["R",html.Sub("in")]), html.Td(id = EnergyLayoutID.TABLE_CELL_RIN)])
row_color1 = html.Tr([html.Td("Transmitted colour"), html.Td(id = EnergyLayoutID.TABLE_CELL_COLOR_TRANS)])
row_color2 = html.Tr([html.Td("Reflected colour"), html.Td(id = EnergyLayoutID.TABLE_CELL_COLOR_REFL)])

table_body = [html.Tbody([row_u, row_shgc,row_vlt,row_rout,row_rin,row_color1,row_color2])]

results_table = dbc.Table(
    table_header + table_body, 
    bordered=True)

def navbar():

    nav = dbc.Nav(
        
        [
            dbc.NavItem(dbc.NavLink( "About",id = EnergyLayoutID.NAVLINK_ABOUT)),
            dbc.NavItem(dbc.NavLink( "GLASS EXPLORE | Structure",id = EnergyLayoutID.NAVLINK_STRUCTURE)),
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


radio_thickness = html.Div([
    dbc.Label("Substrate thickness:"),
     dbc.RadioItems(
            options=[
                {"label": "4mm", "value": 4},
                {"label": "6mm", "value": 6},
                {"label": "8mm", "value": 8},
                {"label": "10mm", "value": 10},
            ],
            value=6,
            id="radio-thickness",
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
                f" (Current database version: IGDB v{igdb.db_version()}). At the moment, app is only set up to run the NFRC 100-2010 environment."]),
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
            html.P(["This app is only intended as a playground - consult manufacturer's published data or use a tool such as LBNL Window to verify."]),
            dbc.Row([
                dbc.Col([
                    html.Label("Search Glass Database:"),
                  dbc.Input(
                        id=EnergyLayoutID.INPUT_GLASS_SEARCH,
                        type="search",
                        placeholder="Search" ,
                        list="search-suggestions",
                        placeholder="Type to search...",
                        debounce=True, # Prevents hitting SQLite on every single keystroke
                    ),
                    html.Datalist(id=EnergyLayoutID.DATALIST_GLASS_SEARCH_SUGGESTIONS)
                ], width=6),
            ]),
            html.P(["The source code for this webapp is available on request, under the AGPL-3.0 license. If you want to use any of the code, or have suggestions for improvements, please get in touch."]),
        ]),
        dbc.ModalFooter(
            dbc.Button(
                "Close", id=EnergyLayoutID.MODAL_SEARCH_IGDB_CLOSE, className="ms-auto", n_clicks=0
            )
        ),
    ],
    id=EnergyLayoutID.MODAL_SEARCH_IGDB,
    is_open=False,
)


model_share = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Share IGU buildup ")),
        dbc.ModalBody([
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
             html.P(["Using the URL above will rebuild the IGU buildup, so share/ save that link to recreate. The icon on the right will copy to your clipboard"]),
                        html.P([
                            "The protocol used for the buildup shorthand is documented here & python implementation is MIT license - ",
                            html.A("here", href=LINK_GLASSMODEL, className="alert-link", target="_blank")          
                        ]),
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
        dbc.CardHeader("Gas layer"),
        dbc.CardBody(   
            dbc.Form(
                dbc.Row(
                    [
                        dbc.Label("Gas", width="auto"),
                        dbc.Col(
                            dbc.Select(
                                id=EnergyLayoutID.SELECT_GAS, 
                                value = 'Air',
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

card_selected_layer = dbc.Card([
        dbc.CardHeader("Outer glass layer (user selected)"),
        dbc.CardBody([
            dbc.Form(
                dbc.Row(
                    [
                        dbc.Col(
                           html.Div(id=EnergyLayoutID.DIV_OUTERLITE_PRODUCT)
                        ),
                        dbc.Col(
                            dbc.Checkbox(
                                id=EnergyLayoutID.CHECKBOX_FLIP_OUTERLAYER,
                                label="Flip layer",
                                value=False,
                            )
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
                                                {"label": "NFRC", "value": "nfrc"},
                                                {"label": "EN419 and EN673", "value": "en"},
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

card_inner_layer = dbc.Card([
        dbc.CardHeader("Inner glass layer"),
        dbc.CardBody(   
            dbc.Form(
                dbc.Row(
                    [
                        dbc.Label("Thickness", width="auto"),
                        dbc.Col(
                            dbc.Select(
                                id=EnergyLayoutID.SELECT_INNERLAYER_THICKNESS, 
                                value = 6,
                                options=[{"label" : f"{t}mm", "value" : t} for t in igdb.CLEAR_LOOKUP]
                            )
                        ),
                        dbc.Label("Substrate", width="auto"),
                        dbc.Col(
                            dbc.Select(
                                id=EnergyLayoutID.SELECT_INNERLAYER_SUBSTRATE, 
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


tabs = html.Div(
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
    ]
)

