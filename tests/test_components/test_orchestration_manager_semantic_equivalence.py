from copy import deepcopy
from typing import Any

from spec_repair.enums import Learning
from spec_repair.components.orchestration_managers import OrchestrationManagerSemanticEquivalence
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file_lines
from tests.base_test_case import BaseTestCase


class TestOrchestrationManagerSemanticEquivalence(BaseTestCase):
    def test_initialise_learning_tasks(self):
        om = OrchestrationManagerSemanticEquivalence()
        case_study_path = '../input-files/case-studies/spectra/minepump'
        spec: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        data: Any = (trace, [], Learning.ASSUMPTION_WEAKENING, [], 0, 0)
        # Check that the stack and visited nodes list are empty
        self.assertEqual(len(om._stack), 0)
        self.assertEqual(len(om._visited_nodes_list), 0)
        om.initialise_learning_tasks(spec, data)
        # Check that the stack and visited nodes list are now populated
        self.assertEqual(len(om._stack), 1)
        self.assertEqual(len(om._visited_nodes_list), 1)
        self.assertEqual(om._stack[0][0].to_str(), spec.to_str())
        self.assertEqual(om._stack[0][1], data)
        self.assertEquals(om._visited_nodes_list[0][0].to_str(), spec.to_str())
        self.assertEquals(om._visited_nodes_list[0][1], ([], Learning.ASSUMPTION_WEAKENING))

    def test_enqueue_new_tasks_same(self):
        om = OrchestrationManagerSemanticEquivalence()
        case_study_path = '../input-files/case-studies/spectra/minepump'
        spec: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        data: Any = (trace, [], Learning.ASSUMPTION_WEAKENING, [], 0, 0)
        om.initialise_learning_tasks(spec, data)
        om.enqueue_new_tasks(deepcopy(spec), deepcopy(data))
        self.assertEqual(len(om._stack), 1)
        om.enqueue_new_tasks(deepcopy(spec), deepcopy(data))
        self.assertEqual(len(om._stack), 1)

    def test_enqueue_new_tasks_different(self):
        self.fail()

    def test_has_next(self):
        self.fail()

    def test_get_next(self):
        self.fail()
