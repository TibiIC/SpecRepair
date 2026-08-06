# Refuse to start a sweep on top of a previous one.
#
# Both runner scripts already reject an exact session-name collision, which is
# not enough: a sweep left over under a *different* name is invisible to that
# check. One from an earlier naming scheme (`parallel_tests`, `trace_tests`)
# survived a relaunch on 2026-08-06 and had to be closed by hand, and a stray
# timing loop in an old session once wrote 241 stale specs into the directory a
# new run was writing to - results that looked genuine.
#
# Orphaned test processes matter just as much. Killing a tmux session does not
# always take its Python down, and a survivor keeps writing into the shared NFS
# output tree long after the session that started it is gone.
#
# Aborts by default rather than killing: another sweep on the same box may be
# deliberate. FORCE=1 kills what it finds and proceeds.

# Session names that mean "a sweep", including the pre-2026-08-06 ones.
SWEEP_SESSION_RE='^(case_study_[12]_|parallel_tests|trace_tests)'
SWEEP_PROC_RE='python -m unittest tests\.test_main\.test_case_study_'

assert_no_previous_sweep() {
    local this_session="$1"
    local stale_sessions stale_procs found=0

    stale_sessions=$(tmux list-sessions -F '#{session_name}' 2>/dev/null \
        | grep -E "$SWEEP_SESSION_RE" | grep -vx "$this_session" || true)
    stale_procs=$(pgrep -u "$USER" -f "$SWEEP_PROC_RE" 2>/dev/null || true)

    if [[ -n "$stale_sessions" ]]; then
        found=1
        echo "Previous sweep session(s) still open on $(hostname -s):" >&2
        while IFS= read -r s; do
            [[ -n "$s" ]] && echo "  $s ($(tmux list-windows -t "$s" 2>/dev/null | wc -l | tr -d ' ') windows)" >&2
        done <<< "$stale_sessions"
    fi

    if [[ -n "$stale_procs" ]]; then
        found=1
        echo "Orphaned test process(es) still running:" >&2
        while IFS= read -r p; do
            [[ -n "$p" ]] && echo "  $(ps -o pid=,etime=,args= -p "$p" 2>/dev/null | cut -c1-110)" >&2
        done <<< "$stale_procs"
    fi

    [[ "$found" -eq 0 ]] && return 0

    if [[ "${FORCE:-0}" != "1" ]]; then
        echo >&2
        echo "Refusing to start: a previous run would keep writing into the shared" >&2
        echo "output tree alongside this one. Close it, or re-run with FORCE=1." >&2
        exit 1
    fi

    echo "FORCE=1: closing them." >&2
    while IFS= read -r s; do
        [[ -n "$s" ]] && tmux kill-session -t "$s" 2>/dev/null && echo "  killed session $s" >&2
    done <<< "$stale_sessions"
    # Killing the session does not reliably take the JVM with it.
    if [[ -n "$stale_procs" ]]; then
        sleep 2
        pkill -u "$USER" -f "$SWEEP_PROC_RE" 2>/dev/null || true
        sleep 3
        pkill -9 -u "$USER" -f "$SWEEP_PROC_RE" 2>/dev/null || true
    fi
    if pgrep -u "$USER" -f "$SWEEP_PROC_RE" >/dev/null 2>&1; then
        echo "Could not clear every orphaned process - aborting rather than" >&2
        echo "running alongside one." >&2
        exit 1
    fi
    echo "  cleared." >&2
}
