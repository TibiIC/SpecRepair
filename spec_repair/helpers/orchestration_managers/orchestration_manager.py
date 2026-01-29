from collections import deque
from typing import Deque, Tuple, Any

from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.config import SEMANTIC_EQUIVALENCE
from spec_repair.helpers.recorders.irecorder import IRecorder
from spec_repair.helpers.recorders.unique_recorder import UniqueRecorder


# TODO: turn this one into an argument in the BFS strategy initialisation as well
class OrchestrationManager:
    def __init__(self):
        self._stack: Deque[Tuple[ISpecification, Any]] = deque()
        if SEMANTIC_EQUIVALENCE:
            self._visited_nodes_list: list[Tuple[ISpecification, Any]] = []
        else:
            self._visited_nodes: IRecorder[Tuple[ISpecification, Any]] = UniqueRecorder()
        # self._graph = nx.DiGraph()

    def _reset(self):
        self._stack.clear()
        self._visited_nodes = UniqueRecorder()

    def initialise_learning_tasks(self, spec: ISpecification, data: Any):
        self._reset()
        self.enqueue_new_tasks(spec, data)

    def enqueue_new_tasks(self, spec: ISpecification, data: Any):
        trace, cts, learning_type, spec_history, learning_steps, learning_time = data
        visited_node: Tuple[ISpecification, Any] = (spec, (cts[-1:], learning_type))
        node: Tuple[ISpecification, Any] = (spec, data)
        if not SEMANTIC_EQUIVALENCE:
            if visited_node not in self._visited_nodes:
                self._stack.append(node)
                self._visited_nodes.add(visited_node)
        else:
            is_visited = False
            for past_node in reversed(self._visited_nodes_list):
                past_spec, past_data = past_node
                if visited_node[0] == past_spec and visited_node[1] == past_data:
                    is_visited = True
                    break
            if not is_visited:
                self._stack.append(node)
                self._visited_nodes_list.append(visited_node)

    def has_next(self) -> bool:
        return bool(self._stack)

    def get_next(self) -> Tuple[ISpecification, Any]:
        return self._stack.popleft()
