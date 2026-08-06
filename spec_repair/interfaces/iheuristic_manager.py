from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List, Any



class IHeuristicManager(ABC):
    def __init__(self):
        self._heuristics = defaultdict(bool)
        self._heuristics["ANTECEDENT_WEAKENING"] = True
        self._heuristics["CONSEQUENT_WEAKENING"] = True
        self._heuristics["INVARIANT_TO_RESPONSE_WEAKENING"] = True

        # Which formulas the learner may weaken at all, one toggle per
        # (assumption|guarantee) x (initial|invariant|justice) pair.
        #
        # These gate whether a formula is written into the *learning task*. A
        # disabled pair gets no `#constant(expression_v, ...)`, so no solver can
        # attach an exception to it - which is stronger than forbidding it in
        # the #bias, since FastLAS ignores hard #bias constraints unless they
        # are translated. The formulas stay in encode_ASP either way, where they
        # are still needed to decide what the trace violates and whether a
        # repair is correct.
        #
        # The two INITIAL toggles are off by default. Weakening an initial
        # assumption or guarantee changes which states the system may start in,
        # which changes the realisability question rather than answering it, and
        # an exception on an initial assumption drags system variables into it,
        # which Spectra's CLI rejects outright. Turn them on for a repair
        # methodology that genuinely intends to move the initial conditions.
        self._heuristics["LEARN_ASSUMPTION_INITIAL"] = False
        self._heuristics["LEARN_ASSUMPTION_INVARIANT"] = True
        self._heuristics["LEARN_ASSUMPTION_JUSTICE"] = True
        self._heuristics["LEARN_GUARANTEE_INITIAL"] = False
        self._heuristics["LEARN_GUARANTEE_INVARIANT"] = True
        self._heuristics["LEARN_GUARANTEE_JUSTICE"] = True

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
