import io
import os
from unittest import TestCase
from unittest.mock import patch

from spec_repair.components.repair_orchestrator import RepairOrchestrator
from spec_repair.components.spec_learner import SpecLearner
from spec_repair.components.spec_oracle import SpecOracle
from spec_repair.util.file_util import write_file, read_file_lines
from spec_repair.util.spec_util import format_spec


class TestRepairOrchestrator(TestCase):

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

    @patch('sys.stdin', io.StringIO('1\n0\n1\n'))
    def test_repair_spec_minepump(self):
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/Minepump/minepump_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/minepump_strong_auto_violation.txt")
        expected_spec: list[str] = format_spec(read_file_lines(
            './test_files/minepump_aw_methane_gw_methane_fix.spectra'))

        repairer: RepairOrchestrator = RepairOrchestrator(SpecLearner(), SpecOracle())
        new_spec = repairer.repair_spec(spec, trace)
        write_file("./test_files/out/minepump_test_fix.spectra", new_spec)
        self.assertEqual(expected_spec, new_spec)

    @patch('sys.stdin', io.StringIO('3\n0\n5\n'))
    def test_repair_spec_minepump_ev(self):
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/Minepump/minepump_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/minepump_strong_auto_violation.txt")
        expected_spec: list[str] = format_spec(read_file_lines(
            './test_files/minepump_aw_ev_gw_ev_fix.spectra'))

        repairer: RepairOrchestrator = RepairOrchestrator(SpecLearner(), SpecOracle())
        new_spec = repairer.repair_spec(spec, trace)
        write_file("./test_files/out/minepump_test_fix.spectra", new_spec)
        self.assertEqual(expected_spec, new_spec)

    @patch('sys.stdin', io.StringIO('5\n'))
    def test_repair_spec_arbiter_ev(self):
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/Arbiter/Arbiter_FINAL_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/arbiter_strong_auto_violation.txt")
        expected_spec: list[str] = format_spec(read_file_lines(
            './test_files/arbiter_aw_ev.spectra'))

        repairer: RepairOrchestrator = RepairOrchestrator(SpecLearner(), SpecOracle())
        new_spec = repairer.repair_spec(spec, trace)
        write_file("./test_files/out/arbiter_test_fix.spectra", new_spec)
        self.assertEqual(expected_spec, new_spec)

    @patch('sys.stdin', io.StringIO('0\n'))
    def test_repair_spec_lift_aw_b1(self):
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/lift_FINAL_NEW_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/lift_strong_auto_violation.txt")
        expected_spec: list[str] = format_spec(read_file_lines(
            './test_files/lift_weakenings/lift_aw_b1.spectra'))

        repairer: RepairOrchestrator = RepairOrchestrator(SpecLearner(), SpecOracle())
        new_spec = repairer.repair_spec(spec, trace)
        write_file("./test_files/out/lift_test_fix.spectra", new_spec)
        self.assertEqual(expected_spec, new_spec)

    @patch('sys.stdin', io.StringIO('3\n'))
    def test_repair_spec_lift_aw_f1(self):
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/lift_FINAL_NEW_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/lift_strong_auto_violation.txt")
        expected_spec: list[str] = format_spec(read_file_lines(
            './test_files/lift_weakenings/lift_aw_f1.spectra'))

        repairer: RepairOrchestrator = RepairOrchestrator(SpecLearner(), SpecOracle())
        new_spec = repairer.repair_spec(spec, trace)
        write_file("./test_files/out/lift_test_fix.spectra", new_spec)
        self.assertEqual(expected_spec, new_spec)

    @patch('sys.stdin', io.StringIO('4\n'))
    def test_repair_spec_lift_aw_c(self):
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/lift_FINAL_NEW_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/lift_strong_auto_violation.txt")
        expected_spec: list[str] = format_spec(read_file_lines(
            './test_files/lift_weakenings/lift_aw_c.spectra'))

        repairer: RepairOrchestrator = RepairOrchestrator(SpecLearner(), SpecOracle())
        new_spec = repairer.repair_spec(spec, trace)
        write_file("./test_files/out/lift_test_fix.spectra", new_spec)
        self.assertEqual(expected_spec, new_spec)

    @patch('sys.stdin', io.StringIO('7\n'))
    def test_repair_spec_lift_ev(self):
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/lift_FINAL_NEW_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/lift_strong_auto_violation.txt")
        expected_spec: list[str] = format_spec(read_file_lines(
            './test_files/lift_weakenings/lift_aw_ev.spectra'))

        repairer: RepairOrchestrator = RepairOrchestrator(SpecLearner(), SpecOracle())
        new_spec = repairer.repair_spec(spec, trace)
        write_file("./test_files/out/lift_test_fix.spectra", new_spec)
        self.assertEqual(expected_spec, new_spec)
