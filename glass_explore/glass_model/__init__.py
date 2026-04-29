# -*- coding: utf-8 -*-
"""
Object-based model for architectural glazing buildups.
Buildup describes in layers all implementing the _BaseLayer subclass
'gstr' is a shorthand protocol used to id buildups.

Google Python Style Guide:
http://google.github.io/styleguide/pyguide.html
"""

__author__ = "Jon Robinson"
__copyright__ = "Copyright 2024, Jon Robinson. All rights reserved"
__email__ = "jonrobinson1980@gmail.com"


from icecream import ic

# builtin modules
import abc  # abstract module
import itertools
import json
from typing import List

# local modules
from glass_explore.glass_model import errors
from glass_explore.glass_model import gstr
from glass_explore.glass_model.gstr import Protocol


class _BaseLayer(abc.ABC):
    """Base abstract class for ALL layers in a glass buildup

    As an abstract class you cannot instantiate _BaseLayer

    Attributes:
        nominal_thickness (float): in mm
        width (float) : in mm. The smaller dimension
        height (float) : in mm. The longer dimension

    """

    THICKNESS_NOT_SET : float = 0

    def __init__(self, descriptor : str, t:float = THICKNESS_NOT_SET):
        self.descriptor = descriptor
        self._t_nom = t
        self._t_actual = t


    @classmethod
    def init_from_g_str(
            cls,
            g_str: str,
    ):
        g_str = g_str.strip() #ignroe all white space

        thickness = gstr.find_first_number(g_str)
        descriptor = g_str.split(str(thickness))[-1]

        return cls(descriptor, thickness)

    def _to_json(self):
        self.__dict__.update({'__meta__':False})
        return self.__dict__


    def to_gstr(self, inc_meta = True):
        return f'{self.t_nom}{self.descriptor}'

    def __str__(self):
        return self.to_gstr()

    @property
    def t_actual(self):
        return self._t_actual


    @t_actual.setter
    def t_actual(self,t):
        self._t_actual = t

    @property
    def t_nom(self):
        return self._t_nom



class HeatTreatment:
    MONO = "MONO" #undefined
    ANNEALED = 'A'
    HEAT_STRENGTHENED = 'HS'
    TOUGHENED = 'T'
    TOUGHEND_HEATSOAKED = "TS"
    VAR = [MONO,ANNEALED, HEAT_STRENGTHENED, TOUGHENED, TOUGHEND_HEATSOAKED]


class Support:
    FOUR_SIDE :int = 4
    TWO_SIDE:int = 2



class Interlayer(_BaseLayer):
    PVB = 'PVB'
    SGP = 'SGP'
    EVA = 'EVA'

    MATERIALS = [PVB,SGP,EVA]
    THICKNESSES = [0.38, 0.76, 1.52]


class GasLayer(_BaseLayer):
    AIR = 'AIR'
    ARGON = 'AR'
    XENON = 'XE'
    KRYPTON = 'KR'

    GAS_MIXTURES = [AIR,ARGON,XENON,KRYPTON]
    THICKNESSES = [12, 13.2, 14] # corresponds to 15/32" 1/2", 9/16" spacers

    gas_mixture: str = None

    def __init__(
        self,
        gas_mixture,
        t: float,
    ):
        if gas_mixture not in GasLayer.GAS_MIXTURES:
            raise errors.BuildupException( \
                'Gas "{}" is not valid. Should be one of {}'.format(gas_mixture,GasLayer.GAS_MIXTURES))

        super(GasLayer, self).__init__(gas_mixture, t)

        self.gas_mixture = self.descriptor


# ******************************************************************************************************************


class GlassBuildup(_BaseLayer):
    """
    abstract class for all single or multi layer glass buildups
    """

    _height = None
    _width = None
    _support = None
    igdbcode: int = None
    igdbflip = False

    @staticmethod
    def make_glass(
            g_str: str
    ):
        """
        given string description of glass will return glass appropriate glass-subclass object
        """

        g_str = g_str.strip() #ignore all white space
        if Protocol.GAS_SEPARATOR in g_str:
            return InsulatedGlass.init_from_g_str(g_str)
        else:
            if Protocol.INTERLAYER_SEPARATOR in g_str or g_str.startswith(Protocol.LAM):
                return LaminatedGlass.init_from_g_str(g_str)
            else:

                return MonoGlass.init_from_g_str(g_str)


    @property
    def ar(self):
        """  geometric aspect ratio

        Returns:
            ar (float) : the aspect ratio (>=1)
        """
        return max(self._width, self._height) / min(self._width, self._height)

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self,w):
        self._width = w

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self,h):
        self._height = h

    @property
    def support(self):
        return self._support

    @support.setter
    def support(self,s):
        self._support = s


    def parse_meta(self,g_str :str) -> str:
        """Parses metadata, e.g. width, height, support conditiojn at end of g_str, after hyphen

        Args:
            g_str (str): _description_

        Returns:
            str: gstr w/o meta data & hyphen at end
        """
        if Protocol.META in g_str:
            self.width = gstr.find_number_after_marker(Protocol.WIDTH,g_str,True)
            self.height = gstr.find_number_after_marker(Protocol.HEIGHT,g_str,True)
            self.support = gstr.find_number_after_marker(Protocol.SUPPORT,g_str,True)
            return g_str.split(Protocol.META)[0]
        else:
            return g_str

    def add_meta(self,g_str) -> str:
        s = ''
        if self.width:
            s += f'{Protocol.WIDTH}{self._width}'
        if self.height:
            s += f'{Protocol.HEIGHT}{self._height}'
        if self.support:
            s += f'{Protocol.SUPPORT}{self.support}'

        if s:
            g_str += f'{Protocol.META}{s}'
            return g_str
        else:
            return g_str


    def parse_igdbcode(self,g_str :str) -> str:
        """

        Args:
            g_str (str): _description_

        Returns:
            str: _description_
        """

        if g_str.startswith(Protocol.IGDB_START) and g_str.endswith(Protocol.IGDB_CLOSE_BRACKET):
            last_br_pair = gstr.find_enclosed_brackets(g_str)[-1]
            i = g_str.find(Protocol.IGDB_OPEN_BRACKET) #first instance
            if i == last_br_pair[0]: #cehck last pair is an outer enclosing bracket
                _x = g_str[1:last_br_pair[0]]

                self.igdbflip = _x.endswith(Protocol.IGDB_FLIP)
                self.igdbcode = int(_x.split(Protocol.IGDB_FLIP)[0])
                                    
                return g_str[last_br_pair[0]+1:last_br_pair[1]]
        # default return is unchanged str
        return g_str

    def add_igdbcode(self, g_str) -> str:
        if self.igdbcode:
            _x = Protocol.IGDB_FLIP if self.igdbflip else ''
            g_str= f'{Protocol.IGDB_START}{self.igdbcode}{_x}({g_str})'
        return g_str

###############################################################################################################

class MonoGlass(GlassBuildup):
    """
    just a single bit of glass.
    """

    THICKNESSES = [4,5,6,8,10,12,15,19,25]

    @classmethod
    def init_from_g_str(
            cls,
            g_str: str,
    ):

        mono = cls(HeatTreatment.MONO,None)

        g_str = mono.parse_meta(g_str)
        g_str = mono.parse_igdbcode(g_str)
        _m= super(MonoGlass,cls).init_from_g_str(g_str)


        mono.descriptor = _m.descriptor
        mono._t_nom = _m._t_nom
        mono._t_actual = _m._t_actual


        return mono

    def __init__(
            self,
            heat_treatment,
            t_nom: float,
    ):
        if heat_treatment not in HeatTreatment.VAR:
            raise errors.BuildupException( \
                'Heat treatment {} is not valid. Should be one of {}'.format(heat_treatment,HeatTreatment.VAR))

        super(MonoGlass, self).__init__(heat_treatment, t_nom)

    def to_gstr(self, inc_meta = True):
        g = super(MonoGlass,self).to_gstr(inc_meta)

        g = self.add_igdbcode(g)

        if inc_meta:
            g =self.add_meta(g)

        return g

    def is_heattreated(self):
        return not self.descriptor == HeatTreatment.ANNEALED


# ******************************************************************************************************************


class MultiLayerGlassBuildup(GlassBuildup):

    def __init__(
            self,
            descriptor: str,
            glass_layers : List[GlassBuildup],
            separator_layers : List[ _BaseLayer]
    ):
        super(MultiLayerGlassBuildup, self).__init__(descriptor)
        self._layers : List[_BaseLayer]= [x for x in itertools.chain.from_iterable(itertools.zip_longest(glass_layers,separator_layers)) if x]

    @property
    def t_actual(self):
        self._t_actual = 0
        for l in self._layers:
            self._t_actual += l.t_actual
        return self._t_actual

    @property
    def t_nom(self):
        self._t_nom = 0
        for l in self._layers:
            if not isinstance(l,Interlayer):
                self._t_nom += l.t_nom
        return self._t_nom

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self,w):
        self._width = w
        for l in self._layers:
            if isinstance(l,GlassBuildup):
                l.width = w

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self,h):
        self._height = h
        for l in self._layers:
            if isinstance(l,GlassBuildup):
                l.height = h

    @property
    def support(self):
        return self._support

    @support.setter
    def support(self,s):
        self._support = s
        for l in self._layers:
            if isinstance(l,GlassBuildup):
                l.support = s


# ******************************************************************************************************************


class LaminatedGlass(MultiLayerGlassBuildup):

    def __init__(
        self,
        plies: List[MonoGlass],
        interlayers: List[Interlayer],
    ):

        if plies and len(interlayers) != len(plies) - 1:
            raise errors.BuildupException("Number of interlayers needs to be one less than number of plies")

        super(LaminatedGlass, self).__init__('lam',plies,interlayers)

    @classmethod
    def init_from_g_str(
            cls,
            g_str: str,
    ):
        lam = cls([],[]) #just a dummy
        g_str = lam.parse_meta(g_str)
        g_str = lam.parse_igdbcode(g_str)

        for i, g in enumerate(g_str.split(Protocol.INTERLAYER_SEPARATOR)):
            if (i % 2) == 0:  # monoglass layer are even, or zero
                m = MonoGlass.init_from_g_str(g)
                lam._layers.append(m)
            else:  # interlayer
                il = Interlayer.init_from_g_str(g)
                lam._layers.append(il)

        return lam



    def to_gstr(self, inc_meta = True):
        _g = []
        for l in self._layers:
            _g.append(l.to_gstr(inc_meta=False))
        g =  Protocol.INTERLAYER_SEPARATOR.join(_g)

        g = self.add_igdbcode(g)

        if inc_meta:
            g =self.add_meta(g)

        return g


    @property
    def plies(self) -> List[MonoGlass]:
        """Return list of laminated glass buildup glass plies, out to in

        Returns:
            List[MonoGlass]: list of plies
        """

        return self._layers[0::2]


    @property
    def interlayers(self) -> List[Interlayer]:
        """Return list of laminated glass buildup interlayer, out to in

        Returns:
            List[Interlayer]: list of interlayers
        """
        return self._layers[1::2]



####################################################################################################################


class InsulatedGlass(MultiLayerGlassBuildup):



    def __init__(
            self,
            lites: List[GlassBuildup],
            gases: List[GasLayer]
    ):

        if lites and len(gases) != len(lites) - 1:
            raise errors.BuildupException("Number of gas gaps needs to be one less than number of lites")

        super(InsulatedGlass, self).__init__('igu', lites,gases)

    def to_gstr(self, inc_meta = True):
        _g = []
        for i,l in enumerate(self.lites):

            _g.append(l.to_gstr(inc_meta=False))
            if i<len(self.gases): _g.append(self.gases[i].to_gstr(inc_meta=False))
        g = Protocol.GAS_SEPARATOR.join(_g)

        g = self.add_igdbcode(g)

        if inc_meta:
            g =self.add_meta(g)

        return g

    @classmethod
    def init_from_g_str(
            cls,
            g_str: str,
    ):

        igu = cls([],[]) #just a dummy

        g_str = igu.parse_meta(g_str)
        #g_str = igu.parse_igdbcode(g_str)


        for i, g in enumerate(g_str.split(Protocol.GAS_SEPARATOR)):
            if (i % 2) == 0:  # glass lite (mono or lam) are even or zero
                # todo
                lite = GlassBuildup.make_glass(g)
                igu._layers.append(lite)
            else:  # gas
                gas = GasLayer.init_from_g_str(g)
                igu._layers.append(gas)

        return igu

    @property
    def lites(self) -> List[GlassBuildup]:
        """Return list of IGU buildup lites, out to in

        Returns:
            List[GlassBuildup]: list of lites
        """

        return self._layers[0::2]

    @property
    def gases(self) -> List[GasLayer]:
        """Return list of IGU buildup gass layers, out to in

        Returns:
            List[GasLayer]: list of gas layers
        """
        return self._layers[1::2]

class GlassJsonEncoder(json.JSONEncoder):
    def default(self, z):
        if isinstance(z, _BaseLayer):
            return z._to_json()
        else:
            return super().default(z)
