#(c)2026 Jon Robinson. All Rights Reserved.

"""Tests for glass_explore.en410 against EN 410:2011 clause 5.4.

Run from the repo root:

    poetry run python -m unittest discover -s tests -t . -v

The tests read data/igdb.sqlite and are skipped when the data files are missing.
SpectralData has no index, so each new product costs one table scan.
Set EN410_SWEEP=1 to also check every coated product in the glass table.

External reference: INISMa test report 2018B COU 35741 (validation of AGC's
calculation tools to EN 410:2011 and EN 673:2011), in references/.
"""

import json
import math
import os
import sqlite3
import unittest
from unittest import mock

import numpy as np

try:
    from glass_explore import (DF_GLASS_TABLE, IGDB_SQLITE_PATH, PATH_STANDARDS,
                               Buildup, en410, en673, igdb, utils)
except FileNotFoundError as exc:  # data/igdb.sqlite is not in git
    raise unittest.SkipTest(f"IGDB data files are not available: {exc}")

# IGDB (NFRC) IDs
CLEAR_6 = 103             # generic clear, the app's default uncoated lite
CLEARLITE_4 = 4492        # AGC Planibel Clearlite 3.85 mm
CLEARLITE_6 = 4493        # AGC Planibel Clearlite 5.85 mm
TOP_N_ON_CLEARLITE_4 = 4451   # AGC soft-coat low-e, coating on the front face
VISION_51T_6 = 20711      # AGC Stopray Vision-51T 5.86 mm, coating on the back face
PYROLYTIC_LOW_E = 9923    # Pilkington Energy Advantage, coating on the front face

MIX_90_AR = "air(10%), ar(90%)"


def _buildup(*lites, gas="argon", gap=16.0):
    """Buildup dict as callbacks_energy.glass_to_store makes it.

    lites: (nfrc_id, flipped) pairs, outside → inside.
    """
    buildup = {
        Buildup.SOLID_LAYERS: [{} for _ in lites],
        Buildup.GAS_LAYERS: [{"gas": gas, "thickness": gap} for _ in lites[1:]],
    }
    for i, (nfrc_id, flipped) in enumerate(lites):
        utils.populate_buildup_with_glass_props(buildup, igdb.lookup_glass_props(nfrc_id), i)
        buildup[Buildup.SOLID_LAYERS][i]["flipped"] = flipped
    return json.loads(json.dumps(buildup))  # the app passes it through a dcc.Store


def _synthetic_buildup(panes=2, eps_room=0.837):
    """Buildup that needs no database; pair it with a patched en410._spectra."""
    layers = [{"id": i, "thickness": 6.0, "flipped": False,
               "props": {"Conductivity": 1.0, "emis1": 0.837, "emis2": 0.837}} for i in range(panes)]
    layers[-1]["props"]["emis2"] = eps_room
    return {Buildup.SOLID_LAYERS: layers,
            Buildup.GAS_LAYERS: [{"gas": "argon", "thickness": 16.0} for _ in layers[1:]]}


def _two_band_spectra(layer):
    """Pane 0 transmits only below 780 nm, pane 1 only above; both reflect 0.1."""
    visible = en410._WAV_NM < 780
    tau = np.where(visible, 0.8, 0.0) if layer["id"] == 0 else np.where(visible, 0.0, 0.8)
    rho = np.full_like(tau, 0.1)
    return tau, rho, rho


class Table2Test(unittest.TestCase):

    def test_weights_are_normalised(self):
        self.assertEqual(len(en410._WEIGHTS), 56)
        self.assertEqual(len(en410._WAV_NM), 56)
        self.assertAlmostEqual(float(en410._WEIGHTS.sum()), 1.0, places=9)

    def test_matches_the_window_standard_file(self):
        path = os.path.join(PATH_STANDARDS, "prEN 410 Table 2 AM1_0.ssp")
        with open(path) as f:
            rows = [line.split() for line in f if line[:1].isdigit()]
        self.assertEqual([float(r[0]) for r in rows], list(en410._WAV_NM))
        np.testing.assert_allclose([float(r[1]) for r in rows], en410._WEIGHTS, rtol=0, atol=1e-12)


class SpectralDataOrderTest(unittest.TestCase):
    """Rows of some products are stored out of wavelength order; np.interp needs them ascending."""

    # (NFRC ID, single-pane tau_e) for products whose rows are stored out of order
    UNSORTED = ((6410, 0.2183), (3267, 0.3910), (8238, 0.8527))

    def test_lookup_returns_ascending_wavelengths(self):
        for nfrc_id, _ in self.UNSORTED:
            with self.subTest(nfrc_id=nfrc_id):
                glazing_id = igdb.lookup_glass_props(nfrc_id)["GlazingID"]
                wavelengths = igdb.lookup_wavelength_data(glazing_id)["Wavelength"].to_numpy()
                self.assertTrue(np.all(np.diff(wavelengths) > 0))

    def test_solar_transmittance_of_unsorted_products(self):
        for nfrc_id, tau_e in self.UNSORTED:
            with self.subTest(nfrc_id=nfrc_id):
                self.assertAlmostEqual(en410.solar_factor(_buildup((nfrc_id, False))).tau_e, tau_e, delta=0.001)


class SingleGlazingTest(unittest.TestCase):

    def test_inisma_task_1_clear_float(self):
        """6 mm Clearlite: the report gives tau_e 84.6, rho_e 7.5, g 86.4 (%).

        Like for like. g only comes out at 86.4 with the 2011 coefficients
        (he = 25, hi = 7.7); the pre-2011 pair (23, 8) gives 86.6.
        """
        r = en410.solar_factor(_buildup((CLEARLITE_6, False)))
        self.assertAlmostEqual(r.tau_e, 0.846, delta=0.001)
        self.assertAlmostEqual(r.rho_e, 0.075, delta=0.001)
        self.assertAlmostEqual(r.g, 0.864, delta=0.001)
        self.assertIsNone(r.conductance)

    def test_equation_12(self):
        with mock.patch.object(en410, "_spectra", _two_band_spectra):
            r = en410.solar_factor(_synthetic_buildup(panes=1))
        s = float(en410._WEIGHTS[en410._WAV_NM < 780].sum())
        self.assertAlmostEqual(r.tau_e, 0.8 * s, places=12)
        self.assertAlmostEqual(r.rho_e, 0.1, places=12)
        alpha_e = 1 - 0.8 * s - 0.1
        self.assertAlmostEqual(r.g, 0.8 * s + alpha_e * 7.7 / (25 + 7.7), places=12)


class DoubleGlazingFormulaTest(unittest.TestCase):
    """Clause 5.4 on synthetic spectra, so the expected values can be worked out by hand."""

    def setUp(self):
        patcher = mock.patch.object(en410, "_spectra", _two_band_spectra)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.s = float(en410._WEIGHTS[en410._WAV_NM < 780].sum())  # solar fraction below 780 nm

    def test_panes_are_combined_per_wavelength(self):
        """Eqs 2, 5, 14, 15. The panes never transmit at the same wavelength, so tau_e is 0;
        combining solar averages instead would give about 0.16."""
        r = en410.solar_factor(_synthetic_buildup())
        s, d = self.s, 1 - 0.1 * 0.1
        self.assertAlmostEqual(r.tau_e, 0.0, places=12)
        self.assertAlmostEqual(r.rho_e, s * (0.1 + 0.8**2 * 0.1 / d) + (1 - s) * 0.1, places=12)
        self.assertAlmostEqual(r.A_1, s * (0.1 + 0.1 * 0.8 * 0.1 / d) + (1 - s) * 0.9, places=12)
        self.assertAlmostEqual(r.A_2, s * 0.9 * 0.8 / d, places=12)
        self.assertAlmostEqual(r.tau_e + r.rho_e + r.A_1 + r.A_2, 1.0, places=12)  # eq. 8

    def test_boundary_conditions_and_equation_13(self):
        r = en410.solar_factor(_synthetic_buildup())
        self.assertEqual(r.h_e, 25.0)
        self.assertAlmostEqual(r.h_i, 7.7, places=9)
        lam = r.conductance
        q_i = ((r.A_1 + r.A_2) / 25.0 + r.A_2 / lam) / (1 / 7.7 + 1 / 25.0 + 1 / lam)
        self.assertAlmostEqual(r.q_i, q_i, places=12)
        self.assertAlmostEqual(r.g, r.tau_e + q_i, places=12)

    def test_conductance_is_en673_total_conductance(self):
        """Λ runs from outer surface to innermost surface, so with he and hi it gives the EN 673 U."""
        buildup = _synthetic_buildup()
        r = en410.solar_factor(buildup)
        declared = en673.u_value(buildup)
        self.assertAlmostEqual(1 / (1 / r.h_e + 1 / r.conductance + 1 / r.h_i), declared.u, places=12)
        self.assertLess(r.conductance, declared.gaps[0].hs)  # the panes add resistance

    def test_low_e_surface_facing_the_room_lowers_h_i(self):
        buildup = _synthetic_buildup(eps_room=0.1)
        r = en410.solar_factor(buildup)
        self.assertAlmostEqual(r.h_i, 3.6 + 4.1 * 0.1 / 0.837, places=12)
        self.assertAlmostEqual(r.h_i, en673.u_value(buildup).h_i, places=12)  # same hi as the U-value
        self.assertLess(r.g, en410.solar_factor(_synthetic_buildup()).g)

    def test_triple_glazing_is_rejected(self):
        with self.assertRaises(NotImplementedError):
            en410.solar_factor(_synthetic_buildup(panes=3))


class DoubleGlazingProductTest(unittest.TestCase):

    # name: (buildup, g, tau_e). Reference values from a separate transcription of
    # eqs 2, 13, 14, 15, which also reproduces the single-glazing report values above.
    REFERENCE = {
        "solar control on #2": (lambda: _buildup((VISION_51T_6, False), (CLEARLITE_6, False), gas=MIX_90_AR), 0.2870, 0.2606),
        "solar control on #3": (lambda: _buildup((CLEARLITE_6, False), (VISION_51T_6, True), gas=MIX_90_AR), 0.4544, 0.2606),
        "app default": (lambda: _buildup((PYROLYTIC_LOW_E, False), (CLEAR_6, False), gas="air", gap=12.0), 0.6339, 0.5528),
        "pyrolytic low-e on #2": (lambda: _buildup((PYROLYTIC_LOW_E, True), (CLEAR_6, False)), 0.6403, 0.5530),
        "pyrolytic low-e on #4": (lambda: _buildup((CLEAR_6, False), (PYROLYTIC_LOW_E, True)), 0.6438, None),
        "soft-coat low-e on #3": (lambda: _buildup((CLEARLITE_4, False), (TOP_N_ON_CLEARLITE_4, False), gas=MIX_90_AR), 0.6428, 0.5813),
        "uncoated": (lambda: _buildup((CLEAR_6, False), (CLEAR_6, False), gas="air"), 0.7049, 0.6203),
    }

    def test_reference_values(self):
        for name, (make, g, tau_e) in self.REFERENCE.items():
            with self.subTest(name):
                r = en410.solar_factor(make())
                self.assertAlmostEqual(r.g, g, delta=2e-4)
                if tau_e is not None:
                    self.assertAlmostEqual(r.tau_e, tau_e, delta=2e-4)
                self.assertAlmostEqual(r.tau_e + r.rho_e + r.A_1 + r.A_2, 1.0, places=9)  # eq. 8

    def test_inisma_task_5_secondary_heat_gain(self):
        """Solar control on #2 / 16 mm 90% Ar / clear: the report gives g - tau_e = 2.5 to 2.6 (%).

        Indicative only: the report used Stopray Vision-51, the IGDB has Vision-51T,
        so tau_e and g themselves are not comparable.
        """
        r = en410.solar_factor(self.REFERENCE["solar control on #2"][0]())
        self.assertAlmostEqual(r.q_i, 0.0255, delta=0.003)

    def test_room_side_coating_uses_the_same_h_i_as_the_u_value(self):
        buildup = self.REFERENCE["pyrolytic low-e on #4"][0]()
        r = en410.solar_factor(buildup)
        self.assertLess(r.h_i, 5.0)
        self.assertAlmostEqual(r.h_i, en673.u_value(buildup).h_i, places=12)


@unittest.skipUnless(os.getenv("EN410_SWEEP"), "set EN410_SWEEP=1 to check every coated product")
class AllCoatedProductsSweep(unittest.TestCase):
    """Every coated 3.5-10.5 mm product, coating on surface 2 and on surface 3,
    with 16 mm argon and generic clear 6 mm as the other lite."""

    def test_invariants(self):
        import pandas as pd

        with sqlite3.connect(IGDB_SQLITE_PATH) as cxn:
            rows = pd.read_sql("select GlazingID, Wavelength, T, Rf, Rb from SpectralData "
                               "order by GlazingID, Wavelength", cxn)
        spectra = {int(glazing_id): df for glazing_id, df in rows.groupby("GlazingID", sort=False)}
        coated = DF_GLASS_TABLE[DF_GLASS_TABLE["Coated_Side"].isin(["Front", "Back"])
                                & DF_GLASS_TABLE["Thickness"].between(3.5, 10.5)]
        tol = 1e-3
        problems = []
        with mock.patch.object(igdb, "lookup_wavelength_data", lambda glazing_id: spectra[int(glazing_id)]):
            for nfrc_id, coated_side in coated["Coated_Side"].items():
                nfrc_id = int(nfrc_id)
                cases = {
                    "#2": _buildup((nfrc_id, coated_side == "Front"), (CLEAR_6, False)),
                    "#3": _buildup((CLEAR_6, False), (nfrc_id, coated_side == "Back")),
                }
                for surface, buildup in cases.items():
                    r = en410.solar_factor(buildup)
                    absorbed = r.A_1 + r.A_2
                    ok = (all(math.isfinite(v) for v in (r.g, r.tau_e, r.rho_e, r.A_1, r.A_2, r.q_i))
                          and abs(r.tau_e + r.rho_e + absorbed - 1.0) < 1e-9
                          and -tol <= r.tau_e <= r.g + tol
                          and r.g <= r.tau_e + absorbed + tol
                          and min(r.A_1, r.A_2, r.rho_e) >= -tol
                          and 0.0 < r.q_1 < r.q_2 < 1.0)
                    if not ok:
                        problems.append((nfrc_id, surface, r))
        self.assertGreater(len(coated), 1000)
        self.assertEqual(problems, [], f"{len(problems)} of {2 * len(coated)} results break an invariant")


if __name__ == "__main__":
    unittest.main()
