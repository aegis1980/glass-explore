import functools
import sqlite3
from typing import Dict
import os
import numpy as np
import pandas as pd
import pywincalc

# nfrc ids for generic clear glasses.
CLEAR_LOOKUP = {
    3 : 102,
    4 : 119,
    5 : 120,
    6 : 103,
    8 : 121,
    10 : 122,
    12 : 123
}

# note these are AGC clearvision low iron products, 
# used as 'generic'
ULTRACLEAR_LOOKUP = {
    3 : 4337,
    4 : 4342,
    5 : 4341,
    6 : 4340,
    8 : 4336,
    10 : 4339,
    12 : 4338  
}


GASES = {
    "air" : pywincalc.PredefinedGasType.AIR,
    "argon" : pywincalc.PredefinedGasType.ARGON
}

path = os.path.join('data', 'igdb.sqlite')

def lookup_wavelength_data(id : int) -> pd.DataFrame:
    """_summary_

    Args:
        id (int): Glazing id (note this is not the same as the NFRC id)

    Returns:
        pd.DataFrame: spectral data
    """

    # Create a SQL connection to our SQLite database
    cxn = sqlite3.connect(path)

    sql = f'select * from SpectralData where GlazingID = {id}'
    return pd.read_sql(sql,cxn)



    
#functools.cache
def lookup_glass_props(nfrc_id : int) -> Dict:
    """
    Performs an SQL (inner) join on data in 'glass' and glazingproperties' tables in IGDB database.

    Args:
        nfrc_id (int): Some confusion -ID in GlassProperties does not align with ID in glass. 

    Returns:
        Dict: Glass props as dictionary
    """
    sql = f'select * from Glass INNER JOIN GlazingProperties on Glass.ID=GlazingProperties.NFRC_ID where ID = {nfrc_id} ' 
    # Create a SQL connection to our SQLite database
    cxn = sqlite3.connect(path)

    raw_df = pd.read_sql(sql,cxn)
    props =  raw_df.to_dict('records')[0]



    return props
