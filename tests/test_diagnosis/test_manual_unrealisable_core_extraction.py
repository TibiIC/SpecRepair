from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
from spec_repair.components.oracles.strix_gr1_revised_oracle import StrixGR1RevisedOracle
from spec_repair.diagnosis.manual_unrealisable_core_extraction import get_unrealisable_cores
from spec_repair.model.spectra_specification import SpectraSpecification
from tests.base_test_case import BaseTestCase


class TestManualUnrealisableCoreExtraction(BaseTestCase):
    def test_get_unrealisable_cores_spectra_oracle(self):
        spec = SpectraSpecification.from_file('./test_files/minepump_aw_methane.spectra')
        oracle = SpectraGR1Oracle()
        ucs = get_unrealisable_cores(spec, oracle)
        expected_ucs = [{'guarantee1_1','guarantee2_1'}]
        self.assertEqual(expected_ucs, ucs)

    def test_get_unrealisable_cores_strix_oracle(self):
        spec = SpectraSpecification.from_file('./test_files/minepump_aw_methane.spectra')
        oracle = StrixGR1RevisedOracle()
        ucs = get_unrealisable_cores(spec, oracle)
        expected_ucs = [{'guarantee1_1','guarantee2_1'}]
        self.assertEqual(expected_ucs, ucs)

    def test_get_unrealisable_cores_edge_case_spectra_oracle(self):
        spec = SpectraSpecification.from_file('./test_files/minepump_aw_pump.spectra')
        oracle = SpectraGR1Oracle()
        ucs = get_unrealisable_cores(spec, oracle)
        expected_ucs = [{'guarantee1_1','guarantee2_1'}]
        self.assertEqual(expected_ucs, ucs)

    def test_get_unrealisable_cores_edge_case_strix_oracle(self):
        spec = SpectraSpecification.from_file('./test_files/minepump_aw_pump.spectra')
        oracle = StrixGR1RevisedOracle()
        ucs = get_unrealisable_cores(spec, oracle)
        expected_ucs = []
        self.assertEqual(expected_ucs, ucs)

    def test_get_unrealisable_cores_multiple_spectra_oracle(self):
        arbiter_spec_file_path = "test_files/unrealisable_core_util_tests/arbiter_uc.spectra"
        spec = SpectraSpecification.from_file(arbiter_spec_file_path)
        oracle = SpectraGR1Oracle()
        ucs = get_unrealisable_cores(spec, oracle)
        expected_ucs = [{"guarantee1_1", "guarantee3_1"}, {"guarantee3_1", "guarantee2_1"}]
        self.assertEqual(set(frozenset(uc) for uc in expected_ucs), set(frozenset(uc) for uc in ucs))

    def test_get_unrealisable_cores_multiple_strix_oracle(self):
        arbiter_spec_file_path = "test_files/unrealisable_core_util_tests/arbiter_uc.spectra"
        spec = SpectraSpecification.from_file(arbiter_spec_file_path)
        oracle = StrixGR1RevisedOracle()
        ucs = get_unrealisable_cores(spec, oracle)
        expected_ucs = [{"guarantee1_1", "guarantee3_1"}, {"guarantee3_1", "guarantee2_1"}]
        self.assertEqual(set(frozenset(uc) for uc in expected_ucs), set(frozenset(uc) for uc in ucs))
