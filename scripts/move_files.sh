#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <source_dir> <destination_dir> <file_list.txt>"
    exit 1
fi

SOURCE_DIR="$1"
DEST_DIR="$2"
FILE_LIST="$3"

# Create destination directory if needed
mkdir -p "$DEST_DIR"

while IFS= read -r filename || [ -n "$filename" ]; do
    # Skip blank lines
    [[ -z "$filename" ]] && continue

    if [[ -e "$SOURCE_DIR/$filename" ]]; then
        cp "$SOURCE_DIR/$filename" "$DEST_DIR/"
        echo "Moved: $filename"
    else
        echo "Warning: '$filename' not found in $SOURCE_DIR" >&2
    fi
done < "$FILE_LIST"