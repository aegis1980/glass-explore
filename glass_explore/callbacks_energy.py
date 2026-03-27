#(c)2026 Jon Robinson. All Rights Reserved.

import json
import urllib.parse

import dash

from dash import Input, Output, State, clientside_callback, callback, no_update, html
from dash.exceptions import PreventUpdate

import pandas as pd


from glass_explore import (ALL_MANUFACTURERS, OG_DESCRIPTION, URL, DF_GLASS_TABLE, DEFAULT_GRAPH_GLASS,Buildup, EnergyLayoutID, WebPaths,
                           caching as caching, callback_helpers, igdb,COLORSPACE_RGB,COLORSPACE_LAB,
                           mywincalc, standards, svg_glass, utils, glass_model_helpers)

import glass_explore
from glass_explore.glass_model import (GlassBuildup, InsulatedGlass)

clientside_callback(
    """
    function(h,w) {
        ht = self.innerHeight - 245;
        s = "height:" + ht + "px";
        document.getElementById('graph-ts-tv').setAttribute("style",s);
        return window.dash_clientside.no_update;
    }
    """,
    Output(EnergyLayoutID.DIV_HIDDEN_WINDOW_HT, "children"),
    Input(EnergyLayoutID.DIV_DISPLAY_RESIZE,"height"),
    Input(EnergyLayoutID.DIV_DISPLAY_RESIZE,"width")
)


@callback(
    Output(EnergyLayoutID.GRAPH_IGDB, "figure"),
    Output("formtext-manufacturer","children"), 
    Output("formtext-manufacturer","color"),
    Input(EnergyLayoutID.TABS, "active_tab"),
    Input("select-manufacturer", "value"),
    Input("radio-thickness", "value"),
    State(EnergyLayoutID.DIV_HIDDEN_SELECTED_ID, 'children'),  
)
def update_igdb_data_display(active_tabs, manufacturer, thickness,selected_id):


    out_fig = dash.no_update
    df = caching.thickness_cached_df(thickness)
    if active_tabs == EnergyLayoutID.TAB_GRAPH_TS_TV:
        out_fig, out_msg, out_msgcolor = callback_helpers.populate_graph_ts_tv(selected_id,df, manufacturer,thickness)
    else:
        if active_tabs == EnergyLayoutID.TAB_GRAPH_RGB:
            color_space = COLORSPACE_RGB
        else:
            color_space = COLORSPACE_LAB

        out_fig, out_msg, out_msgcolor = callback_helpers.populate_graph_colorspace(selected_id,df, manufacturer,thickness, color_space)

    return out_fig, out_msg, out_msgcolor

# CALLBACK 2: Handles the snappy highlight (Patch Only)
@callback(
    Output(EnergyLayoutID.GRAPH_IGDB, "figure", allow_duplicate=True),
    Input(EnergyLayoutID.GRAPH_IGDB, "clickData"),
    prevent_initial_call=True
)
def fast_highlight(click_data):

    point = click_data['points'][0]
    new_x = [point.get("x")]
    new_y = [point.get("y")]
    new_z = [point.get("z")] if "z" in point else None

    new_color = point.get("marker.color") or point.get("marker", {}).get("color")
    
    p = dash.Patch()

    # Target the last trace directly via index -1 which is the dedicated highlight trace
    # Update coordinates
    p["data"][-1]["x"] = new_x
    p["data"][-1]["y"] = new_y
    if new_z is not None:
        p["data"][-1]["z"] = new_z
    
    # Ensure marker dictionary exists before assignment to avoid potential UI errors
    p["data"][-1]["marker"]["color"] = [new_color]
    
    return p


@callback(
    Output(EnergyLayoutID.MODAL_ABOUT, "is_open"),
    [Input(EnergyLayoutID.MODAL_ABOUT_CLOSE, "n_clicks"),Input(EnergyLayoutID.NAVLINK_ABOUT, "n_clicks")],
    [State(EnergyLayoutID.MODAL_ABOUT, "is_open")],
)
def toggle_about_modal(n1, n2, is_open):
    if n1 :
        return not is_open
    if n2 :
        return not is_open
    return is_open



@callback(
    Output(EnergyLayoutID.MODAL_SEARCH_IGDB, "is_open"),
    [Input(EnergyLayoutID.MODAL_SEARCH_IGDB_CLOSE, "n_clicks"),Input(EnergyLayoutID.BUTTON_IGDB_SEARCH, "n_clicks")],
    [State(EnergyLayoutID.MODAL_SEARCH_IGDB, "is_open")],
)
def toggle_search_igdb_modal(n1, n2, is_open):
    if n1 :
        return not is_open
    if n2 :
        return not is_open
    return is_open





@callback(
    Output(EnergyLayoutID.DIV_HIDDEN_SELECTED_ID, 'children'),  
    Input(EnergyLayoutID.GRAPH_IGDB, "clickData"),
)
def store_in_hidden_div(pt_data):
    if pt_data:
        id = pt_data['points'][0]['customdata'][0]
        return id
    else:
        raise PreventUpdate

    
@callback(
    Output(EnergyLayoutID.STORE_BUILDUP_IN_SESSION, 'data'),  
    Input(EnergyLayoutID.GRAPH_IGDB, "clickData"),
    Input(EnergyLayoutID.CHECKBOX_FLIP_OUTERLAYER, "value"),
    Input(EnergyLayoutID.SELECT_GAS,"value"),
    Input(EnergyLayoutID.INPUT_GAP,"value"),
    Input(EnergyLayoutID.SELECT_INNERLAYER_SUBSTRATE,"value"), # clear or ultraclear
    Input(EnergyLayoutID.SELECT_INNERLAYER_THICKNESS,"value")

)
def glass_to_store(pt_data,flipped, gas, gap_thickness, inner_substrate, inner_thickness):
    """
    Stores current user selected buildup in session storage.
    """
    buildup = {}
    buildup[Buildup.SOLID_LAYERS] = [{},{}]
    buildup[Buildup.GAS_LAYERS] = [{}]
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

    buildup[Buildup.GAS_LAYERS][0]['gas'] = gas
    buildup[Buildup.GAS_LAYERS][0]['thickness'] = gap_thickness

    return json.dumps(buildup)


@callback(
    Output(EnergyLayoutID.DIV_BUILDUP_SVG_CONTAINER,"children"),
    Input(EnergyLayoutID.STORE_BUILDUP_IN_SESSION,"modified_timestamp"),
    State(EnergyLayoutID.STORE_BUILDUP_IN_SESSION,"data")
)
def update_buildup_svg(ts, buildup):
    if ts is None or buildup is None:
        raise PreventUpdate

    return svg_glass.generate_buildup(json.loads(buildup))


@callback(
    Output(EnergyLayoutID.DIV_OUTERLITE_PRODUCT,"children"),
    Input(EnergyLayoutID.STORE_BUILDUP_IN_SESSION,"modified_timestamp"),
    State(EnergyLayoutID.STORE_BUILDUP_IN_SESSION,"data")
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
    Output(EnergyLayoutID.SELECT_GAS,"options"),
    Input(EnergyLayoutID.SELECT_STANDARD,"value")
)
def update_gas_options(standard):
    if standard == "nfrc":
        options = [{"label": k, "value": k} for k in igdb.GASES_NFRC_LOOKUP]
    else:
        options = [{"label": k, "value": k} for k in igdb.GASES_EN673_LOOKUP]
    return options

@callback(
    Output(EnergyLayoutID.TABLE_CELL_TVIS_LABEL,"children"),
    Output(EnergyLayoutID.TABLE_CELL_SHGC_LABEL,"children"),
    Input(EnergyLayoutID.SELECT_STANDARD,"value")
)
def update_results_labels(standard):
    if standard == "nfrc":
        return ["Visible transmittance, T",html.Sub("vis")], ["SHGC"]
    else:
        return ["Visible transmittance, τᵥ"], ["Solar factor, g"]



@callback(
    Output(EnergyLayoutID.TABLE_CELL_UVALUE, "children"),
    Output(EnergyLayoutID.TABLE_CELL_SHGC,"children"),
    Output(EnergyLayoutID.TABLE_CELL_TVIS,"children"),
    Output(EnergyLayoutID.TABLE_CELL_ROUT,"children"),
    Output(EnergyLayoutID.TABLE_CELL_RIN,"children"),
    Output(EnergyLayoutID.TABLE_CELL_COLOR_TRANS,"style"),
    Output(EnergyLayoutID.TABLE_CELL_COLOR_REFL,"style"),
    Input(EnergyLayoutID.STORE_BUILDUP_IN_SESSION,"modified_timestamp"),
    Input(EnergyLayoutID.SELECT_STANDARD,"value"),
    State(EnergyLayoutID.STORE_BUILDUP_IN_SESSION,"data")
)
def run_analysis_and_update_results(ts, standard, buildup):
    if ts is None or buildup is None:
        raise PreventUpdate
    buildup = json.loads(buildup)

    print("Running analysis for buildup:",standard)

    if standard == "nfrc":   
        glazing_system_u_environment, glazing_system_solar_environment= mywincalc.run_nfrc_analysis(buildup)
    else:
        glazing_system_u_environment, glazing_system_solar_environment= mywincalc.run_cen_analysis(buildup)

    optical = glazing_system_u_environment.optical_method_results("PHOTOPIC").system_results
    
    uvalue = f'{glazing_system_u_environment.u():.3f}'

    try:
        shgc = f'{glazing_system_solar_environment.shgc():.3f}'
    except Exception as e:
        solar = glazing_system_u_environment.optical_method_results("SOLAR")
        tau_e = solar.system_results.front.transmittance.direct_direct

        absorptances = [
            layer.front.absorptance.total_direct
            for layer in solar.layer_results
        ]
        g = tau_e + 0.5 * sum(absorptances)
        shgc = f'{g:.3f}'
  
    tvis = f'{optical.front.transmittance.direct_direct:.3f}'
    rout = f'{optical.front.reflectance.direct_direct:.3f}'
    rin = f'{optical.back.reflectance.direct_direct:.3f}'

    color_t = glazing_system_u_environment.color().system_results.front.transmittance.direct_direct.rgb
    color_r = glazing_system_u_environment.color().system_results.front.reflectance.direct_direct.rgb
    color_t = utils.rgb_to_csshex(color_t.R,color_t.G,color_t.B)
    color_r = utils.rgb_to_csshex(color_r.R,color_r.G,color_r.B)

    return uvalue,shgc,tvis,rout,rin,{'background-color' : color_t},{'background-color' : color_r}


@callback(
    Output(EnergyLayoutID.LINK_GSTR,"children"),Output(EnergyLayoutID.LINK_GSTR,"href"),
    Input(EnergyLayoutID.STORE_BUILDUP_IN_SESSION,"modified_timestamp"),
    State(EnergyLayoutID.STORE_BUILDUP_IN_SESSION,"data"),
    State(EnergyLayoutID.URL, "href")
)
def update_gstr_url(ts, buildup, href):
    if ts is None or buildup is None:
        raise PreventUpdate
    _buildup = json.loads(buildup)
    
    lites = glass_model_helpers.lites_from_dict(_buildup)
    gases = glass_model_helpers.gaslayers_from_dict(_buildup)

    igu = InsulatedGlass(lites,gases)

    gs = igu.to_gstr(False)
    _gs = urllib.parse.quote(gs)
    root_url = callback_helpers.get_root_netloc(href)

    

    return f'{root_url}{WebPaths.ENERGY}?g={_gs}',f'{root_url}{WebPaths.ENERGY}?g={_gs}'

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
    Output(EnergyLayoutID.GRAPH_IGDB, "clickData"),
    Output(EnergyLayoutID.CHECKBOX_FLIP_OUTERLAYER, "value"),
    Output(EnergyLayoutID.SELECT_GAS,"value"),
    Output(EnergyLayoutID.INPUT_GAP,"value"),
    Output(EnergyLayoutID.SELECT_INNERLAYER_SUBSTRATE,"value"), # clear or ultraclear
    Output(EnergyLayoutID.SELECT_INNERLAYER_THICKNESS,"value"),
    Input(EnergyLayoutID.URL, 'href'),
    State(EnergyLayoutID.URL,'pathname'),
    State(EnergyLayoutID.URL,'search') 
    )
def onload_parse_url(href, pathname,search):
    """
    Mocks a user data point click on the default loadup glass
    to trigger analysis on first load of webapp.

    Selected point in graph is not triggered by this - hard coded in hidden div.
    """
    if href is None:
        raise PreventUpdate
    else:
        if search:
            parsed = urllib.parse.urlparse(href)
            g_str = urllib.parse.parse_qs(parsed.query)['g'][0]
            igu = GlassBuildup.make_glass(g_str)
            return glass_model_helpers.callback_return(igu)
        else:
            return \
                {'points' :[{'customdata': DEFAULT_GRAPH_GLASS}]}, \
                False, \
                'air', \
                12, \
                'clear', \
                6
        
@callback(
    Output(EnergyLayoutID.DATALIST_GLASS_SEARCH_SUGGESTIONS, "children"),
    Input(EnergyLayoutID.INPUT_GLASS_SEARCH, "value")
)
def update_suggestions(search_value):
    if not search_value or len(search_value) < 2:
        return []


    # Logic: Search across multiple specific columns
    # Example: 'Manufacturer', 'Product_Name', and 'Thickness'
    cols_to_search = ['Manufacturer', 'Product_Name']
    
    # Efficient filtering across multiple columns
    mask = pd.concat([
        DF_GLASS_TABLE[col].str.contains(search_value, case=False, na=False) 
        for col in cols_to_search
    ], axis=1).any(axis=1)

    # Extract unique values from the primary display column or a combined label
    suggestions = DF_GLASS_TABLE[mask]['Product_Name'].unique()[:15]
    
    return [{"label": s, "value": s} for s in suggestions]