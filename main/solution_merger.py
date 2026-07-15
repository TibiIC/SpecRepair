from typing import List

import spot

from spec_repair.interfaces.ioracle import IOracle
from spec_repair.interfaces.ispecification import ISpecification
from spec_repair.helpers.formatters.spectra_formula_formatter import SpectraFormulaFormatter
from spec_repair.helpers.formatters.spot_formula_formatter import SpotFormulaFormatter
from spec_repair.helpers.formatters.spot_specification_formatter import SpotSpecificationFormatter
from spec_repair.helpers.gr1_formula import GR1Formula
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import GR1FormulaType, GR1TemporalType
from spec_repair.new_research import get_all_trivial_solutions_guarantee_only
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
        if not self._oracle.is_realisable(spec1) or not self._oracle.is_realisable(spec2):
            print("WARNING: At least one of the two solutions is unrealizable.")
            assert self._oracle.is_realisable(spec1) and self._oracle.is_realisable(spec2)
        assert self._original_spec.implies(spec1, GR1FormulaType.ASM) and self._original_spec.implies(spec2, GR1FormulaType.ASM)
        assert self._original_spec.implies(spec1, GR1FormulaType.GAR) and self._original_spec.implies(spec2, GR1FormulaType.GAR)


        merged_spec = spec1.merge(spec2)
        if self._oracle.is_realisable(merged_spec):
            return [merged_spec]
        else:
            new_merged_specs = get_all_trivial_solutions_guarantee_only(merged_spec)
            for new_merged_spec in new_merged_specs:
                if not self._oracle.is_realisable(new_merged_spec):
                    print("WARNING: Merged solution is unrealizable.")
                    print(merged_spec)
            return new_merged_specs

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
