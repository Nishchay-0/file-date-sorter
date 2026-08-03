import os
import tkinter as tk
from tkinter import ttk
from gui_modules.components import create_info_icon

try:
    import customtkinter as ctk
    HAS_CUSTOMTKINTER = True
except ImportError:
    HAS_CUSTOMTKINTER = False


def setup_renamer_tab(gui_instance):
    scroll = ctk.CTkScrollableFrame(gui_instance.tab_renamer, fg_color="transparent")
    scroll.pack(fill="both", expand=True)
    scroll.grid_columnconfigure(0, weight=1)
    gui_instance.renamer_scroll = scroll

    ren_dir_card = ctk.CTkFrame(scroll, corner_radius=12)
    ren_dir_card.grid(row=0, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    ren_dir_card.grid_columnconfigure(1, weight=1)

    hdr_r = ctk.CTkFrame(ren_dir_card, fg_color="transparent")
    hdr_r.grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(6, 4))
    ctk.CTkLabel(hdr_r, text="🏷️ Bulk File Renamer & Batch Formatter", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).pack(side="left")
    create_info_icon(hdr_r, "Batch renames hundreds of files at once using tags like {YYYY}, {MM}, {001}, text find/replace & case transformers!").pack(side="left", padx=6)

    ctk.CTkLabel(ren_dir_card, text="Target:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.ren_dir_var = tk.StringVar()
    gui_instance.ren_dir_entry = ctk.CTkEntry(ren_dir_card, textvariable=gui_instance.ren_dir_var, placeholder_text="Select directory or pick specific files...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.ren_dir_entry.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)

    ren_btn_box = ctk.CTkFrame(ren_dir_card, fg_color="transparent")
    ren_btn_box.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=4)

    ctk.CTkButton(ren_btn_box, text="📁 Pick Folder...", command=gui_instance.browse_ren_dir, font=ctk.CTkFont(size=10, weight="bold"), height=32, width=95).pack(side="left", padx=(0, 3))
    ctk.CTkButton(ren_btn_box, text="📁+ Multi Folders...", command=lambda: gui_instance.browse_multiple_folders(gui_instance.ren_dir_var, gui_instance.refresh_renamer_preview), font=ctk.CTkFont(size=10, weight="bold"), fg_color="#1565c0", height=32, width=110).pack(side="left", padx=(0, 3))
    ctk.CTkButton(ren_btn_box, text="📄 Pick Files...", command=gui_instance.browse_ren_individual_files, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#00838f", height=32, width=90).pack(side="left")

    # Dedicated Exclusions Row
    ctk.CTkLabel(ren_dir_card, text="Exclusions (Opt):", font=ctk.CTkFont(size=11, weight="bold"), text_color="#ef5350").grid(row=2, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.ren_exc_entry = ctk.CTkEntry(ren_dir_card, textvariable=gui_instance.exclude_folders_var, placeholder_text="Folders/Subfolders to SKIP...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.ren_exc_entry.grid(row=2, column=1, sticky="ew", padx=(0, 6), pady=4)

    ren_exc_btn_box = ctk.CTkFrame(ren_dir_card, fg_color="transparent")
    ren_exc_btn_box.grid(row=2, column=2, sticky="e", padx=(0, 12), pady=4)

    ctk.CTkButton(ren_exc_btn_box, text="🚫 Except Folder...", command=gui_instance.add_exclude_folder_picker, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#c62828", height=32, width=105).pack(side="left", padx=(0, 3))
    ctk.CTkButton(ren_exc_btn_box, text="🚫 Except Files...", command=gui_instance.add_exclude_file_picker, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#ad1457", height=32, width=95).pack(side="left", padx=(0, 3))
    ctk.CTkButton(ren_exc_btn_box, text="🧹 Clear", command=lambda: gui_instance.exclude_folders_var.set(""), font=ctk.CTkFont(size=10), height=32, width=55, fg_color=("gray75", "gray30"), text_color=("gray10", "gray90")).pack(side="left")

    rules_card = ctk.CTkFrame(scroll, corner_radius=12)
    rules_card.grid(row=1, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    rules_card.grid_columnconfigure(1, weight=1)
    rules_card.grid_columnconfigure(3, weight=1)

    ctk.CTkLabel(rules_card, text="1. Naming Pattern & Transformation Rules", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(6, 4))

    ctk.CTkLabel(rules_card, text="Pattern:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.ren_pattern_var = tk.StringVar(value="Photo_{YYYY}_{MM}_{DD}_{001}")
    gui_instance.ren_pattern_entry = ctk.CTkEntry(rules_card, textvariable=gui_instance.ren_pattern_var, placeholder_text="Tags: {OriginalName}, {YYYY}, {MM}, {DD}, {001}, {Category}", font=ctk.CTkFont(size=11), height=32)
    gui_instance.ren_pattern_entry.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(0, 12), pady=4)
    gui_instance.ren_pattern_var.trace_add("write", lambda *args: gui_instance.refresh_renamer_preview())

    ctk.CTkLabel(rules_card, text="Case Converter:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.ren_case_var = ctk.StringVar(value="Keep Original Case")
    gui_instance.ren_case_dropdown = ctk.CTkOptionMenu(
        rules_card,
        variable=gui_instance.ren_case_var,
        values=["Keep Original Case", "lowercase", "UPPERCASE", "Title Case", "camelCase"],
        command=lambda *args: gui_instance.refresh_renamer_preview(),
        font=ctk.CTkFont(size=11),
        height=30
    )
    gui_instance.ren_case_dropdown.grid(row=2, column=1, sticky="ew", padx=(0, 10), pady=4)

    ctk.CTkLabel(rules_card, text="Search & Replace:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=2, sticky="w", padx=(6, 6), pady=4)

    sr_box = ctk.CTkFrame(rules_card, fg_color="transparent")
    sr_box.grid(row=2, column=3, sticky="ew", padx=(0, 12), pady=4)
    sr_box.grid_columnconfigure(0, weight=1)
    sr_box.grid_columnconfigure(1, weight=1)

    gui_instance.ren_find_var = tk.StringVar()
    gui_instance.ren_find_entry = ctk.CTkEntry(sr_box, textvariable=gui_instance.ren_find_var, placeholder_text="Find...", font=ctk.CTkFont(size=11), height=30)
    gui_instance.ren_find_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
    gui_instance.ren_find_var.trace_add("write", lambda *args: gui_instance.refresh_renamer_preview())

    gui_instance.ren_replace_var = tk.StringVar()
    gui_instance.ren_replace_entry = ctk.CTkEntry(sr_box, textvariable=gui_instance.ren_replace_var, placeholder_text="Replace...", font=ctk.CTkFont(size=11), height=30)
    gui_instance.ren_replace_entry.grid(row=0, column=1, sticky="ew")
    gui_instance.ren_replace_var.trace_add("write", lambda *args: gui_instance.refresh_renamer_preview())

    ctk.CTkLabel(rules_card, text="Add Prefix:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=3, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.ren_prefix_var = tk.StringVar()
    gui_instance.ren_prefix_entry = ctk.CTkEntry(rules_card, textvariable=gui_instance.ren_prefix_var, placeholder_text="e.g. DRAFT_", font=ctk.CTkFont(size=11), height=30)
    gui_instance.ren_prefix_entry.grid(row=3, column=1, sticky="ew", padx=(0, 10), pady=4)
    gui_instance.ren_prefix_var.trace_add("write", lambda *args: gui_instance.refresh_renamer_preview())

    ctk.CTkLabel(rules_card, text="Add Suffix:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=3, column=2, sticky="w", padx=(6, 6), pady=4)

    gui_instance.ren_suffix_var = tk.StringVar()
    gui_instance.ren_suffix_entry = ctk.CTkEntry(rules_card, textvariable=gui_instance.ren_suffix_var, placeholder_text="e.g. _v2", font=ctk.CTkFont(size=11), height=30)
    gui_instance.ren_suffix_entry.grid(row=3, column=3, sticky="ew", padx=(0, 12), pady=4)
    gui_instance.ren_suffix_var.trace_add("write", lambda *args: gui_instance.refresh_renamer_preview())

    ren_preview_card = ctk.CTkFrame(scroll, corner_radius=12)
    ren_preview_card.grid(row=2, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=6)
    ren_preview_card.grid_columnconfigure(0, weight=1)

    ren_hdr = ctk.CTkFrame(ren_preview_card, fg_color="transparent")
    ren_hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(6, 4))
    ren_hdr.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(ren_hdr, text="2. Live Rename Preview Map", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).grid(row=0, column=0, sticky="w")

    gui_instance.ren_stats_lbl = ctk.CTkLabel(ren_hdr, text="Files to Rename: 0", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray60")
    gui_instance.ren_stats_lbl.grid(row=0, column=1, sticky="e", padx=(0, 8))

    ctk.CTkButton(ren_hdr, text="🔍 Refresh Map", command=gui_instance.refresh_renamer_preview, font=ctk.CTkFont(size=11, weight="bold"), height=28, width=120, fg_color="#0288d1").grid(row=0, column=2, sticky="e")

    tree_frame = ctk.CTkFrame(ren_preview_card, corner_radius=8, fg_color=("gray95", "gray15"))
    tree_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))
    tree_frame.grid_columnconfigure(0, weight=1)

    columns = ("old_name", "new_name", "category", "size_str")
    gui_instance.ren_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=6)
    gui_instance.ren_tree.heading("old_name", text="Original Filename", command=lambda: gui_instance._sort_tree(gui_instance.ren_tree, "old_name"))
    gui_instance.ren_tree.heading("new_name", text="Proposed New Filename", command=lambda: gui_instance._sort_tree(gui_instance.ren_tree, "new_name"))
    gui_instance.ren_tree.heading("category", text="Category", command=lambda: gui_instance._sort_tree(gui_instance.ren_tree, "category"))
    gui_instance.ren_tree.heading("size_str", text="Size", command=lambda: gui_instance._sort_tree(gui_instance.ren_tree, "size_str"))

    gui_instance.ren_tree.column("old_name", width=300)
    gui_instance.ren_tree.column("new_name", width=320)
    gui_instance.ren_tree.column("category", width=120)
    gui_instance.ren_tree.column("size_str", width=100)

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=gui_instance.ren_tree.yview)
    gui_instance.ren_tree.configure(yscrollcommand=scrollbar.set)
    gui_instance.ren_tree.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
    scrollbar.grid(row=0, column=1, sticky="ns", pady=4)

    ren_act_card = ctk.CTkFrame(scroll, fg_color="transparent")
    ren_act_card.grid(row=3, column=0, sticky="ew", pady=(0, 8))

    ctk.CTkButton(
        ren_act_card,
        text="▶ Start Batch Rename",
        command=gui_instance.start_batch_rename,
        font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        fg_color="#1b5e20",
        hover_color="#2e7d32",
        height=36,
        width=175
    ).pack(side="left", padx=(0, 8))

    ctk.CTkButton(
        ren_act_card,
        text="🛡️ System Vault Restore",
        command=gui_instance.open_system_vault_restore_manager,
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        fg_color="#c62828",
        height=36,
        width=175
    ).pack(side="left")
