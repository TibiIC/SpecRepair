from unittest import TestCase
import unittest
from py_ltl.formula import LTLFormula
from py_ltl.formula import (
    AtomicProposition, Not, And, Or, Until, Next, Globally, Eventually
)

from spec_repair.components.spectra_formula_parser import SpectraFormulaParser


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
        """Test parsing negation (¬p) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("¬p", self.parser)
        self.assertIsInstance(parsed, Not)
        self.assertIsInstance(parsed.formula, AtomicProposition)
        self.assertEqual(parsed.formula.name, "p")

    def test_parse_and(self):
        """Test parsing conjunction (p ∧ q) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("(p ∧ q)", self.parser)
        self.assertIsInstance(parsed, And)
        self.assertIsInstance(parsed.left, AtomicProposition)
        self.assertIsInstance(parsed.right, AtomicProposition)
        self.assertEqual(parsed.left.name, "p")
        self.assertEqual(parsed.right.name, "q")

    def test_parse_or(self):
        """Test parsing disjunction (p ∨ q) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("(p ∨ q)", self.parser)
        self.assertIsInstance(parsed, Or)
        self.assertEqual(parsed.left.name, "p")
        self.assertEqual(parsed.right.name, "q")

    def test_parse_until(self):
        """Test parsing until operator (p U q) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("(p U q)", self.parser)
        self.assertIsInstance(parsed, Until)
        self.assertEqual(parsed.left.name, "p")
        self.assertEqual(parsed.right.name, "q")

    def test_parse_next(self):
        """Test parsing next operator (◯p) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("◯p", self.parser)
        self.assertIsInstance(parsed, Next)
        self.assertIsInstance(parsed.formula, AtomicProposition)
        self.assertEqual(parsed.formula.name, "p")

    def test_parse_globally(self):
        """Test parsing globally operator (□p) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("□p", self.parser)
        self.assertIsInstance(parsed, Globally)
        self.assertEqual(parsed.formula.name, "p")

    def test_parse_eventually(self):
        """Test parsing eventually operator (◇p) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("◇p", self.parser)
        self.assertIsInstance(parsed, Eventually)
        self.assertEqual(parsed.formula.name, "p")

    def test_parse_nested_expression(self):
        """Test parsing a more complex nested formula: (p ∧ (◇q)) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("(p ∧ (◇q))", self.parser)
        self.assertIsInstance(parsed, And)
        self.assertEqual(parsed.left.name, "p")
        self.assertIsInstance(parsed.right, Eventually)
        self.assertEqual(parsed.right.formula.name, "q")

    def test_parse_deeply_nested_expression(self):
        """Test parsing a deeply nested formula: (□(p → (q U r))) using LTLFormula.parse()."""
        parsed = LTLFormula.parse("□(p U (q U r))", self.parser)
        self.assertIsInstance(parsed, Globally)
        self.assertIsInstance(parsed.formula, Until)
        self.assertEqual(parsed.formula.left.name, "p")
        self.assertIsInstance(parsed.formula.right, Until)
        self.assertEqual(parsed.formula.right.left.name, "q")
        self.assertEqual(parsed.formula.right.right.name, "r")

    def test_invalid_formula(self):
        """Test that invalid formulas raise an exception when using LTLFormula.parse()."""
        with self.assertRaises(Exception):
            LTLFormula.parse("p & q", self.parser)  # Invalid symbol "&"

        with self.assertRaises(Exception):
            LTLFormula.parse("()", self.parser)  # Empty brackets


if __name__ == "__main__":
    unittest.main()
