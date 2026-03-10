from abc import ABC, abstractmethod

from spec_repair.components.interfaces.ispecification import ISpecification


class IOracle(ABC):
    @abstractmethod
    def is_valid_or_counter_arguments(self, new_spec: ISpecification, data):
        pass

    @staticmethod
    @abstractmethod
    def is_realisable(new_spec: ISpecification):
        pass
