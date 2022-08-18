

def create_dat(**data):
    s = f"""
        {{ Units, Wavelength Units }} SI Microns
        {{ Thickness }}  {data['thickness']}
        {{ Conductivity }} {data['conductivity']}
        {{ IR Transmittance }} TIR= {data['tir']}
        {{ Emissivity, front back }} Emis= {data['emissivity_f']} {data['emissivity_b']}
        {{ }}
        {{ Ef_Source: {data['ef_source'] or 'Material'} }}
        {{ Eb_Source: {data['eb_source'] or 'Material'}  }}
        {{ IGDB_Checksum: {data['igdb_checksum']} }}
        {{ Product Name: {data['product_name']} }}
        {{ Manufacturer: {data['manufacturer']} }}
        {{ NFRC ID: {data['id']} }}
        {{ Type: {data['type']} }}
        {{ Material: {data['material'] or 'Glass'} }}
        {{ Coating Name: {data['coating_name'] or 'N/A'} }}
        {{ Coated Side: {data['coated_side'] or 'Neither'} }}
        {{ Substrate Filename: {data['substrate_filename'] or 'N/A'}  }}
        {{ Appearance: {data['appearance']}}}
        {{ Acceptance: {data['coated_side'] or '#'} }}
        {{ Uses:  }}
        {{ Availability:   }}
        {{ Structure:  }}
        {data['structure']}

    """