#(c)2026 Jon Robinson. All Rights Reserved.

import logging
from typing import Dict, List, Tuple

from glass_explore import DF_GLASS_TABLE, igdb

from glass_explore import callback_helpers
from glass_explore.glass_model import InsulatedGlass,MonoGlass,HeatTreatment,GlassBuildup,GasLayer

GAS_LOOKUP = {
    'air' : GasLayer.AIR,
    'argon' : GasLayer.ARGON,
    'krypton' : GasLayer.KRYPTON,
    'xenon' : GasLayer.XENON
}



def find_nearest(numbers, target):
    return min(numbers, key=lambda x: abs(x - target))

def lites_from_dict(di : Dict) -> List[GlassBuildup]:
    lites = []
    for l in di['layers']:
        _type = l['props']['GlazingTypeID']
        t = l['thickness']
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


def gaslayers_from_dict(_dict : Dict) -> GasLayer:
    gases = []
    for layer in _dict['gas_layers']:
        t = float(layer['thickness'])
        g = GAS_LOOKUP[layer['gas']]
        gas = GasLayer(g,t)
        gases.append(gas)
    
    return gases


def callback_return_from_igu(igu : InsulatedGlass) -> Tuple:

    gas_idx =list(GAS_LOOKUP.values()).index(igu.gases[0].gas_mixture)
    gas = list(GAS_LOOKUP.keys())[gas_idx] #reverse lookup 

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
        {'points' :[{'customdata': DF_GLASS_TABLE.loc[coated_igdb_id]}]}, \
        DF_GLASS_TABLE.loc[coated_igdb_id]['Manufacturer'], \
        callback_helpers.round_to_nearest_even(DF_GLASS_TABLE.loc[coated_igdb_id]['Thickness']),\
        bool(coated_idx), \
        igu.lites[coated_idx].igdbflip, \
        gas, \
        igu.gases[0].t_actual, \
        'clear' if uncoated_igdb_id in igdb.CLEAR_LOOKUP.values() else 'ultraclear', \
        callback_helpers.round_to_nearest_even(DF_GLASS_TABLE.loc[uncoated_igdb_id]['Thickness'])
    
    return result
