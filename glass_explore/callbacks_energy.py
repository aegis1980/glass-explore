#(c)2026 Jon Robinson. All Rights Reserved.

import json
import re
import urllib.parse

import dash

from dash import Input, Output, State, clientside_callback, callback, no_update, html,ctx,Patch
from dash.exceptions import PreventUpdate

from thefuzz import process, fuzz


from glass_explore import (ALL_MANUFACTURERS, OG_DESCRIPTION, URL, DF_GLASS_TABLE, DEFAULT_GRAPH_GLASS,SEARCH_GLASS_TABLE,Buildup, EnergyLayoutID, WebPaths,
                           caching as caching, callback_helpers, igdb,COLORSPACE_RGB,COLORSPACE_LAB,
                           mywincalc, standards, svg_glass, utils, glass_model_helpers)

from glass_explore.glass_model import (GlassBuildup, InsulatedGlass)

# Dynamic resize graph on window resize 
# clientside_callback(
#     """
#     function(h,w) {
#         ht = self.innerHeight - 245;
#         s = "height:" + ht + "px";
#         document.getElementById('graph-ts-tv').setAttribute("style",s);
#         return window.dash_clientside.no_update;
#     }
#     """,
#     Output(EnergyLayoutID.DIV_HIDDEN_WINDOW_HT, "children"),
#     Input(EnergyLayoutID.DIV_DISPLAY_RESIZE,"height"),
#     Input(EnergyLayoutID.DIV_DISPLAY_RESIZE,"width")
# )


@callback(
    Output(EnergyLayoutID.GRAPH_IGDB, "figure"),
    Output(EnergyLayoutID.FORMTEXT_SELECT_COATED_MANUFACTURER,"children"), 
    Output(EnergyLayoutID.FORMTEXT_SELECT_COATED_MANUFACTURER,"color"),
    Input(EnergyLayoutID.TABS, "active_tab"),
    Input(EnergyLayoutID.SELECT_COATED_MANUFACTURER, "value"),
    Input(EnergyLayoutID.SELECT_COATED_THICKNESS, "value"),
    State(EnergyLayoutID.DIV_HIDDEN_SELECTED_ID, 'children'),  
)
def update_igdb_data_display(active_tabs, manufacturer, thickness,selected_id):
    out_fig = dash.no_update

    if thickness:
        thickness = int(thickness)

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
    Output(EnergyLayoutID.MODAL_SHARE, "is_open"),
    [Input(EnergyLayoutID.MODAL_SHARE_CLOSE, "n_clicks"),Input(EnergyLayoutID.BUTTON_SHARE, "n_clicks")],
    [State(EnergyLayoutID.MODAL_SHARE, "is_open")],
)
def toggle_share_modal(n1, n2, is_open):
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
    Input(EnergyLayoutID.SWITCH_LOWE_SIDE,"value"),
    Input(EnergyLayoutID.CHECKBOX_FLIP_OUTERLAYER, "value"),
    Input(EnergyLayoutID.SELECT_GAS,"value"),
    Input(EnergyLayoutID.INPUT_GAP,"value"),
    Input(EnergyLayoutID.SELECT_UNCOATED_SUBSTRATE,"value"), # clear or ultraclear
    Input(EnergyLayoutID.SELECT_UNCOATED_THICKNESS,"value"),
)
def glass_to_store(pt_data, coated_side_inside, coated_layer_flipped, gas, gap_thickness, uncoated_substrate, uncoated_thickness):
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

    props_coated = igdb.lookup_glass_props(id)
    props_uncoated = mywincalc.generic_uncoated_glass_props(int(uncoated_thickness),uncoated_substrate == 'ultraclear') # note inntersubstrate taking a bool!
    
    if coated_side_inside:
        a=1
        b=0
    else:
        a=0
        b=1

    buildup[Buildup.SOLID_LAYERS][a]['color'] = DF_GLASS_TABLE.loc[int(id)]['CssColor']
    buildup[Buildup.SOLID_LAYERS][a]['flipped'] = coated_layer_flipped
    utils.populate_buildup_with_glass_props(buildup,props_coated,a)

    buildup[Buildup.SOLID_LAYERS][b]['color'] = DF_GLASS_TABLE.loc[props_uncoated['NFRC_ID']]['CssColor']
    buildup[Buildup.SOLID_LAYERS][b]['flipped'] = False
    utils.populate_buildup_with_glass_props(buildup,props_uncoated,b)

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
    Output(EnergyLayoutID.LINK_COATED_LITE_ID,"children"),
    Output(EnergyLayoutID.LINK_COATED_LITE_ID,"value"),
    Output(EnergyLayoutID.DIV_COATED_LITE_PRODUCT,"children"),
    Input(EnergyLayoutID.STORE_BUILDUP_IN_SESSION,"modified_timestamp"),
    State(EnergyLayoutID.STORE_BUILDUP_IN_SESSION,"data")
)
def update_coated_lite_productdata(timestamp, buildup):
    if timestamp is None or buildup is None:
        raise PreventUpdate
    
    buildup = json.loads(buildup)
    props = buildup[Buildup.SOLID_LAYERS][0]['props']

    outer_layer_info = [
            html.Strong(f"{props['ProductName']}, {props['Name']}"),
            f" ( {props['Manufacturer']}, {props['Thickness']:.1f}mm)"
    ]

    return  f"[ID#{props['ID']}]:",props['ID'],outer_layer_info, 


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
    Output(EnergyLayoutID.CARD_HEADER_COATED,"children"),
    Output(EnergyLayoutID.CARD_HEADER_NONCOATED,"children"),
    Input(EnergyLayoutID.SWITCH_LOWE_SIDE,"value")
)
def update_card_headers_on_igu_flip(coated_side_in):
    if not coated_side_in:
        return "Coated outer glass layer", "Non-coated inner glass layer"
    else:
        return "Coated inner glass layer", "Non-coated outer glass layer"


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
    Output(EnergyLayoutID.SELECT_COATED_MANUFACTURER,"value"),
    Output(EnergyLayoutID.SELECT_COATED_THICKNESS,"value"),
    Output(EnergyLayoutID.CHECKBOX_FLIP_OUTERLAYER, "value"),
    Output(EnergyLayoutID.SELECT_GAS,"value"),
    Output(EnergyLayoutID.INPUT_GAP,"value"),
    Output(EnergyLayoutID.SELECT_UNCOATED_SUBSTRATE,"value"), # clear or ultraclear
    Output(EnergyLayoutID.SELECT_UNCOATED_THICKNESS,"value"),
    Input(EnergyLayoutID.URL, 'href'),
    Input(EnergyLayoutID.MODAL_SEARCH_IGDB_OK, 'n_clicks'),
    Input(EnergyLayoutID.LINK_COATED_LITE_ID, 'n_clicks'),
    State(EnergyLayoutID.URL,'search'),
    State(EnergyLayoutID.MODAL_SEARCH_IGDB_OK,'value'),
    State(EnergyLayoutID.LINK_COATED_LITE_ID,"value"),


    )
def onload_parse_url_and_search_table_ok(
    href, 
    btn_click,
    link_click,
    search,
    model_search_id,
    link_id
):
    
    
    """
    Mocks a user data point click on the default loadup glass
    to trigger analysis on first load of webapp.

    Selected point in graph is not triggered by this - hard coded in hidden div.
    """
    if not ctx.triggered_id:
        raise PreventUpdate

    triggered = ctx.triggered_id
    
    if triggered == EnergyLayoutID.URL:
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
                    ALL_MANUFACTURERS, \
                    6, \
                    False, \
                    'air', \
                    12, \
                    'clear', \
                    6

    id = -1        
    if triggered == EnergyLayoutID.MODAL_SEARCH_IGDB_OK:
        if model_search_id is None:
            raise PreventUpdate
        else:
            id = int(model_search_id)

    if triggered == EnergyLayoutID.LINK_COATED_LITE_ID:
        if link_id is None:
            raise PreventUpdate 
        else:    
            id = int(link_id)

    return \
        {'points' :[{'customdata': DF_GLASS_TABLE.loc[id]}]}, \
        DF_GLASS_TABLE.loc[id]['Manufacturer'], \
        callback_helpers.round_to_nearest_even(DF_GLASS_TABLE.loc[id]['Thickness']), \
        no_update, \
        no_update, \
        no_update, \
        no_update, \
        no_update

#############################################################################################
#
# Search Modal Callbacks
#
############################################################################################

@callback(
    Output(EnergyLayoutID.MODAL_SEARCH_IGDB, "is_open"),
    Output(EnergyLayoutID.MODAL_SEARCH_SELECT_COATED_MANUFACTURER,"value"),
    Output(EnergyLayoutID.MODAL_SEARCH_SELECT_COATED_THICKNESS,"value"),
    Input(EnergyLayoutID.MODAL_SEARCH_IGDB_CLOSE, "n_clicks"),
    Input(EnergyLayoutID.BUTTON_IGDB_SEARCH, "n_clicks"),
    Input(EnergyLayoutID.MODAL_SEARCH_IGDB_OK, "n_clicks"),
    State(EnergyLayoutID.MODAL_SEARCH_IGDB, "is_open"),
    State(EnergyLayoutID.SELECT_COATED_MANUFACTURER,"value"),
    State(EnergyLayoutID.SELECT_COATED_THICKNESS,"value"),
)
def toggle_igdb_search_modal(n1, open_search_modal_button, n3,is_open,manufacturer, thickness):
    if n1 or n3:
        #close modal
        return not is_open,no_update,no_update
    if open_search_modal_button:
        return not is_open,manufacturer, int(thickness)
    return is_open,no_update,no_update



@callback(
    Output(EnergyLayoutID.MODAL_SEARCH_DATATABLE, "data"), # Target the 'data' property
    Output(EnergyLayoutID.MODAL_SEARCH_FORMTEXT_SELECT_COATED_MANUFACTURER, "children"),
    Output(EnergyLayoutID.MODAL_SEARCH_FORMTEXT_SELECT_COATED_MANUFACTURER, "color"),
    Input(EnergyLayoutID.MODAL_SEARCH_IGDB, "is_open"),
    Input(EnergyLayoutID.MODAL_SEARCH_INPUT_GLASS_SEARCH, "value"),
    Input(EnergyLayoutID.MODAL_SEARCH_SELECT_COATED_MANUFACTURER,"value"),
    Input(EnergyLayoutID.MODAL_SEARCH_SELECT_COATED_THICKNESS,"value"),
    prevent_initial_call=True
)
def update_table_from_user_input(modal_open,search_value, manufacturer, thickness):

    if not modal_open:
        raise PreventUpdate

    if thickness:
        thickness = int(thickness)

    df = caching.thickness_cached_df(thickness)
    df,msg,msg_color = callback_helpers.populate_datatable(df, manufacturer, thickness)

    # 1. Guard Clause
  #  if not search_value or len(search_value) < 2:
  #      return [] # Returns an empty list to clear the table

    # 2. Define search and display columns
    cols_to_search = ['ID', 'Name', 'ProductName']
    cols_to_return  = ['ID', 'Name', 'ProductName', 'Manufacturer', 'Thickness']


    if search_value and re.match(r'^\d+', search_value):
        # 3a. Dynamic Masking
        # Ensure all columns are treated as strings to avoid errors with numeric IDs/Thickness
        mask = df[cols_to_search].astype(str).apply(
            lambda col: col.str.contains(search_value, case=False, na=False)
        ).any(axis=1)

        # 4a. Filter and Format
        # Select only the specific columns you want the table to show
        results = df.loc[mask, cols_to_return].head(30)

    elif search_value:

        # 3b. Execute Fuzzy Match
        # Extract matches based on the 'Token Set Ratio' (handles out-of-order words)
        matches = process.extract(
            search_value, 
            SEARCH_GLASS_TABLE, 
            scorer=fuzz.token_set_ratio,
            limit=30
        )

        # 4b. Filter DataFrame by resulting indices
        # 'matches' returns a list of tuples: (string, score, index)
        match_indices = [m[2] for m in matches] #if m[1] > 50] # Only keep scores > 50%
        
        results = df.loc[match_indices,cols_to_return]

    else:

        # no search value, return default top results based on manufacturer/thickness filter
        results = df.loc[:,cols_to_return]

    results['Thickness'] = results['Thickness'].round(1)
        
    # 5. Return as a list of dictionaries (records format)
    return results.to_dict('records'),msg,msg_color


@callback(
    Output(EnergyLayoutID.MODAL_SEARCH_IGDB_OK, "value"), # Store id for the selected row data
    Output(EnergyLayoutID.MODAL_SEARCH_IGDB_OK, "outline"), # Store id for the selected row data
    Output(EnergyLayoutID.MODAL_SEARCH_IGDB_OK, "disabled"), # Store id for the selected row data
    Output(EnergyLayoutID.MODAL_SEARCH_IGDB_OK, "children"), # Store id for the selected row data
    Input(EnergyLayoutID.MODAL_SEARCH_DATATABLE, "active_cell"),
    State(EnergyLayoutID.MODAL_SEARCH_DATATABLE, "data"),
    prevent_initial_call=True
)
def handle_search_result_row_click(active_cell, table_data):
    # 1. Check if a cell was actually clicked
    if not active_cell:
        return  no_update, True, True, "No glass selected" # No row selected, return default value and no update for outline

    # 2. Extract the row index from the click event
    # 'row' is the relative index (0 to 14 if you limited to 15 results)
    row_index = active_cell['row']

    # 3. Retrieve the full row dictionary from the table data
    if row_index < len(table_data):
        selected_row = table_data[row_index]
        
        # Example: Print the ID or Name of the clicked glass
        id = selected_row.get('ID')
        
        return id, False, False, f"Glass selected [ID: {id}]" # Return the selected row data and set outline to True

    return no_update, True, True, "No glass selected"


@callback(
    Output(EnergyLayoutID.MODAL_SEARCH_DATATABLE, "selected_rows"),
    Input(EnergyLayoutID.MODAL_SEARCH_DATATABLE, "active_cell"),
    Input(EnergyLayoutID.MODAL_SEARCH_IGDB, "is_open"),
    prevent_initial_call=True
)
def sync_row_selection(active_cell, is_open):
    if not active_cell:
        return []
    
    # Return the index of the row
    return [active_cell['row']]



@callback(
    Output(EnergyLayoutID.MODAL_SEARCH_DATATABLE, "active_cell"),
    Input(EnergyLayoutID.MODAL_SEARCH_IGDB, "is_open"),
    prevent_initial_call=True
)
def deselect_on_modal_open_close(is_open):

    #Deactivate cell (also triggers callback to clear selected_rows)
    return None