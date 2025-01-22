import copy
from unittest import TestCase

from spec_repair.wrappers.spec import Spec
from spec_repair.ltl_types import GR1FormulaType
from tests.test_common_utility_strings.specs import *


class TestSpec(TestCase):
    def test_eq_identical_strings(self):
        spec_1 = Spec(copy.deepcopy(spec_perf))
        spec_2 = Spec(copy.deepcopy(spec_perf))
        self.assertEqual(spec_1, spec_2)

    def test_eq_1(self):
        spec_1 = Spec(copy.deepcopy(spec_perf))
        spec_2 = Spec(copy.deepcopy(spec_fixed_perf))
        self.assertEqual(spec_1, spec_2)

    def test_neq_1(self):
        spec_1 = Spec(copy.deepcopy(spec_perf))
        spec_2 = Spec(copy.deepcopy(spec_fixed_imperf))
        self.assertNotEquals(spec_1, spec_2)

    def test_neq_2(self):
        spec_1 = Spec(copy.deepcopy(spec_fixed_imperf))
        spec_2 = Spec(copy.deepcopy(spec_fixed_perf))
        self.assertNotEquals(spec_1, spec_2)

    def test_swap_rule_1(self):
        spec = Spec(copy.deepcopy(spec_strong))
        new_spec = Spec(copy.deepcopy(spec_strong_asm_w))
        spec.swap_rule(
            name="assumption2_1",
            new_rule="G(highwater=false-> highwater=false|methane=false);",
        )
        self.assertEqual(spec, new_spec)

    def test_asm_eq_gar_weaker(self):
        spec_1 = Spec(copy.deepcopy(spec_perf))
        spec_2 = Spec(copy.deepcopy(spec_asm_eq_gar_weaker))
        self.assertTrue(spec_1.equivalent_to(spec_2, GR1FormulaType.ASM))
        self.assertTrue(spec_1.implies(spec_2, GR1FormulaType.GAR))

    def test_asm_stronger_gar_same(self):
        spec_1 = Spec(copy.deepcopy(spec_perf))
        spec_2 = Spec(copy.deepcopy(spec_asm_stronger_gar_eq))
        self.assertTrue(spec_1.implied_by(spec_2, GR1FormulaType.ASM))
        self.assertTrue(spec_1.equivalent_to(spec_2, GR1FormulaType.GAR))
