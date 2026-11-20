#(c)2026 Jon Robinson. All Rights Reserved.

"""Tests for the coating surface picker: surface number <-> lite position and flip.

Run from the repo root:

    poetry run python -m unittest discover -s tests -t . -v

The tests read data/igdb.sqlite and are skipped when the data files are missing.
"""

import json
import unittest

try:
    from glass_explore import (Buildup, callback_helpers, callbacks_energy, en673,
                               glass_model_helpers, utils)
    from glass_explore.glass_model import GlassBuildup, InsulatedGlass
except FileNotFoundError as exc:  # data/igdb.sqlite is not in git
    raise unittest.SkipTest(f"IGDB data files are not available: {exc}")

# IGDB (NFRC) IDs
CLEAR_6 = 103             # generic clear, uncoated
PYROLYTIC_LOW_E = 9923    # Pilkington Energy Advantage, coating on the front face
VISION_51T_6 = 20711      # AGC Stopray Vision-51T 5.86 mm, coating on the back face

LOW_E = 0.3               # a corrected emissivity below this is a low-e coating


def _buildup(nfrc_id, surface):
    """Buildup dict as the page makes it for a clicked glass and a surface number."""
    buildup = callbacks_energy.buildup_from_inputs(
        callback_helpers.clickdata_for_glass_id(nfrc_id), surface, "argon", 16, "clear", 6)
    return json.loads(json.dumps(buildup))  # the app passes it through a dcc.Store


class SurfaceMappingTest(unittest.TestCase):

    def test_back_coated(self):
        # As measured, a back-coated lite has its coating on the face towards the room
        self.assertEqual(utils.lite_placement_from_surface(1, "Back"), (False, True))
        self.assertEqual(utils.lite_placement_from_surface(2, "Back"), (False, False))
        self.assertEqual(utils.lite_placement_from_surface(3, "Back"), (True, True))
        self.assertEqual(utils.lite_placement_from_surface(4, "Back"), (True, False))

    def test_front_coated(self):
        self.assertEqual(utils.lite_placement_from_surface(1, "Front"), (False, False))
        self.assertEqual(utils.lite_placement_from_surface(2, "Front"), (False, True))
        self.assertEqual(utils.lite_placement_from_surface(3, "Front"), (True, False))
        self.assertEqual(utils.lite_placement_from_surface(4, "Front"), (True, True))

    def test_no_single_coated_face_is_not_flipped_on_surfaces_2_and_4(self):
        for coated_side in ("Neither", "Both", "Unknown", None):
            with self.subTest(coated_side=coated_side):
                self.assertEqual(utils.lite_placement_from_surface(2, coated_side), (False, False))
                self.assertEqual(utils.lite_placement_from_surface(4, coated_side), (True, False))
                self.assertEqual(utils.lite_placement_from_surface(1, coated_side), (False, True))
                self.assertEqual(utils.lite_placement_from_surface(3, coated_side), (True, True))

    def test_inverse(self):
        for coated_side in ("Front", "Back", "Both", "Neither", "front", "BACK", None):
            for surface in utils.COATING_SURFACES:
                with self.subTest(coated_side=coated_side, surface=surface):
                    inside, flipped = utils.lite_placement_from_surface(surface, coated_side)
                    self.assertEqual(utils.surface_from_lite_placement(inside, flipped, coated_side), surface)

    def test_surface_as_string(self):
        self.assertEqual(utils.lite_placement_from_surface("3", "Back"), (True, True))

    def test_surface_out_of_range(self):
        for surface in (0, 5):
            with self.subTest(surface=surface):
                with self.assertRaises(ValueError):
                    utils.lite_placement_from_surface(surface, "Back")


class SurfaceControlTest(unittest.TestCase):

    def test_values_are_the_four_surfaces_for_every_product_type(self):
        for coated_side in ("Front", "Back", "Both", "Neither", None):
            with self.subTest(coated_side=coated_side):
                _, options, _ = callback_helpers.coating_surface_control(coated_side)
                self.assertEqual(sorted(o["value"] for o in options), list(utils.COATING_SURFACES))

    def test_single_coated_face_is_labelled_by_surface_number(self):
        label, options, _ = callback_helpers.coating_surface_control("Back")
        self.assertEqual(label, "Coating on surface")
        self.assertEqual([o["label"] for o in options], ["1", "2", "3", "4"])

    def test_uncoated_is_labelled_by_position(self):
        label, options, _ = callback_helpers.coating_surface_control("Neither")
        self.assertEqual(label, "Position")
        self.assertEqual({o["value"]: o["label"] for o in options},
                         {2: "Outer", 1: "Outer, flipped", 4: "Inner", 3: "Inner, flipped"})


class BuildupSurfaceTest(unittest.TestCase):
    """The coating ends up on the chosen surface whichever face the IGDB measured it on."""

    def _surface_emissivities(self, buildup):
        """Corrected emissivity of surfaces 1-4."""
        emissivities = []
        for layer in buildup[Buildup.SOLID_LAYERS]:
            front, back = layer["props"]["emis1"], layer["props"]["emis2"]
            emissivities += [back, front] if layer["flipped"] else [front, back]
        return emissivities

    def test_low_e_is_on_the_chosen_surface(self):
        for nfrc_id in (PYROLYTIC_LOW_E, VISION_51T_6):
            for surface in utils.COATING_SURFACES:
                with self.subTest(nfrc_id=nfrc_id, surface=surface):
                    emissivities = self._surface_emissivities(_buildup(nfrc_id, surface))
                    low_e = [s for s, e in zip(utils.COATING_SURFACES, emissivities) if e < LOW_E]
                    self.assertEqual(low_e, [surface])

    def test_selected_lite_position(self):
        for surface, coated_index in ((1, 0), (2, 0), (3, 1), (4, 1)):
            with self.subTest(surface=surface):
                buildup = _buildup(PYROLYTIC_LOW_E, surface)
                self.assertEqual(buildup[Buildup.COATED_LAYER_INDEX], coated_index)
                self.assertEqual(buildup[Buildup.SOLID_LAYERS][coated_index]["id"], PYROLYTIC_LOW_E)
                self.assertFalse(buildup[Buildup.SOLID_LAYERS][1 - coated_index]["flipped"])

    def test_front_and_back_coated_products_agree_on_cavity_surfaces(self):
        # The original fault: a front-coated low-e defaulted to surface 1, where it does
        # nothing for the cavity. On surface 2 or 3 the gap sees the low-e coating.
        for nfrc_id in (PYROLYTIC_LOW_E, VISION_51T_6):
            exposed = en673.u_value(_buildup(nfrc_id, 1)).u
            for surface in (2, 3):
                with self.subTest(nfrc_id=nfrc_id, surface=surface):
                    buildup = _buildup(nfrc_id, surface)
                    self.assertLess(min(en673._gap_emissivities(buildup[Buildup.SOLID_LAYERS], 0)), LOW_E)
                    self.assertLess(en673.u_value(buildup).u, exposed - 0.5)

    def test_missing_surface_falls_back_to_the_default(self):
        self.assertEqual(_buildup(PYROLYTIC_LOW_E, None), _buildup(PYROLYTIC_LOW_E, utils.DEFAULT_COATING_SURFACE))


class ShareLinkSurfaceTest(unittest.TestCase):
    """A share link stores lite order and flip; opening it restores the surface number."""

    def _surface_after_round_trip(self, nfrc_id, surface):
        buildup = _buildup(nfrc_id, surface)
        igu = InsulatedGlass(glass_model_helpers.lites_from_dict(buildup),
                             glass_model_helpers.gaslayers_from_dict(buildup))
        outputs = glass_model_helpers.callback_return_from_igu(GlassBuildup.make_glass(igu.to_gstr(False)))
        return outputs[3]

    def test_round_trip(self):
        for nfrc_id in (PYROLYTIC_LOW_E, VISION_51T_6):
            for surface in utils.COATING_SURFACES:
                with self.subTest(nfrc_id=nfrc_id, surface=surface):
                    self.assertEqual(self._surface_after_round_trip(nfrc_id, surface), surface)

    def test_links_made_before_the_picker_keep_their_meaning(self):
        # Outer lite, not flipped: surface 1 for a front-coated glass, 2 for a back-coated one
        for gstr, surface in (("#9923(6MONO)_12.0AIR_#103(6MONO)", 1),
                              ("#20711(6MONO)_12.0AIR_#103(6MONO)", 2),
                              ("#103(6MONO)_12.0AIR_#20711(6MONO)", 4)):
            with self.subTest(gstr=gstr):
                outputs = glass_model_helpers.callback_return_from_igu(GlassBuildup.make_glass(gstr))
                self.assertEqual(outputs[3], surface)


if __name__ == "__main__":
    unittest.main()
