def base10color_to_csshex(x: int) -> str:
    """
    IGDB stores 'color' as a 24-bit color code (int between 0 to 16.8million).
    This returns a css hex string format, eg '#ffffff' for white.

    Args:
        x (int): 

    Returns:
        str: hex str starting with '#' and always 7 chars.
    """
    s = '#' + str("{0:#0{1}x}".format(x,6))[2:]
    if len(s)<7:
        s = s[0:5] + '0' + s[-1]
    return s