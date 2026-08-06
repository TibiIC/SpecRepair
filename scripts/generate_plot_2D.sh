#!/bin/bash

# Get current date in _YYYY-MM-DD format
# Which run to target. Defaults to today; set EXPERIMENT_DATE to point at
# an earlier one, e.g. EXPERIMENT_DATE=_2025-11-19 ./scripts/generate_plots.sh
date="${EXPERIMENT_DATE:-$(date +_%Y-%m-%d)}"

# Define array of tuples (folder path and file1 path)
declare -a experiments=(
    "tests/test_files/out/arbiter input-files/case-studies/spectra/case_study_1/arbiter/ideal.spectra input-files/case-studies/spectra/case_study_1/arbiter/strong.spectra"
    "tests/test_files/out/lift input-files/case-studies/spectra/case_study_1/lift/ideal.spectra input-files/case-studies/spectra/case_study_1/lift/strong.spectra"
    "tests/test_files/out/minepump input-files/case-studies/spectra/case_study_1/minepump/ideal.spectra input-files/case-studies/spectra/case_study_1/minepump/strong.spectra"
    "tests/test_files/out/traffic_single input-files/case-studies/spectra/case_study_1/traffic-single/ideal.spectra input-files/case-studies/spectra/case_study_1/traffic-single/strong.spectra"
    "tests/test_files/out/traffic_updated input-files/case-studies/spectra/case_study_1/traffic-updated/ideal.spectra input-files/case-studies/spectra/case_study_1/traffic-updated/strong.spectra"
)

for pair in "${experiments[@]}"; do
    # Split the pair into folder and file1
    folder=$(echo $pair | cut -d' ' -f1)
    file1=$(echo $pair | cut -d' ' -f2)
    file2=$(echo $pair | cut -d' ' -f3)

    # Run the script with the folder and file1 as arguments
    python -u scripts/generate_plot_weakness_scatter_2D.py "$folder$date" -v --ideal-spec "$file1" --original-spec "$file2" -o "$folder$date/scatter_plot_2D.png" > "$folder$date/output_scatter_plot_2D.txt" 2>&1 &
done

# Wait for all background processes to complete
wait
