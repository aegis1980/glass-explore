from dash import dcc,html, Input, Output, State
import dash_bootstrap_components as dbc

PLOTLY_LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"

navbar = dbc.Navbar(
    [
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    dbc.Col(html.Img(src=PLOTLY_LOGO, height="30px")),
                    dbc.Col(dbc.NavbarBrand("GLASS EXPLORE", className="ms-2")),
                ],
                align="center",
                className="g-0",
            ),
            href="https://plotly.com",
            style={"textDecoration": "none"},
        )
    ],
    color="dark",
    dark=True,
)

modal_popup = dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Welcome to Glass Explore")),
                dbc.ModalBody([
                    html.P("Data from Lawrence Berkeley National Laboratory IGDB database."),
                    html.P(["Chart plots Solar Transmittance (T",html.Sub("sol"),") and Visible Light Transmittance  (T",html.Sub("vis"),") of 6mm and 8mm glasses in the database."]),
                    html.P(["Note:  Solar and visilble light transmission properties will depend on what glazing buildup these products are included in. The charted (T",html.Sub("vis"),") and (T",html.Sub("sol"),") are only indicative of the VLT and g-factor/SHGC of the buildup performance."])
                ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close", className="ms-auto", n_clicks=0
                    )
                ),
            ],
            id="modal",
            is_open=True,
        )