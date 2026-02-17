from abc import ABC, abstractmethod
from typing import List, Tuple, Any

from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.components.repair_data import RepairData


class IMitigator(ABC):
    @abstractmethod
    def prepare_alternative_learning_tasks(self, spec: ISpecification, data: RepairData) -> List[Tuple[ISpecification, RepairData]]:
        pass

    @abstractmethod
    def prepare_learning_task(self, spec: ISpecification, data: RepairData, learned_spec, counter_argument) -> Tuple[ISpecification, RepairData]:
        pass
