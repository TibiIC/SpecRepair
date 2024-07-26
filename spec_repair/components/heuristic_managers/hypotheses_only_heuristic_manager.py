from typing import List

from spec_repair.components.counter_trace import CounterTrace
from spec_repair.components.heuristic_managers.heuristic_manager import HeuristicManager
from spec_repair.heuristics import first_choice, choose_one_with_heuristic


class HypothesesOnlyHeuristicManager(HeuristicManager):
    def select_counter_traces(self, cts: List[CounterTrace]) -> List[CounterTrace]:
        return [choose_one_with_heuristic(cts, first_choice)]

    def select_complete_counter_traces(self, ctss: List[List[CounterTrace]]) -> List[List[CounterTrace]]:
        return [choose_one_with_heuristic(ctss, first_choice)]

    def select_weakening_hypotheses(self, hypotheses: List[List[str]]) -> List[List[str]]:
        return hypotheses
