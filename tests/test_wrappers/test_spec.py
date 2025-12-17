import copy

from spec_repair.util.file_util import read_file
from spec_repair.wrappers.spec import Spec, extract_GR1_expressions_of_type_spot
from spec_repair.ltl_types import GR1FormulaType
from tests.base_test_case import BaseTestCase
from tests.test_common_utility_strings.specs import *


class TestSpec(BaseTestCase):
    def test_genbuf_conversion_ideal_normalised(self):
        spec_txt: str = read_file("../input-files/case-studies/spectra/genbuf/ideal_normalised.spectra")
        spec: Spec = Spec(spec_txt)
        print(spec.to_spot())
        self.assertTrue(False)

    def test_genbuf_conversion_strong(self):
        spec_txt: str = read_file("../input-files/case-studies/spectra/genbuf/strong.spectra")
        spec: Spec = Spec(spec_txt)
        print(spec.to_spot())
        self.assertTrue(False)

    def test_genbuf_compare(self):
        spec_txt: str = read_file("../input-files/case-studies/spectra/genbuf/ideal_normalised.spectra")
        spec_ideal: Spec = Spec(spec_txt)
        spec_txt = read_file("../input-files/case-studies/spectra/genbuf/strong.spectra")
        spec_strong: Spec = Spec(spec_txt)
        self.assertTrue(spec_ideal.equivalent_to(spec_strong, GR1FormulaType.GAR))
        self.assertTrue(spec_ideal.implied_by(spec_strong, GR1FormulaType.ASM))

    def test_minepump_compare(self):
        spec_txt: str = read_file("../input-files/case-studies/spectra/minepump/ideal.spectra")
        spec_ideal: Spec = Spec(spec_txt)
        spec_txt = read_file("../input-files/case-studies/spectra/minepump/strong.spectra")
        spec_strong: Spec = Spec(spec_txt)
        self.assertTrue(spec_ideal.implied_by(spec_strong, GR1FormulaType.GAR))
        self.assertTrue(spec_ideal.implied_by(spec_strong, GR1FormulaType.ASM))

    def test_minepump_is_trivial(self):
        spec_txt: str = read_file("../input-files/case-studies/spectra/minepump/ideal.spectra")
        spec_ideal: Spec = Spec(spec_txt)
        self.assertFalse(spec_ideal.is_trivial_true(GR1FormulaType.ASM))
        self.assertFalse(spec_ideal.is_trivial_false(GR1FormulaType.ASM))

        spec_txt = read_file("../input-files/case-studies/spectra/minepump/strong.spectra")
        spec_strong: Spec = Spec(spec_txt)
        self.assertFalse(spec_strong.is_trivial_true(GR1FormulaType.ASM))
        self.assertFalse(spec_strong.is_trivial_false(GR1FormulaType.ASM))

    def test_minepump_is_trivial_no_initial(self):
        spec_txt: str = read_file("../input-files/case-studies/spectra/minepump/ideal.spectra")
        spec_ideal: Spec = Spec(spec_txt)
        self.assertFalse(spec_ideal.is_trivial_true(GR1FormulaType.ASM, ignore_initial=True))
        self.assertFalse(spec_ideal.is_trivial_false(GR1FormulaType.ASM, ignore_initial=True))

        spec_txt = read_file("../input-files/case-studies/spectra/minepump/strong.spectra")
        spec_strong: Spec = Spec(spec_txt)
        self.assertFalse(spec_strong.is_trivial_true(GR1FormulaType.ASM, ignore_initial=True))
        self.assertFalse(spec_strong.is_trivial_false(GR1FormulaType.ASM, ignore_initial=True))

    def test_extract_gr1_expressions_of_type_spot(self):
        spec_txt: str = read_file("../input-files/case-studies/spectra/minepump/ideal.spectra")
        spec_ideal_spot: str = extract_GR1_expressions_of_type_spot(str(GR1FormulaType.ASM), spec_txt.split("\n"))
        self.assertEqual("!highwater&!methane&G(pump&X(pump)->XX(!highwater))", spec_ideal_spot)

        spec_txt = read_file("../input-files/case-studies/spectra/minepump/strong.spectra")
        spec_strong_spot: str = extract_GR1_expressions_of_type_spot(str(GR1FormulaType.ASM), spec_txt.split("\n"))
        self.assertEqual("!highwater&!methane&G(pump&X(pump)->XX(!highwater))&G(!highwater|!methane)", spec_strong_spot)

        spec_txt: str = read_file("../input-files/case-studies/spectra/minepump/ideal.spectra")
        spec_ideal_spot: str = extract_GR1_expressions_of_type_spot(str(GR1FormulaType.GAR), spec_txt.split("\n"))
        self.assertEqual("!pump&G(highwater&!methane->X(pump))&G(methane->X(!pump))", spec_ideal_spot)

        spec_txt = read_file("../input-files/case-studies/spectra/minepump/strong.spectra")
        spec_strong_spot: str = extract_GR1_expressions_of_type_spot(str(GR1FormulaType.GAR), spec_txt.split("\n"))
        self.assertEqual("!pump&G(highwater->X(pump))&G(methane->X(!pump))", spec_strong_spot)

    def test_extract_gr1_expressions_of_type_spot_no_initial(self):
        spec_txt: str = read_file("../input-files/case-studies/spectra/minepump/ideal.spectra")
        spec_ideal_spot: str = extract_GR1_expressions_of_type_spot(str(GR1FormulaType.ASM), spec_txt.split("\n"), True)
        self.assertEqual("G(pump&X(pump)->XX(!highwater))", spec_ideal_spot)

        spec_txt = read_file("../input-files/case-studies/spectra/minepump/strong.spectra")
        spec_strong_spot: str = extract_GR1_expressions_of_type_spot(str(GR1FormulaType.ASM), spec_txt.split("\n"), True)
        self.assertEqual("G(pump&X(pump)->XX(!highwater))&G(!highwater|!methane)", spec_strong_spot)

        spec_txt: str = read_file("../input-files/case-studies/spectra/minepump/ideal.spectra")
        spec_ideal_spot: str = extract_GR1_expressions_of_type_spot(str(GR1FormulaType.GAR), spec_txt.split("\n"), True)
        self.assertEqual("G(highwater&!methane->X(pump))&G(methane->X(!pump))", spec_ideal_spot)

        spec_txt = read_file("../input-files/case-studies/spectra/minepump/strong.spectra")
        spec_strong_spot: str = extract_GR1_expressions_of_type_spot(str(GR1FormulaType.GAR), spec_txt.split("\n"), True)
        self.assertEqual("G(highwater->X(pump))&G(methane->X(!pump))", spec_strong_spot)

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
