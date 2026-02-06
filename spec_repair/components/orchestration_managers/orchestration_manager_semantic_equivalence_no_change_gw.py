from collections import deque
from typing import Deque, Tuple, Any, Optional

import networkx as nx

from spec_repair.components.interfaces.iorchestration_manager import IOrchestrationManager
from spec_repair.components.interfaces.ispecification import ISpecification
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

    def initialise_learning_tasks(self, spec: ISpecification, data: Any):
        self._reset()
        self.enqueue_new_tasks(spec, data, prev=None)

    def enqueue_new_tasks(self, spec: ISpecification, data: Any, prev: Optional[Tuple[ISpecification, Any]] = None):
        trace, cts, learning_type, spec_history, learning_steps, learning_time = data
        if prev:
            prev_spec, prev_data = prev
            prev_trace, prev_cts, prev_learning_type, prev_spec_history, prev_learning_steps, prev_learning_time = prev_data
            if prev_learning_type == Learning.GUARANTEE_WEAKENING and learning_type == Learning.GUARANTEE_WEAKENING:
                spec = prev_spec
        visited_node: Tuple[ISpecification, Any] = (spec, (sorted(cts), learning_type))
        node: Tuple[ISpecification, Any] = (spec, data)
        graph_node: Tuple[str, Any] = (spec.to_str(), ([ct.get_raw_trace() for ct in cts[-1:]], str(learning_type)))
        for task_id, past_node in enumerate(self._visited_nodes_list):
            past_spec, past_data = past_node
            if visited_node[0] == past_spec and visited_node[1] == past_data:
                if prev is not None:
                    prev_task_id = self.get_task_id(*prev)
                    self._graph.add_edge(prev_task_id, task_id)
                return task_id
        task_id = len(self._visited_nodes_list)
        self._stack.append(node)
        self._visited_nodes_list.append(visited_node)
        self._graph.add_node(task_id, state=graph_node)
        if prev is not None:
            prev_task_id = self.get_task_id(*prev)
            self._graph.add_edge(prev_task_id, task_id)
        return task_id

    def get_task_id(self, spec: ISpecification, data: Any):
        trace, cts, learning_type, spec_history, learning_steps, learning_time = data
        visited_node: Tuple[ISpecification, Any] = (spec, (sorted(cts), learning_type))
        for task_id, past_node in enumerate(self._visited_nodes_list):
            past_spec, past_data = past_node
            if visited_node[0] == past_spec and visited_node[1] == past_data:
                return task_id
        raise ValueError("No such task")

    def connect_leaf_node(self, spec: ISpecification, unique_id: int, prev: Tuple[ISpecification, Any]):
        prev_id = self.get_task_id(*prev)
        self._graph.add_node(f"#{unique_id}", state=spec.to_str())
        self._graph.add_edge(prev_id, f"#{unique_id}")

    def has_next(self) -> bool:
        return bool(self._stack)

    def get_next(self) -> Tuple[ISpecification, Any]:
        return self._stack.popleft()
