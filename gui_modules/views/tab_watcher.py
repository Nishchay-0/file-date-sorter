import tkinter as tk
from gui_modules.components import create_info_icon, get_user_folder

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


def setup_watcher_tab(gui_instance):
    scroll = ctk.CTkScrollableFrame(gui_instance.tab_watcher, fg_color="transparent")
    scroll.pack(fill="both", expand=True)
    scroll.grid_columnconfigure(0, weight=1)
    gui_instance.watcher_scroll = scroll

    wtc_card = ctk.CTkFrame(scroll, corner_radius=16)
    wtc_card.grid(row=0, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    wtc_card.grid_columnconfigure(1, weight=1)

    hdr_w = ctk.CTkFrame(wtc_card, fg_color="transparent")
    hdr_w.grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(6, 4))
    ctk.CTkLabel(hdr_w, text="👁️ Automated Download Folder Watcher Service", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).pack(side="left")
    create_info_icon(hdr_w, "Background service that monitors your Downloads/Target folder and automatically organizes newly dropped files instantly!").pack(side="left", padx=6)

    ctk.CTkLabel(wtc_card, text="Folder to Watch:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.wtc_dir_var = tk.StringVar(value=get_user_folder("Downloads"))
    gui_instance.wtc_dir_entry = ctk.CTkEntry(wtc_card, textvariable=gui_instance.wtc_dir_var, placeholder_text="Select directory to watch...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.wtc_dir_entry.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)

    wtc_btn_box = ctk.CTkFrame(wtc_card, fg_color="transparent")
    wtc_btn_box.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=4)

    ctk.CTkButton(wtc_btn_box, text="📁 Pick Folder...", command=gui_instance.browse_wtc_folder, font=ctk.CTkFont(size=10, weight="bold"), height=32, width=95).pack(side="left", padx=(0, 3))
    ctk.CTkButton(
        wtc_btn_box,
        text="📥 Downloads",
        command=lambda: gui_instance.wtc_dir_var.set(get_user_folder("Downloads")),
        font=ctk.CTkFont(size=10),
        fg_color=("gray75", "gray30"),
        text_color=("gray10", "gray90"),
        height=32,
        width=95
    ).pack(side="left")

    # Options Row: Sort Rule & Debounce Window
    opts_card = ctk.CTkFrame(wtc_card, fg_color=("gray92", "gray20"), corner_radius=8)
    opts_card.grid(row=2, column=0, columnspan=3, sticky="ew", padx=12, pady=6, ipadx=6, ipady=4)

    ctk.CTkLabel(opts_card, text="Sort Criteria:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(8, 4))
    gui_instance.wtc_sort_category_var = ctk.StringVar(value="date")
    ctk.CTkOptionMenu(
        opts_card,
        variable=gui_instance.wtc_sort_category_var,
        values=["date", "category", "extension", "name", "size"],
        font=ctk.CTkFont(size=11),
        width=130
    ).pack(side="left", padx=(0, 16))

    ctk.CTkLabel(opts_card, text="Debounce Window:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 4))
    gui_instance.wtc_debounce_var = tk.StringVar(value="3.0")
    ctk.CTkEntry(opts_card, textvariable=gui_instance.wtc_debounce_var, width=50, font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 4))
    ctk.CTkLabel(opts_card, text="seconds", font=ctk.CTkFont(size=11), text_color="gray60").pack(side="left", padx=(0, 12))

    # Controls Row: Switch & Status
    ctrl_row = ctk.CTkFrame(wtc_card, fg_color="transparent")
    ctrl_row.grid(row=3, column=0, columnspan=3, sticky="ew", padx=12, pady=(4, 6))

    gui_instance.wtc_switch_var = tk.BooleanVar(value=False)
    gui_instance.wtc_switch = ctk.CTkSwitch(
        ctrl_row,
        text="Watch this folder (Background Auto-Organize)",
        variable=gui_instance.wtc_switch_var,
        command=gui_instance.toggle_watcher_switch,
        font=ctk.CTkFont(size=12, weight="bold"),
        progress_color="#2e7d32"
    )
    gui_instance.wtc_switch.pack(side="left", padx=(0, 16))

    gui_instance.wtc_status_lbl = ctk.CTkLabel(ctrl_row, text="Status: 🔴 Service Stopped", font=ctk.CTkFont(size=12, weight="bold"), text_color="#e57373")
    gui_instance.wtc_status_lbl.pack(side="left", padx=8)

    # Session Stats Card
    stats_card = ctk.CTkFrame(scroll, corner_radius=16)
    stats_card.grid(row=1, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    stats_card.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(stats_card, text="📊 Live Watcher Session Statistics", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(6, 4))

    gui_instance.wtc_stats_files_lbl = ctk.CTkLabel(stats_card, text="Files Auto-Organized This Session: 0", font=ctk.CTkFont(size=11, weight="bold"), text_color="#81c784")
    gui_instance.wtc_stats_files_lbl.grid(row=1, column=0, sticky="w", padx=12, pady=2)

    gui_instance.wtc_stats_active_folder_lbl = ctk.CTkLabel(stats_card, text="Watched Target Folder: None", font=ctk.CTkFont(size=11), text_color="gray70")
    gui_instance.wtc_stats_active_folder_lbl.grid(row=2, column=0, sticky="w", padx=12, pady=2)
