from collections import defaultdict
from unittest import TestCase

from spec_repair.helpers.adaptation_learned import AdaptationLearned
from spec_repair.helpers.spectra_rule import SpectraRule
from spec_repair.ltl_types import GR1TemporalType


class TestSpectraRule(TestCase):
    def test_formula_DNF_to_str(self):
        parsed_formula = [
            {'next': ['a=true', 'b=true', 'c=false'], 'current': ['d=false'], 'prev': ['e=true']},  # First conjunct
            {'next': ['f=false'], 'current': ['g=true'], 'eventually': ['h=true', 'i=false']}  # Second conjunct
        ]
        output = SpectraRule.formula_DNF_to_str(parsed_formula)
        expected_output = "(next(a=true&b=true&c=false)&d=false&PREV(e=true))|(next(f=false)&g=true&F(h=true&i=false))"
        self.assertEqual(expected_output, output)

    def test_formula_DNF_to_str_2(self):
        parsed_formula = [
            {'eventually': ['a=true', 'b=true']},
            {'eventually': ['c=true', 'd=false']}
        ]
        output = SpectraRule.formula_DNF_to_str(parsed_formula)
        expected_output = "(F(a=true&b=true))|(F(c=true&d=false))"
        self.assertEqual(expected_output, output)

    def test_parse_spectra_formula_to_DNF(self):
        formula = "\tG(highwater=false|methane=false);"
        output = SpectraRule.from_str(formula)
        expected_output = SpectraRule(
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
        output = SpectraRule.from_str(formula)
        expected_output = SpectraRule(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=[{'prev': ['pump=true'], 'current': ['pump=true']}],
            consequent=[{'current': ['highwater=false']}]
        )
        self.assertEqual(expected_output.temp_type, output.temp_type)
        self.assertEqual(expected_output.antecedent, output.antecedent)
        self.assertEqual(expected_output.consequent, output.consequent)

    def test_parse_spectra_formula_to_DNF_3(self):
        formula = "\tGF(pump=true);"
        output = SpectraRule.from_str(formula)
        expected_output = SpectraRule(
            temp_type=GR1TemporalType.JUSTICE,
            antecedent=[defaultdict(list)],
            consequent=[{'current': ['pump=true']}]
        )
        self.assertEqual(expected_output.temp_type, output.temp_type)
        self.assertEqual(expected_output.antecedent, output.antecedent)
        self.assertEqual(expected_output.consequent, output.consequent)

    def test_parse_justice_rule(self):
        rule = SpectraRule(
            temp_type=GR1TemporalType.JUSTICE,
            antecedent=[defaultdict(list)],
            consequent=[{'current': ['highwater=false']},
                        {'current': ['methane=false']}]
        )
        output = rule.to_str()
        expected_output = "GF(highwater=false|methane=false);"
        self.assertEqual(expected_output, output)


    def test_integrate_adaptation_to_formula(self):
        formula = SpectraRule(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=[defaultdict(list)],
            consequent=[{'current': ['highwater=false']},
                        {'current': ['methane=false']}]
        )
        adaptation = AdaptationLearned(
            type='antecedent_exception',
            name_expression='assumption2_1',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'methane=true')]
        )
        formula.integrate(adaptation)
        output = formula.to_str()
        expected_output = "G(methane=false->highwater=false|methane=false);"
        self.assertEqual(expected_output, output)

    def test_integrate_adaptation_to_formula_2(self):
        formula = SpectraRule(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=[defaultdict(list)],
            consequent=[{'current': ['a=true']}]
        )
        adaptation = AdaptationLearned(
            type='antecedent_exception',
            name_expression='a_always',
            disjunction_index=0,
            atom_temporal_operators=[('current', 'r1=false'),
                                     ('current', 'r2=false')]
        )
        formula.integrate(adaptation)
        output = formula.to_str()
        expected_output = "G(r1=true|r2=true->a=true);"
        self.assertEqual(expected_output, output)

    def test_integrate_eventualisation_adaptation_to_formula(self):
        formula = SpectraRule(
            temp_type=GR1TemporalType.INVARIANT,
            antecedent=[defaultdict(list)],
            consequent=[{'current': ['highwater=false']},
                        {'current': ['methane=false']}]
        )
        adaptation = AdaptationLearned(
            type="ev_temp_op",
            name_expression="assumption2_1",
            disjunction_index=None,
            atom_temporal_operators=[]
        )
        formula.integrate(adaptation)
        output = formula.to_str()
        expected_output = "GF(highwater=false|methane=false);"
        self.assertEqual(expected_output, output)
