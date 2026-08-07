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
#SBATCH --mem=8G
#SBATCH --time=12:00:00
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
export SPEC_REPAIR_LEARNER="$LEARNER_ARG"
export SPEC_REPAIR_FASTLAS_RUNS="${FASTLAS_RUNS:-10}"

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
