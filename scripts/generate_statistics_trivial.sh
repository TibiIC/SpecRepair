#!/bin/bash

# Define array of tuples (folder path and file path)
declare -a experiments=(
    "tests/test_files/out/arbiter tests/test_files/out/trivial_solutions/arbiter.spectra"
    "tests/test_files/out/lift tests/test_files/out/trivial_solutions/lift.spectra"
    "tests/test_files/out/minepump tests/test_files/out/trivial_solutions/minepump.spectra"
    "tests/test_files/out/traffic_single tests/test_files/out/trivial_solutions/traffic-single.spectra"
    "tests/test_files/out/traffic_updated tests/test_files/out/trivial_solutions/traffic-updated.spectra"
)

# Which run to target. Defaults to today; set EXPERIMENT_DATE to point at
# an earlier one, e.g. EXPERIMENT_DATE=_2025-11-19 ./scripts/generate_plots.sh
date="${EXPERIMENT_DATE:-$(date +_%Y-%m-%d)}"

for pair in "${experiments[@]}"; do
    # Split the pair into folder and file
    folder=$(echo $pair | cut -d' ' -f1)
    file=$(echo $pair | cut -d' ' -f2)

    # Run the script with the folder and file as arguments
    python scripts/generate_statistics_row.py "$folder$date" -v --ideal-spec "$file" -o "$folder$date/statistics.csv" > "$folder$date/output.txt" 2>&1 &
done

# Wait for all background processes to complete
wait

# Build arguments array from experiments array
args=()
for pair in "${experiments[@]}"; do
    folder=$(echo "$pair" | cut -d' ' -f1)
    args+=("$folder$date/statistics.csv")
done

# Run generate_statistics_table.py with all statistics files
python scripts/generate_statistics_table.py "${args[@]}" -o all_statistics_trivial.csv
python scripts/generate_statistics_table.py "${args[@]}" -o all_statistics_trivial.tex --latex

