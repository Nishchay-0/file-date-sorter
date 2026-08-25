import os
import tkinter as tk
from gui_modules.components import CTkToolTip, create_info_icon, GRANULAR_FILE_TYPES

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


def setup_duplicates_tab(gui_instance):
    gui_instance.dup_main_scroll = ctk.CTkScrollableFrame(gui_instance.tab_duplicates, fg_color="transparent")
    main_container = gui_instance.dup_main_scroll
    main_container.pack(fill="both", expand=True)
    main_container.grid_columnconfigure(0, weight=1)

    dup_control_card = ctk.CTkFrame(main_container, corner_radius=16)
    dup_control_card.pack(fill="x", pady=(0, 6), ipadx=8, ipady=6)
    dup_control_card.grid_columnconfigure(1, weight=1)

    hdr_dup = ctk.CTkFrame(dup_control_card, fg_color="transparent")
    hdr_dup.grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(4, 4))
    ctk.CTkLabel(hdr_dup, text="🔍 Windows 11 Style Duplicate Conflict Finder", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).pack(side="left")
    create_info_icon(hdr_dup, "Finds duplicate files across subfolders and renders side-by-side comparison cards with real thumbnails!").pack(side="left", padx=6)

    ctk.CTkLabel(dup_control_card, text="Scan Folder:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, sticky="w", padx=(12, 8), pady=3)

    gui_instance.dup_dir_var = tk.StringVar()
    gui_instance.dup_dir_entry = ctk.CTkEntry(dup_control_card, textvariable=gui_instance.dup_dir_var, placeholder_text="Select folder to scan for duplicate conflicts...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.dup_dir_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=3)

    dup_btn_box = ctk.CTkFrame(dup_control_card, fg_color="transparent")
    dup_btn_box.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=3)

    ctk.CTkButton(dup_btn_box, text="📁 Pick Folder...", command=gui_instance.browse_dup_folder, font=ctk.CTkFont(size=10, weight="bold"), height=32, width=95).pack(side="left", padx=(0, 3))
    ctk.CTkButton(dup_btn_box, text="📁+ Multi Folders...", command=lambda: gui_instance.browse_multiple_folders(gui_instance.dup_dir_var, gui_instance.run_find_duplicates), font=ctk.CTkFont(size=10, weight="bold"), fg_color="#1565c0", height=32, width=110).pack(side="left", padx=(0, 3))
    ctk.CTkButton(dup_btn_box, text="📄 Pick Files...", command=gui_instance.browse_dup_files, font=ctk.CTkFont(size=10, weight="bold"), fg_color=("#32ADE6", "#64D2FF") if HAS_THEME else "#00838f", height=32, width=90).pack(side="left")

    # Dedicated Delete / Discard Folder Selection Row
    ctk.CTkLabel(dup_control_card, text="Delete Folder:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#ef9a9a").grid(row=2, column=0, sticky="w", padx=(12, 8), pady=3)

    gui_instance.dup_discard_dir_var = getattr(gui_instance, 'dup_discard_dir_var', tk.StringVar())
    gui_instance.dup_discard_entry = ctk.CTkEntry(dup_control_card, textvariable=gui_instance.dup_discard_dir_var, placeholder_text="Select folder location where deleted duplicate files will be stored...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.dup_discard_entry.grid(row=2, column=1, sticky="ew", padx=(0, 8), pady=3)

    dup_discard_btn_box = ctk.CTkFrame(dup_control_card, fg_color="transparent")
    dup_discard_btn_box.grid(row=2, column=2, sticky="e", padx=(0, 12), pady=3)

    ctk.CTkButton(dup_discard_btn_box, text="🗑️ Select Delete Folder...", command=gui_instance.browse_dup_discard_folder, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#c62828", height=32, width=155).pack(side="left", padx=(0, 3))
    ctk.CTkButton(dup_discard_btn_box, text="🧹 Reset", command=lambda: gui_instance.dup_discard_dir_var.set(""), font=ctk.CTkFont(size=10), height=32, width=55, fg_color=("gray75", "gray30"), text_color=("gray10", "gray90")).pack(side="left")

    # Single Combined Keep Folder Selection Control (Default: Original Location)
    ctk.CTkLabel(dup_control_card, text="Keep Folder:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#81c784").grid(row=3, column=0, sticky="w", padx=(12, 8), pady=3)

    gui_instance.dup_dest_dir_var = getattr(gui_instance, 'dup_dest_dir_var', tk.StringVar())
    gui_instance.dup_kept_mode_var = getattr(gui_instance, 'dup_kept_mode_var', tk.StringVar(value="original"))
    gui_instance.dup_dest_entry = ctk.CTkEntry(dup_control_card, textvariable=gui_instance.dup_dest_dir_var, placeholder_text="📍 Default Location (Kept files stay in original path)", font=ctk.CTkFont(size=11), height=32)
    gui_instance.dup_dest_entry.grid(row=3, column=1, sticky="ew", padx=(0, 8), pady=3)

    dup_dest_btn_box = ctk.CTkFrame(dup_control_card, fg_color="transparent")
    dup_dest_btn_box.grid(row=3, column=2, sticky="e", padx=(0, 12), pady=3)

    ctk.CTkButton(dup_dest_btn_box, text="📁 Select Custom Keep Folder...", command=gui_instance.browse_dup_dest_folder, font=ctk.CTkFont(size=10, weight="bold"), fg_color=("#FF9500", "#FF9F0A") if HAS_THEME else "#f57c00", height=32, width=175).pack(side="left", padx=(0, 3))
    ctk.CTkButton(dup_dest_btn_box, text="🧹 Default", command=gui_instance.reset_dup_dest_folder, font=ctk.CTkFont(size=10, weight="bold"), height=32, width=65, fg_color=("gray75", "gray30"), text_color=("gray10", "gray90")).pack(side="left")
    CTkToolTip(dup_dest_btn_box, "By default, kept files remain in their original location. Click 'Select Custom Keep Folder...' to move them elsewhere.")

    # Dedicated Exclusions Row
    ctk.CTkLabel(dup_control_card, text="Exclusions (Opt):", font=ctk.CTkFont(size=11, weight="bold"), text_color="#ef5350").grid(row=4, column=0, sticky="w", padx=(12, 8), pady=3)

    gui_instance.dup_exc_entry = ctk.CTkEntry(dup_control_card, textvariable=gui_instance.exclude_folders_var, placeholder_text="Folders/Subfolders to SKIP...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.dup_exc_entry.grid(row=4, column=1, sticky="ew", padx=(0, 8), pady=3)

    dup_exc_btn_box = ctk.CTkFrame(dup_control_card, fg_color="transparent")
    dup_exc_btn_box.grid(row=4, column=2, sticky="e", padx=(0, 12), pady=3)

    ctk.CTkButton(dup_exc_btn_box, text="🚫 Except Folder...", command=gui_instance.add_exclude_folder_picker, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#c62828", height=32, width=105).pack(side="left", padx=(0, 3))
    ctk.CTkButton(dup_exc_btn_box, text="🚫 Except Files...", command=gui_instance.add_exclude_file_picker, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#ad1457", height=32, width=95).pack(side="left", padx=(0, 3))
    ctk.CTkButton(dup_exc_btn_box, text="🧹 Clear", command=lambda: gui_instance.exclude_folders_var.set(""), font=ctk.CTkFont(size=10), height=32, width=55, fg_color=("gray75", "gray30"), text_color=("gray10", "gray90")).pack(side="left")

    # Matching Rule Row 1
    match_frame1 = ctk.CTkFrame(dup_control_card, fg_color="transparent")
    match_frame1.grid(row=5, column=0, columnspan=3, sticky="w", padx=12, pady=(3, 2))

    ctk.CTkLabel(match_frame1, text="Matching Rule:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 8))

    gui_instance.dup_match_var = tk.StringVar(value="content")
    rb1 = ctk.CTkRadioButton(match_frame1, text="Exact Byte (SHA-256)", variable=gui_instance.dup_match_var, value="content", font=ctk.CTkFont(size=11, weight="bold"))
    rb1.pack(side="left", padx=(0, 10))

    rb5 = ctk.CTkRadioButton(match_frame1, text="⚡ Quick Scan (Name + Size — No Download Required)", variable=gui_instance.dup_match_var, value="name_size", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2e7d32")
    rb5.pack(side="left", padx=(0, 10))

    rb2 = ctk.CTkRadioButton(match_frame1, text="👁️ Visual Image Similarity", variable=gui_instance.dup_match_var, value="perceptual_image", font=ctk.CTkFont(size=11, weight="bold"), text_color="#00acc1")
    rb2.pack(side="left", padx=(0, 10))

    # Matching Rule Row 2 (Metadata & Thresholds)
    match_frame2 = ctk.CTkFrame(dup_control_card, fg_color="transparent")
    match_frame2.grid(row=7, column=0, columnspan=3, sticky="w", padx=12, pady=(2, 3))

    rb3 = ctk.CTkRadioButton(match_frame2, text="🔤 Fuzzy Name Match", variable=gui_instance.dup_match_var, value="fuzzy_name", font=ctk.CTkFont(size=11, weight="bold"), text_color="#8e24aa")
    rb3.pack(side="left", padx=(0, 10))

    rb4 = ctk.CTkRadioButton(match_frame2, text="📝 Text Similarity", variable=gui_instance.dup_match_var, value="text_similarity", font=ctk.CTkFont(size=11))
    rb4.pack(side="left", padx=(0, 10))

    rb6 = ctk.CTkRadioButton(match_frame2, text="Name + Size + Date", variable=gui_instance.dup_match_var, value="name_size_mtime", font=ctk.CTkFont(size=11))
    rb6.pack(side="left", padx=(0, 15))

    ctk.CTkLabel(match_frame2, text="Similarity Threshold:", font=ctk.CTkFont(size=10, weight="bold")).pack(side="left", padx=(5, 4))
    gui_instance.dup_threshold_var = tk.StringVar(value="90% Match")
    threshold_cb = ctk.CTkOptionMenu(
        match_frame2,
        values=["80% Match", "85% Match", "90% Match", "95% Match", "98% Match", "100% Match"],
        variable=gui_instance.dup_threshold_var,
        font=ctk.CTkFont(size=10, weight="bold"),
        width=100,
        height=24
    )
    threshold_cb.pack(side="left", padx=(0, 10))
    CTkToolTip(threshold_cb, "Sets minimum similarity percentage cutoff for Visual Image, Fuzzy Name, or Text matching.")

    btn_onedrive = ctk.CTkButton(
        match_frame2,
        text="☁️ OneDrive Mode",
        command=gui_instance.set_onedrive_dup_mode,
        font=ctk.CTkFont(size=10, weight="bold"),
        fg_color=("#007AFF", "#0A84FF") if HAS_THEME else "#0288d1",
        hover_color="#0277bd",
        height=24
    )
    btn_onedrive.pack(side="left", padx=(5, 0))
    CTkToolTip(btn_onedrive, "Configures scanner for OneDrive Files On-Demand (0 Bytes Downloaded!).")

    # 2-Column Granular File Type Multi-Selector & Custom Extension Picker (Matching Sorter/Extractor Layout!)
    ext_strat_card = ctk.CTkFrame(dup_control_card, corner_radius=10, fg_color=("gray90", "gray18"))
    ext_strat_card.grid(row=8, column=0, columnspan=3, sticky="ew", padx=12, pady=(4, 6), ipadx=8, ipady=6)
    ext_strat_card.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(ext_strat_card, text="2. Filter Strategy & Specific File Type Multi-Selector", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 4))

    cats_outer = ctk.CTkFrame(ext_strat_card, fg_color="transparent")
    cats_outer.grid(row=1, column=0, columnspan=2, sticky="ew", padx=6, pady=2)
    cats_outer.grid_columnconfigure(0, weight=1)
    cats_outer.grid_columnconfigure(1, weight=1)

    gui_instance.dup_granular_checkbox_vars = {}
    gui_instance.dup_sub_vars = {}
    gui_instance._dup_cat_sub_frames = {}

    sel_toolbar = ctk.CTkFrame(cats_outer, fg_color="transparent")
    sel_toolbar.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
    ctk.CTkLabel(sel_toolbar, text="Quick:", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray60").pack(side="left", padx=(0, 6))
    
    btn_univ_quick = ctk.CTkButton(
        sel_toolbar,
        text="🌐 Universal All-Files Scan",
        command=gui_instance.run_universal_duplicate_scan,
        font=ctk.CTkFont(size=10, weight="bold"),
        height=22,
        width=165,
        fg_color="#1565c0",
        hover_color="#0d47a1"
    )
    btn_univ_quick.pack(side="left", padx=(0, 4))
    CTkToolTip(btn_univ_quick, "Automatically selects ALL file categories (Images, Videos, Docs, PDFs, Audio, Code, Zip) and launches scan!")

    ctk.CTkButton(sel_toolbar, text="☑ Select All Categories", command=gui_instance.dup_select_all_cats, font=ctk.CTkFont(size=10), height=22, width=145, fg_color=("#007AFF", "#0A84FF") if HAS_THEME else "#0288d1").pack(side="left", padx=(0, 4))
    ctk.CTkButton(sel_toolbar, text="☐ Clear All", command=gui_instance.dup_clear_all_cats, font=ctk.CTkFont(size=10), height=22, width=80, fg_color=("gray72", "gray32"), text_color=("gray10", "gray90")).pack(side="left", padx=(0, 4))
    ctk.CTkButton(sel_toolbar, text="⇄ Invert", command=gui_instance.dup_invert_cats, font=ctk.CTkFont(size=10), height=22, width=65, fg_color=("gray72", "gray32"), text_color=("gray10", "gray90")).pack(side="left")

    cat_row = 1
    cat_col = 0
    for type_label, exts in GRANULAR_FILE_TYPES.items():
        cat_var = tk.BooleanVar(value=True)  # Default: ALL CHECKED for Duplicate Scanner!
        gui_instance.dup_granular_checkbox_vars[type_label] = cat_var

        cat_card = ctk.CTkFrame(cats_outer, corner_radius=8, fg_color=("gray85", "gray25"))
        cat_card.grid(row=cat_row, column=cat_col, sticky="ew", padx=4, pady=3, ipadx=2, ipady=2)

        hdr = ctk.CTkFrame(cat_card, fg_color="transparent")
        hdr.pack(fill="x", padx=6, pady=(4, 2))

        master_chk = ctk.CTkCheckBox(
            hdr, text=type_label, variable=cat_var,
            font=ctk.CTkFont(size=10, weight="bold"),
            checkbox_width=18, checkbox_height=18,
            command=lambda lbl=type_label: gui_instance._sync_dup_sub_from_cat(lbl)
        )
        master_chk.pack(side="left", fill="x", expand=True)

        expand_btn = ctk.CTkButton(
            hdr, text="▶ Exts", width=55, height=20,
            font=ctk.CTkFont(size=9),
            fg_color=("gray75", "gray35"),
            text_color=("gray20", "gray80")
        )
        expand_btn.pack(side="right", padx=(4, 0))

        sub_frame = ctk.CTkFrame(cat_card, fg_color=("gray90", "gray18"), corner_radius=6)
        gui_instance._dup_cat_sub_frames[type_label] = sub_frame

        sub_lbl_row = ctk.CTkFrame(sub_frame, fg_color="transparent")
        sub_lbl_row.pack(fill="x", padx=4, pady=(3, 0))
        ctk.CTkLabel(sub_lbl_row, text="Extensions:", font=ctk.CTkFont(size=9, weight="bold"), text_color="gray60").pack(side="left")
        ctk.CTkButton(sub_lbl_row, text="All", width=28, height=16, font=ctk.CTkFont(size=9),
            command=lambda lbl=type_label: gui_instance._dup_sub_select_all(lbl),
            fg_color=("#007AFF", "#0A84FF") if HAS_THEME else "#0288d1").pack(side="right", padx=1)
        ctk.CTkButton(sub_lbl_row, text="None", width=34, height=16, font=ctk.CTkFont(size=9),
            command=lambda lbl=type_label: gui_instance._dup_sub_clear_all(lbl),
            fg_color=("gray75", "gray35"), text_color=("gray20", "gray80")).pack(side="right", padx=1)

        sub_grid = ctk.CTkFrame(sub_frame, fg_color="transparent")
        sub_grid.pack(fill="x", padx=4, pady=2)
        gui_instance.dup_sub_vars[type_label] = {}

        for s_idx, ext in enumerate(exts):
            sub_v = tk.BooleanVar(value=True)
            gui_instance.dup_sub_vars[type_label][ext] = sub_v
            s_row = s_idx // 3
            s_col = s_idx % 3
            sub_chk = ctk.CTkCheckBox(sub_grid, text=ext, variable=sub_v, font=ctk.CTkFont(size=9), checkbox_width=14, checkbox_height=14)
            sub_chk.grid(row=s_row, column=s_col, sticky="w", padx=2, pady=1)

        def make_toggle(sf=sub_frame, btn=expand_btn):
            def toggle():
                if sf.winfo_ismapped():
                    sf.pack_forget()
                    btn.configure(text="▶ Exts")
                else:
                    sf.pack(fill="x", padx=4, pady=(0, 4))
                    btn.configure(text="▼ Exts")
            return toggle

        expand_btn.configure(command=make_toggle())

        cat_col += 1
        if cat_col > 1:
            cat_col = 0
            cat_row += 1

    # Custom Extension Entry Bar with Detect All Exts in Folder Button!
    custom_row = ctk.CTkFrame(ext_strat_card, fg_color="transparent")
    custom_row.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(4, 2))

    ctk.CTkLabel(custom_row, text="Custom Exts:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 6))

    gui_instance.dup_sub_exts_var = tk.StringVar(value="")
    custom_entry = ctk.CTkEntry(
        custom_row,
        textvariable=gui_instance.dup_sub_exts_var,
        placeholder_text="Enter additional extensions e.g. .raw, .heic, .cr3 (or click Detect button)...",
        font=ctk.CTkFont(size=11),
        height=28
    )
    custom_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

    ctk.CTkButton(
        custom_row,
        text="🔍 Detect All Exts in Folder...",
        command=gui_instance.detect_all_exts_in_dup_folder,
        font=ctk.CTkFont(size=10, weight="bold"),
        fg_color=("#32ADE6", "#64D2FF") if HAS_THEME else "#00838f",
        hover_color="#006064",
        height=28
    ).pack(side="right")

    rec_frame = ctk.CTkFrame(dup_control_card, fg_color="transparent")
    rec_frame.grid(row=9, column=0, columnspan=3, sticky="w", padx=12, pady=(2, 4))

    gui_instance.dup_recursive_var = tk.BooleanVar(value=True)
    chk_rec = ctk.CTkCheckBox(
        rec_frame,
        text="🔍 Deep Subfolder Search (Scan all nested subdirectories deep down)",
        variable=gui_instance.dup_recursive_var,
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color="#0288d1"
    )
    chk_rec.pack(side="left", padx=(0, 10))
    CTkToolTip(chk_rec, "When checked, scans every level of nested subfolders deep down.")

    toolbar_card = ctk.CTkFrame(main_container, corner_radius=10, fg_color=GLASS["bg_card_alt"] if HAS_THEME else ("gray90", "gray17"))
    toolbar_card.pack(fill="x", pady=(0, 6), ipadx=8, ipady=4)

    btn_univ_main = ctk.CTkButton(
        toolbar_card,
        text="🌐 Universal Scan (ALL File Types)",
        command=gui_instance.run_universal_duplicate_scan,
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        fg_color="#1565c0",
        hover_color="#0d47a1",
        height=30,
        width=215
    )
    btn_univ_main.pack(side="left", padx=(10, 4))
    CTkToolTip(btn_univ_main, "1-Click Scan: Automatically selects ALL file types (Images, Videos, Docs, PDFs, Audio, Zip, Code) and starts scanning!")

    ctk.CTkButton(
        toolbar_card,
        text="🔍 Scan Selected",
        command=gui_instance.run_find_duplicates,
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        fg_color=("#007AFF", "#0A84FF") if HAS_THEME else "#0288d1",
        hover_color="#0277bd",
        height=30,
        width=125
    ).pack(side="left", padx=(0, 4))

    ctk.CTkButton(
        toolbar_card,
        text="🪟 Popup Resolver",
        command=gui_instance.open_dup_resolver_modal,
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        fg_color=("#AF52DE", "#BF5AF2") if HAS_THEME else "#7b1fa2",
        hover_color="#6a1b9a",
        height=30,
        width=135
    ).pack(side="left", padx=(0, 8))

    ctk.CTkLabel(toolbar_card, text="Auto-Select:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#64b5f6").pack(side="left", padx=(2, 4))

    ctk.CTkButton(toolbar_card, text="🛡️ Keep Oldest", command=gui_instance.auto_select_keep_oldest, font=ctk.CTkFont(size=10, weight="bold"), height=28, fg_color="#2e7d32").pack(side="left", padx=2)
    ctk.CTkButton(toolbar_card, text="⚡ Keep Newest", command=gui_instance.auto_select_keep_newest, font=ctk.CTkFont(size=10, weight="bold"), height=28, fg_color="#6a1b9a").pack(side="left", padx=2)
    ctk.CTkButton(toolbar_card, text="🖼️ Highest Res", command=gui_instance.auto_select_keep_highest_res, font=ctk.CTkFont(size=10, weight="bold"), height=28, fg_color=("#32ADE6", "#64D2FF") if HAS_THEME else "#00838f").pack(side="left", padx=2)
    ctk.CTkButton(toolbar_card, text="📁 Shortest Path", command=gui_instance.auto_select_keep_shortest_path, font=ctk.CTkFont(size=10, weight="bold"), height=28, fg_color="#e65100").pack(side="left", padx=2)
    ctk.CTkButton(toolbar_card, text="📌 Select All", command=gui_instance.auto_select_all_duplicates, font=ctk.CTkFont(size=10), height=28, fg_color=("gray75", "gray30"), text_color=("gray10", "gray90")).pack(side="left", padx=2)
    ctk.CTkButton(toolbar_card, text="🧹 Clear", command=gui_instance.clear_dup_selection, font=ctk.CTkFont(size=10), height=28, fg_color=("gray75", "gray30"), text_color=("gray10", "gray90")).pack(side="left", padx=2)

    gui_instance.use_trash_backup_var = tk.BooleanVar(value=True)
    chk_trash = ctk.CTkCheckBox(toolbar_card, text="🛡️ System Vault Trash", variable=gui_instance.use_trash_backup_var, font=ctk.CTkFont(size=10, weight="bold"), text_color="#388e3c")
    chk_trash.pack(side="right", padx=10)

    # Dedicated Real-time Progress Meter & Live Scanning Preview Card
    gui_instance.dup_progress_frame = ctk.CTkFrame(main_container, corner_radius=10, fg_color=("gray85", "gray22"))
    gui_instance.dup_progress_frame.pack(fill="x", pady=(0, 6), ipadx=8, ipady=6)
    gui_instance.dup_progress_frame.pack_forget()

    prog_top = ctk.CTkFrame(gui_instance.dup_progress_frame, fg_color="transparent")
    prog_top.pack(fill="x", padx=10, pady=(4, 2))

    gui_instance.dup_progress_title = ctk.CTkLabel(
        prog_top,
        text="⚡ Scanning nested subfolders & computing hashes...",
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        text_color="#0288d1"
    )
    gui_instance.dup_progress_title.pack(side="left")

    gui_instance.dup_progress_pct_lbl = ctk.CTkLabel(
        prog_top,
        text="0%",
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color=("gray30", "gray70")
    )
    gui_instance.dup_progress_pct_lbl.pack(side="right")

    gui_instance.dup_progress_bar = ctk.CTkProgressBar(
        gui_instance.dup_progress_frame,
        progress_color=("#007AFF", "#0A84FF"),
        height=12,
        corner_radius=6
    )
    gui_instance.dup_progress_bar.pack(fill="x", padx=10, pady=4)
    gui_instance.dup_progress_bar.set(0.0)

    gui_instance.dup_progress_detail_lbl = ctk.CTkLabel(
        gui_instance.dup_progress_frame,
        text="📄 Initializing scanner engine...",
        font=ctk.CTkFont(size=10),
        text_color=("gray40", "gray60"),
        anchor="w"
    )
    gui_instance.dup_progress_detail_lbl.pack(fill="x", padx=10, pady=(0, 4))

    # Live Duplicate Breakdown & Space Savings Preview Card (Matching File Organiser Layout!)
    gui_instance.dup_summary_card = ctk.CTkFrame(main_container, corner_radius=16, fg_color=GLASS["bg_card_alt"] if HAS_THEME else ("gray90", "gray17"))
    gui_instance.dup_summary_card.pack(fill="x", pady=(0, 6), ipadx=8, ipady=6)

    sum_hdr = ctk.CTkFrame(gui_instance.dup_summary_card, fg_color="transparent")
    sum_hdr.pack(fill="x", padx=12, pady=(4, 4))
    ctk.CTkLabel(sum_hdr, text="📊 Live Duplicate Scan Summary & Reclaimable Space", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")).pack(side="left")
    create_info_icon(sum_hdr, "Shows real-time duplicate scan results, total reclaimable space, and file category breakdown.").pack(side="left", padx=6)

    sum_grid = ctk.CTkFrame(gui_instance.dup_summary_card, fg_color="transparent")
    sum_grid.pack(fill="x", padx=12, pady=(2, 6))
    sum_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

    gui_instance.dup_lbl_total_scanned = ctk.CTkLabel(sum_grid, text="📁 Files Scanned:\n0", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#0288d1", "#64b5f6"))
    gui_instance.dup_lbl_total_scanned.grid(row=0, column=0, sticky="ew", padx=4)

    gui_instance.dup_lbl_groups_found = ctk.CTkLabel(sum_grid, text="👯 Duplicate Groups:\n0", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#7b1fa2", "#ba68c8"))
    gui_instance.dup_lbl_groups_found.grid(row=0, column=1, sticky="ew", padx=4)

    gui_instance.dup_lbl_reclaimable = ctk.CTkLabel(sum_grid, text="💾 Reclaimable Space:\n0 B", font=ctk.CTkFont(size=11, weight="bold"), text_color=("#2e7d32", "#81c784"))
    gui_instance.dup_lbl_reclaimable.grid(row=0, column=2, sticky="ew", padx=4)

    gui_instance.dup_lbl_cat_breakdown = ctk.CTkLabel(sum_grid, text="🖼️ Categories:\nNo duplicates detected", font=ctk.CTkFont(size=11, weight="bold"), text_color=("gray40", "gray70"))
    gui_instance.dup_lbl_cat_breakdown.grid(row=0, column=3, sticky="ew", padx=4)

    # In-Results Filter Bar
    filter_bar = ctk.CTkFrame(main_container, corner_radius=8, fg_color="transparent")
    filter_bar.pack(fill="x", pady=(0, 4), padx=2)

    ctk.CTkLabel(filter_bar, text="🔎 Quick Filter Results:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(4, 6))
    gui_instance.dup_search_var = tk.StringVar()
    gui_instance.dup_search_var.trace_add("write", lambda *args: gui_instance.filter_dup_cards())
    search_entry = ctk.CTkEntry(filter_bar, textvariable=gui_instance.dup_search_var, placeholder_text="Type to filter results by filename or folder...", font=ctk.CTkFont(size=11), height=28)
    search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

    # Action Card (Clean toolbar above cards view)
    act_card = ctk.CTkFrame(main_container, corner_radius=16, fg_color=("gray85", "gray20"))
    act_card.pack(fill="x", pady=(0, 6), ipadx=8, ipady=4)

    gui_instance.dup_action_lbl = ctk.CTkLabel(act_card, text="Selected: 0 files (0 B ready for cleanup)", font=ctk.CTkFont(size=12, weight="bold"))
    gui_instance.dup_action_lbl.pack(side="left", padx=12)

    act_btns = ctk.CTkFrame(act_card, fg_color="transparent")
    act_btns.pack(side="right", padx=8)

    ctk.CTkButton(act_btns, text="🗑️ Delete Selected", command=gui_instance.delete_selected_duplicates, font=ctk.CTkFont(size=11, weight="bold"), height=32, fg_color="#c62828").pack(side="left", padx=3)
    ctk.CTkButton(act_btns, text="📁 Move Selected to Folder...", command=gui_instance.move_selected_duplicates, font=ctk.CTkFont(size=11, weight="bold"), height=32, fg_color=("#FF9500", "#FF9F0A") if HAS_THEME else "#f57c00").pack(side="left", padx=3)
    ctk.CTkButton(act_btns, text="📦 Move ALL (Originals + Dups)...", command=gui_instance.move_all_group_files_to_folder, font=ctk.CTkFont(size=11, weight="bold"), height=32, fg_color=("#AF52DE", "#BF5AF2") if HAS_THEME else "#7b1fa2").pack(side="left", padx=3)
    ctk.CTkButton(act_btns, text="🔗 Hard Link Duplicates", command=gui_instance.link_selected_duplicates, font=ctk.CTkFont(size=11, weight="bold"), height=32, fg_color="#43a047").pack(side="left", padx=3)
    ctk.CTkButton(act_btns, text="📊 Export Report...", command=gui_instance.export_dup_report, font=ctk.CTkFont(size=11, weight="bold"), height=32, fg_color="#1565c0").pack(side="left", padx=3)

    # Cards View Frame (renders seamlessly inside main_container scrollable tab)
    # NOTE: Must NOT use expand=True here — that would collapse the scrollregion to viewport height
    # causing CTkScrollableFrame to think nothing needs scrolling.
    gui_instance.dup_cards_scroll = ctk.CTkFrame(main_container, fg_color="transparent")
    gui_instance.dup_cards_scroll.pack(fill="x", pady=(0, 4))
    gui_instance.dup_cards_scroll.grid_columnconfigure(0, weight=1)

    gui_instance.placeholder_lbl = ctk.CTkLabel(gui_instance.dup_cards_scroll, text="Click '🔍 Scan Duplicates' to display side-by-side file conflict cards.", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray50")
    gui_instance.placeholder_lbl.pack(pady=30)

    # Real-Time Activity Log Console (Integrated with Live Status)
    gui_instance.dup_log_card = ctk.CTkFrame(
        main_container,
        corner_radius=12,
        fg_color=GLASS["bg_card_alt"] if HAS_THEME else ("gray90", "gray17"),
        border_color=GLASS["border"] if HAS_THEME else ("gray70", "gray30"),
        border_width=1
    )
    gui_instance.dup_log_card.pack(fill="x", pady=(6, 6), ipadx=6, ipady=4)

    dup_log_hdr = ctk.CTkFrame(gui_instance.dup_log_card, fg_color="transparent")
    dup_log_hdr.pack(fill="x", padx=10, pady=(6, 4))
    dup_log_hdr.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(
        dup_log_hdr,
        text="⚡ Real-Time Activity Log Console",
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
    ).grid(row=0, column=0, sticky="w")

    # Integrated Live Status Pill Label in console header
    gui_instance.dup_console_status_lbl = ctk.CTkLabel(
        dup_log_hdr,
        textvariable=gui_instance.status_var,
        font=ctk.CTkFont(family="Segoe UI", size=10),
        text_color=GLASS["accent_blue_dk"] if HAS_THEME else "#0288d1",
        anchor="e"
    )
    gui_instance.dup_console_status_lbl.grid(row=0, column=1, sticky="e", padx=(8, 8))

    clear_btn = ctk.CTkButton(
        dup_log_hdr,
        text="🗑️ Clear",
        command=gui_instance.clear_dup_log,
        font=ctk.CTkFont(size=10),
        width=60,
        height=22,
        corner_radius=6,
        fg_color=GLASS["bg_hover"] if HAS_THEME else ("gray75", "gray25"),
        text_color=GLASS["text_primary"] if HAS_THEME else ("gray10", "gray90")
    )
    clear_btn.grid(row=0, column=2, sticky="e")

    gui_instance.dup_log_textbox = ctk.CTkTextbox(
        gui_instance.dup_log_card,
        height=110,
        font=ctk.CTkFont(family="Consolas", size=10),
        corner_radius=8
    )
    gui_instance.dup_log_textbox.pack(fill="both", expand=True, padx=10, pady=(2, 6))

    try:
        tb = gui_instance.dup_log_textbox._textbox
        tb.tag_config("header", foreground="#64b5f6", font=("Consolas", 10, "bold"))
        tb.tag_config("success", foreground="#81c784")
        tb.tag_config("error", foreground="#e57373")
        tb.tag_config("warning", foreground="#ffb74d")
        tb.tag_config("info", foreground="#e0e0e0")
    except Exception:
        pass
