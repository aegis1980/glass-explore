#(c)2026 Jon Robinson. All Rights Reserved.

import logging
import re
from typing import Dict, List, Tuple

from glass_explore import DF_GLASS_TABLE, igdb

from glass_explore import callback_helpers
from glass_explore.glass_model import InsulatedGlass,MonoGlass,HeatTreatment,GlassBuildup,GasCavity

GAS_LOOKUP = {
    'air' : GasCavity.AIR,
    'argon' : GasCavity.ARGON,
    'krypton' : GasCavity.KRYPTON,
    'xenon' : GasCavity.XENON
}



def find_nearest(numbers, target):
    return min(numbers, key=lambda x: abs(x - target))

def lites_from_dict(di : Dict) -> List[GlassBuildup]:
    lites = []
    for l in di['layers']:
        _type = l['props']['GlazingTypeID']
        t = l['thickness']
        lite = None
        if _type == 2 or _type == 3: # Monolithic or Coated
            t = find_nearest(MonoGlass.THICKNESSES,t)
            lite = MonoGlass(HeatTreatment.MONO,t)
        elif _type == 6: #Laminated
            pass

        if lite:
            lite.igdbcode = l['id']
            lite.igdbflip = l['flipped']
            lite._t_actual = l['thickness']
            lites.append(lite)
    
    return lites


import re


def _process_gasmix_gstr(gas_mixture: str):
    """_summary_

    Args:
        gas_mixture (_type_): _description_

    Returns:
        _type_: _description_
    """

    pattern = r'[a-zA-Z]+|[0-9]+\.[0-9]+|[0-9]+'
    raw_list = re.findall(pattern, gas_mixture)
    
    # Convert numerical strings to actual float or int types
    processed_list = []
    for item in raw_list:
        if '.' in item:
            processed_list.append(float(item))
        elif item.isdigit():
            processed_list.append(int(item))
        else:
            processed_list.append(item)
    
    parts = []
    for i in range(0, len(processed_list), 2):
        label = processed_list[i]
        value = processed_list[i+1]
        parts.append(f"{label}({value}%)")
    
    return ", ".join(parts)



def gaslayers_from_dict(_dict : Dict) -> GasCavity:
    gases = []
    for layer in _dict['gas_layers']:
        t = float(layer['thickness'])

        if layer['gas'] in GAS_LOOKUP:
            g = GAS_LOOKUP[layer['gas']]
        else:
            g = re.sub(r'[\[\](){}\s%,]', '', layer['gas']).upper() # e.g "air(5%), ar(95%)" becomes "AIR5AR95"

        gas = GasCavity(g,t)
        gases.append(gas)
    
    return gases


def callback_return_from_igu(igu : InsulatedGlass) -> Tuple:

    try:
        gas_idx =list(GAS_LOOKUP.values()).index(igu.gases[0].gas_mixture)
        gas = list(GAS_LOOKUP.keys())[gas_idx] #reverse lookup 
    except ValueError as e:
        mix =igu.gases[0].gas_mixture.lower()
        gas = _process_gasmix_gstr(mix)



    #detect coated side

    if igu.lites[0].igdbcode in igdb.CLEAR_LOOKUP.values() or igu.lites[0].igdbcode in igdb.ULTRACLEAR_LOOKUP.values():
        coated_idx = 1 #ie inner
        uncoated_idx = 0
    else:
        coated_idx = 0 #ie outer
        uncoated_idx = 1


    coated_igdb_id = igu.lites[coated_idx].igdbcode
    uncoated_igdb_id = igu.lites[uncoated_idx].igdbcode
    logging.info(f"Coated IGDB ID: {coated_igdb_id}, Uncoated IGDB ID: {uncoated_igdb_id}")

    result= \
        callback_helpers.clickdata_for_glass_id(coated_igdb_id), \
        DF_GLASS_TABLE.loc[coated_igdb_id]['Manufacturer'], \
        callback_helpers.round_to_nearest_even(DF_GLASS_TABLE.loc[coated_igdb_id]['Thickness']),\
        bool(coated_idx), \
        igu.lites[coated_idx].igdbflip, \
        gas, \
        igu.gases[0].t_actual, \
        'clear' if uncoated_igdb_id in igdb.CLEAR_LOOKUP.values() else 'ultraclear', \
        callback_helpers.round_to_nearest_even(DF_GLASS_TABLE.loc[uncoated_igdb_id]['Thickness'])
    
    return result
