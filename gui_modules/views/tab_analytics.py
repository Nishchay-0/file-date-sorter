import os
import tkinter as tk
from tkinter import messagebox
from gui_modules.components import create_info_icon
from sorter_core import analyze_storage_insights, fix_win_long_path

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


def setup_insights_tab(gui_instance):
    scroll = ctk.CTkScrollableFrame(gui_instance.tab_insights, fg_color="transparent")
    scroll.pack(fill="both", expand=True)
    scroll.grid_columnconfigure(0, weight=1)
    gui_instance.insights_scroll = scroll

    hdr_card = ctk.CTkFrame(scroll, corner_radius=16)
    hdr_card.grid(row=0, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    hdr_card.grid_columnconfigure(1, weight=1)

    hdr_i = ctk.CTkFrame(hdr_card, fg_color="transparent")
    hdr_i.grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(6, 4))
    ctk.CTkLabel(hdr_i, text="📊 Storage Insights & Visual Category Analytics", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).pack(side="left")
    create_info_icon(hdr_i, "Generates a detailed breakdown of folder disk space by Category (Images, Videos, Docs), Timeline span & Subfolders!").pack(side="left", padx=6)

    ctk.CTkLabel(hdr_card, text="Select Folder:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.ins_dir_var = tk.StringVar()
    gui_instance.ins_dir_entry = ctk.CTkEntry(hdr_card, textvariable=gui_instance.ins_dir_var, placeholder_text="Select directory to generate storage analytics...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.ins_dir_entry.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)

    ins_btn_box = ctk.CTkFrame(hdr_card, fg_color="transparent")
    ins_btn_box.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=4)

    ctk.CTkButton(ins_btn_box, text="📁 Pick Folder...", command=gui_instance.browse_ins_folder, font=ctk.CTkFont(size=10, weight="bold"), height=32, width=95).pack(side="left", padx=(0, 3))
    ctk.CTkButton(ins_btn_box, text="📁+ Multi Folders...", command=lambda: gui_instance.browse_multiple_folders(gui_instance.ins_dir_var, gui_instance.run_insights_analysis), font=ctk.CTkFont(size=10, weight="bold"), fg_color="#1565c0", height=32, width=110).pack(side="left", padx=(0, 3))

    ctk.CTkButton(
        ins_btn_box,
        text="📊 Analyze Storage",
        command=gui_instance.run_insights_analysis,
        font=ctk.CTkFont(size=11, weight="bold"),
        fg_color=("#007AFF", "#0A84FF") if HAS_THEME else "#0288d1",
        height=32,
        width=140
    ).pack(side="left")

    gui_instance.insights_dashboard = ctk.CTkFrame(scroll, corner_radius=16)
    gui_instance.insights_dashboard.grid(row=1, column=0, sticky="ew", pady=(0, 8), ipadx=12, ipady=12)
    gui_instance.insights_dashboard.grid_columnconfigure(0, weight=1)

    gui_instance.ins_placeholder = ctk.CTkLabel(gui_instance.insights_dashboard, text="Select a directory and click '📊 Analyze Storage' to view visual analytics.", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray50")
    gui_instance.ins_placeholder.pack(pady=50)
