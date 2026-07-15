import os
import pytest
import subprocess
import time

from spec_repair.util.specification_helper import create_cmd

current_directory = os.path.dirname(os.path.abspath(__file__))
las_directory_path = os.path.join(current_directory, "las_files")
# List all files in the current directory with full paths
las_file_paths: list[str] = [os.path.join(las_directory_path, f) for f in os.listdir(las_directory_path)
                             if f.endswith(".las")]


def run_this_ILASP_version(cmd: list[str]):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()


@pytest.mark.parametrize("las_file", las_file_paths)
@pytest.mark.benchmark(
    max_time=0.1,
    min_rounds=10,
    timer=time.time,
    warmup=True
)
def test_ILASP_performance(benchmark, las_file):
    cmd = create_cmd(['ILASP', las_file])
    benchmark(run_this_ILASP_version, cmd)


if __name__ == "__main__":
    pytest.main()
