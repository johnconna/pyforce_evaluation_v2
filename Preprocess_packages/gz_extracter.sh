#!/bin/bash

# Script: extract_tar_gz.sh
# Description: Batch extract .tar.gz files and place contents in directories named after the archive files

echo "Starting TAR.GZ file extraction..."

# Counter for processed files
count=0

# Find all .tar.gz files in current directory
for archive in *.tar.gz; do
    if [[ -f "$archive" ]]; then
        # Get filename without .tar.gz extension
        dir_name="${archive%.tar.gz}"
        
        # Create directory if it doesn't exist
        if [[ ! -d "$dir_name" ]]; then
            mkdir -p "$dir_name"
        fi
        
        # Extract .tar.gz file to the directory
        echo "Extracting: $archive -> $dir_name/"
        tar -xzf "$archive" -C "$dir_name"
        
        # Check if extraction was successful
        if [[ $? -eq 0 ]]; then
            echo "✓ Successfully extracted: $archive"
            ((count++))
        else
            echo "✗ Failed to extract: $archive"
        fi
    fi
done

echo "========================================"
echo "Extraction completed! Processed $count TAR.GZ files."

# If no TAR.GZ files were found
if [[ $count -eq 0 ]]; then
    echo "No TAR.GZ files found in current directory."
    echo "Current directory contents:"
    ls -la
fi
