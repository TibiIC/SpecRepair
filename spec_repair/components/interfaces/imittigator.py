from abc import ABC, abstractmethod
from typing import List, Tuple, Any

from spec_repair.components.interfaces.ispecification import ISpecification


class IMittigator(ABC):
    @abstractmethod
    def prepare_alternative_learning_tasks(self, spec, data) -> List[Tuple[ISpecification, Any]]:
        pass

    def add_counter_example_to_data(self, data, counter_argument) -> List[Tuple[ISpecification, Any]]:
        pass
