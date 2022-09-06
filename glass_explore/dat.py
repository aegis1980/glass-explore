from os import fdopen
import os
import tempfile
import pywincalc
import pandas as pd
import shutil

_TYPES = {
    1 : "Unknown",
    2 : "Monolithic",
    3 : "Coated",
    4 : "Film",
    5 : "Applied Film",
    6 : "Laminate",
    7 : "Interlayer",
    8 : "Glazing System",
    9 : "Electrochromic",
    10 : "Thermochromic"
}


def _convert_wavelength_data_dat(raw_wavelength_df : pd.DataFrame):
    data = []
    for i,row in raw_wavelength_df.iterrows():
        w =float(row["Wavelength"])
        t = float(row["T"])
        tb = float(row["Tb"])
        rf = float(row["Rf"])
        rb = float(row["Rb"])
        #data.append(f'{w:.3f}    {t:.4f}    {rf:.4f}    {rb:.4f}')
        data.append(f'{w}    {t}    {rf}    {rb}')
    return "\n".join(data)


def make_datfile(props, raw_wavelength_df : pd.DataFrame, write_to_path = None):
    s = f"""{{ Units, Wavelength Units }} SI Microns
{{ Thickness }} {props['Thickness']} 
{{ Conductivity }} {props['Conductivity']}
{{ IR Transmittance }} TIR= {props['TIR']}
{{ Emissivity, front back }} Emis= {props['emis1']} {props['emis2']}
{{ }}
{{ Ef_Source: {props['Source_ef']} }}
{{ Eb_Source: {props['Source_eb']} }}
{{ IGDB_Checksum: {props['IGDB_Checksum']} }}
{{ Product Name: {props['ProductName']} }}
{{ Manufacturer: {props['Manufacturer']} }}
{{ NFRC ID: {props['NFRC_ID']} }}
{{ Type: {_TYPES[props['GlazingTypeID']]} }}
{{ Material: {props['MaterialName']} }}
{{ Coating Name: {props['Coating_Name']} }}
{{ Coated Side: {props['Coated_Side']} }}
{{ Substrate Filename: {props['Substrate_FileName']} }}
{{ Appearance: {props['Appearance']} }}
{{ Acceptance: # }}
{{ Uses:  }}
{{ Availability:   }}
{{ Structure:  }}
{_convert_wavelength_data_dat(raw_wavelength_df)}"""

    fd, path = tempfile.mkstemp()
    try:
        with os.fdopen(fd, 'w') as tmp:
            # do stuff with temp file
            tmp.write(s)
        layer = pywincalc.parse_optics_file(path)
        if write_to_path:
            shutil.copyfile(path,write_to_path)
    finally:
        os.remove(path)
    
    return layer






from glass_explore import igdb

CLEAR_6 = 103
LOW_E = 9923

props = igdb.lookup_glass_props(LOW_E)
wavelength_df = igdb.lookup_wavelength_data(props['GlazingID'])
path = os.path.join(os.getcwd(),'c1.dat')
clear_6 = make_datfile(props,wavelength_df, path)