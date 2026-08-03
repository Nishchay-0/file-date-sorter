import argparse
import sys
import os
try:
    from version import APP_NAME, VERSION
except ImportError:
    APP_NAME = "Smart File Organizer Suite"
    VERSION = "1.0.0"

from sorter_core import (
    organize_directory,
    list_manifest_files,
    undo_manifest,
    clean_empty_dirs
)

def print_progress(current, total, file_path, status_msg, status_tag):
    print(f"[{current}/{total}] {os.path.basename(file_path)}: {status_msg}")

def main():
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} - Automatically organize files by Date, Extension, File Type, Alphabetical Name, or Size."
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"{APP_NAME} v{VERSION}",
        help="Show program version and exit."
    )

    parser.add_argument(
        "-p", "--path",
        type=str,
        help="Target folder directory path to organize."
    )
    parser.add_argument(
        "-c", "--sort-category",
        choices=["date", "category", "extension", "name", "size"],
        default="date",
        help="Sorting criteria: 'date' (Year/Month), 'category' (Images/Docs/Videos), 'extension' (PDF/PNG), 'name' (Alphabetical A-Z), 'size' (File Size)."
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        default=True,
        help="Include subfolders recursively (default: True)."
    )
    parser.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        help="Do not scan subfolders."
    )
    parser.add_argument(
        "-d", "--date-source",
        choices=["ctime", "mtime", "exif"],
        default="ctime",
        help="Date source for date sorting: 'ctime' (Creation date), 'mtime' (Modification date), 'exif' (Photo EXIF with fallback)."
    )
    parser.add_argument(
        "-f", "--format",
        choices=["YYYY/MM", "YYYY/MM - Month", "YYYY-MM", "YYYY/MM/DD"],
        default="YYYY/MM",
        help="Folder structure format for date sorting (default: YYYY/MM)."
    )
    parser.add_argument(
        "--include-exts",
        type=str,
        help="Comma-separated list of file extensions to include (e.g. '.jpg,.png,.pdf')."
    )
    parser.add_argument(
        "--exclude-exts",
        type=str,
        help="Comma-separated list of file extensions to exclude (e.g. '.tmp,.log,.ini')."
    )
    parser.add_argument(
        "--exclude-folders",
        type=str,
        help="Comma-separated list of subfolder names or paths to exclude (e.g. '.git,node_modules,temp')."
    )
    parser.add_argument(
        "--exclude-files",
        type=str,
        help="Comma-separated list of file names to exclude (e.g. 'desktop.ini,.DS_Store')."
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["move", "copy"],
        default="move",
        help="Action mode: 'move' or 'copy' (default: move)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode: preview files to move without changing disk files."
    )
    parser.add_argument(
        "--clean-empty",
        action="store_true",
        help="Remove empty subfolders after moving files."
    )
    parser.add_argument(
        "--clean-empty-only",
        action="store_true",
        help="Clean all empty subfolders (including OS junk files like desktop.ini) in the target directory without sorting files."
    )
    parser.add_argument(
        "--undo",
        type=str,
        nargs="?",
        const="LATEST",
        help="Undo a previous sort operation using manifest file path or 'LATEST'."
    )

    args = parser.parse_args()

    # Handle Clean Empty Only Mode
    if args.clean_empty_only:
        if not args.path:
            print("Error: Please provide --path <folder_path> to clean empty folders.")
            sys.exit(1)
        target_dir = os.path.abspath(args.path)
        exc_folds = [f.strip() for f in args.exclude_folders.split(',')] if args.exclude_folders else None
        print(f"=== CLEANING EMPTY SUBFOLDERS IN: {target_dir} ===")
        cleaned = clean_empty_dirs(target_dir, remove_os_junk=True, exclude_folders=exc_folds)
        print(f"[OK] Cleaned {cleaned} empty folder(s)!")
        sys.exit(0)

    # Handle Undo Mode
    if args.undo:
        target_dir = args.path if args.path else os.getcwd()
        manifest_path = args.undo

        if manifest_path == "LATEST":
            manifests = list_manifest_files(target_dir)
            if not manifests:
                print(f"Error: No manifest files found in {target_dir}")
                sys.exit(1)
            manifest_path = manifests[0]["path"]

        print(f"=== UNDOING SORTING FROM MANIFEST: {manifest_path} ===")
        try:
            stats = undo_manifest(manifest_path, progress_callback=print_progress)
            print("\n=== UNDO SUMMARY ===")
            print(f"Restored: {stats['undone']}")
            print(f"Errors:   {stats['errors']}")
            sys.exit(0)
        except Exception as e:
            print(f"Undo error: {e}")
            sys.exit(1)

    # Require path for sorting if not undoing
    if not args.path:
        parser.print_help()
        print("\nError: Please provide --path <folder_path> or --undo")
        sys.exit(1)

    target_dir = os.path.abspath(args.path)

    inc_exts = [e.strip() for e in args.include_exts.split(',')] if args.include_exts else None
    exc_exts = [e.strip() for e in args.exclude_exts.split(',')] if args.exclude_exts else None
    exc_folds = [f.strip() for f in args.exclude_folders.split(',')] if args.exclude_folders else None
    exc_files = [f.strip() for f in args.exclude_files.split(',')] if args.exclude_files else None

    print("=== STARTING SMART FILE ORGANIZER ===")
    print(f"Path:            {target_dir}")
    print(f"Sort Category:   {args.sort_category.upper()}")
    if args.sort_category == "date":
        print(f"Date Source:     {args.date_source}")
        print(f"Format:          {args.format}")
    print(f"Mode:            {args.mode}")
    print(f"Recursive:       {args.recursive}")
    print(f"Dry Run:         {args.dry_run}")
    print(f"Clean Empty:     {args.clean_empty}\n")

    try:
        stats, manifest = organize_directory(
            main_folder=target_dir,
            sort_category=args.sort_category,
            recursive=args.recursive,
            date_source=args.date_source,
            structure_format=args.format,
            include_exts=inc_exts,
            exclude_exts=exc_exts,
            exclude_folders=exc_folds,
            exclude_files=exc_files,
            mode=args.mode,
            dry_run=args.dry_run,
            clean_empty=args.clean_empty,
            progress_callback=print_progress
        )

        print("\n=== SORTING COMPLETE ===")
        print(f"Total Analyzed: {stats['total']}")
        print(f"Processed:      {stats['processed']}")
        print(f"Skipped:        {stats['skipped']}")
        print(f"Errors:         {stats['errors']}")

        if args.dry_run:
            print("\n[DRY RUN] No files were moved or changed.")
        elif 'manifest' in stats:
            print(f"Undo manifest created: {stats['manifest']}")

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
