from copy import deepcopy
from typing import List, Tuple, Callable, Dict

from spec_repair.interfaces.imitigator import IMitigator
from spec_repair.interfaces.ispecification import ISpecification
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.model.counter_trace import CounterTrace
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.model.spectra_specification import SpectraSpecification


class LearningTypeSpecMitigator(IMitigator):
    """
    During learning, if no solution given, this mitigator will select one of the
    strategies it has been instantiated with based on the learning_type of the learning task.
    e.g. learning_type==Learning.ASSUMPTION_WEAKENING -> move_to_guarantee_weakening
    """
    def __init__(self, learning_strategies: Dict[Learning, Callable[[ISpecification, RepairData], List[Tuple[ISpecification, RepairData]]]]):
        self._hm = NoFilterHeuristicManager()
        self._mitigation_strategies = learning_strategies

    def prepare_alternative_learning_tasks(
            self,
            spec: SpectraSpecification,
            data: RepairData
    ) -> List[Tuple[ISpecification, RepairData]]:
        # TODO: find way to continue from "Weakening failed: No guarantee weakening produces realizable spec (las file UNSAT)"
        # TODO: because atm, it loops infinitely on the same task
        return self._hm.select_alternative_learning_tasks(self._mitigation_strategies[data.learning_type](spec, data))


    def prepare_learning_task(
            self,
            spec: SpectraSpecification,
            data: RepairData,
            learned_spec: SpectraSpecification,
            counter_argument
    ) -> Tuple[ISpecification, RepairData]:
        new_data = deepcopy(data)
        new_data.counter_traces.append(counter_argument)
        new_data.spec_history.append(deepcopy(learned_spec))
        if data.learning_type == Learning.ASSUMPTION_WEAKENING:
            return spec, new_data
        else:
            return learned_spec, new_data
