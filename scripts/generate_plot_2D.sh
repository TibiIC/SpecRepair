#!/bin/bash

# Get current date in _YYYY-MM-DD format
date=$(date +_%Y-%m-%d)

# Define array of tuples (folder path and file1 path)
declare -a experiments=(
    "tests/test_files/out/arbiter input-files/case-studies/spectra/arbiter/ideal.spectra input-files/case-studies/spectra/arbiter/strong.spectra"
    "tests/test_files/out/lift input-files/case-studies/spectra/lift/ideal.spectra input-files/case-studies/spectra/lift/strong.spectra"
    "tests/test_files/out/minepump input-files/case-studies/spectra/minepump/ideal.spectra input-files/case-studies/spectra/minepump/strong.spectra"
    "tests/test_files/out/traffic_single input-files/case-studies/spectra/traffic-single/ideal.spectra input-files/case-studies/spectra/traffic-single/strong.spectra"
    "tests/test_files/out/traffic_updated input-files/case-studies/spectra/traffic-updated/ideal.spectra input-files/case-studies/spectra/traffic-updated/strong.spectra"
)

for pair in "${experiments[@]}"; do
    # Split the pair into folder and file1
    folder=$(echo $pair | cut -d' ' -f1)
    file1=$(echo $pair | cut -d' ' -f2)
    file2=$(echo $pair | cut -d' ' -f3)

    # Run the script with the folder and file1 as arguments
    python scripts/generate_plot_weakness_scatter_2D.py "$folder$date" -v --ideal-spec "$file1" --original-spec "$file2" -o "$folder$date/scatter_plot_2D.png" > "$folder$date/output_scatter_plot_2D.txt" 2>&1 &
done

# Wait for all background processes to complete
wait