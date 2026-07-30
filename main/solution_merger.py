from typing import List

import spot

from spec_repair.interfaces.ioracle import IOracle
from spec_repair.interfaces.ispecification import ISpecification
from spec_repair.helpers.formatters.spectra_formula_formatter import SpectraFormulaFormatter
from spec_repair.helpers.formatters.spot_formula_formatter import SpotFormulaFormatter
from spec_repair.helpers.formatters.spot_specification_formatter import SpotSpecificationFormatter
from spec_repair.model.gr1_formula import GR1Formula
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import GR1FormulaType, GR1TemporalType
from spec_repair.diagnosis.solution_merging import merge_solutions
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
        """
        Merge two repaired solutions against this RepairBro's original spec.

        Delegates to spec_repair.diagnosis.solution_merging, the single
        implementation shared with scripts/merge_specs.py. `strict=True`
        preserves this class's original behaviour of treating "every solution is
        a weakening of the original" as an invariant to assert, rather than the
        warning the directory-merging path has always used.
        """
        return merge_solutions(
            [spec1, spec2],
            og_spec=self._original_spec,
            oracle=self._oracle,
            strict=True,
        )

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
