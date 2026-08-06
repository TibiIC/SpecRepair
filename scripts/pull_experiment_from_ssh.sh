#!/bin/bash
#
# Step 1 of the experiment pipeline.
#
# Pulls everything run_case_study_1.sh produced on the remote for one
# date, into tests/test_files/out_ssh/<date>/.
#
# The remote writes each case study to
#   <REMOTE_BASE>/case_study_1/<case_study>_<date>/
# so pulling "all case studies for a date" is a glob on the folder suffix. The
# local layout mirrors that folder name exactly, so provenance stays obvious and
# the later pipeline steps can just look for *_<date> directories:
#
#   tests/test_files/out_ssh/<date>/<case_study>_<date>/
#       final_specs/ intermediate_specs/ log.txt graph.png ...
#
# Usage:
#   ./scripts/pull_experiment_from_ssh.sh 2026-07-27
#   ./scripts/pull_experiment_from_ssh.sh 2026-07-27 gpu11
#
set -euo pipefail

DATE="${1:-}"
REMOTE_HOST="${2:-${REMOTE_HOST:-gpu11}}"

if [[ -z "$DATE" ]]; then
    echo "Usage: $0 <date: YYYY-MM-DD> [remote_host]" >&2
    exit 2
fi
if ! [[ "$DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "ERROR: date must look like YYYY-MM-DD, got '$DATE'" >&2
    exit 2
fi

REMOTE_BASE="${REMOTE_BASE:-/vol/bitbucket/tg4018/PhD/SpecRepair/tests/test_files/out}"
REMOTE_SUBDIR="${REMOTE_SUBDIR:-case_study_1}"

# Resolve relative to this script, so the pull works from any cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOCAL_DEST="${LOCAL_DEST:-$REPO_ROOT/tests/test_files/out_ssh/$DATE}"

echo "Remote : $REMOTE_HOST:$REMOTE_BASE/$REMOTE_SUBDIR/*_$DATE"
echo "Local  : $LOCAL_DEST"

# List first so an empty result is a clear message rather than a confusing
# rsync/scp error about a glob that matched nothing.
run_dirs=$(ssh "$REMOTE_HOST" \
    "ls -d ${REMOTE_BASE}/${REMOTE_SUBDIR}/*_${DATE} 2>/dev/null || true")

if [[ -z "$run_dirs" ]]; then
    echo "ERROR: no run directories matching *_${DATE} under ${REMOTE_BASE}/${REMOTE_SUBDIR} on ${REMOTE_HOST}." >&2
    echo "       Check the date, or set REMOTE_BASE/REMOTE_SUBDIR if the remote layout differs." >&2
    exit 1
fi

mkdir -p "$LOCAL_DEST"

# Only `-a` and `-z` can be assumed: macOS ships openrsync, which reports itself
# as "rsync version 2.6.9 compatible" and rejects rsync 3.x's --info=. Probe for
# a summary flag rather than picking one, so the script works with either.
RSYNC_FLAGS=(-az)
if command -v rsync >/dev/null 2>&1; then
    if rsync --info=stats1 --list-only . >/dev/null 2>&1; then
        RSYNC_FLAGS+=(--info=stats1)
    elif rsync --stats --list-only . >/dev/null 2>&1; then
        RSYNC_FLAGS+=(--stats)
    fi
fi

count=0
failed=()
while read -r remote_dir; do
    [[ -z "$remote_dir" ]] && continue
    name="$(basename "$remote_dir")"
    echo "  pulling $name"
    # A single unreachable/corrupt run should not lose the other case studies
    # already pulled, so failures are collected and reported at the end.
    if command -v rsync >/dev/null 2>&1; then
        if ! rsync "${RSYNC_FLAGS[@]}" "$REMOTE_HOST:$remote_dir/" "$LOCAL_DEST/$name/"; then
            echo "  WARNING: failed to pull $name" >&2
            failed+=("$name")
            continue
        fi
    else
        # scp -r recreates the directory under the destination, so copy into the
        # parent rather than into a path that already ends in $name.
        if ! scp -qr "$REMOTE_HOST:$remote_dir" "$LOCAL_DEST/"; then
            echo "  WARNING: failed to pull $name" >&2
            failed+=("$name")
            continue
        fi
    fi
    count=$((count + 1))
done <<< "$run_dirs"

echo "Pulled $count case-study run(s) for $DATE into $LOCAL_DEST"
if (( ${#failed[@]} > 0 )); then
    echo "Failed to pull ${#failed[@]}: ${failed[*]}" >&2
    exit 1
fi
echo
echo "Next: python scripts/run_experiment_pipeline.py $DATE"
