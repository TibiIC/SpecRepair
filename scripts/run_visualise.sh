#!/bin/bash

# ----------------------------
# Config (edit these only)
# ----------------------------
SOURCE_DIR="../tests/test_files/out_ssh/merge_all/minepump_2026-06-03"
OUTPUT_FILE="../tests/test_files/out_ssh/merge_all/minepump_2026-06-03/viz_asms.png"
TYPE="asm"

# ----------------------------
# Run command
# ----------------------------
python visualise_resulting_specs.py \
  -s "$SOURCE_DIR" \
  -o "$OUTPUT_FILE" \
  -t "$TYPE"