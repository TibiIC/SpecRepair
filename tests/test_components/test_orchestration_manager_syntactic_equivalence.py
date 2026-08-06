from copy import deepcopy
from typing import Any

from spec_repair.components.orchestration_managers.orchestration_manager_syntactic_equivalence import \
    OrchestrationManagerSyntacticEquivalence
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.model.counter_trace import CounterTrace
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file_lines
from tests.base_test_case import BaseTestCase

ct_raw_trace = """\
not_holds_at(highwater,0,ini_S0_DEAD).
not_holds_at(methane,0,ini_S0_DEAD).
not_holds_at(pump,0,ini_S0_DEAD).
holds_at(highwater,1,ini_S0_DEAD).
holds_at(methane,1,ini_S0_DEAD).
holds_at(pump,1,ini_S0_DEAD).\
"""
ct_path = "ini_S0_DEAD"
ct_name = "counter_strat_0_0"

class TestOrchestrationManagerSyntacticEquivalence(BaseTestCase):
    def test_initialise_learning_tasks(self):
        om = OrchestrationManagerSyntacticEquivalence()
        case_study_path = '../input-files/case-studies/spectra/strengthened/minepump'
        spec: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        data: RepairData = RepairData(trace, [], Learning.ASSUMPTION_WEAKENING, [], 0, 0)
        # Check that the stack and visited nodes list are empty
        self.assertEqual(len(om._stack), 0)
        self.assertEqual(len(om._visited_nodes), 0)
        om.initialise_learning_tasks(spec, data)
        # Check that the stack and visited nodes list are now populated
        self.assertEqual(len(om._stack), 1)
        self.assertEqual(len(om._visited_nodes), 1)
        self.assertEqual(om._stack[0][0].to_str(), spec.to_str())
        self.assertEqual(om._stack[0][1], data)
        self.assertIn((spec, ([], Learning.ASSUMPTION_WEAKENING)), om._visited_nodes)

    def test_enqueue_new_tasks_same(self):
        om = OrchestrationManagerSyntacticEquivalence()
        case_study_path = '../input-files/case-studies/spectra/strengthened/minepump'
        spec: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        data: RepairData = RepairData(trace, [], Learning.ASSUMPTION_WEAKENING, [], 0, 0)
        self.assertEqual(len(om._stack), 0)
        self.assertEqual(len(om._visited_nodes), 0)
        om.initialise_learning_tasks(spec, data)
        self.assertEqual(len(om._stack), 1)
        self.assertEqual(len(om._visited_nodes), 1)
        self.assertIn((spec, ([], Learning.ASSUMPTION_WEAKENING)), om._visited_nodes)
        om.enqueue_new_tasks(deepcopy(spec), deepcopy(data))
        self.assertEqual(len(om._stack), 1)
        self.assertEqual(len(om._visited_nodes), 1)
        self.assertEqual(om._stack[0][0].to_str(), spec.to_str())
        self.assertEqual(om._stack[0][1], data)
        self.assertIn((spec, ([], Learning.ASSUMPTION_WEAKENING)), om._visited_nodes)
        om.enqueue_new_tasks(deepcopy(spec), deepcopy(data))
        self.assertEqual(len(om._stack), 1)
        self.assertEqual(len(om._visited_nodes), 1)
        self.assertIn((spec, ([], Learning.ASSUMPTION_WEAKENING)), om._visited_nodes)

    def test_enqueue_new_tasks_semantically_equivalent(self):
        om = OrchestrationManagerSyntacticEquivalence()
        case_study_path = '../input-files/case-studies/spectra/strengthened/minepump'
        spec: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        spec_1: SpectraSpecification = SpectraSpecification.from_file("./test_files/minepump_aw_highwater.spectra")
        spec_2: SpectraSpecification = SpectraSpecification.from_file("./test_files/minepump_aw_methane.spectra")
        self.assertEqual(spec_1, spec_2) # Sanity check
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        ct = CounterTrace(raw_trace=ct_raw_trace, raw_path=ct_path, name=ct_name)
        data: RepairData = RepairData(trace, [], Learning.ASSUMPTION_WEAKENING, [], 0, 0)
        data_1: RepairData = RepairData(trace, [ct], Learning.ASSUMPTION_WEAKENING, [], 1, 0)
        data_2: RepairData = RepairData(trace, [ct], Learning.ASSUMPTION_WEAKENING, [], 2, 0)
        self.assertEqual(len(om._stack), 0)
        self.assertEqual(len(om._visited_nodes), 0)
        om.initialise_learning_tasks(spec, data)
        self.assertEqual(len(om._stack), 1)
        self.assertEqual(len(om._visited_nodes), 1)
        self.assertEqual(om._stack[0][0].to_str(), spec.to_str())
        self.assertEqual(om._stack[0][1], data)
        self.assertIn((spec, ([], Learning.ASSUMPTION_WEAKENING)), om._visited_nodes)
        om.enqueue_new_tasks(spec_1, data_1)
        self.assertEqual(len(om._stack), 2)
        self.assertEqual(len(om._visited_nodes), 2)
        self.assertEqual(om._stack[1][0].to_str(), spec_1.to_str())
        self.assertEqual(om._stack[1][1], data_1)
        self.assertIn((spec_1, ([ct], Learning.ASSUMPTION_WEAKENING)), om._visited_nodes)
        om.enqueue_new_tasks(spec_2, data_2)
        self.assertEqual(len(om._stack), 3)
        self.assertEqual(len(om._visited_nodes), 3)
        self.assertEqual(om._stack[2][0].to_str(), spec_2.to_str())
        self.assertEqual(om._stack[2][1], data_2)
        self.assertIn((spec_2, ([ct], Learning.ASSUMPTION_WEAKENING)), om._visited_nodes)

    def test_enqueue_new_tasks_different(self):
        om = OrchestrationManagerSyntacticEquivalence()
        case_study_path = '../input-files/case-studies/spectra/strengthened/minepump'
        spec_1: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        data_1: RepairData = RepairData(trace, [], Learning.ASSUMPTION_WEAKENING, [], 0, 0)
        om.initialise_learning_tasks(spec_1, data_1)
        self.assertEqual(len(om._stack), 1)
        self.assertEqual(len(om._visited_nodes), 1)
        self.assertEqual(om._stack[0][0].to_str(), spec_1.to_str())
        self.assertEqual(om._stack[0][1], data_1)
        self.assertIn((spec_1, ([], Learning.ASSUMPTION_WEAKENING)), om._visited_nodes)
        spec_2: SpectraSpecification = SpectraSpecification.from_file("./test_files/minepump_aw_methane.spectra")
        ct2 = CounterTrace(raw_trace=ct_raw_trace, raw_path=ct_path, name=ct_name)
        data_2 = RepairData(trace, [ct2], Learning.ASSUMPTION_WEAKENING, [deepcopy(spec_1)], 0, 0)
        om.enqueue_new_tasks(spec_2, data_2)
        self.assertEqual(len(om._stack), 2)
        self.assertEqual(len(om._visited_nodes), 2)
        self.assertEqual(om._stack[1][0].to_str(), spec_2.to_str())
        self.assertEqual(om._stack[1][1], data_2)
        self.assertIn((spec_2, ([ct2], Learning.ASSUMPTION_WEAKENING)), om._visited_nodes)

    def test_has_next(self):
        om = OrchestrationManagerSyntacticEquivalence()
        case_study_path = '../input-files/case-studies/spectra/strengthened/minepump'
        spec_1: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        data_1: RepairData = RepairData(trace, [], Learning.ASSUMPTION_WEAKENING, [], 0, 0)
        self.assertFalse(om.has_next())
        om.initialise_learning_tasks(spec_1, data_1)
        self.assertTrue(om.has_next())
        spec_2: SpectraSpecification = SpectraSpecification.from_file("./test_files/minepump_aw_methane.spectra")
        ct2 = CounterTrace(raw_trace=ct_raw_trace, raw_path=ct_path, name=ct_name)
        data_2 = RepairData(trace, [ct2], Learning.ASSUMPTION_WEAKENING, [deepcopy(spec_1)], 0, 0)
        om.enqueue_new_tasks(spec_2, data_2)
        self.assertTrue(om.has_next())
        extracted_spec_1, extracted_data_1 = om.get_next()
        self.assertTrue(om.has_next())
        extracted_spec_2, extracted_data_2 = om.get_next()
        self.assertFalse(om.has_next())

    def test_get_next(self):
        om = OrchestrationManagerSyntacticEquivalence()
        case_study_path = '../input-files/case-studies/spectra/strengthened/minepump'
        spec_1: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        data_1: RepairData = RepairData(trace, [], Learning.ASSUMPTION_WEAKENING, [], 0, 0)
        om.initialise_learning_tasks(spec_1, data_1)
        spec_2: SpectraSpecification = SpectraSpecification.from_file("./test_files/minepump_aw_methane.spectra")
        ct2 = CounterTrace(raw_trace=ct_raw_trace, raw_path=ct_path, name=ct_name)
        data_2 = RepairData(trace, [ct2], Learning.ASSUMPTION_WEAKENING, [deepcopy(spec_1)], 0, 0)
        om.enqueue_new_tasks(spec_2, data_2)
        extracted_spec_1, extracted_data_1 = om.get_next()
        self.assertEqual(extracted_spec_1.to_str(), spec_1.to_str())
        self.assertEqual(extracted_data_1, data_1)
        self.assertEqual(len(om._stack), 1)
        extracted_spec_2, extracted_data_2 = om.get_next()
        self.assertEqual(extracted_spec_2.to_str(), spec_2.to_str())
        self.assertEqual(extracted_data_2, data_2)
        self.assertEqual(len(om._stack), 0)
        with self.assertRaises(IndexError):
            extracted_spec_3, extracted_data_3 = om.get_next()


class TestGraphEdgeAnnotationDegradesGracefully(BaseTestCase):
    """
    The debug graph must never be able to end a repair run.

    `_add_edge_data_to_graph` labels each edge with whatever record of the
    transition exists - a deadlock completion, or the last adaptation. Both were
    indexed unconditionally, so a transition carrying neither ended the whole
    search with `IndexError: list index out of range` from inside graph
    bookkeeping. That is reachable whenever a learner dead-ends before producing
    any counter-trace, which FastLAS does far more often than ILASP because it
    returns a single solution per step. Losing an annotation is an acceptable
    cost; losing the run is not.
    """

    def setUp(self):
        case_study_path = '../input-files/case-studies/spectra/strengthened/minepump'
        self.spec = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        self.trace = read_file_lines(f"{case_study_path}/violation_trace.txt")

    def _data(self, learning_type=Learning.ASSUMPTION_WEAKENING,
              counter_traces=None, adaptation_history=None) -> RepairData:
        # Keyword arguments deliberately: the fourth positional parameter is
        # `spec_history`, not `adaptation_history`, and passing the latter
        # positionally silently populates the wrong field.
        return RepairData(trace=self.trace,
                          counter_traces=counter_traces or [],
                          learning_type=learning_type,
                          adaptation_history=adaptation_history or [])

    def _edge_between(self, om, prev_data, data):
        """Enqueue a transition and return the attributes of the edge it drew."""
        om.initialise_learning_tasks(self.spec, prev_data)
        prev = (self.spec, prev_data)
        other = deepcopy(self.spec)
        other.remove_formula("assumption2_1")
        om.enqueue_new_tasks(other, data, prev=prev)
        edges = list(om._graph.edges(data=True))
        self.assertTrue(edges, "no edge was added to the graph")
        return edges[-1][2]

    def test_transition_with_neither_record_still_draws_an_edge(self):
        """The regression: this raised IndexError instead of adding an edge."""
        om = OrchestrationManagerSyntacticEquivalence()
        attrs = self._edge_between(om, self._data(), self._data())
        self.assertIn("details", attrs)

    def test_transition_with_only_an_adaptation_history_is_labelled_with_it(self):
        om = OrchestrationManagerSyntacticEquivalence()
        attrs = self._edge_between(
            om,
            self._data(adaptation_history=[["some_adaptation"]]),
            self._data())
        self.assertEqual(["some_adaptation"], attrs.get("last_adaptation"))

    def test_counter_traces_still_produce_the_deadlock_annotation(self):
        """The informative path must be unchanged by the guard."""
        ct1 = CounterTrace(ct_raw_trace, ct_path, ct_name)
        ct2 = CounterTrace(ct_raw_trace.replace("holds_at(pump,1", "not_holds_at(pump,1"),
                           ct_path, ct_name)
        om = OrchestrationManagerSyntacticEquivalence()
        attrs = self._edge_between(om,
                                   self._data(counter_traces=[ct1]),
                                   self._data(counter_traces=[ct2]))
        self.assertIn("deadlock_completion", attrs)
