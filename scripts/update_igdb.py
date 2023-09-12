#!/usr/bin/env python
# -*- coding: utf-8 -*-

r"""
Preps Internaotnal Glass Database (IGBD) for use.
File downloaded from LBNL is a password-protected Microsoft Access db file.
All sorts of issues using this on Linux-based (Heroku) server.

Use this script to convert MDB file to SQLITE file. 
Also create h5 file for glass table (for performance) 

Usage: just run this file for defaults.
"""


import os
import sqlite3
import pyodbc
import sqlite3
from collections import namedtuple
import re
import sys

import numpy as np
import pandas as pd
from colorama import Fore,Style

from glass_explore import IGDB_SQLITE_PATH,H5_GLASS_PATH, utils

DEFAULT_LBNL_WINDOWS_MDB_FILE_PATH = "c:/Users/Public/LBNL/WINDOW7.8/w7.mdb"

def decode_sketchy_utf16(raw_bytes):
    s = raw_bytes.decode("utf-16le", "ignore")
    try:
        n = s.index('\u0000')
        s = s[:n]  # respect null terminator
    except ValueError:
        pass
    return s

def hdf_from_glass_table(datasource :str = 'sqlite', path :str = IGDB_SQLITE_PATH, hdf_file_path :str = H5_GLASS_PATH ):
    """
    Creates an hdf file for modified GLASS tables in igdb, for quicker app loads times.

    Args:
        datasource (str, optional): _description_. Defaults to 'sqlite'.
        path (str, optional): _description_. Defaults to IGDB_SQLITE_PATH.
        hdf_file_path (str, optional): _description_. Defaults to H5_GLASS_PATH.
    """

    if datasource == 'pyodbc':
        import pyodbc
        if os.name == 'nt':
            cxn_str = f'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};'
        else:
            cxn_str = f'DRIVER={{mdb-sql}};DBQ={path};' #nb This doent actaully work in linux (on Heruko)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              

        cxn = pyodbc.connect(cxn_str)
        sql = 'select * from Glass' # where thickness > 5.5 and thickness < 6.5'
        raw_df = pd.read_sql(sql,cxn)
    elif datasource == 'sqlite' :
        # Create a SQL connection to our SQLite database
        cxn = sqlite3.connect(path)
        sql = 'select * from Glass' 
        raw_df = pd.read_sql(sql,cxn)

    elif datasource == 'csv':
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

    raw_df.to_hdf(hdf_file_path, key = 'df')


def convert_mdb_to_sqlite(filename_in : str,filename_out:str):

    cnxn = pyodbc.connect('Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};Dbq={};'.format(filename_in))
    cnxn.add_output_converter(pyodbc.SQL_WVARCHAR, decode_sketchy_utf16)

    cursor = cnxn.cursor()

    conn = sqlite3.connect(filename_out)
    c = conn.cursor()

    Table = namedtuple('Table', ['cat', 'schem', 'name', 'type'])

    print ("Converting MDB to SQLITE")

    # get a list of tables
    tables = []
    for row in cursor.tables():
        if row.table_type == 'TABLE':
            t = Table(row.table_cat, row.table_schem, row.table_name, row.table_type)
            tables.append(t)

    for t in tables:
        print("    Converting table: " + t.name + " ... ", end="")
    
        # SQLite tables must being with a character or _
        t_name = t.name
        if not re.match('[a-zA-Z]', t.name):
            t_name = '_' + t_name

        # get table definition
        columns = []
        for row in cursor.columns(table=t.name):
            #print ('    {} [{}({})]'.format(row.column_name, row.type_name, row.column_size))
            col_name = re.sub('[^a-zA-Z0-9]', '_', row.column_name)
            if col_name == 'Index':
                col_name = "'Index'"
            if not row.type_name.startswith(('INT')):
                columns.append('{} {}({})'.format(col_name, row.type_name, row.column_size))
            else:
                columns.append('{} INT'.format(col_name))

        cols = ', '.join(columns)
        #print(cols)    
        # create the table in SQLite
        c.execute('DROP TABLE IF EXISTS "{}"'.format(t_name))
        c.execute('CREATE TABLE "{}" ({})'.format(t_name, cols))
        
        # copy the data from MDB to SQLite
        cursor.execute('SELECT * FROM "{}"'.format(t.name))
        for row in cursor:
            values = []
            for value in row:
                if value is None:
                    values.append(u'NULL')
                else:
                    if isinstance(value, bytearray):
                        value = sqlite3.Binary(value)
                    else:
                        value = u'{}'.format(value)
                    values.append(value)
            v = ', '.join(['?']*len(values))
            sql = 'INSERT INTO "{}" VALUES(' + v + ')'
            c.execute(sql.format(t_name), values)
        print(Fore.GREEN + "done" + Style.RESET_ALL)


    conn.commit()
    print ("Conversion complete")
    conn.close()
    print ("db connections closed")



if __name__ == "__main__":

    convert_mdb_to_sqlite(DEFAULT_LBNL_WINDOWS_MDB_FILE_PATH,IGDB_SQLITE_PATH)
    print()
    hdf_from_glass_table()