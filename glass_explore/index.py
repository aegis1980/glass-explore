import json
import time

import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
from dash import Input, Output, State, ctx, dcc, html
from dash.exceptions import PreventUpdate

from glass_explore import (ALL_MANUFACTURERS, OG_DESCRIPTION, RAW_DF, Buildup, LayoutID,
                           SelectedPointProps, caching, callback_helpers, igdb,COLORSPACE_RGB,COLORSPACE_LAB,
                           layout, mywincalc, standards, svg_glass, utils)

manufacturers = np.sort(RAW_DF.Manufacturer.unique())
manufacturers = np.insert(manufacturers,0,ALL_MANUFACTURERS)


select_manufacturer = html.Div([
    dbc.Label("Manufacturer:"),
    dbc.Select(
        id="select-manufacturer", value = ALL_MANUFACTURERS,
        options=[{"label": m, "value": m} for m in manufacturers]
    ),
    dbc.FormText(id = 'formtext-manufacturer',color='red'),
])


CLEAR_6 = 103
DEFAULT_GRAPH_GLASS = RAW_DF.loc[CLEAR_6]


#my_bcm = caching.background_callback_manager()

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    #background_callback_manager=my_bcm,
    index_string=dash.dash._default_index.replace('<html>', '<html lang="en" prefix="og: http://ogp.me/ns#">'),
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"property" : "og:title", "content": "Glass Explore"},
        {"name":"image" ,  "property":"og:image" ,  "content":"https://floatingintheclouds.com/wp-content/uploads/2022/09/glass-explore.png" },
        {"name":"author" ,  "content":"Jon Robinson" },
        {"property" : "og:description", "content": OG_DESCRIPTION},
        {"property" : "og:url", "content": "http://glass-explore.floatingintheclouds.com"}
    ],
)

app.layout = html.Div([
    html.Div(f"{CLEAR_6}",id=LayoutID.DIV_HIDDEN_SELECTED_ID,className= "hidden"),
    dcc.Location(LayoutID.URL),
    dcc.Store(LayoutID.STORE_BUILDUP_IN_SESSION,  storage_type = "session"),
    dcc.Store(LayoutID.STORE_SETTINGS_IN_LOCAL,  storage_type = "local"),
    layout.navbar(app),
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Row([
                    dbc.Col(select_manufacturer, xl=6),
                    dbc.Col(layout.radio_thickness, xl = 6)
                ]),
                layout.tabs
            ], xl = 8),
            dbc.Col([
                dbc.Row(dbc.Col(html.Div(id=LayoutID.DIV_BUILDUP_SVG_CONTAINER),className="mb-2")),
                dbc.Row(dbc.Col(layout.card_selected_layer)),
                dbc.Row(dbc.Col(layout.card_gas_layer)),
                dbc.Row(dbc.Col(layout.card_other_layer)),
                dbc.Row(dbc.Col(dbc.Spinner(layout.results_table, color="dark", type="grow")))
            ],xl = 4)
        ]),
        layout.modal_about(app),
        layout.modal_settings,
       
    ], fluid=True )])


@app.callback(
    Output(LayoutID.GRAPH, "figure"),Output("formtext-manufacturer","children"), Output("formtext-manufacturer","color"),
    Input(LayoutID.TABS, "active_tab"),
    Input("select-manufacturer", "value"),
    Input("radio-thickness", "value"),
    State(LayoutID.DIV_HIDDEN_SELECTED_ID, 'children'),  
)
def update_graph(active_tabs, manufacturer, thickness,selected_id):
    df = caching.thickness_cached_df(thickness)
    if active_tabs == LayoutID.TAB_DATATABLE:
        raise PreventUpdate
    elif active_tabs == LayoutID.TAB_GRAPH_TS_TV:
        fig, msg, color = callback_helpers.populate_graph_ts_tv(selected_id,df, manufacturer,thickness)
    else:
        if active_tabs == LayoutID.TAB_GRAPH_RGB:
            color_space = COLORSPACE_RGB
        else:
            color_space = COLORSPACE_LAB
        fig, msg, color = callback_helpers.populate_graph_colorspace(selected_id,df, manufacturer,thickness, color_space)

    return fig, msg, color


@app.callback(
    Output(LayoutID.DATATABLE_OUTERLITE, "data"),
    Input(LayoutID.TABS, "active_tab"),
    Input("select-manufacturer", "value"),
    Input("radio-thickness", "value"),
    State(LayoutID.DIV_HIDDEN_SELECTED_ID, 'children'),  
)
def update_datatable(active_tabs, manufacturer, thickness,selected_id):
    df = caching.thickness_cached_df(thickness)
    if active_tabs == LayoutID.TAB_DATATABLE:
        data = callback_helpers.populate_datatable(selected_id,df, manufacturer,thickness)
    else:
        raise PreventUpdate
    print(data)
    return data


@app.callback(
    Output(LayoutID.SELECT_OPTICAL_STANDARD,"options"),
    [Input(LayoutID.MODAL_SETTINGS, "is_open"),Input(LayoutID.CHECKBOX_ADVANCED_OPTICAL_STANDARD, "value")],
    [State(LayoutID.STORE_SETTINGS_IN_LOCAL,'data')]
)
def populate_standards_select(settings_open,inc_advanced,stored_settings):
    return callback_helpers.populate_standards(include_interesting=inc_advanced)


@app.callback(
    Output(LayoutID.MODAL_ABOUT, "is_open"),
    [Input(LayoutID.MODAL_ABOUT_CLOSE, "n_clicks"),Input(LayoutID.NAVLINK_ABOUT, "n_clicks")],
    [State(LayoutID.MODAL_ABOUT, "is_open")],
)
def toggle_about_modal(n1, n2, is_open):
    if n1 :
        return not is_open
    if n2 :
        return not is_open
    return is_open


@app.callback(
    Output(LayoutID.MODAL_SETTINGS, "is_open"),
    [Input(LayoutID.MODAL_SETTINGS_CLOSE, "n_clicks"),Input(LayoutID.NAVLINK_SETTINGS, "n_clicks")],
    [State(LayoutID.MODAL_SETTINGS, "is_open")],
)
def toggle_settings_modal(n1, n2, is_open):
    if n1 :
        return not is_open
    if n2 :
        return not is_open
    return is_open


@app.callback(
    Output(LayoutID.DIV_HIDDEN_SELECTED_ID, 'children'),  
    Input(LayoutID.GRAPH, "clickData"),
)
def store_in_hidden_div(pt_data):
    if pt_data:
        id = pt_data['points'][0]['customdata'][0]
        return id
    else:
        raise PreventUpdate

    
@app.callback(
    Output(LayoutID.STORE_BUILDUP_IN_SESSION, 'data'),  
    Input(LayoutID.GRAPH, "clickData"),
    Input(LayoutID.CHECKBOX_FLIP_OUTERLAYER, "value"),
    Input(LayoutID.SELECT_GAS,"value"),
    Input(LayoutID.INPUT_GAP,"value"),
    Input(LayoutID.SELECT_INNERLAYER_SUBSTRATE,"value"), # clear or ultraclear
    Input(LayoutID.SELECT_INNERLAYER_THICKNESS,"value")

)
def glass_to_store(pt_data,flipped, gas, gap_thickness, inner_substrate, inner_thickness):
    """
    Stores current user selected buildup in session storage.
    """
    buildup = {}
    buildup[Buildup.SOLID_LAYERS] = [{},{}]
    buildup[Buildup.GAP_LAYERS] = [{}]
    if pt_data:
        id = pt_data['points'][0]['customdata'][0]
    else:
        return dash.no_update, 'no glass id'

    props_outer = igdb.lookup_glass_props(id)
    
    buildup[Buildup.SOLID_LAYERS][0]['color'] = RAW_DF.loc[int(id)]['CssColor']
    buildup[Buildup.SOLID_LAYERS][0]['flipped'] = flipped
    utils.populate_buildup_with_glass_props(buildup,props_outer,0)

    
    props_inner = mywincalc.generic_uncoated_glass_props(int(inner_thickness),inner_substrate == 'ultraclear')
    buildup[Buildup.SOLID_LAYERS][1]['color'] = RAW_DF.loc[props_inner['NFRC_ID']]['CssColor']
    buildup[Buildup.SOLID_LAYERS][1]['flipped'] = False
    utils.populate_buildup_with_glass_props(buildup,props_inner,1)

    buildup[Buildup.GAP_LAYERS][0]['gas'] = gas
    buildup[Buildup.GAP_LAYERS][0]['thickness'] = gap_thickness

    return json.dumps(buildup)


@app.callback(
    Output(LayoutID.DIV_BUILDUP_SVG_CONTAINER,"children"),
    Input(LayoutID.STORE_BUILDUP_IN_SESSION,"modified_timestamp"),
    State(LayoutID.STORE_BUILDUP_IN_SESSION,"data")
)
def update_buildup_svg(ts, buildup):
    if ts is None or buildup is None:
        raise PreventUpdate

    return svg_glass.generate_buildup(json.loads(buildup))


@app.callback(
    Output(LayoutID.DIV_OUTERLITE_PRODUCT,"children"),
    Input(LayoutID.STORE_BUILDUP_IN_SESSION,"modified_timestamp"),
    State(LayoutID.STORE_BUILDUP_IN_SESSION,"data")
)
def update_outer_lite_productdata(ts, buildup):
    if ts is None or buildup is None:
        raise PreventUpdate
    buildup = json.loads(buildup)
    props = buildup[Buildup.SOLID_LAYERS][0]['props']

    outer_layer_info = f"""
            {props['ProductName']}
            ({props['Manufacturer']})
        """ 

    return outer_layer_info   


@app.callback(
    Output(LayoutID.TABLE_CELL_UVALUE, "children"),
    Output(LayoutID.TABLE_CELL_SHGC,"children"),
    Output(LayoutID.TABLE_CELL_TVIS,"children"),
    Output(LayoutID.TABLE_CELL_ROUT,"children"),
    Output(LayoutID.TABLE_CELL_RIN,"children"),
    Output(LayoutID.TABLE_CELL_COLOR_TRANS,"style"),
    Output(LayoutID.TABLE_CELL_COLOR_REFL,"style"),
    Input(LayoutID.STORE_BUILDUP_IN_SESSION,"modified_timestamp"),
    State(LayoutID.STORE_BUILDUP_IN_SESSION,"data")
)
def run_analysis_and_update_results(ts, buildup):
    if ts is None or buildup is None:
        raise PreventUpdate
    buildup = json.loads(buildup)

    glazing_system_u_environment, glazing_system_shgc_environment= mywincalc.run_analysis(buildup)

    optical = glazing_system_u_environment.optical_method_results("PHOTOPIC").system_results
    
    uvalue = f'{glazing_system_u_environment.u():.3f}'
    shgc = f'{glazing_system_shgc_environment.shgc():.3f}'
    tvis = f'{optical.front.transmittance.direct_hemispherical:.3f}'
    rout = f'{optical.front.reflectance.direct_hemispherical:.3f}'
    rin = f'{optical.back.reflectance.direct_hemispherical:.3f}'

    color_t = glazing_system_u_environment.color().system_results.front.transmittance.direct_direct.rgb
    color_r = glazing_system_u_environment.color().system_results.front.reflectance.direct_direct.rgb
    color_t = utils.rgb_to_csshex(color_t.R,color_t.G,color_t.B)
    color_r = utils.rgb_to_csshex(color_r.R,color_r.G,color_r.B)

    return uvalue,shgc,tvis,rout,rin,{'background-color' : color_t},{'background-color' : color_r}


# add callback for toggling the collapse on small screens
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


# app.clientside_callback(
#     """
#     function(click_data, figure, graph_type) {
    
#         if (click_data === undefined){
#             return window.dash_clientside.no_update;
#         }

#         if (figure === undefined || figure['data'].length == 0){
#             return window.dash_clientside.no_update;
#         }

#         point = click_data['points'][0];

#         if (graph_type == 1){
#             hilight = {
#                 'x' : [[point['x']]],
#                 'y' : [[point['y']]],
#                 'marker.color' :[[point['marker.color']]]
#             }
#         } else {
#             hilight = {
#                 'x' : [[point['x']]],
#                 'y' : [[point['y']]],
#                 'z' : [[point['z']]],
#                 'marker.color' :[[point['marker.color']]]
#             }
#         }

#         last_trace_index = figure['data'].length-1; //will always be the last trace

#         return [hilight,[last_trace_index],1];
#     }
#     """,
#     Output(LayoutID.GRAPH, "extendData"),
#     Input(LayoutID.GRAPH, "clickData"),
#     State(LayoutID.GRAPH, "figure"),
#     State(LayoutID.TABS,"active_tab" )
# )

@app.callback(
    Output(LayoutID.GRAPH, "extendData"),
    Input(LayoutID.GRAPH, "clickData"),
    State(LayoutID.GRAPH, "figure"),
    State(LayoutID.TABS,"active_tab" )
)
def highlight_point_on_graph(click_data, figure, active_tab):
    """
    uses extend data to hlighlight seleced point without redrawing graph.
    """
    if not click_data:
        raise PreventUpdate
    if len(figure['data']) == 0: #ie graph is empty - no traces
        raise PreventUpdate
    point = click_data['points'][0]
    if active_tab == LayoutID.TAB_GRAPH_TS_TV:
        hilight = {
            'x' : [[point['x']]],
            'y' : [[point['y']]],
            'marker.color' :[[point['marker.color']]],
        }
    else:
        hilight = {
            'x' : [[point['x']]],
            'y' : [[point['y']]],
            'z' : [[point['z']]],
            'marker.color' :[[point['marker.color']]],
        }
    last_trace_index = len(figure['data'])-1 #will always be the last trace

    return [hilight,[last_trace_index],1]



@app.callback(Output(LayoutID.GRAPH, "clickData"),
              [Input(LayoutID.URL, 'href')])
def onload_default_glass_select(href):
    """
    Mocks a user data point click on the default loadup glass
    to trigger analysis on first load of webapp.

    Selected point in graph is not triggered by this - hard coded in hidden div.
    """
    if href is None:
        raise PreventUpdate
    else:
        return {'points' :[{'customdata': DEFAULT_GRAPH_GLASS}]}


app.title = "Glass Explore"


if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=True)  



