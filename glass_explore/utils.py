from typing import Dict, Tuple

from skimage.color import rgb2lab

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
    buildup['layers'][i]['id'] = props['NFRC_ID']
    buildup['layers'][i]['props'] = props
    buildup['layers'][i]['thickness'] = float(props['Thickness']) #is in mm

    buildup['layers'][i]['coating'] = props['Coated_Side']
    return buildup

if __name__ == "__main__":
    color_code = 628991
    csshex = base10color_to_csshex(color_code)
    print(csshex)
    print(csshex_to_rgb(csshex))
