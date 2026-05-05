#(c)2026 Jon Robinson. All Rights Reserved.

"""
entry point for the glass explore dash (multipage) app

Run this file for development. For production, use gunicorn or similar to run the server instance directly (production.py).
"""


import dash
import os
from dash import Dash, html, dcc

import dash_bootstrap_components as dbc
from flask import Flask, redirect,url_for

RAILWAY_ENVIRONMENT_NAME = os.getenv("RAILWAY_ENVIRONMENT_NAME", "").lower()
DASH_DEBUG = os.getenv("DASH_DEBUG", "").lower() in {"1", "true", "yes", "on"}
DEBUG = DASH_DEBUG or RAILWAY_ENVIRONMENT_NAME == "staging"

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

server.debug = DEBUG
app.enable_dev_tools(
    debug=DEBUG,
    dev_tools_ui=DEBUG,
    dev_tools_props_check=DEBUG,
    dev_tools_serve_dev_bundles=DEBUG,
    dev_tools_hot_reload=False,
)

app.layout = html.Div([
    dash.page_container
])

if __name__ == "__main__":
    app.run(debug=DEBUG, use_reloader=DEBUG)
