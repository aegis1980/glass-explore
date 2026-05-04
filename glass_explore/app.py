#(c)2026 Jon Robinson. All Rights Reserved.

"""
entry point for the glass explore dash (multipage) app

Run this file for development. For production, use gunicorn or similar to run the server instance directly (production.py).
"""


import dash
from dash import Dash, html, dcc

import dash_bootstrap_components as dbc
from flask import Flask, redirect,url_for

server = Flask(__name__)

@server.route('/')
def index_redirect():
    return redirect('/energy')

app = Dash(
    __name__, 
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP,dbc.icons.BOOTSTRAP],
    server=server,
    assets_external_path="/",
    suppress_callback_exceptions=True,
    compress=True
)

app.layout = html.Div([
    dash.page_container
])

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)  