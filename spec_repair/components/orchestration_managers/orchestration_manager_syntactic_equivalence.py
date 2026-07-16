from typing import Deque, Tuple, Any, Optional

from spec_repair.interfaces.ispecification import ISpecification
from spec_repair.components.orchestration_managers.a_orchestration_manager_with_graph import \
    AOrchestrationManagerWithStackAndGraph
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.interfaces.irecorder import IRecorder
from spec_repair.components.recorders.unique_recorder import UniqueRecorder

RED = "#ff4444"
GREEN = "#44ff44"
BLUE = "#4444ff"
YELLOW = "#ffff44"


class OrchestrationManagerSyntacticEquivalence(AOrchestrationManagerWithStackAndGraph):
    def __init__(self):
        super().__init__()
        self._visited_nodes: IRecorder[Tuple[ISpecification, Any]] = UniqueRecorder()

    def _reset(self):
        super()._reset()
        self._visited_nodes = UniqueRecorder()

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
            visited_node: Tuple[ISpecification, Any] = (spec, (data.counter_traces, data.learning_type))
        node: Tuple[ISpecification, Any] = (spec, data)
        if visited_node in self._visited_nodes:
            task_id = self._visited_nodes.get_id(visited_node)
            self._add_edge_data_to_graph(data, prev, failed_spec, task_id)
            return task_id

        self._stack.append(node)
        self._visited_nodes.add(visited_node)
        task_id = self._visited_nodes.get_id(visited_node)
        node_color = YELLOW if not prev else (RED if data.learning_type == Learning.ASSUMPTION_WEAKENING else GREEN)
        self._graph.add_node(
            task_id,
            spec=spec.to_str(),
            color=node_color,
            data=([ct.print_multi_line() for ct in data.counter_traces[-1:]], str(data.learning_type))
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
        return self._visited_nodes.get_id(visited_node)
