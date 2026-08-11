"""
The pRespondsToS substitution has to count parentheses, not guess at them.

It used to take `s` as everything between `G(` and the first `-`, and `p` as
everything after `F(` less two characters. That is right only for a formula
with exactly one level of parentheses around the implication - the form
`ideal.spectra` happens to use. Every `strong.spectra` has one level more, as
does amba's `original.spectra`, and the result was an unmatched `(` in `s` and a
spare `)` in `p`:

    G((a->F(b)))  ->  pRespondsToS((a,b))

Spectra rejected that with `missing ')' at ','` - a message that names the
comma, and so reads as a broken specification rather than a broken rewrite.
26 of the 92 response formulas in the case studies were affected, amba's six
among them, which is why amba could not be synthesised through this path.
"""
import unittest

from spec_repair.util.asp_trace_util import _response_operands


def balanced(expr: str) -> bool:
    depth = 0
    for c in expr:
        depth += (c == "(") - (c == ")")
        if depth < 0:
            return False
    return depth == 0


class TestResponseOperands(unittest.TestCase):
    def test_single_level_of_parentheses(self):
        """The form that always worked, and must keep working."""
        self.assertEqual(("a=true", "b=false"),
                         _response_operands("\tG(a=true->F(b=false));"))

    def test_extra_level_of_parentheses(self):
        """The regression: strong.spectra's form."""
        self.assertEqual(("a=true", "b=false"),
                         _response_operands("\tG((a=true->F(b=false)));"))

    def test_amba(self):
        """The formula that took amba down, verbatim."""
        line = ("G((((hmastlock=true&(hburst_single=false&hburst_burst4=false))"
                "&hmaster_val0=true)->F(next(hbusreq_0=false))))")
        s, p = _response_operands(line)
        self.assertEqual("(hmastlock=true&(hburst_single=false&hburst_burst4=false))"
                         "&hmaster_val0=true", s)
        self.assertEqual("next(hbusreq_0=false)", p)
        self.assertTrue(balanced(s) and balanced(p))

    def test_nested_implication_in_the_antecedent(self):
        """
        The split must be at the top-level `->`. Splitting at the first one
        would make the antecedent `(a` and lose the rest.
        """
        s, p = _response_operands("G(((a->b)&c)->F(d))")
        self.assertEqual("(a->b)&c", s)
        self.assertEqual("d", p)

    def test_parenthesised_consequent(self):
        s, p = _response_operands("G((a->F((b&c))))")
        self.assertEqual("a", s)
        self.assertEqual("b&c", p)

    def test_rejects_a_formula_with_no_implication(self):
        with self.assertRaises(ValueError):
            _response_operands("G(F(a=true));")

    def test_rejects_a_consequent_that_is_not_eventually(self):
        with self.assertRaises(ValueError):
            _response_operands("G((a=true->b=false));")

    def test_every_case_study_response_formula_is_balanced(self):
        """
        The property that matters: whatever the shape, both operands come out
        balanced, because an unbalanced one is what Spectra refuses to parse.
        """
        import glob
        from spec_repair.util.patterns import PRS_REG
        checked = 0
        for path in glob.glob("input-files/case-studies/spectra/case_study_*/*/*.spectra"):
            for line in open(path).read().splitlines():
                if not PRS_REG.search(line.strip("\t\n;")):
                    continue
                checked += 1
                s, p = _response_operands(line)
                self.assertTrue(balanced(s), f"unbalanced antecedent in {path}: {s}")
                self.assertTrue(balanced(p), f"unbalanced consequent in {path}: {p}")
        self.assertGreater(checked, 0, "no response formulas found - wrong working directory?")


if __name__ == "__main__":
    unittest.main()
