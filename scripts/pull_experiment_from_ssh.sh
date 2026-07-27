#!/bin/bash
#
# Step 1 of the experiment pipeline.
#
# Pulls everything run_parallel_bfs_repair_syn.sh produced on the remote for one
# date, into tests/test_files/out_ssh/<date>/.
#
# The remote writes each case study to
#   <REMOTE_BASE>/repair_syn/<case_study>_<date>/
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
REMOTE_SUBDIR="${REMOTE_SUBDIR:-repair_syn}"

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

count=0
while read -r remote_dir; do
    [[ -z "$remote_dir" ]] && continue
    name="$(basename "$remote_dir")"
    echo "  pulling $name"
    if command -v rsync >/dev/null 2>&1; then
        rsync -az --info=stats1 "$REMOTE_HOST:$remote_dir/" "$LOCAL_DEST/$name/"
    else
        # scp -r recreates the directory under the destination, so copy into the
        # parent rather than into a path that already ends in $name.
        scp -qr "$REMOTE_HOST:$remote_dir" "$LOCAL_DEST/"
    fi
    count=$((count + 1))
done <<< "$run_dirs"

echo "Pulled $count case-study run(s) for $DATE into $LOCAL_DEST"
echo
echo "Next: python scripts/run_experiment_pipeline.py $DATE"
