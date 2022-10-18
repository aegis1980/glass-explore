"""
Creates an hdf file for modified GLASS tables in igdb, for quicker app loads times.
"""


import os
import sqlite3

import numpy as np
import pandas as pd

from glass_explore import ALL_MANUFACTURERS, utils

DATA_SOURCE = 'sqlite'



if DATA_SOURCE == 'pyodbc':
    import pyodbc
    path = os.path.join('data','igdb.mdb')
    if os.name == 'nt':
        cxn_str = f'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};'
    else:
        cxn_str = f'DRIVER={{mdb-sql}};DBQ={path};' #nb This doent actaully work in linux (on Heruko)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              

    cxn = pyodbc.connect(cxn_str)
    sql = 'select * from Glass' # where thickness > 5.5 and thickness < 6.5'
    raw_df = pd.read_sql(sql,cxn)
elif DATA_SOURCE == 'sqlite':
    path = os.path.join('data', 'igdb.sqlite')
    # Create a SQL connection to our SQLite database
    cxn = sqlite3.connect(path)
    sql = 'select * from Glass' 
    raw_df = pd.read_sql(sql,cxn)

elif DATA_SOURCE == 'csv':
    path = os.path.join('data', 'igdb.csv')
    raw_df = pd.read_csv(path, encoding='ISO-8859-1')
    #raw_df = raw_df[raw_df['Thickness'].between(5.5, 8.5)]



raw_df.set_index('ID', inplace=True, drop=False)

# IGDB uses number for color, we want CSS hex value.
raw_df['CssColor'] = raw_df['Color'].map(lambda x:utils.base10color_to_csshex(x))
raw_df['rgb'] = raw_df['CssColor'].map(lambda x:utils.csshex_to_rgb(x))
raw_df[['RColor','GColor','BColor']] = raw_df['rgb'].apply(pd.Series)
raw_df['lab'] = raw_df['rgb'].map(lambda x:utils.rgb_to_lab(x))
raw_df[['lColor','aColor','bColor']] = raw_df['lab'].apply(pd.Series)
raw_df.drop(columns=['rgb', 'lab'],inplace = True)

path = os.path.join('data', 'glass.h5')
raw_df.to_hdf(path, key = 'df')