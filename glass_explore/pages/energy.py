
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


dash.register_page(
    __name__, 
    path=WebPaths.ENERGY,
    title = "Glass Explore | Energy"
)




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
        dcc.Store(EnergyLayoutID.STORE_GSTR_FROM_URL),
        dcc.Store(EnergyLayoutID.STORE_BUILDUP_IN_SESSION,  storage_type = "session"),
        dcc.Store(EnergyLayoutID.STORE_SETTINGS_IN_LOCAL,  storage_type = "local"),
        energy_layout.navbar(),
        dbc.Container([
            dbc.Row([
                # Left column - search, manufacturer, thickness and graph tabs
                dbc.Col([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Search IGDB by glass name, id etc", color="secondary",size="sm", id=EnergyLayoutID.BUTTON_IGDB_SEARCH,className="mb-2"),
                        ], width=12),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            energy_layout.select_manufacturer()
                        ], xl=6),
                        dbc.Col(energy_layout.select_thickness(), xl = 6)
                    ],className="mb-2"),
                    energy_layout.graph_tabs()
                ], xl = 8, className="d-flex flex-column vh-100 border-end"),

                # Right column - buildup svg and layer cards including results
                dbc.Col([
                    dbc.Row([   
                        dbc.Col([
                            html.Div(id=EnergyLayoutID.DIV_BUILDUP_SVG_CONTAINER),
                            dbc.Switch(
                                id=EnergyLayoutID.SWITCH_COATED_GLASS_SIDE,
                                value=False,
                                className="static-switch",
                            ),
                            dbc.Popover(
                                "Swap position of coated layer in IGU outside <-> inside",
                                target=EnergyLayoutID.SWITCH_COATED_GLASS_SIDE,
                                body=True,
                                trigger="hover",
                                placement="bottom"
                            ),
                        ],width=10,className="d-flex flex-column align-items-center"),
                        dbc.Col([
                             dbc.Button("", color="light", className="me-1 bi bi-share-fill", id=EnergyLayoutID.BUTTON_SHARE, size="sm"),
                        ],width=2,className="text-end"),
                        ],
                        className="mb-2"
                    ),
                    dbc.Row(dbc.Col(energy_layout.card_coated_layer())),
                    dbc.Row(dbc.Col(energy_layout.card_gas_layer())),
                    dbc.Row(dbc.Col(energy_layout.card_noncoated_layer())),
                    dbc.Row(dbc.Col(energy_layout.card_results()))
                ],
                id= EnergyLayoutID.COLUMN_RHS,
                xl = 4)
            ]),
            energy_layout.modal_about(),
            energy_layout.modal_glass_search(),
            energy_layout.modal_share()
        
        ], fluid=True )],
       
    )
