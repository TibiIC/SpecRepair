from copy import deepcopy
from typing import Deque, Tuple, Any, Optional
from collections import deque

from spec_repair.interfaces.ispecification import ISpecification
from spec_repair.components.orchestration_managers.a_orchestration_manager_with_graph import \
    AOrchestrationManagerWithStackAndGraph
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.model.counter_trace import CounterTrace

RED = "#ff4444"
GREEN = "#44ff44"
BLUE = "#4444ff"
YELLOW = "#ffff44"


class OrchestrationManagerSemanticEquivalenceAsmOnly(AOrchestrationManagerWithStackAndGraph):
    def __init__(self):
        super().__init__()
        self._visited_nodes_list: list[Tuple[ISpecification, Learning, Any]] = []
        self._stack_candidates: Deque[Tuple[ISpecification, Any, list[Tuple[ISpecification, RepairData]]]] = deque()

    def _reset(self):
        super()._reset()
        self._visited_nodes_list = []
        self._stack_candidates = deque()

    def enqueue_new_tasks(
            self,
            spec: ISpecification,
            data: RepairData,
            prev: Optional[Tuple[ISpecification, RepairData]] = None,
            failed_spec: Optional[ISpecification] = None
    ) -> None:
        new_spec = spec
        new_learning_type = data.learning_type
        if data.learning_type == Learning.ASSUMPTION_WEAKENING:
            new_data = sorted(data.counter_traces)
        elif prev:
            new_data = data.counter_traces[-1]
        else:
            assert data.counter_traces == [] and data.learning_type == Learning.GUARANTEE_WEAKENING
            new_data = data.counter_traces
        for task_id, visited_node in enumerate(self._visited_nodes_list):
            visited_spec, visited_learning_type, visited_data = visited_node
            if new_spec == visited_spec and new_learning_type == visited_learning_type and new_data == visited_data:
                assert failed_spec
                self._add_edge_data_to_graph(data, prev, failed_spec, task_id)
                return None
        if new_learning_type == Learning.ASSUMPTION_WEAKENING:
            for candidate_id, candidate_node in enumerate(self._stack_candidates):
                key_spec, (candidate_spec, candidate_data), candidate_prev_list = candidate_node
                if failed_spec == key_spec:
                    new_candidate_data = deepcopy(candidate_data)
                    new_candidate_data.counter_traces = list(
                        set(new_candidate_data.counter_traces) | set(data.counter_traces))
                    self._stack_candidates[candidate_id] = (key_spec, (candidate_spec, new_candidate_data),
                                                            candidate_prev_list + [prev])
                    return None
            if failed_spec and prev:
                self._stack_candidates.append((failed_spec, (spec, data), [prev]))
            else:
                self._stack_candidates.append((spec, (spec, data), []))

        return None

    def _get_task_id(
            self,
            spec: ISpecification,
            data: RepairData
    ):
        if data.learning_type == Learning.ASSUMPTION_WEAKENING:
            visited_node: Tuple[ISpecification, Learning, Any] = (spec, data.learning_type, sorted(data.counter_traces))
        elif data.counter_traces:
            visited_node: Tuple[ISpecification, Learning, Any] = (spec, data.learning_type, data.counter_traces[-1])
        else:
            assert data.counter_traces == [] and data.learning_type == Learning.GUARANTEE_WEAKENING
            visited_node: Tuple[ISpecification, Any] = (spec, data.learning_type, data.counter_traces)
        for task_id, past_node in enumerate(self._visited_nodes_list):
            past_spec, past_learning_type, past_data = past_node
            if visited_node[0] == past_spec and visited_node[1] == past_learning_type and visited_node[2] == past_data:
                return task_id
        raise ValueError("No such task")

    def has_next(self) -> bool:
        self._if_stack_empty_add_next_stack_candidate()
        return super().has_next()

    def _if_stack_empty_add_next_stack_candidate(self) -> bool:
        if not self._stack:
            return self._add_next_stack_candidate()
        return False

    def get_next(self) -> Tuple[ISpecification, Any]:
        self._if_stack_empty_add_next_stack_candidate()
        spec, data = super().get_next()
        if data.learning_type == Learning.ASSUMPTION_WEAKENING:
            visited_data = sorted(data.counter_traces)
        else:
            if not data.counter_traces:
                visited_data = data.counter_traces
            else:
                visited_data = data.counter_traces[-1]
        self._visited_nodes_list.append((spec, data.learning_type, visited_data))
        return spec, data

    def _add_next_stack_candidate(self):
        while self._stack_candidates:
            failed_spec, (spec, data), prev_list = self._stack_candidates.popleft()

            if data.learning_type == Learning.ASSUMPTION_WEAKENING:
                new_data = sorted(data.counter_traces)
            elif not data.counter_traces:
                new_data = data.counter_traces[-1]
            else:
                assert data.learning_type == Learning.GUARANTEE_WEAKENING
                new_data = data.counter_traces
            is_visited = False
            for task_id, visited_node in enumerate(self._visited_nodes_list):
                if task_id == 3:
                    print("stop here")
                visited_spec, visited_learning_type, visited_data = visited_node
                if spec == visited_spec and data.learning_type == visited_learning_type and new_data == visited_data:
                    assert failed_spec
                    for prev in prev_list:
                        self._add_edge_data_to_graph(data, prev, failed_spec, task_id)
                    is_visited = True
            if not is_visited:
                self._stack.append((spec, data))
                node_color = YELLOW if not prev_list else (RED if data.learning_type == Learning.ASSUMPTION_WEAKENING else GREEN)
                cts: list[CounterTrace] = data.counter_traces[
                    -1:] if data.learning_type == Learning.GUARANTEE_WEAKENING else sorted(data.counter_traces)
                task_id = len(self._visited_nodes_list)
                self._graph.add_node(
                    task_id,
                    spec=spec.to_str(),
                    color=node_color,
                    data=([ct.print_multi_line() for ct in cts], str(data.learning_type))
                )
                for prev in prev_list:
                    self._add_edge_data_to_graph(data, prev, failed_spec, task_id)
                return True
        return False
