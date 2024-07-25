from spec_repair.components.heuristic_managers.heuristic_manager import HeuristicManager


class NoFilterHeuristicManager(HeuristicManager):
    def select_counter_traces(self, cts):
        return cts

    def select_complete_counter_traces(self, ctss):
        return ctss

    def select_weakening_hypotheses(self, hypotheses):
        return hypotheses
