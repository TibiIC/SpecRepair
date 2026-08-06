# A counting semaphore over tmux windows, backed by files on the shared NFS.
#
# All windows are created up front so the sweep is visible at a glance, but only
# MAX_WINDOWS of them run a test at a time - without a cap, 60 simultaneous JVMs
# exhaust memory on the box, and even 19 was enough to cause the OOM failures on
# the strengthened sweep.
#
# Free and taken slots live in SEPARATE directories, which is the whole trick.
# They used to share one, with a claimed slot renamed in place to
# slot_<n>.taken.<pid> - but the waiting glob is slot_*, which matches
# slot_0.taken.123 exactly as happily as slot_0. Waiting windows therefore
# claimed already-claimed slots, chaining names into slot_0.taken.X.taken.Y, and
# the release mv failed with "cannot stat" because another window had renamed the
# file again. Measured on the 2026-08-06 16:30 sweep: 0 free slots and 39
# concurrent runs against a cap of 8.
#
# Shared by both runners so the two cannot drift apart - the bug above existed in
# one of them only because the other had no cap at all.

slots_init() {
    # $1 logdir, $2 max concurrent
    local logdir="$1" max="$2"
    [[ "$max" -gt 0 ]] || return 0
    mkdir -p "$logdir/.slots" "$logdir/.slots_busy"
    local i
    for ((i = 0; i < max; i++)); do
        touch "$logdir/.slots/slot_$i"
    done
}

# Wrap a command so it waits for a free slot, runs, then releases it.
# The release is trapped on EXIT/INT/TERM as well: a slot leaked by a killed run
# is one fewer run for the whole rest of the sweep.
slots_wrap() {
    # $1 logdir, $2 max concurrent, $3 the command to run
    local logdir="$1" max="$2" cmd="$3"
    local free="$logdir/.slots" busy="$logdir/.slots_busy"
    if [[ "$max" -le 0 ]]; then
        echo "$cmd"
        return 0
    fi
    echo "while true; do for s in $free/slot_*; do [ -e \"\$s\" ] && mv \"\$s\" \"$busy/\$(basename \"\$s\").\$\$\" 2>/dev/null && { export MY_SLOT=\"\$s\"; break 2; }; done; sleep 5; done; trap 'mv \"$busy/\$(basename \"\$MY_SLOT\").\$\$\" \"\$MY_SLOT\" 2>/dev/null' EXIT INT TERM; $cmd; trap - EXIT INT TERM; mv \"$busy/\$(basename \"\$MY_SLOT\").\$\$\" \"\$MY_SLOT\""
}
