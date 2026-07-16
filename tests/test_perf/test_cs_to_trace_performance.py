import sys

import pytest
import time

sys.path.append("/Users/tg4018/Documents/PhD/SpectraASPTranslators")

from spec_repair.model.counter_trace import extract_trace

# List all files in the current directory with full paths
cs_lines: list = [
    ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
     'S0 -> DEAD {highwater:true, methane:true} / {pump:false};',
     'S0 -> DEAD {highwater:true, methane:true} / {pump:true};'],
    ['INI -> S0 {highwater:false, methane:false} / {pump:false};',
     'S0 -> S1 {highwater:false, methane:true} / {pump:false};',
     'S0 -> S1 {highwater:false, methane:true} / {pump:true};',
     'S1 -> DEAD {highwater:true, methane:true} / {pump:false};'],
]


def run_this_counter_strat_to_trace_version(lines: list[str]):
    start = "INI"
    output = ""
    trace_name_dict: dict[str, str] = {}
    # TODO: ASK TITUS what is the relationship between low caps "ini" and "ini_S" infinite traces?
    extract_trace(lines, output, start, 0, "ini", trace_name_dict)
    print(trace_name_dict)


@pytest.mark.parametrize("cs_line", cs_lines)
@pytest.mark.benchmark(
    max_time=0.1,
    min_rounds=10,
    timer=time.time,
    warmup=True
)
def test_cs_to_trace_performance(benchmark, cs_line):
    benchmark(run_this_counter_strat_to_trace_version, cs_line)


if __name__ == "__main__":
    pytest.main()
