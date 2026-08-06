#!/bin/bash

# Runs each test_case_study_1_*_syn case study in its own named tmux
# window, in parallel, for unattended background runs on the GPU box.

# List of test names (method names on TestCaseStudy1), one tmux
# window per entry.
#
# Select which group to run with the first argument:
#   ./run_case_study_1.sh            # all (default)
#   ./run_case_study_1.sh original   # the assumption-only fixtures
#   ./run_case_study_1.sh updated    # the *_updated fixtures
#
# Select the solver with LEARNER (default: ilasp):
#   LEARNER=fastlas ./run_case_study_1.sh
#   LEARNER=fastlas FASTLAS_RUNS=10 ./run_case_study_1.sh  # up to 10 solutions per step
# A FastLAS run writes to <case_study>_fastlas_<date> and so lands beside an
# ILASP run of the same date rather than overwriting it. ILASP runs keep the
# unsuffixed name every existing path was written against.
# Each *_updated case study shares its original's ideal.spectra but pairs it
# with a strong.spectra that strengthens at least one assumption AND at least
# one guarantee, so those runs exercise guarantee weakening too.
original_tests=(
    "test_case_study_1_amba_syn"
    "test_case_study_1_arbiter_syn"
    "test_case_study_1_traffic_single_syn"
    "test_case_study_1_traffic_updated_syn"
    "test_case_study_1_lift_syn"
    "test_case_study_1_minepump_syn"
    "test_case_study_1_colorsort_syn"
    "test_case_study_1_genbuf_syn"
    "test_case_study_1_gyro_syn"
    "test_case_study_1_elevator_syn"
    "test_case_study_1_humanoid_syn"
    "test_case_study_1_pcar_syn"
)

updated_tests=(
    "test_case_study_1_traffic_updated_updated_syn"
    "test_case_study_1_lift_updated_syn"
    "test_case_study_1_colorsort_updated_syn"
    "test_case_study_1_gyro_updated_syn"
    "test_case_study_1_elevator_updated_syn"
    "test_case_study_1_humanoid_updated_syn"
    "test_case_study_1_pcar_updated_syn"
)

case "${1:-all}" in
    original) tests=("${original_tests[@]}") ;;
    updated)  tests=("${updated_tests[@]}") ;;
    all)      tests=("${original_tests[@]}" "${updated_tests[@]}") ;;
    *)
        echo "Unknown group '$1'. Use one of: all (default), original, updated." >&2
        exit 1
        ;;
esac

# Name of the tmux session - group-scoped, so an "updated" run can be started
# alongside an already-running "original" one without the has-session check
# below rejecting it.
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
# Session and log directory are learner-scoped, so a FastLAS sweep can run
# alongside an ILASP one without the has-session check below rejecting it.
SESSION="case_study_1_${1:-all}_${LEARNER}"
CONDA_ENV="logic"
WORKDIR="/vol/bitbucket/tg4018/PhD/SpecRepair"  # Optional working directory
LOGDIR="$WORKDIR/logs/case_study_1/${1:-all}_${LEARNER}_$(date +%Y-%m-%d_%H%M%S)"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "tmux session '$SESSION' already exists - attach to it, or rename/kill it before re-running this script." >&2
    exit 1
fi

# Refuse to start on top of a previous sweep, including one left under an older
# session name - the exact-name check below only catches a collision with *this*
# run's name.
source "$(dirname "${BASH_SOURCE[0]}")/lib/sweep_guard.sh"
assert_no_previous_sweep "$SESSION"

mkdir -p "$LOGDIR"

# Cap concurrency. This sweep had none: all 19 tests started at once, 19
# simultaneous JVMs, which is the condition behind the OutOfMemoryError failures
# seen on the strengthened runs. Set MAX_WINDOWS=0 for the old uncapped
# behaviour. The semaphore itself is shared with run_case_study_2.sh so the two
# cannot drift apart.
MAX_WINDOWS="${MAX_WINDOWS:-8}"
if ! [[ "$MAX_WINDOWS" =~ ^[0-9]+$ ]]; then
    echo "MAX_WINDOWS='$MAX_WINDOWS' must be a non-negative integer." >&2; exit 1
fi
source "$(dirname "${BASH_SOURCE[0]}")/lib/slots.sh"
slots_init "$LOGDIR" "$MAX_WINDOWS"

# Define the setup commands
SETUP_CMDS="source ~/.sdkman/bin/sdkman-init.sh && source ~/phd_work.sh && conda activate $CONDA_ENV && export LD_LIBRARY_PATH=\$CONDA_PREFIX/lib:\$LD_LIBRARY_PATH && export SPEC_REPAIR_LEARNER=$LEARNER && export SPEC_REPAIR_FASTLAS_RUNS=$FASTLAS_RUNS && cd $WORKDIR"

# Create a new tmux session in detached mode, with the first test as window 0
run_command_for() {
    local test_name="$1"
    local test_cmd="python -m unittest tests.test_main.test_case_study_1.TestCaseStudy1.${test_name} 2>&1 | tee $LOGDIR/${test_name}.log"
    echo "$SETUP_CMDS && $(slots_wrap "$LOGDIR" "$MAX_WINDOWS" "$test_cmd"); read"
}

first_test="${tests[0]}"
tmux new-session -d -s "$SESSION" -n "$first_test"
tmux send-keys -t "$SESSION:$first_test" "$(run_command_for "$first_test")" C-m

# Remaining tests, each in its own named window
for test_name in "${tests[@]:1}"; do
    tmux new-window -t "$SESSION" -n "$test_name"
    tmux send-keys -t "$SESSION:$test_name" "$(run_command_for "$test_name")" C-m
done

echo "Started ${#tests[@]} tests with the $LEARNER learner in tmux session '$SESSION'. Logs under $LOGDIR"
if [[ "$MAX_WINDOWS" -gt 0 ]]; then
    echo "Concurrency capped at $MAX_WINDOWS; the rest wait for a free slot."
fi
echo "Attach with: tmux attach -t $SESSION"

# Attach to the session
# tmux attach -t $SESSION
