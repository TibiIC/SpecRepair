import os
import os.path
import platform
import re
import subprocess
import tempfile
from typing import List, Set

import jpype
from jpype.types import *

import spec_repair.wrappers.jvm  # noqa: F401 - import side effect starts the shared JVM
from spec_repair.components.unrealisable_core_cache import UnrealisableCoreCache
from spec_repair.enums import SimEnv
from spec_repair.util.asp_trace_util import pRespondsToS_substitution, simplify_assignments
from spec_repair.util.file_util import generate_temp_filename, get_line_from_file, read_file_lines, write_to_file
from spec_repair.util.formula_string_util import shift_prev_to_next
from spec_repair.util.spectra_text_util import canonical_spectra_text
from spec_repair.util.formula_string_util import strip_vars

SpectraToolbox = jpype.JClass('cores.SpectraToolbox')
SpectraCLI = jpype.JClass('tau.smlab.syntech.Spectra.cli.SpectraCliTool')


_UC_CACHE_ENV = "SPEC_REPAIR_UC_CACHE"

# One cache for the process, owned here rather than hidden inside the function.
# Swap it or call .reset() to control it; SPEC_REPAIR_UC_CACHE=0 starts it off.
unrealisable_core_cache = UnrealisableCoreCache(
    enabled=os.environ.get(_UC_CACHE_ENV, "1").strip() != "0")


def _bdd_package_name() -> str:
    return "jtlv" if _bdd_args() else "cudd"


def run_all_unrealisable_cores(spectra_str: str) -> List[Set[str]]:
    """
    Gets the names of all unrealisable cores from a given spectra specification as string.

    Memoised through `unrealisable_core_cache`, because the search is the most
    expensive call in the system - exponential in the number of expressions, and
    measured on genbuf at over thirteen hours inside `Checker$Memoize.seek`
    without returning - and the same specification text reaches it repeatedly.

    The *key* is canonicalised so that `asm A; gar B` and `gar B; asm A` share an
    entry. The *search* is still given `spectra_str` exactly as it arrived:
    `_search_all_unrealisable_cores` maps Spectra's answer back onto names by
    line number, so analysing reordered text would attach the wrong names to a
    core. Checked against the real tool rather than assumed - permuting the
    formulas of a two-core specification returns the same cores every time.
    """
    return unrealisable_core_cache.lookup_or_compute(
        canonical_spectra_text(spectra_str),
        _bdd_package_name(),
        lambda: _search_all_unrealisable_cores(spectra_str))


def _search_all_unrealisable_cores(spectra_str: str) -> List[Set[str]]:
    """The actual search, with no memoisation of its own."""
    temp_spectra_file = generate_temp_filename(ext=".spectra")
    write_to_file(temp_spectra_file, spectra_str)
    pRespondsToS_substitution(temp_spectra_file)
    # A realizable specification has no unrealisable core by definition, so the
    # exhaustive exploreAllCores search below can only ever return [].
    if is_realizable(temp_spectra_file, suppress=True):
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
    args = jpype.JArray(JString)([filepath] + _bdd_args())
    output = SpectraToolbox.exploreAllCores(args)
    return str(output)


def semantically_identical_spot(to_cmp_file, baseline_file):
    to_cmp_file = re.sub("_patterned\.spectra", ".spectra", to_cmp_file)
    assumption = equivalent_expressions("assumption|asm", to_cmp_file, baseline_file)
    if assumption is None:
        return SimEnv.Invalid
    if not assumption:
        if is_realizable(to_cmp_file):
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


def is_realizable(file, suppress=False):
    if violations_in_initial_conditions(file):
        print("Spectra file in wrong format for CLI realizability check: (initial conditions)")
        print(file)
        return None
    file = pRespondsToS_substitution(file)
    args = ["-i", file] + _bdd_args()
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
    args = ["-i", file, "--counter-strategy"] + _bdd_args()
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
    args = ["-i", file] + _bdd_args()
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
    args = ["-i", spec_file_path] + _bdd_args() + ['-s', '--static', '-o', output_folder_path]
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



_BDD_PACKAGE_ENV = "SPEC_REPAIR_BDD"
_cudd_state = {"warned": False}


def _bdd_args() -> list:
    """
    Which BDD backend to ask Spectra for.

    **Defaults to CUDD since 2026-08-13.** `SPEC_REPAIR_BDD=jtlv` selects the
    pure-Java package instead.

    It used to default to `--jtlv`, not because that is better but because it
    was the only one that ran: CUDD needs a native library shipped inside the
    jars and never on `java.library.path`, which `jvm.ensure_cudd_native` now
    unpacks. Measured on gpu13: minepump 0.19s under CUDD against 1.17s under
    JTLV, genbuf 0.2s against 0.4s, same verdicts.

    JTLV is not merely slower on the large case studies - it does not finish.
    Its node table never grows, so a big specification reaches an equilibrium of
    permanent garbage collection: genbuf trace 0 sat an hour at 100% CPU in
    `JTLVJavaFactory.makenode` with no progress, and under CUDD cleared that
    phase immediately. A default that cannot complete amba, genbuf or colorsort
    is not a safe default.

    The comparability caveat is real and stands: a different BDD package can
    return a different counter-strategy among the many valid ones, and the
    search branches on the counter-strategy it is given. Every repair found
    remains genuine, but results from either side of this change are not
    comparable with each other - which is why it changed between full reruns
    rather than underneath one, and why anything measured before 2026-08-13
    needs regenerating before it sits in the same table.
    """
    requested = os.environ.get(_BDD_PACKAGE_ENV, "").strip().lower() or "cudd"
    if requested == "jtlv":
        return ["--jtlv"]
    if platform.system() == "Darwin":
        # The jars ship libcudd.so and cudd.dll and no .dylib, so there is no
        # CUDD to load on macOS at all. Honouring the request would swap a
        # working run for `NullPointerException: ... "attrSizes" is null`, so
        # say so once and carry on with JTLV.
        if not _cudd_state["warned"]:
            _cudd_state["warned"] = True
            print("Spectra ships no CUDD native for macOS; using JTLV. The "
                  "large case studies do not finish under JTLV, so run them on "
                  "a Linux box.")
        return ["--jtlv"]
    return []


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


_CALL_LOG_ENV = "SPEC_REPAIR_SPECTRA_CALL_LOG_DIR"


def spectra_call_log_path() -> str:
    """
    Where the *current* Spectra call's output is written as it is produced.

    Spectra runs inside this process's JVM, so a native crash or a kill during
    synthesis takes the repair run down with it - and the output was previously
    captured into an in-memory `ByteArrayOutputStream` that was only read back
    after `main` returned. Anything Spectra said on its way down therefore died
    in that buffer, which is why five FastLAS runs on 2026-08-08 ended with an
    ordinary progress line and no cause: every one of them was inside a
    verification call.

    Written per process (the pid is in the name) and overwritten per call, so
    what survives a death is the last call - the one that killed it.

    Set `SPEC_REPAIR_SPECTRA_CALL_LOG_DIR` to keep it beside the sweep's other
    logs; it falls back to the system temp directory, where a run that nobody is
    supervising costs nothing.
    """
    directory = os.environ.get(_CALL_LOG_ENV, "").strip() or tempfile.gettempdir()
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, f"spectra_last_call_{os.getpid()}.log")


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
    java_io_FileOutputStream = jpype.JClass("java.io.FileOutputStream")
    java_io_PrintStream = jpype.JClass("java.io.PrintStream")

    # Backup original System.out
    original_out = java_lang_System.out

    # Capture to a file rather than to memory, with autoFlush so each line
    # reaches the disk as Spectra prints it. See spectra_call_log_path: the
    # point is that the output survives the process, not that it is a file.
    call_log = spectra_call_log_path()
    fos = java_io_FileOutputStream(call_log, False)
    ps = java_io_PrintStream(fos, True, "UTF-8")

    # Redirect System.out to our PrintStream
    java_lang_System.setOut(ps)

    try:
        _maybe_enable_bdd_reorder()

        # Load the Java class and convert args to Java String[]
        java_args = JArray(JString)(args)

        # Call the main method
        SpectraCLI.main(java_args)

        # Flush and read back what was captured
        ps.flush()
        with open(call_log, "rb") as f:
            output_str = f.read().decode("utf-8")

    finally:
        # Restore original System.out no matter what, and close the file behind
        # it - a sweep makes tens of thousands of these calls, and the sweep
        # box's open-file limit is 1024.
        java_lang_System.setOut(original_out)
        ps.close()

    return output_str
