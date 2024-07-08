from __future__ import annotations

from collections import deque
from copy import deepcopy
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


class BaseRepairNode:
    def __init__(
            self,
            spec: list[str],
            ct_list: Optional[any],
            learning_type: Learning
    ):
        self.spec = spec
        self.ct_list = ct_list
        self.learning_type = learning_type

    def __eq__(self, other) -> bool:
        return (self.spec == other.spec and
                self.ct_list == other.ct_list and
                self.learning_type == other.learning_type)

    def __hash__(self) -> int:
        return hash((tuple(self.spec), tuple(self.ct_list), self.learning_type))

    def __str__(self) -> str:
        return f"""
        Spec: {self.spec}
        CTs: {self.ct_list}
        Learning Type: {self.learning_type}
        """

    def get_hypothesised_repair_node(self, learning_hypothesis: list[str]) -> RepairNode:
        return RepairNode(
            deepcopy(self.spec),
            deepcopy(self.ct_list),
            learning_hypothesis,
            deepcopy(self.learning_type)
        )


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

    def __str__(self):
        return f"""
        Spec: {self.spec}
        CTs: {self.ct_list}
        Learning Hypothesis: {self.learning_hypothesis}
        Learning Type: {self.learning_type}
        Weak Spec History: {self.weak_spec_history}
        """


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
        node = RepairNode(spec, [], None, Learning.ASSUMPTION_WEAKENING)
        try:
            hypotheses = self._learner.find_weakening_hypotheses(node.spec, trace, node.ct_list, node.learning_type)
        except NoWeakeningException as e:
            print(str(e))
            print(node)
            node.spec = node.weak_spec_history[0]
            node.ct_list = node.ct_list[:1]
            node.learning_hypothesis = None
            node.learning_type = Learning.GUARANTEE_WEAKENING
            if node in visited_nodes:
                hypotheses = []  # No learning needed anymore, steps would be repeated
            else:
                visited_nodes.add(node)
                hypotheses = self._learner.find_weakening_hypotheses(node.spec, trace, node.ct_list,
                                                                     node.learning_type)
        for hypothesis in hypotheses:
            new_node = deepcopy(node)
            new_node.learning_hypothesis = hypothesis
            if new_node not in visited_nodes:
                stack.append(new_node)
                visited_nodes.add(new_node)

        while stack:
            node = stack.popleft()
            new_spec = self._learner.integrate_learning_hypothesis(node.spec, node.learning_hypothesis,
                                                                   node.learning_type)
            node.weak_spec_history.append(new_spec)
            cs = self._oracle.synthesise_and_check(new_spec)
            if not cs:
                unique_specs.add(Spec(''.join(new_spec)))
            else:
                node = deepcopy(node)
                node.ct_list.append(self.ct_from_cs(cs))
                try:
                    hypotheses = self._learner.find_weakening_hypotheses(node.spec, trace, node.ct_list,
                                                                         node.learning_type)
                except NoWeakeningException as e:
                    print(str(e))
                    print(node)
                    node.spec = node.weak_spec_history[0]
                    node.ct_list = node.ct_list[:1]
                    node.learning_hypothesis = None
                    node.learning_type = Learning.GUARANTEE_WEAKENING
                    if node in visited_nodes:
                        hypotheses = []  # No learning needed anymore, steps would be repeated
                    else:
                        visited_nodes.add(node)
                        hypotheses = self._learner.find_weakening_hypotheses(node.spec, trace, node.ct_list,
                                                                             node.learning_type)
                for hypothesis in hypotheses:
                    new_node = deepcopy(node)
                    new_node.learning_hypothesis = hypothesis
                    if new_node not in visited_nodes:
                        stack.append(new_node)
                        visited_nodes.add(new_node)

        return unique_specs

    def ct_from_cs(self, cs: list[str]) -> CounterTrace:
        ct_name = f"counter_strat_{self._ct_cnt}"
        self._ct_cnt += 1
        return CounterTrace(cs, heuristic=first_choice, name=ct_name)
