from typing import List

from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager


class NoEventuallyHypothesisHeuristicManager(NoFilterHeuristicManager):

    def __init__(self):
        super().__init__()
        self._heuristics["INVARIANT_TO_RESPONSE_WEAKENING"] = False

    def select_weakening_hypotheses(self, hypotheses: List[List[str]]) -> List[List[str]]:
        hypotheses = super().select_weakening_hypotheses(hypotheses)
        return [h for h in hypotheses if 'ev_temp_op' not in "".join(h)]
