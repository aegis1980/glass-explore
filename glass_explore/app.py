#(c)2026 Jon Robinson. All Rights Reserved.

"""
entry point for the glass explore dash (multipage) app

Run this file for development. For production, use gunicorn or similar to run the server instance directly (production.py).
"""

import dash
import os
from dash import Dash, html

import dash_bootstrap_components as dbc
from flask import Flask, redirect,url_for

RAILWAY_ENVIRONMENT_NAME = os.getenv("RAILWAY_ENVIRONMENT_NAME", "").lower()
RAILWAY_STAGING = (RAILWAY_ENVIRONMENT_NAME == "staging")

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

#server.debug = DEBUG
if RAILWAY_STAGING:
    app.enable_dev_tools(
        dev_tools_ui=RAILWAY_STAGING,
        dev_tools_props_check=RAILWAY_STAGING,
        dev_tools_serve_dev_bundles=RAILWAY_STAGING,
        dev_tools_hot_reload=False,
    )

app.layout = html.Div([
    dash.page_container
])

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
