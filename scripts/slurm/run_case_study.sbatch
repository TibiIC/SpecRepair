#!/bin/bash
# Run one repair job per array index on the Imperial DoC Slurm cluster.
#
# UNTESTED: written from the CSG documentation, not yet run - the login hosts'
# SSH host keys are not trusted from this machine yet. Treat the resource
# numbers as a starting point and check `squeue --me` after the first submit.
#
#   ssh gpucluster2                      # once, to accept the host key
#   cd /vol/bitbucket/$USER/PhD/SpecRepair
#   sbatch --array=0-59 scripts/slurm/run_case_study.sbatch case_study_2 ilasp
#   sbatch --array=0-28 scripts/slurm/run_case_study.sbatch case_study_3 fastlas
#   squeue --me                          # what is queued and running
#   scancel <job_id>                     # stop the whole array
#
# Why this is a better fit than the tmux setup:
#
#   * **Time limits are enforced.** The tmux runs had no per-job limit, which is
#     how six jobs on gpu11 sat blocked in a hung `dot -Tpng` for twelve hours
#     without anyone noticing. Slurm would have killed each at --time and moved
#     on.
#   * **The scheduler owns concurrency.** scripts/lib/slots.sh exists only
#     because nothing else was capping parallelism, and its first version was
#     wrong in a way that ran 39 jobs against a cap of 8. Slurm does this
#     properly, including across machines.
#   * **One job per (case study, trace)** via a job array, so a failure is
#     isolated to its own index and its own slurm-<id>_<n>.out.
#
# These jobs are **CPU work**, not GPU: ILASP, FastLAS, clingo and a JVM. No
# --gres=gpu is requested, which also means they queue against CPU capacity
# rather than waiting behind GPU demand.

#SBATCH --job-name=specrepair
#SBATCH --cpus-per-task=2
# A repair run holds 5-9GB once its search is a few thousand nodes deep, so 8G
# was inside the range it is expected to reach - and over the limit is an OOM
# kill, not a slowdown.
#SBATCH --mem=16G
# Slurm ends a job at its time limit with SIGTERM, which is exit 143 - the same
# signature as the unexplained lab-box kills. Long runs are intended here
# (minepump_2 was at leaf #2149 after 5h51m and still going), so the limit must
# be well clear of them. The `long` partition allows up to 30 days; every
# partition on this cluster is a GPU partition, so gres/gpu:1 is not optional
# and CPU-only jobs still queue against the GPU quota.
#SBATCH --partition=long
#SBATCH --time=7-00:00:00
#SBATCH --output=slurm-%A_%a.out

set -u

SETUP="${SETUP:-case_study_2}"
LEARNER_ARG="${LEARNER:-ilasp}"
[[ $# -ge 1 ]] && SETUP="$1"
[[ $# -ge 2 ]] && LEARNER_ARG="$2"

WORKDIR="${WORKDIR:-/vol/bitbucket/$USER/PhD/SpecRepair}"
cd "$WORKDIR" || { echo "no $WORKDIR" >&2; exit 1; }

# Initialise conda explicitly. A batch job is not an interactive shell: `conda`
# is not defined here (measured on gpuvm36 - `type -t conda` is empty and
# `which python` is /usr/bin/python), and sourcing ~/phd_work.sh is not a
# substitute. That file is written for a login shell and ends the job outright
# when sourced in batch: the first trial exited 1 with a completely empty
# output file, which is what a `source` that exits looks like.
CONDA_BASE="${CONDA_BASE:-/vol/bitbucket/tg4018/anaconda3}"
if [[ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]]; then
    source "$CONDA_BASE/etc/profile.d/conda.sh"
else
    echo "No conda at $CONDA_BASE - set CONDA_BASE." >&2; exit 1
fi
conda activate "${CONDA_ENV:-logic}" || { echo "conda activate failed" >&2; exit 1; }

# Java for the Spectra JVM. sdkman's init reads variables it does not set
# first - it fails on line 20 with "SDKMAN_CANDIDATES_API: unbound variable"
# under `set -u` - so nounset is lifted across the source and restored after.
# Its absence is not fatal if java is already on PATH.
if [[ -f ~/.sdkman/bin/sdkman-init.sh ]]; then
    set +u
    source ~/.sdkman/bin/sdkman-init.sh
    set -u
fi
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"
# The jars and solver binaries live off /vol/bitbucket, not ~/Tools. phd_work.sh
# exports this for interactive shells, but that file cannot be sourced in batch
# (see above), so it is set here explicitly - without it the JVM starts and then
# fails with "Class cores.SpectraToolbox is not found".
export SPEC_REPAIR_TOOLS="${SPEC_REPAIR_TOOLS:-/vol/bitbucket/tg4018/Tools}"
# **Appended, not prepended.** Tools/bin carries its own Spot binaries, and
# prepending them puts an `ltlfilt` on PATH that then loads `libspot.so.0` from
# the conda env, because LD_LIBRARY_PATH points there. The two are different
# Spot versions, so ltlfilt dies with
# `symbol lookup error: undefined symbol: _ZN4spot14ltl_to_tgba_fm...` and exit
# 127 - and `does_left_imply_right` reports only "the output of ltlfilt is
# unexpected", which is what made every implication graph fail on 2026-08-15.
# Appending leaves conda's matching ltlfilt/libspot pair in charge while FastLAS
# and ILASP, which exist nowhere else, are still found here.
export PATH="$PATH:$SPEC_REPAIR_TOOLS/bin"

# clingo is invoked by name, and the compute nodes do not have it - the DoC lab
# machines get it from /usr/bin as a system package, the GPU cluster nodes do
# not. The conda env on /vol/bitbucket carries its own clingo and its own
# libraries, so it is the first choice; the standalone build is the fallback.
#
# The test is that clingo *runs*, not that the file is executable. The
# standalone build passes an -x test on every node and then exits 127 on the
# compute nodes, where it cannot load liblua5.1.so.0 - the whole of array
# 273723 died that way, five for five, seconds in.
#
# Fix it *here*, per node, and never by installing clingo into the conda env.
# That env is on shared NFS, so an install into it lands on every lab box at
# once, ahead of /usr/bin/clingo - and FastLAS shells out to whatever clingo is
# on PATH. Doing exactly that on 2026-08-13 turned every FastLAS learning task
# into UNSATISFIABLE across the whole estate, with no code change to explain it.
# Both builds reported version 5.7.1; the version string proves nothing.
clingo_runs() { "$1" --version >/dev/null 2>&1; }

if ! clingo_runs clingo; then
    CLINGO_BIN="${CLINGO_BIN:-/vol/bitbucket/tg4018/clingo-build/bin}"
    # libclingo.so sits beside the binary, and liblua5.1.so.0 - which the
    # compute nodes do not carry - is staged in ../lib next to it.
    export PATH="$CLINGO_BIN:$PATH"
    export LD_LIBRARY_PATH="$CLINGO_BIN:$(dirname "$CLINGO_BIN")/lib:${LD_LIBRARY_PATH:-}"
fi
clingo_runs clingo || {
    echo "clingo is on PATH but will not run here ($(command -v clingo))." >&2
    echo "Exit 127 means a missing shared library - check with ldd." >&2
    exit 1
}
echo "clingo: $(command -v clingo) ($(clingo --version 2>&1 | head -1))"
export SPEC_REPAIR_LEARNER="$LEARNER_ARG"
export SPEC_REPAIR_FASTLAS_RUNS="${FASTLAS_RUNS:-10}"

# Results are written to <case>_trace<N>_<learner>_<RUN_DATE>/, and every
# pipeline step selects a run by globbing `*_<date>`. A job continuing an
# earlier sweep therefore has to carry that sweep's date or its results land in
# a second tree and post-processing silently sees half of each:
#
#     SPEC_REPAIR_RUN_DATE=2026-08-13 sbatch ... run_case_study.sbatch ...
#
# Inherited from the submitting environment when set - do not pass it through
# `--export`, which on this cluster fails the job with "user env retrieval
# failed requeued held". Unset, each job stamps its own start date.
if [[ -n "${SPEC_REPAIR_RUN_DATE:-}" ]]; then
    export SPEC_REPAIR_RUN_DATE
    echo "run date: $SPEC_REPAIR_RUN_DATE (inherited)"
fi

# The array index selects one (case study, trace) pair. Built from what is on
# disk rather than assumed: a controller-generated case study only has the
# traces its controller produced, so case_study_3's pcar has 0, 1, 2 and 4.
mapfile -t JOBS < <(
  python - "$SETUP" <<'PY'
import os, re, sys
setup = sys.argv[1]
root = os.path.join("input-files", "case-studies", "spectra", setup)
for case_study in sorted(os.listdir(root)):
    d = os.path.join(root, case_study)
    if not os.path.isdir(d):
        continue
    traces = sorted(int(m.group(1))
                    for f in os.listdir(d)
                    if (m := re.fullmatch(r"violation_trace_(\d+)\.txt", f)))
    if traces:
        for t in traces:
            print(f"{case_study} {t}")
    elif os.path.isfile(os.path.join(d, "strong.spectra")):
        print(f"{case_study} -")      # case_study_1 has one run per case study
PY
)

if [[ "${SLURM_ARRAY_TASK_ID:-0}" -ge "${#JOBS[@]}" ]]; then
    echo "Array index ${SLURM_ARRAY_TASK_ID} beyond ${#JOBS[@]} jobs - nothing to do."
    exit 0
fi

read -r CASE_STUDY TRACE <<< "${JOBS[$SLURM_ARRAY_TASK_ID]}"

if [[ "$SETUP" == "case_study_1" ]]; then
    TEST="tests.test_main.test_case_study_1.TestCaseStudy1.test_case_study_1_${CASE_STUDY}_syn"
else
    n="${SETUP#case_study_}"
    TEST="tests.test_main.test_case_study_${n}.TestCaseStudy${n}.test_case_study_${n}_${CASE_STUDY}_${TRACE}_syn"
fi

echo "[$(date '+%F %T')] ${SETUP} ${CASE_STUDY} trace ${TRACE} with ${LEARNER_ARG} on $(hostname)"
exec python -m unittest "$TEST"
