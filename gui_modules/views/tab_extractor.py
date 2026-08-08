import os
import tkinter as tk
from tkinter import filedialog, ttk
from gui_modules.components import CTkToolTip, create_info_icon, GRANULAR_FILE_TYPES

try:
    import customtkinter as ctk
    HAS_CUSTOMTKINTER = True
except ImportError:
    HAS_CUSTOMTKINTER = False


def setup_extractor_tab(gui_instance):
    scroll = ctk.CTkScrollableFrame(gui_instance.tab_extractor, fg_color="transparent")
    scroll.pack(fill="both", expand=True)
    scroll.grid_columnconfigure(0, weight=1)
    gui_instance.extractor_scroll = scroll

    ext_preset_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray90", "gray17"))
    ext_preset_card.grid(row=0, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=4)
    ctk.CTkLabel(ext_preset_card, text="⚡ Extraction Presets:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(12, 4))
    create_info_icon(ext_preset_card, "Extract specific file types (e.g. ONLY PDFs or EXCEPT Media) out of subfolders into a single output directory!").pack(side="left", padx=(0, 6))

    btn_only_pdf = ctk.CTkButton(ext_preset_card, text="📄 ONLY PDFs (.pdf)", command=gui_instance.preset_only_pdf, font=ctk.CTkFont(size=11, weight="bold"), height=26, fg_color="#c62828")
    btn_only_pdf.pack(side="left", padx=3)

    btn_only_office = ctk.CTkButton(ext_preset_card, text="📝 ONLY Office Docs", command=gui_instance.preset_only_office_docs, font=ctk.CTkFont(size=11, weight="bold"), height=26, fg_color="#2e7d32")
    btn_only_office.pack(side="left", padx=3)

    btn_only_media = ctk.CTkButton(ext_preset_card, text="🖼️ ONLY Photos & Videos", command=gui_instance.preset_only_media, font=ctk.CTkFont(size=11, weight="bold"), height=26, fg_color="#0288d1")
    btn_only_media.pack(side="left", padx=3)

    btn_exc1 = ctk.CTkButton(ext_preset_card, text="🚫 Except Photos & Videos", command=gui_instance.preset_except_media, font=ctk.CTkFont(size=11, weight="bold"), height=26, fg_color="#6a1b9a")
    btn_exc1.pack(side="left", padx=3)

    ctk.CTkButton(ext_preset_card, text="🧹 Clear All", command=gui_instance.preset_clear_extractor_checkboxes, font=ctk.CTkFont(size=10), height=26, width=65, fg_color=("gray75", "gray30"), text_color=("gray10", "gray90")).pack(side="left", padx=3)

    # Directories Card WITH DUAL FILE & FOLDER PICKER!
    ext_dir_card = ctk.CTkFrame(scroll, corner_radius=12)
    ext_dir_card.grid(row=1, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    ext_dir_card.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(ext_dir_card, text="1. Target Folders to Extract From", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(6, 4))

    ctk.CTkLabel(ext_dir_card, text="Source:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.ext_src_var = tk.StringVar()
    gui_instance.ext_src_entry = ctk.CTkEntry(ext_dir_card, textvariable=gui_instance.ext_src_var, placeholder_text="Select source folder or pick specific files...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.ext_src_entry.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)

    ext_btn_box = ctk.CTkFrame(ext_dir_card, fg_color="transparent")
    ext_btn_box.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=4)

    ctk.CTkButton(ext_btn_box, text="📁 Pick Folder...", command=gui_instance.browse_ext_src, font=ctk.CTkFont(size=10, weight="bold"), height=32, width=95).pack(side="left", padx=(0, 3))
    ctk.CTkButton(ext_btn_box, text="📁+ Multi Folders...", command=lambda: gui_instance.browse_multiple_folders(gui_instance.ext_src_var, gui_instance.refresh_extractor_preview), font=ctk.CTkFont(size=10, weight="bold"), fg_color="#1565c0", height=32, width=110).pack(side="left", padx=(0, 3))
    ctk.CTkButton(ext_btn_box, text="📄 Pick Files...", command=gui_instance.browse_ext_individual_files, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#00838f", height=32, width=90).pack(side="left")

    # Dedicated Exclusions Row
    ctk.CTkLabel(ext_dir_card, text="Exclusions (Opt):", font=ctk.CTkFont(size=11, weight="bold"), text_color="#ef5350").grid(row=2, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.ext_exc_entry = ctk.CTkEntry(ext_dir_card, textvariable=gui_instance.exclude_folders_var, placeholder_text="Folders/Subfolders to SKIP...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.ext_exc_entry.grid(row=2, column=1, sticky="ew", padx=(0, 6), pady=4)

    ext_exc_btn_box = ctk.CTkFrame(ext_dir_card, fg_color="transparent")
    ext_exc_btn_box.grid(row=2, column=2, sticky="e", padx=(0, 12), pady=4)

    ctk.CTkButton(ext_exc_btn_box, text="🚫 Except Folder...", command=gui_instance.add_exclude_folder_picker, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#c62828", height=32, width=105).pack(side="left", padx=(0, 3))
    ctk.CTkButton(ext_exc_btn_box, text="🚫 Except Files...", command=gui_instance.add_exclude_file_picker, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#ad1457", height=32, width=95).pack(side="left", padx=(0, 3))
    ctk.CTkButton(ext_exc_btn_box, text="🧹 Clear", command=lambda: gui_instance.exclude_folders_var.set(""), font=ctk.CTkFont(size=10), height=32, width=55, fg_color=("gray75", "gray30"), text_color=("gray10", "gray90")).pack(side="left")

    ctk.CTkLabel(ext_dir_card, text="Output Directory:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=3, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.ext_dest_var = tk.StringVar()
    gui_instance.ext_dest_entry = ctk.CTkEntry(ext_dir_card, textvariable=gui_instance.ext_dest_var, placeholder_text="Optional destination folder for extracted files...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.ext_dest_entry.grid(row=3, column=1, sticky="ew", padx=(0, 6), pady=4)

    ctk.CTkButton(ext_dir_card, text="Browse...", command=gui_instance.browse_ext_dest, font=ctk.CTkFont(size=11), height=32, width=95).grid(row=3, column=2, sticky="e", padx=(0, 12), pady=4)

    # Strategy & Filter Card
    ext_strat_card = ctk.CTkFrame(scroll, corner_radius=12)
    ext_strat_card.grid(row=2, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    ext_strat_card.grid_columnconfigure(1, weight=1)
    ext_strat_card.grid_columnconfigure(3, weight=1)

    ctk.CTkLabel(ext_strat_card, text="2. Filter Strategy & Specific File Type Multi-Selector", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(6, 4))

    ctk.CTkLabel(ext_strat_card, text="Filter Mode:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.ext_filter_mode_var = ctk.StringVar(value="🎯 INCLUDE ONLY Selected File Types (Rest Untouched)")
    gui_instance.ext_filter_dropdown = ctk.CTkOptionMenu(
        ext_strat_card,
        variable=gui_instance.ext_filter_mode_var,
        values=[
            "🎯 INCLUDE ONLY Selected File Types (Rest Untouched)",
            "🚫 EXCLUDE (Except) Selected File Types",
            "🏷️ Specific Custom Extensions List"
        ],
        command=gui_instance.on_extractor_filter_mode_changed,
        font=ctk.CTkFont(size=11),
        dropdown_font=ctk.CTkFont(size=11),
        height=32
    )
    gui_instance.ext_filter_dropdown.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=4)

    ctk.CTkLabel(ext_strat_card, text="Output Structure:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=2, sticky="w", padx=(6, 6), pady=4)

    gui_instance.ext_output_struct_var = ctk.StringVar(value="Flatten into Single Folder")
    gui_instance.ext_struct_dropdown = ctk.CTkOptionMenu(
        ext_strat_card,
        variable=gui_instance.ext_output_struct_var,
        values=[
            "Flatten into Single Folder",
            "Organize into Category Folders",
            "Organize into Extension Folders"
        ],
        font=ctk.CTkFont(size=11),
        dropdown_font=ctk.CTkFont(size=11),
        height=32
    )
    gui_instance.ext_struct_dropdown.grid(row=1, column=3, sticky="ew", padx=(0, 12), pady=4)

    ctk.CTkLabel(ext_strat_card, text="Tick File Types:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=0, sticky="nw", padx=(12, 6), pady=4)

    cats_outer = ctk.CTkFrame(ext_strat_card, fg_color="transparent")
    cats_outer.grid(row=2, column=1, columnspan=3, sticky="ew", padx=(0, 12), pady=4)
    cats_outer.grid_columnconfigure(0, weight=1)
    cats_outer.grid_columnconfigure(1, weight=1)

    gui_instance.granular_checkbox_vars = {}
    gui_instance.ext_sub_vars = {}
    gui_instance._cat_sub_frames = {}

    sel_toolbar = ctk.CTkFrame(cats_outer, fg_color="transparent")
    sel_toolbar.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
    ctk.CTkLabel(sel_toolbar, text="Quick:", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray60").pack(side="left", padx=(0, 6))
    ctk.CTkButton(sel_toolbar, text="☑ Select All Categories", command=gui_instance.extractor_select_all_cats,
        font=ctk.CTkFont(size=10), height=22, width=145, fg_color="#0288d1").pack(side="left", padx=(0, 4))
    ctk.CTkButton(sel_toolbar, text="☐ Clear All", command=gui_instance.extractor_clear_all_cats,
        font=ctk.CTkFont(size=10), height=22, width=80,
        fg_color=("gray72", "gray32"), text_color=("gray10", "gray90")).pack(side="left", padx=(0, 4))
    ctk.CTkButton(sel_toolbar, text="⇄ Invert", command=gui_instance.extractor_invert_cats,
        font=ctk.CTkFont(size=10), height=22, width=65,
        fg_color=("gray72", "gray32"), text_color=("gray10", "gray90")).pack(side="left")

    cat_row = 1
    cat_col = 0
    for type_label, exts in GRANULAR_FILE_TYPES.items():
        cat_var = tk.BooleanVar(value=False)
        gui_instance.granular_checkbox_vars[type_label] = cat_var

        cat_card = ctk.CTkFrame(cats_outer, corner_radius=8, fg_color=("gray85", "gray25"))
        cat_card.grid(row=cat_row, column=cat_col, sticky="ew", padx=4, pady=3, ipadx=2, ipady=2)

        hdr = ctk.CTkFrame(cat_card, fg_color="transparent")
        hdr.pack(fill="x", padx=6, pady=(4, 2))

        master_chk = ctk.CTkCheckBox(
            hdr, text=type_label, variable=cat_var,
            font=ctk.CTkFont(size=10, weight="bold"),
            checkbox_width=18, checkbox_height=18,
            command=lambda lbl=type_label: gui_instance._sync_sub_from_cat(lbl)
        )
        master_chk.pack(side="left", fill="x", expand=True)
        cat_var.trace_add("write", lambda *a: gui_instance.refresh_extractor_preview())

        expand_var = tk.BooleanVar(value=False)
        expand_btn = ctk.CTkButton(
            hdr, text="▶ Exts", width=55, height=20,
            font=ctk.CTkFont(size=9),
            fg_color=("gray75", "gray35"),
            text_color=("gray20", "gray80")
        )
        expand_btn.pack(side="right", padx=(4, 0))

        sub_frame = ctk.CTkFrame(cat_card, fg_color=("gray90", "gray18"), corner_radius=6)
        gui_instance._cat_sub_frames[type_label] = sub_frame

        sub_lbl_row = ctk.CTkFrame(sub_frame, fg_color="transparent")
        sub_lbl_row.pack(fill="x", padx=4, pady=(3, 0))
        ctk.CTkLabel(sub_lbl_row, text="Extensions:", font=ctk.CTkFont(size=9, weight="bold"), text_color="gray60").pack(side="left")
        ctk.CTkButton(sub_lbl_row, text="All", width=28, height=16, font=ctk.CTkFont(size=9),
            command=lambda lbl=type_label: gui_instance._sub_select_all(lbl),
            fg_color="#0288d1").pack(side="right", padx=1)
        ctk.CTkButton(sub_lbl_row, text="None", width=32, height=16, font=ctk.CTkFont(size=9),
            command=lambda lbl=type_label: gui_instance._sub_select_none(lbl),
            fg_color=("gray72","gray32"), text_color=("gray10","gray80")).pack(side="right", padx=1)

        sub_chk_frame = ctk.CTkFrame(sub_frame, fg_color="transparent")
        sub_chk_frame.pack(fill="x", padx=4, pady=(2, 4))

        sub_col = 0
        sub_r = 0
        for ext in exts:
            if ext not in gui_instance.ext_sub_vars:
                gui_instance.ext_sub_vars[ext] = tk.BooleanVar(value=False)
            sv = gui_instance.ext_sub_vars[ext]
            sv.trace_add("write", lambda *a, lbl=type_label: gui_instance._sync_cat_from_subs(lbl))
            sv.trace_add("write", lambda *a: gui_instance.refresh_extractor_preview())
            ctk.CTkCheckBox(
                sub_chk_frame, text=ext, variable=sv,
                font=ctk.CTkFont(size=9), width=60, checkbox_width=14, checkbox_height=14
            ).grid(row=sub_r, column=sub_col, sticky="w", padx=4, pady=1)
            sub_col += 1
            if sub_col > 2:
                sub_col = 0
                sub_r += 1

        def _toggle_expand(btn=expand_btn, sf=sub_frame, ev=expand_var):
            if ev.get():
                sf.pack_forget()
                btn.configure(text="▶ Exts")
                ev.set(False)
            else:
                sf.pack(fill="x", padx=4, pady=(0, 4))
                btn.configure(text="▼ Exts")
                ev.set(True)
        expand_btn.configure(command=_toggle_expand)

        cat_col += 1
        if cat_col > 1:
            cat_col = 0
            cat_row += 1

    ctk.CTkLabel(ext_strat_card, text="Custom Exts:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=3, column=0, sticky="w", padx=(12, 6), pady=4)

    custom_ext_frame = ctk.CTkFrame(ext_strat_card, fg_color="transparent")
    custom_ext_frame.grid(row=3, column=1, columnspan=3, sticky="ew", padx=(0, 12), pady=4)
    custom_ext_frame.grid_columnconfigure(0, weight=1)

    gui_instance.ext_custom_exts_var = tk.StringVar()
    gui_instance.ext_custom_exts_var.trace_add("write", lambda *args: gui_instance.refresh_extractor_preview())
    gui_instance.ext_custom_entry = ctk.CTkEntry(
        custom_ext_frame,
        textvariable=gui_instance.ext_custom_exts_var,
        placeholder_text="Type custom exts (e.g. .psd, .blend, .epub) or click Auto-Detect ↗",
        font=ctk.CTkFont(size=11),
        height=28
    )
    gui_instance.ext_custom_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

    btn_detect_exts = ctk.CTkButton(
        custom_ext_frame,
        text="🔍 Detect All Exts in Folder...",
        command=gui_instance.open_custom_ext_detector,
        font=ctk.CTkFont(size=10, weight="bold"),
        fg_color="#0288d1",
        hover_color="#0277bd",
        height=28,
        width=175
    )
    btn_detect_exts.grid(row=0, column=1, sticky="e")
    CTkToolTip(btn_detect_exts, "Scans the source folder for ALL unique file extensions present\n(including custom formats like .psd, .blend, .sketch, .epub) and lets you pick them!")

    ctk.CTkLabel(ext_strat_card, text="Action Mode:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=4, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.ext_action_mode = ctk.CTkSegmentedButton(ext_strat_card, values=["Move", "Copy"], font=ctk.CTkFont(size=11, weight="bold"), height=30)
    gui_instance.ext_action_mode.set("Move")
    gui_instance.ext_action_mode.grid(row=4, column=1, sticky="w", padx=(0, 10), pady=4)

    ctk.CTkLabel(ext_strat_card, text="Conflicts:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=4, column=2, sticky="w", padx=(6, 6), pady=4)

    gui_instance.ext_conflict_mode_var = ctk.StringVar(value="🛡️ Skip Conflicts (Default)")
    gui_instance.ext_conflict_dropdown = ctk.CTkOptionMenu(
        ext_strat_card,
        variable=gui_instance.ext_conflict_mode_var,
        values=[
            "🛡️ Skip Conflicts (Default)",
            "🔍 Interactive Windows 11 Resolver",
            "🔢 Keep Both (Auto-number)",
            "♻️ Replace Target File"
        ],
        font=ctk.CTkFont(size=11),
        dropdown_font=ctk.CTkFont(size=11),
        height=30
    )
    gui_instance.ext_conflict_dropdown.grid(row=4, column=3, sticky="ew", padx=(0, 12), pady=4)

    ext_chk_box = ctk.CTkFrame(ext_strat_card, fg_color="transparent")
    ext_chk_box.grid(row=5, column=0, columnspan=4, sticky="w", padx=12, pady=(4, 6))

    chk_ext_zip = ctk.CTkCheckBox(
        ext_chk_box,
        text="📦 System Vault Zip Backup (Optional ZIP Archive — Unchecked for Cloud/OneDrive)",
        variable=gui_instance.enable_zip_backup_var,
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color="#0288d1"
    )
    chk_ext_zip.pack(side="left", padx=(0, 15))

    gui_instance.ext_clean_empty_var = tk.BooleanVar(value=True)
    chk_ext_clean = ctk.CTkCheckBox(
        ext_chk_box,
        text="🧹 Clean Leftover Empty Folders (Delete empty subfolders & OS junk)",
        variable=gui_instance.ext_clean_empty_var,
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color="#ff9800"
    )
    chk_ext_clean.pack(side="left")

    ext_skip_row = ctk.CTkFrame(ext_strat_card, fg_color="transparent")
    ext_skip_row.grid(row=6, column=0, columnspan=4, sticky="w", padx=12, pady=(2, 6))

    ctk.CTkLabel(ext_skip_row, text="Skipped Files Handling:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 6))

    gui_instance.ext_skipped_dropdown = ctk.CTkOptionMenu(
        ext_skip_row,
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
    gui_instance.ext_skipped_dropdown.pack(side="left", padx=(0, 8))
    CTkToolTip(gui_instance.ext_skipped_dropdown, "Controls what happens to files that are NOT extracted or skipped:\n• Leave in Original Location: Untouched files stay right where they are.\n• Move Skipped Files: Gathers all unextracted/skipped files into a '_Skipped_Files' folder.")

    ext_preview_card = ctk.CTkFrame(scroll, corner_radius=12)
    ext_preview_card.grid(row=3, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=6)
    ext_preview_card.grid_columnconfigure(0, weight=1)

    ext_preview_hdr = ctk.CTkFrame(ext_preview_card, fg_color="transparent")
    ext_preview_hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(6, 4))
    ext_preview_hdr.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(ext_preview_hdr, text="3. Extraction Preview Map", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).grid(row=0, column=0, sticky="w")

    gui_instance.ext_preview_stats_lbl = ctk.CTkLabel(ext_preview_hdr, text="Matching Files: 0 | Total Size: 0 B", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray60")
    gui_instance.ext_preview_stats_lbl.grid(row=0, column=1, sticky="e", padx=(0, 8))

    ctk.CTkButton(ext_preview_hdr, text="🔍 Scan Extractor Map", command=gui_instance.refresh_extractor_preview, font=ctk.CTkFont(size=11, weight="bold"), height=28, width=150, fg_color="#0288d1").grid(row=0, column=2, sticky="e")

    tree_frame = ctk.CTkFrame(ext_preview_card, corner_radius=8, fg_color=("gray95", "gray15"))
    tree_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))
    tree_frame.grid_columnconfigure(0, weight=1)

    columns = ("filename", "rel_src", "rel_target", "category", "size_str", "status")
    gui_instance.ext_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=5)
    gui_instance.ext_tree.heading("filename", text="File Name", command=lambda: gui_instance._sort_tree(gui_instance.ext_tree, "filename"))
    gui_instance.ext_tree.heading("rel_src", text="Subfolder Source Path", command=lambda: gui_instance._sort_tree(gui_instance.ext_tree, "rel_src"))
    gui_instance.ext_tree.heading("rel_target", text="Target Path", command=lambda: gui_instance._sort_tree(gui_instance.ext_tree, "rel_target"))
    gui_instance.ext_tree.heading("category", text="Category", command=lambda: gui_instance._sort_tree(gui_instance.ext_tree, "category"))
    gui_instance.ext_tree.heading("size_str", text="Size", command=lambda: gui_instance._sort_tree(gui_instance.ext_tree, "size_str"))
    gui_instance.ext_tree.heading("status", text="Status", command=lambda: gui_instance._sort_tree(gui_instance.ext_tree, "status"))

    gui_instance.ext_tree.column("filename", width=180)
    gui_instance.ext_tree.column("rel_src", width=220)
    gui_instance.ext_tree.column("rel_target", width=200)
    gui_instance.ext_tree.column("category", width=110)
    gui_instance.ext_tree.column("size_str", width=90)
    gui_instance.ext_tree.column("status", width=120)

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=gui_instance.ext_tree.yview)
    gui_instance.ext_tree.configure(yscrollcommand=scrollbar.set)
    gui_instance.ext_tree.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
    scrollbar.grid(row=0, column=1, sticky="ns", pady=4)

    ext_action_card = ctk.CTkFrame(scroll, fg_color="transparent")
    ext_action_card.grid(row=5, column=0, sticky="ew", pady=(0, 8))
    ext_action_card.grid_columnconfigure(4, weight=1)

    gui_instance.ext_start_btn = ctk.CTkButton(
        ext_action_card,
        text="⚡ Start Extraction",
        command=gui_instance.start_extractor,
        font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        fg_color="#1b5e20",
        hover_color="#2e7d32",
        height=36,
        width=150
    )
    gui_instance.ext_start_btn.grid(row=0, column=0, padx=(0, 6), sticky="w")

    btn_ext_del_empty = ctk.CTkButton(
        ext_action_card,
        text="🧹 Delete Empty Folders",
        command=lambda: gui_instance.run_delete_empty_folders(gui_instance.ext_src_var.get().strip()),
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        fg_color="#e65100",
        hover_color="#f57c00",
        height=36,
        width=175
    )
    btn_ext_del_empty.grid(row=0, column=1, padx=(0, 6), sticky="w")

    gui_instance.ext_undo_btn = ctk.CTkButton(
        ext_action_card,
        text="🛡️ System Vault Restore",
        command=gui_instance.open_system_vault_restore_manager,
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        fg_color="#c62828",
        hover_color="#d32f2f",
        height=36,
        width=175
    )
    gui_instance.ext_undo_btn.grid(row=0, column=2, padx=(0, 6), sticky="w")

    ctk.CTkButton(
        ext_action_card,
        text="🧹 Clear Log",
        command=gui_instance.clear_log,
        font=ctk.CTkFont(family="Segoe UI", size=12),
        fg_color=("gray75", "gray30"),
        text_color=("gray10", "gray90"),
        height=36,
        width=90
    ).grid(row=0, column=3, padx=(0, 10), sticky="w")

    gui_instance.ext_progress_bar = ctk.CTkProgressBar(ext_action_card, height=12)
    gui_instance.ext_progress_bar.set(0)
    gui_instance.ext_progress_bar.grid(row=0, column=4, sticky="ew")
