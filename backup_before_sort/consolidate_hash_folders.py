"""
consolidate_hash_folders.py

One-time cleanup: scan a directory for hash-named subfolders created by the
old (buggy) Smart Name Sorter, move their contents into a single Unsorted/
folder, and delete the now-empty hash folders.

Usage:
    python consolidate_hash_folders.py "C:\\Path\\To\\SortedDir" [--dry-run]
    python consolidate_hash_folders.py "C:\\Path\\To\\SortedDir" --execute
"""

import os
import re
import sys
import shutil
import argparse

# -- Same detection regexes as sorter_core.py --
UUID_REGEX       = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
HEX_HASH_REGEX   = re.compile(r'^[0-9a-fA-F]{12,}$')
CDN_SUFFIX_REGEX = re.compile(
    r'[_-](video_dashinit|transcode_output_dashinit|transcode_oil_output_dashinit'
    r'|video_init|audio_dashinit|media_dashinit|dash_init)(?:[_-]\d+)?$',
    re.IGNORECASE
)
META_CDN_REGEX   = re.compile(r'^\d+_\d{10,}_\d{10,}_[a-zA-Z0-9]+$', re.IGNORECASE)


def is_hash_folder(name: str) -> bool:
    if UUID_REGEX.match(name):
        return True
    if HEX_HASH_REGEX.match(name) and any(c.lower() in 'abcdef' for c in name):
        return True
    stripped = CDN_SUFFIX_REGEX.sub('', name)
    if stripped != name and HEX_HASH_REGEX.match(stripped) and any(c.lower() in 'abcdef' for c in stripped):
        return True
    if META_CDN_REGEX.match(name):
        return True
    return False


def consolidate(target_dir: str, unsorted_name: str = "Unsorted", dry_run: bool = True):
    target_dir = os.path.abspath(target_dir)
    if not os.path.isdir(target_dir):
        print(f"[ERROR] Not a directory: {target_dir}")
        sys.exit(1)

    unsorted_dir = os.path.join(target_dir, unsorted_name)
    mode = "[DRY-RUN]" if dry_run else "[MOVE]"

    hash_folders = []
    for entry in os.scandir(target_dir):
        if not entry.is_dir():
            continue
        if entry.name == unsorted_name:
            continue
        if is_hash_folder(entry.name):
            hash_folders.append(entry.path)

    if not hash_folders:
        print("No hash-named folders found. Nothing to do.")
        return

    print(f"Found {len(hash_folders)} hash folders to consolidate into '{unsorted_name}/'")
    print(f"Mode: {'DRY-RUN (no changes made)' if dry_run else 'LIVE MOVE'}\n")

    if not dry_run:
        os.makedirs(unsorted_dir, exist_ok=True)

    moved_total = 0
    removed_dirs = 0

    for folder_path in sorted(hash_folders):
        folder_name = os.path.basename(folder_path)
        contents = list(os.scandir(folder_path))

        if not contents:
            print(f"  {mode} REMOVE empty folder: {folder_name}/")
            if not dry_run:
                os.rmdir(folder_path)
            removed_dirs += 1
            continue

        print(f"  {mode} {folder_name}/ ({len(contents)} item(s))")
        for item in contents:
            dest = os.path.join(unsorted_dir, item.name)
            if os.path.exists(dest) and not dry_run:
                stem, ext = os.path.splitext(item.name)
                counter = 1
                while os.path.exists(dest):
                    dest = os.path.join(unsorted_dir, f"{stem}_{counter}{ext}")
                    counter += 1
            print(f"    -> {unsorted_name}/{os.path.basename(dest)}")
            if not dry_run:
                shutil.move(item.path, dest)
            moved_total += 1

        if not dry_run:
            try:
                os.rmdir(folder_path)
                removed_dirs += 1
            except OSError:
                print(f"    [WARN] Could not remove {folder_name}/ (not empty?)")

    print(f"\n{'DRY-RUN SUMMARY' if dry_run else 'DONE'}:")
    print(f"  Hash folders found : {len(hash_folders)}")
    print(f"  Files to move      : {moved_total}")
    if not dry_run:
        print(f"  Folders removed    : {removed_dirs}")
        print(f"  All moved to       : {unsorted_dir}")
    else:
        print("\n  Run with --execute to apply changes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Consolidate hash-named folders into Unsorted/")
    parser.add_argument("target_dir", help="Directory containing the hash-named subfolders")
    parser.add_argument("--execute", action="store_true",
                        help="Actually move the files (default is dry-run)")
    parser.add_argument("--unsorted-name", default="Unsorted",
                        help="Name of the destination folder (default: Unsorted)")
    args = parser.parse_args()

    consolidate(args.target_dir, unsorted_name=args.unsorted_name, dry_run=not args.execute)
