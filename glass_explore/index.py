import pyodbc
import os
import dash
from dash import dcc,html, Input, Output, State
import dash_bootstrap_components as dbc
import numpy as np
import plotly.express as px
import pandas as pd
from glass_explore import utils

data = 'csv'

if data == 'sql':
    cxn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=F:\dev\glass-explore\.venv\data\test.mdb;')
    sql = 'select * from Glass where thickness > 5.5 and thickness < 6.5'
    df = pd.read_sql(sql,cxn)
elif data == 'csv':
    path = os.path.join('data', 'igdb.csv')
    raw_df = pd.read_csv(path, encoding='ISO-8859-1')
    df = raw_df[raw_df['Thickness'].between(5.5, 6.5)]
    

manufacturers = np.sort(df.Manufacturer.unique())
manufacturers = np.insert(manufacturers,0,"[ALL]")


df['Color'] = df['Color'].map(lambda x:utils.base10color_to_csshex(x))
fig = px.scatter(df, x="Tsol", y="Tvis",  hover_data= ["ID","Manufacturer", "ProductName"])
fig.update_traces(marker=dict(color = df['Color']),
                selector=dict(mode='markers'))

fig.layout.plot_bgcolor = 'white'

def query_data():
    df = pd.read_sql(sql,cxn)
    df['Color'] = df['Color'].map(lambda x:utils.base10color_to_csshex(x))
    fig = px.scatter(df, x="Tsol", y="Tvis",  hover_data= ["ID","Manufacturer", "ProductName"])
    fig.update_traces(marker=dict(color = df['Color']),
                    selector=dict(mode='markers'))



manufacturer_select = html.Div([
    dbc.Label("Choose manufacturer:"),
    dbc.Select(
        id="select-manufacturer",
        options=[{"label": m, "value": m} for m in manufacturers]
    )
])


app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = dbc.Container([
    manufacturer_select,
    dcc.Graph(id = "graph", figure=fig)
])




@app.callback(
    Output("graph", "figure"),
    [
        Input("select-manufacturer", "value"),
    ],
    [
        State("graph", "figure")
    ]
)
def on_filter_change(manufacturer, figure):
    print(manufacturer)
    figure.update_traces(marker=dict(color = df['Color'],
                            line=dict(width=2,
                                        color='DarkSlateGrey')),
                    selector=dict(mode='markers'))
    return figure





if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=True)  