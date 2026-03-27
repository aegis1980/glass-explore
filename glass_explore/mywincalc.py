#(c)2026 Jon Robinson. All Rights Reserved.

import functools
import os
from typing import Dict

import pandas as pd
import pywincalc

from glass_explore import PATH_STANDARDS, igdb, optics,Buildup
import glass_explore


def load_optical_standard(filename):
    # Path to the optical standard file.  All other files referenced by the standard file must be in the same directory
    # Note:  While all optical standards packaged with WINDOW should work with optical calculations care should be
    # taken to use NFRC standards if NFRC thermal results are desired.  This is because for thermal calculations currently
    # only ISO 15099 is supported.  While it is possible to use EN optical standards and create thermal results
    # those results will not be based on EN 673
    optical_standard_path = os.path.join(PATH_STANDARDS, filename or glass_explore.NFRC_OPTICAL_STANDARD)
    return pywincalc.load_standard(optical_standard_path)

glazing_system_width = 1.0  # width of the glazing system in meters
glazing_system_height = 1.0  # height of the glazing system in meters

def coated_side(side : str):
    
    s = pywincalc.CoatedSide.NEITHER

    if side.upper() == 'BACK':
        s = pywincalc.CoatedSide.BACK
    elif side.upper() == 'FRONT':
        s = pywincalc.CoatedSide.FRONT
    elif side.upper() == 'BOTH':
        s = pywincalc.CoatedSide.BOTH

    return s

def gap_layer(gas : str, standard : str, thickness: float):

    if standard == "nfrc":
        gas_id = igdb.GASES_NFRC_LOOKUP[gas]
    else:   
        gas_id = igdb.GASES_EN673_LOOKUP[gas]

    gas = igdb.lookup_gas_props(gas_id)  

    return  pywincalc.Layers.gap(
        thickness = float(thickness)/1000,
        gas=gas
    )



def _convert_wavelength_data(raw_wavelength_df : pd.DataFrame):
    # Whatever format your raw wavelength data is it will need to be converted to a list of pywincalc.WavelengthData
    # For this example it is assumed that the raw measured values for each wavelength is a dict with keys
    # "wavelength_microns", "transmittance_front", "transmittance_back", "reflectance_front", and "reflectance_back"
    # See the data returned by the raw_wavelength_data function below

    # This can be done as a list comprehension but for clarity in this example it is done in a loop
    pywincalc_wavelength_measured_data = []
    for i,row in raw_wavelength_df.iterrows():
        wavelength = row["Wavelength"]
        # In this case the raw data only has the direct component measured
        # Diffuse measured data is not yet supported in the calculations
        direct_component = pywincalc.OpticalMeasurementComponent(
            row["T"],
            row["Tb"],
            row["Rf"],
            row["Rb"]
        )

        pywincalc_wavelength_measured_data.append(pywincalc.WavelengthData(wavelength, direct_component))

    return pywincalc_wavelength_measured_data




def glass_layer_from_props(props, flipped = False):
    # Create optical data for the glass layer

    # Make sure to select the approriate material type for the layer.
    # Current supported options are: 
    # APPLIED_FILM, COATED, ELECTROCHROMIC, FILM, INTERLAYER, LAMINATE, MONOLITHIC, THERMOCHROMIC
    glass_material_type = pywincalc.MaterialType.MONOLITHIC
    glass_material_thickness =  props['Thickness']/1000  # in mm in db. pywincalc wants meters.
    glass_wavelength_measurements = _convert_wavelength_data(igdb.lookup_wavelength_data(props['GlazingID']))
    # Since the measurements do not extend to the IR range emissivity and IR transmittances should be provided
    # If there are measurements that extend to the IR range these values can be provided but result calculated
    # from the measurements will be used
    glass_emissivity_front = props['emis1']
    glass_emissivity_back = props['emis2']
    glass_ir_transmittance_front =0 # props['Tir']
    glass_ir_transmittance_back =0 # props['Tir']
    glass_coated_side = coated_side(props['Coated_Side'])

    glass_n_band_optical_data = pywincalc.ProductDataOpticalNBand(glass_material_type,
                                                                glass_material_thickness,
                                                                glass_wavelength_measurements,
                                                                glass_coated_side,
                                                                glass_emissivity_front,
                                                                glass_emissivity_back,
                                                                glass_ir_transmittance_front,
                                                                glass_ir_transmittance_back,
                                                                flipped)

    # Next create the thermal data for the glass layer
    glass_conductivity = props['Conductivity']
    # Since thermal openings in this case are all zero they can be omitted.  They are included he for example purposes.
    glass_opening_top = 0
    glass_opening_bottom = 0
    glass_opening_left = 0
    glass_opening_right = 0

    glass_thermal = pywincalc.ProductDataThermal(glass_conductivity, glass_material_thickness, flipped,)

    # Create a glass layer from both the optical and thermal data
    return pywincalc.ProductDataOpticalAndThermal(glass_n_band_optical_data, glass_thermal)


def generic_uncoated_glass_props(thickness : int , ultraclear : bool):
    if ultraclear:
        id = igdb.ULTRACLEAR_LOOKUP[thickness]
    else:
        id = igdb.CLEAR_LOOKUP[thickness]
    props = igdb.lookup_glass_props(id)
    return props


def generic_uncoated_glass(thickness : int , ultraclear : bool):
    if ultraclear:
        id = igdb.ULTRACLEAR_LOOKUP[thickness]
    else:
        id = igdb.CLEAR_LOOKUP[thickness]
    props = igdb.lookup_glass_props(id)
    wavelength_df = igdb.lookup_wavelength_data(props['GlazingID'])
    return optics.product_from_tempfile(props,wavelength_df)

    #return glass_layer_from_props(props)


def run_nfrc_analysis(buildup : Dict):
    
    optical_standard = load_optical_standard(glass_explore.NFRC_OPTICAL_STANDARD)

    solid_layers = []
    gas_layers = []

    for l in buildup[Buildup.SOLID_LAYERS]:
        props = igdb.lookup_glass_props(l['id'])
        wavelength_df = igdb.lookup_wavelength_data(props['GlazingID'])
        layer = optics.product_from_tempfile(props,wavelength_df,flipped=l['flipped'])
        solid_layers.append(layer)

    for g in buildup[Buildup.GAS_LAYERS]:
        gap = gap_layer(g['gas'],'nfrc', g['thickness'])
        gas_layers.append(gap)
    # Create a glazing system using the NFRC U environment in order to get NFRC U results
    # U and SHGC can be caculated for any given environment but in order to get results
    # The NFRC U and SHGC environments are provided as already constructed environments and Glazing_System
    # defaults to using the NFRC U environments
    glazing_system_u_environment = pywincalc.GlazingSystem(optical_standard=optical_standard,
                                                        solid_layers=solid_layers,
                                                        gap_layers=gas_layers,
                                                        width_meters=glazing_system_width,
                                                        height_meters=glazing_system_height)

    # In order to get NFRC SHGC results the NFRC SHGC environment should be used when creating the glazing system
    glazing_system_shgc_environment = pywincalc.GlazingSystem(optical_standard=optical_standard,
                                                            solid_layers=solid_layers,
                                                            gap_layers=gas_layers,
                                                            width_meters=glazing_system_width,
                                                            height_meters=glazing_system_height,
                                                            environment=pywincalc.nfrc_shgc_environments())


    #results_printer.print_results(glazing_system_u_environment, glazing_system_shgc_environment)
    #results_printer.print_optical_method_results(glazing_system_u_environment, "SOLAR", 0, 0, '')
    return glazing_system_u_environment, glazing_system_shgc_environment


def run_cen_analysis(buildup : Dict):
    
    optical_standard = load_optical_standard(glass_explore.CEN_OPTICAL_STANDARD)


    # EN673-like Boundary Conditions
    inside_environment = pywincalc.Environment(
        air_temperature=293.15,   # 20 C
        pressure=101325.0,
        convection_coefficient=7.0,
        coefficient_model=pywincalc.BoundaryConditionsCoefficientModelType.HC_PRESCRIBED,
        radiation_temperature=293.15,
        emissivity=1.0,
        air_speed=0.0,
        air_direction=pywincalc.AirHorizontalDirection.NONE,
        direct_solar_radiation=0.0,
    )

    outside_environment = pywincalc.Environment(
        air_temperature=273.15,   # 0 C
        pressure=101325.0,
        convection_coefficient=25.0,
        coefficient_model=pywincalc.BoundaryConditionsCoefficientModelType.HC_PRESCRIBED,
        radiation_temperature=273.15,
        emissivity=1.0,
        air_speed=0.0,
        air_direction=pywincalc.AirHorizontalDirection.NONE,
        direct_solar_radiation=0.0,
    )

    en673_env = pywincalc.Environments(
        outside_environment,
        inside_environment,
    )


    solid_layers = []
    gap_layers = []

    for l in buildup[Buildup.SOLID_LAYERS]:
        props = igdb.lookup_glass_props(l['id'])
        wavelength_df = igdb.lookup_wavelength_data(props['GlazingID'])
        layer = optics.product_from_tempfile(props,wavelength_df,flipped=l['flipped'])
        solid_layers.append(layer)

    for g in buildup[Buildup.GAS_LAYERS]:
        gap = gap_layer(g['gas'],'en673', g['thickness'])
        gap_layers.append(gap)

    glazing_system_u_environment = pywincalc.GlazingSystem(
                                                        solid_layers=solid_layers,
                                                        gap_layers=gap_layers,
                                                        width_meters=glazing_system_width,
                                                        height_meters=glazing_system_height,
                                                        environment=en673_env)

    # In order to get NFRC SHGC results the NFRC SHGC environment should be used when creating the glazing system
    glazing_system_shgc_environment = pywincalc.GlazingSystem(optical_standard=optical_standard,
                                                            solid_layers=solid_layers,
                                                            gap_layers=gap_layers,
                                                            width_meters=glazing_system_width,
                                                            height_meters=glazing_system_height,
                                                            environment=en673_env)


    #results_printer.print_results(glazing_system_u_environment, glazing_system_shgc_environment)
    #results_printer.print_optical_method_results(glazing_system_u_environment, "SOLAR", 0, 0, '')
    return glazing_system_u_environment, glazing_system_shgc_environment
