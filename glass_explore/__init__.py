#(c)2026 Jon Robinson. All Rights Reserved.

import functools
import json
import logging
import os
import subprocess

import pandas as pd

DEBUG = False

class WebPaths:
    ENERGY = '/energy'

URL = "http://glass-explore.floatingintheclouds.com"
OG_DESCRIPTION = "Glass explore calculates thermal and optic properties of double-glazing"

is_railway = os.getenv("RAILWAY_ENVIRONMENT") is not None

if is_railway:

    # Use absolute paths by starting with '/'
    # This points to the mount point at the root of the container
    BASE_VOLUME_PATH = '/igdb'
    SUB_FOLDER = 'storage'  # Adjust if your files are in a subfolder within the mounted volume


    CACHE_PATH = os.path.join(BASE_VOLUME_PATH, 'cache')

    IGDB_SQLITE_PATH = os.path.join(BASE_VOLUME_PATH,SUB_FOLDER,'data', 'igdb.sqlite')
    PARQUET_GLASS_PATH = os.path.join(BASE_VOLUME_PATH,SUB_FOLDER,'data', 'glass.parquet')
    PARQUET_READABLE_GLASS_PATH= os.path.join(BASE_VOLUME_PATH,SUB_FOLDER,  'data','readable_glass.parquet')
    logging.info("Railway environment detected, using paths for railway deployment")
    logging.info(f"IGDB_SQLITE_PATH: {IGDB_SQLITE_PATH}")
    logging.info(f"PARQUET_GLASS_PATH: {PARQUET_GLASS_PATH}")    
    logging.info(f"PARQUET_READABLE_GLASS_PATH: {PARQUET_READABLE_GLASS_PATH}")

    logging.info(f"Checking path: {PARQUET_GLASS_PATH}")
    
    # Debugging check: Does the file actually exist?
    if not os.path.exists(PARQUET_GLASS_PATH):
        logging.info(f"WARNING: {PARQUET_GLASS_PATH} not found. Contents of {BASE_VOLUME_PATH}:")
        try:
            logging.info(os.listdir(BASE_VOLUME_PATH))
        except Exception as e:
            logging.info(f"Could not list volume: {e}")

else:
    CACHE_PATH =  os.path.join('cache')

    IGDB_SQLITE_PATH = os.path.join('data', 'igdb.sqlite')
    PARQUET_GLASS_PATH = os.path.join('data','glass.parquet')
    PARQUET_READABLE_GLASS_PATH= os.path.join('data','readable_glass.parquet')
    logging.info("Local environment detected, using local paths")

PATH_DATA = os.path.join('data')
PATH_STANDARDS = os.path.join('data','standards')
PATH_PRODUCTS = os.path.join('data','products')

DEVTEMP = os.path.join(os.getcwd(),'temp') 

ALL_MANUFACTURERS = '[ALL]'

GRAPHTYPE_TS_TV = 1
COLORSPACE_LAB = 2 
COLORSPACE_RGB = 3

DATATABLE_COLUMNS = ['ID','ProductName','Manufacturer','Thickness','Tvis','Tsol','Rvis1','Rvis2']


try:
    DF_GLASS_TABLE = pd.read_parquet(PARQUET_GLASS_PATH, engine='pyarrow',)

    DF_GLASS_TABLE['_search_blob'] = (
            DF_GLASS_TABLE.index.astype(str) + " " + 
            DF_GLASS_TABLE['Name'].fillna('') + " " + 
            DF_GLASS_TABLE['ProductName'].fillna('')
        ).str.lower()


    SEARCH_GLASS_TABLE = DF_GLASS_TABLE[['ID', 'Name', 'ProductName']].astype(str).agg(' '.join, axis=1)

    CLEAR_6 = 103
    DEFAULT_GRAPH_GLASS = DF_GLASS_TABLE.loc[CLEAR_6]
except FileNotFoundError:
    logging.info("Glass table Parquet file not found")

try:
    DF_READABLE_GLASS_TABLE = pd.read_parquet(PARQUET_READABLE_GLASS_PATH, engine='pyarrow')
except FileNotFoundError:
    logging.info("Readable glass table Parquet file not found")


class Buildup:
    SOLID_LAYERS = 'layers'
    GAS_LAYERS = 'gas_layers'


class SelectedPointProps:
    SIZE_2D = 30
    SIZE_3D = 12
    COLOR_OUTLINE = "black"
    THICKNESS_OUTLINE = 1

class EnergyLayoutID:

    BUTTON_SHARE = "button-share"
    BUTTON_REPORT = "button-report"
    BUTTON_IGDB_SEARCH = "button-igdb-search"

    CARD_HEADER_COATED = "card-coated"
    CARD_HEADER_NONCOATED = "card-non-coated"

    COLUMN_LHS = "column-lhs"
    COLUMN_RHS = "column-rhs"

    DIV_HIDDEN_WINDOW_HT = "div-hidden-window-ht"
    DIV_HIDDEN_SELECTED_ID = "div-selected-id-hidden"
    DIV_GRAPH_IGDB = "div-graph-igdb"
    DIV_DISPLAY_RESIZE = "div-displayresize"

    GRAPH_IGDB = "graph-ts-tv"
    GRAPH_LAB = "graph-lab"

    LINK_COATED_LITE_ID = "link-coated-lite-id"

    MODAL_ABOUT = "modal-splash"
    MODAL_ABOUT_CLOSE = "modal-splash-close"

    MODAL_SETTINGS = "modal-settings"
    MODAL_SETTINGS_CLOSE = "modal-settings-close"

    MODAL_SHARE = "modal-share"
    MODAL_SHARE_CLOSE = "modal-share-close"

    MODAL_SEARCH_IGDB = "modal-search-igdb"
    MODAL_SEARCH_IGDB_CLOSE = "modal-search-igdb-close"
    MODAL_SEARCH_IGDB_OK = "modal-search-igdb-ok"
    MODAL_SEARCH_INPUT_GLASS_SEARCH = "modal-search-input-glass-search"
    MODAL_SEARCH_DATATABLE = "modal-search-datatable"
    MODAL_SEARCH_SELECT_COATED_MANUFACTURER = "modal-search-select-coated-manufacturer"
    MODAL_SEARCH_FORMTEXT_SELECT_COATED_MANUFACTURER = "modal-search-formtext-select-coated-manufacturer"
    MODAL_SEARCH_SELECT_COATED_THICKNESS = "modal-search-select-coated-thickness"



    SELECT_STANDARD = "select-standard"

    SELECT_COATED_MANUFACTURER = "select-manufacturer"
    FORMTEXT_SELECT_COATED_MANUFACTURER = "formtext-select-manufacturer"

    SELECT_GAS = "select-gas"
    INPUT_GAP = "input-gap"

    SWITCH_COATED_GLASS_SIDE = "switch-lowe-side"

    CHECKBOX_FLIP_COATEDLAYER = "checkbox-flip-outerlayer"
    CHECKBOX_ADVANCED_OPTICAL_STANDARD = "checkbox-advance-standard"

    DIV_COATED_LITE_PRODUCT = "div-outerlite-product"
    DIV_BUILDUP_SVG_CONTAINER = "div-buildup-svg-container"
    LINK_GSTR = "div-gstr"

    NAV_GRAPHTYPE = "nav_graphtype"
    
    NAVLINK_ABOUT = "navlink_about"
    NAVLINK_STRUCTURE = "navlink_structure"

    NAVLINK_GRAPHTYPE_TS_TV = 1
    NAVLINK_GRAPHTYPE_LAB = 2 
    NAVLINK_GRAPHTYPE_RGB = 3

    SELECT_COATED_THICKNESS = "select-thickness"

    SELECT_UNCOATED_THICKNESS = "select-innerlayer-thickness"
    SELECT_UNCOATED_SUBSTRATE = "select-innerlayer-substrate"

    SELECT_COATED_MANUFACTURER = "select-manufacturer"
    SELECT_OPTICAL_STANDARD = "select-standard"

    DUMMY_FOR_CALLBACK = "dummy-for-callback"
    STORE_BUILDUP_IN_SESSION = "store-buildup-session"
    STORE_GSTR_FROM_URL = "store-gstr-from-url"
    STORE_SETTINGS_IN_LOCAL = "store-settings-local"

    TABLE_CELL_UVALUE = "table-cell-uvalue"
    TABLE_CELL_SHGC_LABEL = "table-cell-shgc-label"
    TABLE_CELL_SHGC = "table-cell-shgc"
    TABLE_CELL_TVIS_LABEL = "table-cell-tvis-label"
    TABLE_CELL_TVIS = "table-cell-tvis"
    TABLE_CELL_ROUT = "table-cell-rout"
    TABLE_CELL_RIN  = "table-cell-rin"
    TABLE_CELL_COLOR_TRANS = "table-cell-color_trans"
    TABLE_CELL_COLOR_REFL = "table-cell-color_refl"
    
    TABS = "tabs"
    TAB_CONTENT = "tab-content"
    TAB_GRAPH_TS_TV = "tab-graph-ts-tv"
    TAB_GRAPH_LAB = "tab-graph-ab"
    TAB_GRAPH_RGB = "tab-graph-rgb"
   
    URL = "url"




NFRC_OPTICAL_STANDARD = "W5_NFRC_2003.std"
CEN_OPTICAL_STANDARD = "prEN_410.std"

@functools.cache    
def standards():

    fpath = os.path.join(PATH_DATA,'standards.json')
    with open(fpath) as f:
        s = json.load(f)
    return s
    
