#(c)2026 Jon Robinson. All Rights Reserved.

"""EN 673:2011 Thermal transmittance (U-value) — pure-Python implementation.

Implements the declared-value calculation for vertical glazing:
  U = 1 / (1/h_e + R_panes + Σ(1/hs_k) + 1/h_i)

Gap conductance hs = hr + hg is iterated per Annex A until Σ(1/hs) converges.

Gas mixtures (e.g. "air(5%), ar(95%)") are supported via EN 673 Annex B mixing
rules: mole-fraction-weighted density, mass-fraction-weighted specific heat, and
Wilke's rule for viscosity and conductivity.

detailed_analysis=True adds an outer loop that iterates on actual gap mean
temperature Tm (derived from the converged temperature profile) rather than the
fixed declared value of 283 K. Gas properties are also interpolated to actual Tm
using the full EN 673 Table 1 data. Boundary temperatures are still the declared
values: T_e = 0°C, T_i = 20°C.

Reference: BS EN 673:2011 Glass in building — Determination of thermal
transmittance (U value) — Calculation method.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from glass_explore import Buildup

# EN 673:2011 declared-value constants
_SIGMA = 5.67e-8      # Stefan-Boltzmann [W/(m²·K⁴)]
_T_M = 283.0          # declared mean gas temperature [K] (10°C)
_T_I = 293.15         # declared inside air temperature [K] (20°C)
_T_E = 273.15         # declared outside air temperature [K] (0°C)
_DELTA_T = 15.0       # temperature difference across glazing [K]
_H_E = 25.0           # external surface coefficient [W/(m²·K)]
_H_I_CONV = 3.6       # internal convection component [W/(m²·K)]
_H_I_RAD_REF = 4.1    # internal radiation component for ε = 0.837 [W/(m²·K)]
_EPS_UNCOATED = 0.837 # corrected emissivity, uncoated soda lime glass

# Nusselt constants — vertical glazing (standard orientation)
_A_VERT, _N_VERT = 0.035, 0.38

# EN 673 Table 1 — gas properties at four temperatures
# Tuple layout per gas: (temps_°C, density kg/m³, viscosity Pa·s, conductivity W/(m·K), specific_heat J/(kg·K))
# Specific heat is approximately constant over this range.
_GAS_TABLE: Dict[str, Tuple] = {
    'air':     ([-10, 0, 10, 20],
                [1.326, 1.277, 1.232, 1.189],
                [1.661e-5, 1.711e-5, 1.761e-5, 1.811e-5],
                [2.336e-2, 2.416e-2, 2.496e-2, 2.576e-2],
                1008.0),
    'argon':   ([-10, 0, 10, 20],
                [1.829, 1.762, 1.699, 1.640],
                [2.038e-5, 2.101e-5, 2.164e-5, 2.228e-5],
                [1.584e-2, 1.634e-2, 1.684e-2, 1.734e-2],
                519.0),
    'krypton': ([-10, 0, 10, 20],
                [3.832, 3.690, 3.560, 3.430],
                [2.260e-5, 2.330e-5, 2.400e-5, 2.470e-5],
                [0.842e-2, 0.870e-2, 0.900e-2, 0.926e-2],
                245.0),
    'xenon':   ([-10, 0, 10, 20],
                [6.121, 5.897, 5.689, 5.495],
                [2.078e-5, 2.152e-5, 2.226e-5, 2.299e-5],
                [0.494e-2, 0.512e-2, 0.529e-2, 0.546e-2],
                161.0),
}


# Molar masses [g/mol] — needed for mixture property calculations (Annex B)
_MOLAR_MASS: Dict[str, float] = {
    'air': 28.97, 'argon': 39.95, 'krypton': 83.80, 'xenon': 131.29,
}

# Short-form aliases used in IGDB mixture strings
_GAS_ALIASES: Dict[str, str] = {
    'air': 'air', 'ar': 'argon', 'argon': 'argon',
    'kr': 'krypton', 'krypton': 'krypton',
    'xe': 'xenon', 'xenon': 'xenon',
}


def _interp1(x: float, xs: list, ys: list) -> float:
    """Linear interpolation with clamped extrapolation."""
    if x <= xs[0]:  return ys[0]
    if x >= xs[-1]: return ys[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] * (1.0 - t) + ys[i + 1] * t


def _pure_gas_props(gas: str, Tm_K: float) -> Tuple:
    """Gas properties at Tm_K for a pure gas, interpolated from EN 673 Table 1."""
    temps, rho_t, mu_t, lam_t, c = _GAS_TABLE[gas]
    T_C = Tm_K - 273.15
    return _interp1(T_C, temps, rho_t), _interp1(T_C, temps, mu_t), _interp1(T_C, temps, lam_t), c


def _parse_gas(gas_str: str) -> List[Tuple[str, float]]:
    """Parse a gas string into [(canonical_name, mole_fraction), ...].

    Accepts pure gas names ("air", "argon", "ar", …) and IGDB-style mixture
    strings ("air(5%), ar(95%)").  Fractions are normalised so they sum to 1.
    """
    s = gas_str.strip().lower()
    canonical = _GAS_ALIASES.get(s)
    if canonical:
        return [(canonical, 1.0)]
    parts = re.findall(r'(\w+)\s*\(\s*([\d.]+)\s*%\s*\)', s)
    if not parts:
        raise ValueError(f"Cannot parse gas string: {gas_str!r}")
    components = [(_GAS_ALIASES[name], float(pct) / 100.0) for name, pct in parts]
    total = sum(f for _, f in components)
    return [(g, f / total) for g, f in components]


def _gas_props(gas_str: str, Tm_K: float) -> Tuple:
    """Gas properties at Tm_K — handles pure gases and mixtures.

    Pure gas: looks up EN 673 Table 1 directly.
    Mixture: applies EN 673 Annex B rules —
      ρ  = Σ x_i·ρ_i                                   (ideal, mole-fraction)
      c_p = Σ(x_i·M_i·c_p,i) / Σ(x_i·M_i)             (mass-fraction weighted)
      μ, λ: Wilke's rule with φ_ij = [1+(μ_i/μ_j)^½·(M_j/M_i)^¼]² / √(8(1+M_i/M_j))
    """
    components = _parse_gas(gas_str)
    if len(components) == 1:
        return _pure_gas_props(components[0][0], Tm_K)

    xs   = [f  for _, f in components]
    Ms   = [_MOLAR_MASS[g] for g, _ in components]
    pp   = [_pure_gas_props(g, Tm_K) for g, _ in components]
    rhos = [p[0] for p in pp]
    mus  = [p[1] for p in pp]
    lams = [p[2] for p in pp]
    cps  = [p[3] for p in pp]

    rho_mix = sum(x * r for x, r in zip(xs, rhos))

    xM = [x * M for x, M in zip(xs, Ms)]
    cp_mix = sum(xMi * cp for xMi, cp in zip(xM, cps)) / sum(xM)

    n = len(components)
    phi = [
        [
            (1.0 + (mus[i] / mus[j])**0.5 * (Ms[j] / Ms[i])**0.25)**2
            / (8.0 * (1.0 + Ms[i] / Ms[j]))**0.5
            for j in range(n)
        ]
        for i in range(n)
    ]
    mu_mix  = sum(xs[i] * mus[i]  / sum(xs[j] * phi[i][j] for j in range(n)) for i in range(n))
    lam_mix = sum(xs[i] * lams[i] / sum(xs[j] * phi[i][j] for j in range(n)) for i in range(n))

    return rho_mix, mu_mix, lam_mix, cp_mix


def _h_r(eps1: float, eps2: float, Tm: float = _T_M) -> float:
    """Radiation conductance of a gas space [W/(m²·K)] — EN 673 eq. 4."""
    return 4.0 * _SIGMA * Tm**3 / (1.0/eps1 + 1.0/eps2 - 1.0)


def _h_g(gas: str, s: float, delta_t: float, Tm: float = _T_M) -> float:
    """Gas (convection/conduction) conductance [W/(m²·K)] — EN 673 eq. 5–8.

    Gr = 9.81·s³·ΔT·ρ² / (Tm·μ²)   [eq. 7, β = 1/Tm for ideal gas]
    Pr = μ·c / λ                      [eq. 8]
    Nu = max(1, A·(Gr·Pr)^n)          [eq. 6]
    hg = λ·Nu / s                     [eq. 5]
    """
    rho, mu, lam, c = _gas_props(gas, Tm)
    Gr = 9.81 * s**3 * delta_t * rho**2 / (Tm * mu**2)
    Pr = mu * c / lam
    Nu = max(1.0, _A_VERT * (Gr * Pr)**_N_VERT)
    return lam * Nu / s


def _gap_emissivities(solid: List[Dict], k: int) -> Tuple[float, float]:
    """
    (ε₁, ε₂) — corrected emissivities of the surfaces bounding gap k.

    ε₁ = back face of outer pane (or front if flipped).
    ε₂ = front face of inner pane (or back if flipped).
    """
    outer, inner = solid[k], solid[k + 1]
    p_o, p_i = outer['props'], inner['props']
    eps1 = p_o['emis1'] if outer.get('flipped') else p_o['emis2']
    eps2 = p_i['emis2'] if inner.get('flipped') else p_i['emis1']
    return eps1, eps2


def _h_i(inner_layer: Dict) -> float:
    """Internal surface coefficient [W/(m²·K)] — EN 673 eq. 10/12.

    hi = h_i_conv + 4.1 · ε_inner / 0.837
    Fixed at 7.7 for uncoated glass; lower for a low-ε room-facing surface.
    """
    p = inner_layer['props']
    eps = p['emis1'] if inner_layer.get('flipped') else p['emis2']
    return _H_I_CONV + _H_I_RAD_REF * eps / _EPS_UNCOATED


def _compute_gap_tm(r_panes_list: List[float], gap_hs: List[float],
                    u: float) -> List[float]:
    """Mean temperature of each gas gap from the converged thermal model.

    Traverses the resistance network outside → inside using EN 673 declared
    boundary temperatures (T_e=273.15K, T_i=293.15K) to find the temperature
    on each side of every gap, then returns the average.
    """
    q = u * (_T_I - _T_E)        # steady-state heat flux [W/m²]
    T = _T_E + q / _H_E          # outer face of solid[0]
    Tm_list = []
    for k, r_pane in enumerate(r_panes_list):
        T += q * r_pane           # traverse pane k (outside → inside)
        if k < len(gap_hs):
            T1 = T
            T += q / gap_hs[k]   # traverse gap k
            Tm_list.append((T1 + T) / 2.0)
    return Tm_list


@dataclass
class GapResult:
    hs: float              # total gap conductance [W/(m²·K)]
    hr: float              # radiation component
    hg: float              # gas (convection + conduction) component
    delta_t: float         # converged ΔT across this gap [K]
    actual_tm: Optional[float] = None  # converged gap mean temp [K]; None in basic mode


@dataclass
class EN673Result:
    u: float               # thermal transmittance [W/(m²·K)]
    h_i: float             # internal surface coefficient used
    r_panes: float         # combined pane thermal resistance [m²·K/W]
    gaps: List[GapResult] = field(default_factory=list)


def u_value(buildup: Dict, detailed_analysis: bool = False) -> EN673Result:
    """
    Compute EN 673:2011 thermal transmittance U [W/(m²·K)].

    Args:
        buildup: buildup dict from callbacks_energy.run_analysis_and_update_results
        detailed_analysis: if True, adds an outer iteration loop that derives
            the actual mean temperature of each gap from the temperature profile
            (T_e=0°C, T_i=20°C declared) and recomputes hr, hg, hs at that Tm
            until Tm converges (< 0.01 K). Gas properties are also interpolated
            to actual Tm from EN 673 Table 1 rather than fixed at 283 K.

    Returns:
        EN673Result with u, h_i, r_panes, and per-gap breakdown.
        In detailed mode, GapResult.actual_tm holds the converged gap temperature.
    """
    solid = buildup[Buildup.SOLID_LAYERS]
    gas   = buildup[Buildup.GAS_LAYERS]
    N = len(gas)

    r_panes_list = [float(l['thickness']) / 1000.0 / l['props']['Conductivity'] for l in solid]
    r_panes      = sum(r_panes_list)
    emissivities = [_gap_emissivities(solid, k) for k in range(N)]
    gap_s        = [float(g['thickness']) / 1000.0 for g in gas]
    gap_gas      = [g['gas'] for g in gas]
    hi           = _h_i(solid[-1])

    Tm_k = [_T_M] * N  # gap mean temperatures; fixed at 283K in basic mode

    for _outer in range(20 if detailed_analysis else 1):

        # Annex A inner iteration: distribute ΔT across gaps proportional to 1/hs
        delta_ts = [_DELTA_T / N] * N
        r_prev = None
        for _ in range(10):
            hs     = [_h_r(*emissivities[k], Tm_k[k]) + _h_g(gap_gas[k], gap_s[k], delta_ts[k], Tm_k[k]) for k in range(N)]
            r_gaps = [1.0 / h for h in hs]
            r_sum  = sum(r_gaps)
            delta_ts = [_DELTA_T * r / r_sum for r in r_gaps]
            if r_prev is not None and abs(r_sum - r_prev) < 5e-4 * r_sum:
                break
            r_prev = r_sum

        # Final hs with converged delta_ts
        hs     = [_h_r(*emissivities[k], Tm_k[k]) + _h_g(gap_gas[k], gap_s[k], delta_ts[k], Tm_k[k]) for k in range(N)]
        r_gaps = [1.0 / h for h in hs]

        if not detailed_analysis:
            break

        # Outer iteration: update Tm from actual temperature profile
        u_iter   = 1.0 / (1.0/_H_E + r_panes + sum(r_gaps) + 1.0/hi)
        new_Tm_k = _compute_gap_tm(r_panes_list, hs, u_iter)

        if max(abs(new_Tm_k[k] - Tm_k[k]) for k in range(N)) < 0.01:
            break  # hs are already consistent with converged Tm_k

        Tm_k = new_Tm_k

    u = 1.0 / (1.0/_H_E + r_panes + sum(r_gaps) + 1.0/hi)

    gaps_out = [
        GapResult(
            hs=hs[k],
            hr=_h_r(*emissivities[k], Tm_k[k]),
            hg=_h_g(gap_gas[k], gap_s[k], delta_ts[k], Tm_k[k]),
            delta_t=delta_ts[k],
            actual_tm=Tm_k[k] if detailed_analysis else None,
        )
        for k in range(N)
    ]

    return EN673Result(u=u, h_i=hi, r_panes=r_panes, gaps=gaps_out)
