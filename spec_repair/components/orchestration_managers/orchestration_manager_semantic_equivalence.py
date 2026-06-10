from typing import Deque, Tuple, Any, Optional

from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.components.orchestration_managers.a_orchestration_manager_with_graph import \
    AOrchestrationManagerWithStackAndGraph
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.helpers.counter_trace import CounterTrace

RED = "#ff4444"
GREEN = "#44ff44"
BLUE = "#4444ff"
YELLOW = "#ffff44"


class OrchestrationManagerSemanticEquivalence(AOrchestrationManagerWithStackAndGraph):
    def __init__(self):
        super().__init__()
        self._visited_nodes_list: list[Tuple[ISpecification, Any]] = []

    def _reset(self):
        super()._reset()
        self._visited_nodes_list = []

    def enqueue_new_tasks(
            self,
            spec: ISpecification,
            data: RepairData,
            prev: Optional[Tuple[ISpecification, RepairData]] = None,
            failed_spec: Optional[ISpecification] = None
    ):
        if data.learning_type == Learning.ASSUMPTION_WEAKENING:
            visited_node: Tuple[ISpecification, Any] = (spec, (sorted(data.counter_traces), data.learning_type))
        elif prev:
            visited_node: Tuple[ISpecification, Any] = (spec, (data.counter_traces[-1], data.learning_type))
        else:
            assert data.counter_traces == [] and data.learning_type == Learning.GUARANTEE_WEAKENING
            visited_node: Tuple[ISpecification, Any] = (spec, (sorted(data.counter_traces), data.learning_type))
        node: Tuple[ISpecification, Any] = (spec, data)
        for task_id, past_node in enumerate(self._visited_nodes_list):
            past_spec, past_data = past_node
            if visited_node[0] == past_spec and visited_node[1] == past_data:
                self._add_edge_data_to_graph(data, prev, failed_spec, task_id)
                return task_id
        task_id = len(self._visited_nodes_list)
        self._stack.append(node)
        self._visited_nodes_list.append(visited_node)
        node_color = YELLOW if not prev else (RED if data.learning_type == Learning.ASSUMPTION_WEAKENING else GREEN)
        cts: list[CounterTrace] = data.counter_traces[
            -1:] if data.learning_type == Learning.GUARANTEE_WEAKENING else sorted(data.counter_traces)
        self._graph.add_node(
            task_id,
            spec=spec.to_str(),
            color=node_color,
            data=([ct.print_multi_line() for ct in cts], str(data.learning_type))
        )
        self._add_edge_data_to_graph(data, prev, failed_spec, task_id)
        return task_id

    def _get_task_id(
            self,
            spec: ISpecification,
            data: RepairData
    ):
        if data.learning_type == Learning.ASSUMPTION_WEAKENING:
            visited_node: Tuple[ISpecification, Any] = (spec, (sorted(data.counter_traces), data.learning_type))
        elif data.counter_traces:
            visited_node: Tuple[ISpecification, Any] = (spec, (data.counter_traces[-1], data.learning_type))
        else:
            assert data.counter_traces == [] and data.learning_type == Learning.GUARANTEE_WEAKENING
            visited_node: Tuple[ISpecification, Any] = (spec, (data.counter_traces, data.learning_type))
        for task_id, past_node in enumerate(self._visited_nodes_list):
            past_spec, past_data = past_node
            if visited_node[0] == past_spec and visited_node[1] == past_data:
                return task_id
        raise ValueError("No such task")
