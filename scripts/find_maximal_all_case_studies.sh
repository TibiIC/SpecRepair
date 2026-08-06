#!/bin/bash

# Save the current directory
ORIGINAL_DIR=$(pwd)

DATE="2026-06-03" #  $(date '+%Y-%m-%d')

# Set working directory
WORKDIR="/Users/tg4018/Documents/PhD/SpecRepair"
cd "$WORKDIR" || { echo "Directory $WORKDIR not found! Exiting."; exit 1; }

# Activate Conda
ENV_PATH="/Users/tg4018/miniforge3/envs/arm_env"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_PATH" || { echo "Failed to activate Conda environment: $ENV_PATH"; exit 1; }

# Define input and output arrays
INPUT_FILES=(
    # "tests/test_files/out/repair/traffic_updated_${DATE}"
    # "tests/test_files/out/repair/traffic_single_${DATE}"
    # "tests/test_files/out/repair/minepump_${DATE}"
    # "tests/test_files/out/repair/arbiter_${DATE}"
    # "tests/test_files/out/repair/lift_${DATE}"
    # "tests/test_files/out_ssh/case_study_1/arbiter_${DATE}/final"
    # "tests/test_files/out_ssh/case_study_1/minepump_${DATE}/final"
    "tests/test_files/out_ssh/case_study_1/lift_${DATE}/distinct"
    "tests/test_files/out_ssh/case_study_1/traffic_single_${DATE}/distinct"
    "tests/test_files/out_ssh/case_study_1/traffic_updated_${DATE}/distinct"
)

OUTPUT_FILES=(
    # "scripts/maximal_outputs/${DATE}/traffic_updated.txt"
    # "scripts/maximal_outputs/${DATE}/traffic_single.txt"
    # "scripts/maximal_outputs/${DATE}/minepump.txt"
    # "scripts/maximal_outputs/${DATE}/arbiter.txt"
    # "scripts/maximal_outputs/${DATE}/lift.txt"
    # "scripts/out_ssh/maximal_outputs/${DATE}/arbiter.txt"
    # "scripts/out_ssh/maximal_outputs/${DATE}/minepump.txt"
    "scripts/out_ssh/maximal_outputs/${DATE}/lift.txt"
    "scripts/out_ssh/maximal_outputs/${DATE}/traffic_single.txt"
    "scripts/out_ssh/maximal_outputs/${DATE}/traffic_updated.txt"
)

# Create output directory if it doesn't exist
mkdir -p "scripts/out_ssh/maximal_outputs/${DATE}"

# Run tasks in parallel
for i in "${!INPUT_FILES[@]}"; do
    python scripts/find_maximal_specifications.py "${INPUT_FILES[i]}" &> "${OUTPUT_FILES[i]}" &
done

# Wait for all processes to complete
wait

# Return to the original directory (with a safety check)
cd "$ORIGINAL_DIR" || { echo "Failed to return to the original directory: $ORIGINAL_DIR. Exiting."; exit 1; }

echo "All tasks completed!"