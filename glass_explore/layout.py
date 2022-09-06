from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import glass_explore
from glass_explore import LayoutID, callback_helpers, igdb

FITC_LOGO = 'balloon_white_h30px.png'

nav = dbc.Nav(
    [
        dbc.NavItem(dbc.NavLink( "About",id = LayoutID.NAVLINK_ABOUT)),
        dbc.NavItem(dbc.NavLink("Settings",disabled=True,id = LayoutID.NAVLINK_SETTINGS)),
    ]
)

def navbar(app):
    return dbc.Navbar(
    [
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    dbc.Col(html.Img(src=app.get_asset_url(FITC_LOGO), height="30px")),
                    dbc.Col(dbc.NavbarBrand("GLASS EXPLORE", className="ms-2")),
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

modal_about = dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Welcome to Glass Explore")),
                dbc.ModalBody([
                    html.P("I wote this web app as playgrou"),
                    html.P(["Running website comes at a personal cost and if it beomes too costly it'll be lights out. So, if you find useful please consider the following:"]),
                    html.P(["Passing through? Click on the advertising banner above"]),
                    html.P(["You find useful? Consider a dinatoin thghh. "]),
                ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id=LayoutID.MODAL_ABOUT_CLOSE, className="ms-auto", n_clicks=0
                    )
                ),
            ],
            id=LayoutID.MODAL_ABOUT,
            is_open=True,
        )




modal_settings = dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Settings")),
                dbc.ModalBody([
                    dbc.Label("Optical standard"),
                    dbc.Select(
                        id=LayoutID.SELECT_OPTICAL_STANDARD,
                        options = callback_helpers.populate_standards(False),
                        value=glass_explore.DEFAULT_OPTICAL_STANDARD
                    ),
                    dbc.Checkbox(
                        id=LayoutID.CHECKBOX_ADVANCED_OPTICAL_STANDARD,
                        label="Show some other optical setups",
                        value=False,
                    )                            
                 ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Done with settings", id=LayoutID.MODAL_SETTINGS_CLOSE, className="ms-auto", n_clicks=0
                    )
                ),
            ],
            id=LayoutID.MODAL_SETTINGS,
            is_open=False,
        )


card_gas_layer = dbc.Card([
    dbc.CardHeader("Gas layer"),
    dbc.CardBody(   
        dbc.Form(
            dbc.Row(
                [
                    dbc.Label("Gas", width="auto"),
                    dbc.Col(
                        dbc.Select(
                            id=LayoutID.SELECT_GAS, 
                            value = 'air',
                            options=[{"label": k, "value": k} for k in igdb.GASES],
                        ),
                        className="me-3",
                    ),
                    dbc.Label("Gap width (mm)", width="auto"),
                    dbc.Col(
                        dbc.Input(
                            id=LayoutID.INPUT_GAP,
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
                           html.Div(id=LayoutID.DIV_OUTERLITE_PRODUCT)
                        ),
                        dbc.Col(
                            dbc.Checkbox(
                                id=LayoutID.CHECKBOX_FLIP_OUTERLAYER,
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

card_other_layer = dbc.Card([
        dbc.CardHeader("Inner glass layer"),
        dbc.CardBody(   
            dbc.Form(
                dbc.Row(
                    [
                        dbc.Label("Thickness", width="auto"),
                        dbc.Col(
                            dbc.Select(
                                id=LayoutID.SELECT_INNERLAYER_THICKNESS, 
                                value = 6,
                                options=[{"label" : f"{t}mm", "value" : t} for t in igdb.CLEAR_LOOKUP]
                            )
                        ),
                        dbc.Label("Substrate", width="auto"),
                        dbc.Col(
                            dbc.Select(
                                id=LayoutID.SELECT_INNERLAYER_SUBSTRATE, 
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


table_header = [
    html.Thead(html.Tr([html.Th("Parameter"), html.Th("Value")]))
]

row_u = html.Tr([html.Td("U-value"), html.Td(id = LayoutID.TABLE_CELL_UVALUE)])
row_shgc = html.Tr([html.Td("SHGC"), html.Td(id = LayoutID.TABLE_CELL_SHGC)])

row_vlt = html.Tr([html.Td(["T",html.Sub("vis")]), html.Td(id = LayoutID.TABLE_CELL_TVIS)])
row_rout = html.Tr([html.Td(["R",html.Sub("out")]), html.Td(id = LayoutID.TABLE_CELL_ROUT)])
row_rin = html.Tr([html.Td(["R",html.Sub("in")]), html.Td(id = LayoutID.TABLE_CELL_RIN)])
row_color1 = html.Tr([html.Td(["Colour",html.Sub("trans")]), html.Td(id = LayoutID.TABLE_CELL_COLOR_TRANS)])
row_color2 = html.Tr([html.Td(["Colour",html.Sub("refl")]), html.Td(id = LayoutID.TABLE_CELL_COLOR_REFL)])

table_body = [html.Tbody([row_u, row_shgc,row_vlt,row_rout,row_rin,row_color1,row_color2])]

results_table = dbc.Table(
    table_header + table_body, 
    bordered=True)

def graphs():

    fig1 = go.Figure()
    fig1.update_layout(
        height = 800,
    )

    graph_ts_tv  = dcc.Graph(id = LayoutID.GRAPH, figure = fig1)

    return html.Div(graph_ts_tv)




nav_graphs = html.Div(
    [
        dbc.RadioItems(
            id=LayoutID.BUTTONGROUP_GRAPHTYPE,
            className="btn-group",
            inputClassName="btn-check",
            labelClassName="btn btn-outline-primary",
            labelCheckedClassName="active",
            options=[
                {"label": "Graph: Ts vs Tv", "value": glass_explore.GRAPHTYPE_TS_TV},
                {"label": "Graph: l*a*b* color space", "value": glass_explore.GRAPHTYPE_LAB},
                {"label": "Graph: RGB color space", "value": glass_explore.GRAPHTYPE_RGB},
            ],
            value=1,
        ),
        html.Div(id="output"),
    ],
    className="radio-group",
)

# nav_graphs = dbc.Nav(
#     [
#         dbc.NavItem(dbc.NavLink("Graph: Ts vs Tv", active=True)),
#         dbc.NavItem(dbc.NavLink("Graph: l*a*b* color space")),
#         dbc.NavItem(dbc.NavLink("Graph: RGB color space")),
#     ],
#     pills=True,
#     id=LayoutID.NAV_GRAPHTYPE
# )