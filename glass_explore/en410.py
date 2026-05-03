#(c)2026 Jon Robinson. All Rights Reserved.

"""EN 410:2011 Total solar energy transmittance (solar factor g).

Computes g = τ_e + q_1·A_1 + q_2·A_2 for a double-glazed unit using spectral
data from the IGDB and the EN 410 solar spectrum.

Basic mode: secondary heat transfer factors are derived from the EN 673 U-value
(via pywincalc) using the EN 410 boundary conditions h_e=23, h_i=8 W/(m²·K).
The back-calculated h_g absorbs pane resistance into the gap conductance.

detailed_analysis=True: uses en673.u_value(detailed_analysis=True) to get the
converged gap conductance hs directly (no pane-resistance approximation).
The EN 410 boundary conditions h_e=23, h_i=8 are still used for q_1, q_2.
"""

from dataclasses import dataclass
from typing import Dict

import numpy as np

from glass_explore import Buildup, igdb

# EN 410:2011 Section 6.2 boundary conditions
_H_E = 23.0  # W/(m²·K) external surface heat transfer coefficient
_H_I = 8.0   # W/(m²·K) internal surface heat transfer coefficient

# prEN 410 Table 2 — pre-weighted normalised solar spectrum (D(λ)·Δλ / ΣD·Δλ)
# Source: data/standards/prEN 410 Table 2 AM1_0.ssp  — weights sum to 1.0
# Wavelengths in nm; 56 bands from 300–2500 nm at varying intervals.
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


def _solar_weighted(wav_um: np.ndarray, values: np.ndarray) -> float:
    """Dot-product of EN 410 weights with values interpolated to the standard wavelengths."""
    interp = np.interp(_WAV_UM, wav_um, values, left=0.0, right=0.0)
    return float(_WEIGHTS @ interp)


def _pane_solar_props(layer: Dict):
    """
    Solar-weighted (τ_e, ρ_ef, ρ_eb) for a single pane.
    Front = side facing incident solar (accounts for the 'flipped' flag).
    """
    props = igdb.lookup_glass_props(layer['id'])
    df = igdb.lookup_wavelength_data(props['GlazingID'])
    flipped = layer.get('flipped', False)

    wav = df['Wavelength'].to_numpy()
    T  = df['T'].to_numpy()
    Rf = df['Rb'].to_numpy() if flipped else df['Rf'].to_numpy()
    Rb = df['Rf'].to_numpy() if flipped else df['Rb'].to_numpy()

    return _solar_weighted(wav, T), _solar_weighted(wav, Rf), _solar_weighted(wav, Rb)


def _gap_conductance_from_u(u: float) -> float:
    """
    Back-calculate gap conductance from pywincalc U-value.
    Approximation: pane resistance is folded into h_g; error ~1.6% for standard IGUs.
        U = 1 / (1/h_e + 1/h_g + 1/h_i)  →  h_g = 1 / (1/U − 1/h_e − 1/h_i)
    """
    return 1.0 / (1.0 / u - 1.0 / _H_E - 1.0 / _H_I)


@dataclass
class EN410Result:
    g: float      # total solar energy transmittance (solar factor)
    tau_e: float  # solar direct transmittance of the system
    A_1: float    # system solar absorptance, outer pane
    A_2: float    # system solar absorptance, inner pane
    q_1: float    # secondary heat transfer factor, outer pane
    q_2: float    # secondary heat transfer factor, inner pane


def solar_factor(buildup: Dict, u_EN673: float,
                 detailed_analysis: bool = False) -> EN410Result:
    """
    Compute EN 410:2011 total solar energy transmittance (solar factor g).

    Args:
        buildup: buildup dict from callbacks_energy.run_analysis_and_update_results
        u_EN673: U-value from pywincalc (EN 673 environment) — used in basic mode
            to back-calculate gap conductance for secondary heat transfer factors.
        detailed_analysis: if True, uses en673.u_value(detailed_analysis=True) to
            obtain the converged gap hs directly, avoiding the pane-resistance
            approximation implicit in back-calculating h_g from U.

    Returns:
        EN410Result with g, tau_e, A_1, A_2, q_1, q_2
    """
    from glass_explore import en673  # local import to avoid circular dependency

    layers = buildup[Buildup.SOLID_LAYERS]
    tau1, rho1f, rho1b = _pane_solar_props(layers[0])  # outer pane
    tau2, rho2f, _     = _pane_solar_props(layers[1])  # inner pane (rho2b unused)

    # System optical properties accounting for inter-pane reflections (EN 410 eq. 5–8)
    d = 1.0 - rho1b * rho2f
    tau_e = tau1 * tau2 / d
    A_1 = (1.0 - tau1 - rho1f) + tau1 * rho2f * (1.0 - tau1 - rho1b) / d
    A_2 = tau1 * (1.0 - tau2 - rho2f) / d

    # Gap conductance for secondary heat transfer factors (EN 410 Section 6.3)
    if detailed_analysis:
        # Use converged hs from EN 673 iteration; no pane-resistance approximation
        en673_result = en673.u_value(buildup, detailed_analysis=True)
        h_g = en673_result.gaps[0].hs
    else:
        h_g = _gap_conductance_from_u(u_EN673)

    denom = _H_E * h_g + _H_E * _H_I + h_g * _H_I
    q_1 = _H_I * h_g / denom          # outer pane → must conduct through gap first
    q_2 = _H_I * (_H_E + h_g) / denom # inner pane → directly faces interior

    g = tau_e + q_1 * A_1 + q_2 * A_2
    return EN410Result(g=g, tau_e=tau_e, A_1=A_1, A_2=A_2, q_1=q_1, q_2=q_2)
