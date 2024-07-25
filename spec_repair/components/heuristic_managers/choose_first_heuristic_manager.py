from spec_repair.components.heuristic_managers.heuristic_manager import HeuristicManager
from spec_repair.heuristics import first_choice, choose_one_with_heuristic


class ChooseFirstHeuristicManager(HeuristicManager):
    def select_counter_traces(self, cts):
        return [choose_one_with_heuristic(cts, first_choice)]

    def select_complete_counter_traces(self, ctss):
        return [choose_one_with_heuristic(ctss, first_choice)]

    def select_weakening_hypotheses(self, hypotheses):
        return [choose_one_with_heuristic(hypotheses, first_choice)]
