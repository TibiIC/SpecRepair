from abc import ABC, abstractmethod
from typing import List

from spec_repair.helpers.counter_trace import CounterTrace


class HeuristicManager(ABC):
    @abstractmethod
    def select_counter_traces(self, cts: List[CounterTrace]) -> List[CounterTrace]:
        pass

    @abstractmethod
    def select_complete_counter_traces(self, ctss: List[List[CounterTrace]]) -> List[List[CounterTrace]]:
        pass

    @abstractmethod
    def select_weakening_hypotheses(self, hypotheses: List[List[str]]) -> List[List[str]]:
        pass

    def reset(self):
        """
        A heuristic manager may keep track internally of the state of
        the learning, and make choices using historical knowledge.
        Resetting it at the start of a new learning process is expected
        to be necessary.
        """
        pass
