
from typing import Dict, List, Tuple

from glass_explore import DF_GLASS_TABLE

from glass_model import InsulatedGlass,MonoGlass,HeatTreatment,GlassBuildup,GasLayer

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
    for l in _dict['gas_layers']:
        t = float(l['thickness'])
        g = GAS_LOOKUP[l['gas']]
        gas = GasLayer(g,t)
        gases.append(gas)
    
    return gases


def callback_return(igu : InsulatedGlass) -> Tuple:
    gas = GAS_LOOKUP.keys()[list(GAS_LOOKUP.values()).index(igu.gases[0].gas_mixture)] #reverse lookup 
    outer_igdb_id = igu.lites[0].igdbcode
    inner_igdb_id = igu.lites[1].igdbcode
    return \
        {'points' :[{'customdata': DF_GLASS_TABLE.loc[outer_igdb_id]}]}, \
        igu.lites[0].igdbflip, \
        gas, \
        igu.gases[0].t_actual, \
        'clear', \
        6
