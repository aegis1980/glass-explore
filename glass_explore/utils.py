#(c)2026 Jon Robinson. All Rights Reserved.

import logging
from typing import Dict, Tuple

from skimage.color import rgb2lab

from glass_explore import Buildup

HEX_LETTER = ['a','b','c','d','e','f']
LITTLE_ENDIAN_ORDER = [1,0,3,2,5,4]

def base10color_to_csshex(x: int) -> str:
    """
    IGDB stores 'color' as a 24-bit color code (int between 0 to 16.8million).
    This returns a css hex string format, eg '#ffffff' for white.

    Args:
        x (int): 24bit colour code

    Returns:
        str: hex str starting with '#' and always 7 chars.
    """
    h = ['0'] * 6 
    for i in range(6):
        
        x1 = x % 16
        x = x // 16
        if x1>=10:
            x1 = HEX_LETTER[x1-10]
        h[LITTLE_ENDIAN_ORDER[i]] =  str(x1)   
    return '#' + ''.join(h)


def csshex_to_rgb(csshex: str) -> Tuple[int,int,int]:
    """ Convert a CSS hex string to rgb tuple

    Args:
        csshex (str): css hex color in format '#rrggbb

    Returns:
        Tuple[int,int,int]: Tuple red, green, blue (0..255)
    """
    h = csshex.lstrip('#')
    (r,g,b) = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    return (r,g,b) 


def rgb_to_csshex(r:int,g:int,b:int) -> str:
    """_summary_

    Args:
        r (int): _description_
        g (int): _description_
        b (int): _description_

    Returns:
        str: _description_
    """

    return '#%02x%02x%02x' % (r, g, b)


def rgb_to_lab(rgb : Tuple[int,int,int]):
    lab = rgb2lab([x / 256.0 for x in rgb])
    return  tuple(lab)


def populate_buildup_with_glass_props(buildup: Dict, props:Dict, i : int) -> Dict:
    buildup[Buildup.SOLID_LAYERS][i]['id'] = props['NFRC_ID']
    buildup[Buildup.SOLID_LAYERS][i]['props'] = props
    buildup[Buildup.SOLID_LAYERS][i]['thickness'] = float(props['Thickness']) #is in mm

    buildup[Buildup.SOLID_LAYERS][i]['coating'] = props['Coated_Side']
    return buildup


# Surfaces of a double-glazed unit are numbered from the outside: 1 and 2 are the faces of the
# outer lite, 3 and 4 those of the inner lite, so 2 and 3 face the cavity.
COATING_SURFACES = (1, 2, 3, 4)
DEFAULT_COATING_SURFACE = 2


def has_single_coated_face(coated_side) -> bool:
    """True when the IGDB Coated_Side is 'Front' or 'Back', i.e. exactly one face is coated."""
    return str(coated_side).upper() in ('FRONT', 'BACK')


def _reference_face_is_front(coated_side) -> bool:
    # The reference face is the one the surface number refers to: the coated face, or the
    # IGDB back face for a lite coated on both faces or on neither. With the back face as
    # reference, surfaces 2 and 4 are the lite as measured (not flipped).
    return str(coated_side).upper() == 'FRONT'


def lite_placement_from_surface(surface, coated_side) -> Tuple[bool, bool]:
    """
    Where the selected lite goes for a coating surface number.

    Args:
        surface: 1..4, the surface the lite's reference face is on (see COATING_SURFACES)
        coated_side: IGDB Coated_Side of the lite ('Front', 'Back', 'Both', 'Neither', ...)

    Returns:
        (inside, flipped): inside is True for the inner lite; flipped is the buildup dict's
        'flipped', i.e. the IGDB front face turned towards the inside.
    """
    surface = int(surface)
    if surface not in COATING_SURFACES:
        raise ValueError(f"Coating surface must be one of {COATING_SURFACES}, not {surface}")

    inside = surface >= 3
    on_inward_face = surface in (2, 4)  # the face of the lite that points towards the room
    flipped = on_inward_face == _reference_face_is_front(coated_side)
    return inside, flipped


def surface_from_lite_placement(inside: bool, flipped: bool, coated_side) -> int:
    """Inverse of lite_placement_from_surface: the surface number for a position and flip."""
    on_inward_face = bool(flipped) == _reference_face_is_front(coated_side)
    return (3 if inside else 1) + (1 if on_inward_face else 0)

if __name__ == "__main__":
    color_code = 628991
    csshex = base10color_to_csshex(color_code)
    logging.info(csshex)
    logging.info(csshex_to_rgb(csshex))
