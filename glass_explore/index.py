from tkinter.tix import ListNoteBook
import pyodbc
import os
import dash
from dash import dcc,html, Input, Output, State
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from glass_explore import utils

DATA_SOURCE = 'csv'

ALL = '[ALL]'

if DATA_SOURCE == 'sql':
    cxn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=F:\dev\glass-explore\.venv\data\test.mdb;')
    sql = 'select * from Glass where thickness > 5.5 and thickness < 6.5'
    df = pd.read_sql(sql,cxn)
elif DATA_SOURCE == 'csv':
    path = os.path.join('data', 'igdb.csv')
    raw_df = pd.read_csv(path, encoding='ISO-8859-1')
    raw_df = raw_df[raw_df['Thickness'].between(5.5, 8.5)]

manufacturers = np.sort(raw_df.Manufacturer.unique())
manufacturers = np.insert(manufacturers,0,ALL)

# IGDB uses nnumber for color, we waht CSS hex value.
raw_df['CssColor'] = raw_df['Color'].map(lambda x:utils.base10color_to_csshex(x))

fig = go.Figure()
fig.update_layout(
    height = 800,
)

modal_popup = dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Welcome to Glass Explore")),
                dbc.ModalBody([
                    html.P("Data from Lawrence Berkeley National Laboratory IDGB database."),
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
                {"label": "6mm", "value": 6},
                {"label": "8mm", "value": 8},
            ],
            value=6,
            id="radio-thickness",
        ),
    ]
)


app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
)
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(select_manufacturer),
        dbc.Col(radio_thickness)
    ]),
    dcc.Graph(id = "graph", figure = fig),
    modal_popup
])

@app.callback(
    Output("graph", "figure"),Output("formtext-manufacturer","children"),Output("formtext-manufacturer","color"),
    [
        Input("select-manufacturer", "value"),
        Input("radio-thickness", "value"),
    ]
)
def on_filter_change(manufacturer, thickness):

    df = raw_df[raw_df['Thickness'].between(thickness - 0.5, thickness + 0.5)]

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
    Output("modal", "is_open"),
    [Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n, is_open):
    if n:
        return not is_open
    return is_open


if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=True)  