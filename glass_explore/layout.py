import imp
from dash import html
import dash_bootstrap_components as dbc

from glass_explore import LayoutID, igdb

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
        dbc.CardBody()
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
                        ),
                        className="me-3",
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
                ],
                className="g-2"
            )
        )
    )])


table_header = [
    html.Thead(html.Tr([html.Th("Parameter"), html.Th("Value")]))
]

row_u = html.Tr([html.Td("U-value"), html.Td(id = LayoutID.TABLE_CELL_UVALUE)])
row_shgc = html.Tr([html.Td("SHGC"), html.Td(id = LayoutID.TABLE_CELL_SHGC)])

row_vlt = html.Tr([html.Td("U-value"), html.Td(id = LayoutID.TABLE_CELL_UVALUE)])
row_rint = html.Tr([html.Td("U-value"), html.Td(id = LayoutID.TABLE_CELL_UVALUE)])
row_rext = html.Tr([html.Td("U-value"), html.Td(id = LayoutID.TABLE_CELL_UVALUE)])
row_color = html.Tr([html.Td("U-value"), html.Td(id = LayoutID.TABLE_CELL_UVALUE)])

table_body = [html.Tbody([row_u, row_shgc,])]

results_table = dbc.Table(
    table_header + table_body, 
    bordered=True)






graph_tabs = dbc.Tabs(
    [
        dbc.Tab(tab1_content, label="Tab 1"),
        dbc.Tab(tab2_content, label="Tab 2"),
    ]
)
