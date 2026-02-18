from collections import deque
from typing import Deque, Tuple, Any, Optional

import networkx as nx

from spec_repair.components.interfaces.iorchestration_manager import IOrchestrationManager
from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.helpers.recorders.irecorder import IRecorder
from spec_repair.helpers.recorders.unique_recorder import UniqueRecorder


class OrchestrationManagerSyntacticEquivalence(IOrchestrationManager):
    def __init__(self):
        self._stack: Deque[Tuple[ISpecification, Any]] = deque()
        self._visited_nodes: IRecorder[Tuple[ISpecification, Any]] = UniqueRecorder()
        self._graph = nx.DiGraph()

    def _reset(self):
        self._stack.clear()
        self._visited_nodes = UniqueRecorder()

    def initialise_learning_tasks(self, spec: ISpecification, data: Any):
        self._reset()
        self.enqueue_new_tasks(spec, data, prev=None)

    def enqueue_new_tasks(self, spec: ISpecification, data: Any, prev: Optional[Tuple[ISpecification, Any]] = None):
        trace, cts, learning_type, spec_history, learning_steps, learning_time = data
        visited_node: Tuple[ISpecification, Any] = (spec, (cts[-1:], learning_type))
        node: Tuple[ISpecification, Any] = (spec, data)
        graph_node: Tuple[str, Any] = (spec.to_str(), ([ct.get_raw_trace() for ct in cts[-1:]], str(learning_type)))
        if visited_node not in self._visited_nodes:
            self._stack.append(node)
            self._visited_nodes.add(visited_node)
            self._graph.add_node(len(self._visited_nodes)-1, state=graph_node)
        task_id = self._visited_nodes.get_id(visited_node)
        if prev is not None:
            prev_task_id = self._get_task_id(*prev)
            self._graph.add_edge(prev_task_id, task_id)
        return task_id

    def _get_task_id(self, spec: ISpecification, data: Any):
        node: Tuple[ISpecification, Any] = (spec, data)
        return self._visited_nodes.get_id(node)

    def connect_leaf_node(self, spec: ISpecification, unique_id: int, prev: Tuple[ISpecification, Any]):
        prev_id = self._get_task_id(*prev)
        self._graph.add_node(f"#{unique_id}", state=spec.to_str())
        self._graph.add_edge(prev_id, f"#{unique_id}")

    def has_next(self) -> bool:
        return bool(self._stack)

    def get_next(self) -> Tuple[ISpecification, Any]:
        return self._stack.popleft()
