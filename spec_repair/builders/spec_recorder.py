from typing import Optional

from spec_repair.util.file_util import write_to_file
from spec_repair.wrappers.spec import Spec


class SpecRecorder:
    def __init__(self, debug_folder: Optional[str] = None):
        self.storage: dict[Spec, int] = dict()
        self.debug_folder = debug_folder

    def add(self, new_spec: Spec):
        for spec, index in self.storage.items():
            if spec == new_spec:
                return index
        index = len(self.storage)
        self.storage[new_spec] = index
        if self.debug_folder:
            write_to_file(f"{self.debug_folder}/spec_{index}.spectra", new_spec.get_spec())
        return index

    def get_id(self, new_spec: Spec):
        for spec, index in self.storage.values():
            if spec == new_spec:
                return index
        return -1

    def get_specs(self) -> list[str]:
        return [spec.get_spec() for spec in self.storage.keys()]
