#!/bin/bash
# Status of a case-study experiment: post-processing jobs, still-running
# searches, graphs drawn, and the stage counts per run.
#
# Reads the filesystem only - no ssh, no fan-out. The lab boxes cannot ssh each
# other, and the work tree is on shared NFS, so a filesystem-only script gives
# the same answer from any of them:
#
#     ssh gpu20 bash /vol/bitbucket/tg4018/PhD/SpecRepair/scripts/experiment_status.sh
#
# Everything environment-specific is an override with a sensible default:
#
#   SPEC_REPAIR_WORK      base for the log trees      (default /vol/bitbucket/$USER)
#   SPEC_REPAIR_LOGS      job logs                    ($SPEC_REPAIR_WORK/postproc_logs)
#   SPEC_REPAIR_UNIQ_LOGS filter_then_merge --unique  ($SPEC_REPAIR_WORK/uniq_logs)
#   SPEC_REPAIR_FIVE_LOGS filter_then_merge --five    ($SPEC_REPAIR_WORK/five_logs)
#   EXPERIMENT_DATES      run dates to report on      (2026-08-29 2026-08-13)
#   SETUP                 case study directory        (case_study_3)
#   FRESH_SECONDS         "live" if written within    (1800)
#   SEARCH_WINDOW_DAYS    ignore search dirs older than  (7)
#
# Usage: experiment_status.sh [-d "<dates>"] [-s <setup>] [-h]
set -u

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
WORK="${SPEC_REPAIR_WORK:-/vol/bitbucket/$USER}"
LOGS="${SPEC_REPAIR_LOGS:-$WORK/postproc_logs}"
UNIQ_LOGS="${SPEC_REPAIR_UNIQ_LOGS:-$WORK/uniq_logs}"
FIVE_LOGS="${SPEC_REPAIR_FIVE_LOGS:-$WORK/five_logs}"
DATES="${EXPERIMENT_DATES:-2026-08-29 2026-08-13}"
SETUP="${SETUP:-case_study_3}"
FRESH="${FRESH_SECONDS:-1800}"
SEARCH_DAYS="${SEARCH_WINDOW_DAYS:-7}"    # ignore search dirs older than this

while getopts ":d:s:h" opt; do
  case $opt in
    d) DATES="$OPTARG" ;;
    s) SETUP="$OPTARG" ;;
    h) sed -n '2,25p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option -$OPTARG; -h for help" >&2; exit 2 ;;
  esac
done

OUT="$REPO_ROOT/tests/test_files/out/$SETUP"
SEARCH_LOGS="$REPO_ROOT/logs/$SETUP"
now=$(date +%s)

# GNU and BSD stat/date disagree; support both so this runs on the Mac too.
mtime() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null || echo 0; }
when()  { local e; e=$(mtime "$1")
          date -d "@$e" '+%m-%d %H:%M' 2>/dev/null || date -r "$e" '+%m-%d %H:%M' 2>/dev/null; }
fresh() { [ $(( now - $(mtime "$1") )) -lt "$FRESH" ] && echo live || echo quiet; }

echo "########## POST-PROCESSING ##########"
if compgen -G "$LOGS/ftm_*.log" >/dev/null; then
  printf "%-9s %-6s %-12s %s\n" JOB STATE UPDATED PROGRESS
  for f in "$LOGS"/ftm_*.log; do
    n=$(basename "$f" .log); n=${n#ftm_}
    if grep -q "##### DONE" "$f" 2>/dev/null; then st=done; else st=$(fresh "$f"); fi
    p=$(grep -aE "compared|##### DONE|stage [0-9]" "$f" 2>/dev/null | tail -1 | sed 's/^ *//' | cut -c1-52)
    printf "%-9s %-6s %-12s %s\n" "$n" "$st" "$(when "$f")" "$p"
  done
else
  echo "  no ftm_*.log under $LOGS"
fi

echo
echo "########## OTHER filter_then_merge RUNS (live only) ##########"
found=0
for f in "$UNIQ_LOGS"/*.log "$FIVE_LOGS"/*.log; do
  [ -f "$f" ] || continue
  [ "$(fresh "$f")" = live ] || continue
  [ $found -eq 0 ] && printf "%-34s %-12s %s\n" LOG UPDATED PROGRESS && found=1
  printf "%-34s %-12s %s\n" "$(basename "$f")" "$(when "$f")" \
    "$(tail -1 "$f" | sed 's/^ *//' | cut -c1-46)"
done
[ $found -eq 0 ] && echo "  none written in the last $((FRESH/60)) min"

echo
echo "########## SEARCHES WITHOUT AN EXITCODE (last $SEARCH_DAYS days) ##########"
echo "  A killed search leaves no exitcode either, so these are candidates, not"
echo "  proof of life. Check the host with: pgrep -af test_case_study"
found=0
cutoff=$(( now - SEARCH_DAYS * 86400 ))
for d in "$SEARCH_LOGS"/*/; do
  [ -d "$d" ] || continue
  # Killed sweeps never write an exitcode either, so "no exitcode" on its own
  # matches every historical run. Bound it to recently-touched directories.
  [ "$(mtime "$d")" -ge "$cutoff" ] || continue
  for lg in "$d"*.log; do
    [ -f "$lg" ] || continue
    b=${lg%.log}
    [ -f "$b.exitcode" ] && continue                 # finished, and said so
    found=1
    # A search with no exitcode did not finish, but that covers two cases the
    # filesystem cannot separate: still working in silence (GenBuf sits inside
    # one Spectra call for days without logging) and killed before it could
    # write one. Report both and let the date say which is plausible.
    printf "  %-22s %-6s %-12s %s\n" "$(basename "$b")" "$(fresh "$lg")" "$(when "$lg")" \
      "$(grep -a NODE "$lg" | tail -1 | cut -c1-42)"
  done
done
[ $found -eq 0 ] && echo "  none unfinished in the last $SEARCH_DAYS days"

echo
echo "########## GRAPHS ##########"
for g in asm gar gr1 asm_with_unique_min gar_with_unique_min; do
  printf "  %-22s %s\n" "$g" "$(ls "$OUT"/*/implication_graph_$g.png 2>/dev/null | wc -l)"
done

echo
echo "########## STAGE COUNTS ##########"
printf "%-44s %7s %7s %7s %7s\n" RUN final unique min merged
for date in $DATES; do
  for d in "$OUT"/*_"$date"; do
    [ -d "$d" ] || continue
    f=$(ls "$d/final_specs" 2>/dev/null | wc -l)
    [ "$f" -eq 0 ] && continue
    printf "%-44s %7s %7s %7s %7s\n" "$(basename "$d")" "$f" \
      "$(ls "$d/unique_specs" 2>/dev/null | wc -l)" \
      "$(ls "$d/max_unique_specs" 2>/dev/null | wc -l)" \
      "$(ls "$d/filtered_merged_specs" 2>/dev/null | wc -l)"
  done
done

cat <<'NOTE'

NOTE: "min" is max_unique_specs/ on disk. It holds the STRONGEST guarantees,
      which are semantically MINIMAL - the fewest behaviours allowed. The
      directory name is legacy and reads the wrong way round.
NOTE: GenBuf and ColorSort are past the LTL-to-automaton translation cliff
      (28 and 25 assumption conjuncts against a cliff at 20-23), so their
      semantic comparisons do not terminate in useful time.
NOTE
