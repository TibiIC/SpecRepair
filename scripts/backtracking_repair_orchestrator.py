from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Deque, List

from spec_repair.helpers.logger import Logger, NoLogger
from spec_repair.builders.spec_recorder import SpecRecorder
from spec_repair.helpers.counter_trace import CounterTrace, cts_from_cs
from spec_repair.components.heuristic_managers.heuristic_manager import HeuristicManager
from spec_repair.components.spec_learner import SpecLearner
from spec_repair.components.spec_oracle import SpecOracle
from spec_repair.enums import Learning
from spec_repair.exceptions import NoAssumptionWeakeningException
from spec_repair.helpers.recorder import Recorder
from spec_repair.helpers.repair_nodes.candidate_repair_node import CandidateRepairNode
from spec_repair.wrappers.spec import Spec


class BacktrackingRepairOrchestrator:
    def __init__(
            self,
            learner: SpecLearner,
            oracle: SpecOracle,
            heuristic_manager: HeuristicManager,
            logger: Logger = NoLogger()

    ):
        self._learner = learner
        self._oracle = oracle
        self._hm = heuristic_manager
        self._logger = logger
        self._initialise_repair_variables()

    # Reimplementation of the highest level abstraction code
    def repair_spec_bfs(
            self,
            spec: list[str],
            trace: list[str]
    ) -> SpecRecorder:
        self._initialise_repair_variables()
        unique_specs = SpecRecorder()
        root_node = CandidateRepairNode(spec, [], None, Learning.ASSUMPTION_WEAKENING)
        self._visited_nodes.add(root_node)
        self._stack.append(root_node)

        while self._stack:
            node = self._stack.popleft()
            if not node.learning_hypothesis:
                self._find_and_enqueue_weaker_spec_candidates(node, trace)
            else:
                new_spec = self._compile_and_record_weaker_spec_candidate(node)
                cs = self._oracle.synthesise_and_check(new_spec)
                if not cs:
                    node_id = self._visited_nodes.get_id(node)
                    spec_id = unique_specs.add(Spec(''.join(new_spec)))
                    self._logger.log_transition(node_id, f"#{spec_id}", f"End")
                else:
                    cts = self._selected_cts_from_cs(cs)
                    self._enqueue_unvisited_learning_candidates(node, new_spec, cts)

        return unique_specs

    def _find_and_enqueue_weaker_spec_candidates(
            self,
            incomplete_node: CandidateRepairNode,
            trace: list[str],
    ):
        """
        Find all possible weaker repair nodes and add them to the stack if they are not already visited
        @param incomplete_node: The node to find weaker repair nodes for (possibly containing unresolved deadlocks)
        @param trace: The trace to learn from
        @return: None
        """
        complete_ctss = self._complete_and_select_counter_trace_lists(incomplete_node, trace)
        for complete_cts in complete_ctss:
            node = deepcopy(incomplete_node)
            node.ct_list = complete_cts
            # TODO: wrap logging logic
            if node not in self._visited_nodes:
                self._stack.append(node)
                self._visited_nodes.add(node)
            from_id = self._visited_nodes.get_id(incomplete_node)
            to_id = self._visited_nodes.get_id(node)
            new_cts_str = f"CTS({';'.join([ct.print_one_line() for ct in complete_cts])})"
            self._logger.log_transition(from_id, to_id, f"{node.learning_type.name} -> {new_cts_str}")
            try:
                hypotheses = self._learn_and_select_weakening_hypotheses(node, trace)
                self._enqueue_unvisited_weaker_spec_candidates(node, hypotheses)
            except NoAssumptionWeakeningException as e:
                self._initialise_guarantee_weakening(node)

    def _complete_and_select_counter_trace_lists(self, incomplete_node, trace):
        complete_ctss: List[List[CounterTrace]] = self._learner.get_all_complete_counter_trace_lists(
            incomplete_node.spec,
            trace,
            incomplete_node.ct_list,
            incomplete_node.learning_type
        )
        return self._hm.select_complete_counter_traces(complete_ctss)

    def _learn_and_select_weakening_hypotheses(self, node, trace):
        hypotheses = self._learner.find_weakening_hypotheses(
            node.spec,
            trace,
            node.ct_list,
            node.learning_type
        )
        hypotheses = self._hm.select_weakening_hypotheses(hypotheses)
        return hypotheses

    def _enqueue_unvisited_weaker_spec_candidates(self, node, hypotheses):
        for hypothesis in hypotheses:
            new_node = deepcopy(node)
            new_node.learning_hypothesis = hypothesis
            if new_node not in self._visited_nodes:
                self._stack.append(new_node)
                self._visited_nodes.add(new_node)
            from_id = self._visited_nodes.get_id(node)
            to_id = self._visited_nodes.get_id(new_node)
            self._logger.log_transition(from_id, to_id, f"{node.learning_type.name} -> {new_node.learning_hypothesis}")

    def _enqueue_unvisited_learning_candidates(self, node, new_spec, cts):
        for ct in cts:
            new_node = deepcopy(node)
            new_node.learning_hypothesis = None
            new_node.weak_spec_history.append(new_spec)
            new_node.ct_list.append(ct)
            if new_node not in self._visited_nodes:
                self._stack.append(new_node)
                self._visited_nodes.add(new_node)
            from_id = self._visited_nodes.get_id(node)
            to_id = self._visited_nodes.get_id(new_node)
            self._logger.log_transition(from_id, to_id, f"{new_node.learning_type.name} -> {ct.print_one_line()}")

    def _compile_and_record_weaker_spec_candidate(self, node):
        new_spec = self._learner.integrate_learning_hypothesis(node.spec, node.learning_hypothesis,
                                                               node.learning_type)
        return new_spec

    def _initialise_repair_variables(self):
        # Counter for recording counter traces
        self._ct_cnt = 0
        self._hm.reset()
        self._stack: Deque[CandidateRepairNode] = deque()
        self._visited_nodes: Recorder[CandidateRepairNode] = Recorder()

    def _initialise_guarantee_weakening(self, node):
        assert node.learning_type == Learning.ASSUMPTION_WEAKENING
        new_node = deepcopy(node)
        # TODO: weak_spec_history may be empty if the first assumption weakening fails
        new_node.spec = new_node.weak_spec_history[0]
        new_node.ct_list = new_node.ct_list[:1]
        new_node.learning_hypothesis = None
        new_node.learning_type = Learning.GUARANTEE_WEAKENING
        if new_node not in self._visited_nodes:
            self._visited_nodes.add(new_node)
            self._stack.append(new_node)
        from_id = self._visited_nodes.get_id(node)
        to_id = self._visited_nodes.get_id(new_node)
        self._logger.log_transition(from_id, to_id, f"{new_node.learning_type.name} -> Start")

    def _selected_cts_from_cs(self, cs: list[str]) -> list[CounterTrace]:
        """
        Create all CounterTrace objects from a counter strategy
        """
        cts = cts_from_cs(cs, cs_id=self._ct_cnt)
        self._ct_cnt += 1
        return self._hm.select_counter_traces(cts)
