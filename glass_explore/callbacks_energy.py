#(c)2026 Jon Robinson. All Rights Reserved.

import json
import re
import urllib.parse

import dash

from dash import Input, Output, State, clientside_callback, callback, no_update, html,ctx,Patch
from dash.exceptions import PreventUpdate

from thefuzz import process, fuzz


from glass_explore import (ALL_MANUFACTURERS, OG_DESCRIPTION, URL, DF_GLASS_TABLE, DEFAULT_GRAPH_GLASS,Buildup, EnergyLayoutID, WebPaths,
                           caching, callback_helpers, en410, en673, igdb,COLORSPACE_RGB,COLORSPACE_LAB,
                           mywincalc, svg_glass, utils, glass_model_helpers)

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
    State(EnergyLayoutID.GRAPH_IGDB, "clickData"),
)
def update_igdb_data_display(active_tabs, manufacturer, thickness, selected_id, click_data):
    out_fig = dash.no_update

    if thickness:
        thickness = int(thickness)

    selected_id = _selected_id_from_clickdata(click_data) or selected_id

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


def _selected_id_from_customdata(customdata):
    if customdata is None:
        return None

    if isinstance(customdata, dict):
        return customdata.get("ID")

    if hasattr(customdata, "get"):
        id_from_label = customdata.get("ID", None)
        if id_from_label is not None:
            return id_from_label

    try:
        return customdata[0]
    except (KeyError, IndexError, TypeError):
        return None


def _selected_id_from_clickdata(pt_data):
    if not pt_data:
        return None

    points = pt_data.get("points") if isinstance(pt_data, dict) else None
    if not points:
        return None

    return _selected_id_from_customdata(points[0].get("customdata"))


# CALLBACK 2: Handles the snappy highlight (Patch Only)
# Runs in the browser, so the highlight moves on the click itself instead of after a round
# trip to the server.
clientside_callback(
    """
    function(clickData, figure) {
        const no_update = window.dash_clientside.no_update;

        // Programmatic selection writes a clickData with no coordinates; the figure
        // callback draws the highlight for those.
        const point = clickData && clickData.points && clickData.points[0];
        if (!point || !("x" in point) || !("y" in point)) {
            return no_update;
        }

        // The last trace is the dedicated highlight trace
        const traces = (figure && figure.data) || [];
        const highlight = traces[traces.length - 1];
        if (!highlight) {
            return no_update;
        }

        const color = point["marker.color"] || (point.marker || {}).color;

        // A 3D scene fires a click on every frame drawn while the mouse button is down:
        // skip the repeats, where the highlight is already on this point.
        const is = (value, expected) => Array.isArray(value) && value.length === 1 && value[0] === expected;
        if (is(highlight.x, point.x) && is(highlight.y, point.y)
                && (!("z" in point) || is(highlight.z, point.z))
                && is((highlight.marker || {}).color, color)) {
            return no_update;
        }

        // Target the last trace directly via index -1
        const patch = new window.dash_clientside.Patch();
        patch.assign(["data", -1, "x"], [point.x]);
        patch.assign(["data", -1, "y"], [point.y]);
        if ("z" in point) {
            patch.assign(["data", -1, "z"], [point.z]);
        }
        patch.assign(["data", -1, "marker", "color"], [color]);
        return patch.build();
    }
    """,
    Output(EnergyLayoutID.GRAPH_IGDB, "figure", allow_duplicate=True),
    Input(EnergyLayoutID.GRAPH_IGDB, "clickData"),
    State(EnergyLayoutID.GRAPH_IGDB, "figure"),
    prevent_initial_call=True
)


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
    id = _selected_id_from_clickdata(pt_data)
    if id is None:
        raise PreventUpdate

    return id

    
def buildup_from_inputs(pt_data, coating_surface, gas, gap_thickness, uncoated_substrate, uncoated_thickness):
    """
    Current user selected buildup as a dict, or None if no glass is selected.

    coating_surface is the surface (1-4, numbered from outside) that the selected lite's
    coating is on. It sets both which lite the selected glass is and whether it is flipped,
    whichever face the IGDB measured the coating on (utils.lite_placement_from_surface).
    """
    buildup = {}
    buildup[Buildup.SOLID_LAYERS] = [{},{}]
    buildup[Buildup.GAS_LAYERS] = [{}]
    id = _selected_id_from_clickdata(pt_data)
    if id is None:
        return None

    props_coated = igdb.lookup_glass_props(id)
    props_uncoated = mywincalc.generic_uncoated_glass_props(int(uncoated_thickness),uncoated_substrate == 'ultraclear') # note inntersubstrate taking a bool!

    coated_side_inside, coated_layer_flipped = utils.lite_placement_from_surface(
        coating_surface or utils.DEFAULT_COATING_SURFACE, props_coated['Coated_Side'])

    if coated_side_inside:
        a=1
        b=0
    else:
        a=0
        b=1

    buildup[Buildup.COATED_LAYER_INDEX] = a

    buildup[Buildup.SOLID_LAYERS][a]['color'] = DF_GLASS_TABLE.loc[int(id)]['CssColor']
    buildup[Buildup.SOLID_LAYERS][a]['flipped'] = coated_layer_flipped
    utils.populate_buildup_with_glass_props(buildup,props_coated,a)

    buildup[Buildup.SOLID_LAYERS][b]['color'] = DF_GLASS_TABLE.loc[props_uncoated['NFRC_ID']]['CssColor']
    buildup[Buildup.SOLID_LAYERS][b]['flipped'] = False
    utils.populate_buildup_with_glass_props(buildup,props_uncoated,b)

    buildup[Buildup.GAS_LAYERS][0]['gas'] = gas
    buildup[Buildup.GAS_LAYERS][0]['thickness'] = gap_thickness

    return buildup


def coated_lite_productdata(buildup):
    """
    Link text, link value and product description for the coated lite.
    """
    # The coated lite is layers[1] when the outside/inside switch is on. Older session data has no index; assume outer.
    coated_idx = buildup.get(Buildup.COATED_LAYER_INDEX, 0)
    props = buildup[Buildup.SOLID_LAYERS][coated_idx]['props']

    if props['Coating_Name'] and props['Coating_Name'] != "N/A" and props['Coating_Name'] != "Unknowen":
        product = html.Strong(f"{props['ProductName']}, {props['Coating_Name']}")
    else:
        product = html.Strong(f"{props['ProductName']}")

    outer_layer_info = [
            product,
            html.Br(),
            f" ( {props['Manufacturer']}, {props['Thickness']:.1f}mm, {props['Name']})"
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
    


def run_analysis_and_update_results(standard, buildup):
    """
    Runs the analysis for the buildup and returns the values for the results table:
    U-value, SHGC / solar factor, Tvis, Rout, Rin, and the transmitted and reflected colour styles.
    """
    if standard == "nfrc":
        glazing_system_u_environment, glazing_system_solar_environment = mywincalc.run_nfrc_analysis(buildup)
        uvalue = f'{glazing_system_u_environment.u():.1f}'
        shgc = f'{glazing_system_solar_environment.shgc():.2f}'

        color_results = glazing_system_solar_environment.color() # one call: pywincalc recomputes the colour results every time
        color_t = color_results.system_results.front.transmittance.direct_direct.rgb
        color_r = color_results.system_results.front.reflectance.direct_direct.rgb

        optical = glazing_system_solar_environment.optical_method_results("PHOTOPIC").system_results

    else: #CEN  EN 410:2011
        _trial = True # set to True to compare our EN 673 implementation with pywincalc's (which is very slow due to the iteration in Python rather than C++)  
        glazing_system_u_environment, glazing_system_optical_environment = mywincalc.run_cen_analysis(buildup)
        
        if _trial:
            # For testing purposes, bypass the pywincalc EN 673 iteration and use our own implementation which is much faster and gives essentially the same result (within 0.001 W/m²K)
            en673_result = en673.u_value(buildup, detailed_analysis=True)
            u_en673 = en673_result.u
        else:
            u_en673 = glazing_system_u_environment.u()
            
        uvalue = f'{u_en673:.1f}'
        en410result = en410.solar_factor(buildup) # currently only returns solar factor, but also computes intermediate values that could be added to results display in future if desired
        shgc = f'{en410result.g:.2f}'

        color_results = glazing_system_optical_environment.color(tristimulus_x_method="CRI_X",
                                     tristimulus_y_method="CRI_Y",
                                     tristimulus_z_method="CRI_Z")
        color_t = color_results.system_results.front.transmittance.direct_direct.rgb
        color_r = color_results.system_results.front.reflectance.direct_direct.rgb
        
        optical = glazing_system_optical_environment.optical_method_results("PHOTOPIC").system_results

    tvis = f'{optical.front.transmittance.direct_direct:.2f}'
    rout = f'{optical.front.reflectance.direct_direct:.2f}'
    rin = f'{optical.back.reflectance.direct_direct:.2f}'

    color_t = utils.rgb_to_csshex(color_t.R,color_t.G,color_t.B)
    color_r = utils.rgb_to_csshex(color_r.R,color_r.G,color_r.B)


    return uvalue,shgc,tvis,rout,rin,{'background-color' : color_t},{'background-color' : color_r}


@callback(
    Output(EnergyLayoutID.STORE_BUILDUP_IN_SESSION, 'data'),
    Output(EnergyLayoutID.DIV_BUILDUP_SVG_CONTAINER,"children"),
    Output(EnergyLayoutID.LINK_COATED_LITE_ID,"children"),
    Output(EnergyLayoutID.LINK_COATED_LITE_ID,"value"),
    Output(EnergyLayoutID.DIV_COATED_LITE_PRODUCT,"children"),
    Output(EnergyLayoutID.LABEL_COATING_SURFACE,"children"),
    Output(EnergyLayoutID.RADIO_COATING_SURFACE,"options"),
    Output(EnergyLayoutID.FORMTEXT_COATING_SURFACE,"children"),
    Output(EnergyLayoutID.TABLE_CELL_UVALUE, "children"),
    Output(EnergyLayoutID.TABLE_CELL_SHGC,"children"),
    Output(EnergyLayoutID.TABLE_CELL_TVIS,"children"),
    Output(EnergyLayoutID.TABLE_CELL_ROUT,"children"),
    Output(EnergyLayoutID.TABLE_CELL_RIN,"children"),
    Output(EnergyLayoutID.TABLE_CELL_COLOR_TRANS,"style"),
    Output(EnergyLayoutID.TABLE_CELL_COLOR_REFL,"style"),
    Input(EnergyLayoutID.GRAPH_IGDB, "clickData"),
    Input(EnergyLayoutID.RADIO_COATING_SURFACE,"value"),
    Input(EnergyLayoutID.SELECT_GAS,"value"),
    Input(EnergyLayoutID.INPUT_GAP,"value"),
    Input(EnergyLayoutID.SELECT_UNCOATED_SUBSTRATE,"value"), # clear or ultraclear
    Input(EnergyLayoutID.SELECT_UNCOATED_THICKNESS,"value"),
    Input(EnergyLayoutID.SELECT_STANDARD,"value"),
)
def update_buildup_and_results(pt_data, coating_surface, gas, gap_thickness, uncoated_substrate, uncoated_thickness, standard):
    """
    Everything that follows from a selection, in one round trip to the server: stores the
    buildup in session storage (the share link reads it from there) and returns the buildup
    thumbnail, the coated lite product text, the wording of the coating surface picker and
    the analysis results.

    These used to be four callbacks chained through the store's modified_timestamp, which
    cost a second round trip on every click.
    """
    buildup = buildup_from_inputs(pt_data, coating_surface, gas, gap_thickness, uncoated_substrate, uncoated_thickness)
    if buildup is None:
        raise PreventUpdate

    # The store holds the buildup as JSON. Everything below works from the decoded copy, not
    # from the dict built above: that one holds the cached igdb props dicts by reference.
    buildup_json = json.dumps(buildup)
    buildup = json.loads(buildup_json)

    coated_layer = buildup[Buildup.SOLID_LAYERS][buildup[Buildup.COATED_LAYER_INDEX]]

    return (
        buildup_json,
        svg_glass.generate_buildup(buildup),
        *coated_lite_productdata(buildup),
        *callback_helpers.coating_surface_control(coated_layer['coating']),
        *run_analysis_and_update_results(standard, buildup),
    )


@callback(
    Output(EnergyLayoutID.CARD_HEADER_COATED,"children"),
    Output(EnergyLayoutID.CARD_HEADER_NONCOATED,"children"),
    Input(EnergyLayoutID.RADIO_COATING_SURFACE,"value")
)
def update_card_headers_on_igu_flip(coating_surface):
    # Surfaces 3 and 4 are the inner lite
    coated_side_in = int(coating_surface or utils.DEFAULT_COATING_SURFACE) >= 3
    if not coated_side_in:
        return "Coated outer glass layer", "Non-coated inner glass layer"
    else:
        return "Coated inner glass layer", "Non-coated outer glass layer"


def _gstr_from_search(search):
    if not search:
        return None

    query = urllib.parse.urlparse(search).query or search.lstrip("?")
    return urllib.parse.parse_qs(query).get("g", [None])[0]


@callback(
    Output(EnergyLayoutID.LINK_GSTR,"children"),Output(EnergyLayoutID.LINK_GSTR,"href"),
    Input(EnergyLayoutID.MODAL_SHARE, "is_open"),
    State(EnergyLayoutID.STORE_BUILDUP_IN_SESSION,"data"),
    State(EnergyLayoutID.URL, "href")
)
def update_gstr_url(is_open, buildup, href):
    if not is_open or buildup is None:
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
    Output(EnergyLayoutID.RADIO_COATING_SURFACE, "value"),
    Output(EnergyLayoutID.SELECT_GAS,"value"),
    Output(EnergyLayoutID.INPUT_GAP,"value"),
    Output(EnergyLayoutID.SELECT_UNCOATED_SUBSTRATE,"value"), # clear or ultraclear
    Output(EnergyLayoutID.SELECT_UNCOATED_THICKNESS,"value"),
    Input(EnergyLayoutID.URL, 'pathname'),
    Input(EnergyLayoutID.URL, "search"),
    Input(EnergyLayoutID.STORE_GSTR_FROM_URL, "modified_timestamp"),
    Input(EnergyLayoutID.MODAL_SEARCH_IGDB_OK, 'n_clicks'),
    Input(EnergyLayoutID.LINK_COATED_LITE_ID, 'n_clicks'),
    State(EnergyLayoutID.STORE_GSTR_FROM_URL, "data"),
    State(EnergyLayoutID.MODAL_SEARCH_IGDB_OK,'value'),
    State(EnergyLayoutID.LINK_COATED_LITE_ID,"value"),


    )
def onload_parse_url_and_search_table_ok(
    _pathname,
    url_search,
    _gstr_timestamp,
    btn_click,
    link_click,
    gstr_from_url,
    model_search_id,
    link_id
):
    
    
    """
    Mocks a user data point click on the default loadup glass
    to trigger analysis on first load of webapp.

    Selected point in graph is not triggered by this - hard coded in hidden div.
    """
    triggered = ctx.triggered_id or EnergyLayoutID.URL

    if triggered == EnergyLayoutID.URL:
        gstr = _gstr_from_search(url_search)
        if gstr:
            igu = GlassBuildup.make_glass(gstr)
            return glass_model_helpers.callback_return_from_igu(igu)

    if triggered == EnergyLayoutID.STORE_GSTR_FROM_URL:
        if not gstr_from_url:
            raise PreventUpdate

        igu = GlassBuildup.make_glass(gstr_from_url)
        return glass_model_helpers.callback_return_from_igu(igu)

    if triggered == EnergyLayoutID.URL:
        return \
            callback_helpers.clickdata_for_glass_id(DEFAULT_GRAPH_GLASS["ID"]), \
            ALL_MANUFACTURERS, \
            6, \
            utils.DEFAULT_COATING_SURFACE, \
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
        callback_helpers.clickdata_for_glass_id(id), \
        DF_GLASS_TABLE.loc[id]['Manufacturer'], \
        callback_helpers.round_to_nearest_even(DF_GLASS_TABLE.loc[id]['Thickness']), \
        no_update, \
        no_update, \
        no_update, \
        no_update, \
        no_update


@callback(
    Output(EnergyLayoutID.STORE_GSTR_FROM_URL, "data"),
    Input(EnergyLayoutID.URL, "search"),
)
def store_gstr_from_url(search):
    gstr = _gstr_from_search(search)
    if not gstr:
        raise PreventUpdate

    return gstr


clientside_callback(
    """
    function(timestamp, gstr, pathname) {
        if (timestamp === undefined || timestamp === null || !gstr) {
            return window.dash_clientside.no_update;
        }

        window.history.replaceState(null, "", pathname || "/energy");
        return window.dash_clientside.no_update;
    }
    """,
    Output(EnergyLayoutID.DUMMY_FOR_CALLBACK, "data"),
    Input(EnergyLayoutID.STORE_GSTR_FROM_URL, "modified_timestamp"),
    State(EnergyLayoutID.STORE_GSTR_FROM_URL, "data"),
    State(EnergyLayoutID.URL, "pathname"),
    prevent_initial_call=True
)

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
    Output(EnergyLayoutID.MODAL_SEARCH_DATATABLE, "active_cell", allow_duplicate=True),
    Output(EnergyLayoutID.MODAL_SEARCH_DATATABLE, "selected_cells"),
    Input(EnergyLayoutID.MODAL_SEARCH_IGDB, "is_open"),
    Input(EnergyLayoutID.MODAL_SEARCH_INPUT_GLASS_SEARCH, "value"),
    Input(EnergyLayoutID.MODAL_SEARCH_SELECT_COATED_MANUFACTURER,"value"),
    Input(EnergyLayoutID.MODAL_SEARCH_SELECT_COATED_THICKNESS,"value"),
    State(EnergyLayoutID.MODAL_SEARCH_DATATABLE, "active_cell"),
    prevent_initial_call=True
)
def update_table_from_user_input(modal_open,search_value, manufacturer, thickness, active_cell):

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
            search_value.lower(),
            df['_search_blob'],
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

    # An 'id' key on each row makes DataTable report the clicked row's glass ID as
    # active_cell['row_id']. The table sorts natively, so a row's position on screen
    # is not its position in 'data'.
    results['id'] = results['ID']

    # The table keeps its active and selected cells at the same screen position when the rows
    # are replaced, which would leave the highlight on a different glass from the one the OK
    # button holds. Clearing the active cell resets the OK button as well, through
    # handle_search_result_row_click; selected_cells is what draws the highlight.
    deselect = None if active_cell else no_update

    # 5. Return as a list of dictionaries (records format)
    return results.to_dict('records'),msg,msg_color,deselect,[]


@callback(
    Output(EnergyLayoutID.MODAL_SEARCH_IGDB_OK, "value"), # Store id for the selected row data
    Output(EnergyLayoutID.MODAL_SEARCH_IGDB_OK, "outline"), # Store id for the selected row data
    Output(EnergyLayoutID.MODAL_SEARCH_IGDB_OK, "disabled"), # Store id for the selected row data
    Output(EnergyLayoutID.MODAL_SEARCH_IGDB_OK, "children"), # Store id for the selected row data
    Input(EnergyLayoutID.MODAL_SEARCH_DATATABLE, "active_cell"),
    prevent_initial_call=True
)
def handle_search_result_row_click(active_cell):
    # row_id is the glass ID, taken from the row's 'id' key. Do not use active_cell['row']
    # to index the table data: it is the row's position in the sorted view.
    id = active_cell.get('row_id') if active_cell else None

    if id is None:
        return no_update, True, True, "No glass selected" # No row selected, return default value and no update for outline

    return id, False, False, f"Glass selected [ID: {id}]" # Return the selected glass id and set outline to True


# Sync row selection with the active cell.
# selected_rows are indices into 'data', but active_cell.row is the row's position in the
# sorted view; derived_viewport_indices maps one to the other. Clientside, so that list
# (one entry per table row) is not uploaded on every row click.
clientside_callback(
    """
    function(active_cell, is_open, viewport_indices) {
        if (!active_cell || !viewport_indices || active_cell.row >= viewport_indices.length) {
            return [];
        }
        return [viewport_indices[active_cell.row]];
    }
    """,
    Output(EnergyLayoutID.MODAL_SEARCH_DATATABLE, "selected_rows"),
    Input(EnergyLayoutID.MODAL_SEARCH_DATATABLE, "active_cell"),
    Input(EnergyLayoutID.MODAL_SEARCH_IGDB, "is_open"),
    State(EnergyLayoutID.MODAL_SEARCH_DATATABLE, "derived_viewport_indices"),
    prevent_initial_call=True
)



@callback(
    Output(EnergyLayoutID.MODAL_SEARCH_DATATABLE, "active_cell"),
    Input(EnergyLayoutID.MODAL_SEARCH_IGDB, "is_open"),
    prevent_initial_call=True
)
def deselect_on_modal_open_close(is_open):

    #Deactivate cell (also triggers callback to clear selected_rows)
    return None
