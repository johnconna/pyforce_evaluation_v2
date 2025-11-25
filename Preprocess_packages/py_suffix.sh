#!/bin/bash

# Script: add_py_suffix.sh
# Description: Force add .py suffix to all files in version_files directory

TARGET_DIR="version_files"

echo "Starting to add .py suffix to files in $TARGET_DIR/"

# Check if directory exists
if [[ ! -d "$TARGET_DIR" ]]; then
    echo "Error: Directory '$TARGET_DIR' does not exist!"
    exit 1
fi

# Counter for renamed files
count=0

# Change to target directory
cd "$TARGET_DIR"

# Process all files in the directory
for file in *; do
    # Skip if it's a directory or special files
    if [[ -f "$file" ]]; then
        # Check if file already has .py extension
        if [[ "$file" != *.py ]]; then
            # Rename file to add .py extension
            mv -- "$file" "$file.py"
            echo "Renamed: $file -> $file.py"
            ((count++))
        else
            echo "Skipped: $file (already has .py extension)"
        fi
    fi
done

echo "========================================"
echo "Operation completed! Renamed $count files."

# Return to original directory
cd -

# Show summary
echo "Files in $TARGET_DIR/ after operation:"
find "$TARGET_DIR" -type f -name "*.py" | wc -l
