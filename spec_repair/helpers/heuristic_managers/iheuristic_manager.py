from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List

from spec_repair.helpers.counter_trace import CounterTrace


class IHeuristicManager(ABC):
    def __init__(self):
        self._heuristics = defaultdict(bool)
        self._heuristics["ANTECEDENT_WEAKENING"] = True
        self._heuristics["CONSEQUENT_WEAKENING"] = True
        self._heuristics["INVARIANT_TO_RESPONSE_WEAKENING"] = True

    @abstractmethod
    def select_counter_traces(self, cts: List[CounterTrace]) -> List[CounterTrace]:
        pass

    @abstractmethod
    def select_complete_counter_traces(self, ctss: List[List[CounterTrace]]) -> List[List[CounterTrace]]:
        pass

    @abstractmethod
    def select_weakening_hypotheses(self, hypotheses: List[List[str]]) -> List[List[str]]:
        pass

    def is_enabled(self, param):
        return self._heuristics[param]

    def set_enabled(self, param):
        self._heuristics[param] = True

    def set_disabled(self, param):
        self._heuristics[param] = False

    def reset(self):
        """
        A heuristic manager may keep track internally of the state of
        the learning, and make choices using historical knowledge.
        Resetting it at the start of a new learning process is expected
        to be necessary.
        """
        pass
