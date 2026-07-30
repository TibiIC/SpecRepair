#!/bin/bash

# Runs each test_bfs_repair_spec_*_syn case study in its own named tmux
# window, in parallel, for unattended background runs on the GPU box.

# List of test names (method names on TestBFSRepairOrchestrator), one tmux
# window per entry.
#
# Select which group to run with the first argument:
#   ./run_parallel_bfs_repair_syn.sh            # all (default)
#   ./run_parallel_bfs_repair_syn.sh original   # the assumption-only fixtures
#   ./run_parallel_bfs_repair_syn.sh updated    # the *_updated fixtures
# Each *_updated case study shares its original's ideal.spectra but pairs it
# with a strong.spectra that strengthens at least one assumption AND at least
# one guarantee, so those runs exercise guarantee weakening too.
original_tests=(
    "test_bfs_repair_spec_arbiter_syn"
    "test_bfs_repair_spec_traffic_single_syn"
    "test_bfs_repair_spec_traffic_updated_syn"
    "test_bfs_repair_spec_lift_syn"
    "test_bfs_repair_spec_minepump_syn"
    "test_bfs_repair_spec_colorsort_syn"
    "test_bfs_repair_spec_gyro_syn"
    "test_bfs_repair_spec_elevator_syn"
    "test_bfs_repair_spec_humanoid_syn"
    "test_bfs_repair_spec_pcar_syn"
)

updated_tests=(
    "test_bfs_repair_spec_traffic_updated_updated_syn"
    "test_bfs_repair_spec_lift_updated_syn"
    "test_bfs_repair_spec_colorsort_updated_syn"
    "test_bfs_repair_spec_gyro_updated_syn"
    "test_bfs_repair_spec_elevator_updated_syn"
    "test_bfs_repair_spec_humanoid_updated_syn"
    "test_bfs_repair_spec_pcar_updated_syn"
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
SESSION="parallel_tests_${1:-all}"
CONDA_ENV="logic"
WORKDIR="/vol/bitbucket/tg4018/PhD/SpecRepair"  # Optional working directory
LOGDIR="$WORKDIR/logs/parallel_tests/${1:-all}_$(date +%Y-%m-%d_%H%M%S)"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "tmux session '$SESSION' already exists - attach to it, or rename/kill it before re-running this script." >&2
    exit 1
fi

mkdir -p "$LOGDIR"

# Define the setup commands
SETUP_CMDS="source ~/.sdkman/bin/sdkman-init.sh && source ~/phd_work.sh && conda activate $CONDA_ENV && export LD_LIBRARY_PATH=\$CONDA_PREFIX/lib:\$LD_LIBRARY_PATH && cd $WORKDIR"

# Create a new tmux session in detached mode, with the first test as window 0
first_test="${tests[0]}"
tmux new-session -d -s "$SESSION" -n "$first_test"
tmux send-keys -t "$SESSION:$first_test" \
    "$SETUP_CMDS && python -m unittest tests.test_main.test_bfs_repair_orchestrator.TestBFSRepairOrchestrator.${first_test} 2>&1 | tee $LOGDIR/${first_test}.log && read" C-m

# Remaining tests, each in its own named window
for test_name in "${tests[@]:1}"; do
    tmux new-window -t "$SESSION" -n "$test_name"
    tmux send-keys -t "$SESSION:$test_name" \
        "$SETUP_CMDS && python -m unittest tests.test_main.test_bfs_repair_orchestrator.TestBFSRepairOrchestrator.${test_name} 2>&1 | tee $LOGDIR/${test_name}.log && read" C-m
done

echo "Started ${#tests[@]} tests in tmux session '$SESSION'. Logs under $LOGDIR"
echo "Attach with: tmux attach -t $SESSION"

# Attach to the session
# tmux attach -t $SESSION
