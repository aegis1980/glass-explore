from re import L
import sqlite3
import os
import dash
from dash import dcc,html, Input, Output, State
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from glass_explore import LayoutID, utils, layout, wincalc

DATA_SOURCE = 'sqlite'

ALL = '[ALL]'

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
manufacturers = np.insert(manufacturers,0,ALL)

# IGDB uses nnumber for color, we waht CSS hex value.
raw_df['CssColor'] = raw_df['Color'].map(lambda x:utils.base10color_to_csshex(x))

fig = go.Figure()
fig.update_layout(
    height = 800,
)

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
        id="select-manufacturer", value = ALL,
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
        # dbc.Row([
        #     dbc.Col(select_type),
        #     dbc.Col()
        # ]),
        dbc.Row([
            dbc.Col(select_manufacturer),
            dbc.Col(radio_thickness)
        ]),
        dcc.Graph(id = "graph", figure = fig),
        html.Div(id="click"),
        layout.modal_splash,
        layout.modal_analysis
    ])]
    )

@app.callback(
    Output("graph", "figure"),Output("formtext-manufacturer","children"),Output("formtext-manufacturer","color"),
    [
        Input("select-manufacturer", "value"),
        Input("radio-thickness", "value"),
    ]
)
def on_filter_change(manufacturer, thickness):

    df = raw_df[raw_df['Thickness'].between(thickness - 0.75, thickness + 0.75)]

    fig = go.Figure()
    if manufacturer == ALL:

        msg = f'{len(df.index)} glasses'
        color = 'darkgrey'
        fig.add_trace(
            go.Scatter(
                mode='markers',
                x=df["Tsol"],
                y=df["Tvis"],
                customdata=df,
                marker=dict(
                    color=df['CssColor'],
                    size=10,
                ),

                showlegend=False,
                hovertemplate = 
                    '<b>id</b>: %{customdata[0]}' + 
                    '<br>(<b>T_v</b>: %{y:.2f}' + ' <b>T_s</b>: %{x:.2f})'+
                    '<br>%{customdata[17]}' + 
                    '<br>%{customdata[18]}'
            )
        )
       
    else:
        mask_na = (df['Manufacturer'] != manufacturer)
        mask = (df['Manufacturer'] == manufacturer)

        if len(df[mask].index)==0:
            msg = f'No glasses from {manufacturer} with thickness, {thickness}mm'
            color = 'red'
        else:
            msg = f'{len(df[mask].index)} glasses'
            color = 'darkgrey'

        fig.add_trace(
            go.Scatter(
                mode='markers',
                x=df[mask_na]["Tsol"],
                y=df[mask_na]["Tvis"],
                marker=dict(
                    color=df[mask_na]['CssColor'],
                    opacity = 0.4,
                    size=10,
                ),
                showlegend=False,
                hoverinfo='skip'
            )
        )
        fig.add_trace(
            go.Scatter(
                mode='markers',
                x=df[mask]["Tsol"],
                y=df[mask]["Tvis"],
                customdata=df[mask],
                marker=dict(
                    color=df[mask]['CssColor'],
                    size=20,
                    line=dict(
                        color='Red',
                        width=1
                    )
                ),
                showlegend=False,
                hovertemplate = 
                    '<b>id</b>: %{customdata[0]}' + 
                    '<br>(<b>T_v</b>: %{y:.2f}' + ' <b>T_s</b>: %{x:.2f})'+
                    '<br>%{customdata[17]}' + 
                    '<br>%{customdata[18]}'
            )
        )
        
        
      #  fig = px.scatter(df[mask], x="Tsol", y="Tvis",  hover_data= ["ID","Manufacturer", "ProductName"])
    
    fig.update_layout(
        xaxis_title="T_solar",
        yaxis_title="T_visible",
        plot_bgcolor = "white",
        hovermode = 'closest'
    )

    fig.update_xaxes(
        dtick=0.1, 
        range=[0, 1],
        zeroline = False,
        fixedrange=True,
        showgrid = True,
        gridcolor='LightGrey',
        minor=dict(showgrid=True)
      #  autorange="reversed",
      #  constrain="domain",  # meanwhile compresses the xaxis by decreasing its "domain"
    ) 
    fig.update_yaxes(
        dtick=0.1, 
        range=[0, 1],
        zeroline = False,
        fixedrange=True,
        showgrid = True,
        gridcolor='LightGrey',
        minor=dict(showgrid=True)
    )

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
    Output(LayoutID.MODAL_ANALYSIS, "is_open"),
    [Input("graph", "clickData"),Input(LayoutID.MODAL_ANALYSIS_CLOSE, "n_clicks")],
    [State(LayoutID.MODAL_ANALYSIS, "is_open")]
)
def analysis_modal_control(pt_data, n , is_open):
    if n or pt_data:
        return not is_open
        
    return is_open


@app.callback(
    Output(LayoutID.MODAL_ANALYSIS_DIV_RESULTS, "children"),
    [
        Input(LayoutID.GRAPH_TS_TV, "clickData"),
        Input(LayoutID.MODAL_ANALYSIS_SELECT_GAS,"value"),
        Input(LayoutID.MODAL_ANALYSIS_INPUT_GAP,"value")
    ]
)
def on_buildup_change(pt_data, gas, gap_thickness):
    if pt_data:
        id = pt_data['points'][0]['customdata'][0]
        if id:
            gap_layer = wincalc.gap_layer(gas, gap_thickness)
            other_layer = wincalc.generic_uncoated_glass(thickness = 5, super_clear = False)
            u_result, shgc_result = wincalc.run_sim(id, gap_layer, other_layer)
        else:
            return dash.no_update, 'no glass id'


    




if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=True)  



app.title = "Glass explore (using Plotly Dash)"
