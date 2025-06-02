#!/bin/bash

# Define array of tuples (folder path and file path)
declare -a experiments=(
    "tests/test_files/out/arbiter input_files/case_studies/spectra/arbiter/ideal.spectra"
    "tests/test_files/out/lift input_files/case_studies/spectra/lift/ideal.spectra"
    "tests/test_files/out/minepump input_files/case_studies/spectra/minepump/ideal.spectra"
    "tests/test_files/out/traffic-single input_files/case_studies/spectra/traffic-single/ideal.spectra"
    "tests/test_files/out/traffic-updated input_files/case_studies/spectra/traffic-updated/ideal.spectra"
)

date="_2025-06-01"

for pair in "${experiments[@]}"; do
    # Split the pair into folder and file
    folder=$(echo $pair | cut -d' ' -f1)
    file=$(echo $pair | cut -d' ' -f2)

    # Run the script with the folder and file as arguments
    python generate_statistics_row.py "$folder$date" -v --ideal-spec "$file" -o "$folder$date/statistics.csv" > "$folder$date/output.txt" 2>&1 &
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
python generate_statistics_table.py "${args[@]}" -o all_statistics.csv
python generate_statistics_table.py "${args[@]}" -o all_statistics.tex --latex
