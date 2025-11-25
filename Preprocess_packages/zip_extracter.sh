#!/bin/bash

# Script: extract_zips.sh
# Description: Batch extract ZIP files and place contents in directories named after the ZIP files

echo "Starting ZIP file extraction..."

# Counter for processed files
count=0

# Find all ZIP files in current directory
for zipfile in *.zip; do
    if [[ -f "$zipfile" ]]; then
        # Get filename without extension
        dir_name="${zipfile%.zip}"
        
        # Create directory if it doesn't exist
        if [[ ! -d "$dir_name" ]]; then
            mkdir -p "$dir_name"
        fi
        
        # Extract ZIP file to the directory
        echo "Extracting: $zipfile -> $dir_name/"
        unzip -q "$zipfile" -d "$dir_name"
        
        # Check if extraction was successful
        if [[ $? -eq 0 ]]; then
            echo "✓ Successfully extracted: $zipfile"
            ((count++))
        else
            echo "✗ Failed to extract: $zipfile"
        fi
    fi
done

echo "========================================"
echo "Extraction completed! Processed $count ZIP files."

# If no ZIP files were found
if [[ $count -eq 0 ]]; then
    echo "No ZIP files found in current directory."
    echo "Current directory contents:"
    ls -la
fi
