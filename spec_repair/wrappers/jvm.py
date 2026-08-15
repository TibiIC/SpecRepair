"""
Single source of truth for starting/stopping the JVM shared by every module
that resolves Java classes via jpype (spectra_toolbox.py, controller_shield.py).

JPype only allows one JVM per process, and its classpath is fixed at the
first startJVM() call - so every jar any Java-backed module needs must be
known here before that call happens. Importing this module is enough:
starting the JVM is a side effect of the import, guarded so re-imports are
no-ops, matching jpype's own recommended idempotent-startup pattern.
"""
import atexit
import os
import tempfile
import threading

import jpype
import jpype.imports

import platform
import zipfile

from spec_repair.config import (CUDD_NATIVE_DIR, PATH_TO_JVM, PATH_TO_TOOLBOX,
                                PATH_TO_CLI, PATH_TO_SHIELD)


def ensure_cudd_native() -> str:
    """
    Unpack CUDD's native library from the Spectra jars, returning its directory.

    Spectra's default BDD backend is CUDD; we fall back to `--jtlv`, a pure-Java
    package whose node table is fixed at 200033 and never grows, so a large
    enough specification sits in a garbage-collection equilibrium that never
    errors and never finishes (measured on amba: ~186 collections/second). CUDD
    is native and grows dynamically.

    The reason CUDD never worked is mundane: `libcudd.so` is *inside* the jars
    and never on `java.library.path`, so loading it failed with
    `NullPointerException: Cannot load from int array because "attrSizes" is
    null`. Extracting it needs no root.

    Returns "" on macOS: the jars ship `libcudd.so` and `cudd.dll` and no
    `.dylib`, so there is nothing to extract and JTLV is the only option there.
    """
    if platform.system() == "Darwin":
        return ""
    member = "cudd.dll" if platform.system() == "Windows" else "libcudd.so"
    target = os.path.join(CUDD_NATIVE_DIR, member)
    if os.path.isfile(target):
        return CUDD_NATIVE_DIR
    try:
        os.makedirs(CUDD_NATIVE_DIR, exist_ok=True)
        with zipfile.ZipFile(PATH_TO_CLI) as jar, jar.open(member) as src:
            with open(target, "wb") as out:
                out.write(src.read())
        os.chmod(target, 0o755)
        return CUDD_NATIVE_DIR
    except (OSError, KeyError):
        # A read-only tools directory or a jar without the native: JTLV still
        # works, so this must not stop the JVM from starting.
        return ""


def _error_file_arg() -> str:
    """
    Put the JVM's fatal-error log somewhere findable, one file per process.

    The default is `hs_err_pid%p.log` in the working directory, which on the
    sweep box is the repository root - and after seven JVM deaths on the
    2026-08-08 sweep there was not one there, so the default is unreliable
    under whatever conditions actually kill it (a directory the run cannot
    write, or a crash too early to open it). Naming it explicitly, next to the
    Spectra call log, means a crash leaves *some* record even when the process
    dies with its stdout buffer unflushed.
    """
    directory = os.environ.get("SPEC_REPAIR_SPECTRA_CALL_LOG_DIR", "").strip() or tempfile.gettempdir()
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError:
        return ""
    return f"-XX:ErrorFile={os.path.join(directory, 'hs_err_pid%p.log')}"


if not jpype.isJVMStarted():
    _native_dir = ensure_cudd_native()
    _jvm_args = ["-ea", "--enable-native-access=ALL-UNNAMED"]
    # `SPEC_REPAIR_JVM_HEAP=48g` raises the maximum heap. Unset, the JVM takes
    # its default of a quarter of RAM - about 15.5GB of a 62GB box - and leaves
    # the other three quarters unused.
    #
    # That default is what stops colorsort. Its candidates are learned in
    # seconds and then discarded: synthesis exhausts the heap, and
    # `_synthesise_or_reject` turns the OutOfMemoryError into
    # SpecificationNotVerifiableException, which the search records as "cannot
    # verify" and skips. Measured on colorsort trace 2, which finished with no
    # repair after three candidates failed verification in 46m, 1h59m and 30m.
    #
    # Only the Java heap. CUDD's BDD tables are native and uncapped, so this
    # does not bound them - and the run's total footprint grows accordingly,
    # which on a shared box is what earlyoom reacts to.
    _heap = os.environ.get("SPEC_REPAIR_JVM_HEAP", "").strip()
    if _heap:
        _jvm_args.append(f"-Xmx{_heap}")
    _error_file = _error_file_arg()
    if _error_file:
        _jvm_args.append(_error_file)
    if _native_dir:
        _jvm_args.append(f"-Djava.library.path={_native_dir}")
    jpype.startJVM(
        *_jvm_args,
        jvmpath=PATH_TO_JVM,
        classpath=[PATH_TO_TOOLBOX, PATH_TO_CLI, PATH_TO_SHIELD],
        convertStrings=False,
    )
    print("JVM started successfully")


def _shutdown_jvm() -> None:
    if not jpype.isJVMStarted():
        return

    def force_exit():
        print("Shutdown taking too long, forcing exit.")
        os._exit(1)

    print("Shutting down JVM...")
    timer = threading.Timer(10, force_exit)
    timer.start()
    jpype.shutdownJVM()
    print("JVM shutdown initiated...")
    timer.cancel()
    print("JVM shutdown complete.")


atexit.register(_shutdown_jvm)
