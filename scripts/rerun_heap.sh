#!/bin/bash
# Re-run one case_study_3 experiment with a real JVM heap, into the original
# 2026-08-13 output directory.
#   rerun_heap.sh <case_study> <trace_no>
#
# Why this exists: run_case_study_3.sh exports the learner, its run count, the
# timeout, the run date and the Spectra call log dir - but not the heap. Unset,
# the JVM takes a quarter of RAM, about 15.5GB of a 62GB box. colorsort learns
# its candidates in seconds and then loses every one of them to an
# OutOfMemoryError during synthesis, which `_synthesise_or_reject` turns into
# SpecificationNotVerifiableException; the search records "cannot verify", moves
# on, and finishes reporting no repair. Measured on trace 2: three candidates
# failed verification in 46m, 1h59m and 30m, and the run ended with nothing.
#
# MARCO cores are on for the same reason they are in rerun_marco.sh: colorsort
# is the largest case study here at 20 violated assumptions, and Syntech's
# exploreAllCores does not finish at that size.
source /vol/bitbucket/tg4018/anaconda3/etc/profile.d/conda.sh
conda activate logic
source ~/sdkman_init.sh >/dev/null 2>&1 || source ~/.sdkman/bin/sdkman-init.sh >/dev/null 2>&1
source ~/phd_work.sh >/dev/null 2>&1
export SPEC_REPAIR_TOOLS=${SPEC_REPAIR_TOOLS:-/vol/bitbucket/tg4018/Tools}
export PATH=$PATH:$SPEC_REPAIR_TOOLS/bin
export SPEC_REPAIR_LTLFILT=/vol/bitbucket/tg4018/spot-maxacc/bin/ltlfilt
export SPEC_REPAIR_CRASH_DIR=/vol/bitbucket/tg4018/crash
export LD_LIBRARY_PATH=/vol/bitbucket/tg4018/spot-maxacc/lib:$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
export SPEC_REPAIR_RUN_DATE=2026-08-13
export SPEC_REPAIR_MARCO_CORES=1
export SPEC_REPAIR_LEARNER=fastlas
export SPEC_REPAIR_FASTLAS_RUNS=10
export SPEC_REPAIR_JVM_HEAP=${SPEC_REPAIR_JVM_HEAP:-48g}
export SPEC_REPAIR_SPECTRA_CALL_LOG_DIR=${SPEC_REPAIR_SPECTRA_CALL_LOG_DIR:-/vol/bitbucket/tg4018/rerun_logs/jvm}
cd /vol/bitbucket/tg4018/PhD/SpecRepair
mkdir -p /vol/bitbucket/tg4018/rerun_logs "$SPEC_REPAIR_SPECTRA_CALL_LOG_DIR"
L=/vol/bitbucket/tg4018/rerun_logs/${1}_trace${2}.heap.log
echo "=== $1 trace $2 (heap=$SPEC_REPAIR_JVM_HEAP, MARCO cores) on $(hostname -s) started $(date +%F_%T) ===" > $L
python -u -m unittest tests.test_main.test_case_study_3.TestCaseStudy3.test_case_study_3_${1}_${2}_syn >> $L 2>&1
echo "rc=$? finished $(date +%F_%T)" >> $L
