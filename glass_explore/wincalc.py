import os
import pywincalc
from glass_explore import PATH_PRODUCTS, PATH_STANDARDS, igdb,results_printer



# Path to the optical standard file.  All other files referenced by the standard file must be in the same directory
# Note:  While all optical standards packaged with WINDOW should work with optical calculations care should be
# taken to use NFRC standards if NFRC thermal results are desired.  This is because for thermal calculations currently
# only ISO 15099 is supported.  While it is possible to use EN optical standards and create thermal results
# those results will not be based on EN 673
optical_standard_path = os.path.join(PATH_STANDARDS, "W5_NFRC_2003.std")
optical_standard = pywincalc.load_standard(optical_standard_path)

glazing_system_width = 1.0  # width of the glazing system in meters
glazing_system_height = 1.0  # height of the glazing system in meters


def generic_uncoated_glass(thickness : int , super_clear : bool):
    clear_6_path = os.path.join(PATH_PRODUCTS, "CLEAR_6.DAT")
    return pywincalc.parse_optics_file(clear_6_path)


def gap_layer(gas : str, thickness: float):
    return  pywincalc.Gap(igdb.GASES[gas], thickness/1000)

def convert_wavelength_data(raw_wavelength_data):
    # Whatever format your raw wavelength data is it will need to be converted to a list of pywincalc.WavelengthData
    # For this example it is assumed that the raw measured values for each wavelength is a dict with keys
    # "wavelength_microns", "transmittance_front", "transmittance_back", "reflectance_front", and "reflectance_back"
    # See the data returned by the raw_wavelength_data function below

    # This can be done as a list comprehension but for clarity in this example it is done in a loop
    pywincalc_wavelength_measured_data = []
    for i in range(len(raw_wavelength_data["GlazingID"])):
        wavelength = raw_wavelength_data["Wavelength"][i]
        # In this case the raw data only has the direct component measured
        # Diffuse measured data is not yet supported in the calculations
        direct_component = pywincalc.OpticalMeasurementComponent(
            raw_wavelength_data["T"][i],
            raw_wavelength_data["Tb"][i],
            raw_wavelength_data["Rf"][i],
            raw_wavelength_data["Rb"][i])
        pywincalc_wavelength_measured_data.append(pywincalc.WavelengthData(wavelength, direct_component))

    return pywincalc_wavelength_measured_data



def run_sim(
        id,
        gap_layer,
        other_layer,
    ):
    # Create optical data for the glass layer

    # Make sure to select the approriate material type for the layer.
    # Current supported options are: 
    # APPLIED_FILM, COATED, ELECTROCHROMIC, FILM, INTERLAYER, LAMINATE, MONOLITHIC, THERMOCHROMIC

    props = igdb.lookup_glass_props(id)

    glass_material_type = pywincalc.MaterialType.MONOLITHIC
    glass_material_thickness =  props['Thickness']/1000  # in metres
    glass_wavelength_measurements = convert_wavelength_data(igdb.lookup_wavelength_data(props['GlazingID']))
    # Since the measurements do not extend to the IR range emissivity and IR transmittances should be provided
    # If there are measurements that extend to the IR range these values can be provided but result calculated
    # from the measurements will be used
    glass_emissivity_front = props['emis1']
    glass_emissivity_back = props['emis2']
    glass_ir_transmittance_front = props['Tir']
    glass_ir_transmittance_back = props['Tir']
    glass_coated_side = props['Coated_Side']
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
    glass_conductivity = props['Conductivity']
    # Since thermal openings in this case are all zero they can be omitted.  They are included he for example purposes.
    glass_opening_top = 0
    glass_opening_bottom = 0
    glass_opening_left = 0
    glass_opening_right = 0

    glass_thermal = pywincalc.ProductDataThermal(glass_conductivity, glass_material_thickness, flipped, glass_opening_top,
                                                glass_opening_bottom, glass_opening_left, glass_opening_right)

    # Create a glass layer from both the optical and thermal data
    coated_layer = pywincalc.ProductDataOpticalAndThermal(glass_n_band_optical_data, glass_thermal)

    # Create a glazing system using the NFRC U environment in order to get NFRC U results
    # U and SHGC can be caculated for any given environment but in order to get results
    # The NFRC U and SHGC environments are provided as already constructed environments and Glazing_System
    # defaults to using the NFRC U environments
    glazing_system_u_environment = pywincalc.GlazingSystem(optical_standard=optical_standard,
                                                        solid_layers=[coated_layer],
                                                        width_meters=glazing_system_width,
                                                        height_meters=glazing_system_height,
                                                        environment=pywincalc.nfrc_u_environments())

    # In order to get NFRC SHGC results the NFRC SHGC environment should be used when creating the glazing system
    glazing_system_shgc_environment = pywincalc.GlazingSystem(optical_standard=optical_standard,
                                                            solid_layers=[coated_layer,other_layer],
                                                            gap_layers=[gap_layer],
                                                            width_meters=glazing_system_width,
                                                            height_meters=glazing_system_height,
                                                            environment=pywincalc.nfrc_shgc_environments())


    #results_printer.print_results(glazing_system_u_environment, glazing_system_shgc_environment)
    print('done')
    return glazing_system_u_environment, glazing_system_shgc_environment

if __name__ == "__main__":
    run_sim(id = 11594)