from spec_repair.components.interfaces.ioracle import IOracle
from spec_repair.components.spec_oracle import SpecOracle


class NewSpecOracle(IOracle):
    def __init__(self):
        # Simple wrapper for the SpecOracle
        self._oracle = SpecOracle()

    def is_valid_or_counter_arguments(self, new_spec):
        return self._oracle.synthesise_and_check(new_spec.to_str().replace("\n\n","\n").split("\n"))