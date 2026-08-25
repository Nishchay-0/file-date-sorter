#!/usr/bin/env python3
r"""
File Categorization and Natural Sorting Script

Organizes and sorts files and folders into three distinct categories:
  1. Pure Numeric Names (e.g., '0', '1', '05', '10') -> Zero-padded to 2 digits ('01') and sorted numerically.
  2. Standard Text Names -> Sorted using natural sorting key (file2 before file10).
  3. Hexadecimal / Hash Strings -> Detected via regex, normalized to lowercase, and grouped together.

Features:
  - Natural sorting implementation using re.split(r'(\d+)', filename)
  - In-place renaming mode or move into categorized subdirectories (01_Numeric/, 02_Standard/, 03_Hashes/)
  - Safe dry-run mode by default, undo manifest generation, and collision protection.
"""

import os
import re
import shutil
import argparse
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any

# --------------------------------------------------------------------------- #
# Categorization & Regex Rules
# --------------------------------------------------------------------------- #

HEX_REGEX = re.compile(r'^[0-9a-fA-F]+$')
HEX_HASH_REGEX = re.compile(r'^[0-9a-fA-F]{12,}$')
UUID_REGEX = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
CDN_MEDIA_SUFFIX_REGEX = re.compile(r'[_-](video_dashinit|transcode_output_dashinit|video_init|audio_dashinit|media_dashinit|dash_init)$', re.IGNORECASE)
META_CDN_REGEX = re.compile(r'^\d+_\d{10,}_\d{10,}_[a-zA-Z0-9]+$', re.IGNORECASE)

PROTECTED_DIRS = {
    '01_Numeric', '02_Standard', '03_Hashes',
    'indexed_folders', 'hash_folders', 'Unsorted',
    '.git', '.svn', '.hg', '__pycache__', '.pytest_cache'
}


def natural_sort_key(text: str) -> List[Tuple[int, Any]]:
    r"""
    Natural sorting key function using re.split(r'(\d+)', text).
    Splits text into chunks where numbers are compared numerically (type tag 0)
    and text strings are compared lexicographically (type tag 1).
    """
    chunks = [c for c in re.split(r'(\d+)', text) if c]
    return [(0, int(c)) if c.isdigit() else (1, c.lower()) for c in chunks]


def split_stem_and_ext(name: str, is_directory: bool = False) -> Tuple[str, str]:
    """
    Splits a filename into its stem and extension.
    For directories, the entire name is considered the stem with no extension.
    """
    if is_directory:
        return name, ""
    stem, ext = os.path.splitext(name)
    return stem, ext


def categorize_item(name: str, is_directory: bool = False) -> Tuple[str, str, str]:
    """
    Categorize an item into one of three categories:
      - 'numeric': Pure numbers (e.g., '0', '1', '05', '10')
      - 'hash': Hexadecimal strings, UUIDs, or CDN machine hashes
      - 'standard': Standard text/human names

    Returns:
      (category, normalized_name, reason)
    """
    stem, ext = split_stem_and_ext(name, is_directory)

    if not stem:
        return 'standard', name, "Empty stem name"

    # Category 1: Pure Numeric Names
    if stem.isdigit():
        padded_stem = str(int(stem)).zfill(2) if len(stem) < 2 else stem
        normalized = padded_stem + ext
        return 'numeric', normalized, f"Pure numeric '{stem}' -> zero-padded '{padded_stem}'"

    # Category 3: Hexadecimal / Hash Strings
    # 3a. UUID
    if UUID_REGEX.match(stem):
        normalized = stem.lower() + ext
        return 'hash', normalized, f"UUID string -> normalized lowercase"

    # 3b. Meta/FB/IG CDN numeric machine ID
    if META_CDN_REGEX.match(stem):
        normalized = stem.lower() + ext
        return 'hash', normalized, f"Meta CDN hash ID -> normalized lowercase"

    # 3c. Hex with CDN suffix (e.g. 3E4396DAE40C47DA_video_dashinit)
    cdn_stripped = CDN_MEDIA_SUFFIX_REGEX.sub('', stem)
    if cdn_stripped != stem and HEX_HASH_REGEX.match(cdn_stripped):
        normalized = stem.lower() + ext
        return 'hash', normalized, f"Hex stream ID with CDN suffix -> normalized lowercase"

    # 3d. Pure Hex strings (minimum 12 characters to avoid classifying words like 'cafe', 'deadbeef')
    # or general hex string >= 12 chars
    if len(stem) >= 12 and HEX_REGEX.match(stem):
        normalized = stem.lower() + ext
        return 'hash', normalized, f"Hexadecimal hash ({len(stem)} chars) -> normalized lowercase"

    # 3e. Multi-digit machine ID sequences with separators
    clean_no_sep = re.sub(r'[_\-\.\s]', '', stem)
    if clean_no_sep.isdigit() and len(clean_no_sep) >= 12:
        normalized = stem.lower() + ext
        return 'hash', normalized, f"Long numeric machine ID sequence ({len(clean_no_sep)} digits)"

    # Category 2: Standard Text Names
    return 'standard', name, "Standard text name"


# --------------------------------------------------------------------------- #
# Directory Scanner & Sorter
# --------------------------------------------------------------------------- #

def scan_and_categorize(
    directory_path: str,
    target_type: str = 'all'
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Scans the specified directory, categorizes each item, and sorts each category
    using the natural sorting key.

    target_type can be 'all', 'files', or 'folders'.
    """
    directory_path = os.path.abspath(directory_path)
    categories: Dict[str, List[Dict[str, Any]]] = {
        'numeric': [],
        'standard': [],
        'hash': []
    }

    try:
        entries = list(os.scandir(directory_path))
    except Exception as e:
        print(f"[ERROR] Unable to scan directory '{directory_path}': {e}")
        return categories

    for entry in entries:
        name = entry.name
        if name in PROTECTED_DIRS or name.startswith('.fix_hash') or name.startswith('.undo'):
            continue

        is_dir = entry.is_dir(follow_symlinks=False)
        if target_type == 'files' and is_dir:
            continue
        if target_type == 'folders' and not is_dir:
            continue

        cat, norm_name, reason = categorize_item(name, is_directory=is_dir)
        categories[cat].append({
            'original_name': name,
            'normalized_name': norm_name,
            'category': cat,
            'reason': reason,
            'is_directory': is_dir,
            'original_path': entry.path,
        })

    # Sort each category using natural sort key
    for cat in categories:
        categories[cat].sort(key=lambda x: natural_sort_key(x['normalized_name']))

    return categories


# --------------------------------------------------------------------------- #
# Plan Display & Execution
# --------------------------------------------------------------------------- #

def display_plan(
    categories: Dict[str, List[Dict[str, Any]]],
    mode: str = 'move',
    dest_folders: Dict[str, str] = None
) -> None:
    """
    Displays the categorized and sorted plan in the terminal.
    """
    if dest_folders is None:
        dest_folders = {
            'numeric': '01_Numeric',
            'standard': '02_Standard',
            'hash': '03_Hashes'
        }

    total_count = sum(len(items) for items in categories.values())
    print("\n" + "=" * 76)
    print("                    CATEGORIZATION & SORTING PLAN")
    print("=" * 76)
    print(f"Total Items Found: {total_count} | Mode: {mode.upper()}")
    print("-" * 76)

    category_titles = [
        ('numeric', "1. PURE NUMERIC (Sorted Numerically, Zero-Padded)"),
        ('standard', "2. STANDARD TEXT (Sorted Naturally)"),
        ('hash', "3. HEXADECIMAL / HASH STRINGS (Normalized Lowercase)")
    ]

    for cat_key, title in category_titles:
        items = categories[cat_key]
        dest_folder = dest_folders.get(cat_key, cat_key)
        print(f"\n[+] {title} - [{len(items)} items]")
        if mode == 'move':
            print(f"    Target Subdirectory: {dest_folder}/")
        print(f"    {'Original Name':<42} -> {'Action / New Target'}")
        print("    " + "-" * 70)

        if not items:
            print("    (No items in this category)")
            continue

        for item in items:
            orig = item['original_name']
            norm = item['normalized_name']
            itype = "[DIR]" if item['is_directory'] else "[FILE]"

            if mode == 'move':
                action = f"move to {dest_folder}/{norm}"
            elif mode == 'rename':
                action = f"rename to '{norm}'" if norm != orig else "no rename needed (already normalized)"
            else:
                action = f"normalize to '{norm}'"

            print(f"    {itype} {orig:<36} -> {action}")

    print("\n" + "=" * 76)


def execute_plan(
    directory_path: str,
    categories: Dict[str, List[Dict[str, Any]]],
    mode: str = 'move',
    dest_folders: Dict[str, str] = None,
    dry_run: bool = True
) -> List[Dict[str, Any]]:
    """
    Executes the organization plan (rename or move) with rollback manifest recording.
    """
    if dest_folders is None:
        dest_folders = {
            'numeric': '01_Numeric',
            'standard': '02_Standard',
            'hash': '03_Hashes'
        }

    undo_operations: List[Dict[str, Any]] = []
    base_dir = os.path.abspath(directory_path)

    for cat_key, items in categories.items():
        dest_subfolder = dest_folders.get(cat_key, cat_key)
        target_dir = os.path.join(base_dir, dest_subfolder) if mode == 'move' else base_dir

        if mode == 'move' and not dry_run and items:
            os.makedirs(target_dir, exist_ok=True)

        for item in items:
            orig_name = item['original_name']
            norm_name = item['normalized_name']
            orig_path = item['original_path']

            if mode == 'move':
                final_dest = os.path.join(target_dir, norm_name)
                if os.path.exists(final_dest) and os.path.abspath(final_dest) != os.path.abspath(orig_path):
                    # Handle name collision by appending timestamp counter
                    base_n, ext_n = os.path.splitext(norm_name)
                    final_dest = os.path.join(target_dir, f"{base_n}_collision_{int(datetime.now().timestamp())}{ext_n}")

                if dry_run:
                    continue

                shutil.move(orig_path, final_dest)
                undo_operations.append({
                    'type': 'move',
                    'source': final_dest,
                    'original': orig_path
                })

            elif mode == 'rename':
                if orig_name == norm_name:
                    continue
                final_dest = os.path.join(base_dir, norm_name)
                if os.path.exists(final_dest) and os.path.abspath(final_dest) != os.path.abspath(orig_path):
                    print(f"  [SKIP] Destination '{norm_name}' already exists.")
                    continue

                if dry_run:
                    continue

                os.rename(orig_path, final_dest)
                undo_operations.append({
                    'type': 'rename',
                    'source': final_dest,
                    'original': orig_path
                })

    if not dry_run and undo_operations:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        manifest_path = os.path.join(base_dir, f".undo_categorize_manifest_{timestamp}.json")
        try:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': timestamp,
                    'base_dir': base_dir,
                    'mode': mode,
                    'operations': undo_operations
                }, f, indent=2)
            print(f"\n[INFO] Undo manifest saved to: {manifest_path}")
            print(f"[INFO] To undo this operation, run: python file_categorize_sorter.py --undo \"{manifest_path}\"")
        except Exception as e:
            print(f"[WARNING] Could not save undo manifest: {e}")

    return undo_operations


def rollback_manifest(manifest_path: str) -> bool:
    """
    Rolls back operations recorded in an undo manifest.
    """
    manifest_path = os.path.abspath(manifest_path)
    if not os.path.isfile(manifest_path):
        print(f"[ERROR] Manifest file not found: {manifest_path}")
        return False

    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    operations = list(reversed(data.get('operations', [])))
    print(f"\n[UNDO] Rolling back {len(operations)} operations from {data.get('timestamp')}...")

    success_count = 0
    for op in operations:
        src = op['source']
        orig = op['original']
        if not os.path.exists(src):
            print(f"  [WARN] Source file missing: {src}")
            continue

        os.makedirs(os.path.dirname(orig), exist_ok=True)
        if op['type'] in ('move', 'rename'):
            shutil.move(src, orig)
            success_count += 1
            print(f"  Restored: {os.path.basename(src)} -> {orig}")

    print(f"\n[UNDO] Successfully restored {success_count}/{len(operations)} items.")
    return True


# --------------------------------------------------------------------------- #
# Command-Line Interface
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Categorize, normalize, and sort files and folders with natural sorting."
    )
    parser.add_argument(
        '--path', '-p',
        type=str,
        help="Target directory path to sort and organize."
    )
    parser.add_argument(
        '--mode', '-m',
        choices=['move', 'rename'],
        default='move',
        help="Execution mode: 'move' into categorized subdirectories (default), or 'rename' in-place."
    )
    parser.add_argument(
        '--target', '-t',
        choices=['all', 'files', 'folders'],
        default='all',
        help="Target items to process: 'all' (default), 'files' only, or 'folders' only."
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=False,
        help="Perform a dry-run preview without making filesystem modifications."
    )
    parser.add_argument(
        '--execute', '-e',
        action='store_true',
        help="Execute the changes (if omitted and --dry-run is not set, dry-run preview is shown)."
    )
    parser.add_argument(
        '--undo',
        type=str,
        metavar='MANIFEST_JSON',
        help="Path to an undo manifest JSON file to revert a previous organization run."
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.undo:
        rollback_manifest(args.undo)
        return

    if not args.path:
        parser.print_help()
        print("\n[ERROR] Please provide a target directory via --path.")
        return

    target_dir = os.path.abspath(args.path.strip('"').strip("'"))
    if not os.path.isdir(target_dir):
        print(f"[ERROR] Specified path is not a valid directory: {target_dir}")
        return

    # Determine if dry run
    is_dry_run = args.dry_run or (not args.execute)

    categories = scan_and_categorize(target_dir, target_type=args.target)
    display_plan(categories, mode=args.mode)

    if is_dry_run:
        print("[NOTICE] Running in DRY-RUN mode. No changes were made to disk.")
        print("[NOTICE] To apply these changes, rerun with --execute (e.g. python file_categorize_sorter.py --path ... --execute)")
    else:
        print("\nExecuting organization plan...")
        undo_ops = execute_plan(target_dir, categories, mode=args.mode, dry_run=False)
        print(f"\n[SUCCESS] Completed {len(undo_ops)} operations.")


if __name__ == '__main__':
    main()
