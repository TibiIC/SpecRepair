import os
import os.path
import re
import subprocess
from typing import List, Set

import jpype
from jpype.types import *

import spec_repair.wrappers.jvm  # noqa: F401 - import side effect starts the shared JVM
from spec_repair.enums import SimEnv
from spec_repair.util.asp_trace_util import pRespondsToS_substitution, simplify_assignments
from spec_repair.util.file_util import generate_temp_filename, get_line_from_file, read_file_lines, write_to_file
from spec_repair.util.formula_string_util import shift_prev_to_next
from spec_repair.util.formula_string_util import strip_vars

SpectraToolbox = jpype.JClass('cores.SpectraToolbox')
SpectraCLI = jpype.JClass('tau.smlab.syntech.Spectra.cli.SpectraCliTool')


def run_all_unrealisable_cores(spectra_str: str) -> List[Set[str]]:
    """
    Gets the names of all unrealisable cores from a given spectra specification as string.
    """
    temp_spectra_file = generate_temp_filename(ext=".spectra")
    write_to_file(temp_spectra_file, spectra_str)
    pRespondsToS_substitution(temp_spectra_file)
    # A realizable specification has no unrealisable core by definition, so the
    # exhaustive exploreAllCores search below can only ever return []. Paying a
    # single realizability check first to skip it is a large win: on ColorSort's
    # 77-formula spec exploreAllCores ran >16 minutes without returning, while
    # the realizability check answers in ~1.4s. Every other case study's spec is
    # small enough that exploreAllCores finishes in <1s either way, so this only
    # ever adds ~0.05s there. `realizable` returns None when the file isn't in a
    # form the CLI can check - deliberately fall through to the full search in
    # that case rather than assume anything.
    if realizable(temp_spectra_file, suppress=True):
        return []
    output = run_all_unrealisable_cores_raw(temp_spectra_file)
    core_nums_list: List[Set[int]] = _extract_cores(output)
    core_names_list = []
    for core_nums in core_nums_list:
        core_names = set()
        for core_num in core_nums:
            line_with_name = get_line_from_file(temp_spectra_file, core_num)
            name = line_with_name.split("--")[1].strip()
            core_names.add(name)
        core_names_list.append(core_names)
    return core_names_list


def _extract_cores(text) -> List[Set[int]]:
    # Split to get the part after "Final results:"
    parts = text.split("Final results:")
    if len(parts) < 2:
        return []

    final_section = parts[1]

    # Pattern to match lines like "Core #1 at lines < 12 15 >"
    pattern = re.compile(r'Core\s+#\d+\s+at\s+lines\s+<\s*([\d\s]*)\s*>')

    results = []
    for match in pattern.finditer(final_section):
        numbers = match.group(1).strip()
        if numbers:  # Only add non-empty sets
            num_set = {int(n) for n in numbers.split()}
            results.append(num_set)

    return results


def run_all_unrealisable_cores_raw(filename) -> str:
    filepath = f"{filename}"
    args = jpype.JArray(JString)([filepath, "--jtlv"])
    output = SpectraToolbox.exploreAllCores(args)
    return str(output)


def semantically_identical_spot(to_cmp_file, baseline_file):
    to_cmp_file = re.sub("_patterned\.spectra", ".spectra", to_cmp_file)
    assumption = equivalent_expressions("assumption|asm", to_cmp_file, baseline_file)
    if assumption is None:
        return SimEnv.Invalid
    if not assumption:
        if realizable(to_cmp_file):
            return SimEnv.Realizable
        else:
            # This should never happen:
            return SimEnv.Unrealizable
    guarantee = equivalent_expressions("guarantee|gar", to_cmp_file, baseline_file)
    if guarantee is None:
        print("Guarantees Not Working in Spot:\n" + to_cmp_file)
    if not guarantee:
        return SimEnv.IncorrectGuarantees
    return SimEnv.Success


def equivalent_expressions(exp_type, start_file, end_file):
    start_exp = extract_all_expressions_spot(exp_type, start_file)
    end_exp = extract_all_expressions_spot(exp_type, end_file)
    linux_cmd = ["ltlfilt", "-c", "-f", f"{start_exp}", "--equivalent-to", f"{end_exp}"]
    p = subprocess.Popen(linux_cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.communicate()[0]
    close_file_descriptors_of_subprocess(p)
    output = output.decode('utf-8')
    reg = re.search(r"(\d)\n", output)
    if not reg:
        return None
    result = reg.group(1)
    if result == "0":
        return False
    if result == "1":
        return True
    return None


def close_file_descriptors_of_subprocess(p):
    if p.stdin:
        p.stdin.close()
    if p.stdout:
        p.stdout.close()
    if p.stderr:
        p.stderr.close()


def extract_all_expressions_spot(exp_type, file, return_list=False):
    spec = read_file_lines(file)
    variables = strip_vars(spec)
    spec = simplify_assignments(spec, variables)
    expressions = [re.sub(r"\s", "", spec[i + 1]) for i, line in enumerate(spec) if re.search("^" + exp_type, line)]
    expressions = [shift_prev_to_next(formula, variables) for formula in expressions]
    if any([re.search("PREV", x) for x in expressions]):
        raise Exception("There are still PREVs in the expressions!")
    if return_list:
        return [re.sub(";", "", x) for x in expressions]
    exp_conj = re.sub(";", "", '&'.join(expressions))
    return exp_conj


def violations_in_initial_conditions(file):
    '''
    This is because the Spectra CLI is inconsistent in throwing errors relating to initial conditions. Initial
    conditions cannot refer to primed (next) variables. Initial assumptions cannot refer to system variables.
    :param file:
    :return:
    '''
    spec = read_file_lines(file)
    sys_vars = strip_vars(spec, "sys")
    inits = [(line, spec[i + 1]) for i, line in enumerate(spec) if
             line.find("--") >= 0 and not re.search(r"G|F|pRespondsToS", spec[i + 1])]
    if any([bool(re.search(r"next|X", tup[1])) for tup in inits]):
        print("Initial expression contains primed (next) variables.")
        return True
    sys_vars = [re.escape(var) for var in sys_vars]
    init_ass = [tup[1] for tup in inits if re.search(r"assumption", tup[0])]
    if any([re.search(r'|'.join(sys_vars), ass) for ass in init_ass]):
        print("Initial assumption refers to system variables.")
        return True
    return False


def realizable(file, suppress=False):
    if violations_in_initial_conditions(file):
        print("Spectra file in wrong format for CLI realizability check: (initial conditions)")
        print(file)
        return None
    file = pRespondsToS_substitution(file)
    args = ["-i", file, "--jtlv"]
    output = run_spectra_cli(args)
    if re.search("Result: Specification is unrealizable", output):
        return False
    elif re.search("Result: Specification is realizable", output):
        return True
    if not suppress:
        print(output)
    print("Spectra file in wrong format for CLI realizability check:")
    print(file)
    return None


def synthesise_extract_counter_strategies(file):
    if violations_in_initial_conditions(file):
        print("Spectra file in wrong format for CLI realizability check: (initial conditions)")
        print(file)
        return None
    file = pRespondsToS_substitution(file)
    args = ["-i", file, "--counter-strategy", "--jtlv"]
    output = run_spectra_cli(args)
    return output


def synthesise_check_realisability_only(file):
    """
    Same as synthesise_extract_counter_strategies, minus --counter-strategy:
    for callers that only need the yes/no realizability verdict (its
    "Result: Specification is (un)?realizable" line) and never touch the
    strategy. --counter-strategy makes the BDD-based synthesis compute and
    materialize a full counter-strategy even when nothing downstream reads
    it, which can be dramatically more expensive - confirmed on a spec with
    a large boolean-expanded state space where --counter-strategy ran the
    JVM's BDD engine past 12.8M nodes and out of heap memory, while this
    (otherwise identical) call completed in seconds.
    """
    if violations_in_initial_conditions(file):
        print("Spectra file in wrong format for CLI realizability check: (initial conditions)")
        print(file)
        return None
    file = pRespondsToS_substitution(file)
    args = ["-i", file, "--jtlv"]
    output = run_spectra_cli(args)
    return output


def synthesise_controller(spec_file_path, output_folder_path, suppress=False) -> bool:
    if violations_in_initial_conditions(spec_file_path):
        print("Spectra file in wrong format for CLI realizability check: (initial conditions)")
        print(spec_file_path)
        return False
    # Check if parent directory exists
    parent_dir = os.path.dirname(output_folder_path)
    if not os.path.exists(parent_dir):
        print(f"Error: Path to output folder does not exist: {parent_dir}")
        return False

    spec_file_path = pRespondsToS_substitution(spec_file_path)
    args = ["-i", spec_file_path, "--jtlv", '-s', '--static', '-o', output_folder_path]
    output = run_spectra_cli(args)
    if re.search("Error: Cannot synthesize an unrealizable specification", output):
        print("Error: Cannot synthesize an unrealizable specification")
        return False
    elif re.search("Result: Specification is realizable", output):
        return True
    if not suppress:
        print(output)
    print("Spectra file in wrong format for CLI realizability check:")
    print(spec_file_path)
    return False



_BDD_REORDER_ENV = "SPEC_REPAIR_BDD_REORDER"
_reorder_state = {"applied": False}


def _maybe_enable_bdd_reorder() -> None:
    """
    Turn on dynamic BDD variable reordering, when asked for explicitly.

    We run Spectra with `--jtlv`, which selects the pure-Java BDD package,
    because the default CUDD backend cannot load here - measured on macOS and on
    the Linux GPU boxes alike, both failing with
    `NullPointerException: Cannot load from int array because "attrSizes" is
    null`. The JTLV factory runs a node table of 200033 that never grows: each
    collection frees 40-60% of it, which is above the threshold at which
    JavaBDD would resize, but the space refills within milliseconds. Measured on
    amba: ~186 collections/second, indefinitely. It never errors and never
    finishes.

    Variable order is what actually drives BDD size, so sifting is the lever
    that can move a specification out of that equilibrium. It is
    semantics-preserving - reordering changes the representation, not the
    function - so a realisability verdict cannot change.

    **Opt-in, and deliberately not the default.** Reordering can change *which*
    counter-strategy Spectra returns among the many valid ones, and the search
    branches on the counter-strategy it is given. Every repair found remains a
    genuine repair, but two runs either side of this flag are not
    result-comparable, so it must not turn itself on underneath a sweep already
    in progress. Set SPEC_REPAIR_BDD_REORDER=1 to enable.
    """
    if _reorder_state["applied"] or os.environ.get(_BDD_REORDER_ENV, "") != "1":
        return
    _reorder_state["applied"] = True
    try:
        jpype.JClass("tau.smlab.syntech.jtlv.Env").enableReorder()
        print("BDD dynamic variable reordering enabled.")
    except Exception as e:  # noqa: BLE001 - never let a tuning knob break a run
        print(f"Could not enable BDD reordering ({type(e).__name__}); continuing without it.")


def run_spectra_cli(args: list[str]) -> str:
    """
    Run a Java main method and capture its printed output as a string.

    Parameters:
    - args: list of string arguments to pass to main()

    Returns:
    - Captured standard output as a Python string.
    """
    if not jpype.isJVMStarted():
        raise RuntimeError("JVM is not started. Start it with jpype.startJVM() before calling this function.")

    # Import Java system classes
    java_lang_System = jpype.JClass("java.lang.System")
    java_io_ByteArrayOutputStream = jpype.JClass("java.io.ByteArrayOutputStream")
    java_io_PrintStream = jpype.JClass("java.io.PrintStream")

    # Backup original System.out
    original_out = java_lang_System.out

    # Prepare streams to capture output
    baos = java_io_ByteArrayOutputStream()
    ps = java_io_PrintStream(baos)

    # Redirect System.out to our PrintStream
    java_lang_System.setOut(ps)

    try:
        _maybe_enable_bdd_reorder()

        # Load the Java class and convert args to Java String[]
        java_args = JArray(JString)(args)

        # Call the main method
        SpectraCLI.main(java_args)

        # Flush and get captured output as bytes
        ps.flush()
        output_bytes = baos.toByteArray()

        # Decode bytes to Python string
        output_str = bytes(output_bytes).decode("utf-8")

    finally:
        # Restore original System.out no matter what
        java_lang_System.setOut(original_out)

    return output_str
