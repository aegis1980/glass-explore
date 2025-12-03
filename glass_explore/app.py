import dash
from dash import Dash, html, dcc

import dash_bootstrap_components as dbc
from flask import Flask, redirect,url_for

server = Flask(__name__)

@server.route('/')
def index_redirect():
    return redirect('/energy/')

app = Dash(
    __name__, 
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    server=server,
    assets_external_path="/"
)

app.layout = html.Div([
    dash.page_container
])

if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=True)  