from typing import List

from spec_repair.components.interfaces.ioracle import IOracle
from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.helpers.spectra_specification import SpectraSpecification


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

