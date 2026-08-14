"""
Canonical Spectra text, used to key the unrealisable-core cache.

Two properties matter, and they pull against each other: reorderings of the same
specification must collapse to one string, and two *different* specifications
must never do so - a false match would serve one specification's cores for
another's, silently.
"""
import unittest
from unittest import TestCase

from spec_repair.util.spectra_text_util import canonical_spectra_text

MINEPUMP = """\
module Minepump

env boolean highwater;
env boolean methane;
sys boolean pump;

assumption -- initial_assumption
    !highwater & !methane;

guarantee -- initial_guarantee
    !pump;

guarantee -- guarantee1_1
\tG(highwater->next(pump));
"""

# Same specification, written in a different order and indented differently.
MINEPUMP_REORDERED = """\
module Minepump

sys boolean pump;
env boolean methane;
env boolean highwater;

guarantee -- guarantee1_1
    G(highwater->next(pump));

guarantee -- initial_guarantee
\t!pump;

assumption -- initial_assumption
        !highwater & !methane;
"""


class TestCanonicalSpectraText(TestCase):
    def test_reordering_formulas_and_declarations_gives_the_same_text(self):
        self.assertEqual(canonical_spectra_text(MINEPUMP),
                         canonical_spectra_text(MINEPUMP_REORDERED))

    def test_a_changed_formula_does_not_collapse(self):
        changed = MINEPUMP.replace("G(highwater->next(pump));", "G(highwater->next(!pump));")
        self.assertNotEqual(canonical_spectra_text(MINEPUMP),
                            canonical_spectra_text(changed))

    def test_a_renamed_formula_does_not_collapse(self):
        """Cores come back as names, so a rename is a different answer, not a formatting change."""
        renamed = MINEPUMP.replace("guarantee1_1", "guarantee1_2")
        self.assertNotEqual(canonical_spectra_text(MINEPUMP),
                            canonical_spectra_text(renamed))

    def test_an_added_formula_does_not_collapse(self):
        extra = MINEPUMP + "\nguarantee -- extra\n    G(pump);\n"
        self.assertNotEqual(canonical_spectra_text(MINEPUMP),
                            canonical_spectra_text(extra))

    def test_assumption_and_guarantee_of_the_same_name_stay_distinct(self):
        as_asm = "module M\nassumption -- x\n G(a);\n"
        as_gar = "module M\nguarantee -- x\n G(a);\n"
        self.assertNotEqual(canonical_spectra_text(as_asm),
                            canonical_spectra_text(as_gar))

    def test_asm_and_assumption_spellings_agree(self):
        long_form = "module M\nassumption -- x\n G(a);\n"
        short_form = "module M\nasm -- x\n G(a);\n"
        self.assertEqual(canonical_spectra_text(long_form),
                         canonical_spectra_text(short_form))

    def test_multi_line_formulas_are_kept_whole(self):
        multi = "module M\nguarantee -- g\n G(a ->\n   next(b));\n"
        single = "module M\nguarantee -- g\n G(a -> next(b));\n"
        self.assertEqual(canonical_spectra_text(multi), canonical_spectra_text(single))

    def test_unrecognised_lines_are_preserved_in_order(self):
        """An unparsed construct should cost a miss, never a wrong hit."""
        with_define = "module M\ndefine foo := a & b;\nguarantee -- g\n G(a);\n"
        self.assertIn("define foo := a & b;", canonical_spectra_text(with_define))

    def test_is_idempotent(self):
        once = canonical_spectra_text(MINEPUMP)
        self.assertEqual(once, canonical_spectra_text(once))

    def test_empty_input_is_handled(self):
        self.assertEqual("", canonical_spectra_text(""))


if __name__ == "__main__":
    unittest.main()
