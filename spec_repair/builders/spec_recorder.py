from spec_repair.wrappers.spec import Spec


class SpecRecorder:
    def __init__(self):
        self.storage: dict[Spec, int] = dict()

    def add(self, new_spec: Spec):
        for spec, index in self.storage.items():
            if spec == new_spec:
                return index
        index = len(self.storage)
        self.storage[new_spec] = index
        return index

    def get_id(self, new_spec: Spec):
        for spec, index in self.storage.values():
            if spec == new_spec:
                return index
        return -1

    def get_specs(self) -> list[str]:
        return [spec.get_spec() for spec in self.storage.keys()]
