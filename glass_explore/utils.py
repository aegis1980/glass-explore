def base10color_to_csshex_old(x: int, reverse  : bool = True) -> str:
    """
    IGDB stores 'color' as a 24-bit color code (int between 0 to 16.8million).
    This returns a css hex string format, eg '#ffffff' for white.

    Args:
        x (int): 24bit colour code
        reverse (bool) : swaps 'Red' and 'Blue', eg #c93658 -> #5836c9

    Returns:
        str: hex str starting with '#' and always 7 chars.
    """
    s = '#' + str("{0:#0{1}x}".format(x,6))[2:]
    if len(s)<7:
        s = s[0:5] + '0' + s[-1]
    if reverse:
        s = s[0] + s[-2:] + s[3:5]  + s[1:3]  
    return s


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


if __name__ == "__main__":
    print(base10color_to_csshex(628991))
