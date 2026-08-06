#!/bin/bash

# Runs the trace-violation case studies in parallel, one tmux window each, for
# unattended background runs on the GPU box.
#
# The counterpart to run_case_study_1.sh, which does the same for the
# strengthened (ideal + strong) case studies. Two differences follow from the
# pivot:
#
#   * the specification repaired is original.spectra, not strong.spectra;
#   * each case study has five traces, each violating a different group of
#     assumptions, so it contributes five independent runs rather than one.
#
# Usage:
#   ./run_case_study_2.sh                  # every case study, every trace
#   ./run_case_study_2.sh minepump         # one case study, all its traces
#   ./run_case_study_2.sh minepump 0       # one case study, one trace
#   TRACES="0 1" ./run_case_study_2.sh     # every case study, traces 0 and 1
#   LEARNER=fastlas ./run_case_study_2.sh  # learn with FastLAS, not ILASP
#   LEARNER=fastlas FASTLAS_RUNS=10 ./run_case_study_2.sh  # up to 10 solutions per step
#
# A FastLAS run writes to <case_study>_trace<ID>_fastlas_<date>, so it lands
# beside an ILASP run of the same date rather than overwriting it.
#
# 50 windows is a lot to start at once; MAX_WINDOWS caps how many run
# concurrently, with the rest queued. Set MAX_WINDOWS=0 for no cap.

set -u

WORKDIR="${WORKDIR:-/vol/bitbucket/tg4018/PhD/SpecRepair}"
CONDA_ENV="${CONDA_ENV:-logic}"
MAX_WINDOWS="${MAX_WINDOWS:-10}"
TEST_MODULE="tests.test_main.test_case_study_2.TestCaseStudy2"

LEARNER="${LEARNER:-ilasp}"
case "$LEARNER" in
    ilasp|fastlas) ;;
    *) echo "Unknown LEARNER '$LEARNER'. Use one of: ilasp, fastlas." >&2; exit 1 ;;
esac

# FastLAS returns one solution per invocation where ILASP returns all optimal
# ones, so FASTLAS_RUNS caps how many distinct solutions a learning step
# enumerates: each solution found is forbidden before FastLAS is asked again,
# and the step stops early once the space is exhausted. 10 mirrors ILASP's
# MAX_ASP_HYPOTHESES. Ignored when LEARNER=ilasp.
FASTLAS_RUNS="${FASTLAS_RUNS:-1}"
if ! [[ "$FASTLAS_RUNS" =~ ^[1-9][0-9]*$ ]]; then
    echo "FASTLAS_RUNS='$FASTLAS_RUNS' must be a positive integer." >&2; exit 1
fi

# arbiter is absent deliberately: its only assumption is GF(a), and liveness is
# vacuously satisfied on a finite prefix, so it has no violating trace to repair
# against at any length. See docs/session-notes/2026-07-28.
all_case_studies=(
    "amba"
    "colorsort"
    "elevator"
    "genbuf"
    "gyro"
    "humanoid"
    "lift"
    "minepump"
    "minepump_liveness"
    "pcar"
    "traffic_single"
    "traffic_updated"
)

case_study_arg="${1:-all}"
trace_arg="${2:-}"

if [[ "$case_study_arg" == "all" ]]; then
    case_studies=("${all_case_studies[@]}")
else
    if [[ ! " ${all_case_studies[*]} " =~ " ${case_study_arg} " ]]; then
        echo "Unknown case study '${case_study_arg}'." >&2
        echo "Use one of: all (default), ${all_case_studies[*]}" >&2
        exit 1
    fi
    case_studies=("$case_study_arg")
fi

if [[ -n "$trace_arg" ]]; then
    traces=("$trace_arg")
else
    read -r -a traces <<< "${TRACES:-0 1 2 3 4}"
fi

# Session name is scoped to the selection, so a single-case-study rerun can be
# started alongside a full run already in progress.
SESSION="case_study_2_${case_study_arg}${trace_arg:+_$trace_arg}_${LEARNER}"
LOGDIR="$WORKDIR/logs/case_study_2/${case_study_arg}${trace_arg:+_$trace_arg}_${LEARNER}_$(date +%Y-%m-%d_%H%M%S)"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "tmux session '$SESSION' already exists - attach to it, or rename/kill it before re-running." >&2
    exit 1
fi

mkdir -p "$LOGDIR"

SETUP_CMDS="source ~/.sdkman/bin/sdkman-init.sh && source ~/phd_work.sh && conda activate $CONDA_ENV && export LD_LIBRARY_PATH=\$CONDA_PREFIX/lib:\$LD_LIBRARY_PATH && export SPEC_REPAIR_LEARNER=$LEARNER && export SPEC_REPAIR_FASTLAS_RUNS=$FASTLAS_RUNS && cd $WORKDIR"

# Build the full (case study, trace) work list first, so the window count and
# the concurrency cap are both known before anything starts.
jobs=()
for case_study in "${case_studies[@]}"; do
    for trace in "${traces[@]}"; do
        jobs+=("${case_study}_${trace}")
    done
done

if [[ ${#jobs[@]} -eq 0 ]]; then
    echo "Nothing to run." >&2
    exit 1
fi

# One semaphore file per concurrent slot. Each window waits for a free slot
# before starting its test, so all 50 windows can be created up front while only
# MAX_WINDOWS tests run at a time. Without this, 50 simultaneous JVMs is enough
# to exhaust memory on the box.
#
# Free and taken slots live in SEPARATE directories. They used to share one,
# with a taken slot renamed in place to slot_<n>.taken.<pid> - but the waiting
# glob is slot_*, which matches slot_0.taken.123 just as happily as slot_0. So a
# waiting window would "claim" an already-claimed slot, renaming it
# slot_0.taken.123.taken.456, and the cap collapsed: measured on the 2026-08-06
# 16:30 sweep, 0 free slots and 39 concurrent runs against a cap of 8. The
# release mv then failed ("cannot stat ...taken.X.taken.Y") because another
# window had renamed the file again, so slots were never returned either.
SLOTDIR="$LOGDIR/.slots"
BUSYDIR="$LOGDIR/.slots_busy"
if [[ "$MAX_WINDOWS" -gt 0 ]]; then
    mkdir -p "$SLOTDIR" "$BUSYDIR"
    for ((i = 0; i < MAX_WINDOWS; i++)); do
        touch "$SLOTDIR/slot_$i"
    done
fi

run_command_for() {
    local job="$1"
    local case_study="${job%_*}"
    local trace="${job##*_}"
    local test_name="test_case_study_2_${case_study}_${trace}_syn"
    local test_cmd="python -m unittest ${TEST_MODULE}.${test_name} 2>&1 | tee $LOGDIR/${job}.log"

    if [[ "$MAX_WINDOWS" -gt 0 ]]; then
        # Claim a slot by moving it out of SLOTDIR into BUSYDIR - mv is atomic
        # within a filesystem, so two windows cannot claim the same one, and a
        # claimed slot is no longer visible to the waiting glob. Release it on
        # the way out, whether the test passed, failed or died: a slot leaked
        # here is one less run for the whole rest of the sweep.
        echo "$SETUP_CMDS && while true; do for s in $SLOTDIR/slot_*; do [ -e \"\$s\" ] && mv \"\$s\" \"$BUSYDIR/\$(basename \"\$s\").\$\$\" 2>/dev/null && { export MY_SLOT=\"\$s\"; break 2; }; done; sleep 5; done; trap 'mv \"$BUSYDIR/\$(basename \"\$MY_SLOT\").\$\$\" \"\$MY_SLOT\" 2>/dev/null' EXIT INT TERM; $test_cmd; trap - EXIT INT TERM; mv \"$BUSYDIR/\$(basename \"\$MY_SLOT\").\$\$\" \"\$MY_SLOT\"; read"
    else
        echo "$SETUP_CMDS && $test_cmd && read"
    fi
}

first_job="${jobs[0]}"
tmux new-session -d -s "$SESSION" -n "$first_job"
tmux send-keys -t "$SESSION:$first_job" "$(run_command_for "$first_job")" C-m

for job in "${jobs[@]:1}"; do
    tmux new-window -t "$SESSION" -n "$job"
    tmux send-keys -t "$SESSION:$job" "$(run_command_for "$job")" C-m
done

echo "Started ${#jobs[@]} run(s) with the $LEARNER learner in tmux session '$SESSION'"
if [[ "$MAX_WINDOWS" -gt 0 ]]; then
    echo "Concurrency capped at $MAX_WINDOWS; the rest wait for a free slot."
fi
echo "Logs under $LOGDIR"
echo "Attach with: tmux attach -t $SESSION"
