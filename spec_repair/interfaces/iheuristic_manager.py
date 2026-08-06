from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List, Any



class IHeuristicManager(ABC):
    def __init__(self):
        self._heuristics = defaultdict(bool)
        self._heuristics["ANTECEDENT_WEAKENING"] = True
        self._heuristics["CONSEQUENT_WEAKENING"] = True
        self._heuristics["INVARIANT_TO_RESPONSE_WEAKENING"] = True

        # Which formulas may be weakened is *not* configured here. It is a
        # property of the repair methodology, not a per-run heuristic, and this
        # manager is shared by every learner and reset between runs - so a flag
        # set for one learner cannot survive to mean anything different for
        # another. See NON_LEARNABLE_WHEN in new_spec_encoder.

    @abstractmethod
    def select_counter_traces(self, cts: List[Any]) -> List[Any]:
        pass

    @abstractmethod
    def select_alternative_learning_tasks(self, ctss: List[List[Any]]) -> List[List[Any]]:
        pass

    @abstractmethod
    def select_possible_learning_adaptations(self, adaptations: List[Any]) -> List[Any]:
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
