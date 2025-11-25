#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="/home/john/pyforce/malware_d1"
DST_DIR="/home/john/pyforce/malware_d1_extracted"
RESULTS_DIR="/home/john/pyforce/results"

mkdir -p "$DST_DIR"
mkdir -p "$RESULTS_DIR"

# Helper function: create unique destination if exists
# Args: target_path
unique_dest() {
    local dest="$1"
    if [ ! -e "$dest" ]; then
        printf '%s' "$dest"
        return
    fi
    local dir name ext base newdest i=1
    dir=$(dirname "$dest")
    name=$(basename "$dest")
    ext="${name##*.}"
    base="${name%.*}"
    while :; do
        newdest="$dir/${base}_$i.$ext"
        if [ ! -e "$newdest" ]; then
            printf '%s' "$newdest"
            return
        fi
        i=$((i+1))
    done
}

echo "Source directory: $SRC_DIR"
echo "Extraction directory: $DST_DIR"
echo "Results directory: $RESULTS_DIR"

shopt -s nullglob
for f in "$SRC_DIR"/*; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")

    # Skip .txt files
    case "$fname" in
        *.txt) 
            echo "Skipping txt file: $fname"
            continue
            ;;
    esac

    tempd=$(mktemp -d)
    echo "Processing: $fname -> temp dir $tempd"

    # Choose extraction method by file extension
    if [[ "$fname" =~ \.tar\.gz$ ]] || [[ "$fname" =~ \.tgz$ ]]; then
        tar -xzf "$f" -C "$tempd" || { echo "Failed to extract tar.gz: $fname"; rm -rf "$tempd"; continue; }
    elif [[ "$fname" =~ \.tar$ ]]; then
        tar -xf "$f" -C "$tempd" || { echo "Failed to extract tar: $fname"; rm -rf "$tempd"; continue; }
    elif [[ "$fname" =~ \.zip$ ]] || [[ "$fname" =~ \.tar\.zip$ ]] || [[ "$fname" =~ \.whl$ ]]; then
        unzip -q "$f" -d "$tempd" || { echo "Failed to unzip: $fname"; rm -rf "$tempd"; continue; }
    else
        echo "Unknown format, skipping: $fname"
        rm -rf "$tempd"
        continue
    fi

    # Move only .py files to DST_DIR with unique naming
    cd "$tempd"
    find . -type f -name "*.py" -print0 | while IFS= read -r -d '' srcfile; do
        relpath="${srcfile#./}"
        destpath="$DST_DIR/$relpath"
        destdir=$(dirname "$destpath")
        mkdir -p "$destdir"

        if [ -e "$destpath" ]; then
            newdest=$(unique_dest "$destpath")
            mv -n "$srcfile" "$newdest"
            echo "Renamed and moved: $relpath -> ${newdest#$DST_DIR/}"
        else
            mv -n "$srcfile" "$destpath"
            echo "Moved: $relpath"
        fi
    done
    cd /

    # Clean temporary extraction directory
    rm -rf "$tempd"

    # Scan the extracted package and generate JSON per package
    pkg_name="${fname%.*}"
    output_json="$RESULTS_DIR/${pkg_name}_bandit.json"
    echo "Scanning package $pkg_name..."
    bandit -r "$DST_DIR" -f json -o "$output_json"
done

echo "All packages processed and scanned. Results are in $RESULTS_DIR"

