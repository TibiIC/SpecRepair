import os
from unittest import TestCase

import dill

from spec_repair.components.new_spec_learner import NewSpecLearner
from spec_repair.enums import Learning


class TestILASPGWAll(TestCase):
    @classmethod
    def setUpClass(cls):
        # Change the working directory to the script's directory
        cls.original_working_directory = os.getcwd()
        test_components_dir = os.path.dirname(os.path.abspath(__file__))
        tests_dir = os.path.dirname(test_components_dir)
        os.chdir(tests_dir)

    @classmethod
    def tearDownClass(cls):
        # Restore the original working directory
        os.chdir(cls.original_working_directory)

    def test_ilasp_gw_all_minepump(self):
        with open('./test_debug/ilasp_gw_all_helper_files/minepump_debug_vars.dill', 'rb') as f:
            spec, trace, cts, learning_type, violations = dill.load(f)
        learner = NewSpecLearner()
        learner.find_all_exception_adaptations(spec, trace, cts, learning_type, violations)

    def test_ilasp_gw_all_arbiter(self):
        with open('./test_debug/ilasp_gw_all_helper_files/arbiter_debug_vars.dill', 'rb') as f:
            spec, trace, cts, learning_type, violations = dill.load(f)
        learner = NewSpecLearner()
        adaptations = learner.find_all_exception_adaptations(spec, trace, cts, learning_type, violations)

        spec.integrate_multiple(adaptations[0][1])
        learning_type = Learning.GUARANTEE_WEAKENING
        violations = learner.get_spec_violations(spec, trace, cts, learning_type)
        learner.find_all_exception_adaptations(spec, trace, cts, learning_type, violations)
