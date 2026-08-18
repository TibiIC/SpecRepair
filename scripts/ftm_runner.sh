#!/bin/bash
# Filter (semantically unique -> strongest guarantees) then merge, per run.
# Output unbuffered: no pipe, so stage counts appear as they happen.
source /vol/bitbucket/tg4018/anaconda3/etc/profile.d/conda.sh
conda activate logic
source ~/phd_work.sh >/dev/null 2>&1
export SPEC_REPAIR_TOOLS=${SPEC_REPAIR_TOOLS:-/vol/bitbucket/tg4018/Tools}
export PATH=$PATH:$SPEC_REPAIR_TOOLS/bin
export SPEC_REPAIR_LTLFILT=/vol/bitbucket/tg4018/spot-maxacc/bin/ltlfilt
export LD_LIBRARY_PATH=/vol/bitbucket/tg4018/spot-maxacc/lib:$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
cd /vol/bitbucket/tg4018/PhD/SpecRepair
ROOT=tests/test_files/out/case_study_3
for prefix in "$@"; do
    for d in $ROOT/${prefix}_trace*_fastlas_2026-08-13; do
        [ -d "$d" ] || continue
        # find, not a glob: `ls "$d/final_specs"/*.spectra` dies with
        # "Argument list too long" once a pool passes ARG_MAX (~2MB of argv,
        # about 20k paths here). ls then prints nothing, wc reports 0, and
        # 2>/dev/null hides the error - so the *largest* runs were silently
        # skipped as though they had produced no results at all.
        n=$(find "$d/final_specs" -maxdepth 1 -name '*.spectra' 2>/dev/null | wc -l)
        [ "$n" -gt 0 ] || continue
        echo "##### $(basename $d) ($n final specs)"
        timeout 21600 python -u scripts/filter_then_merge.py "$d" --max-inputs 600
        echo "  rc=$?"
    done
done
echo "DONE on $(hostname -s)"
