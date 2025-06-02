from unittest import TestCase

from scripts.old_scripts.choices_walker import ChoicesWalker


class TestChoicesWalker(TestCase):
    choices_walker = ChoicesWalker()

    def test_cut_tail_of_zeros(self):
        res = self.choices_walker.cut_tail_of_zeros([0, 1, 0])
        self.assertEqual(res, [0, 1])

        res = self.choices_walker.cut_tail_of_zeros([0, 2, 0])
        self.assertEqual(res, [0, 2])

        res = self.choices_walker.cut_tail_of_zeros([1, 1, 0])
        self.assertEqual(res, [1, 1])

        res = self.choices_walker.cut_tail_of_zeros([2, 0, 0])
        self.assertEqual(res, [2])

    def test_get_next_runs(self):
        next_runs = self.choices_walker.get_next_runs([0, 0, 0],
                                                      [2, 3, 2])
        self.assertListEqual(next_runs, [
            [0, 0, 1],
            [0, 0, 2],
            [0, 1],
            [0, 2],
            [0, 3],
            [1],
            [2],
        ])

    def test_get_next_runs_2(self):
        next_runs = self.choices_walker.get_next_runs([2, 0, 0],
                                                      [2, 3, 2])
        self.assertListEqual(next_runs, [
            [2, 0, 1],
            [2, 0, 2],
            [2, 1],
            [2, 2],
            [2, 3]
        ])

    def test_get_next_runs_last(self):
        next_run = self.choices_walker.get_next_runs([2, 3, 1],
                                                     [2, 3, 2])
        self.assertListEqual(next_run, [[2, 3, 2]])

    def test_get_next_runs_empty(self):
        next_run = self.choices_walker.get_next_runs([2, 3, 2],
                                                     [2, 3, 2])
        self.assertListEqual(next_run, [])

    def test_get_next_run_0(self):
        next_run = self.choices_walker.get_next_run([],
                                                    [2, 3, 2])
        self.assertListEqual(next_run, [0, 0, 1])

    def test_get_next_run(self):
        next_run = self.choices_walker.get_next_run([0, 0, 0],
                                                    [2, 3, 2])
        self.assertListEqual(next_run, [0, 0, 1])

    def test_get_next_run_2(self):
        next_run = self.choices_walker.get_next_run([0, 0, 1],
                                                    [2, 3, 2])
        self.assertListEqual(next_run, [0, 0, 2])

    def test_get_next_run_3(self):
        next_run = self.choices_walker.get_next_run([0, 0, 2],
                                                    [2, 3, 2])
        self.assertListEqual(next_run, [0, 1, 0])

    def test_get_next_run_4(self):
        next_run = self.choices_walker.get_next_run([0, 3, 2],
                                                    [2, 3, 2])
        self.assertListEqual(next_run, [1, 0, 0])

    def test_get_next_run_none(self):
        next_run = self.choices_walker.get_next_run([2, 3, 2],
                                                    [2, 3, 2])
        self.assertIsNone(next_run)

    def test_get_next_run_trims_on_list_mismatch(self):
        next_run = self.choices_walker.get_next_run([0, 3, 2],
                                                    [2, 3])
        self.assertListEqual(next_run, [1, 0])

    def test_get_next_run_trims_on_list_mismatch_2(self):
        next_run = self.choices_walker.get_next_run([0, 3, 0],
                                                    [2, 3])
        self.assertListEqual(next_run, [1, 0])

    def test_get_next_run_extends_on_list_mismatch(self):
        next_run = self.choices_walker.get_next_run([0, 3, 2],
                                                    [2, 3, 2, 4])
        self.assertListEqual(next_run, [0, 3, 2, 1])

    def test_get_next_run_raises_assertion_on_input_list_of_illegal_value_anywhere(self):
        with self.assertRaises(ValueError):
            self.choices_walker.get_next_run([1, 4, 2], [2, 3, 2])

    def test_get_fixed_specification_path(self):
        path = self.choices_walker.get_fixed_specification_path("Fixed specification: /Users/tg4018/Documents/PhD/SpectraASPTranslators/input-files/examples/Minepump/minepump_strong_fixed_EpAZftrauf.spectra")
        self.assertEqual("/Users/tg4018/Documents/PhD/SpectraASPTranslators/input-files/examples/Minepump/minepump_strong_fixed_EpAZftrauf.spectra", path)

"""
    def test_run_script_with_choices(self):
        self.choices_walker.run_script_with_choices()
        self.assertListEqual(self.choices_walker.max_options, [2, 1, 0, 1, 1, 1, 0, 2])
"""
