from abc import ABC, abstractmethod
from typing import Any

from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.components.repair_data import RepairData


class IDiscriminator(ABC):
    @abstractmethod
    def get_learning_strategy(
            self,
            spec: ISpecification,
            data: RepairData
    ) -> str:
        """
        Given a specification and data, return the learning strategy.
        :param spec: The specification.
        :param data: The data to learn from.
        :return: The learning strategy.
        """
        pass
