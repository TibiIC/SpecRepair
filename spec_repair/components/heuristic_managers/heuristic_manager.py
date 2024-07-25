from abc import ABC, abstractmethod


class HeuristicManager(ABC):
    @abstractmethod
    def select_counter_traces(self, cts):
        pass

    @abstractmethod
    def select_complete_counter_traces(self, ctss):
        pass

    @abstractmethod
    def select_weakening_hypotheses(self, hypotheses):
        pass

    def reset(self):
        """
        A heuristic manager may keep track internally of the state of
        the learning, and make choices using historical knowledge.
        Resetting it at the start of a new learning process is expected
        to be necessary.
        """
        pass
