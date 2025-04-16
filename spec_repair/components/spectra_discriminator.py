from typing import Any

from spec_repair.components.interfaces.idiscriminator import IDiscriminator
from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.enums import Learning


class SpectraDiscriminator(IDiscriminator):
    strategies = ["assumption_weakening", "guarantee_weakening"]
    def get_learning_strategy(self, spec: ISpecification, data: Any) -> str:
        """
        Given a specification and data, return the learning strategy.
        :param spec: The specification.
        :param data: The data to learn from.
        :return: The learning strategy.
        """
        trace, cts, learning_type = data
        match learning_type:
            case Learning.ASSUMPTION_WEAKENING:
                return "assumption_weakening"
            case Learning.GUARANTEE_WEAKENING:
                return "guarantee_weakening"
            case _:
                raise ValueError(f"Unknown learning type: {learning_type}")
