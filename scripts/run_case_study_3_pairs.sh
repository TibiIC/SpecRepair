#!/usr/bin/env bash
#
# Run an explicit list of case_study_3 (case study, trace) pairs on this machine,
# all at once, with no concurrency cap.
#
# The counterpart to run_case_study_3.sh, which enumerates every pair itself and
# then queues them behind a slot semaphore. That is the right shape for one box:
# 55 simultaneous JVMs do not fit in 62GB. It is the wrong shape for 19 boxes,
# where the queue is the only thing making the sweep take a week - runs that
# individually take days sit waiting for a slot on one machine while most of the
# lab is idle.
#
# So: the caller decides which pairs go where, and every pair here starts
# immediately. Sizing is the caller's problem too, which is the point - put five
# light traces on a small box and two colorsort traces on a large one, rather
# than letting one cap serve both.
#
# Usage:
#   LEARNER=fastlas ./scripts/run_case_study_3_pairs.sh amba:0 amba:1 genbuf:3
#   LEARNER=ilasp RUN_DATE=2026-08-13 ./scripts/run_case_study_3_pairs.sh lift:1 lift:2
#
# RUN_DATE matters and defaults to today. Results land in
# tests/test_files/out/case_study_3/<case>_trace<N>_<learner>_<RUN_DATE>/, so a
# distributed continuation of an existing sweep must be given that sweep's date
# or the results split across two trees and post-processing sees half of each.

set -u

# tmux must not run under the conda LD_LIBRARY_PATH: it loads conda's libtinfo
# and dies with `undefined symbol: tiparm_s`, so new-window fails while the
# launch still reports success. Each window sets its own environment below.
tmux() { env -u LD_LIBRARY_PATH tmux "$@"; }

WORKDIR="${WORKDIR:-/vol/bitbucket/tg4018/PhD/SpecRepair}"
CONDA_ENV="${CONDA_ENV:-logic}"
TEST_MODULE="tests.test_main.test_case_study_3.TestCaseStudy3"

LEARNER="${LEARNER:-ilasp}"
case "$LEARNER" in
    ilasp|fastlas) ;;
    *) echo "Unknown LEARNER '$LEARNER'. Use one of: ilasp, fastlas." >&2; exit 1 ;;
esac

FASTLAS_RUNS="${FASTLAS_RUNS:-10}"
LEARNER_TIMEOUT="${LEARNER_TIMEOUT:-600}"
RUN_DATE="${RUN_DATE:-$(date +%Y-%m-%d)}"

if [[ $# -eq 0 ]]; then
    echo "No pairs given. Usage: LEARNER=fastlas $0 amba:0 genbuf:3" >&2
    exit 1
fi

HOST_SHORT="$(hostname -s)"
SESSION="cs3_${LEARNER}_${HOST_SHORT}"
LOGDIR="$WORKDIR/logs/case_study_3/dist_${LEARNER}_${HOST_SHORT}_$(date +%Y-%m-%d_%H%M%S)"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "tmux session '$SESSION' already exists on $HOST_SHORT - kill it first." >&2
    exit 1
fi

# Validate every pair before starting any of them: a typo that surfaces as a
# missing test halfway through a launch leaves a session half-populated.
jobs=()
for pair in "$@"; do
    case_study="${pair%%:*}"
    trace="${pair##*:}"
    if [[ "$case_study" == "$pair" || -z "$trace" ]]; then
        echo "Malformed pair '$pair' - expected <case_study>:<trace>, e.g. amba:0." >&2
        exit 1
    fi
    trace_file="$WORKDIR/input-files/case-studies/spectra/case_study_3/$case_study/violation_trace_${trace}.txt"
    if [[ ! -f "$trace_file" ]]; then
        echo "No such trace: $trace_file" >&2
        exit 1
    fi
    jobs+=("${case_study}_${trace}")
done

mkdir -p "$LOGDIR/jvm"

SETUP_CMDS="source ~/.sdkman/bin/sdkman-init.sh && source ~/phd_work.sh && conda activate $CONDA_ENV && export LD_LIBRARY_PATH=\$CONDA_PREFIX/lib:\$LD_LIBRARY_PATH && export SPEC_REPAIR_LEARNER=$LEARNER && export SPEC_REPAIR_FASTLAS_RUNS=$FASTLAS_RUNS && export SPEC_REPAIR_LEARNER_TIMEOUT=$LEARNER_TIMEOUT && export SPEC_REPAIR_RUN_DATE=$RUN_DATE && export SPEC_REPAIR_SPECTRA_CALL_LOG_DIR=$LOGDIR/jvm && cd $WORKDIR"

source "$(dirname "${BASH_SOURCE[0]}")/lib/job_cmd.sh"

run_command_for() {
    local job="$1"
    local case_study="${job%_*}"
    local trace="${job##*_}"
    local test_cmd
    test_cmd="$(job_test_cmd "$LOGDIR" "$job" "${TEST_MODULE}.test_case_study_3_${case_study}_${trace}_syn")"
    echo "$SETUP_CMDS && $test_cmd; read"
}

first="${jobs[0]}"
tmux new-session -d -s "$SESSION" -n "$first"
tmux send-keys -t "$SESSION:$first" "$(run_command_for "$first")" C-m

for job in "${jobs[@]:1}"; do
    tmux new-window -t "$SESSION" -n "$job"
    tmux send-keys -t "$SESSION:$job" "$(run_command_for "$job")" C-m
done

echo "$HOST_SHORT: started ${#jobs[@]} run(s) with $LEARNER, all concurrent, run date $RUN_DATE"
echo "  jobs: ${jobs[*]}"
echo "  logs: $LOGDIR"
