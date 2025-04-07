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

    def test_parse_spectra_formula_justice(self):
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

    def test_parse_spectra_formula_response(self):
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

    def test_integrate_adaptation_to_formula_antecedent_exception(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=None,
            consequent=Or(AtomicProposition("highwater", False), AtomicProposition("methane", False))
        )  # formula === G(highwater=false|methane=false)
        adaptation = Adaptation(
            type='antecedent_exception',
            formula_name='assumption2_1',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'methane=true')]
        )
        formula.integrate(adaptation)
        output = formula.to_str(self.formatter)
        expected_output = "G((methane=false->(highwater=false|methane=false)))"
        self.assertEqual(expected_output, output)

    def test_integrate_adaptation_to_formula_antecedent_exception_2(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=None,
            consequent=AtomicProposition("a", True),
        )  # formula === G(a=true)
        adaptation = Adaptation(
            type='antecedent_exception',
            formula_name='a_always',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'r1=false'),
                                     ('current', 'r2=false')]
        )
        formula.integrate(adaptation)
        output = formula.to_str(self.formatter)
        expected_output = "G(((r1=true|r2=true)->a=true))"
        self.assertEqual(expected_output, output)

    def test_integrate_adaptation_to_formula_antecedent_exception_3(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=AtomicProposition("a", True),
            consequent=AtomicProposition("b", True),
        )  # formula === G(a=true->b=true)
        adaptation = Adaptation(
            type='antecedent_exception',
            formula_name='a_always',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'c=false')]
        )
        formula.integrate(adaptation)
        output = formula.to_str(self.formatter)
        expected_output = "G(((a=true&c=true)->b=true))"
        self.assertEqual(expected_output, output)

    def test_integrate_adaptation_to_formula_antecedent_exception_4(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=And(AtomicProposition("a", True), AtomicProposition("b", True)),
            consequent=AtomicProposition("c", True),
        )  # formula === G(a=true&b=true->c=true)
        adaptation = Adaptation(
            type='antecedent_exception',
            formula_name='a_always',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'd=false')]
        )
        formula.integrate(adaptation)
        output = formula.to_str(self.formatter)
        expected_output = "G((((a=true&b=true)&d=true)->c=true))"
        self.assertEqual(expected_output, output)

    def test_integrate_adaptation_to_formula_antecedent_exception_5(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=Or(AtomicProposition("a", True), AtomicProposition("b", True)),
            consequent=AtomicProposition("c", True),
        )  # formula === G(a=true|b=true->c=true)
        adaptation = Adaptation(
            type='antecedent_exception',
            formula_name='a_always',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'd=false')]
        )
        formula.integrate(adaptation)
        output = formula.to_str(self.formatter)
        expected_output = "G(((b=true|(a=true&d=true))->c=true))"
        self.assertEqual(expected_output, output)

    def test_integrate_adaptation_to_formula_antecedent_exception_6(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=Or(AtomicProposition("a", True), AtomicProposition("b", True)),
            consequent=AtomicProposition("c", True),
        )  # formula === G(a=true|b=true->c=true)
        adaptation = Adaptation(
            type='antecedent_exception',
            formula_name='a_always',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'd=false'), ('current', 'e=false')]
        )
        formula.integrate(adaptation)
        output = formula.to_str(self.formatter)
        expected_output = "G((((b=true|(a=true&d=true))|(a=true&e=true))->c=true))"
        self.assertEqual(expected_output, output)

    def test_integrate_adaptation_to_formula_antecedent_exception_7(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=Or(Prev(AtomicProposition("a", True)), AtomicProposition("b", True)),
            consequent=AtomicProposition("c", True),
        )  # formula === G(a=true|b=true->c=true)
        adaptation = Adaptation(
            type='antecedent_exception',
            formula_name='a_always',
            disjunction_index=0,
            atom_temporal_operators=[('next', 'd=false'), ('prev', 'e=false')]
        )
        formula.integrate(adaptation)
        output = formula.to_str(self.formatter)
        expected_output = "G((((b=true|(PREV(a=true)&next(d=true)))|(PREV(a=true)&PREV(e=true)))->c=true))"
        self.assertEqual(expected_output, output)

    def test_integrate_adaptation_to_formula_consequent_exception(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=AtomicProposition("highwater", True),
            consequent=Next(AtomicProposition("pump", True))
        )  # formula === G(highwater=true->next(pump=true))
        adaptation = Adaptation(
            type='consequent_exception',
            formula_name='consequent2_1',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'methane=true')]
        )
        formula.integrate(adaptation)
        output = formula.to_str(self.formatter)
        expected_output = "G((highwater=true->(next(pump=true)|methane=true)))"
        self.assertEqual(expected_output, output)

    def test_integrate_adaptation_to_formula_consequent_exception_2(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=AtomicProposition("a", True),
            consequent=Next(AtomicProposition("b", True))
        )  # formula === G(a=true->next(b=true))
        adaptation = Adaptation(
            type='consequent_exception',
            formula_name='consequent2_1',
            disjunction_index=0,
            atom_temporal_operators=[('prev', 'c=true')]
        )
        formula.integrate(adaptation)
        output = formula.to_str(self.formatter)
        expected_output = "G((a=true->(next(b=true)|PREV(c=true))))"
        self.assertEqual(expected_output, output)

    def test_integrate_adaptation_to_formula_consequent_exception_3(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=AtomicProposition("a", True),
            consequent=Or(AtomicProposition("b", True), AtomicProposition("c", True))
        )  # formula === G(a=true->(b=true|c=true))
        adaptation = Adaptation(
            type='consequent_exception',
            formula_name='consequent2_1',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'd=true')]
        )
        formula.integrate(adaptation)
        output = formula.to_str(self.formatter)
        expected_output = "G((a=true->((b=true|c=true)|d=true)))"
        self.assertEqual(expected_output, output)

    def test_integrate_adaptation_to_formula_consequent_exception_4(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=AtomicProposition("a", True),
            consequent=And(AtomicProposition("b", True), AtomicProposition("c", True))
        )  # formula === G(a=true->(b=true&c=true))
        adaptation = Adaptation(
            type='consequent_exception',
            formula_name='consequent2_1',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'd=true')]
        )
        formula.integrate(adaptation)
        output = formula.to_str(self.formatter)
        expected_output = "G((a=true->((b=true&c=true)|d=true)))"
        self.assertEqual(expected_output, output)

    def test_integrate_adaptation_to_formula_consequent_exception_5(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=AtomicProposition("a", True),
            consequent=Or(AtomicProposition("b", True), AtomicProposition("c", True))
        )  # formula === G(a=true->(b=true|c=true))
        adaptation = Adaptation(
            type='consequent_exception',
            formula_name='consequent2_1',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'd=true'), ('current', 'e=true')]
        )
        formula.integrate(adaptation)
        output = formula.to_str(self.formatter)
        expected_output = "G((a=true->((b=true|c=true)|(d=true&e=true))))"
        self.assertEqual(expected_output, output)

    def test_integrate_adaptation_to_formula_consequent_exception_6(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=AtomicProposition("a", True),
            consequent=Or(AtomicProposition("b", True), And(AtomicProposition("c", True), AtomicProposition("d", True)))
        )  # formula === G(a=true->(b=true|(c=true&d=true))
        adaptation = Adaptation(
            type='consequent_exception',
            formula_name='consequent2_1',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'e=true'), ('current', 'f=true')]
        )
        formula.integrate(adaptation)
        output = formula.to_str(self.formatter)
        expected_output = "G((a=true->((b=true|(c=true&d=true))|(e=true&f=true))))"
        self.assertEqual(expected_output, output)

    def test_integrate_adaptation_to_formula_ev_temp_op(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=None,
            consequent=Or(AtomicProposition("highwater", False), AtomicProposition("methane", False))
        )  # formula === G(highwater=false|methane=false
        adaptation = Adaptation(
            type="ev_temp_op",
            formula_name="assumption2_1",
            disjunction_index=None,
            atom_temporal_operators=[]
        )
        formula.integrate(adaptation)
        output = formula.to_str(self.formatter)
        expected_output = "GF((highwater=false|methane=false))"
        self.assertEqual(expected_output, output)

    def test_integrate_eventualisation_adaptation_to_formula_2(self):
        formula = GR1Formula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=AtomicProposition("a", False),
            consequent=Or(AtomicProposition("r1", False),
                          And(AtomicProposition("g1", False), AtomicProposition("g2", False)))
        )
        adaptation = Adaptation(
            type="ev_temp_op",
            formula_name="guarantee3_1",
            disjunction_index=None,
            atom_temporal_operators=[]
        )
        formula.integrate(adaptation)
        output = formula.to_str(self.formatter)
        expected_output = "G((a=false->F((r1=false|(g1=false&g2=false)))))"
        self.assertEqual(expected_output, output)
