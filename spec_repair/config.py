"""
Configuration, resolved so that the same committed file works on every machine.

Nothing here should ever need editing to move between a laptop and the GPU box.
The three things that genuinely differ per machine are read from the
environment, each with a default that covers the common case:

    SPEC_REPAIR_TOOLS   where the Spectra jars and the ILASP/FastLAS binaries
                        live. Default ~/Tools.
    SPEC_REPAIR_JVM     libjvm.{dylib,so}. Default: Homebrew's newest openjdk
                        on macOS, else $JAVA_HOME - see _default_jvm_path for
                        why $JAVA_HOME is not tried first.
    SPEC_REPAIR_LOGS    the violation-listening log folder. Rarely used.

`PROJECT_PATH` is *derived* from this file's own location rather than
configured, so it is always right and can never drift.

On a machine whose layout differs from the defaults, set the variables in your
shell profile - e.g. on the GPU box:

    export SPEC_REPAIR_TOOLS=/vol/bitbucket/tg4018/Tools

That way `git pull` and `git push` work from anywhere without a
stash/pop dance around locally-edited paths.
"""
import glob
import os.path
import re
import sys

# Where the jars and solver binaries live. One root covers all of them.
TOOLS_DIR: str = os.path.expanduser(os.environ.get("SPEC_REPAIR_TOOLS", "~/Tools"))

# The repository root: this file is <root>/spec_repair/config.py. Derived rather
# than configured, so it is correct on every checkout including worktrees.
PROJECT_PATH: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _default_jvm_path() -> str:
    """
    libjvm for a JVM new enough to load the Spectra jars.

    `$SPEC_REPAIR_JVM` wins outright. Failing that, candidates are tried in
    order and the first that exists is used.

    **`$JAVA_HOME` is deliberately the last resort, not the first.** It is
    whatever the current shell happens to select, which is often too old: inside
    the `arm_env` conda environment it points at the environment's own JDK, and
    loading the Spectra jars against it fails with
    `java.lang.UnsupportedClassVersionError`. Homebrew's openjdk is checked
    first on macOS, newest version first, because that is the install these jars
    actually need. On Linux there is no Homebrew, so `$JAVA_HOME` applies - and
    on the GPU box sdkman sets it to a suitable JDK.

    Returning "" rather than guessing lets the JVM loader fail with its own
    message instead of pointing at a path that was never going to exist.
    """
    explicit = os.environ.get("SPEC_REPAIR_JVM")
    if explicit:
        return explicit

    candidates = []
    if sys.platform == "darwin":
        # Newest first: "25" must beat "17", so sort numerically where possible.
        cellar = sorted(
            glob.glob("/opt/homebrew/Cellar/openjdk/*/libexec/openjdk.jdk"
                      "/Contents/Home/lib/server/libjvm.dylib"),
            key=lambda p: [int(n) if n.isdigit() else n
                           for n in re.split(r"[.\-]", p.split("/openjdk/")[1].split("/")[0])],
            reverse=True)
        candidates.extend(cellar)
    else:
        # sdkman's selected JDK, which is what the GPU box has. Preferred over
        # $JAVA_HOME for the same reason Homebrew is on macOS: $JAVA_HOME is
        # only right if the shell happened to source sdkman first. Under conda
        # alone it points at the environment's own Java 21, and the Spectra
        # jars need 23+ - `UnsupportedClassVersionError: class file version
        # 67.0, this version ... recognizes up to 65.0`.
        candidates.append(os.path.expanduser(
            "~/.sdkman/candidates/java/current/lib/server/libjvm.so"))

    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        suffix = "libjvm.dylib" if sys.platform == "darwin" else "libjvm.so"
        candidates.append(os.path.join(java_home, "lib", "server", suffix))

    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return ""


PATH_TO_CLI = f"{TOOLS_DIR}/spectra-cli/tau.smlab.syntech.Spectra.cli/lib/spectra-cli.jar"
PATH_TO_CORES = f"{TOOLS_DIR}/spectra_unrealizable_cores.jar"
PATH_TO_ALL_CORES = f"{TOOLS_DIR}/spectra_all_unrealisable_cores.jar"
PATH_TO_TOOLBOX = f"{TOOLS_DIR}/spectra_toolbox.jar"
PATH_TO_ILASP = f"{TOOLS_DIR}/bin/ILASP"
PATH_TO_FASTLAS = f"{TOOLS_DIR}/bin/FastLAS"
PATH_TO_JVM = _default_jvm_path()

# Where CUDD's native library is unpacked, if it is used at all.
#
# Spectra's default BDD backend is CUDD, and it is dramatically faster than the
# pure-Java JTLV package we fall back to - but it needs a native library that is
# never on the library path, so every CUDD run failed with
# `NullPointerException: Cannot load from int array because "attrSizes" is null`
# and `--jtlv` became the only thing that worked.
#
# The library ships *inside* the Spectra jars: `libcudd.so` and `cudd.dll`.
# There is no `.dylib`, so CUDD is available on Linux and Windows and simply
# cannot run on macOS - which is why the same failure appears on both a Mac and
# the Linux GPU boxes, for two different reasons. Extracting the bundled `.so`
# needs no root, so a shared box can use it.
CUDD_NATIVE_DIR = os.path.expanduser(
    os.environ.get("SPEC_REPAIR_CUDD_DIR", f"{TOOLS_DIR}/native"))
PATH_TO_SHIELD = os.path.join(PROJECT_PATH, "easy-downloads", "spectra-executor.jar")

PRINT_CS = False
FASTLAS = False  # TODO: modify into enum (inductive ASP tool)
RESTORE_FIRST_HYPOTHESIS = True

# This determines the paths for running clingo and ILASP and whether to use
# Windows Subsystem for Linux (WSL):
SETUP_DICT = {'wsl': False,
              'clingo': 'clingo',
              'ILASP': PATH_TO_ILASP,
              'FastLAS': PATH_TO_FASTLAS,
              'ltlfilt': 'ltlfilt',
              'java': 'java',
              }

GENERATE_MULTIPLE_TRACES = False

# Violation Listening Configurations
LOG_FOLDER = os.path.expanduser(
    os.environ.get("SPEC_REPAIR_LOGS", "~/eclipse-workspace/PhD/Lift"))

# TODO: add these in a config class
MAX_ASP_HYPOTHESES = 10

# For testing and statistics
STATISTICS: bool = True
MANUAL: bool = True

# Configuration of Learning
SEMANTIC_EQUIVALENCE = True
# 29.01.2026: Note no Semantic Equivalence above
# * Makes learning solutions much faster, but
# * Leaves out many weakenings, most likely, response pattern
# e.g. G(a->b) weakens to either
# 1. G(a&c->b) or 2. G(a->b|!c), and 1 equivalent to 2.
# But both can be weakened further to response as:
# 1. G(a&c->F(b)) or 2. G(a->F(b|!c)), who are not equivalent.
