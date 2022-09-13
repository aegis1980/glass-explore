
import os
import json
import functools
from typing import Dict

PATH_DATA = os.path.join('data')
PATH_STANDARDS = os.path.join('data','standards')
PATH_PRODUCTS = os.path.join('data','products')

DEVTEMP = os.path.join(os.getcwd(),'temp') 


ALL_MANUFACTURERS = '[ALL]'

GRAPHTYPE_TS_TV = 1
GRAPHTYPE_LAB = 2 
GRAPHTYPE_RGB = 3

class Buildup:
    SOLID_LAYERS = 'layers'
    GAP_LAYERS = 'gas_layers'


class LayoutID:
    GRAPH = "graph-ts-tv"
    GRAPH_LAB = "graph-lab"

    MODAL_ABOUT = "modal-splash"
    MODAL_ABOUT_CLOSE = "modal-splash-close"

    MODAL_SETTINGS = "modal-settings"
    MODAL_SETTINGS_CLOSE = "modal-settings-close"

    SELECT_GAS = "select-gas"
    INPUT_GAP = "input-gap"

    CHECKBOX_FLIP_OUTERLAYER = "checkbox-flip-outerlayer"
    CHECKBOX_ADVANCED_OPTICAL_STANDARD = "checkbox-advance-standard"

    DIV_OUTERLITE_PRODUCT = "div-outerlite-product"
    DIV_BUILDUP_SVG_CONTAINER = "div-buildup-svg-container"

    NAV_GRAPHTYPE = "nav_graphtype"
    
    NAVLINK_ABOUT = "navlink_about"
    NAVLINK_SETTINGS = "navlink_settings"

    NAVLINK_GRAPHTYPE_TS_TV = 1
    NAVLINK_GRAPHTYPE_LAB = 2 
    NAVLINK_GRAPHTYPE_RGB = 3

    SELECT_INNERLAYER_THICKNESS = "select-innerlayer-thickness"
    SELECT_INNERLAYER_SUBSTRATE = "select-innerlayer-substrate"
    SELECT_MANUFACTURER = "select-manufacturer"
    SELECT_OPTICAL_STANDARD = "select-standard"

    STORE_BUILDUP_IN_SESSION = "store-buildup-session"
    STORE_SETTINGS_IN_LOCAL = "store-settings-local"

    TABLE_CELL_UVALUE = "table-cell-uvalue"
    TABLE_CELL_SHGC = "table-cell-shgc"
    TABLE_CELL_TVIS = "table-cell-tvis"
    TABLE_CELL_ROUT = "table-cell-rout"
    TABLE_CELL_RIN  = "table-cell-rin"
    TABLE_CELL_COLOR_TRANS = "table-cell-color_trans"
    TABLE_CELL_COLOR_REFL = "table-cell-color_refl"
    
    BUTTONGROUP_GRAPHTYPE = "buttongroup-graphtype"

    URL = "url"




DEFAULT_OPTICAL_STANDARD = "W5_NFRC_2003.std"

@functools.cache    
def standards():

    fpath = os.path.join(PATH_DATA,'standards.json')
    with open(fpath) as f:
        s = json.load(f)
    return s
    