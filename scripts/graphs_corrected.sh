#!/bin/bash
# Implication graphs from the *corrected* merges.
#
# Draws original / trivial / filtered_merged as groups, where filtered_merged is
# the result of semantically-unique -> strongest-guarantees -> merge. The
# `unique_max_merged_specs` directory holds the old merge-then-filter output and
# is deliberately not used.
source /vol/bitbucket/tg4018/anaconda3/etc/profile.d/conda.sh
conda activate logic
source ~/phd_work.sh >/dev/null 2>&1
export SPEC_REPAIR_TOOLS=${SPEC_REPAIR_TOOLS:-/vol/bitbucket/tg4018/Tools}
export PATH=$PATH:$SPEC_REPAIR_TOOLS/bin
# Spot rebuilt with --enable-max-accsets=128; stock Spot caps at 32 and the gr1
# graph exceeds that on any specification with enough liveness.
export SPEC_REPAIR_LTLFILT=/vol/bitbucket/tg4018/spot-maxacc/bin/ltlfilt
export SPEC_REPAIR_CRASH_DIR=/vol/bitbucket/tg4018/crash
export LD_LIBRARY_PATH=/vol/bitbucket/tg4018/spot-maxacc/lib:$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
cd /vol/bitbucket/tg4018/PhD/SpecRepair

ROOT=tests/test_files/out/case_study_3
TRIVIAL=tests/test_files/out/trivial_solutions/2026-08-13/all
SPECS=input-files/case-studies/spectra/case_study_3

for prefix in "$@"; do
    for d in $ROOT/${prefix}_trace*_fastlas_2026-08-13; do
        [ -d "$d" ] || continue
        merged="$d/filtered_merged_specs"
        n=$(ls "$merged"/*.spectra 2>/dev/null | wc -l)
        # A run merged by the merge-first pipeline has no filtered_merged_specs;
        # its output is maximal_merged_specs. genbuf trace 1 is the only one so
        # far, and without this it is silently skipped and genbuf never reaches
        # the atlas at all.
        if [ "$n" -eq 0 ]; then
            merged="$d/maximal_merged_specs"
            n=$(ls "$merged"/*.spectra 2>/dev/null | wc -l)
        fi
        [ "$n" -gt 0 ] || { echo "SKIP $(basename $d) - no corrected merge yet"; continue; }
        base=$(basename "$d" _fastlas_2026-08-13)
        case_study="${base%_trace*}"
        echo "=== $base ==="
        groups=(--group "original=$SPECS/$case_study/original.spectra")
        if [ -d "$TRIVIAL/$base" ]; then
            groups+=(--group "trivial=$TRIVIAL/$base")
        else
            echo "  (no trivial solutions - graph will have no floor)"
        fi
        groups+=(--group "corrected_merged=$merged")
        for t in asm gar gr1; do
            timeout 3600 python -u scripts/visualise_resulting_specs.py \
                -o "$d/corrected_graph_${t}.png" -t "$t" --legend compact \
                "${groups[@]}" > /dev/null 2>&1
            rc=$?
            [ "$rc" -eq 0 ] && echo "  $t ok" || echo "  $t FAILED rc=$rc"
        done
    done
done
echo "GRAPHS DONE on $(hostname -s)"
