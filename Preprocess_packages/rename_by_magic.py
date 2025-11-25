#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rename_by_magic.py (multi-process + simplified MAGIC, remove multi-level suffix)

- Python files: version MAGIC -> .py
- Gzip files: 1F 8B 08 -> .gz
- Zip files: 50 4B 03 04 -> .zip
- Original multi-level suffix removed, only main filename kept
"""

import argparse, pathlib, sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
from tqdm import tqdm

# Simplified MAGIC -> suffix mapping
MAGIC_SUFFIX_MAP = {
    "76 65 72 73 69 6F 6E 20": ".py",  # Python version
    "1F 8B 08": ".gz",                  # gzip
    "50 4B 03 04": ".zip",              # zip
}

def hex_to_bytes(s):
    """Convert hex string like '1F 8B 08' to bytes"""
    return bytes(int(x, 16) for x in s.split())

# Precompute bytes mapping
MAGIC_BYTES_MAP = {hex_to_bytes(k): v for k, v in MAGIC_SUFFIX_MAP.items()}

def determine_new_name(fpath, suffix):
    """Return unique path with desired suffix, remove original multi-level suffix"""
    stem = fpath.name.split('.')[0]  # 主文件名，不保留原多级后缀
    new_name = fpath.parent / f"{stem}{suffix}"
    i = 1
    while new_name.exists():
        new_name = fpath.parent / f"{stem}.{i}{suffix}"
        i += 1
    return new_name

def process_file(fpath, min_bytes=4096):
    """Check MAGIC for a single file and determine new name if needed"""
    f = pathlib.Path(fpath)
    try:
        with open(f, 'rb') as fh:
            data = fh.read(min_bytes)
    except Exception:
        return None

    for magic_bytes, suffix in MAGIC_BYTES_MAP.items():
        if data.startswith(magic_bytes):
            return (f, determine_new_name(f, suffix))
    return None

def collect_files(base_dir, pattern="*"):
    base = pathlib.Path(base_dir)
    if not base.exists():
        print('Directory not found:', base, file=sys.stderr)
        sys.exit(2)
    return [f for f in base.rglob(pattern) if f.is_file()]

def process_files(file_list, dry_run=True, workers=4, min_bytes=4096):
    results = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        func = partial(process_file, min_bytes=min_bytes)
        futures = {executor.submit(func, f): f for f in file_list}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing"):
            res = future.result()
            if res:
                results.append(res)

    if not dry_run:
        for src, dst in results:
            try:
                src.rename(dst)
                print('Renamed:', src, '->', dst)
            except Exception as e:
                print('Failed to rename:', src, '->', dst, 'Reason:', e)
    return results

def main():
    parser = argparse.ArgumentParser(description='Rename files based on simplified MAGIC bytes')
    parser.add_argument('--dir', '-d', required=True, help='Directory to scan')
    parser.add_argument('--pattern', '-p', default='*', help='Glob pattern (default *)')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Only show actions (default)')
    parser.add_argument('--apply', action='store_true', help='Apply changes (turns off dry-run)')
    parser.add_argument('--workers', type=int, default=4, help='Parallel worker processes')
    parser.add_argument('--min-bytes', type=int, default=4096, help='Bytes to read from each file')
    args = parser.parse_args()

    dry_run = not args.apply
    files = collect_files(args.dir, args.pattern)
    print(f"Found {len(files)} files to process...")

    results = process_files(files, dry_run=dry_run, workers=args.workers, min_bytes=args.min_bytes)

    if results:
        print(f"\nPlanned renames (total {len(results)}):")
        for src, dst in results:
            print(f"  {src} -> {dst}")
    else:
        print("No files matched any MAGIC criteria.")

    if dry_run:
        print("\nDry-run mode: use --apply to actually rename files.")

if __name__ == '__main__':
    main()
