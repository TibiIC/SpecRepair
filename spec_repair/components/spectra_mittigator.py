from typing import List, Tuple, Any

from spec_repair.components.interfaces.imittigator import IMittigator
from spec_repair.components.interfaces.ispecification import ISpecification


class SpectraMittigator(IMittigator):
    def prepare_alternative_learning_tasks(self, spec, data) -> List[Tuple[ISpecification, Any]]:
        pass