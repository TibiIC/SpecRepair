"""
Labelling the debug graph must not be able to end a repair run.

A leaf can be reached with an empty adaptation history: guarantee weakening
with no counter-traces hands its task straight back for the oracle to extract
counter-strategies from, unchanged and with nothing appended. If that
specification then verifies clean, it is a leaf whose incoming edge has no
adaptation to name, and `[-1]` on the empty history raised.

Measured on the 2026-08-07 ILASP sweep: 11 of 57 runs died this way - every
amba trace, every colorsort trace, and gyro_0 - all with an IndexError thrown
while writing a label onto a graph nobody had read yet.
"""
import unittest

from spec_repair.components.orchestration_managers.orchestration_manager_syntactic_equivalence import \
    OrchestrationManagerSyntacticEquivalence
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.model.spectra_specification import SpectraSpecification

SPEC = """module Test

env boolean a;
sys boolean b;

assumption -- asm1
\tG(a);

guarantee -- gar1
\tG(b);
"""


class TestLeafEdgeLabelling(unittest.TestCase):
    def setUp(self):
        self.om = OrchestrationManagerSyntacticEquivalence()
        self.spec = SpectraSpecification.from_str(SPEC)

    def _data(self, history):
        return RepairData(trace=[""], counter_traces=[],
                          learning_type=Learning.GUARANTEE_WEAKENING,
                          adaptation_history=history)

    def test_a_leaf_with_no_adaptation_history_is_recorded(self):
        """The case that killed 11 runs: nothing to name on the incoming edge."""
        data = self._data([])
        self.om.initialise_learning_tasks(self.spec, data)
        self.om.connect_leaf_node(self.spec, 0, prev=(self.spec, data))
        self.assertIn("#0", self.om._graph.nodes)

    def test_the_edge_says_why_there_is_no_adaptation(self):
        """Losing the label is acceptable; losing the explanation is not."""
        data = self._data([])
        self.om.initialise_learning_tasks(self.spec, data)
        self.om.connect_leaf_node(self.spec, 0, prev=(self.spec, data))
        edges = [d for _, _, d in self.om._graph.edges(data=True) if d]
        self.assertTrue(any("details" in d for d in edges), edges)

    def test_an_adaptation_is_still_labelled_when_there_is_one(self):
        data = self._data([["antecedent_exception(asm1,0,[('current','a=false')])"]])
        self.om.initialise_learning_tasks(self.spec, data)
        self.om.connect_leaf_node(self.spec, 1, prev=(self.spec, data))
        edges = [d for _, _, d in self.om._graph.edges(data=True) if d]
        self.assertTrue(any("last_adaptation" in d for d in edges), edges)


if __name__ == "__main__":
    unittest.main()
