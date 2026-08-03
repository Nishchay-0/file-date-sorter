import tkinter as tk
from tkinter import ttk
from gui_modules.components import create_info_icon

try:
    import customtkinter as ctk
    HAS_CUSTOMTKINTER = True
except ImportError:
    HAS_CUSTOMTKINTER = False


def setup_converter_tab(gui_instance):
    scroll = ctk.CTkScrollableFrame(gui_instance.tab_converter, fg_color="transparent")
    scroll.pack(fill="both", expand=True)
    scroll.grid_columnconfigure(0, weight=1)

    conv_hdr_card = ctk.CTkFrame(scroll, corner_radius=12)
    conv_hdr_card.grid(row=0, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    conv_hdr_card.grid_columnconfigure(1, weight=1)

    hdr_c = ctk.CTkFrame(conv_hdr_card, fg_color="transparent")
    hdr_c.grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(6, 4))
    ctk.CTkLabel(hdr_c, text="🪄 Smart Magic File Converter & Format Auto-Fixer", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).pack(side="left")
    create_info_icon(hdr_c, "Auto-detects real file types via Magic Byte Headers! Converts 3GA, OPUS, AMR -> MP3, VOB, 3GP, MKV -> MP4, WEBP, HEIC -> JPG, and repairs missing/corrupted file extensions.").pack(side="left", padx=6)

    ctk.CTkLabel(conv_hdr_card, text="Scan Directory:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.conv_src_var = tk.StringVar()
    gui_instance.conv_src_entry = ctk.CTkEntry(conv_hdr_card, textvariable=gui_instance.conv_src_var, placeholder_text="Select folder containing 3GA, OPUS, VOB, WEBP, or misnamed files to convert...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.conv_src_entry.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)

    conv_btn_box = ctk.CTkFrame(conv_hdr_card, fg_color="transparent")
    conv_btn_box.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=4)

    ctk.CTkButton(conv_btn_box, text="📁 Pick Folder...", command=gui_instance.browse_conv_folder, font=ctk.CTkFont(size=10, weight="bold"), height=32, width=105).pack(side="left", padx=(0, 3))
    ctk.CTkButton(conv_btn_box, text="📄 Pick Files...", command=gui_instance.browse_conv_files, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#00838f", height=32, width=95).pack(side="left")

    ctk.CTkLabel(conv_hdr_card, text="Export Output (Opt):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.conv_dest_var = tk.StringVar()
    gui_instance.conv_dest_entry = ctk.CTkEntry(conv_hdr_card, textvariable=gui_instance.conv_dest_var, placeholder_text="Leave blank to convert in-place, or choose a folder to export converted files...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.conv_dest_entry.grid(row=2, column=1, sticky="ew", padx=(0, 6), pady=4)

    ctk.CTkButton(conv_hdr_card, text="📂 Export Folder...", command=gui_instance.browse_conv_dest, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#4527a0", height=32, width=120).grid(row=2, column=2, sticky="e", padx=(0, 12), pady=4)

    conv_opt_card = ctk.CTkFrame(scroll, corner_radius=12)
    conv_opt_card.grid(row=1, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    conv_opt_card.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(conv_opt_card, text="Conversion Action:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="w", padx=(12, 6), pady=6)

    gui_instance.conv_mode_var = ctk.StringVar(value="⚡ Auto-Detect & Convert Everything (Recommended)")
    gui_instance.conv_mode_dropdown = ctk.CTkOptionMenu(
        conv_opt_card,
        variable=gui_instance.conv_mode_var,
        values=[
            "⚡ Auto-Detect & Convert Everything (Recommended)",
            "🎵 Convert All Audio -> MP3 (3GA, OPUS, OGG, AMR, WAV)",
            "🎬 Convert All Video -> MP4 (VOB, 3GP, MKV, AVI, WEBM)",
            "🖼️ Convert All Images -> JPG (WEBP, HEIC, BMP, TIFF)",
            "🏷️ Fix Wrong/Missing Extensions Only"
        ],
        command=lambda x: gui_instance.refresh_converter_preview(),
        font=ctk.CTkFont(size=11),
        dropdown_font=ctk.CTkFont(size=11),
        height=32,
        width=340
    )
    gui_instance.conv_mode_dropdown.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=6)

    gui_instance.conv_delete_orig_var = tk.BooleanVar(value=False)
    chk_del_orig = ctk.CTkCheckBox(
        conv_opt_card,
        text="🗑️ Delete Original Files After Successful Conversion",
        variable=gui_instance.conv_delete_orig_var,
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color="#ef5350"
    )
    chk_del_orig.grid(row=0, column=2, sticky="e", padx=(0, 12), pady=6)

    # Parallel Execution Speed Selector
    ctk.CTkLabel(conv_opt_card, text="Parallel Processing:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, sticky="w", padx=(12, 6), pady=6)

    gui_instance.conv_threads_var = ctk.StringVar(value="⚡ 4 Parallel Threads (Fast)")
    gui_instance.conv_threads_dropdown = ctk.CTkOptionMenu(
        conv_opt_card,
        variable=gui_instance.conv_threads_var,
        values=[
            "1 Sequential Thread (Single File)",
            "⚡ 2 Parallel Threads",
            "⚡ 4 Parallel Threads (Fast)",
            "🚀 8 Parallel Threads (Ultra Fast)"
        ],
        font=ctk.CTkFont(size=11),
        dropdown_font=ctk.CTkFont(size=11),
        height=30,
        width=250
    )
    gui_instance.conv_threads_dropdown.grid(row=1, column=1, sticky="w", padx=(0, 12), pady=6)


    conv_prev_card = ctk.CTkFrame(scroll, corner_radius=12)
    conv_prev_card.grid(row=2, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=6)
    conv_prev_card.grid_columnconfigure(0, weight=1)

    conv_prev_hdr = ctk.CTkFrame(conv_prev_card, fg_color="transparent")
    conv_prev_hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(6, 4))
    conv_prev_hdr.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(conv_prev_hdr, text="Conversion Preview Plan:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w")

    conv_hdr_btns = ctk.CTkFrame(conv_prev_hdr, fg_color="transparent")
    conv_hdr_btns.grid(row=0, column=1, sticky="e")

    ctk.CTkButton(
        conv_hdr_btns,
        text="🔄 Refresh Scan",
        command=gui_instance.refresh_converter_preview,
        font=ctk.CTkFont(size=10, weight="bold"),
        fg_color=("gray75", "gray30"),
        text_color=("gray10", "gray90"),
        height=26, width=105
    ).pack(side="left", padx=2)

    tree_conv_frame = ctk.CTkFrame(conv_prev_card, fg_color="transparent")
    tree_conv_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(2, 6))
    tree_conv_frame.grid_columnconfigure(0, weight=1)
    tree_conv_frame.grid_rowconfigure(0, weight=1)

    cols_cv = ("filename", "rel_path", "detected_format", "action", "target_name", "size_str")
    gui_instance.conv_tree = ttk.Treeview(tree_conv_frame, columns=cols_cv, show="headings", height=8, selectmode="extended")
    gui_instance.conv_tree.heading("filename", text="Original File Name", command=lambda: gui_instance._sort_tree(gui_instance.conv_tree, "filename"))
    gui_instance.conv_tree.heading("rel_path", text="Subfolder Path", command=lambda: gui_instance._sort_tree(gui_instance.conv_tree, "rel_path"))
    gui_instance.conv_tree.heading("detected_format", text="Detected Magic Header", command=lambda: gui_instance._sort_tree(gui_instance.conv_tree, "detected_format"))
    gui_instance.conv_tree.heading("action", text="Action / Conversion", command=lambda: gui_instance._sort_tree(gui_instance.conv_tree, "action"))
    gui_instance.conv_tree.heading("target_name", text="Target Filename", command=lambda: gui_instance._sort_tree(gui_instance.conv_tree, "target_name"))
    gui_instance.conv_tree.heading("size_str", text="Size", command=lambda: gui_instance._sort_tree(gui_instance.conv_tree, "size_str"))

    gui_instance.conv_tree.column("filename", width=180, minwidth=100)
    gui_instance.conv_tree.column("rel_path", width=220, minwidth=100)
    gui_instance.conv_tree.column("detected_format", width=160, minwidth=90)
    gui_instance.conv_tree.column("action", width=180, minwidth=100)
    gui_instance.conv_tree.column("target_name", width=180, minwidth=100)
    gui_instance.conv_tree.column("size_str", width=80, minwidth=50)

    sb_cv = ttk.Scrollbar(tree_conv_frame, orient="vertical", command=gui_instance.conv_tree.yview)
    gui_instance.conv_tree.configure(yscrollcommand=sb_cv.set)
    gui_instance.conv_tree.grid(row=0, column=0, sticky="nsew")
    sb_cv.grid(row=0, column=1, sticky="ns")

    gui_instance.conv_stats_lbl = ctk.CTkLabel(
        conv_prev_card,
        text="Preview: 0 convertible file(s) detected.",
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color=("#0288d1", "#64b5f6")
    )
    gui_instance.conv_stats_lbl.grid(row=2, column=0, sticky="w", padx=12, pady=(2, 6))

    conv_act_card = ctk.CTkFrame(scroll, corner_radius=12)
    conv_act_card.grid(row=3, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    conv_act_card.grid_columnconfigure(1, weight=1)

    gui_instance.conv_start_btn = ctk.CTkButton(
        conv_act_card,
        text="⚡ Start Magic Conversion",
        command=gui_instance.start_converter_execution,
        font=ctk.CTkFont(size=13, weight="bold"),
        fg_color="#2e7d32",
        hover_color="#1b5e20",
        height=38, width=220
    )
    gui_instance.conv_start_btn.grid(row=0, column=0, sticky="w", padx=12, pady=6)

    gui_instance.conv_progress_bar = ctk.CTkProgressBar(conv_act_card, height=12)
    gui_instance.conv_progress_bar.set(0)
    gui_instance.conv_progress_bar.grid(row=0, column=1, sticky="ew", padx=12, pady=6)
