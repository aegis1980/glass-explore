#(c)2026 Jon Robinson. All Rights Reserved.

"""EN 410:2011 total solar energy transmittance (solar factor g), clause 5.4.

    g = τe + qi                                                      (eq. 7)

The panes are combined at each Table 2 wavelength (eqs. 2, 5, 14, 15) and the
results are then weighted with the solar spectrum. Weighting each pane first
and combining the averages is not equivalent for spectrally selective coatings.

The secondary heat transfer factor qi uses the boundary conditions of 5.4.6.1,
he = 25 and hi = 3.6 + 4.1·εi/0.837 W/(m²·K). For double glazing it also needs
the thermal conductance Λ between the outer and the innermost glass surface
(eq. 13, Figure 4). That is EN 673's total conductance ht at declared
conditions, so it includes the resistance of the panes.

Single glazing (eq. 12) and double glazing (eq. 13) are implemented.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np

from glass_explore import Buildup, igdb

# EN 410:2011 5.4.6.1 — conventional boundary conditions, the same as EN 673:2011
_H_E = 25.0             # external heat transfer coefficient [W/(m²·K)]
_H_I_CONV = 3.6         # internal convective part [W/(m²·K)]
_H_I_RAD = 4.1          # internal radiative part for ε = 0.837 [W/(m²·K)]
_EPS_UNCOATED = 0.837   # corrected emissivity of uncoated soda lime glass

# EN 410:2011 Table 2 — normalised solar spectrum already multiplied by the
# wavelength interval (Sλ·Δλ), so ΣSλ·Δλ = 1 and eqs. 10, 11, 14, 15 are plain
# dot products. The same table is in data/standards/prEN 410 Table 2 AM1_0.ssp.
# Wavelengths in nm; 56 points from 300–2500 nm at varying intervals.
_WAV_NM = np.array([
     300,  320,  340,  360,  380,  400,  420,  440,  460,  480,
     500,  520,  540,  560,  580,  600,  620,  640,  660,  680,
     700,  720,  740,  760,  780,  800,  850,  900,  950, 1000,
    1050, 1100, 1150, 1200, 1250, 1300, 1350, 1400, 1450, 1500,
    1550, 1600, 1650, 1700, 1750, 1800, 1850, 1900, 1950, 2000,
    2050, 2100, 2200, 2300, 2400, 2500,
], dtype=float)

_WEIGHTS = np.array([
    0.0005, 0.0069, 0.0122, 0.0145, 0.0177, 0.0235, 0.0268, 0.0294, 0.0343, 0.0339,
    0.0326, 0.0318, 0.0321, 0.0312, 0.0294, 0.0289, 0.0289, 0.0280, 0.0273, 0.0246,
    0.0237, 0.0220, 0.0230, 0.0199, 0.0211, 0.0330, 0.0453, 0.0381, 0.0220, 0.0329,
    0.0306, 0.0185, 0.0136, 0.0210, 0.0211, 0.0166, 0.0042, 0.0010, 0.0044, 0.0095,
    0.0123, 0.0110, 0.0106, 0.0093, 0.0068, 0.0024, 0.0005, 0.0002, 0.0012, 0.0030,
    0.0037, 0.0057, 0.0066, 0.0060, 0.0041, 0.0006,
])

_WAV_UM = _WAV_NM / 1000.0  # IGDB spectral data is in microns


def _solar_weighted(values: np.ndarray) -> float:
    """ΣSλ·Δλ·value(λ) for values given at the Table 2 wavelengths."""
    return float(_WEIGHTS @ values)


def _spectra(layer: Dict) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    (τ, ρ, ρ') of one pane at the Table 2 wavelengths.

    ρ is the reflectance of the face towards the incident radiation and ρ' that
    of the opposite face, so a flipped pane swaps the IGDB front and back.
    """
    props = igdb.lookup_glass_props(layer['id'])
    df = igdb.lookup_wavelength_data(props['GlazingID'])
    wav = df['Wavelength'].to_numpy()  # ascending; see igdb.lookup_wavelength_data

    def at_table2(column: str) -> np.ndarray:
        # Outside the measured range np.interp holds the end value. Every IGDB
        # product covers 300–2500 nm, but wavelengths are stored as float32, so a
        # first point of "0.3" sits marginally above 300 nm.
        return np.interp(_WAV_UM, wav, df[column].to_numpy())

    tau, rho_front, rho_back = at_table2('T'), at_table2('Rf'), at_table2('Rb')
    if layer.get('flipped', False):
        return tau, rho_back, rho_front
    return tau, rho_front, rho_back


def _h_i(inner_layer: Dict) -> float:
    """
    Internal heat transfer coefficient, 5.4.6.1: hi = 3.6 + 4.1·εi/0.837.

    εi is the corrected emissivity of the room-facing surface. 7.7 for uncoated
    glass; lower when a low-e coating faces the room, which the standard allows
    only where condensation on that surface can be excluded. en673._h_i applies
    the same rule to the U-value, and the two must stay in step.
    """
    props = inner_layer['props']
    eps = props['emis1'] if inner_layer.get('flipped') else props['emis2']
    return _H_I_CONV + _H_I_RAD * eps / _EPS_UNCOATED


@dataclass
class EN410Result:
    g: float      # total solar energy transmittance (solar factor)
    tau_e: float  # solar direct transmittance of the glazing
    A_1: float    # solar direct absorptance of the outer pane within the glazing, αe1
    A_2: float    # solar direct absorptance of the second pane, αe2 (0 for single glazing)
    q_1: float    # fraction of αe1 that is passed to the inside
    q_2: float    # fraction of αe2 that is passed to the inside
    rho_e: float  # solar direct reflectance of the glazing, outside face
    q_i: float    # secondary heat transfer factor towards the inside
    h_e: float    # external heat transfer coefficient used [W/(m²·K)]
    h_i: float    # internal heat transfer coefficient used [W/(m²·K)]
    conductance: Optional[float]  # Λ [W/(m²·K)]; None for single glazing


def solar_factor(buildup: Dict) -> EN410Result:
    """
    Compute EN 410:2011 total solar energy transmittance (solar factor g).

    Args:
        buildup: buildup dict from callbacks_energy.run_analysis_and_update_results,
            with one or two solid layers (outside → inside).

    Returns:
        EN410Result. g = tau_e + q_i and q_i = q_1·A_1 + q_2·A_2.
    """
    layers = buildup[Buildup.SOLID_LAYERS]
    if len(layers) not in (1, 2):
        raise NotImplementedError(
            f"EN 410 solar factor is implemented for single and double glazing only, not {len(layers)} panes")

    h_i = _h_i(layers[-1])
    tau1, rho1, rho1_back = _spectra(layers[0])

    if len(layers) == 1:
        # Single glazing: eq. 8 for the absorptance, eq. 12 for qi
        tau, rho = tau1, rho1
        alpha1, alpha2 = 1.0 - tau1 - rho1, np.zeros_like(tau1)
        conductance = None
        q_1, q_2 = h_i / (_H_E + h_i), 0.0
    else:
        from glass_explore import en673  # local import to avoid circular dependency

        tau2, rho2, _ = _spectra(layers[1])

        # Inter-reflection between the panes, wavelength by wavelength
        d = 1.0 - rho1_back * rho2
        tau = tau1 * tau2 / d                                                   # eq. 2
        rho = rho1 + tau1**2 * rho2 / d                                         # eq. 5
        alpha1 = (1.0 - tau1 - rho1) + (1.0 - tau1 - rho1_back) * tau1 * rho2 / d  # eq. 14 with 16, 17
        alpha2 = (1.0 - tau2 - rho2) * tau1 / d                                 # eq. 15 with 18

        # Λ: outer surface to innermost surface, by EN 673 at declared conditions
        # (Tm = 283 K, ΔT = 15 K). 1/Λ = Σ1/hs + Σd·r, i.e. EN 673's 1/ht.
        declared = en673.u_value(buildup)
        conductance = 1.0 / (sum(1.0 / gap.hs for gap in declared.gaps) + declared.r_panes)

        # eq. 13, split into the share of each pane's absorptance
        resistance = 1.0 / h_i + 1.0 / _H_E + 1.0 / conductance
        q_1 = (1.0 / _H_E) / resistance
        q_2 = (1.0 / _H_E + 1.0 / conductance) / resistance

    tau_e = _solar_weighted(tau)       # eq. 10
    rho_e = _solar_weighted(rho)       # eq. 11
    A_1 = _solar_weighted(alpha1)
    A_2 = _solar_weighted(alpha2)
    q_i = q_1 * A_1 + q_2 * A_2

    return EN410Result(g=tau_e + q_i, tau_e=tau_e, A_1=A_1, A_2=A_2, q_1=q_1, q_2=q_2,
                       rho_e=rho_e, q_i=q_i, h_e=_H_E, h_i=h_i, conductance=conductance)
