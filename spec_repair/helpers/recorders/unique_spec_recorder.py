from typing import Optional

from spec_repair.helpers.recorders.unique_recorder import UniqueRecorder
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import write_to_file

class UniqueSpecRecorder(UniqueRecorder[SpectraSpecification]):
    def __init__(self, sem_equivalence=True, debug_folder: Optional[str] = None):
        super().__init__()
        self.debug_folder = debug_folder
        self._semantic_equivalence = sem_equivalence
        if self._semantic_equivalence:
            self._specs: list[SpectraSpecification] = []

    def add(self, new_spec: SpectraSpecification):
        if not self._semantic_equivalence:
            index = super().add(new_spec)
        else:
            for index, spec in enumerate(self._specs):
                if spec == new_spec:
                    return index
            index = len(self._specs)
            self._specs.append(new_spec)
        if self.debug_folder:
            write_to_file(f"{self.debug_folder}/spec_{index}.spectra", new_spec.to_str())
        return index

    def get_specs(self) -> list[str]:
        if not self._semantic_equivalence:
            return [spec.to_str() for spec in self._value_to_id.keys()]
        else:
            return [spec.to_str() for spec in self._specs]
