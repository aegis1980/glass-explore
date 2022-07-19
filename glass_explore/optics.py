

def create_file(id:int, temp = True):
    thickness = 0
    structure = []

    s = f"""
        {{ Units, Wavelength Units }} SI Microns
        {{ Thickness }}  {thickness}
        {{ Conductivity }} {conductivity}
        {{ IR Transmittance }} TIR=0
        {{ Emissivity, front back }} Emis= 0.84 0.84
        {{ }}
        {{ Ef_Source: Material }}
        {{ Eb_Source: Material }}
        {{ IGDB_Checksum: -1717699038 }}
        {{ Product Name: Generic Clear Glass }}
        {{ Manufacturer: Generic }}
        {{ NFRC ID: 102 }}
        {{ Type: Monolithic }}
        {{ Material: Glass }}
        {{ Coating Name: N/A }}
        {{ Coated Side: Neither }}
        {{ Substrate Filename: N/A }}
        {{ Appearance: Clear }}
        {{ Acceptance: # }}
        {{ Uses:  }}
        {{ Availability:   }}
        {{ Structure:  }}
        {structure}

    """