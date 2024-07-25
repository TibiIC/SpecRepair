from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Optional, Deque, Set, List

from spec_repair.builders.spec_recorder import SpecRecorder
from spec_repair.components.counter_trace import CounterTrace, ct_from_cs, cts_from_cs
from spec_repair.components.heuristic_managers.heuristic_manager import HeuristicManager
from spec_repair.components.spec_learner import SpecLearner
from spec_repair.components.spec_oracle import SpecOracle
from spec_repair.enums import Learning
from spec_repair.exceptions import NoWeakeningException
from spec_repair.heuristics import first_choice
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
                sorted(self.ct_list) == sorted(other.ct_list) and
                self.learning_hypothesis == other.learning_hypothesis and
                self.learning_type == other.learning_type)

    def __hash__(self):
        hashable_learning_hypothesis = tuple(self.learning_hypothesis) if self.learning_hypothesis is not None else None
        return hash((tuple(self.spec), tuple(sorted(self.ct_list)), hashable_learning_hypothesis, self.learning_type))

    def __str__(self):
        return f"""
        Spec: {self.spec}
        CTs: {self.ct_list}
        Learning Hypothesis: {self.learning_hypothesis}
        Learning Type: {self.learning_type}
        Weak Spec History: {self.weak_spec_history}
        """


class BacktrackingRepairOrchestrator:
    def __init__(self, learner: SpecLearner, oracle: SpecOracle, heuristic_manager: HeuristicManager):
        self._learner = learner
        self._oracle = oracle
        self._hm = heuristic_manager
        self._initialise_repair_variables()

    # Reimplementation of the highest level abstraction code
    def repair_spec_bfs(
            self,
            spec: list[str],
            trace: list[str]
    ) -> SpecRecorder:
        self._initialise_repair_variables()
        stack: Deque[RepairNode] = deque()
        visited_nodes: Set[RepairNode] = set()
        unique_specs = SpecRecorder()
        root_node = RepairNode(spec, [], None, Learning.ASSUMPTION_WEAKENING)
        visited_nodes.add(root_node)
        stack.append(root_node)

        while stack:
            node = stack.popleft()
            if not node.learning_hypothesis:
                self._enqueue_weaker_repair_candidates(node, trace, stack, visited_nodes)
            else:
                new_spec = self._learner.integrate_learning_hypothesis(node.spec, node.learning_hypothesis,
                                                                       node.learning_type)
                node.weak_spec_history.append(new_spec)
                cs = self._oracle.synthesise_and_check(new_spec)
                if not cs:
                    unique_specs.add(Spec(''.join(new_spec)))
                else:
                    cts = self._selected_cts_from_cs(cs)
                    for ct in cts:
                        new_node = deepcopy(node)
                        new_node.ct_list.append(ct)
                        if new_node not in visited_nodes:
                            visited_nodes.add(new_node)
                            stack.append(new_node)

        return unique_specs

    def _initialise_repair_variables(self):
        # Counter for recording counter traces
        self._ct_cnt = 0
        self._hm.reset()

    def _enqueue_weaker_repair_candidates(
            self,
            incomplete_node: RepairNode,
            trace: list[str],
            stack: Deque[RepairNode],
            visited_nodes: Set[RepairNode]
    ):
        """
        Find all possible weaker repair nodes and add them to the stack if they are not already visited
        @param incomplete_node: The node to find weaker repair nodes for (possibly containing unresolved deadlocks)
        @param trace: The trace to learn from
        @param stack: The stack to add the new nodes to
        @param visited_nodes: The set of visited nodes
        @return: None
        """
        complete_ctss = self._complete_and_select_counter_traces(incomplete_node, trace)
        for complete_cts in complete_ctss:
            node = deepcopy(incomplete_node)
            node.ct_list = complete_cts
            try:
                hypotheses = self._find_and_select_weakening_hypotheses(node, trace)
                for hypothesis in hypotheses:
                    new_node = deepcopy(node)
                    new_node.learning_hypothesis = hypothesis
                    if new_node not in visited_nodes:
                        stack.append(new_node)
                        visited_nodes.add(new_node)
            except NoWeakeningException as e:
                print(str(e))
                print(node)
                # TODO: weak_spec_history may be empty if the first assumption weakening fails
                node.spec = node.weak_spec_history[0]
                node.ct_list = node.ct_list[:1]
                node.learning_hypothesis = None
                node.learning_type = Learning.GUARANTEE_WEAKENING
                if node not in visited_nodes:
                    visited_nodes.add(node)
                    stack.append(node)

    def _find_and_select_weakening_hypotheses(self, node, trace):
        hypotheses = self._learner.find_weakening_hypotheses(
            node.spec,
            trace,
            node.ct_list,
            node.learning_type
        )
        hypotheses = self._hm.select_weakening_hypotheses(hypotheses)
        return hypotheses

    def _complete_and_select_counter_traces(self, incomplete_node, trace):
        complete_ctss: List[List[CounterTrace]] = self._learner.violating_counter_trace_lists(
            incomplete_node.spec,
            trace,
            incomplete_node.ct_list,
            incomplete_node.learning_type
        )
        return self._hm.select_complete_counter_traces(complete_ctss)

    def _ct_from_cs(self, cs: list[str]) -> CounterTrace:
        """
        Create a CounterTrace object from a counter strategy
        """
        ct = ct_from_cs(cs, heuristic=first_choice, cs_id=self._ct_cnt)
        self._ct_cnt += 1
        return ct

    def _selected_cts_from_cs(self, cs: list[str]) -> list[CounterTrace]:
        """
        Create all CounterTrace objects from a counter strategy
        """
        cts = cts_from_cs(cs, cs_id=self._ct_cnt)
        self._ct_cnt += 1
        return self._hm.select_counter_traces(cts)
