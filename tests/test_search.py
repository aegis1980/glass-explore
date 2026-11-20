#(c)2026 Jon Robinson. All Rights Reserved.

"""Tests for glass_explore.search, the text search behind the search modal.

Run from the repo root:

    poetry run python -m unittest discover -s tests -t . -v

The tests read data/glass.parquet and are skipped when the data files are missing.
"""

import unittest

try:
    from glass_explore import DF_GLASS_TABLE, callback_helpers, search
except FileNotFoundError as exc:  # data/igdb.sqlite is not in git
    raise unittest.SkipTest(f"IGDB data files are not available: {exc}")

# IGDB (NFRC) IDs
CLEAR_6 = 103             # generic clear
PYROLYTIC_LOW_E = 9923    # Pilkington Energy Advantage
SOLARBAN_60_CLEAR_6 = 5284

PILKINGTON_NA = "Pilkington North America"


def _names(ids):
    return DF_GLASS_TABLE.loc[ids, "ProductName"].map(search.normalise)


class NormaliseTest(unittest.TestCase):

    def test_trade_mark_signs_and_punctuation(self):
        self.assertEqual(search.normalise("Solarban® 60 on Starphire®  6mm"), "solarban 60 on starphire 6mm")
        self.assertEqual(search.normalise("Energy Advantage™ Low-E"), "energy advantage low e")
        self.assertEqual(search.normalise("SB60 Clear_6.VTA"), "sb60 clear 6 vta")

    def test_accents(self):
        self.assertEqual(search.normalise("Glas Trösch AG"), "glas trosch ag")

    def test_nothing_searchable(self):
        for text in ("", "   ", "®", None, "--"):
            with self.subTest(text=text):
                self.assertEqual(search.normalise(text), "")


class SearchTest(unittest.TestCase):

    def test_no_query_lists_everything_in_table_order(self):
        found = search.search("")
        self.assertFalse(found.has_query)
        self.assertEqual(found.total, len(DF_GLASS_TABLE))
        self.assertEqual(list(found.ids), list(DF_GLASS_TABLE.index))

    def test_query_without_letters_or_digits_is_no_query(self):
        for query in (None, "   ", "®", "-"):
            with self.subTest(query=query):
                self.assertFalse(search.search(query).has_query)

    def test_trade_mark_sign_in_the_product_name(self):
        # 'Solarban® 60' used to hide these from a search for 'solarban 60'
        found = search.search("solarban 60")
        self.assertIn(SOLARBAN_60_CLEAR_6, found.ids)
        self.assertFalse(found.similar)
        self.assertTrue(_names(found.ids).str.contains("solarban").all())
        self.assertTrue(_names(found.ids[:10]).str.startswith("solarban 60").all())

    def test_every_word_has_to_match(self):
        found = search.search("solarban 60 starphire")
        self.assertGreater(found.total, 0)
        self.assertLess(found.total, search.search("solarban 60").total)
        self.assertTrue(_names(found.ids).str.contains("starphire").all())

    def test_word_order_and_case_do_not_matter(self):
        self.assertEqual(set(search.search("STARPHIRE Solarban 60").ids), set(search.search("solarban 60 starphire").ids))

    def test_letters_joined_to_digits(self):
        self.assertEqual(list(search.search("solarban60").ids), list(search.search("solarban 60").ids))

    def test_manufacturer_and_nominal_thickness_are_searched(self):
        found = search.search("vitro solarban 60 6mm clear")
        self.assertIn(SOLARBAN_60_CLEAR_6, found.ids)
        self.assertTrue((DF_GLASS_TABLE.loc[found.ids, "Thickness"].round() == 6).all())

    def test_accents_are_optional(self):
        found = search.search("glas trosch")
        self.assertGreater(found.total, 0)
        self.assertTrue((DF_GLASS_TABLE.loc[found.ids, "Manufacturer"] == "Glas Trösch AG").all())

    def test_exact_id_comes_first(self):
        for glass_id in (CLEAR_6, PYROLYTIC_LOW_E):
            with self.subTest(glass_id=glass_id):
                self.assertEqual(search.search(str(glass_id)).ids[0], glass_id)

    def test_number_matches_the_start_of_an_id_not_the_middle(self):
        ids = search.search("992").ids
        self.assertIn(PYROLYTIC_LOW_E, ids)
        self.assertNotIn(19923, ids)   # holds whether or not ID 19923 exists
        found = search.search(str(PYROLYTIC_LOW_E)[1:])  # "923"
        self.assertNotIn(PYROLYTIC_LOW_E, found.ids)

    def test_own_name_ranks_above_coating_name(self):
        # Some SKN 076 products carry the coating name "SKN 176"
        names = _names(search.search("cool-lite skn 176").ids)
        with_176 = names.str.contains("skn 176").to_list()
        self.assertTrue(with_176[0])
        self.assertEqual(with_176, sorted(with_176, reverse=True))

    def test_spelling_mistake(self):
        found = search.search("pilkinton optifloat")
        self.assertTrue(found.similar)
        self.assertGreater(found.total, 0)
        self.assertTrue(DF_GLASS_TABLE.loc[found.ids, "Manufacturer"].str.contains("Pilkington").all())
        self.assertTrue(_names(found.ids).str.contains("optifloat").all())

    def test_nonsense_finds_nothing(self):
        # There is no "closest 30" fallback
        for query in ("xyzzy", "qwertyuiop asdf", "solarban qwertyuiop"):
            with self.subTest(query=query):
                found = search.search(query)
                self.assertTrue(found.has_query)
                self.assertEqual((found.total, found.total_unfiltered, len(found.ids)), (0, 0, 0))

    def test_filter(self):
        pilkington = DF_GLASS_TABLE.index[DF_GLASS_TABLE["Manufacturer"] == PILKINGTON_NA]

        found = search.search("energy advantage", allowed_ids=pilkington)
        self.assertIn(PYROLYTIC_LOW_E, found.ids)
        self.assertTrue(set(found.ids) <= set(pilkington))
        self.assertGreater(found.total_unfiltered, found.total)  # other makers laminate it

        hidden = search.search("solarban 60", allowed_ids=pilkington)
        self.assertEqual(hidden.total, 0)
        self.assertEqual(hidden.total_unfiltered, search.search("solarban 60").total)

    def test_limit(self):
        found = search.search("clear", limit=10)
        self.assertEqual(len(found.ids), 10)
        self.assertGreater(found.total, 10)
        self.assertEqual(list(found.ids), list(search.search("clear").ids[:10]))

    def test_thicknesses_of_one_product_are_in_order(self):
        ids = search.search("solarban 60 on clear").ids
        rows = DF_GLASS_TABLE.loc[ids]
        rows = rows[rows["ProductName"].str.startswith("Solarban® 60 on Clear")]
        self.assertGreater(len(rows), 3)
        self.assertEqual(rows["Thickness"].to_list(), sorted(rows["Thickness"]))


class SearchMessageTest(unittest.TestCase):

    def _message(self, query, allowed_ids=None, filtered=False, limit=search.MAX_ROWS):
        found = search.search(query, allowed_ids=allowed_ids, limit=limit)
        return callback_helpers.search_message(found, filtered, PILKINGTON_NA, 4)

    def test_no_query(self):
        self.assertEqual(self._message("", limit=None), (f"{len(DF_GLASS_TABLE)} glasses", "darkgrey"))
        text, _ = self._message("")
        self.assertTrue(text.startswith(f"Showing the first {search.MAX_ROWS} of {len(DF_GLASS_TABLE)} glasses"))

    def test_matches(self):
        self.assertEqual(self._message(str(PYROLYTIC_LOW_E)), ("1 match", "darkgrey"))
        text, colour = self._message("solarban 60")
        self.assertRegex(text, r"^\d+ matches$")
        self.assertEqual(colour, "darkgrey")

    def test_similar_spelling(self):
        text, colour = self._message("pilkinton optifloat")
        self.assertRegex(text, r"^No exact match; \d+ with similar spelling$")
        self.assertEqual(colour, "darkgrey")

    def test_no_match(self):
        self.assertEqual(self._message("xyzzy"), ("No match", "red"))

    def test_filters_hiding_the_matches(self):
        pilkington = DF_GLASS_TABLE.index[DF_GLASS_TABLE["Manufacturer"] == PILKINGTON_NA]
        text, colour = self._message("solarban 60", allowed_ids=pilkington, filtered=True)
        self.assertRegex(text, r"^No match with these filters; \d+ without them$")
        self.assertEqual(colour, "red")

    def test_empty_filter(self):
        text, colour = self._message("", allowed_ids=DF_GLASS_TABLE.index[:0], filtered=True)
        self.assertEqual((text, colour), (f"No glasses from {PILKINGTON_NA} with thickness, 4mm", "red"))


if __name__ == "__main__":
    unittest.main()
