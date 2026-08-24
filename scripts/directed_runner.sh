#!/bin/bash
# Design 3: descend from the original specification's unrealisable cores.
# Writes directed_merged_specs/, so it never collides with a --maximal run of
# the same run directory - both can be in flight at once.
source /vol/bitbucket/tg4018/anaconda3/etc/profile.d/conda.sh
conda activate logic
source ~/phd_work.sh >/dev/null 2>&1
export SPEC_REPAIR_TOOLS=${SPEC_REPAIR_TOOLS:-/vol/bitbucket/tg4018/Tools}
export PATH=$PATH:$SPEC_REPAIR_TOOLS/bin
export SPEC_REPAIR_LTLFILT=/vol/bitbucket/tg4018/spot-maxacc/bin/ltlfilt
export SPEC_REPAIR_CRASH_DIR=/vol/bitbucket/tg4018/crash
export SPEC_REPAIR_JVM_HEAP=${SPEC_REPAIR_JVM_HEAP:-48g}
export SPEC_REPAIR_SPECTRA_CALL_LOG_DIR=${SPEC_REPAIR_SPECTRA_CALL_LOG_DIR:-/vol/bitbucket/tg4018/max_logs/jvm}
export LD_LIBRARY_PATH=/vol/bitbucket/tg4018/spot-maxacc/lib:$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
cd /vol/bitbucket/tg4018/PhD/SpecRepair
mkdir -p /vol/bitbucket/tg4018/max_logs "$SPEC_REPAIR_SPECTRA_CALL_LOG_DIR"
DIR_WORKERS=${DIR_WORKERS:-8}
for r in "$@"; do
  L=/vol/bitbucket/tg4018/max_logs/${r}.directed.log
  echo "=== $r on $(hostname -s) started $(date +%F_%T) ===" > $L
  python -u scripts/filter_then_merge.py \
      tests/test_files/out/case_study_3/${r}_fastlas_2026-08-13 \
      --directed --workers $DIR_WORKERS >> $L 2>&1
  echo "rc=$? finished $(date +%F_%T)" >> $L
done
