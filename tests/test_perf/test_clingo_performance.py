import os
import pytest
import time

from spec_repair.old_experiments import run_clingo

current_directory = os.path.dirname(os.path.abspath(__file__))
las_directory_path = os.path.join(current_directory, "lp_files")
# List all files in the current directory with full paths
lp_file_paths: list[str] = [os.path.join(las_directory_path, f) for f in os.listdir(las_directory_path)
                            if f.endswith(".lp")]
exp_types: list[str] = ["assumption", "guarantee"]
lp_file = lp_file_paths[0]

@pytest.mark.parametrize("exp_type", exp_types)
@pytest.mark.benchmark(
    max_time=0.1,
    min_rounds=50,
    timer=time.time,
    warmup=True
)
def test_clingo_performance(benchmark, exp_type):
    benchmark(run_clingo, lp_file, True, exp_type)


if __name__ == "__main__":
    pytest.main()
