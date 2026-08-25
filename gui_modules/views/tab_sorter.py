import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from gui_modules.components import CTkToolTip, create_info_icon, get_user_folder

try:
    import customtkinter as ctk
    HAS_CUSTOMTKINTER = True
except ImportError:
    HAS_CUSTOMTKINTER = False

try:
    from gui_modules.theme_manager import (
        GLASS, FONTS, glass_frame, glass_frame_alt, accent_button,
        secondary_button, section_label, status_badge,
        styled_entry, styled_progress, resolve_accent, animate_hover
    )
    HAS_THEME = True
except ImportError:
    HAS_THEME = False


def setup_organizer_tab(gui_instance):
    scroll = ctk.CTkScrollableFrame(gui_instance.tab_organizer, fg_color="transparent")
    scroll.pack(fill="both", expand=True)
    scroll.grid_columnconfigure(0, weight=1)
    gui_instance.organizer_scroll = scroll

    if hasattr(gui_instance, 'StorageChartCanvas'):
        gui_instance.chart_canvas = gui_instance.StorageChartCanvas(scroll, height=110, corner_radius=10, fg_color=GLASS["bg_card_alt"] if HAS_THEME else ("gray90", "gray16"))
        gui_instance.chart_canvas.grid(row=0, column=0, sticky="ew", pady=(0, 6))

    # Presets Bar
    preset_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color=GLASS["bg_card_alt"] if HAS_THEME else ("gray90", "gray17"))
    preset_card.grid(row=1, column=0, sticky="ew", pady=(0, 6), ipadx=8, ipady=4)
    ctk.CTkLabel(preset_card, text="⚡ Quick Presets:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(12, 4))
    create_info_icon(preset_card, "1-Click Presets instantly configure sorting strategy, filters & date formats!").pack(side="left", padx=(0, 8))

    btn1 = ctk.CTkButton(preset_card, text="📸 Photos & EXIF", command=gui_instance.apply_preset_photos, font=ctk.CTkFont(size=11), height=26, width=125, fg_color=("#007AFF", "#0A84FF") if HAS_THEME else "#0288d1")
    btn1.pack(side="left", padx=3)

    btn2 = ctk.CTkButton(preset_card, text="📥 Downloads Clean", command=gui_instance.apply_preset_downloads, font=ctk.CTkFont(size=11), height=26, width=135, fg_color=("#AF52DE", "#BF5AF2") if HAS_THEME else "#7b1fa2")
    btn2.pack(side="left", padx=3)

    btn3 = ctk.CTkButton(preset_card, text="💼 Work Documents", command=gui_instance.apply_preset_documents, font=ctk.CTkFont(size=11), height=26, width=130, fg_color=("#34C759", "#30D158") if HAS_THEME else "#388e3c")
    btn3.pack(side="left", padx=3)

    btn4 = ctk.CTkButton(preset_card, text="🧹 Big File Finder", command=gui_instance.apply_preset_size, font=ctk.CTkFont(size=11), height=26, width=120, fg_color=("#FF9500", "#FF9F0A") if HAS_THEME else "#f57c00")
    btn4.pack(side="left", padx=3)

    # 2-Column Grid Container
    grid_cols = ctk.CTkFrame(scroll, fg_color="transparent")
    grid_cols.grid(row=2, column=0, sticky="ew", pady=(0, 6))
    grid_cols.grid_columnconfigure(0, weight=1)
    grid_cols.grid_columnconfigure(1, weight=1)

    # Col 0: Directories & Shortcuts Card
    dir_card = ctk.CTkFrame(grid_cols, corner_radius=16)
    dir_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5), ipadx=8, ipady=8)
    dir_card.grid_columnconfigure(1, weight=1)

    hdr_d = ctk.CTkFrame(dir_card, fg_color="transparent")
    hdr_d.grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(6, 4))
    ctk.CTkLabel(hdr_d, text="1. Select Target Folder OR Pick Files", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).pack(side="left")
    create_info_icon(hdr_d, "Pick an entire folder OR click '📄 Pick Files...' to pick individual specific files!").pack(side="left", padx=6)

    quick_frame = ctk.CTkFrame(dir_card, fg_color="transparent")
    quick_frame.grid(row=1, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 6))
    ctk.CTkLabel(quick_frame, text="Shortcuts:", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray60").pack(side="left", padx=(0, 6))

    for fname, icon in [("Downloads", "📥"), ("Pictures", "🖼️"), ("Documents", "📄"), ("Desktop", "🖥️")]:
        path = get_user_folder(fname)
        btn_sc = ctk.CTkButton(
            quick_frame,
            text=f"{icon} {fname}",
            command=lambda p=path: gui_instance.set_target_dir(p),
            font=ctk.CTkFont(size=10),
            height=22,
            width=85,
            fg_color=GLASS["bg_hover"] if HAS_THEME else ("gray80", "gray25"),
            text_color=("gray10", "gray90")
        )
        btn_sc.pack(side="left", padx=2)

    ctk.CTkLabel(dir_card, text="Target:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=0, sticky="w", padx=(12, 6), pady=(0, 4))

    gui_instance.dir_var = tk.StringVar()
    gui_instance.dir_entry = ctk.CTkEntry(dir_card, textvariable=gui_instance.dir_var, placeholder_text="Select folder or pick specific files...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.dir_entry.grid(row=2, column=1, sticky="ew", padx=(0, 6), pady=(0, 4))

    btn_box = ctk.CTkFrame(dir_card, fg_color="transparent")
    btn_box.grid(row=2, column=2, sticky="e", padx=(0, 10), pady=(0, 4))

    gui_instance.browse_folder_btn = ctk.CTkButton(btn_box, text="📁 Pick Folder...", command=gui_instance.browse_folder, font=ctk.CTkFont(size=10, weight="bold"), height=32, width=95)
    gui_instance.browse_folder_btn.pack(side="left", padx=(0, 3))
    CTkToolTip(gui_instance.browse_folder_btn, "Selects a single target directory to organize!")

    gui_instance.browse_multi_btn = ctk.CTkButton(btn_box, text="📁+ Multi Folders...", command=lambda: gui_instance.browse_multiple_folders(gui_instance.dir_var, gui_instance.refresh_preview), font=ctk.CTkFont(size=10, weight="bold"), fg_color="#1565c0", height=32, width=110)
    gui_instance.browse_multi_btn.pack(side="left", padx=(0, 3))
    CTkToolTip(gui_instance.browse_multi_btn, "Pick multiple target folders sequentially to organize altogether!")

    gui_instance.browse_files_btn = ctk.CTkButton(btn_box, text="📄 Pick Files...", command=gui_instance.browse_individual_files, font=ctk.CTkFont(size=10, weight="bold"), fg_color=("#32ADE6", "#64D2FF") if HAS_THEME else "#00838f", height=32, width=90)
    gui_instance.browse_files_btn.pack(side="left", padx=(0, 3))
    CTkToolTip(gui_instance.browse_files_btn, "Select specific individual files anywhere on your computer!")

    gui_instance.open_folder_btn = ctk.CTkButton(
        btn_box, text="Open ↗", command=gui_instance.open_target_folder,
        fg_color=("gray75", "gray30"), text_color=("gray10", "gray90"),
        font=ctk.CTkFont(size=10, weight="bold"), height=32, width=55
    )
    gui_instance.open_folder_btn.pack(side="left")

    ctk.CTkLabel(dir_card, text="Exclusions (Opt):", font=ctk.CTkFont(size=11, weight="bold"), text_color="#ef5350").grid(row=3, column=0, sticky="w", padx=(12, 6), pady=(4, 6))

    gui_instance.sorter_exc_entry = ctk.CTkEntry(dir_card, textvariable=gui_instance.exclude_folders_var, placeholder_text="Folders/Subfolders to SKIP...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.sorter_exc_entry.grid(row=3, column=1, sticky="ew", padx=(0, 6), pady=(4, 6))

    sorter_exc_btn_box = ctk.CTkFrame(dir_card, fg_color="transparent")
    sorter_exc_btn_box.grid(row=3, column=2, sticky="e", padx=(0, 10), pady=(4, 6))

    gui_instance.btn_exc_fld = ctk.CTkButton(sorter_exc_btn_box, text="🚫 Except Folder...", command=gui_instance.add_exclude_folder_picker, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#c62828", height=32, width=105)
    gui_instance.btn_exc_fld.pack(side="left", padx=(0, 3))
    CTkToolTip(gui_instance.btn_exc_fld, "Select a folder to EXCLUDE. That folder and all its subfolders deep down will be skipped while processing!")

    gui_instance.btn_exc_file = ctk.CTkButton(sorter_exc_btn_box, text="🚫 Except Files...", command=gui_instance.add_exclude_file_picker, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#ad1457", height=32, width=95)
    gui_instance.btn_exc_file.pack(side="left", padx=(0, 3))
    CTkToolTip(gui_instance.btn_exc_file, "Select specific file(s) to EXCLUDE from processing!")

    ctk.CTkButton(sorter_exc_btn_box, text="🧹 Clear", command=lambda: gui_instance.exclude_folders_var.set(""), font=ctk.CTkFont(size=10), height=32, width=55, fg_color=("gray75", "gray30"), text_color=("gray10", "gray90")).pack(side="left")

    ctk.CTkLabel(dir_card, text="Output:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=4, column=0, sticky="w", padx=(12, 6), pady=(0, 6))

    gui_instance.dest_dir_var = tk.StringVar()
    gui_instance.dest_entry = ctk.CTkEntry(dir_card, textvariable=gui_instance.dest_dir_var, placeholder_text="Optional custom output folder...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.dest_entry.grid(row=4, column=1, sticky="ew", padx=(0, 6), pady=(0, 6))

    dest_btn_box = ctk.CTkFrame(dir_card, fg_color="transparent")
    dest_btn_box.grid(row=4, column=2, sticky="e", padx=(0, 10), pady=(0, 6))

    ctk.CTkButton(dest_btn_box, text="Browse...", command=gui_instance.browse_dest_folder, font=ctk.CTkFont(size=11), fg_color=("gray70", "gray35"), height=32, width=95).pack(side="left", padx=(0, 4))
    ctk.CTkButton(dest_btn_box, text="Clear", command=lambda: gui_instance.dest_dir_var.set(""), font=ctk.CTkFont(size=10), fg_color=("gray75", "gray30"), text_color=("gray10", "gray90"), height=32, width=55).pack(side="left")

    # Col 1: Strategy & Rules Card
    strategy_card = ctk.CTkFrame(grid_cols, corner_radius=16)
    strategy_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0), ipadx=8, ipady=8)
    strategy_card.grid_columnconfigure(1, weight=1)
    strategy_card.grid_columnconfigure(3, weight=1)

    hdr_s = ctk.CTkFrame(strategy_card, fg_color="transparent")
    hdr_s.grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(6, 6))
    ctk.CTkLabel(hdr_s, text="2. Strategy & Rules", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).pack(side="left")
    create_info_icon(hdr_s, "Configure sorting rules: Date (Year/Month), File Category, Extension, A-Z Name, or File Size.").pack(side="left", padx=6)

    ctk.CTkLabel(strategy_card, text="Sort By:", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").grid(row=1, column=0, sticky="w", padx=(12, 4), pady=4)

    gui_instance.sort_category_var = ctk.StringVar(value="📅 Date (Creation / Mod / EXIF)")
    gui_instance.category_dropdown = ctk.CTkOptionMenu(
        strategy_card,
        variable=gui_instance.sort_category_var,
        values=[
            "📅 Date (Creation / Mod / EXIF)",
            "🎯 Smart Full Name (Auto-Catch Random/Hashes)",
            "📁 File Category (Images, Docs...)",
            "🏷️ Extension (PDF, PNG, DOCX...)",
            "🔤 Alphabetical (A-Z)",
            "⚖️ File Size (<1MB, >100MB...)"
        ],
        command=gui_instance.on_category_changed,
        font=ctk.CTkFont(size=11),
        dropdown_font=ctk.CTkFont(size=11),
        height=32,
        dynamic_resizing=True
    )
    gui_instance.category_dropdown.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=4)

    ctk.CTkLabel(strategy_card, text="Action:", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").grid(row=1, column=2, sticky="w", padx=(6, 4), pady=4)

    gui_instance.mode_segmented = ctk.CTkSegmentedButton(strategy_card, values=["Move", "Copy"], font=ctk.CTkFont(size=11, weight="bold"), height=32)
    gui_instance.mode_segmented.set("Move")
    gui_instance.mode_segmented.grid(row=1, column=3, sticky="ew", padx=(0, 12), pady=4)

    # ── Smart Name extra controls (shown only when Smart Full Name mode is active) ──
    gui_instance._smart_name_extra_row = ctk.CTkFrame(strategy_card, fg_color="transparent")
    gui_instance._smart_name_extra_row.grid(row=2, column=0, columnspan=4, sticky="ew", padx=12, pady=(0, 4))

    ctk.CTkLabel(gui_instance._smart_name_extra_row, text="Unsorted Subdivide:",
                 font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 6))
    gui_instance.unsorted_subdivide_var = ctk.StringVar(value="🗂️ None (Flat)")
    gui_instance.unsorted_subdivide_dropdown = ctk.CTkOptionMenu(
        gui_instance._smart_name_extra_row,
        variable=gui_instance.unsorted_subdivide_var,
        values=[
            "🗂️ None (Flat)",
            "📁 By File Type (Images / Videos / Other)",
            "📅 By Month (YYYY-MM)"
        ],
        font=ctk.CTkFont(size=11),
        dropdown_font=ctk.CTkFont(size=11),
        height=28,
        width=220
    )
    gui_instance.unsorted_subdivide_dropdown.pack(side="left", padx=(0, 18))
    CTkToolTip(gui_instance.unsorted_subdivide_dropdown,
               "Subdivide the Unsorted catch-all folder:\n• None (Flat): all random files in Unsorted/.\n• By File Type: Unsorted/Images/, Unsorted/Videos/, Unsorted/Other/.\n• By Month: Unsorted/YYYY-MM/ based on file modification date.")

    gui_instance.iso_date_prefix_var = tk.BooleanVar(value=False)
    iso_chk = ctk.CTkCheckBox(
        gui_instance._smart_name_extra_row,
        text="📅 ISO Date Prefix (rename to YYYY-MM-DD_filename.ext)",
        variable=gui_instance.iso_date_prefix_var,
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color="#00acc1"
    )
    iso_chk.pack(side="left", padx=(0, 18))
    CTkToolTip(iso_chk, "When checked, renames each file with an ISO date prefix (e.g. 2026-08-25_invoice.pdf) so files sort chronologically natively in Windows/macOS.")

    gui_instance.route_corrupted_var = tk.BooleanVar(value=False)
    corr_chk = ctk.CTkCheckBox(
        gui_instance._smart_name_extra_row,
        text="🚨 Route Zero-Byte to Review_Corrupted/",
        variable=gui_instance.route_corrupted_var,
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color="#ef5350"
    )
    corr_chk.pack(side="left")
    CTkToolTip(corr_chk, "Moves zero-byte / corrupted files to a separate Review_Corrupted/ folder instead of sorting them normally.")

    # Hide by default (shown only when Smart Full Name is selected)
    gui_instance._smart_name_extra_row.grid_remove()
    # ── End Smart Name extra controls ──

    gui_instance.sub_options_lbl = ctk.CTkLabel(strategy_card, text="Date Src:", font=ctk.CTkFont(size=11, weight="bold"), anchor="w")
    gui_instance.sub_options_lbl.grid(row=3, column=0, sticky="w", padx=(12, 4), pady=4)

    gui_instance.date_source_var = ctk.StringVar(value="📅 Smart Auto (Filename Date -> EXIF -> File System)")
    gui_instance.date_src_dropdown = ctk.CTkOptionMenu(
        strategy_card,
        variable=gui_instance.date_source_var,
        values=[
            "📅 Smart Auto (Filename Date -> EXIF -> File System)",
            "🔤 Filename Embedded Date (e.g. 20022022)",
            "ctime (Creation Date)",
            "mtime (Modification Date)",
            "exif (Camera EXIF / Fallback)"
        ],
        font=ctk.CTkFont(size=11),
        dropdown_font=ctk.CTkFont(size=11),
        height=32,
        dynamic_resizing=True
    )
    gui_instance.date_src_dropdown.grid(row=3, column=1, sticky="ew", padx=(0, 10), pady=4)
    CTkToolTip(gui_instance.date_src_dropdown, "Selects source for sorting dates:\n• Smart Auto: Parses embedded filename dates (e.g. 20022022), EXIF, then OS file dates.\n• Filename Embedded Date: Extracts 8-digit or ISO dates directly from filenames.")

    gui_instance.format_lbl = ctk.CTkLabel(strategy_card, text="Format:", font=ctk.CTkFont(size=11, weight="bold"), anchor="w")
    gui_instance.format_lbl.grid(row=3, column=2, sticky="w", padx=(6, 4), pady=4)

    gui_instance.structure_var = ctk.StringVar(value="YYYY/MM (e.g. 2020/01)")
    gui_instance.struct_dropdown = ctk.CTkOptionMenu(
        strategy_card,
        variable=gui_instance.structure_var,
        values=["YYYY/MM (e.g. 2020/01)", "YYYY/MM - Month (e.g. 2020/01 - January)", "YYYY-MM (e.g. 2020-01)", "YYYY/MM/DD (e.g. 2020/01/15)"],
        font=ctk.CTkFont(size=11),
        dropdown_font=ctk.CTkFont(size=11),
        height=32,
        dynamic_resizing=True
    )
    gui_instance.struct_dropdown.grid(row=3, column=3, sticky="ew", padx=(0, 12), pady=4)

    ctk.CTkLabel(strategy_card, text="Conflicts:", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").grid(row=4, column=0, sticky="w", padx=(12, 4), pady=4)

    gui_instance.conflict_mode_var = ctk.StringVar(value="🛡️ Skip Conflicts (Default)")
    gui_instance.conflict_dropdown = ctk.CTkOptionMenu(
        strategy_card,
        variable=gui_instance.conflict_mode_var,
        values=[
            "🛡️ Skip Conflicts (Default)",
            "🔍 Interactive Windows 11 Resolver (Prompt me to compare!)",
            "🔢 Keep Both (Auto-number name_1.ext)",
            "♻️ Replace Target File (Backup to Vault)"
        ],
        font=ctk.CTkFont(size=11),
        dropdown_font=ctk.CTkFont(size=11),
        height=32,
        dynamic_resizing=True
    )
    gui_instance.conflict_dropdown.grid(row=4, column=1, columnspan=3, sticky="ew", padx=(0, 12), pady=4)

    # Exclusions & Filters Card
    filter_card = ctk.CTkFrame(scroll, corner_radius=16)
    filter_card.grid(row=3, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=6)
    filter_card.grid_columnconfigure(0, weight=0)
    filter_card.grid_columnconfigure(1, weight=1)
    filter_card.grid_columnconfigure(2, weight=0)
    filter_card.grid_columnconfigure(3, weight=1)

    hdr_f = ctk.CTkFrame(filter_card, fg_color="transparent")
    hdr_f.grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(6, 4))
    ctk.CTkLabel(hdr_f, text="3. Exclusions & Execution Options", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).pack(side="left")
    create_info_icon(hdr_f, "Filter files by extension, exclude specific subfolders or file names, and toggle safety zip backups.").pack(side="left", padx=6)

    ctk.CTkLabel(filter_card, text="Include Exts:", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").grid(row=1, column=0, sticky="w", padx=(12, 4), pady=3)

    gui_instance.include_ext_var = tk.StringVar()
    gui_instance.inc_entry = ctk.CTkEntry(filter_card, textvariable=gui_instance.include_ext_var, placeholder_text="e.g. .jpg, .png, .pdf", font=ctk.CTkFont(size=11), height=28)
    gui_instance.inc_entry.grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=3)

    ctk.CTkLabel(filter_card, text="Exclude Exts:", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").grid(row=1, column=2, sticky="w", padx=(6, 4), pady=3)

    gui_instance.exclude_ext_var = tk.StringVar(value=".tmp, .log, .bak, .crdownload, .part")
    gui_instance.exc_entry = ctk.CTkEntry(filter_card, textvariable=gui_instance.exclude_ext_var, placeholder_text="e.g. .tmp, .log", font=ctk.CTkFont(size=11), height=28)
    gui_instance.exc_entry.grid(row=1, column=3, sticky="ew", padx=(0, 12), pady=3)

    ctk.CTkLabel(filter_card, text="Exclude Folders:", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").grid(row=2, column=0, sticky="w", padx=(12, 4), pady=3)

    gui_instance.exclude_folders_var = tk.StringVar(value=".git, node_modules, _Duplicates, temp")
    gui_instance.exc_fold_entry = ctk.CTkEntry(filter_card, textvariable=gui_instance.exclude_folders_var, placeholder_text="e.g. .git, node_modules, temp", font=ctk.CTkFont(size=11), height=28)
    gui_instance.exc_fold_entry.grid(row=2, column=1, sticky="ew", padx=(0, 6), pady=3)

    exc_fold_box = ctk.CTkFrame(filter_card, fg_color="transparent")
    exc_fold_box.grid(row=2, column=2, columnspan=2, sticky="w", padx=(0, 12), pady=3)

    btn_f = ctk.CTkButton(exc_fold_box, text="+ Add Folder", command=gui_instance.add_exclude_folder_picker, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#c62828", height=26, width=90)
    btn_f.pack(side="left", padx=(0, 4))

    ctk.CTkButton(exc_fold_box, text="Clear", command=lambda: gui_instance.exclude_folders_var.set(""), font=ctk.CTkFont(size=10), fg_color=("gray75", "gray30"), text_color=("gray10", "gray90"), height=26, width=50).pack(side="left")

    ctk.CTkLabel(filter_card, text="Exclude Files:", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").grid(row=3, column=0, sticky="w", padx=(12, 4), pady=3)

    gui_instance.exclude_files_var = tk.StringVar(value="desktop.ini, .DS_Store, thumbs.db")
    gui_instance.exc_file_entry = ctk.CTkEntry(filter_card, textvariable=gui_instance.exclude_files_var, placeholder_text="e.g. desktop.ini, thumbs.db", font=ctk.CTkFont(size=11), height=28)
    gui_instance.exc_file_entry.grid(row=3, column=1, sticky="ew", padx=(0, 6), pady=3)

    exc_file_box = ctk.CTkFrame(filter_card, fg_color="transparent")
    exc_file_box.grid(row=3, column=2, columnspan=2, sticky="w", padx=(0, 12), pady=3)

    btn_fi = ctk.CTkButton(exc_file_box, text="+ Add File", command=gui_instance.add_exclude_file_picker, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#ad1457", height=26, width=80)
    btn_fi.pack(side="left", padx=(0, 4))

    ctk.CTkButton(exc_file_box, text="Clear", command=lambda: gui_instance.exclude_files_var.set(""), font=ctk.CTkFont(size=10), fg_color=("gray75", "gray30"), text_color=("gray10", "gray90"), height=26, width=50).pack(side="left")

    # Checkboxes Grid
    chk_box = ctk.CTkFrame(filter_card, fg_color="transparent")
    chk_box.grid(row=4, column=0, columnspan=4, sticky="w", padx=12, pady=(4, 6))

    gui_instance.enable_zip_backup_var = tk.BooleanVar(value=False)
    chk0 = ctk.CTkCheckBox(chk_box, text="📦 System Vault Zip Backup (Optional ZIP Archive — Unchecked for Cloud/OneDrive)", variable=gui_instance.enable_zip_backup_var, font=ctk.CTkFont(size=11, weight="bold"), text_color="#0288d1")
    chk0.grid(row=0, column=0, sticky="w", padx=(0, 15), pady=3)

    gui_instance.recursive_var = tk.BooleanVar(value=True)
    chk1 = ctk.CTkCheckBox(chk_box, text="Process Subfolders (Scan subdirectories)", variable=gui_instance.recursive_var, font=ctk.CTkFont(size=11))
    chk1.grid(row=0, column=1, sticky="w", padx=(0, 15), pady=3)

    gui_instance.isolate_dup_var = tk.BooleanVar(value=False)
    chk2 = ctk.CTkCheckBox(chk_box, text="👯 Isolate Duplicates to _Duplicates/", variable=gui_instance.isolate_dup_var, font=ctk.CTkFont(size=11, weight="bold"), text_color="#ab47bc")
    chk2.grid(row=1, column=0, sticky="w", padx=(0, 15), pady=3)

    gui_instance.dry_run_var = tk.BooleanVar(value=False)
    chk3 = ctk.CTkCheckBox(chk_box, text="Dry Run (Test preview without modifying disk)", variable=gui_instance.dry_run_var, font=ctk.CTkFont(size=11))
    chk3.grid(row=1, column=1, sticky="w", padx=(0, 15), pady=3)

    gui_instance.clean_empty_var = tk.BooleanVar(value=True)
    chk4 = ctk.CTkCheckBox(chk_box, text="🧹 Clean Empty Folders (Delete leftover empty folders & OS junk)", variable=gui_instance.clean_empty_var, font=ctk.CTkFont(size=11, weight="bold"), text_color="#ff9800")
    chk4.grid(row=2, column=0, sticky="w", padx=(0, 15), pady=3)

    gui_instance.sync_filename_dates_var = tk.BooleanVar(value=False)
    chk5 = ctk.CTkCheckBox(chk_box, text="📅 Fix OS Timestamps (Update file dates to match filename date)", variable=gui_instance.sync_filename_dates_var, font=ctk.CTkFont(size=11, weight="bold"), text_color="#00acc1")
    chk5.grid(row=2, column=1, sticky="w", padx=(0, 15), pady=3)
    CTkToolTip(chk5, "When checked, updates the file's creation/modified dates on Windows to match the date extracted from its filename (fixes 1980/1987 corrupt OS dates!)")

    skip_row = ctk.CTkFrame(chk_box, fg_color="transparent")
    skip_row.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 2))

    ctk.CTkLabel(skip_row, text="Skipped Files Handling:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 6))

    gui_instance.skipped_handling_var = tk.StringVar(value="📌 Leave in Original Location (Default)")
    gui_instance.skipped_dropdown = ctk.CTkOptionMenu(
        skip_row,
        variable=gui_instance.skipped_handling_var,
        values=[
            "📌 Leave in Original Location (Default)",
            "📁 Move Skipped Files to '_Skipped_Files' Folder",
            "📂 Move Skipped Files to Custom Folder..."
        ],
        command=gui_instance.on_skipped_handling_changed,
        font=ctk.CTkFont(size=11),
        dropdown_font=ctk.CTkFont(size=11),
        height=28,
        width=270
    )
    gui_instance.skipped_dropdown.pack(side="left", padx=(0, 8))
    CTkToolTip(gui_instance.skipped_dropdown, "Controls what happens to files that are NOT matched or sorted:\n• Leave in Original Location: Untouched files stay right where they are.\n• Move Skipped Files: Gathers all skipped/excluded files into a '_Skipped_Files' folder.")

    gui_instance.custom_skipped_dest_var = tk.StringVar()

    # Live Preview Table
    preview_card = ctk.CTkFrame(scroll, corner_radius=16)
    preview_card.grid(row=4, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=6)
    preview_card.grid_columnconfigure(0, weight=1)

    preview_hdr = ctk.CTkFrame(preview_card, fg_color="transparent")
    preview_hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(6, 4))
    preview_hdr.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(preview_hdr, text="4. Live File Map Preview", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).grid(row=0, column=0, sticky="w")
    create_info_icon(preview_hdr, "Shows exact destination paths and duplicate warnings before executing!").grid(row=0, column=1, sticky="w", padx=6)

    gui_instance.preview_stats_lbl = ctk.CTkLabel(preview_hdr, text="Files Found: 0 | Size: 0 B | Duplicates: 0", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray60")
    gui_instance.preview_stats_lbl.grid(row=0, column=2, sticky="e", padx=(0, 8))

    gui_instance.show_plan_btn = ctk.CTkButton(
        preview_hdr, text="📋 Show Plan",
        command=gui_instance.show_smart_name_plan,
        font=ctk.CTkFont(size=11, weight="bold"),
        height=28, width=110, fg_color=("#AF52DE", "#BF5AF2") if HAS_THEME else "#7b1fa2"
    )
    gui_instance.show_plan_btn.grid(row=0, column=3, sticky="e", padx=(0, 6))
    CTkToolTip(gui_instance.show_plan_btn, "Shows a pre-execution plan summary: proposed folders, Unsorted count, and files needing manual review — before anything is moved.")
    # Only show in Smart Name mode
    gui_instance.show_plan_btn.grid_remove()

    gui_instance.scan_btn = ctk.CTkButton(preview_hdr, text="🔍 Scan Preview", command=gui_instance.refresh_preview, font=ctk.CTkFont(size=11, weight="bold"), height=28, width=120, fg_color=("#007AFF", "#0A84FF") if HAS_THEME else "#0288d1")
    gui_instance.scan_btn.grid(row=0, column=4, sticky="e")

    tree_frame = ctk.CTkFrame(preview_card, corner_radius=8, fg_color=("gray95", "gray15"))
    tree_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
    tree_frame.grid_columnconfigure(0, weight=1)
    tree_frame.grid_rowconfigure(0, weight=1)

    columns = ("filename", "rel_src", "rel_target", "category", "size_str", "status")
    gui_instance.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=5)
    gui_instance.tree.heading("filename", text="File Name", command=lambda: gui_instance._sort_tree(gui_instance.tree, "filename"))
    gui_instance.tree.heading("rel_src", text="Current Subpath", command=lambda: gui_instance._sort_tree(gui_instance.tree, "rel_src"))
    gui_instance.tree.heading("rel_target", text="Target Path", command=lambda: gui_instance._sort_tree(gui_instance.tree, "rel_target"))
    gui_instance.tree.heading("category", text="Category", command=lambda: gui_instance._sort_tree(gui_instance.tree, "category"))
    gui_instance.tree.heading("size_str", text="Size", command=lambda: gui_instance._sort_tree(gui_instance.tree, "size_str"))
    gui_instance.tree.heading("status", text="Status", command=lambda: gui_instance._sort_tree(gui_instance.tree, "status"))

    gui_instance.tree.column("filename", width=180)
    gui_instance.tree.column("rel_src", width=180)
    gui_instance.tree.column("rel_target", width=220)
    gui_instance.tree.column("category", width=110)
    gui_instance.tree.column("size_str", width=90)
    gui_instance.tree.column("status", width=120)

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=gui_instance.tree.yview)
    gui_instance.tree.configure(yscrollcommand=scrollbar.set)
    gui_instance.tree.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
    scrollbar.grid(row=0, column=1, sticky="ns", pady=4)

    preview_card.grid_rowconfigure(1, weight=1, minsize=140)

    # Zero-Deletion Guarantee Banner — placed inside preview_card at row=2,
    # cleanly separated from tree_frame above with explicit spacing.
    guarantee_card = ctk.CTkFrame(preview_card, corner_radius=10, fg_color=("#e8f5e9", "#1b3320"), border_color="#388e3c", border_width=1)
    guarantee_card.grid(row=2, column=0, sticky="ew", padx=12, pady=(10, 8), ipadx=8, ipady=4)

    ctk.CTkLabel(
        guarantee_card,
        text="🛡️ ZERO-DELETION GUARANTEE: Files are safely organized into subfolders. Conflicts can be skipped or resolved with the Windows 11 comparison dialog.",
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        text_color=("#1b5e20", "#81c784")
    ).pack(side="left", padx=12, pady=4)

    # Action Buttons & Progress
    action_card = ctk.CTkFrame(scroll, fg_color="transparent")
    action_card.grid(row=5, column=0, sticky="ew", pady=(0, 8))
    action_card.grid_columnconfigure(4, weight=1)

    gui_instance.start_btn = ctk.CTkButton(
        action_card,
        text="▶ Start Sorting",
        command=gui_instance.start_sorting,
        font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        fg_color="#1b5e20",
        hover_color="#2e7d32",
        height=36,
        width=140
    )
    gui_instance.start_btn.grid(row=0, column=0, padx=(0, 6), sticky="w")

    btn_del_empty = ctk.CTkButton(
        action_card,
        text="🧹 Delete Empty Folders",
        command=lambda: gui_instance.run_delete_empty_folders(gui_instance.dir_var.get().strip()),
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        fg_color="#e65100",
        hover_color="#f57c00",
        height=36,
        width=175
    )
    btn_del_empty.grid(row=0, column=1, padx=(0, 6), sticky="w")

    gui_instance.undo_btn = ctk.CTkButton(
        action_card,
        text="🛡️ System Vault Restore",
        command=gui_instance.open_system_vault_restore_manager,
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        fg_color="#c62828",
        hover_color="#d32f2f",
        height=36,
        width=175
    )
    gui_instance.undo_btn.grid(row=0, column=2, padx=(0, 10), sticky="w")

    gui_instance.progress_bar = ctk.CTkProgressBar(action_card, height=14)
    gui_instance.progress_bar.set(0)
    gui_instance.progress_bar.grid(row=0, column=3, sticky="ew", padx=6)

    # Live Execution Console Log Card
    log_card = ctk.CTkFrame(scroll, corner_radius=16)
    log_card.grid(row=6, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=6)
    log_card.grid_columnconfigure(0, weight=1)

    log_hdr = ctk.CTkFrame(log_card, fg_color="transparent")
    log_hdr.pack(fill="x", padx=12, pady=(6, 2))
    ctk.CTkLabel(log_hdr, text="5. Real-Time Activity Log Console", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")).pack(side="left")

    gui_instance.log_textbox = ctk.CTkTextbox(log_card, height=130, font=ctk.CTkFont(family="Consolas", size=10))
    gui_instance.log_textbox.pack(fill="both", expand=True, padx=12, pady=(2, 6))

    try:
        tb = gui_instance.log_textbox._textbox
        tb.tag_config("header", foreground="#64b5f6", font=("Consolas", 10, "bold"))
        tb.tag_config("success", foreground="#81c784")
        tb.tag_config("error", foreground="#e57373")
        tb.tag_config("warning", foreground="#ffb74d")
        tb.tag_config("info", foreground="#e0e0e0")
    except Exception:
        pass

