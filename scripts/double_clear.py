import pywincalc
import os
from glass_explore import PATH_STANDARDS, dat, results_printer,PATH_PRODUCTS,igdb

# Path to the optical standard file.  All other files referenced by the standard file must be in the same directory
# Note:  While all optical standards packaged with WINDOW should work with optical calculations care should be
# taken to use NFRC standards if NFRC thermal results are desired.  This is because for thermal calculations currently
# only ISO 15099 is supported.  While it is possible to use EN optical standards and create thermal results
# those results will not be based on EN 673
optical_standard_path = os.path.join(PATH_STANDARDS,"W5_NFRC_2003.std")
optical_standard = pywincalc.load_standard(optical_standard_path)

width = 1.0  # width of the glazing system in meters
height = 1.0  # height of the glazing system in meters


props = igdb.lookup_glass_props(103)
wavelength_df = igdb.lookup_wavelength_data(props['GlazingID'])
clear_6 = dat.make_datfile(props,wavelength_df)

# Create a list of solid layers in order from outside to inside
# This is a double glazing where the outside and inside are the glass
# that was just loaded and the middle is the same glass as the single clear example above
solid_layers = [clear_6, clear_6]

# Solid layers must be separated by gap layers
# Currently there are four pre-defined gases available: Air, Argon, Krypton, and Xenon
# Vacuum gaps are not yet supported
# To create a gap with 100% of a predefined gas create a Gap_Data object with the gas type
# and thickness in meters
gap_1 = pywincalc.Gap(pywincalc.PredefinedGasType.AIR, .0127)  # .0127 is gap thickness in meters


# Put all gaps into a list ordered from outside to inside
# Note:  This is only specifying gaps between solid layers
# Gases on the interior and exterior of the glazing system are more fixed and only subject to
# change based on the properties in the environmental conditions
gaps = [gap_1]

# Create a glazing system using the NFRC U environment in order to get NFRC U results
# U and SHGC can be caculated for any given environment but in order to get results
# The NFRC U and SHGC environments are provided as already constructed environments and Glazing_System
# defaults to using the NFRC U environments
glazing_system_u_environment = pywincalc.GlazingSystem(optical_standard, solid_layers, gaps, width, height)
# If SHGC results for the NFRC SHGC environment are needed create a glazing system with that environment
glazing_system_shgc_environment = pywincalc.GlazingSystem(optical_standard=optical_standard,
                                                                       solid_layers=solid_layers,
                                                                       gap_layers=gaps,
                                                                       width_meters=width,
                                                                       height_meters=height,
                                                                       environment=pywincalc.nfrc_shgc_environments())

results_name = "Results for a double-clear system"
print("*" * len(results_name))
print(results_name)
print("*" * len(results_name))
results_printer.print_results(glazing_system_u_environment, glazing_system_shgc_environment)