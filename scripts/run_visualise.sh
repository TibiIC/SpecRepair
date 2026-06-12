#!/bin/bash

# ----------------------------
# Config (edit these only)
# ----------------------------
SOURCE_DIR="../tests/test_files/out_ssh/repair_syn/arbiter_2026-06-03/final"
OUTPUT_FILE="../tests/test_files/out_ssh/repair_syn/arbiter_2026-06-03/viz_gars.png"
TYPE="gar"

# ----------------------------
# Run command
# ----------------------------
python visualise_resulting_specs.py \
  -s "$SOURCE_DIR" \
  -o "$OUTPUT_FILE" \
  -t "$TYPE"