
from typing import Dict, List
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

