# The command a sweep window actually runs, shared by all three runners.
#
# Two properties the previous inline version did not have, both learned from the
# 2026-08-08 FastLAS sweep, where five runs died leaving no trace of how:
#
#   * `python ... | tee LOG` reports *tee's* exit status, and nothing recorded
#     python's. A run killed mid-BFS therefore looked exactly like one still
#     queued behind the semaphore - the sweep log's last line was an ordinary
#     progress line either way. `${PIPESTATUS[0]}` is written to
#     <job>.exitcode, so "finished cleanly" (0), "failed its assertion" (1) and
#     "was killed" (128+signal) are afterwards distinguishable without guessing.
#     PIPESTATUS rather than `set -o pipefail`: the pipeline's own status is
#     wanted, not a promoted failure, and it needs no shell option that the
#     rest of the window then inherits.
#
#   * python's stdout is block-buffered when piped, so a hard death discards
#     whatever had not filled the buffer - which is exactly the part naming the
#     cause. `-u` costs nothing at this output volume.
#
# The exitcode file is written *after* the pipeline and before anything else, so
# PIPESTATUS still refers to it.
#
# `\${PIPESTATUS[0]}` stays literal all the way to the tmux window: it is
# expanded there, at run time, not by the shell building the string.

# Build the "run one test, record how it ended" command.
#   $1 logdir, $2 job name (used for <job>.log and <job>.exitcode), $3 unittest target
job_test_cmd() {
    local logdir="$1" job="$2" target="$3"
    echo "python -u -m unittest ${target} 2>&1 | tee $logdir/${job}.log; echo \"\${PIPESTATUS[0]}\" > $logdir/${job}.exitcode"
}
