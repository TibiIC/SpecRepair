from abc import abstractmethod
from typing import Tuple, Any, Optional

from spec_repair.components.interfaces.ispecification import ISpecification


class IOrchestrationManager:
    @abstractmethod
    def initialise_learning_tasks(self, spec: ISpecification, data: Any):
        pass

    @abstractmethod
    def enqueue_new_tasks(self, spec: ISpecification, data: Any, prev: Optional[Tuple[ISpecification, Any]] = None, failed_spec: Optional[ISpecification] = None):
        pass

    @abstractmethod
    def _get_task_id(self, spec: ISpecification, data: Any) -> int:
        pass

    @abstractmethod
    def connect_leaf_node(self, spec: ISpecification, unique_id: int, prev: Tuple[ISpecification, Any]):
        pass

    @abstractmethod
    def has_next(self) -> bool:
        pass

    @abstractmethod
    def get_next(self) -> Tuple[ISpecification, Any]:
        pass
