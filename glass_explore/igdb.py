#(c)2026 Jon Robinson. All Rights Reserved.

import logging
import sqlite3
from functools import cache
from typing import Dict

import pandas as pd
import pywincalc

from glass_explore import IGDB_SQLITE_PATH,DF_GLASS_TABLE

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


# Keys are the gas names shown in the UI and stored in the buildup dict; they are
# also parsed by en673._parse_gas, so the percentages must match the IGDB Gap table.
# Values are IDs in the IGDB Gap table (1-9 NFRC gases, 100-107 their EN 673 variants).
GASES_NFRC_LOOKUP = {
    "air" : 1,
    "argon" : 2,
    "krypton" : 3,
    "xenon" : 4,
    "air(5%), ar(95%)" : 6,
    "air(10%), ar(90%)" : 9,
    "air(5%), kr(95%)" : 8,
    "air(12%), ar(22%), kr(66%)" : 7,
}

GASES_EN673_LOOKUP = {
    "air" : 100,
    "argon" : 101,
    "krypton" : 102,
    "xenon" : 103,
    "air(5%), ar(95%)" : 104,
    "air(10%), ar(90%)" : 107,
    "air(5%), kr(95%)" : 106,
    "air(12%), ar(22%), kr(66%)" : 105,
}

@cache
def db_version() -> float:
    """
    Returns:
        int: IGDB version
    """
    s = DF_GLASS_TABLE['Source'].str.extractall(r'(\d+)')[0].astype(float).groupby(level=0).max()
    return max(s)


def _read_sql(sql: str, params: tuple = ()) -> pd.DataFrame:
    with sqlite3.connect(IGDB_SQLITE_PATH) as cxn:
        return pd.read_sql(sql, cxn, params=params)


def _single_record(raw_df: pd.DataFrame, table_name: str, id_value) -> Dict:
    if raw_df.empty:
        raise LookupError(f"No record found in {table_name} for ID {id_value}")
    return raw_df.to_dict('records')[0]


@cache
def lookup_wavelength_data(glazing_id : int) -> pd.DataFrame:
    """Spectral data for one glazing, in ascending wavelength order.

    The rows of about 5% of products are stored out of wavelength order, and
    np.interp silently returns nonsense for those, so the ordering is done here.

    Args:
        glazing_id (int): Glazing id (note this is not the same as the NFRC id)

    Returns:
        pd.DataFrame: spectral data
    """

    sql = 'select * from SpectralData where GlazingID = ? order by Wavelength'
    return _read_sql(sql, (glazing_id,))


@cache
def lookup_glass_props(nfrc_id : int) -> Dict:
    """
    Performs an SQL (inner) join on data in 'glass' and glazingproperties' tables in IGDB database.

    Args:
        nfrc_id (int): Some confusion -ID in GlassProperties does not align with ID in glass. 

    Returns:
        Dict: Glass props as dictionary
    """
    sql = """
        select
            Glass.ID,
            Glass.Name,
            Glass.Source,
            Glass.SpectralData,
            Glass.AngularFunction,
            GlazingProperties.Thickness as Thickness,
            Glass.Tsol,
            Glass.Rsol1,
            Glass.Rsol2,
            Glass.Tvis,
            Glass.Rvis1,
            Glass.Rvis2,
            Glass.Tir,
            Glass.emis1,
            Glass.emis2,
            GlazingProperties.Conductivity as Conductivity,
            Glass.Comment,
            GlazingProperties.Manufacturer as Manufacturer,
            GlazingProperties.ProductName as ProductName,
            Glass.Color,
            Glass.Certification,
            Glass.Status,
            Glass.Timestamp,
            Glass.Specularity,
            Glass.Tvis2,
            Glass.Tsol2,
            Glass.MaterialID,
            GlazingProperties.GlazingID,
            GlazingProperties.FileName,
            GlazingProperties.NFRC_ID,
            GlazingProperties.Appearance,
            GlazingProperties.Coating_Name,
            GlazingProperties.Coated_Side,
            GlazingProperties.Film_Filename,
            GlazingProperties.Substrate_FileName,
            GlazingProperties.MaterialName,
            GlazingProperties.Acceptance,
            GlazingProperties.TIR,
            GlazingProperties.ef,
            GlazingProperties.Source_ef,
            GlazingProperties.eb,
            GlazingProperties.Source_eb,
            GlazingProperties.DataSource,
            GlazingProperties.Structure_String,
            GlazingProperties.Time_Created,
            GlazingProperties.Database_Version,
            GlazingProperties.Time_LastEdited,
            GlazingProperties.Precalc_StandardName,
            GlazingProperties.Precalc_Time,
            GlazingProperties.Precalc_Tsol,
            GlazingProperties.Precalc_Rfsol,
            GlazingProperties.Precalc_Tvis,
            GlazingProperties.Precalc_Rfvis,
            GlazingProperties.Precalc_Rbvis,
            GlazingProperties.Precalc_TCIEX,
            GlazingProperties.Precalc_TCIEY,
            GlazingProperties.Precalc_TCIEZ,
            GlazingProperties.Precalc_RfCIEX,
            GlazingProperties.Precalc_RfCIEY,
            GlazingProperties.Precalc_RfCIEZ,
            GlazingProperties.Precalc_Tdw,
            GlazingProperties.Precalc_Tuv,
            GlazingProperties.Precalc_TSPF,
            GlazingProperties.Checksum_Date,
            GlazingProperties.IGDB_Checksum,
            GlazingProperties.Precalc_Rbsol,
            GlazingProperties.GlazingTypeID
        from Glass
        inner join GlazingProperties on Glass.ID = GlazingProperties.NFRC_ID
        where Glass.ID = ?
    """
    raw_df = _read_sql(sql, (nfrc_id,))

    return _single_record(raw_df, "Glass", nfrc_id)

def _gas_data_from_gap_row(props: Dict) -> pywincalc.GasData:
    """Build pywincalc GasData from a pure-gas row of the IGDB Gap table."""
    conductivity_coefficients = pywincalc.GasCoefficients(props['ConductivityA'], props['ConductivityB'], props['ConductivityC'])

    viscosity_coefficients = pywincalc.GasCoefficients(props['ViscosityA'], props['ViscosityB'], props['ViscosityC'])

    Cp_coefficients = pywincalc.GasCoefficients(props['CpA'], props['CpB'], props['CpC'])

    return pywincalc.GasData(
        name=props['Name'],
        molecular_weight=props['MolecularWeight'],
        specific_heat_ratio=props['SpecificHeatRatio'],
        Cp=Cp_coefficients,
        thermal_conductivity=conductivity_coefficients,
        viscosity=viscosity_coefficients,
    )


@cache
def lookup_gas_props(igdb_id : int) -> pywincalc.Gas:
    """
    Builds a pywincalc Gas from the IGDB Gap table.

    Pure gases (nGasses == 0) use the coefficients on their own Gap row. Mixtures
    (nGasses > 0) are defined in the GapMixtures table as (component Gap ID, mole
    fraction) pairs; the coefficients on the mixture's own Gap row are placeholders
    (copies of air or SF6) and must not be used.

    Args:
        igdb_id (int): ID in the Gap table

    Returns:
        pywincalc.Gas: pure gas or mixture
    """
    sql = 'select * from Gap where ID = ?'
    props = _single_record(_read_sql(sql, (igdb_id,)), "Gap", igdb_id)

    n_gasses = props.get('nGasses')
    is_mixture = isinstance(n_gasses, (int, float)) and n_gasses > 0
    if not is_mixture:
        return pywincalc.create_gas([[1.0, _gas_data_from_gap_row(props)]])

    components = _read_sql(
        'select GapID, Percentage from GapMixtures where ParentID = ? and Percentage > 0 order by "Index"',
        (igdb_id,),
    )
    if components.empty:
        raise LookupError(f"Gap {igdb_id} ({props['Name']}) is flagged as a mixture but has no GapMixtures components")

    total = float(components['Percentage'].sum())  # stored as float32 fractions, e.g. 0.05 + 0.95 = 0.99999999
    parts = []
    for row in components.itertuples(index=False):
        component = _single_record(_read_sql(sql, (int(row.GapID),)), "Gap", row.GapID)
        parts.append([float(row.Percentage) / total, _gas_data_from_gap_row(component)])

    return pywincalc.create_gas(parts)



if __name__ == "__main__":
    logging.info(f'IGDB v{db_version()}')


    logging.info(lookup_gas_props(4))
