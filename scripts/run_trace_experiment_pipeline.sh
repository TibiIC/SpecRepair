#!/bin/bash

# Post-processes a pulled trace-violation experiment: steps 2-6 for every
# <case_study>_trace<ID>_<date> run of one date.
#
# The counterpart to running run_experiment_pipeline.py over the strengthened
# case studies. Same pipeline - merge, maximal, semantically unique, graph - with
# --setup trace_violation, so the graphs reference original.spectra instead of
# the strong.spectra/ideal.spectra pair that setup does not have.
#
# Usage:
#   ./run_trace_experiment_pipeline.sh 2026-07-30
#   ./run_trace_experiment_pipeline.sh 2026-07-30 minepump_trace0   # one run
#   SKIP_GRAPH=1 ./run_trace_experiment_pipeline.sh 2026-07-30
#
# Step 1, pulling the runs from the remote, is pull_experiment_from_ssh.sh with
# REMOTE_SUBDIR=repair_trace_syn:
#
#   REMOTE_SUBDIR=repair_trace_syn ./scripts/pull_experiment_from_ssh.sh 2026-07-30

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <date> [case_study_run]" >&2
    echo "  e.g. $0 2026-07-30" >&2
    echo "       $0 2026-07-30 minepump_trace0" >&2
    exit 2
fi

DATE="$1"
CASE_STUDY="${2:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

# The conda environment is activated here rather than assumed, matching
# find_maximal_all_case_studies.sh - these are run by hand, often from a shell
# that has not sourced anything.
ENV_NAME="${CONDA_ENV:-arm_env}"
if [[ -z "${CONDA_DEFAULT_ENV:-}" || "${CONDA_DEFAULT_ENV}" != *"${ENV_NAME}" ]]; then
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "$ENV_NAME" || {
        echo "Failed to activate conda environment '$ENV_NAME'. Set CONDA_ENV to override." >&2
        exit 1
    }
fi

args=("$DATE" "--setup" "trace_violation")
[[ -n "$CASE_STUDY" ]] && args+=("--case-study" "$CASE_STUDY")
[[ -n "${SKIP_GRAPH:-}" ]] && args+=("--skip-graph")
[[ -n "${GRAPH_TYPE:-}" ]] && args+=("--graph-type" ${GRAPH_TYPE})
[[ -n "${LEGEND:-}" ]] && args+=("--legend" "${LEGEND}")

echo "Post-processing trace-violation runs for ${DATE}${CASE_STUDY:+ (${CASE_STUDY})}"
python scripts/run_experiment_pipeline.py "${args[@]}"
