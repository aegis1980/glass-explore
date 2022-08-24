from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from glass_explore import GRAPHTYPE_RGB, GRAPHTYPE_TS_TV,GRAPHTYPE_LAB, LayoutID, igdb

FITC_LOGO = 'balloon_white_h30px.png'

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
        )
    ],
    color="dark",
    dark=True,
)

modal_splash = dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Welcome to Glass Explore")),
                dbc.ModalBody([
                    html.P("Data from Lawrence Berkeley National Laboratory IGDB database."),
                    html.P(["Chart plots Solar Transmittance (T",html.Sub("sol"),") and Visible Light Transmittance  (T",html.Sub("vis"),") of 6mm and 8mm glasses in the database."]),
                    html.P(["Note:  Solar and visible light transmission properties will depend on what glazing buildup these products are included in. The charted (T",html.Sub("vis"),") and (T",html.Sub("sol"),") are only indicative of the VLT and g-factor/SHGC of the buildup performance."])
                ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id=LayoutID.MODAL_SPLASH_CLOSE, className="ms-auto", n_clicks=0
                    )
                ),
            ],
            id=LayoutID.MODAL_SPLASH,
            is_open=True,
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
        )
    )])

card_selected_layer = dbc.Card([
        dbc.CardHeader("Outer lite (user selected)"),
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
        ])
    ])

card_other_layer = dbc.Card([
    dbc.CardHeader("Inner lite"),
    dbc.CardBody(   
        dbc.Form(
            dbc.Row(
                [
                    dbc.Label("Thickness", width="auto"),
                    dbc.Col(
                        dbc.Select(
                            id=LayoutID.SELECT_INNERLAYER_THICKNESS, 
                            value = 6,
                            options=[
                                {"label": "4mm", "value": 4},
                                {"label": "6mm", "value": 6},
                                {"label": "8mm", "value": 8},
                                {"label": "10mm", "value": 10},
                            ],
                        )
                    ),
                    dbc.Label("Substrate", width="auto"),
                    dbc.Col(
                        dbc.Select(
                            id=LayoutID.SELECT_INNERLAYER_SUBSTRATE, 
                            value = 'clear',
                            options=[
                                {"label": "clear", "value": "clear"},
                                {"label": "super-clear (low iron)", "value": "super-clear"},
                            ],
                        ),
                        className="me-3",
                    )
                ]
            )
        )
    )])


table_header = [
    html.Thead(html.Tr([html.Th("Parameter"), html.Th("Value")]))
]

row_u = html.Tr([html.Td("U-value"), html.Td(id = LayoutID.TABLE_CELL_UVALUE)])
row_shgc = html.Tr([html.Td("SHGC"), html.Td(id = LayoutID.TABLE_CELL_SHGC)])

row_vlt = html.Tr([html.Td(["T",html.Sub("vis")]), html.Td(id = LayoutID.TABLE_CELL_TVIS)])
row_rout = html.Tr([html.Td(["R",html.Sub("out")]), html.Td(id = LayoutID.TABLE_CELL_ROUT)])
row_rin = html.Tr([html.Td(["R",html.Sub("in")]), html.Td(id = LayoutID.TABLE_CELL_RIN)])

table_body = [html.Tbody([row_u, row_shgc,row_vlt,row_rout,row_rin])]

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



def tabs():

    

    fig1 = go.Figure()
    fig1.update_layout(
        height = 800,
    )

    fig2 = go.Figure()
    fig2.update_layout(
        height = 800,
    )

    graph_ts_tv  = dcc.Graph(id = LayoutID.GRAPH, figure = fig1)
    graph_lab = dcc.Graph(id = LayoutID.GRAPH_LAB, figure = fig2)

    tabs = dbc.Tabs(
        [
            dbc.Tab(graph_ts_tv, label="Graph: Tsolar vs Tvis"),
            dbc.Tab(graph_lab, label="Graph: Colour space"),
        ]
    )

    return tabs


buttongroup_graphs = html.Div(
    [
        dbc.RadioItems(
            id=LayoutID.BUTTONGROUP_GRAPHTYPE,
            className="btn-group",
            inputClassName="btn-check",
            labelClassName="btn btn-outline-primary",
            labelCheckedClassName="active",
            options=[
                {"label": "Graph: Ts vs Tv", "value": GRAPHTYPE_TS_TV},
                {"label": "Graph: l*a*b* color space", "value": GRAPHTYPE_LAB},
                {"label": "Graph: RGB color space", "value": GRAPHTYPE_RGB},
            ],
            value=1,
        ),
        html.Div(id="output"),
    ],
    className="radio-group",
)