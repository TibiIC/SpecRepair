from typing import List

import spot

from spec_repair.components.interfaces.ioracle import IOracle
from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.helpers.formatters.spectra_formula_formatter import SpectraFormulaFormatter
from spec_repair.helpers.formatters.spot_formula_formatter import SpotFormulaFormatter
from spec_repair.helpers.formatters.spot_specification_formatter import SpotSpecificationFormatter
from spec_repair.helpers.gr1_formula import GR1Formula
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import GR1FormulaType, GR1TemporalType
from spec_repair.util.spot_ltl_conjoining_util import conjoin_and_simplify


class RepairBro:
    def __init__(self, original_spec, oracle: IOracle):
        if isinstance(original_spec, ISpecification):
            self._original_spec = original_spec
        elif isinstance(original_spec, str):
            self._original_spec = SpectraSpecification.from_file(original_spec)
        else:
            raise ValueError("Invalid original_spec type. Expected ISpecification or str.")
        self._oracle = oracle
        assert oracle.is_realisable(self._original_spec)

    def merge_two_solutions(self, spec1: ISpecification, spec2: ISpecification) -> List[ISpecification]:
        assert self._oracle.is_realisable(spec1) and self._oracle.is_realisable(spec2)
        assert self._original_spec.implies(spec1, GR1FormulaType.ASM) and self._original_spec.implies(spec2, GR1FormulaType.ASM)
        assert self._original_spec.implies(spec1, GR1FormulaType.GAR) and self._original_spec.implies(spec2, GR1FormulaType.GAR)

        if self._original_spec.equivalent_to(spec1, GR1FormulaType.GAR) and self._original_spec.equivalent_to(spec2, GR1FormulaType.GAR):
            print("Guarantees equivalent! There exists a single solution, where the assumptions are conjoined!")
            gar_only_spec = self._original_spec.extract_sub_specification(lambda x: (x['type'] == GR1FormulaType.GAR))
            asm_only_spec_1 = spec1.extract_sub_specification(lambda x: (x['type'] == GR1FormulaType.ASM))
            asm_only_spec_2 = spec2.extract_sub_specification(lambda x: (x['type'] == GR1FormulaType.ASM))
            conjoined_asms_spec = self._merge_two_assumption_sets(asm_only_spec_1, asm_only_spec_2)
            merged_spec = conjoined_asms_spec.join_with_spec(gar_only_spec)
            assert merged_spec.is_realisable()
            return [merged_spec]

    def _merge_two_assumption_sets(self, asm_only_spec_1: SpectraSpecification, asm_only_spec_2: SpectraSpecification):
        asm_only_spec = self._original_spec.extract_sub_specification(lambda x: (x['type'] == GR1FormulaType.ASM))
        og_spec_asm_only_df = asm_only_spec._formulas_df
        spec_1_asm_only_df = asm_only_spec_1._formulas_df
        spec_2_asm_only_df = asm_only_spec_2._formulas_df

        for index, row in og_spec_asm_only_df.iterrows():
            formula_name: str = row['name']
            formula_type_: GR1FormulaType = row['type']
            formula_when: GR1TemporalType = row['when']
            formula: GR1Formula = row['formula']
            formula_spot = formula.to_str(SpotFormulaFormatter())
            spot.are_equivalent(original, result)

        asms_1_spot = asm_only_spec_1.to_formatted_string(SpotSpecificationFormatter(GR1FormulaType.ASM))
        asms_2_spot = asm_only_spec_2.to_formatted_string(SpotSpecificationFormatter(GR1FormulaType.ASM))
        conjoined_asm_spot = conjoin_and_simplify(asms_1_spot, asms_2_spot)
        return SpectraSpecification.from_str(SpectraFormulaFormatter.format(conjoined_asm_spot))
