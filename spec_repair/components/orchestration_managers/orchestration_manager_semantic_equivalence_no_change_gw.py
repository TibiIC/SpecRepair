from collections import deque
from typing import Deque, Tuple, Any, Optional

import networkx as nx

from spec_repair.components.interfaces.iorchestration_manager import IOrchestrationManager
from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.helpers.recorders.unique_recorder import UniqueRecorder


class OrchestrationManagerSemanticEquivalenceNoGWChange(IOrchestrationManager):
    def __init__(self):
        self._stack: Deque[Tuple[ISpecification, Any]] = deque()
        self._visited_nodes_list: list[Tuple[ISpecification, Any]] = []
        self._graph = nx.DiGraph()

    def _reset(self):
        self._stack.clear()
        self._visited_nodes = UniqueRecorder()

    def initialise_learning_tasks(self, spec: ISpecification, data: RepairData):
        self._reset()
        self.enqueue_new_tasks(spec, data, prev=None)

    def enqueue_new_tasks(self, spec: ISpecification, data: RepairData, prev: Optional[Tuple[ISpecification, Any]] = None, failed_spec: Optional[ISpecification] = None):
        if prev:
            prev_spec, prev_data = prev
            if prev_data.learning_type == Learning.GUARANTEE_WEAKENING and data.learning_type == Learning.GUARANTEE_WEAKENING:
                spec = prev_spec
        visited_node: Tuple[ISpecification, Any] = (spec, (sorted(data.counter_traces), data.learning_type))
        node: Tuple[ISpecification, Any] = (spec, data)
        graph_node: Tuple[str, Any] = (spec.to_str(), ([ct.get_raw_trace() for ct in data.counter_traces[-1:]], str(data.learning_type)))
        for task_id, past_node in enumerate(self._visited_nodes_list):
            past_spec, past_data = past_node
            if visited_node[0] == past_spec and visited_node[1] == past_data:
                if prev is not None:
                    prev_task_id = self._get_task_id(*prev)
                    if failed_spec is not None:
                        self._graph.add_edge(
                            prev_task_id,
                            task_id,
                            failed_spec=failed_spec.to_str(),
                            last_adaptation=[str(adaptation) for adaptation in prev_data.adaptation_history[-1]]
                        )
                    else:
                        self._graph.add_edge(
                            prev_task_id,
                            task_id
                        )
                return task_id
        task_id = len(self._visited_nodes_list)
        self._stack.append(node)
        self._visited_nodes_list.append(visited_node)
        self._graph.add_node(task_id, spec=spec.to_str(), data=([ct.get_raw_trace() for ct in data.counter_traces[-1:]], str(data.learning_type)))
        if prev is not None:
            prev_task_id = self._get_task_id(*prev)
            self._graph.add_edge(
                prev_task_id,
                task_id,
                failed_spec=failed_spec.to_str(),
                last_adaptation=[str(adaptation) for adaptation in prev_data.adaptation_history[-1]]
            )
        return task_id

    def _get_task_id(self, spec: ISpecification, data: RepairData):
        visited_node: Tuple[ISpecification, Any] = (spec, (sorted(data.counter_traces), data.learning_type))
        for task_id, past_node in enumerate(self._visited_nodes_list):
            past_spec, past_data = past_node
            if visited_node[0] == past_spec and visited_node[1] == past_data:
                return task_id
        raise ValueError("No such task")

    def connect_leaf_node(self, spec: ISpecification, unique_id: int, prev: Tuple[ISpecification, RepairData]):
        prev_id = self._get_task_id(*prev)
        prev_spec, prev_data = prev
        self._graph.add_node(f"#{unique_id}", spec=spec.to_str(), color="#ff4444")
        self._graph.add_edge(prev_id, f"#{unique_id}")

        self._graph.add_edge(
            prev_id,
            f"#{unique_id}",
            last_adaptation=[str(adaptation) for adaptation in prev_data.adaptation_history[-1]]
        )

    def has_next(self) -> bool:
        return bool(self._stack)

    def get_next(self) -> Tuple[ISpecification, Any]:
        return self._stack.popleft()
