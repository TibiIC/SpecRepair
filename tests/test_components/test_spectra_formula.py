from collections import defaultdict
from unittest import TestCase

from spec_repair.helpers.adaptation_learned import Adaptation
from spec_repair.helpers.spectra_formula import SpectraFormula
from spec_repair.ltl_types import GR1TemporalType


class TestSpectraFormula(TestCase):
    def test_formula_DNF_to_str(self):
        parsed_formula = [
            {'next': ['a=true', 'b=true', 'c=false'], 'current': ['d=false'], 'prev': ['e=true']},  # First conjunct
            {'next': ['f=false'], 'current': ['g=true'], 'eventually': ['h=true', 'i=false']}  # Second conjunct
        ]
        output = SpectraFormula.formula_DNF_to_str(parsed_formula)
        expected_output = "(next(a=true&b=true&c=false)&d=false&PREV(e=true))|(next(f=false)&g=true&F(h=true&i=false))"
        self.assertEqual(expected_output, output)

    def test_formula_DNF_to_str_2(self):
        parsed_formula = [
            {'eventually': ['a=true', 'b=true']},
            {'eventually': ['c=true', 'd=false']}
        ]
        output = SpectraFormula.formula_DNF_to_str(parsed_formula)
        expected_output = "(F(a=true&b=true))|(F(c=true&d=false))"
        self.assertEqual(expected_output, output)

    def test_parse_spectra_formula_ini_to_DNF(self):
        formula = "\thighwater=false&methane=false;"
        output = SpectraFormula.from_str(formula)
        expected_output = SpectraFormula(
            temp_type=GR1TemporalType.INITIAL,
            antecedent=[defaultdict(list)],
            consequent=[{'current': ['highwater=false','methane=false']}]
        )
        self.assertEqual(expected_output.temp_type, output.temp_type)
        self.assertEqual(expected_output.antecedent, output.antecedent)
        self.assertEqual(expected_output.consequent, output.consequent)


    def test_parse_spectra_formula_to_DNF(self):
        formula = "\tG(highwater=false|methane=false);"
        output = SpectraFormula.from_str(formula)
        expected_output = SpectraFormula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=[defaultdict(list)],
            consequent=[{'current': ['highwater=false']},
                        {'current': ['methane=false']}]
        )
        self.assertEqual(expected_output.temp_type, output.temp_type)
        self.assertEqual(expected_output.antecedent, output.antecedent)
        self.assertEqual(expected_output.consequent, output.consequent)

    def test_parse_spectra_formula_to_DNF_2(self):
        formula = "\tG(PREV(pump=true)&pump=true->highwater=false);"
        output = SpectraFormula.from_str(formula)
        expected_output = SpectraFormula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=[{'prev': ['pump=true'], 'current': ['pump=true']}],
            consequent=[{'current': ['highwater=false']}]
        )
        self.assertEqual(expected_output.temp_type, output.temp_type)
        self.assertEqual(expected_output.antecedent, output.antecedent)
        self.assertEqual(expected_output.consequent, output.consequent)

    def test_parse_spectra_formula_to_DNF_3(self):
        formula = "\tGF(pump=true);"
        output = SpectraFormula.from_str(formula)
        expected_output = SpectraFormula(
            temp_type=GR1TemporalType.JUSTICE,
            antecedent=[defaultdict(list)],
            consequent=[{'current': ['pump=true']}]
        )
        self.assertEqual(expected_output.temp_type, output.temp_type)
        self.assertEqual(expected_output.antecedent, output.antecedent)
        self.assertEqual(expected_output.consequent, output.consequent)

    def test_parse_spectra_formula_to_DNF_4(self):
        formula = "\tG(true->F(highwater=false|methane=false));"
        output = SpectraFormula.from_str(formula)
        expected_output = SpectraFormula(
            temp_type=GR1TemporalType.JUSTICE,
            antecedent=[defaultdict(list)],
            consequent=[{'current': ['highwater=false']},
                        {'current': ['methane=false']}]
        )
        self.assertEqual(expected_output.temp_type, output.temp_type)
        self.assertEqual(expected_output.antecedent, output.antecedent)
        self.assertEqual(expected_output.consequent, output.consequent)


    def test_parse_justice_formula(self):
        formula = SpectraFormula(
            temp_type=GR1TemporalType.JUSTICE,
            antecedent=[defaultdict(list)],
            consequent=[{'current': ['highwater=false']},
                        {'current': ['methane=false']}]
        )
        output = formula.to_str()
        expected_output = "GF(highwater=false|methane=false);"
        self.assertEqual(expected_output, output)


    def test_integrate_adaptation_to_formula(self):
        formula = SpectraFormula(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=[defaultdict(list)],
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
        formula = SpectraFormula(
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
        formula = SpectraFormula(
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
        formula = SpectraFormula(
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

    def test_parse_spectra_formula_to_justice(self):
        formula = "\tG(true->F(highwater=false|methane=false));"
        output = SpectraFormula.from_str(formula)
        expected_output = SpectraFormula(
            temp_type=GR1TemporalType.JUSTICE,
            antecedent=[defaultdict(list)],
            consequent=[{'current': ['highwater=false']},
                        {'current': ['methane=false']}]
        )
        self.assertEqual(expected_output.temp_type, output.temp_type)
        self.assertEqual(expected_output.antecedent, output.antecedent)
        self.assertEqual(expected_output.consequent, output.consequent)

