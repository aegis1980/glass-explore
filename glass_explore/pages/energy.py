
# (c)2026 Jon Robinson. All Rights Reserved.

import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd

from dash import Input, Output, State, ctx, dcc, html,clientside_callback, callback
from dash.exceptions import PreventUpdate

import dash_breakpoints

from glass_explore import (ALL_MANUFACTURERS, OG_DESCRIPTION, URL, DF_GLASS_TABLE,CLEAR_6,DEFAULT_GRAPH_GLASS, Buildup, EnergyLayoutID, WebPaths,
                           SelectedPointProps, caching, callback_helpers, energy_layout, igdb,COLORSPACE_RGB,COLORSPACE_LAB,
                           standards)

from glass_explore import callbacks_energy

manufacturers = np.sort(DF_GLASS_TABLE.Manufacturer.unique())
manufacturers = np.insert(manufacturers,0,ALL_MANUFACTURERS)


dash.register_page(
    __name__, 
    path=WebPaths.ENERGY,
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


def layout(g = None): 
    return html.Div([
        html.Div('',id=EnergyLayoutID.DIV_HIDDEN_WINDOW_HT,className= "hidden"),
            dash_breakpoints.WindowBreakpoints(
                id = EnergyLayoutID.DIV_DISPLAY_RESIZE,
                height  = 100
            ),
        html.Div(f"{CLEAR_6}",id=EnergyLayoutID.DIV_HIDDEN_SELECTED_ID,className= "hidden"),
        dcc.Location(EnergyLayoutID.URL),
        dcc.Store(EnergyLayoutID.DUMMY_FOR_CALLBACK),
        dcc.Store(EnergyLayoutID.STORE_BUILDUP_IN_SESSION,  storage_type = "session"),
        dcc.Store(EnergyLayoutID.STORE_SETTINGS_IN_LOCAL,  storage_type = "local"),
        energy_layout.navbar(),
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Search IGDB by glass name, id etc", color="secondary",size="sm", id=EnergyLayoutID.BUTTON_IGDB_SEARCH,className="mb-2"),
                            select_manufacturer
                        ], xl=6),
                        dbc.Col(energy_layout.radio_thickness, xl = 6)
                    ]),
                    energy_layout.tabs
                ], xl = 8),
                dbc.Col([
                    dbc.Row(dbc.Col(html.Div(id=EnergyLayoutID.DIV_BUILDUP_SVG_CONTAINER),className="mb-2")),
                    dbc.Row(dbc.Col(energy_layout.card_selected_layer)),
                    dbc.Row(dbc.Col(energy_layout.card_gas_layer())),
                    dbc.Row(dbc.Col(energy_layout.card_inner_layer)),
                    dbc.Row(dbc.Col(energy_layout.card_results()))
                ],xl = 4)
            ]),
            energy_layout.modal_about(),
            energy_layout.modal_glass_search(),
            energy_layout.model_share
        
        ], fluid=True )],
       
    )
