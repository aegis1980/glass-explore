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

form_gap = dbc.Form(
    dbc.Row(
        [
            dbc.Label("Gas", width="auto"),
            dbc.Col(
                dbc.Select(
                    id=LayoutID.MODAL_ANALYSIS_SELECT_GAS, 
                    value = 'air',
                    options=[{"label": k, "value": k} for k in igdb.GASES],
                ),
                className="me-3",
            ),
            dbc.Label("Gap width (mm)", width="auto"),
            dbc.Col(
                dbc.Input(
                    id=LayoutID.MODAL_ANALYSIS_INPUT_GAP,
                    type="number", 
                    value="12"
                ),
                
                className="me-3",
            )
        ],
        className="g-2",
    )
)

modal_analysis = dbc.Modal(
            [
                dbc.ModalBody([
                    form_gap
                ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id=LayoutID.MODAL_ANALYSIS_CLOSE, className="ms-auto", n_clicks=0
                    )
                ),
            ],
            id=LayoutID.MODAL_ANALYSIS,
            size="xl",
            is_open=False,
        )
