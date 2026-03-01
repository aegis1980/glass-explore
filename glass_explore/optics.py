#(c)2026 Jon Robinson. All Rights Reserved.

import os
import shutil
import tempfile

import pandas as pd
import pywincalc

# TODO Should get from database GlazingTypes table
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


def _convert_wavelength_data_dat(raw_wavelength_df : pd.DataFrame, flipped = False):
    """_summary_

    Args:
        raw_wavelength_df (pd.DataFrame): _description_
        flipped (bool, optional): _description_. Defaults to False.

    Returns:
        str : spectral data  four-space separated string
    """

    data = []
    for i,row in raw_wavelength_df.iterrows():
        w =row["Wavelength"]
        t = row["T"]
        tb = row["Tb"]
        rf = row["Rb"] if flipped else row["Rf"]
        rb = row["Rf"] if flipped else row["Rb"]
        data.append(f'{w:.3f}    {t:.4f}    {rf:.4f}    {rb:.4f}')
    return "\n".join(data)


def product_from_tempfile(props, raw_wavelength_df : pd.DataFrame, flipped = False, write_to_path = None) -> pywincalc.ProductData:
    """
    Make pywincalc glass layer via a temp optics file
    This is my workaround for not being able to get 'custom glass' approach not working
    """
    emis1 = props['emis2'] if flipped else props['emis1'] 
    emis2 = props['emis1'] if flipped else props['emis2'] 

    source_ef = props['Source_eb'] if flipped else props['Source_ef']
    source_eb = props['Source_ef'] if flipped else props['Source_eb']
    
  #  if flipped:
  #      if props['Coated_Side'] == 'Back':
  #          props['Coated_Side'] = 'Front'
  #      elif props['Coated_Side'] == 'Front':
  #          props['Coated_Side'] = 'Back'


    s = f"""{{ Units, Wavelength Units }} SI Microns
{{ Thickness }} {props['Thickness']:.3f} 
{{ Conductivity }} {props['Conductivity']:.3f}
{{ IR Transmittance }} TIR= {props['TIR']}
{{ Emissivity, front back }} Emis= {emis1:.3f} {emis2:.3f}
{{ }}
{{ Ef_Source: {source_ef} }}
{{ Eb_Source: {source_eb} }}
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
{_convert_wavelength_data_dat(raw_wavelength_df,flipped)}"""


    


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





if __name__ == "__main__":
    from glass_explore import igdb

    CLEAR_6 = 103
    LOW_E = 9923

    props = igdb.lookup_glass_props(CLEAR_6)
    wavelength_df = igdb.lookup_wavelength_data(props['GlazingID'])
    path = os.path.join(os.getcwd(),'c1.dat')
    clear_6 = product_from_tempfile(props,wavelength_df, path)