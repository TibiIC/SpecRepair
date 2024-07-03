from collections import deque
from copy import copy
from typing import Optional, Deque, Set

from spec_repair.builders.spec_recorder import SpecRecorder
from spec_repair.components.counter_trace import CounterTrace
from spec_repair.components.spec_learner import SpecLearner
from spec_repair.components.spec_oracle import SpecOracle
from spec_repair.enums import Learning
from spec_repair.exceptions import NoWeakeningException
from spec_repair.heuristics import first_choice
from spec_repair.special_types import StopHeuristicType
from spec_repair.wrappers.spec import Spec


class RepairNode:
    def __init__(
            self,
            spec: list[str],
            ct_list: Optional[any],
            learning_hypothesis: Optional[list[str]],
            learning_type: Learning
    ):
        self.spec = spec
        self.ct_list = ct_list
        self.learning_hypothesis = learning_hypothesis
        self.learning_type = learning_type
        self.weak_spec_history = []

    def __eq__(self, other):
        return (self.spec == other.spec and
                self.ct_list == other.ct_list and
                self.learning_hypothesis == other.learning_hypothesis and
                self.learning_type == other.learning_type)

    def __hash__(self):
        hashable_learning_hypothesis = tuple(self.learning_hypothesis) if self.learning_hypothesis is not None else None
        return hash((tuple(self.spec), tuple(self.ct_list), hashable_learning_hypothesis, self.learning_type))


class BacktrackingRepairOrchestrator:
    def __init__(self, learner: SpecLearner, oracle: SpecOracle):
        self._learner = learner
        self._oracle = oracle
        self._ct_cnt = 0

    # Reimplementation of the highest level abstraction code
    def repair_spec_bfs(
            self,
            spec: list[str],
            trace: list[str],
            stop_heuristic: StopHeuristicType = lambda a, g: True
    ) -> SpecRecorder:
        self._ct_cnt = 0
        stack: Deque[RepairNode] = deque()
        visited_nodes: Set[RepairNode] = set()
        unique_specs = SpecRecorder()
        # TODO: what if the first spec cannot be weakened by assumption weakening?
        hypotheses = self._learner.find_weakening_hypotheses(spec, trace, [], Learning.ASSUMPTION_WEAKENING)
        for hypothesis in hypotheses:
            node = RepairNode(spec, [], hypothesis, Learning.ASSUMPTION_WEAKENING)
            if node not in visited_nodes:
                stack.append(node)
                visited_nodes.add(node)

        while stack:
            node = stack.pop()
            try:
                new_spec = self._learner.integrate_learning_hypothesis(node.spec, node.learning_hypothesis, node.learning_type)
                cs = self._oracle.synthesise_and_check(new_spec)
                if not cs:
                    unique_specs.add(Spec(''.join(new_spec)))
                else:
                    ct_list = copy(node.ct_list)
                    ct_list.append(self.ct_from_cs(cs))
                    hypotheses = self._learner.find_weakening_hypotheses(spec, trace, ct_list, node.learning_type)
                    for hypothesis in hypotheses:
                        match node.learning_type:
                            case Learning.ASSUMPTION_WEAKENING:
                                node = RepairNode(copy(spec), copy(ct_list), hypothesis, node.learning_type)
                            case Learning.GUARANTEE_WEAKENING:
                                node = RepairNode(copy(new_spec), copy(ct_list), hypothesis, node.learning_type)
                            case _:
                                raise ValueError("Invalid learning type")
                        node.weak_spec_history.append(new_spec)
                        if node not in visited_nodes:
                            stack.append(node)
                            visited_nodes.add(node)
            except NoWeakeningException as e:
                print(str(e))
                node = copy(node)
                node.spec = node.weak_spec_history[0]
                node.ct_list = node.ct_list[:1]
                node.learning_hypothesis = None
                node.learning_type = Learning.GUARANTEE_WEAKENING
                if node not in visited_nodes:
                    visited_nodes.add(node)
                    hypotheses = self._learner.find_weakening_hypotheses(node.spec, trace, node.ct_list, node.learning_type)
                    for hypothesis in hypotheses:
                        node = copy(node)
                        node.learning_hypothesis = hypothesis
                        if node not in visited_nodes:
                            stack.append(node)
                            visited_nodes.add(node)

        return unique_specs

    def ct_from_cs(self, cs: list[str]) -> CounterTrace:
        ct_name = f"counter_strat_{self._ct_cnt}"
        self._ct_cnt += 1
        return CounterTrace(cs, heuristic=first_choice, name=ct_name)
