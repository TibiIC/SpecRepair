from typing import Any, Tuple

from spec_repair.components.interfaces.idiscriminator import IDiscriminator
from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.helpers.counter_trace import CounterTrace
from spec_repair.helpers.spectra_specification import SpectraSpecification


class SpectraDiscriminator(IDiscriminator):
    strategies = ["assumption_weakening", "guarantee_weakening"]
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
        match data.learning_type:
            case Learning.ASSUMPTION_WEAKENING:
                return "assumption_weakening"
            case Learning.GUARANTEE_WEAKENING:
                return "guarantee_weakening"
            case _:
                raise ValueError(f"Unknown learning type: {data.learning_type}")
