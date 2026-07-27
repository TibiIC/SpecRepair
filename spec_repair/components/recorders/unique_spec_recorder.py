from typing import List, Optional

from spec_repair.components.recorders.unique_recorder import UniqueRecorder
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import write_to_file


class UniqueSpecRecorder(UniqueRecorder[SpectraSpecification]):
    """
    Records specifications, deduplicating them either semantically or
    syntactically.

    The two modes differ in *which* comparison decides that two specs are the
    same, and both ultimately bottom out in SpectraSpecification's dunders:

    - `sem_equivalence=True` scans a list and compares with `__eq__`, which is
      spot-backed logical equivalence over the assumptions and the guarantees.
      Two specs written completely differently collapse to one entry.
    - `sem_equivalence=False` uses UniqueRecorder's set/dict, so `__hash__`
      decides the bucket first and `__eq__` only ever runs within a bucket.
      `__hash__` is purely syntactic (module name plus the formula rows), so
      logically-equivalent-but-differently-written specs hash differently, never
      get compared, and stay separate entries - i.e. syntactic dedup.

    Pair the mode with the orchestration manager: a syntactic search wants
    `sem_equivalence=False`, otherwise the recorder collapses results the search
    deliberately kept apart.
    """

    def __init__(self, sem_equivalence=True, debug_folder: Optional[str] = None):
        super().__init__()
        self.debug_folder = debug_folder
        self._semantic_equivalence = sem_equivalence
        # Always present, so the semantic-mode accessors below never depend on
        # whether __init__ happened to create it.
        self._specs: List[SpectraSpecification] = []

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

    # Semantic mode stores specs in `self._specs` and never touches
    # UniqueRecorder's `_set`/`_value_to_id`, so every inherited read method has
    # to be redirected. Without these overrides they all reported on an empty
    # backing store: get_all_values() returned [], __len__ returned 0,
    # __contains__ returned False and get_id() returned None, no matter how many
    # specs had been recorded - silently dropping every result for callers that
    # read back through get_all_values() rather than get_specs().

    def get_all_values(self) -> List[SpectraSpecification]:
        if not self._semantic_equivalence:
            # Deliberately the dict's keys rather than UniqueRecorder's
            # `list(self._set)`: dict preserves insertion order, so results come
            # back in the order they were recorded instead of set-iteration
            # order, which varies run to run.
            return list(self._value_to_id.keys())
        return list(self._specs)

    def get_id(self, value: SpectraSpecification) -> Optional[int]:
        if not self._semantic_equivalence:
            return super().get_id(value)
        for index, spec in enumerate(self._specs):
            if spec == value:
                return index
        return None

    def get_element_by_id(self, id_: int) -> Optional[SpectraSpecification]:
        if not self._semantic_equivalence:
            return super().get_element_by_id(id_)
        if 0 <= id_ < len(self._specs):
            return self._specs[id_]
        return None

    def __contains__(self, element: SpectraSpecification) -> bool:
        if not self._semantic_equivalence:
            return super().__contains__(element)
        return self.get_id(element) is not None

    def __len__(self):
        if not self._semantic_equivalence:
            return super().__len__()
        return len(self._specs)

    def get_specs(self) -> list[str]:
        return [spec.to_str() for spec in self.get_all_values()]
