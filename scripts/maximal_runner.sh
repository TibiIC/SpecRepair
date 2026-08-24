#!/bin/bash
# Merge-first: maximal realisable subsets of the pooled guarantees, then report
# the unique and strongest counts over the result. Takes a queue of run names
# and works through them in order, one at a time.
source /vol/bitbucket/tg4018/anaconda3/etc/profile.d/conda.sh
conda activate logic
source ~/phd_work.sh >/dev/null 2>&1
export SPEC_REPAIR_TOOLS=${SPEC_REPAIR_TOOLS:-/vol/bitbucket/tg4018/Tools}
export PATH=$PATH:$SPEC_REPAIR_TOOLS/bin
export SPEC_REPAIR_LTLFILT=/vol/bitbucket/tg4018/spot-maxacc/bin/ltlfilt
export SPEC_REPAIR_CRASH_DIR=/vol/bitbucket/tg4018/crash
# minepump trace 4 died with rc=139 after seven hours, on a pool of 12,148
# distinct guarantees - the largest specification anything here has handed
# Spectra. Unset, the JVM takes a quarter of RAM (~15.5GB of a 62GB box) and
# leaves the rest idle; jvm.py already names that default as what stops
# colorsort. No fatal-error log was written anywhere, so point one somewhere
# findable before asking again.
export SPEC_REPAIR_JVM_HEAP=${SPEC_REPAIR_JVM_HEAP:-48g}
export SPEC_REPAIR_SPECTRA_CALL_LOG_DIR=${SPEC_REPAIR_SPECTRA_CALL_LOG_DIR:-/vol/bitbucket/tg4018/max_logs/jvm}
export LD_LIBRARY_PATH=/vol/bitbucket/tg4018/spot-maxacc/lib:$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
cd /vol/bitbucket/tg4018/PhD/SpecRepair
mkdir -p /vol/bitbucket/tg4018/max_logs "$SPEC_REPAIR_SPECTRA_CALL_LOG_DIR"
MAX_WORKERS=${MAX_WORKERS:-8}
for r in "$@"; do
  L=/vol/bitbucket/tg4018/max_logs/${r}.max.log
  echo "=== $r on $(hostname -s) started $(date +%F_%T) ===" > $L
  python -u scripts/filter_then_merge.py \
      tests/test_files/out/case_study_3/${r}_fastlas_2026-08-13 \
      --maximal --workers $MAX_WORKERS >> $L 2>&1
  echo "rc=$? finished $(date +%F_%T)" >> $L
done
