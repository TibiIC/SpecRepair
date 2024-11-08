from unittest import TestCase

import pandas as pd

from spec_repair.components.spec_encoder import SpecEncoder
from spec_repair.components.spec_generator import SpecGenerator
from spec_repair.enums import Learning
from spec_repair.helpers.adaptation_learned import AdaptationLearned
from spec_repair.util.exp_util import extract_adaptation_from_rule
from spec_repair.util.file_util import read_file
from spec_repair.util.spec_util import get_assumptions_and_guarantees_from


class TestSpecEncoder(TestCase):
    minepump_spec_file = '../../input-files/examples/Minepump/minepump_strong.spectra'
    minepump_spec_1_aw_step = '../test_files/minepump_aw_methane.spectra'
    minepump_clingo_file = '../test_files/minepump_strong_WA_no_cs.lp'
    minepump_mode_bias_aw_file = '../test_files/mode_bias/minepump_1_aw_step.txt'
    minepump_mode_bias_gw_file = '../test_files/mode_bias/minepump_1_gw_step.txt'
    maxDiff = None

    def test_encode_asp(self):
        expected_clingo_str: str = read_file(self.minepump_clingo_file)
        spec_df: pd.DataFrame = get_assumptions_and_guarantees_from(self.minepump_spec_file)
        trace_name = "trace_name_0"
        trace = [
            f'not_holds_at(highwater,0,{trace_name}).\n',
            f'not_holds_at(methane,0,{trace_name}).\n',
            f'not_holds_at(pump,0,{trace_name}).\n',
            '\n',
            f'holds_at(highwater,1,{trace_name}).\n',
            f'holds_at(methane,1,{trace_name}).\n',
            f'not_holds_at(pump,1,{trace_name}).\n',
            '\n'
        ]
        encoder: SpecEncoder = SpecEncoder(SpecGenerator())
        clingo_str: str = encoder.encode_ASP(spec_df, trace, set())
        clingo_str = clingo_str.replace('\n\n\n', '\n\n')

        self.assertEqual(expected_clingo_str, clingo_str)

    def test_create_mode_bias_aw(self):
        spec_df: pd.DataFrame = get_assumptions_and_guarantees_from(self.minepump_spec_file)
        violations: list[str] = [
            """\
    assumption(initial_assumption)
    assumption(assumption1_1)
    assumption(assumption2_1)
    guarantee(initial_guarantee)
    guarantee(guarantee1_1)
    guarantee(guarantee2_1)
    violation_holds(assumption2_1,1,trace_name_0)
    violation_holds(guarantee1_1,1,trace_name_0)\
    """
        ]
        encoder: SpecEncoder = SpecEncoder(SpecGenerator())
        mode_bias: str = encoder._create_mode_bias(spec_df, violations, Learning.ASSUMPTION_WEAKENING)

        expected_mode_bias: str = read_file(self.minepump_mode_bias_aw_file)
        self.assertEqual(expected_mode_bias, mode_bias)

    def test_create_mode_bias_gw(self):
        spec_df: pd.DataFrame = get_assumptions_and_guarantees_from(self.minepump_spec_1_aw_step)
        violations: list[str] = [
            """\
    assumption(initial_assumption)
    assumption(assumption1_1)
    assumption(assumption2_1)
    guarantee(initial_guarantee)
    guarantee(guarantee1_1)
    guarantee(guarantee2_1)
    violation_holds(guarantee1_1,1,trace_name_0)
    violation_holds(guarantee1_1,1,counter_strat_0)\
    """
        ]
        encoder: SpecEncoder = SpecEncoder(SpecGenerator())
        mode_bias: str = encoder._create_mode_bias(spec_df, violations, Learning.GUARANTEE_WEAKENING)

        expected_mode_bias: str = read_file(self.minepump_mode_bias_gw_file)
        self.assertEquals(expected_mode_bias, mode_bias)

    def test_integrate_learned_hypothesis(self):
        rule = 'antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(methane,V1,V2).'
        adaptation = extract_adaptation_from_rule(rule)
        expected_adaptation = AdaptationLearned(
            type="antecedent_exception",
            name_expression="assumption2_1",
            disjunction_index=0,
            atom_temporal_operators=[("current", "methane=true")]
        )

        self.assertEquals(expected_adaptation.type, adaptation.type)
        self.assertEquals(expected_adaptation.name_expression, adaptation.name_expression)
        self.assertEquals(expected_adaptation.disjunction_index, adaptation.disjunction_index)
        self.assertEquals(expected_adaptation.atom_temporal_operators, adaptation.atom_temporal_operators)

    def test_integrate_learned_hypothesis_2(self):
        rule = 'antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(methane,V1,V2); holds_at(highwater,V1,V2).'
        adaptation = extract_adaptation_from_rule(rule)
        expected_adaptation = AdaptationLearned(
            type="antecedent_exception",
            name_expression="assumption2_1",
            disjunction_index=0,
            atom_temporal_operators=[("current", "methane=true"), ("current", "highwater=true")]
        )

        self.assertEquals(expected_adaptation.type, adaptation.type)
        self.assertEquals(expected_adaptation.name_expression, adaptation.name_expression)
        self.assertEquals(expected_adaptation.disjunction_index, adaptation.disjunction_index)
        self.assertEquals(expected_adaptation.atom_temporal_operators, adaptation.atom_temporal_operators)

    def test_integrate_learned_hypothesis_3(self):
        rule = (
            'antecedent_exception(assumption2_1,0,V1,V2) :- '
            'timepoint_of_op(current,V1,V1,V2); '
            'holds_at(methane,V1,V2); '
            'not_holds_at(highwater,V1,V2);.'
            'timepoint_of_op(next,V1,V3,V2); '
            'holds_at(pump,V3,V2); '
        )
        adaptation = extract_adaptation_from_rule(rule)
        expected_adaptation = AdaptationLearned(
            type="antecedent_exception",
            name_expression="assumption2_1",
            disjunction_index=0,
            atom_temporal_operators=[("current", "methane=true"), ("current", "highwater=false"), ("next", "pump=true")]
        )

        self.assertEquals(expected_adaptation.type, adaptation.type)
        self.assertEquals(expected_adaptation.name_expression, adaptation.name_expression)
        self.assertEquals(expected_adaptation.disjunction_index, adaptation.disjunction_index)
        self.assertEquals(expected_adaptation.atom_temporal_operators, adaptation.atom_temporal_operators)
