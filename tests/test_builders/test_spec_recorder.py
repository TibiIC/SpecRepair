from unittest import TestCase

from spec_repair.components.recorders.unique_spec_recorder import UniqueSpecRecorder
from spec_repair.model.spectra_specification import SpectraSpecification
from tests.test_common_utility_strings.specs import *


class TestSpecRecorder(TestCase):
    def test_add_same_and_similar(self):
        recorder = UniqueSpecRecorder()
        spec_1 = SpectraSpecification.from_str(spec_perf)
        spec_2 = SpectraSpecification.from_str(spec_fixed_perf)
        id = recorder.add(spec_1)
        self.assertEqual(0, id)
        id = recorder.add(spec_1)
        self.assertEqual(0, id)
        id = recorder.add(spec_2)
        self.assertEqual(0, id)

    def test_add_same_and_different(self):
        recorder = UniqueSpecRecorder()
        spec_1 = SpectraSpecification.from_str(spec_perf)
        spec_2 = SpectraSpecification.from_str(spec_fixed_imperf)
        id = recorder.add(spec_1)
        self.assertEqual(0, id)
        id = recorder.add(spec_1)
        self.assertEqual(0, id)
        id = recorder.add(spec_2)
        self.assertEqual(1, id)

    def test_add_same_similar_and_different(self):
        recorder = UniqueSpecRecorder()
        spec_1 = SpectraSpecification.from_str(spec_perf)
        spec_2 = SpectraSpecification.from_str(spec_fixed_perf)
        spec_3 = SpectraSpecification.from_str(spec_fixed_imperf)
        id = recorder.add(spec_1)
        self.assertEqual(0, id)
        id = recorder.add(spec_2)
        self.assertEqual(0, id)
        id = recorder.add(spec_3)
        self.assertEqual(1, id)
