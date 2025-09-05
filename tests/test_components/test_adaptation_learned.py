from unittest import TestCase

from spec_repair.helpers.adaptation_learned import Adaptation


class TestAdaptationLearned(TestCase):
    def test_integrate_learned_hypothesis(self):
        rule = 'antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(methane,V1,V2).'
        adaptation = Adaptation.from_str(rule)
        expected_adaptation = Adaptation(
            type="antecedent_exception",
            formula_name="assumption2_1",
            disjunction_index=0,
            atom_temporal_operators=[("current", "methane=true")]
        )

        self.assertEquals(expected_adaptation.type, adaptation.type)
        self.assertEquals(expected_adaptation.formula_name, adaptation.formula_name)
        self.assertEquals(expected_adaptation.disjunction_index, adaptation.disjunction_index)
        self.assertEquals(expected_adaptation.atom_temporal_operators, adaptation.atom_temporal_operators)

    def test_integrate_learned_hypothesis_2(self):
        rule = 'antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(methane,V1,V2); holds_at(highwater,V1,V2).'
        adaptation = Adaptation.from_str(rule)
        expected_adaptation = Adaptation(
            type="antecedent_exception",
            formula_name="assumption2_1",
            disjunction_index=0,
            atom_temporal_operators=[("current", "methane=true"), ("current", "highwater=true")]
        )

        self.assertEquals(expected_adaptation.type, adaptation.type)
        self.assertEquals(expected_adaptation.formula_name, adaptation.formula_name)
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
        adaptation = Adaptation.from_str(rule)
        expected_adaptation = Adaptation(
            type="antecedent_exception",
            formula_name="assumption2_1",
            disjunction_index=0,
            atom_temporal_operators=[("current", "methane=true"), ("current", "highwater=false"), ("next", "pump=true")]
        )

        self.assertEquals(expected_adaptation.type, adaptation.type)
        self.assertEquals(expected_adaptation.formula_name, adaptation.formula_name)
        self.assertEquals(expected_adaptation.disjunction_index, adaptation.disjunction_index)
        self.assertEquals(expected_adaptation.atom_temporal_operators, adaptation.atom_temporal_operators)

    def test_guarantee_weakening_learned(self):
        rule = 'consequent_exception(guarantee1_1,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(highwater,V1,V2).'
        adaptation = Adaptation.from_str(rule)
        expected_adaptation = Adaptation(
            type="consequent_exception",
            formula_name="guarantee1_1",
            disjunction_index=None,
            atom_temporal_operators=[("current", "highwater=true")]
        )

        self.assertEquals(expected_adaptation.type, adaptation.type)
        self.assertEquals(expected_adaptation.formula_name, adaptation.formula_name)
        self.assertEquals(expected_adaptation.disjunction_index, adaptation.disjunction_index)
        self.assertEquals(expected_adaptation.atom_temporal_operators, adaptation.atom_temporal_operators)

    def test_eventualisation_weakening_learned(self):
        rule = 'ev_temp_op(assumption2_1).'
        adaptation = Adaptation.from_str(rule)
        expected_adaptation = Adaptation(
            type="ev_temp_op",
            formula_name="assumption2_1",
            disjunction_index=None,
            atom_temporal_operators=[]
        )

        self.assertEquals(expected_adaptation.type, adaptation.type)
        self.assertEquals(expected_adaptation.formula_name, adaptation.formula_name)
        self.assertEquals(expected_adaptation.disjunction_index, adaptation.disjunction_index)
        self.assertEquals(expected_adaptation.atom_temporal_operators, adaptation.atom_temporal_operators)

    def test_integrate_learned_hypothesis_enum(self):
        rule = 'antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(methane,high,V1,V2).'
        adaptation = Adaptation.from_str(rule)
        expected_adaptation = Adaptation(
            type="antecedent_exception",
            formula_name="assumption2_1",
            disjunction_index=0,
            atom_temporal_operators=[("current", "methane=high")]
        )

        self.assertEquals(expected_adaptation.type, adaptation.type)
        self.assertEquals(expected_adaptation.formula_name, adaptation.formula_name)
        self.assertEquals(expected_adaptation.disjunction_index, adaptation.disjunction_index)
        self.assertEquals(expected_adaptation.atom_temporal_operators, adaptation.atom_temporal_operators)

    def test_integrate_learned_hypothesis_enum_2(self):
        rule = 'antecedent_exception(assumption2_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(methane,low,V1,V2); holds_at(water,high,V1,V2).'
        adaptation = Adaptation.from_str(rule)
        expected_adaptation = Adaptation(
            type="antecedent_exception",
            formula_name="assumption2_1",
            disjunction_index=0,
            atom_temporal_operators=[("current", "methane=low"), ("current", "water=high")]
        )

        self.assertEquals(expected_adaptation.type, adaptation.type)
        self.assertEquals(expected_adaptation.formula_name, adaptation.formula_name)
        self.assertEquals(expected_adaptation.disjunction_index, adaptation.disjunction_index)
        self.assertEquals(expected_adaptation.atom_temporal_operators, adaptation.atom_temporal_operators)

    def test_integrate_learned_hypothesis_enum_3(self):
        rule = (
            'antecedent_exception(assumption2_1,0,V1,V2) :- '
            'timepoint_of_op(current,V1,V1,V2); '
            'holds_at(methane,high,V1,V2); '
            'holds_at(water,low,V1,V2);.'
            'timepoint_of_op(next,V1,V3,V2); '
            'holds_at(pump,true,V3,V2); '
        )
        adaptation = Adaptation.from_str(rule)
        expected_adaptation = Adaptation(
            type="antecedent_exception",
            formula_name="assumption2_1",
            disjunction_index=0,
            atom_temporal_operators=[("current", "methane=high"), ("current", "water=low"), ("next", "pump=true")]
        )

        self.assertEquals(expected_adaptation.type, adaptation.type)
        self.assertEquals(expected_adaptation.formula_name, adaptation.formula_name)
        self.assertEquals(expected_adaptation.disjunction_index, adaptation.disjunction_index)
        self.assertEquals(expected_adaptation.atom_temporal_operators, adaptation.atom_temporal_operators)

    def test_guarantee_weakening_learned_enum(self):
        rule = 'consequent_exception(guarantee1_1,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(water,high,V1,V2).'
        adaptation = Adaptation.from_str(rule)
        expected_adaptation = Adaptation(
            type="consequent_exception",
            formula_name="guarantee1_1",
            disjunction_index=None,
            atom_temporal_operators=[("current", "water=high")]
        )

        self.assertEquals(expected_adaptation.type, adaptation.type)
        self.assertEquals(expected_adaptation.formula_name, adaptation.formula_name)
        self.assertEquals(expected_adaptation.disjunction_index, adaptation.disjunction_index)
        self.assertEquals(expected_adaptation.atom_temporal_operators, adaptation.atom_temporal_operators)
