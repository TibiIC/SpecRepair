from typing import List, Any

from spec_repair.interfaces.iheuristic_manager import IHeuristicManager


class NoFilterHeuristicManager(IHeuristicManager):
    def __init__(self):
        super().__init__()

    def select_counter_traces(self, cts: List[Any]) -> List[Any]:
        return cts

    def select_alternative_learning_tasks(self, ctss: List[List[Any]]) -> List[List[Any]]:
        return ctss

    def select_possible_learning_adaptations(self, adaptations: List[List[str]]) -> List[List[str]]:
        return adaptations
