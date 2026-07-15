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
        case_study_path = '../input-files/case-studies/spectra/minepump'
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
        case_study_path = '../input-files/case-studies/spectra/minepump'
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
        case_study_path = '../input-files/case-studies/spectra/minepump'
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
        case_study_path = '../input-files/case-studies/spectra/minepump'
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
        case_study_path = '../input-files/case-studies/spectra/minepump'
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
        case_study_path = '../input-files/case-studies/spectra/minepump'
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
