import tkinter as tk
from tkinter import ttk
from gui_modules.components import create_info_icon

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


def setup_cleaner_tab(gui_instance):
    scroll = ctk.CTkScrollableFrame(gui_instance.tab_cleaner, fg_color="transparent")
    scroll.pack(fill="both", expand=True)
    scroll.grid_columnconfigure(0, weight=1)
    gui_instance.cleaner_scroll = scroll

    cln_hdr_card = ctk.CTkFrame(scroll, corner_radius=16)
    cln_hdr_card.grid(row=0, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    cln_hdr_card.grid_columnconfigure(1, weight=1)

    hdr_c = ctk.CTkFrame(cln_hdr_card, fg_color="transparent")
    hdr_c.grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(6, 4))
    ctk.CTkLabel(hdr_c, text="🧹 Storage Analyzer & Junk File Cleaner", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).pack(side="left")
    create_info_icon(hdr_c, "Scans for 0-byte empty files, temporary junk (.tmp, .log, .bak, Thumbs.db), and ranks Top 100 Largest Files!").pack(side="left", padx=6)

    ctk.CTkLabel(cln_hdr_card, text="Scan Folder:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.cln_dir_var = tk.StringVar()
    gui_instance.cln_dir_entry = ctk.CTkEntry(cln_hdr_card, textvariable=gui_instance.cln_dir_var, placeholder_text="Select directory to analyze for junk and large files...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.cln_dir_entry.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)

    cln_btn_box = ctk.CTkFrame(cln_hdr_card, fg_color="transparent")
    cln_btn_box.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=4)

    ctk.CTkButton(cln_btn_box, text="📁 Pick Folder...", command=gui_instance.browse_cln_folder, font=ctk.CTkFont(size=10, weight="bold"), height=32, width=95).pack(side="left", padx=(0, 3))
    ctk.CTkButton(cln_btn_box, text="📁+ Multi Folders...", command=lambda: gui_instance.browse_multiple_folders(gui_instance.cln_dir_var, gui_instance.run_cleaner_scan), font=ctk.CTkFont(size=10, weight="bold"), fg_color="#1565c0", height=32, width=110).pack(side="left", padx=(0, 3))
    ctk.CTkButton(cln_btn_box, text="📄 Pick Files...", command=gui_instance.browse_cln_files, font=ctk.CTkFont(size=10, weight="bold"), fg_color=("#32ADE6", "#64D2FF") if HAS_THEME else "#00838f", height=32, width=90).pack(side="left", padx=(0, 3))

    ctk.CTkButton(
        cln_btn_box,
        text="🔍 Scan Storage",
        command=gui_instance.run_cleaner_scan,
        font=ctk.CTkFont(size=11, weight="bold"),
        fg_color=("#007AFF", "#0A84FF") if HAS_THEME else "#0288d1",
        height=32,
        width=120
    ).pack(side="left")

    # Dedicated Exclusions Row
    ctk.CTkLabel(cln_hdr_card, text="Exclusions (Opt):", font=ctk.CTkFont(size=11, weight="bold"), text_color="#ef5350").grid(row=2, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.cln_exc_entry = ctk.CTkEntry(cln_hdr_card, textvariable=gui_instance.exclude_folders_var, placeholder_text="Folders/Subfolders to SKIP...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.cln_exc_entry.grid(row=2, column=1, sticky="ew", padx=(0, 6), pady=4)

    cln_exc_btn_box = ctk.CTkFrame(cln_hdr_card, fg_color="transparent")
    cln_exc_btn_box.grid(row=2, column=2, sticky="e", padx=(0, 12), pady=4)

    ctk.CTkButton(cln_exc_btn_box, text="🚫 Except Folder...", command=gui_instance.add_exclude_folder_picker, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#c62828", height=32, width=105).pack(side="left", padx=(0, 3))
    ctk.CTkButton(cln_exc_btn_box, text="🚫 Except Files...", command=gui_instance.add_exclude_file_picker, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#ad1457", height=32, width=95).pack(side="left", padx=(0, 3))
    ctk.CTkButton(cln_exc_btn_box, text="🧹 Clear", command=lambda: gui_instance.exclude_folders_var.set(""), font=ctk.CTkFont(size=10), height=32, width=55, fg_color=("gray75", "gray30"), text_color=("gray10", "gray90")).pack(side="left")

    clean_tabview = ctk.CTkTabview(scroll, corner_radius=10, height=420)
    clean_tabview.grid(row=1, column=0, sticky="ew", pady=(0, 8))

    tab_junk = clean_tabview.add("🗑️ Temp & Junk Files")
    tab_empty = clean_tabview.add("📂 Empty Folders Cleaner")
    tab_large = clean_tabview.add("⚖️ Top 100 Largest Files")

    # ---- JUNK FILES TAB ----
    junk_toolbar = ctk.CTkFrame(tab_junk, corner_radius=8, fg_color=("gray88", "gray22"))
    junk_toolbar.pack(fill="x", padx=4, pady=(4, 0))

    ctk.CTkLabel(junk_toolbar, text="Select:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(10, 6), pady=5)

    ctk.CTkButton(
        junk_toolbar, text="☑ All", command=gui_instance.junk_select_all,
        font=ctk.CTkFont(size=10, weight="bold"), height=24, width=55,
        fg_color=("#007AFF", "#0A84FF") if HAS_THEME else "#0288d1", hover_color="#0277bd"
    ).pack(side="left", padx=2, pady=5)

    ctk.CTkButton(
        junk_toolbar, text="☐ None", command=gui_instance.junk_select_none,
        font=ctk.CTkFont(size=10), height=24, width=60,
        fg_color=("gray75", "gray35"), text_color=("gray10", "gray90")
    ).pack(side="left", padx=2, pady=5)

    ctk.CTkButton(
        junk_toolbar, text="⇄ Invert", command=gui_instance.junk_select_invert,
        font=ctk.CTkFont(size=10), height=24, width=65,
        fg_color=("gray75", "gray35"), text_color=("gray10", "gray90")
    ).pack(side="left", padx=2, pady=5)

    ctk.CTkLabel(junk_toolbar, text="|", font=ctk.CTkFont(size=12), text_color="gray50").pack(side="left", padx=6, pady=5)
    ctk.CTkLabel(junk_toolbar, text="Filter by type:", font=ctk.CTkFont(size=10), text_color="gray60").pack(side="left", padx=(0, 4), pady=5)

    ctk.CTkButton(
        junk_toolbar, text="🗂️ .tmp/.log", command=lambda: gui_instance.junk_select_by_reason("Temp"),
        font=ctk.CTkFont(size=10), height=24, width=80,
        fg_color=("#FF9500", "#FF9F0A") if HAS_THEME else "#f57c00", hover_color="#ef6c00"
    ).pack(side="left", padx=2, pady=5)

    ctk.CTkButton(
        junk_toolbar, text="📄 0-Byte Files", command=lambda: gui_instance.junk_select_by_reason("0-Byte"),
        font=ctk.CTkFont(size=10), height=24, width=90,
        fg_color="#6a1b9a", hover_color="#7b1fa2"
    ).pack(side="left", padx=2, pady=5)

    ctk.CTkButton(
        junk_toolbar, text="💾 .crdownload/.part", command=lambda: gui_instance.junk_select_by_reason("crdownload"),
        font=ctk.CTkFont(size=10), height=24, width=110,
        fg_color="#37474f", hover_color="#455a64"
    ).pack(side="left", padx=2, pady=5)

    gui_instance.junk_sel_lbl = ctk.CTkLabel(
        junk_toolbar,
        text="Selected: 0 of 0 files (0 B)",
        font=ctk.CTkFont(size=10, weight="bold"),
        text_color=("#0288d1", "#64b5f6")
    )
    gui_instance.junk_sel_lbl.pack(side="right", padx=10, pady=5)

    tree_junk_frame = ctk.CTkFrame(tab_junk, fg_color="transparent")
    tree_junk_frame.pack(fill="both", expand=True, padx=4, pady=(2, 4))
    tree_junk_frame.grid_columnconfigure(0, weight=1)
    tree_junk_frame.grid_rowconfigure(0, weight=1)

    cols_j = ("filename", "rel_path", "reason", "size_str", "mtime_str")
    gui_instance.junk_tree = ttk.Treeview(tree_junk_frame, columns=cols_j, show="headings", height=8, selectmode="extended")
    gui_instance.junk_tree.heading("filename", text="Junk File Name", command=lambda: gui_instance._sort_tree(gui_instance.junk_tree, "filename"))
    gui_instance.junk_tree.heading("rel_path", text="Subfolder Location", command=lambda: gui_instance._sort_tree(gui_instance.junk_tree, "rel_path"))
    gui_instance.junk_tree.heading("reason", text="Junk Reason", command=lambda: gui_instance._sort_tree(gui_instance.junk_tree, "reason"))
    gui_instance.junk_tree.heading("size_str", text="Size", command=lambda: gui_instance._sort_tree(gui_instance.junk_tree, "size_str"))
    gui_instance.junk_tree.heading("mtime_str", text="Modified Date", command=lambda: gui_instance._sort_tree(gui_instance.junk_tree, "mtime_str"))

    gui_instance.junk_tree.column("filename", width=200, minwidth=100)
    gui_instance.junk_tree.column("rel_path", width=250, minwidth=100)
    gui_instance.junk_tree.column("reason", width=150, minwidth=80)
    gui_instance.junk_tree.column("size_str", width=90, minwidth=60)
    gui_instance.junk_tree.column("mtime_str", width=140, minwidth=100)

    gui_instance.junk_tree.bind("<<TreeviewSelect>>", gui_instance._on_junk_select)

    sb_j = ttk.Scrollbar(tree_junk_frame, orient="vertical", command=gui_instance.junk_tree.yview)
    gui_instance.junk_tree.configure(yscrollcommand=sb_j.set)
    gui_instance.junk_tree.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
    sb_j.grid(row=0, column=1, sticky="ns", pady=4)

    # ---- EMPTY FOLDERS CLEANER TAB ----
    empty_toolbar = ctk.CTkFrame(tab_empty, corner_radius=8, fg_color=("gray88", "gray22"))
    empty_toolbar.pack(fill="x", padx=4, pady=(4, 0))

    ctk.CTkLabel(empty_toolbar, text="Select:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(10, 6), pady=5)

    ctk.CTkButton(
        empty_toolbar, text="☑ All", command=gui_instance.empty_select_all,
        font=ctk.CTkFont(size=10, weight="bold"), height=24, width=55,
        fg_color=("#007AFF", "#0A84FF") if HAS_THEME else "#0288d1", hover_color="#0277bd"
    ).pack(side="left", padx=2, pady=5)

    ctk.CTkButton(
        empty_toolbar, text="☐ None", command=gui_instance.empty_select_none,
        font=ctk.CTkFont(size=10), height=24, width=60,
        fg_color=("gray75", "gray35"), text_color=("gray10", "gray90")
    ).pack(side="left", padx=2, pady=5)

    ctk.CTkButton(
        empty_toolbar, text="⇄ Invert", command=gui_instance.empty_select_invert,
        font=ctk.CTkFont(size=10), height=24, width=65,
        fg_color=("gray75", "gray35"), text_color=("gray10", "gray90")
    ).pack(side="left", padx=2, pady=5)

    ctk.CTkLabel(empty_toolbar, text="|", font=ctk.CTkFont(size=12), text_color="gray50").pack(side="left", padx=6, pady=5)

    gui_instance.empty_remove_os_junk_var = tk.BooleanVar(value=True)
    chk_os_junk = ctk.CTkCheckBox(
        empty_toolbar,
        text="🧹 Clean OS Junk (desktop.ini, thumbs.db)",
        variable=gui_instance.empty_remove_os_junk_var,
        font=ctk.CTkFont(size=10, weight="bold"),
        text_color="#ff9800"
    )
    chk_os_junk.pack(side="left", padx=4, pady=5)

    ctk.CTkButton(
        empty_toolbar, text="🔍 Scan Empty Folders", command=gui_instance.run_empty_folder_scan,
        font=ctk.CTkFont(size=10, weight="bold"), height=24, width=135,
        fg_color=("#007AFF", "#0A84FF") if HAS_THEME else "#0288d1", hover_color="#0277bd"
    ).pack(side="left", padx=3, pady=5)

    ctk.CTkButton(
        empty_toolbar, text="🗑️ Delete Selected", command=gui_instance.delete_selected_empty_folders,
        font=ctk.CTkFont(size=10, weight="bold"), height=24, width=115,
        fg_color=("#FF3B30", "#FF453A") if HAS_THEME else "#d32f2f", hover_color="#b71c1c"
    ).pack(side="left", padx=2, pady=5)

    ctk.CTkButton(
        empty_toolbar, text="🧹 Delete ALL Empty", command=gui_instance.delete_all_empty_folders,
        font=ctk.CTkFont(size=10, weight="bold"), height=24, width=125,
        fg_color="#c62828", hover_color="#8e0000"
    ).pack(side="left", padx=2, pady=5)

    gui_instance.empty_sel_lbl = ctk.CTkLabel(
        empty_toolbar,
        text="Detected: 0 empty folder(s)",
        font=ctk.CTkFont(size=10, weight="bold"),
        text_color=("#0288d1", "#64b5f6")
    )
    gui_instance.empty_sel_lbl.pack(side="right", padx=10, pady=5)

    tree_empty_frame = ctk.CTkFrame(tab_empty, fg_color="transparent")
    tree_empty_frame.pack(fill="both", expand=True, padx=4, pady=(2, 4))
    tree_empty_frame.grid_columnconfigure(0, weight=1)
    tree_empty_frame.grid_rowconfigure(0, weight=1)

    cols_e = ("folder_name", "rel_path", "reason", "full_path")
    gui_instance.empty_tree = ttk.Treeview(tree_empty_frame, columns=cols_e, show="headings", height=8, selectmode="extended")
    gui_instance.empty_tree.heading("folder_name", text="Folder Name", command=lambda: gui_instance._sort_tree(gui_instance.empty_tree, "folder_name"))
    gui_instance.empty_tree.heading("rel_path", text="Relative Subfolder Path", command=lambda: gui_instance._sort_tree(gui_instance.empty_tree, "rel_path"))
    gui_instance.empty_tree.heading("reason", text="Empty Reason / Junk Status", command=lambda: gui_instance._sort_tree(gui_instance.empty_tree, "reason"))
    gui_instance.empty_tree.heading("full_path", text="Full Directory Path", command=lambda: gui_instance._sort_tree(gui_instance.empty_tree, "full_path"))

    gui_instance.empty_tree.column("folder_name", width=180, minwidth=100)
    gui_instance.empty_tree.column("rel_path", width=240, minwidth=120)
    gui_instance.empty_tree.column("reason", width=200, minwidth=100)
    gui_instance.empty_tree.column("full_path", width=280, minwidth=150)

    gui_instance.empty_tree.bind("<<TreeviewSelect>>", gui_instance._on_empty_select)

    sb_e = ttk.Scrollbar(tree_empty_frame, orient="vertical", command=gui_instance.empty_tree.yview)
    gui_instance.empty_tree.configure(yscrollcommand=sb_e.set)
    gui_instance.empty_tree.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
    sb_e.grid(row=0, column=1, sticky="ns", pady=4)

    # ---- LARGE FILES TAB ----
    large_toolbar = ctk.CTkFrame(tab_large, corner_radius=8, fg_color=("gray88", "gray22"))
    large_toolbar.pack(fill="x", padx=4, pady=(4, 0))

    ctk.CTkLabel(large_toolbar, text="Select:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(10, 6), pady=5)

    ctk.CTkButton(
        large_toolbar, text="☑ All", command=gui_instance.large_select_all,
        font=ctk.CTkFont(size=10, weight="bold"), height=24, width=55,
        fg_color=("#007AFF", "#0A84FF") if HAS_THEME else "#0288d1", hover_color="#0277bd"
    ).pack(side="left", padx=2, pady=5)

    ctk.CTkButton(
        large_toolbar, text="☐ None", command=gui_instance.large_select_none,
        font=ctk.CTkFont(size=10), height=24, width=60,
        fg_color=("gray75", "gray35"), text_color=("gray10", "gray90")
    ).pack(side="left", padx=2, pady=5)

    ctk.CTkButton(
        large_toolbar, text="⇄ Invert", command=gui_instance.large_select_invert,
        font=ctk.CTkFont(size=10), height=24, width=65,
        fg_color=("gray75", "gray35"), text_color=("gray10", "gray90")
    ).pack(side="left", padx=2, pady=5)

    ctk.CTkLabel(large_toolbar, text="|", font=ctk.CTkFont(size=12), text_color="gray50").pack(side="left", padx=6, pady=5)
    ctk.CTkLabel(large_toolbar, text="Filter by category:", font=ctk.CTkFont(size=10), text_color="gray60").pack(side="left", padx=(0, 4), pady=5)

    ctk.CTkButton(
        large_toolbar, text="🎬 Videos", command=lambda: gui_instance.large_select_by_category("Videos"),
        font=ctk.CTkFont(size=10), height=24, width=65,
        fg_color="#1565c0", hover_color="#1976d2"
    ).pack(side="left", padx=2, pady=5)

    ctk.CTkButton(
        large_toolbar, text="🖼️ Images", command=lambda: gui_instance.large_select_by_category("Images"),
        font=ctk.CTkFont(size=10), height=24, width=65,
        fg_color="#2e7d32", hover_color="#388e3c"
    ).pack(side="left", padx=2, pady=5)

    ctk.CTkButton(
        large_toolbar, text="📦 Archives", command=lambda: gui_instance.large_select_by_category("Archives"),
        font=ctk.CTkFont(size=10), height=24, width=70,
        fg_color="#6a1b9a", hover_color="#7b1fa2"
    ).pack(side="left", padx=2, pady=5)

    ctk.CTkButton(
        large_toolbar, text=">1 GB", command=lambda: gui_instance.large_select_above_size(1024 * 1024 * 1024),
        font=ctk.CTkFont(size=10, weight="bold"), height=24, width=55,
        fg_color="#c62828", hover_color="#d32f2f"
    ).pack(side="left", padx=2, pady=5)

    ctk.CTkButton(
        large_toolbar, text=">500 MB", command=lambda: gui_instance.large_select_above_size(500 * 1024 * 1024),
        font=ctk.CTkFont(size=10), height=24, width=65,
        fg_color="#e65100", hover_color="#f57c00"
    ).pack(side="left", padx=2, pady=5)

    gui_instance.large_sel_lbl = ctk.CTkLabel(
        large_toolbar,
        text="Selected: 0 of 0 files (0 B)",
        font=ctk.CTkFont(size=10, weight="bold"),
        text_color=("#0288d1", "#64b5f6")
    )
    gui_instance.large_sel_lbl.pack(side="right", padx=10, pady=5)

    tree_large_frame = ctk.CTkFrame(tab_large, fg_color="transparent")
    tree_large_frame.pack(fill="both", expand=True, padx=4, pady=(2, 4))
    tree_large_frame.grid_columnconfigure(0, weight=1)
    tree_large_frame.grid_rowconfigure(0, weight=1)

    cols_l = ("filename", "rel_path", "category", "size_str", "mtime_str")
    gui_instance.large_tree = ttk.Treeview(tree_large_frame, columns=cols_l, show="headings", height=8, selectmode="extended")
    gui_instance.large_tree.heading("filename", text="Large File Name", command=lambda: gui_instance._sort_tree(gui_instance.large_tree, "filename"))
    gui_instance.large_tree.heading("rel_path", text="Subfolder Location", command=lambda: gui_instance._sort_tree(gui_instance.large_tree, "rel_path"))
    gui_instance.large_tree.heading("category", text="Category", command=lambda: gui_instance._sort_tree(gui_instance.large_tree, "category"))
    gui_instance.large_tree.heading("size_str", text="Size ↓", command=lambda: gui_instance._sort_tree(gui_instance.large_tree, "size_str"))
    gui_instance.large_tree.heading("mtime_str", text="Modified Date", command=lambda: gui_instance._sort_tree(gui_instance.large_tree, "mtime_str"))

    gui_instance.large_tree.column("filename", width=200, minwidth=100)
    gui_instance.large_tree.column("rel_path", width=250, minwidth=100)
    gui_instance.large_tree.column("category", width=120, minwidth=60)
    gui_instance.large_tree.column("size_str", width=100, minwidth=60)
    gui_instance.large_tree.column("mtime_str", width=140, minwidth=100)

    gui_instance.large_tree.bind("<<TreeviewSelect>>", gui_instance._on_large_select)

    sb_l = ttk.Scrollbar(tree_large_frame, orient="vertical", command=gui_instance.large_tree.yview)
    gui_instance.large_tree.configure(yscrollcommand=sb_l.set)
    gui_instance.large_tree.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
    sb_l.grid(row=0, column=1, sticky="ns", pady=4)

    cln_act_card = ctk.CTkFrame(scroll, fg_color="transparent")
    cln_act_card.grid(row=2, column=0, sticky="ew", pady=(0, 8))

    ctk.CTkButton(
        cln_act_card,
        text="🗑️ Move Selected Junk to Vault Trash",
        command=gui_instance.clean_selected_junk,
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        fg_color="#c62828",
        hover_color="#d32f2f",
        height=36
    ).pack(side="left", padx=(0, 8))

    ctk.CTkButton(
        cln_act_card,
        text="📁 Move Selected Large Files to Folder...",
        command=gui_instance.move_selected_large_files,
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        fg_color=("#FF9500", "#FF9F0A") if HAS_THEME else "#f57c00",
        height=36
    ).pack(side="left")
