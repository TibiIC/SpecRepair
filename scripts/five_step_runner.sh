#!/bin/bash
# The five-step post-processing pipeline, per run.
#   five_step_runner.sh <run> [<run>...]
#   RUN_DATE=2026-08-29 five_step_runner.sh <run> [<run>...]
# Writes five_step_specs/ and logs to /vol/bitbucket/tg4018/five_logs.
#
# RUN_DATE selects which sweep to post-process. It used to be hardcoded to
# 2026-08-13, which silently pointed every re-run at the old sweep's output -
# and the log name carries it too, so a re-merge of a different date cannot
# overwrite the log of the first.
source /vol/bitbucket/tg4018/anaconda3/etc/profile.d/conda.sh
conda activate logic
source ~/phd_work.sh >/dev/null 2>&1
export SPEC_REPAIR_TOOLS=${SPEC_REPAIR_TOOLS:-/vol/bitbucket/tg4018/Tools}
export PATH=$PATH:$SPEC_REPAIR_TOOLS/bin
export SPEC_REPAIR_LTLFILT=/vol/bitbucket/tg4018/spot-maxacc/bin/ltlfilt
export SPEC_REPAIR_CRASH_DIR=/vol/bitbucket/tg4018/crash
export SPEC_REPAIR_JVM_HEAP=${SPEC_REPAIR_JVM_HEAP:-48g}
export SPEC_REPAIR_SPECTRA_CALL_LOG_DIR=${SPEC_REPAIR_SPECTRA_CALL_LOG_DIR:-/vol/bitbucket/tg4018/five_logs/jvm}
export LD_LIBRARY_PATH=/vol/bitbucket/tg4018/spot-maxacc/lib:$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
cd /vol/bitbucket/tg4018/PhD/SpecRepair
mkdir -p /vol/bitbucket/tg4018/five_logs "$SPEC_REPAIR_SPECTRA_CALL_LOG_DIR"
RUN_DATE=${RUN_DATE:-2026-08-13}
for r in "$@"; do
  L=/vol/bitbucket/tg4018/five_logs/${r}_${RUN_DATE}.five.log
  # Never truncate. Re-running this once destroyed minepump trace 3's recorded
  # stage counts - hours of work whose only record was the log it overwrote.
  # The previous log is kept under its finish time, and the live one appends.
  if [ -f "$L" ]; then
    ts=$(grep -m1 "^rc=" "$L" | sed -E "s/.*finished //" | tr -d " :" )
    mv "$L" "${L%.log}.${ts:-$(date +%F_%H%M%S)}.log"
  fi
  echo "=== $r ($RUN_DATE) on $(hostname -s) started $(date +%F_%T) ===" >> $L
  python -u scripts/filter_then_merge.py \
      tests/test_files/out/case_study_3/${r}_fastlas_${RUN_DATE} \
      --five-step --workers ${FIVE_WORKERS:-8} >> $L 2>&1
  echo "rc=$? finished $(date +%F_%T)" >> $L
done
