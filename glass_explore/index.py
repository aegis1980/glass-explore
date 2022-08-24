import sqlite3
import os

import pandas as pd
import numpy as np


import dash
from dash import dcc,html, Input, Output, State
import dash_bootstrap_components as dbc

import plotly.graph_objects as go


from glass_explore import LayoutID, svg_glass, utils, layout, wincalc, callback_helpers, ALL_MANUFACTURERS   ,GRAPHTYPE_TS_TV,GRAPHTYPE_LAB,GRAPHTYPE_RGB
from glass_explore.results_printer import print_system_optical_results_side

DATA_SOURCE = 'sqlite'


if DATA_SOURCE == 'pyodbc':
    import pyodbc
    path = os.path.join('data','igdb.mdb')
    if os.name == 'nt':
        cxn_str = f'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};'
    else:
        cxn_str = f'DRIVER={{mdb-sql}};DBQ={path};' #nb This doent actaully work in linux (on Heruko)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              

    cxn = pyodbc.connect(cxn_str)
    sql = 'select * from Glass' # where thickness > 5.5 and thickness < 6.5'
    raw_df = pd.read_sql(sql,cxn)
elif DATA_SOURCE == 'sqlite':
    path = os.path.join('data', 'igdb.sqlite')
    # Create a SQL connection to our SQLite database
    cxn = sqlite3.connect(path)
    sql = 'select * from Glass' # where thickness > 5.5 and thickness < 6.5'
    raw_df = pd.read_sql(sql,cxn)

elif DATA_SOURCE == 'csv':
    path = os.path.join('data', 'igdb.csv')
    raw_df = pd.read_csv(path, encoding='ISO-8859-1')
    #raw_df = raw_df[raw_df['Thickness'].between(5.5, 8.5)]

manufacturers = np.sort(raw_df.Manufacturer.unique())
manufacturers = np.insert(manufacturers,0,ALL_MANUFACTURERS)

# IGDB uses number for color, we what CSS hex value.
raw_df['CssColor'] = raw_df['Color'].map(lambda x:utils.base10color_to_csshex(x))
raw_df['rgb'] = raw_df['CssColor'].map(lambda x:utils.csshex_to_rgb(x))
raw_df[['RColor','GColor','BColor']] = raw_df['rgb'].apply(pd.Series)
raw_df['lab'] = raw_df['rgb'].map(lambda x:utils.rgb_to_lab(x))
raw_df[['lColor','aColor','bColor']] = raw_df['lab'].apply(pd.Series)
raw_df.drop(columns=['rgb', 'lab'])
# select_type = html.Div([
#     dbc.Label("Glazing type:"),
#     dbc.Select(
#         id="select-type", value = 'dgu',
#         options=[
#             {"label": "Single-glazed", "value": "sgu"},
#             {"label": "Double-glazed", "value": "dgu"},
#         ]
#     ),
# ])

select_manufacturer = html.Div([
    dbc.Label("Manufacturer:"),
    dbc.Select(
        id="select-manufacturer", value = ALL_MANUFACTURERS,
        options=[{"label": m, "value": m} for m in manufacturers]
    ),
    dbc.FormText(id = 'formtext-manufacturer',color='red'),
])

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


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
)

app.layout = html.Div([
    layout.navbar(app),
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Row([
                    dbc.Col(select_manufacturer),
                    dbc.Col(radio_thickness)
                ]),
                layout.buttongroup_graphs,
                layout.graphs()
            ], width = 8),
            dbc.Col([
                dbc.Row(dbc.Col(svg_glass.generate_buildup())),
                dbc.Row(dbc.Col(layout.card_selected_layer)),
                dbc.Row(dbc.Col(layout.card_gas_layer)),
                dbc.Row(dbc.Col(layout.card_other_layer)),
                dbc.Row(dbc.Col(layout.results_table))
            ],width = 4)
        ]),
        layout.modal_splash,
    ], fluid=True )])


@app.callback(
    Output(LayoutID.GRAPH, "figure"),Output("formtext-manufacturer","children"),Output("formtext-manufacturer","color"),
    [
        Input(LayoutID.BUTTONGROUP_GRAPHTYPE, "value"),
        Input("select-manufacturer", "value"),
        Input("radio-thickness", "value"),
    ]
)
def update_graphing(graph_type, manufacturer, thickness):

    df = raw_df[raw_df['Thickness'].between(thickness - 0.75, thickness + 0.75)]

    if graph_type == GRAPHTYPE_TS_TV:
        fig, msg, color = callback_helpers.graphing_ts_tv(df, manufacturer,thickness)
    else:
        fig, msg, color = callback_helpers.graphing_3d_colorspace(df, manufacturer,thickness, graph_type)

    return fig, msg, color




@app.callback(
    Output(LayoutID.MODAL_SPLASH, "is_open"),
    [Input(LayoutID.MODAL_SPLASH_CLOSE, "n_clicks")],
    [State(LayoutID.MODAL_SPLASH, "is_open")],
)
def toggle_modal(n, is_open):
    if n :
        return not is_open
    return is_open


@app.callback(
    Output(LayoutID.DIV_OUTERLITE_PRODUCT,"children"),
    Output(LayoutID.TABLE_CELL_UVALUE, "children"),
    Output(LayoutID.TABLE_CELL_SHGC,"children"),
    Output(LayoutID.TABLE_CELL_TVIS,"children"),
    Output(LayoutID.TABLE_CELL_ROUT,"children"),
    Output(LayoutID.TABLE_CELL_RIN,"children"),

    [
        Input(LayoutID.GRAPH, "clickData"),
        Input(LayoutID.SELECT_GAS,"value"),
        Input(LayoutID.INPUT_GAP,"value"),
        Input(LayoutID.CHECKBOX_FLIP_OUTERLAYER, "value"),
    ]
)
def on_buildup_change(pt_data, gas, gap_thickness,flipped):
    
    if pt_data:
        id = pt_data['points'][0]['customdata'][0]
        if id:
            gap_layer = wincalc.gap_layer(gas, gap_thickness)
            
            other_layer = wincalc.generic_uncoated_glass(thickness = 5, super_clear = False)
            props,glazing_system_u_environment, glazing_system_shgc_environment = wincalc.run_sim(id,flipped, gap_layer, other_layer)
        else:
            return dash.no_update, 'no glass id'
        
        optical = glazing_system_u_environment.optical_method_results("PHOTOPIC").system_results
        
        outer_layer_info = f"""
            {props['ProductName']}
            ({props['Manufacturer']})
        """

        uvalue = f'{glazing_system_u_environment.u(0,0):.1f}'
        shgc = f'{glazing_system_shgc_environment.shgc(0,0):.2f}'
        tvis = f'{optical.front.transmittance.direct_hemispherical:.2f}'
        rout = f'{optical.front.reflectance.direct_hemispherical:.2f}'
        rin = f'{optical.back.reflectance.direct_hemispherical:.2f}'
      
        return outer_layer_info, uvalue,shgc,tvis,rout,rin


app.title = "Glass explore (using Plotly Dash)"

if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=True)  



