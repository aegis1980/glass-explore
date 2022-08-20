
import sqlite3
from typing import Dict
import os
import numpy as np
import pandas as pd
import pywincalc


GASES = {
    "air" : pywincalc.PredefinedGasType.AIR,
    "argon" : pywincalc.PredefinedGasType.ARGON
}

path = os.path.join('data', 'igdb.sqlite')

def lookup_wavelength_data(id : int) -> Dict:
    """
        Return spectral data for given product (id)

    Args:
        id (int): igdb GlazingID

    Returns:
        Dict: _description_
    """
    # Create a SQL connection to our SQLite database
    cxn = sqlite3.connect(path)

    sql = f'select * from SpectralData where GlazingID = {id}'
    raw_df = pd.read_sql(sql,cxn)
    return raw_df.to_dict()


def coated_side(side : str):
    
    s = pywincalc.CoatedSide.NEITHER

    if side == 'Back':
        s = pywincalc.CoatedSide.BACK
    elif side == 'Front':
        s = pywincalc.CoatedSide.FRONT
    elif side == 'Both':
        s = pywincalc.CoatedSide.BOTH

    return s
    

def lookup_glass_props(nfrc_id : int) -> Dict:
    sql = f'select * from Glass INNER JOIN GlazingProperties on Glass.ID=GlazingProperties.NFRC_ID where ID = {nfrc_id} ' 
    # Create a SQL connection to our SQLite database
    cxn = sqlite3.connect(path)

    raw_df = pd.read_sql(sql,cxn)
    props =  raw_df.to_dict('records')[0]

    props['Coated_Side'] = coated_side(props['Coated_Side'])

    return props
