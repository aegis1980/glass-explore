# -*- coding: utf-8 -*-
"""
Modules settig out dash layout for general tab.
Defines glass geometry, buildup types and heat-treatments.

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html
"""

__author__ = "Jon Robinson"
__copyright__ = "Copyright 2020, Jon Robinson. All rights reserved"
__email__ = "jonrobinson1980@gmail.com"


import logging
from typing import List, Union
import re


class Protocol:
    IGDB_START = '#'
    IGDB_OPEN_BRACKET = '('
    IGDB_CLOSE_BRACKET = ')'
    IGDB_FLIP = "x"


    GAS_SEPARATOR = '_'
    INTERLAYER_SEPARATOR = '&'
    META = "-"

    WIDTH = 'W'
    HEIGHT = 'H'
    SUPPORT = 'SUPPORT'

    LAM = 'LAM'
    IGU = 'IGU'



def mysplit(s):
    x = s.split('.')
    if len(x) == 2:
        s = x[-1]
    print (s)
    tail = s.lstrip('0123456789')


    head = s[:-len(tail)]
    if len(x) == 2:
        head = x[0] + '.' + head

    return head, tail


def find_enclosed_brackets(s):
    stack = []
    enclosed_pairs = []

    for i, char in enumerate(s):
        if char == '(':
            stack.append(i)
        elif char == ')':
            if stack:
                enclosed_pairs.append((stack.pop(), i))
                i1 =enclosed_pairs[-1][0]
                i0 = s[:enclosed_pairs[-1][0]].rfind('#')


            else:
                logging.info("Error: Unmatched closing bracket at index %s", i)

    if stack:
        logging.info("Error: Unmatched opening brackets at indices %s", stack)

    return enclosed_pairs


def find_number_after_marker(marker: str,string :str,after_last = False) -> Union[int,float]:
    """Regular expression to match marker (e.g. 'w') followed by digits

    Args:
        marker (str): str to find
        string (str): string to search
        after_last (bool)

    Returns:
        Union[int,float]: number as float or int,
    """

    pattern = r'' +marker + r'([-+]?(?:\d*\.*\d+))'

    match = re.findall(pattern, string)
    # If a match is found, return the number after 'x'
    if match:

        x = float(match[-1 if after_last else 0])
        if x == int(x):
            return int(x)
        return x
    else:
        return None


def find_first_number(input_string):
    # Regular expression to match float or int
    pattern = r'\b\d+\.\d+|\b\d+'
    match = re.search(pattern, input_string)
    if match:
        x = float(match.group())
        if '.' in input_string:
            return x
        else:
            return int(x)
    else:
        return None

if __name__ == "__main__":
    print (find_first_number("6mono"))
