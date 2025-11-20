#!/bin/bash

# Get current date in _YYYY-MM-DD format
date=$(date +_%Y-%m-%d)

# Define array of tuples (folder path and file path)
declare -a experiments=(
    "tests/test_files/out/arbiter input-files/case-studies/spectra/arbiter/ideal.spectra"
    "tests/test_files/out/lift input-files/case-studies/spectra/lift/ideal.spectra"
    "tests/test_files/out/minepump input-files/case-studies/spectra/minepump/ideal.spectra"
    "tests/test_files/out/traffic_single input-files/case-studies/spectra/traffic-single/ideal.spectra"
    "tests/test_files/out/traffic_updated input-files/case-studies/spectra/traffic-updated/ideal.spectra"
)

for pair in "${experiments[@]}"; do
    # Split the pair into folder and file
    folder=$(echo $pair | cut -d' ' -f1)
    file=$(echo $pair | cut -d' ' -f2)

    # Run the script with the folder and file as arguments
    python scripts/generate_plot_weakness.py "$folder$date" -v --ideal-spec "$file" --compare-type=ASM -o "$folder$date/bar_plot_asm.png" > "$folder$date/output_scatter_plot_asm.txt" 2>&1 &
    python scripts/generate_plot_weakness_scatter.py "$folder$date" -v --ideal-spec "$file" --compare-type=ASM -o "$folder$date/scatter_plot_asm.png" > "$folder$date/output_scatter_plot_asm.txt" 2>&1 &
    python scripts/generate_plot_weakness.py "$folder$date" -v --ideal-spec "$file" --compare-type=GAR -o "$folder$date/bar_plot_gar.png" > "$folder$date/output_scatter_plot_gar.txt" 2>&1 &
    python scripts/generate_plot_weakness_scatter.py "$folder$date" -v --ideal-spec "$file" --compare-type=GAR -o "$folder$date/scatter_plot_gar.png" > "$folder$date/output_scatter_plot_gar.txt" 2>&1 &
done

# Wait for all background processes to complete
wait