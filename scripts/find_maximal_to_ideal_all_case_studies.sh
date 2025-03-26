#!/bin/bash

# Save the current directory
ORIGINAL_DIR=$(pwd)

# Set working directory
# WORKDIR="/Users/tg4018/Documents/PhD/SpecRepair"
# cd "$WORKDIR" || { echo "Directory $WORKDIR not found! Exiting."; exit 1; }

# Activate Conda
# ENV_PATH="/Users/tg4018/opt/anaconda3/envs/logic"
# source "$(conda info --base)/etc/profile.d/conda.sh"
# conda activate "$ENV_PATH" || { echo "Failed to activate Conda environment: $ENV_PATH"; exit 1; }

# Define input and output arrays
INPUT_SPECS=(
    "tests/test_files/out/traffic_non_unique_eventually"
    "tests/test_files/out/traffic_non_unique_no_eventually"
    "tests/test_files/out/minepump_test_bfs_non_unique_no_eventually"
    "tests/test_files/out/minepump_test_bfs_non_unique"
    "tests/test_files/out/arbiter_test_bfs_non_unique"
    "tests/test_files/out/arbiter_test_bfs_non_unique_no_eventually"
    "tests/test_files/out/lift_non_unique_no_eventually"
    "tests/test_files/out/lift_non_unique_eventually"
    "tests/test_files/out/traffic_single_non_unique_no_eventually"
    "tests/test_files/out/traffic_single_non_unique_eventually"
)

INPUT_IDEAL=(
    "input-files/case-studies/spectra/traffic-updated/ideal.spectra"
    "input-files/case-studies/spectra/traffic-updated/ideal.spectra"
    "input-files/case-studies/spectra/minepump/ideal.spectra"
    "input-files/case-studies/spectra/minepump/ideal.spectra"
    "input-files/case-studies/spectra/arbiter/ideal.spectra"
    "input-files/case-studies/spectra/arbiter/ideal.spectra"
    "input-files/case-studies/spectra/lift/ideal.spectra"
    "input-files/case-studies/spectra/lift/ideal.spectra"
    "input-files/case-studies/spectra/traffic-single/ideal.spectra"
    "input-files/case-studies/spectra/traffic-single/ideal.spectra"
)

OUTPUT_FILES=(
    "scripts/maximal_outputs/to_ideal/traffic_updated_non_unique_eventually_fixed.txt"
    "scripts/maximal_outputs/to_ideal/traffic_updated_non_unique_no_eventually_fixed.txt"
    "scripts/maximal_outputs/to_ideal/minepump_non_unique_no_eventually.txt"
    "scripts/maximal_outputs/to_ideal/minepump_non_unique_eventually.txt"
    "scripts/maximal_outputs/to_ideal/arbiter_non_unique_eventually.txt"
    "scripts/maximal_outputs/to_ideal/arbiter_non_unique_no_eventually.txt"
    "scripts/maximal_outputs/to_ideal/lift_non_unique_no_eventually.txt"
    "scripts/maximal_outputs/to_ideal/lift_non_unique_eventually.txt"
    "scripts/maximal_outputs/to_ideal/traffic_single_non_unique_no_eventually.txt"
    "scripts/maximal_outputs/to_ideal/traffic_single_non_unique_eventually.txt"
)

echo "Running tasks in parallel..."
# Run tasks in parallel
for ((i=0; i<${#INPUT_SPECS[@]}; i++)); do
    python scripts/find_maximal_to_ideal_specs.py -i "${INPUT_IDEAL[i]}" -s "${INPUT_SPECS[i]}" &> "${OUTPUT_FILES[i]}" &
done

# Wait for all processes to complete
wait

# Return to the original directory (with a safety check)
cd "$ORIGINAL_DIR" || { echo "Failed to return to the original directory: $ORIGINAL_DIR. Exiting."; exit 1; }

echo "All tasks completed!"