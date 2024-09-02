import copy
from unittest import TestCase

from spec_repair.helpers.spec_recorder import SpecRecorder
from spec_repair.wrappers.spec import Spec
from tests.test_common_utility_strings.specs import *


class TestSpecRecorder(TestCase):
    def test_add_same_and_similar(self):
        recorder = SpecRecorder()
        spec_1 = Spec(copy.deepcopy(spec_perf))
        spec_2 = Spec(copy.deepcopy(spec_fixed_perf))
        id = recorder.add(spec_1)
        self.assertEqual(0, id)
        id = recorder.add(spec_1)
        self.assertEqual(0, id)
        id = recorder.add(spec_2)
        self.assertEqual(0, id)

    def test_add_same_and_different(self):
        recorder = SpecRecorder()
        spec_1 = Spec(copy.deepcopy(spec_perf))
        spec_2 = Spec(copy.deepcopy(spec_fixed_imperf))
        id = recorder.add(spec_1)
        self.assertEqual(0, id)
        id = recorder.add(spec_1)
        self.assertEqual(0, id)
        id = recorder.add(spec_2)
        self.assertEqual(1, id)

    def test_add_same_similar_and_different(self):
        recorder = SpecRecorder()
        spec_1 = Spec(copy.deepcopy(spec_perf))
        spec_2 = Spec(copy.deepcopy(spec_fixed_perf))
        spec_3 = Spec(copy.deepcopy(spec_fixed_imperf))
        id = recorder.add(spec_1)
        self.assertEqual(0, id)
        id = recorder.add(spec_2)
        self.assertEqual(0, id)
        id = recorder.add(spec_3)
        self.assertEqual(1, id)
