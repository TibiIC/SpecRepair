#!/bin/bash

# Runs the controller-generated case studies in parallel, one tmux window each, for
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
#   ./run_case_study_3.sh                  # every case study, every trace
#   ./run_case_study_3.sh minepump         # one case study, all its traces
#   ./run_case_study_3.sh minepump 0       # one case study, one trace
#   TRACES="0 1" ./run_case_study_3.sh     # every case study, traces 0 and 1
#   LEARNER=fastlas ./run_case_study_3.sh  # learn with FastLAS, not ILASP
#   LEARNER=fastlas FASTLAS_RUNS=10 ./run_case_study_3.sh  # up to 10 solutions per step
#   LEARNER_TIMEOUT=900 ./run_case_study_3.sh    # seconds per learning task (default 600)
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
TEST_MODULE="tests.test_main.test_case_study_3.TestCaseStudy3"

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
# Discovered from disk, not listed. A controller-generated setup gains and
# loses case studies as the generator improves - genbuf started producing a
# trace once the environment was aimed at a specific assumption, and a
# hardcoded list silently skipped it, running 27 jobs where 28 existed. The
# same drift already cost a phantom pcar_3.
CASE_STUDY_DIR="$WORKDIR/input-files/case-studies/spectra/case_study_3"
all_case_studies=()
for _dir in "$CASE_STUDY_DIR"/*/; do
    [[ -d "$_dir" ]] || continue
    _name="$(basename "$_dir")"
    compgen -G "$_dir/violation_trace_*.txt" >/dev/null || continue
    all_case_studies+=("$_name")
done
if [[ ${#all_case_studies[@]} -eq 0 ]]; then
    echo "No case studies with traces under $CASE_STUDY_DIR." >&2; exit 1
fi

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

# Traces are discovered per case study, not assumed. Unlike case_study_2, which
# has exactly five everywhere, a controller-generated case study only has the
# traces its controller actually produced - pcar has 0, 1, 2 and 4, because no
# violation was reached for 3 within the budget. Iterating a fixed 0..4 launched
# a test that was never generated, and unittest failed the window with
# "AttributeError: type object 'TestCaseStudy3' has no attribute
# test_case_study_3_pcar_3_syn", which reads like a broken test rather than a
# trace that does not exist.
#
# The test module already discovers its traces from disk; this makes the runner
# agree with it instead of guessing.
CASE_STUDY_DIR="$WORKDIR/input-files/case-studies/spectra/case_study_3"

traces_for() {
    local case_study="$1"
    if [[ -n "$trace_arg" ]]; then
        echo "$trace_arg"
        return
    fi
    if [[ -n "${TRACES:-}" ]]; then
        echo "$TRACES"
        return
    fi
    local f n found=""
    for f in "$CASE_STUDY_DIR/$case_study"/violation_trace_*.txt; do
        [[ -e "$f" ]] || continue
        n="${f##*violation_trace_}"
        found+="${n%.txt} "
    done
    echo "$found"
}

# Seconds a single learning task gets before its branch is abandoned. The
# library default is 60, which the 2026-08-08 sweep showed is far too tight for
# ILASP: 2,671 learning tasks across the three ILASP sweeps hit it (1,109 in
# this one) against 0 for FastLAS. Each is a branch the ILASP arm never
# explored, so at 60s a comparison between the two learners measures the
# timeout rather than the learners. Exported explicitly rather than left to the
# library default, so the value a sweep ran under is visible in its launch.
LEARNER_TIMEOUT="${LEARNER_TIMEOUT:-600}"
if ! [[ "$LEARNER_TIMEOUT" =~ ^[1-9][0-9]*$ ]]; then
    echo "LEARNER_TIMEOUT='$LEARNER_TIMEOUT' must be a positive integer." >&2; exit 1
fi

# Resolved once, here, and handed to every job. The date used to come from
# `datetime.now()` inside the test, which is evaluated when the *job* starts -
# and jobs start over many hours as the concurrency semaphore releases them. A
# sweep launched at 20:11 therefore stamped its output directories with two
# different dates, and every pipeline step selects a run by globbing
# `*_<date>`, so half the results were silently left behind. A two-day sweep
# would scatter across three.
RUN_DATE="$(date +%Y-%m-%d)"

# Session name is scoped to the selection, so a single-case-study rerun can be
# started alongside a full run already in progress.
SESSION="case_study_3_${case_study_arg}${trace_arg:+_$trace_arg}_${LEARNER}"
LOGDIR="$WORKDIR/logs/case_study_3/${case_study_arg}${trace_arg:+_$trace_arg}_${LEARNER}_$(date +%Y-%m-%d_%H%M%S)"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "tmux session '$SESSION' already exists - attach to it, or rename/kill it before re-running." >&2
    exit 1
fi

# Refuse to start on top of a previous sweep, including one left under an older
# session name - the exact-name check below only catches a collision with *this*
# run's name.
source "$(dirname "${BASH_SOURCE[0]}")/lib/sweep_guard.sh"
assert_no_previous_sweep "$SESSION"

mkdir -p "$LOGDIR"

SETUP_CMDS="source ~/.sdkman/bin/sdkman-init.sh && source ~/phd_work.sh && conda activate $CONDA_ENV && export LD_LIBRARY_PATH=\$CONDA_PREFIX/lib:\$LD_LIBRARY_PATH && export SPEC_REPAIR_LEARNER=$LEARNER && export SPEC_REPAIR_FASTLAS_RUNS=$FASTLAS_RUNS && export SPEC_REPAIR_LEARNER_TIMEOUT=$LEARNER_TIMEOUT && export SPEC_REPAIR_RUN_DATE=$RUN_DATE && cd $WORKDIR"

# Build the full (case study, trace) work list first, so the window count and
# the concurrency cap are both known before anything starts.
jobs=()
for case_study in "${case_studies[@]}"; do
    read -r -a traces <<< "$(traces_for "$case_study")"
    for trace in "${traces[@]}"; do
        jobs+=("${case_study}_${trace}")
    done
done

if [[ ${#jobs[@]} -eq 0 ]]; then
    echo "Nothing to run." >&2
    exit 1
fi

source "$(dirname "${BASH_SOURCE[0]}")/lib/slots.sh"
slots_init "$LOGDIR" "$MAX_WINDOWS"

run_command_for() {
    local job="$1"
    local case_study="${job%_*}"
    local trace="${job##*_}"
    local test_name="test_case_study_3_${case_study}_${trace}_syn"
    local test_cmd="python -m unittest ${TEST_MODULE}.${test_name} 2>&1 | tee $LOGDIR/${job}.log"

    echo "$SETUP_CMDS && $(slots_wrap "$LOGDIR" "$MAX_WINDOWS" "$test_cmd"); read"
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
