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

    def test_semantic_mode_collapses_equivalent_specs_syntactic_keeps_them(self):
        """
        spec_perf and spec_fixed_perf are logically equivalent but written
        differently, which is exactly where the two modes must disagree:
        __eq__ is spot-backed equivalence, __hash__ is syntactic.
        """
        spec_1 = SpectraSpecification.from_str(spec_perf)
        spec_2 = SpectraSpecification.from_str(spec_fixed_perf)

        semantic = UniqueSpecRecorder(sem_equivalence=True)
        semantic.add(spec_1)
        semantic.add(spec_2)
        self.assertEqual(1, len(semantic.get_specs()))

        syntactic = UniqueSpecRecorder(sem_equivalence=False)
        syntactic.add(spec_1)
        syntactic.add(spec_2)
        self.assertEqual(2, len(syntactic.get_specs()))

    def test_semantic_mode_read_methods_see_recorded_specs(self):
        """
        Regression: semantic mode stores specs in its own list and never
        populates UniqueRecorder's set/dict, so every inherited read method used
        to report on an empty backing store - get_all_values() returned [] and
        len() returned 0 no matter how many specs had been recorded, silently
        dropping results for callers reading back via get_all_values().
        """
        for sem_equivalence in (True, False):
            with self.subTest(sem_equivalence=sem_equivalence):
                recorder = UniqueSpecRecorder(sem_equivalence=sem_equivalence)
                spec_1 = SpectraSpecification.from_str(spec_perf)
                spec_2 = SpectraSpecification.from_str(spec_fixed_imperf)
                recorder.add(spec_1)
                recorder.add(spec_2)

                self.assertEqual(2, len(recorder.get_all_values()))
                self.assertEqual(2, len(recorder))
                self.assertEqual(2, len(recorder.get_specs()))
                self.assertIn(spec_1, recorder)
                self.assertEqual(0, recorder.get_id(spec_1))
                self.assertEqual(1, recorder.get_id(spec_2))
                self.assertIsNotNone(recorder.get_element_by_id(0))
                self.assertIsNone(recorder.get_element_by_id(99))

    def test_get_all_values_is_in_insertion_order(self):
        for sem_equivalence in (True, False):
            with self.subTest(sem_equivalence=sem_equivalence):
                recorder = UniqueSpecRecorder(sem_equivalence=sem_equivalence)
                spec_1 = SpectraSpecification.from_str(spec_perf)
                spec_2 = SpectraSpecification.from_str(spec_fixed_imperf)
                recorder.add(spec_1)
                recorder.add(spec_2)
                self.assertEqual([spec_1.to_str(), spec_2.to_str()], recorder.get_specs())
