import json

import dash

from dash import Input, Output, State, ctx, dcc, html,clientside_callback, callback
from dash.exceptions import PreventUpdate


from glass_explore import (ALL_MANUFACTURERS, OG_DESCRIPTION, URL, DF_GLASS_TABLE, DEFAULT_GRAPH_GLASS,Buildup, LayoutID,
                           SelectedPointProps, caching, callback_helpers, igdb,COLORSPACE_RGB,COLORSPACE_LAB,
                           layout, mywincalc, standards, svg_glass, utils, glass_model_helpers)

from glass_model import InsulatedGlass

clientside_callback(
    """
    function(h,w) {
        ht = self.innerHeight - 245;
        s = "height:" + ht + "px";
        document.getElementById('graph-ts-tv').setAttribute("style",s);
        return window.dash_clientside.no_update;
    }
    """,
    Output(LayoutID.DIV_HIDDEN_WINDOW_HT, "children"),
    Input(LayoutID.DIV_DISPLAY_RESIZE,"height"),
    Input(LayoutID.DIV_DISPLAY_RESIZE,"width")
)


@callback(
    Output(LayoutID.GRAPH_IGDB, "figure"),Output("formtext-manufacturer","children"), Output("formtext-manufacturer","color"),
    Input(LayoutID.TABS, "active_tab"),
    Input("select-manufacturer", "value"),
    Input("radio-thickness", "value"),
    State(LayoutID.DIV_HIDDEN_SELECTED_ID, 'children'),  
)
def update_igdb_data_display(active_tabs, manufacturer, thickness,selected_id):
    out_fig = dash.no_update
    if active_tabs == LayoutID.TAB_GRAPH_TS_TV:
        df = caching.thickness_cached_df(thickness)
        out_fig, out_msg, out_msgcolor = callback_helpers.populate_graph_ts_tv(selected_id,df, manufacturer,thickness)
    else:
        df = caching.thickness_cached_df(thickness)
        if active_tabs == LayoutID.TAB_GRAPH_RGB:
            color_space = COLORSPACE_RGB
        else:
            color_space = COLORSPACE_LAB

        out_fig, out_msg, out_msgcolor = callback_helpers.populate_graph_colorspace(selected_id,df, manufacturer,thickness, color_space)

    return out_fig, out_msg, out_msgcolor


@callback(
    Output(LayoutID.SELECT_OPTICAL_STANDARD,"options"),
    Input(LayoutID.MODAL_SETTINGS, "is_open"),
    Input(LayoutID.CHECKBOX_ADVANCED_OPTICAL_STANDARD, "value"),
    State(LayoutID.STORE_SETTINGS_IN_LOCAL,'data')
)
def populate_standards_select(settings_open,inc_advanced,stored_settings):
    return callback_helpers.populate_standards(include_interesting=inc_advanced)


@callback(
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


@callback(
    Output(LayoutID.MODAL_SHARE, "is_open"),
    [Input(LayoutID.MODAL_SHARE_CLOSE, "n_clicks"),Input(LayoutID.BUTTON_SHARE, "n_clicks")],
    [State(LayoutID.MODAL_SHARE, "is_open")],
)
def toggle_share_modal(n1, n2, is_open):
    if n1 :
        return not is_open
    if n2 :
        return not is_open
    return is_open


@callback(
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


@callback(
    Output(LayoutID.DIV_HIDDEN_SELECTED_ID, 'children'),  
    Input(LayoutID.GRAPH_IGDB, "clickData"),
    State(LayoutID.TABS, "active_tab")
)
def store_in_hidden_div(pt_data, active_tab):
    if pt_data:
        id = pt_data['points'][0]['customdata'][0]
        return id
    else:
        raise PreventUpdate

    
@callback(
    Output(LayoutID.STORE_BUILDUP_IN_SESSION, 'data'),  
    Input(LayoutID.GRAPH_IGDB, "clickData"),
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
    
    buildup[Buildup.SOLID_LAYERS][0]['color'] = DF_GLASS_TABLE.loc[int(id)]['CssColor']
    buildup[Buildup.SOLID_LAYERS][0]['flipped'] = flipped
    utils.populate_buildup_with_glass_props(buildup,props_outer,0)

    
    props_inner = mywincalc.generic_uncoated_glass_props(int(inner_thickness),inner_substrate == 'ultraclear') # note inntersubstrate taking a bool!
    buildup[Buildup.SOLID_LAYERS][1]['color'] = DF_GLASS_TABLE.loc[props_inner['NFRC_ID']]['CssColor']
    buildup[Buildup.SOLID_LAYERS][1]['flipped'] = False
    utils.populate_buildup_with_glass_props(buildup,props_inner,1)

    buildup[Buildup.GAP_LAYERS][0]['gas'] = gas
    buildup[Buildup.GAP_LAYERS][0]['thickness'] = gap_thickness

    return json.dumps(buildup)


@callback(
    Output(LayoutID.DIV_BUILDUP_SVG_CONTAINER,"children"),
    Input(LayoutID.STORE_BUILDUP_IN_SESSION,"modified_timestamp"),
    State(LayoutID.STORE_BUILDUP_IN_SESSION,"data")
)
def update_buildup_svg(ts, buildup):
    if ts is None or buildup is None:
        raise PreventUpdate

    return svg_glass.generate_buildup(json.loads(buildup))


@callback(
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


@callback(
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


@callback(
    Output(LayoutID.LINK_GSTR,"children"),
    Input(LayoutID.STORE_BUILDUP_IN_SESSION,"modified_timestamp"),
    State(LayoutID.STORE_BUILDUP_IN_SESSION,"data"),
    State(LayoutID.URL, "href")
)
def update_gstr_url(ts, buildup, href):
    if ts is None or buildup is None:
        raise PreventUpdate
    _buildup = json.loads(buildup)
   
    lites = glass_model_helpers.lites_from_dict(_buildup)
    gases = glass_model_helpers.gaslayers_from_dict(_buildup)

    igu = InsulatedGlass(lites,gases)

    gs = igu.to_gstr(False)
    root_url = callback_helpers.get_root_netloc(href)
    return f'{root_url}/{gs}'

# add callback for toggling the collapse on small screens
@callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@callback(
    Output(LayoutID.GRAPH_IGDB, "extendData"),
    Input(LayoutID.GRAPH_IGDB, "clickData"),
    State(LayoutID.GRAPH_IGDB, "figure"),
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



@callback(Output(LayoutID.GRAPH_IGDB, "clickData"),
    Input(LayoutID.URL, 'href'),
    State(LayoutID.URL,'pathname' ))
def onload_parse_url(href, pathname):
    """
    Mocks a user data point click on the default loadup glass
    to trigger analysis on first load of webapp.

    Selected point in graph is not triggered by this - hard coded in hidden div.
    """
    if href is None:
        raise PreventUpdate
    else:
        if not pathname or pathname == '/':
            return {'points' :[{'customdata': DEFAULT_GRAPH_GLASS}]}
        else:
            #print(pathname)
            return {'points' :[{'customdata': DEFAULT_GRAPH_GLASS}]}