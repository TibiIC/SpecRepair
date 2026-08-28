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
    # A prefix names a case study and matches all its traces; an exact run name
    # matches just that one, so a slow case study can be split across boxes
    # instead of three of them racing to write the same PNGs.
    if [ -d "$ROOT/${prefix}_fastlas_2026-08-13" ]; then
        targets="$ROOT/${prefix}_fastlas_2026-08-13"
    else
        targets="$ROOT/${prefix}_trace*_fastlas_2026-08-13"
    fi
    for d in $targets; do
        [ -d "$d" ] || continue
        # Prefer the newest pipeline's output. five_step_specs is the five-step
        # result; maximal_merged_specs came from the merge-first enumeration
        # (genbuf trace 1 only); filtered_merged_specs is the original greedy
        # merge. Without the fallbacks a run merged by anything but the greedy
        # pipeline is silently skipped, which is how genbuf stayed off the
        # atlas entirely.
        # FIVE_STEP_ONLY=1 refuses to fall back, so a half-finished sweep
        # cannot quietly draw some runs from the five-step merge and others from
        # the greedy one - an atlas mixing two pipelines is worse than an
        # incomplete one, because nothing on the page says which is which.
        CANDIDATES="five_step_specs maximal_merged_specs filtered_merged_specs"
        [ "${FIVE_STEP_ONLY:-0}" = "1" ] && CANDIDATES="five_step_specs"
        merged=""
        for candidate in $CANDIDATES; do
            n=$(ls "$d/$candidate"/*.spectra 2>/dev/null | wc -l)
            if [ "$n" -gt 0 ]; then merged="$d/$candidate"; break; fi
        done
        n=$(ls "$merged"/*.spectra 2>/dev/null | wc -l)
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
        # A fourth group for the guarantee comparison only: what step 4 left,
        # just before the merge. Seeing original, trivial, strongest-unique and
        # merged on one picture shows how much of the distance from the floor to
        # the ceiling the merge itself closes.
        strongest="$d/strongest_specs"
        sn=$(ls "$strongest"/*.spectra 2>/dev/null | wc -l)
        echo "  merge source: $(basename $merged) ($n spec(s))"
        # asm and gar only. The whole-GR1 graph costs an hour per trace and
        # times out on amba every time (rc=124), and the comparison being asked
        # of these pictures is between assumptions and between guarantees - the
        # combined view answers neither. GRAPH_TYPES="asm gar gr1" restores it.
        if [ "$sn" -gt 0 ]; then
            echo "  strongest: $sn spec(s)"
            timeout ${GRAPH_TIMEOUT:-3600} python -u scripts/visualise_resulting_specs.py \
                -o "$d/corrected_graph_gar_strongest.png" -t gar --legend compact \
                "${groups[@]}" --group "strongest=$strongest" > /dev/null 2>&1
            rc=$?
            [ "$rc" -eq 0 ] && echo "  gar+strongest ok" \
                            || echo "  gar+strongest FAILED rc=$rc"
        fi
        for t in ${GRAPH_TYPES:-asm gar}; do
            # GRAPH_TIMEOUT seconds per graph. An hour is plenty for most
            # runs and not enough for genbuf, whose 81 guarantees make every
            # implication check expensive even though its merged set is one
            # specification - asm and gar both hit rc=124 on traces 0, 1 and 2.
            timeout ${GRAPH_TIMEOUT:-3600} python -u scripts/visualise_resulting_specs.py \
                -o "$d/corrected_graph_${t}.png" -t "$t" --legend compact \
                "${groups[@]}" > /dev/null 2>&1
            rc=$?
            [ "$rc" -eq 0 ] && echo "  $t ok" || echo "  $t FAILED rc=$rc"
        done
    done
done
echo "GRAPHS DONE on $(hostname -s)"
