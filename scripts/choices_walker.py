import os.path
import re
import shutil
from typing import Optional, List, Set

from spec_repair.config import PROJECT_PATH
from spec_repair.helpers.spec_recorder import SpecRecorder
from spec_repair.wrappers.script import Script
from spec_repair.wrappers.spec import Spec
from spec_repair.util.file_util import read_file
from spec_repair.old.util_titus import semantically_identical_spot

ideal_spec_file_path = f"{PROJECT_PATH}/input-files/examples/Minepump/minepump_FINAL.spectra"
saved_specs_folder_path = f"{PROJECT_PATH}/scripts/saved_specs/minepump_test"


def save_new_spec_if_semantically_unique(spec_id, fixed_spec_file_path):
    _, file_extension = os.path.splitext(fixed_spec_file_path)
    if not os.path.exists(saved_specs_folder_path):
        os.makedirs(saved_specs_folder_path)

    saved_spec_file_path = os.path.join(saved_specs_folder_path, f"{spec_id}{file_extension}")
    if not os.path.exists(saved_spec_file_path):
        shutil.copy(fixed_spec_file_path, saved_spec_file_path)


class ChoicesWalker:

    def run_script_with_choices(self):
        run_parameters: list[int] = [0]
        spec_recorder: SpecRecorder = SpecRecorder()
        spec_path_recorder: Set[Optional[str]] = {None}
        ideal_spec = Spec(read_file(ideal_spec_file_path))
        spec_recorder.add(ideal_spec)

        script = Script(args=["python", f"{PROJECT_PATH}/spec_repair/old_experiments.py"])
        run_parameters, max_options = self.run_weakening_with_choices(run_parameters, script, spec_recorder,
                                                                      spec_path_recorder)
        next_run = self.get_next_run(run_parameters, max_options)

        while next_run:
            print(f"Moving to next run {next_run}")
            print("#" * 25)
            run_parameters, max_options = self.run_weakening_with_choices(next_run, script, spec_recorder,
                                                                          spec_path_recorder)
            next_run = self.get_next_run(run_parameters, max_options)

        print(f"No new runs possible")
        print("#" * 25)

    def run_weakening_with_choices(self, run_parameters, script, spec_recorder, spec_path_recorder):
        max_options: list[int] = []
        fixed_spec_file_path: Optional[str] = None
        script.start()
        step = 0
        output = script.read_next_line()
        while output:
            print(output)
            max_choice = self.get_max_choice(output)
            fixed_spec_file_path = self.get_fixed_specification_path(output) or fixed_spec_file_path
            if max_choice is not None:  # it can be 0
                max_options.append(max_choice)
                choice = self.get_choice(run_parameters, step)
                step += 1
                print(f"Choice taken: '{choice}'")
                script.write_line(str(choice))
            output = script.read_next_line()
        script.end()
        # Ensure the spec is saved at a new unique path
        assert fixed_spec_file_path not in spec_path_recorder
        spec_path_recorder.add(fixed_spec_file_path)
        # For testing purposes
        self.max_options = max_options
        run_parameters = self.adjust_list_size(run_parameters, max_options)
        print("#" * 25)
        print(
            f"Last run ended with {run_parameters} and max_options={max_options}, at file path={fixed_spec_file_path}.")
        semantical_cmp = semantically_identical_spot(fixed_spec_file_path, ideal_spec_file_path)
        print(f"This run is {semantical_cmp}.")
        fixed_spec = Spec(read_file(fixed_spec_file_path))
        spec_id = spec_recorder.add(fixed_spec)
        save_new_spec_if_semantically_unique(spec_id, fixed_spec_file_path)
        # TODO: Add intermediary specification ID
        print(f"SPEC ID: {spec_id}.")
        return run_parameters, max_options

    def get_choice(self, run: list[int], step: int):
        if step >= len(run):
            return 0
        return run[step]

    def get_max_choice(self, output) -> Optional[int]:
        match = re.search(r'Enter the index of your choice \[\d+-(\d+)\]:', output)
        if match:
            return int(match.group(1))
        return None

    def get_fixed_specification_path(self, line: str) -> Optional[str]:
        match = re.match(r"^Fixed specification: (.+)$", line)
        if match:
            return match.group(1)
        return None

    def get_next_runs(self, run: list[int], max_options: list[int]) -> list[list[int]]:
        new_runs = []
        new_run = run
        while new_run is not None:
            new_run = self.get_next_run(new_run, max_options[:len(new_run)])
            if new_run is not None:
                new_run = self.cut_tail_of_zeros(new_run)
                new_runs.append(new_run)
        return new_runs

    def cut_tail_of_zeros(self, lst: list[int]) -> list[int]:
        last_non_zero_index = len(lst) - 1
        while last_non_zero_index >= 0 and lst[last_non_zero_index] == 0:
            last_non_zero_index -= 1

        return lst[:last_non_zero_index + 1]

    def get_next_run(self, run: list[int], max_options: list[int]) -> Optional[list[int]]:
        if len(run) != len(max_options):
            run = self.adjust_list_size(run, max_options)
            # raise ValueError(f"Run {run} and maximum options {max_options} are not of equal length!")
        if any(choice > max_option for choice, max_option in zip(run, max_options)):
            raise ValueError(
                f"Run {run} contains an illegal value (larger than one of the maximum options in {max_options})")

        new_run = run.copy()
        self.increment_and_compare(new_run, max_options)

        if all(choice == 0 for choice in new_run):
            return None
        else:
            return new_run

    def adjust_list_size(self, target_list, reference_list):
        if len(target_list) < len(reference_list):
            target_list.extend([0] * (len(reference_list) - len(target_list)))
        elif len(target_list) > len(reference_list):
            target_list = target_list[:len(reference_list)]
        return target_list

    def increment_and_compare(self, list_to_increment: List[int], max_list: List[int]):
        for i in reversed(range(len(list_to_increment))):
            list_to_increment[i] += 1
            if list_to_increment[i] > max_list[i]:
                list_to_increment[i] = 0
            else:
                return


if __name__ == '__main__':
    choices_walker = ChoicesWalker()
    choices_walker.run_script_with_choices()
    print(choices_walker.max_options)
