from collections import defaultdict
from unittest import TestCase

from spec_repair.helpers.adaptation_learned import Adaptation
from spec_repair.helpers.gr1_formula import GR1Formula
from spec_repair.helpers.spectra_formula_formatter import SpectraFormulaFormatter
from spec_repair.helpers.spectra_formula_parser import SpectraFormulaParser
from spec_repair.ltl_types import GR1TemporalType

from py_ltl.formula import AtomicProposition, Not, And, Or, Until, Next, Globally, Eventually, Implies, Prev, Top, \
    Bottom


class TestGR1Formula(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = SpectraFormulaParser()
        cls.formatter = SpectraFormulaFormatter()

    def test_parse_spectra_formula_ini(self):
        formula = "\thighwater=false&methane=false;"
        output = GR1Formula.from_str(formula, parser=self.parser)
        expected_output = GR1Formula(
            temp_type=GR1TemporalType.INITIAL,
            antecedent=None,
            consequent=And(AtomicProposition("highwater", False), AtomicProposition("methane", False)),
        )
        self.assertEqual(expected_output.temp_type, output.temp_type)
        self.assertEqual(expected_output.antecedent, output.antecedent)
        self.assertEqual(expected_output.consequent, output.consequent)

    def test_parse_spectra_formula_inv(self):
        formula = "\tG(highwater=false|methane=false);"
        output = GR1Formula.from_str(formula, parser=self.parser)
        expected_output = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=None,
            consequent=Or(AtomicProposition("highwater", False), AtomicProposition("methane", False)),
        )
        self.assertEqual(expected_output.temp_type, output.temp_type)
        self.assertEqual(expected_output.antecedent, output.antecedent)
        self.assertEqual(expected_output.consequent, output.consequent)

    def test_parse_spectra_formula_inv_2(self):
        formula = "\tG(PREV(pump=true)&pump=true->highwater=false);"
        output = GR1Formula.from_str(formula, parser=self.parser)
        expected_output = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=And(Prev(AtomicProposition("pump", True)), AtomicProposition("pump", True)),
            consequent=AtomicProposition("highwater", False),
        )
        self.assertEqual(expected_output.temp_type, output.temp_type)
        self.assertEqual(expected_output.antecedent, output.antecedent)
        self.assertEqual(expected_output.consequent, output.consequent)

    def test_parse_spectra_formula_to_justice(self):
        formula = "\tGF(pump=true);"
        output = GR1Formula.from_str(formula, parser=self.parser)
        expected_output = GR1Formula(
            temp_type=GR1TemporalType.JUSTICE,
            antecedent=None,
            consequent=AtomicProposition("pump", True),
        )
        self.assertEqual(expected_output.temp_type, output.temp_type)
        self.assertEqual(expected_output.antecedent, output.antecedent)
        self.assertEqual(expected_output.consequent, output.consequent)

    def test_parse_spectra_formula_to_response(self):
        formula = "\tG(true->F(highwater=false|methane=false));"
        output = GR1Formula.from_str(formula, parser=self.parser)
        expected_output = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=Top(),
            consequent=Eventually(Or(AtomicProposition("highwater", False), AtomicProposition("methane", False))),
        )
        self.assertEqual(expected_output.temp_type, output.temp_type)
        self.assertEqual(expected_output.antecedent, output.antecedent)
        self.assertEqual(expected_output.consequent, output.consequent)

    def test_format_formula_ini(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INITIAL,
            antecedent=None,
            consequent=Or(AtomicProposition("highwater", False), AtomicProposition("methane", False)),
        )
        output = formula.to_str(formatter=self.formatter)
        expected_output = "(highwater=false|methane=false)"
        self.assertEqual(expected_output, output)

    def test_format_formula_inv(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=None,
            consequent=Or(AtomicProposition("highwater", False), AtomicProposition("methane", False)),
        )
        output = formula.to_str(formatter=self.formatter)
        expected_output = "G((highwater=false|methane=false))"
        self.assertEqual(expected_output, output)

    def test_format_formula_inv_2(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=And(Prev(AtomicProposition("pump", True)), AtomicProposition("pump", True)),
            consequent=AtomicProposition("highwater", False),
        )
        output = formula.to_str(formatter=self.formatter)
        expected_output = "G(((PREV(pump=true)&pump=true)->highwater=false))"
        self.assertEqual(expected_output, output)

    def test_format_formula_justice(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.JUSTICE,
            antecedent=None,
            consequent=Or(AtomicProposition("highwater", False), AtomicProposition("methane", False))
        )
        output = formula.to_str(formatter=self.formatter)
        expected_output = "GF((highwater=false|methane=false))"
        self.assertEqual(expected_output, output)

    def test_format_formula_response(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=Top(),
            consequent=Eventually(Or(AtomicProposition("highwater", False), AtomicProposition("methane", False))),
        )
        output = formula.to_str(formatter=self.formatter)
        expected_output = "G((true->F((highwater=false|methane=false))))"
        self.assertEqual(expected_output, output)

    def test_integrate_adaptation_to_formula(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=None,
            consequent=[{'current': ['highwater=false']},
                        {'current': ['methane=false']}]
        )
        adaptation = Adaptation(
            type='antecedent_exception',
            formula_name='assumption2_1',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'methane=true')]
        )
        formula.integrate(adaptation)
        output = formula.to_str()
        expected_output = "G(methane=false->highwater=false|methane=false);"
        self.assertEqual(expected_output, output)

    def test_integrate_adaptation_to_formula_2(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=[defaultdict(list)],
            consequent=[{'current': ['a=true']}]
        )
        adaptation = Adaptation(
            type='antecedent_exception',
            formula_name='a_always',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'r1=false'),
                                     ('current', 'r2=false')]
        )
        formula.integrate(adaptation)
        output = formula.to_str()
        expected_output = "G(r1=true|r2=true->a=true);"
        self.assertEqual(expected_output, output)

    def test_integrate_eventualisation_adaptation_to_formula(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=[defaultdict(list)],
            consequent=[{'current': ['highwater=false']},
                        {'current': ['methane=false']}]
        )
        adaptation = Adaptation(
            type="ev_temp_op",
            formula_name="assumption2_1",
            disjunction_index=None,
            atom_temporal_operators=[]
        )
        formula.integrate(adaptation)
        output = formula.to_str()
        expected_output = "GF(highwater=false|methane=false);"
        self.assertEqual(expected_output, output)

    def test_integrate_eventualisation_adaptation_to_formula_2(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=[{'current': ['a=false']}],
            consequent=[{'current': ['r2=false']},
                        {'current': ['g1=false', 'g2=false']}]
        )
        adaptation = Adaptation(
            type="ev_temp_op",
            formula_name="guarantee3_1",
            disjunction_index=None,
            atom_temporal_operators=[]
        )
        formula.integrate(adaptation)
        output = formula.to_str()
        expected_output = "G(a=false->F(r2=false)|F(g1=false&g2=false));"
        self.assertEqual(expected_output, output)
