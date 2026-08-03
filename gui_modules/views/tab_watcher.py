import tkinter as tk
from gui_modules.components import create_info_icon, get_user_folder

try:
    import customtkinter as ctk
    HAS_CUSTOMTKINTER = True
except ImportError:
    HAS_CUSTOMTKINTER = False


def setup_watcher_tab(gui_instance):
    scroll = ctk.CTkScrollableFrame(gui_instance.tab_watcher, fg_color="transparent")
    scroll.pack(fill="both", expand=True)
    scroll.grid_columnconfigure(0, weight=1)

    wtc_card = ctk.CTkFrame(scroll, corner_radius=12)
    wtc_card.grid(row=0, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    wtc_card.grid_columnconfigure(1, weight=1)

    hdr_w = ctk.CTkFrame(wtc_card, fg_color="transparent")
    hdr_w.grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(6, 4))
    ctk.CTkLabel(hdr_w, text="👁️ Automated Download Folder Watcher Service", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).pack(side="left")
    create_info_icon(hdr_w, "Background service that monitors your Downloads folder and automatically organizes newly downloaded files instantly!").pack(side="left", padx=6)

    ctk.CTkLabel(wtc_card, text="Folder to Watch:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.wtc_dir_var = tk.StringVar(value=get_user_folder("Downloads"))
    gui_instance.wtc_dir_entry = ctk.CTkEntry(wtc_card, textvariable=gui_instance.wtc_dir_var, placeholder_text="Select directory to watch...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.wtc_dir_entry.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)

    wtc_btn_box = ctk.CTkFrame(wtc_card, fg_color="transparent")
    wtc_btn_box.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=4)

    ctk.CTkButton(wtc_btn_box, text="📁 Pick Folder...", command=gui_instance.browse_wtc_folder, font=ctk.CTkFont(size=10, weight="bold"), height=32, width=95).pack(side="left", padx=(0, 3))
    ctk.CTkButton(wtc_btn_box, text="📁+ Multi Folders...", command=lambda: gui_instance.browse_multiple_folders(gui_instance.wtc_dir_var), font=ctk.CTkFont(size=10, weight="bold"), fg_color="#1565c0", height=32, width=110).pack(side="left", padx=(0, 3))

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

    gui_instance.wtc_status_lbl = ctk.CTkLabel(wtc_card, text="Status: 🔴 Service Stopped", font=ctk.CTkFont(size=12, weight="bold"), text_color="#e57373")
    gui_instance.wtc_status_lbl.grid(row=2, column=0, columnspan=2, sticky="w", padx=12, pady=6)

    btn_box = ctk.CTkFrame(wtc_card, fg_color="transparent")
    btn_box.grid(row=3, column=0, columnspan=3, sticky="w", padx=12, pady=(4, 6))

    gui_instance.wtc_start_btn = ctk.CTkButton(
        btn_box,
        text="▶ Start Folder Watcher",
        command=gui_instance.start_watcher_service,
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        fg_color="#1b5e20",
        height=34
    )
    gui_instance.wtc_start_btn.pack(side="left", padx=(0, 8))

    gui_instance.wtc_stop_btn = ctk.CTkButton(
        btn_box,
        text="⏹ Stop Service",
        command=gui_instance.stop_watcher_service,
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        fg_color="#c62828",
        height=34,
        state="disabled"
    )
    gui_instance.wtc_stop_btn.pack(side="left")
