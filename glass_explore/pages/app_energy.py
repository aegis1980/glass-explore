
import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd

from dash import Input, Output, State, ctx, dcc, html,clientside_callback, callback
from dash.exceptions import PreventUpdate

import dash_breakpoints

from glass_explore import (ALL_MANUFACTURERS, OG_DESCRIPTION, URL, DF_GLASS_TABLE,CLEAR_6,DEFAULT_GRAPH_GLASS, Buildup, EnergyLayoutID, Paths,
                           SelectedPointProps, caching, callback_helpers, energy_layout, igdb,COLORSPACE_RGB,COLORSPACE_LAB,
                           standards)
from glass_explore import callbacks_energy

manufacturers = np.sort(DF_GLASS_TABLE.Manufacturer.unique())
manufacturers = np.insert(manufacturers,0,ALL_MANUFACTURERS)


dash.register_page(
    __name__, 
    path=Paths.ENERGY,
    title = "Glass Explore | Energy"
)


select_manufacturer = html.Div([
    dbc.Label("Manufacturer:"),
    dbc.Select(
        id="select-manufacturer", value = ALL_MANUFACTURERS,
        options=[{"label": m, "value": m} for m in manufacturers]
    ),
    dbc.FormText(id = 'formtext-manufacturer',color='red'),
])




#my_bcm = caching.background_callback_manager()

# app = dash.Dash(
#     __name__,
#     external_stylesheets=[dbc.themes.BOOTSTRAP],
#     #background_callback_manager=my_bcm,
#     index_string=dash.dash._default_index.replace('<html>', '<html lang="en" prefix="og: http://ogp.me/ns#">'),
#     meta_tags=[
#         {"name": "viewport", "content": "width=device-width, initial-scale=1"},
#         {"property" : "og:title", "content": "Glass Explore"},
#         {"name":"image" ,  "property":"og:image" ,  "content":"https://floatingintheclouds.com/wp-content/uploads/2022/09/glass-explore.png" },
#         {"name":"author" ,  "content":"Jon Robinson" },
#         {"property" : "og:description", "content": OG_DESCRIPTION},
#         {"property" : "og:url", "content": URL}
#     ],
# )

# app.title = "Glass Explore"
def layout(g = None): 
    return html.Div([
        html.Div('',id=EnergyLayoutID.DIV_HIDDEN_WINDOW_HT,className= "hidden"),
            dash_breakpoints.WindowBreakpoints(
                id = EnergyLayoutID.DIV_DISPLAY_RESIZE,
                height  = 100
            ),
        html.Div(f"{CLEAR_6}",id=EnergyLayoutID.DIV_HIDDEN_SELECTED_ID,className= "hidden"),
        dcc.Location(EnergyLayoutID.URL),
        dcc.Store(EnergyLayoutID.STORE_BUILDUP_IN_SESSION,  storage_type = "session"),
        dcc.Store(EnergyLayoutID.STORE_SETTINGS_IN_LOCAL,  storage_type = "local"),
        energy_layout.navbar(),
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Row([
                        dbc.Col(select_manufacturer, xl=6),
                        dbc.Col(energy_layout.radio_thickness, xl = 6)
                    ]),
                    energy_layout.tabs
                ], xl = 8),
                dbc.Col([
                    dbc.Row(dbc.Col(energy_layout.div_buttons)),
                    dbc.Row(dbc.Col(html.Div(id=EnergyLayoutID.DIV_BUILDUP_SVG_CONTAINER),className="mb-2")),
                    dbc.Row(dbc.Col(energy_layout.card_selected_layer)),
                    dbc.Row(dbc.Col(energy_layout.card_gas_layer)),
                    dbc.Row(dbc.Col(energy_layout.card_inner_layer)),
                    
                    dbc.Row(dbc.Col(dbc.Spinner(energy_layout.results_table, color="dark", type="grow")))
                ],xl = 4)
            ]),
            energy_layout.modal_about,
            energy_layout.modal_settings,
            energy_layout.model_share
        
        ], fluid=True )],
       
    )


