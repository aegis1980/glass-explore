import logging
import os

import pywincalc
from glass_explore import PATH_PRODUCTS, PATH_STANDARDS

logging.basicConfig(level=logging.INFO, format="%(message)s")

def convert(filename):
    in_data = False
    pywincalc_wavelength_measured_data = []
    with open(filename) as file:
        while (line := file.readline().rstrip()):
            if "Structure" in line:
                in_data = True
                continue
            if in_data:
                points = line.split('    ')
                pywincalc_wavelength_measured_data.append(
                    pywincalc.WavelengthData(
                        float(points[0]), #wavelength_microns:
                        float(points[1]), #direct_transmittance
                        float(points[2]),#direct_reflectance_front:
                        float(points[3]) #direct_reflectance_back:
                     ))

    return pywincalc_wavelength_measured_data

glass_wavelength_measurements = convert(os.path.join(PATH_PRODUCTS,'CLEAR_6.DAT'))
# Path to the optical standard file.  All other files referenced by the standard file must be in the same directory
# Note:  While all optical standards packaged with WINDOW should work with optical calculations care should be
# taken to use NFRC standards if NFRC thermal results are desired.  This is because for thermal calculations currently
# only ISO 15099 is supported.  While it is possible to use EN optical standards and create thermal results
# those results will not be based on EN 673
optical_standard_path = os.path.join(PATH_STANDARDS,"W5_NFRC_2003.std")
optical_standard = pywincalc.load_standard(optical_standard_path)

glazing_system_width = 1.0  # width of the glazing system in meters
glazing_system_height = 1.0  # height of the glazing system in meters


# Create optical data for the glass layer

# Make sure to select the approriate material type for the layer.
# Current supported options are: 
# APPLIED_FILM, COATED, ELECTROCHROMIC, FILM, INTERLAYER, LAMINATE, MONOLITHIC, THERMOCHROMIC
glass_material_type = pywincalc.MaterialType.MONOLITHIC
glass_material_thickness = 5.715 /1000  

# Since the measurements do not extend to the IR range emissivity and IR transmittances should be provided
# If there are measurements that extend to the IR range these values can be provided but result calculated
# from the measurements will be used
glass_emissivity_front = .84
glass_emissivity_back = .84
glass_ir_transmittance_front = 0
glass_ir_transmittance_back = 0
glass_coated_side = pywincalc.CoatedSide.NEITHER
flipped = False

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
glass_conductivity = 1
# Since thermal openings in this case are all zero they can be omitted.  They are included he for example purposes.
glass_opening_top = 0
glass_opening_bottom = 0
glass_opening_left = 0
glass_opening_right = 0

glass_thermal = pywincalc.ProductDataThermal(glass_conductivity,glass_material_thickness)

# Create a glass layer from both the optical and thermal data
glass_layer = pywincalc.ProductDataOpticalAndThermal(glass_n_band_optical_data, glass_thermal)

# Create a glazing system using the NFRC U environment in order to get NFRC U results
# U and SHGC can be caculated for any given environment but in order to get results
# The NFRC U and SHGC environments are provided as already constructed environments and Glazing_System
# defaults to using the NFRC U environments
glazing_system_u_environment = pywincalc.GlazingSystem(optical_standard=optical_standard,
                                                       solid_layers=[glass_layer],
                                                       width_meters=glazing_system_width,
                                                       height_meters=glazing_system_height)

# In order to get NFRC SHGC results the NFRC SHGC environment should be used when creating the glazing system
glazing_system_shgc_environment = pywincalc.GlazingSystem(optical_standard=optical_standard,
                                                          solid_layers=[glass_layer],
                                                          width_meters=glazing_system_width,
                                                          height_meters=glazing_system_height,
                                                          environment=pywincalc.nfrc_shgc_environments())

results_name = "Results for a single-layer system with a single glazing layer made from user-defined spectral data."
logging.info("*" * len(results_name))
logging.info(results_name)
logging.info("*" * len(results_name))
