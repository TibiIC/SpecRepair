from unittest import TestCase

from spec_repair.helpers.adaptation_learned import AdaptationLearned


class TestAdaptationLearned(TestCase):
    def test_integrate_learned_hypothesis(self):
        rule = 'antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(methane,V1,V2).'
        adaptation = AdaptationLearned.from_str(rule)
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
        adaptation = AdaptationLearned.from_str(rule)
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
        adaptation = AdaptationLearned.from_str(rule)
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
