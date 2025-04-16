from unittest import TestCase
import unittest
from py_ltl.formula import LTLFormula
from py_ltl.formula import (
    AtomicProposition, Not, And, Or, Until, Next, Globally, Eventually, Implies, Prev
)

from spec_repair.helpers.spectra_formula_parser import SpectraFormulaParser


class TestSpectraFormulaParser(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = SpectraFormulaParser()

    def test_parse_atomic(self):
        """Test parsing a simple atomic proposition using LTLFormula.parse()."""
        parsed = LTLFormula.parse("highwater=false", self.parser)
        self.assertIsInstance(parsed, AtomicProposition)
        self.assertEqual(parsed.value, False)
        self.assertEqual(parsed.name, "highwater")

    def test_parse_not(self):
        """Test parsing negation (!p) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("!highwater", self.parser)
        self.assertIsInstance(parsed, Not)
        self.assertIsInstance(parsed.formula, AtomicProposition)
        self.assertEqual(parsed.formula.name, "highwater")
        self.assertEqual(parsed.formula.value, True)

    def test_parse_and(self):
        """Test parsing conjunction (p & q) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("(highwater & methane)", self.parser)
        self.assertIsInstance(parsed, And)
        self.assertIsInstance(parsed.left, AtomicProposition)
        self.assertIsInstance(parsed.right, AtomicProposition)
        self.assertEqual(parsed.left.name, "highwater")
        self.assertEqual(parsed.left.value, True)
        self.assertEqual(parsed.right.name, "methane")
        self.assertEqual(parsed.right.value, True)

    def test_parse_and_2(self):
        """Test parsing conjunction (p & q) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("(highwater=true & methane=false)", self.parser)
        self.assertIsInstance(parsed, And)
        self.assertIsInstance(parsed.left, AtomicProposition)
        self.assertIsInstance(parsed.right, AtomicProposition)
        self.assertEqual(parsed.left.name, "highwater")
        self.assertEqual(parsed.left.value, True)
        self.assertEqual(parsed.right.name, "methane")
        self.assertEqual(parsed.right.value, False)

    def test_parse_or(self):
        """Test parsing disjunction (p | q) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("(highwater | pump)", self.parser)
        self.assertIsInstance(parsed, Or)
        self.assertEqual(parsed.left.name, "highwater")
        self.assertEqual(parsed.right.name, "pump")

    def test_parse_until(self):
        """Parsing until operator (p U q) should raise an error."""
        with self.assertRaises(NotImplementedError):
            parsed = LTLFormula.parse("(p U q)", self.parser)

    def test_parse_next(self):
        """Test parsing next operator (Xp) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("X(p)", self.parser)
        self.assertIsInstance(parsed, Next)
        self.assertIsInstance(parsed.formula, AtomicProposition)
        self.assertEqual(parsed.formula.name, "p")

    def test_parse_next_2(self):
        """Test parsing next operator (next(p=True)) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("next(pump=True)", self.parser)
        self.assertIsInstance(parsed, Next)
        self.assertIsInstance(parsed.formula, AtomicProposition)
        self.assertEqual(parsed.formula.name, "pump")
        self.assertEqual(parsed.formula.value, True)

    def test_parse_globally(self):
        """Test parsing globally operator (G(p)) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("G(highwater=false)", self.parser)
        self.assertIsInstance(parsed, Globally)
        self.assertEqual(parsed.formula.name, "highwater")
        self.assertEqual(parsed.formula.value, False)

    def test_parse_eventually(self):
        """Test parsing eventually operator (F(p)) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("F(p)", self.parser)
        self.assertIsInstance(parsed, Eventually)
        self.assertEqual(parsed.formula.name, "p")

    def test_parse_nested_expression(self):
        """Test parsing a more complex nested formula: (p=true->(q=false|r=true) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("(p=true -> (q=false | r=true))", self.parser)
        self.assertIsInstance(parsed, Implies)
        self.assertEqual(parsed.left.name, "p")
        self.assertIsInstance(parsed.right, Or)
        self.assertEqual(parsed.right.left.name, "q")
        self.assertEqual(parsed.right.left.value, False)
        self.assertEqual(parsed.right.right.name, "r")
        self.assertEqual(parsed.right.right.value, True)

    def test_parse_nested_expression_with_eventually(self):
        """Test parsing a more complex nested formula: (p=true->(q=false|r=true) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("(p=true -> F(q=false & r=true))", self.parser)
        self.assertIsInstance(parsed, Implies)
        self.assertEqual(parsed.left.name, "p")
        self.assertIsInstance(parsed.right, Eventually)
        self.assertIsInstance(parsed.right.formula, And)
        self.assertEqual(parsed.right.formula.left.name, "q")
        self.assertEqual(parsed.right.formula.left.value, False)
        self.assertEqual(parsed.right.formula.right.name, "r")
        self.assertEqual(parsed.right.formula.right.value, True)

    def test_parse_nested_expression_global_eventually(self):
        """Test parsing a more complex nested formula: () using LTLFormula.parse()."""
        parsed = LTLFormula.parse("\tGF(pump=true);", self.parser)
        self.assertIsInstance(parsed, Globally)
        self.assertIsInstance(parsed.formula, Eventually)
        self.assertIsInstance(parsed.formula.formula, AtomicProposition)
        self.assertEqual(parsed.formula.formula.name, "pump")
        self.assertEqual(parsed.formula.formula.value, True)

    @unittest.skip("Not happening in spectra, but should find way to allow anyway")
    def test_parse_nested_expression_eventually_global(self):
        """Test parsing a more complex nested formula: () using LTLFormula.parse()."""
        parsed = LTLFormula.parse("\tFG(pump=true);", self.parser)
        self.assertIsInstance(parsed, Eventually)
        self.assertIsInstance(parsed.formula, Globally)
        self.assertIsInstance(parsed.formula.formula, AtomicProposition)
        self.assertEqual(parsed.formula.formula.name, "pump")
        self.assertEqual(parsed.formula.formula.value, True)


    def test_parse_nested_expression_with_next(self):
        """Test parsing a more complex nested formula: (p & next(q)) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("(p=true & next(q=false))", self.parser)
        self.assertIsInstance(parsed, And)
        self.assertEqual(parsed.left.name, "p")
        self.assertIsInstance(parsed.right, Next)
        self.assertEqual(parsed.right.formula.name, "q")

    def test_parse_nested_expression_with_next_in_brackets(self):
        """Test parsing a more complex nested formula: (p & next(q)) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("(p & (next(q)))", self.parser)
        self.assertIsInstance(parsed, And)
        self.assertEqual(parsed.left.name, "p")
        self.assertIsInstance(parsed.right, Next)
        self.assertEqual(parsed.right.formula.name, "q")

    def test_parse_deeply_nested_expression(self):
        """Test parsing a deeply nested formula: (□(p → (q U r))) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("G(highwater=true->next(pump=true))", self.parser)
        self.assertIsInstance(parsed, Globally)
        self.assertIsInstance(parsed.formula, Implies)
        self.assertEqual(parsed.formula.left.name, "highwater")
        self.assertEqual(parsed.formula.left.value, True)
        self.assertIsInstance(parsed.formula.right, Next)
        self.assertEqual(parsed.formula.right.formula.name, "pump")
        self.assertEqual(parsed.formula.right.formula.value, True)

    def test_parse_deeply_nested_expression_prev(self):
        """Test parsing a deeply nested formula: () using LTLFormula.parse()."""
        parsed = LTLFormula.parse("\tG(PREV(pump=true)&pump=true->highwater=false);", self.parser)
        self.assertIsInstance(parsed, Globally)
        self.assertIsInstance(parsed.formula, Implies)
        self.assertIsInstance(parsed.formula.left, And)
        self.assertIsInstance(parsed.formula.left.left, Prev)
        self.assertEqual(parsed.formula.left.left.formula.name, "pump")
        self.assertEqual(parsed.formula.left.left.formula.value, True)
        self.assertEqual(parsed.formula.left.right.name, "pump")
        self.assertEqual(parsed.formula.left.right.value, True)
        self.assertEqual(parsed.formula.right.name, "highwater")
        self.assertEqual(parsed.formula.right.value, False)

    def test_parse_disjunction(self):
        """Test parsing nested disjunctions."""
        parsed = LTLFormula.parse("(highwater=true | methane=false | pump=true)", self.parser)
        print(parsed)
        self.assertIsInstance(parsed, Or)
        self.assertIsInstance(parsed.left, Or)
        self.assertEqual(parsed.left.left.name, "highwater")
        self.assertEqual(parsed.left.left.value, True)
        self.assertEqual(parsed.left.right.name, "methane")
        self.assertEqual(parsed.left.right.value, False)
        self.assertEqual(parsed.right.name, "pump")
        self.assertEqual(parsed.right.value, True)

    def test_parse_conjunction(self):
        """Test parsing nested conjunctions."""
        parsed = LTLFormula.parse("(highwater=true & methane=false & pump=true)", self.parser)
        self.assertIsInstance(parsed, And)
        self.assertIsInstance(parsed.left, And)
        self.assertEqual(parsed.left.left.name, "highwater")
        self.assertEqual(parsed.left.left.value, True)
        self.assertEqual(parsed.left.right.name, "methane")
        self.assertEqual(parsed.left.right.value, False)
        self.assertEqual(parsed.right.name, "pump")
        self.assertEqual(parsed.right.value, True)

    def test_parse_dnf(self):
        """Test parsing a formula in DNF: (a=true & b=false) | (c=true & d=false)."""
        parsed = LTLFormula.parse("((a=true & b=false) | (c=true & d=false))", self.parser)
        self.assertIsInstance(parsed, Or)
        self.assertIsInstance(parsed.left, And)
        self.assertEqual(parsed.left.left.name, "a")
        self.assertEqual(parsed.left.left.value, True)
        self.assertEqual(parsed.left.right.name, "b")
        self.assertEqual(parsed.left.right.value, False)
        self.assertIsInstance(parsed.right, And)
        self.assertEqual(parsed.right.left.name, "c")
        self.assertEqual(parsed.right.left.value, True)
        self.assertEqual(parsed.right.right.name, "d")
        self.assertEqual(parsed.right.right.value, False)

    def test_parse_nested_implication(self):
        """Test parsing nested implications."""
        parsed = LTLFormula.parse("(highwater=true -> methane=false -> pump=true)", self.parser)
        self.assertIsInstance(parsed, Implies)
        self.assertEqual(parsed.left.name, "highwater")
        self.assertEqual(parsed.left.value, True)
        self.assertIsInstance(parsed.right, Implies)
        self.assertEqual(parsed.right.left.name, "methane")
        self.assertEqual(parsed.right.left.value, False)
        self.assertEqual(parsed.right.right.name, "pump")
        self.assertEqual(parsed.right.right.value, True)

    def test_parse_ignore_optional_tab_and_semicolumn(self):
        """Test that optional tabs at the beginning of the formula are ignored."""
        parsed = LTLFormula.parse("\tG(highwater=false|methane=false);", self.parser)
        self.assertIsInstance(parsed, Globally)
        self.assertIsInstance(parsed.formula, Or)
        self.assertEqual(parsed.formula.left.name, "highwater")
        self.assertEqual(parsed.formula.left.value, False)
        self.assertEqual(parsed.formula.right.name, "methane")
        self.assertEqual(parsed.formula.right.value, False)

    def test_parse_real_example_lift(self):
        """Test that optional tabs at the beginning of the formula are ignored."""
        parsed = LTLFormula.parse("\tG(f2 -> (next(f1) & b1) | (next(f2) & !b1 & !b3) | (next(f3) & b3) | next(f2) & c);", self.parser)
        self.assertIsInstance(parsed, Globally)
        self.assertIsInstance(parsed.formula, Implies)
        self.assertEqual(parsed.formula.left.name, "f2")
        self.assertEqual(parsed.formula.left.value, True)
        self.assertIsInstance(parsed.formula.right, Or)
        self.assertIsInstance(parsed.formula.right.left, Or)
        self.assertIsInstance(parsed.formula.right.left.left, Or)
        self.assertIsInstance(parsed.formula.right.left.left.left, And)
        self.assertIsInstance(parsed.formula.right.left.left.left.left, Next)
        self.assertEqual(parsed.formula.right.left.left.left.left.formula.name, "f1")
        self.assertEqual(parsed.formula.right.left.left.left.right.name, "b1")
        self.assertIsInstance(parsed.formula.right.left.left.right, And)
        self.assertIsInstance(parsed.formula.right.left.left.right.left, And)
        self.assertIsInstance(parsed.formula.right.left.left.right.left.left, Next)
        self.assertEqual(parsed.formula.right.left.left.right.left.left.formula.value, "f2")
        self.assertIsInstance(parsed.formula.right.left.left.right.left.right, Not)
        self.assertEqual(parsed.formula.right.left.left.right.left.right.formula.name, "b1")
        self.assertIsInstance(parsed.formula.right.left.left.right.right, Not)
        self.assertEqual(parsed.formula.right.left.left.right.right.formula.name, "b3")

    def test_invalid_formula(self):
        """Test that invalid formulas raise an exception when using LTLFormula.parse()."""
        with self.assertRaises(Exception):
            LTLFormula.parse("p ^ q", self.parser)  # Invalid symbol "^"

        with self.assertRaises(Exception):
            LTLFormula.parse("()", self.parser)  # Empty brackets


if __name__ == "__main__":
    unittest.main()
