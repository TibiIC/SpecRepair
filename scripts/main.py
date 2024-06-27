from spec_repair.components.repair_orchestrator import RepairOrchestrator
from spec_repair.components.spec_learner import SpecLearner
from spec_repair.components.spec_oracle import SpecOracle
from spec_repair.util.file_util import read_file_lines, write_file
from spec_repair.util.spec_util import format_spec

spec: list[str] = format_spec(read_file_lines(
    '../input-files/examples/Minepump/minepump_strong.spectra'))
trace: list[str] = read_file_lines(
    "../tests/test_files/minepump_strong_auto_violation.txt")
expected_spec: list[str] = format_spec(read_file_lines(
    '../tests/test_files/minepump_aw_methane_gw_methane_fix.spectra'))

repairer: RepairOrchestrator = RepairOrchestrator(SpecLearner(), SpecOracle())
new_spec = repairer.repair_spec(spec, trace)
write_file("../tests/test_files/out/minepump_test_fix.spectra", new_spec)
