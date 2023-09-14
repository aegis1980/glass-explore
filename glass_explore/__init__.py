import functools
import json
import os
from typing import Dict

import pandas as pd

URL = "http://glass-explore.floatingintheclouds.com"
OG_DESCRIPTION = "Glass explore calculates thermal and optic properties of double-glazing"

PATH_DATA = os.path.join('data')
PATH_STANDARDS = os.path.join('data','standards')
PATH_PRODUCTS = os.path.join('data','products')

IGDB_SQLITE_PATH = os.path.join('data', 'igdb.sqlite')


DEVTEMP = os.path.join(os.getcwd(),'temp') 

ALL_MANUFACTURERS = '[ALL]'

GRAPHTYPE_TS_TV = 1
COLORSPACE_LAB = 2 
COLORSPACE_RGB = 3

DATATABLE_COLUMNS = ['ID','ProductName','Manufacturer','Thickness','Tvis','Tsol','Rvis1','Rvis2']

H5_GLASS_PATH = os.path.join('data','glass.h5')
H5_READABLE_GLASS_PATH= os.path.join('data','readable_glass.h5')

try:
    DF_GLASS_TABLE = pd.read_hdf(H5_GLASS_PATH, 'df')
except FileNotFoundError:
    print("Glass table HD5 file not found")

try:
    DF_READABLE_GLASS_TABLE = pd.read_hdf(H5_READABLE_GLASS_PATH, 'df')
except FileNotFoundError:
    print("Readable glass table HD5 file not found")


class Buildup:
    SOLID_LAYERS = 'layers'
    GAP_LAYERS = 'gas_layers'


class SelectedPointProps:
    SIZE_2D = 30
    SIZE_3D = 12
    COLOR_OUTLINE = "black"
    THICKNESS_OUTLINE = 1

class LayoutID:
    DIV_HIDDEN_SELECTED_ID = "div-selected-id-hidden"
    DIV_DATATABLE_IGDB = "div-datatable-igdb"
    DIV_GRAPH_IGDB = "div-graph-igdb"

    GRAPH_IGDB = "graph-ts-tv"
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

    SPINNER_DATATABLE_IGDB = "spinner-datatable-idgb"

    STORE_BUILDUP_IN_SESSION = "store-buildup-session"
    STORE_SETTINGS_IN_LOCAL = "store-settings-local"

    TABLE_CELL_UVALUE = "table-cell-uvalue"
    TABLE_CELL_SHGC = "table-cell-shgc"
    TABLE_CELL_TVIS = "table-cell-tvis"
    TABLE_CELL_ROUT = "table-cell-rout"
    TABLE_CELL_RIN  = "table-cell-rin"
    TABLE_CELL_COLOR_TRANS = "table-cell-color_trans"
    TABLE_CELL_COLOR_REFL = "table-cell-color_refl"

    DATATABLE_IGDB = "datatable-outerlite"
    
    TABS = "tabs"
    TAB_CONTENT = "tab-content"
    TAB_GRAPH_TS_TV = "tab-graph-ts-tv"
    TAB_GRAPH_LAB = "tab-graph-ab"
    TAB_GRAPH_RGB = "tab-graph-rgb"
    TAB_DATATABLE = "tab-datatable"

    URL = "url"




DEFAULT_OPTICAL_STANDARD = "W5_NFRC_2003.std"

@functools.cache    
def standards():

    fpath = os.path.join(PATH_DATA,'standards.json')
    with open(fpath) as f:
        s = json.load(f)
    return s
    