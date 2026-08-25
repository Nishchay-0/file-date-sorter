import os
import tkinter as tk
from tkinter import filedialog, messagebox

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


def setup_exclusions_tab(gui_instance):
    scroll = ctk.CTkScrollableFrame(gui_instance.tab_exclusions, fg_color="transparent")
    scroll.pack(fill="both", expand=True)
    scroll.grid_columnconfigure(0, weight=1)
    gui_instance.exclusions_scroll = scroll

    # Header Card
    hdr_card = ctk.CTkFrame(scroll, corner_radius=16)
    hdr_card.grid(row=0, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    hdr_card.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        hdr_card,
        text="🚫 App-Wide Exclusions & Exceptions Manager",
        font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
    ).pack(anchor="w", padx=12, pady=(6, 2))

    ctk.CTkLabel(
        hdr_card,
        text="Exclusions configured here apply automatically across ALL 7 tools (Sorter, Duplicates, Extractor, Cleaner, Renamer, Analytics, Auto Watcher).",
        font=ctk.CTkFont(size=11),
        text_color="gray60"
    ).pack(anchor="w", padx=12, pady=(0, 6))

    # ── SECTION 1: EXCLUDED FOLDERS ──
    fld_card = ctk.CTkFrame(scroll, corner_radius=16)
    fld_card.grid(row=1, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    fld_card.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(fld_card, text="1. Excluded Folders & Subdirectories", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(6, 4))

    ctk.CTkLabel(fld_card, text="Excluded Folders:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.exc_fold_entry_global = ctk.CTkEntry(fld_card, textvariable=gui_instance.exclude_folders_var, placeholder_text="e.g. .git, node_modules, temp, _Duplicates", font=ctk.CTkFont(size=11), height=32)
    gui_instance.exc_fold_entry_global.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)

    btn_fld_box = ctk.CTkFrame(fld_card, fg_color="transparent")
    btn_fld_box.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=4)

    ctk.CTkButton(btn_fld_box, text="📁 Add Folder...", command=gui_instance.add_exclude_folder_picker, font=ctk.CTkFont(size=10, weight="bold"), height=32, fg_color="#c62828").pack(side="left", padx=(0, 3))
    ctk.CTkButton(btn_fld_box, text="📁+ Add Multi Folders...", command=lambda: gui_instance.browse_multiple_folders(gui_instance.exclude_folders_var), font=ctk.CTkFont(size=10, weight="bold"), height=32, fg_color="#b71c1c").pack(side="left", padx=(0, 3))
    ctk.CTkButton(btn_fld_box, text="🧹 Clear All", command=lambda: gui_instance.exclude_folders_var.set(""), font=ctk.CTkFont(size=10), height=32, width=65, fg_color=("gray75", "gray30"), text_color=("gray10", "gray90")).pack(side="left")

    # Preset Folder Exclusions
    preset_fld_box = ctk.CTkFrame(fld_card, fg_color="transparent")
    preset_fld_box.grid(row=2, column=0, columnspan=3, sticky="w", padx=12, pady=(2, 6))
    ctk.CTkLabel(preset_fld_box, text="Quick Add Common Exclusions:", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray60").pack(side="left", padx=(0, 6))

    def _add_fld_preset(name):
        curr = gui_instance.parse_comma_list(gui_instance.exclude_folders_var.get().strip())
        if name not in curr:
            curr.append(name)
            gui_instance.exclude_folders_var.set(", ".join(curr))

    for p_name in [".git", "node_modules", "temp", "tmp", "System Volume Information", "$RECYCLE.BIN", "_Duplicates", ".backups"]:
        ctk.CTkButton(preset_fld_box, text=f"+ {p_name}", command=lambda n=p_name: _add_fld_preset(n), font=ctk.CTkFont(size=9), height=22, fg_color=("gray75", "gray30"), text_color=("gray10", "gray90")).pack(side="left", padx=2)

    # ── SECTION 2: EXCLUDED FILE NAMES ──
    file_card = ctk.CTkFrame(scroll, corner_radius=16)
    file_card.grid(row=2, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    file_card.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(file_card, text="2. Excluded File Names & System Artifacts", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(6, 4))

    ctk.CTkLabel(file_card, text="Excluded Files:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.exc_file_entry_global = ctk.CTkEntry(file_card, textvariable=gui_instance.exclude_files_var, placeholder_text="e.g. desktop.ini, .DS_Store, thumbs.db, pagefile.sys", font=ctk.CTkFont(size=11), height=32)
    gui_instance.exc_file_entry_global.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)

    btn_file_box = ctk.CTkFrame(file_card, fg_color="transparent")
    btn_file_box.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=4)

    ctk.CTkButton(btn_file_box, text="📄 Add Files...", command=gui_instance.add_exclude_file_picker, font=ctk.CTkFont(size=10, weight="bold"), height=32, fg_color="#ad1457").pack(side="left", padx=(0, 3))
    ctk.CTkButton(btn_file_box, text="🧹 Clear All", command=lambda: gui_instance.exclude_files_var.set(""), font=ctk.CTkFont(size=10), height=32, width=65, fg_color=("gray75", "gray30"), text_color=("gray10", "gray90")).pack(side="left")

    # Preset File Exclusions
    preset_file_box = ctk.CTkFrame(file_card, fg_color="transparent")
    preset_file_box.grid(row=2, column=0, columnspan=3, sticky="w", padx=12, pady=(2, 6))
    ctk.CTkLabel(preset_file_box, text="Quick Add Common System Files:", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray60").pack(side="left", padx=(0, 6))

    def _add_file_preset(name):
        curr = gui_instance.parse_comma_list(gui_instance.exclude_files_var.get().strip())
        if name not in curr:
            curr.append(name)
            gui_instance.exclude_files_var.set(", ".join(curr))

    for pf_name in ["desktop.ini", ".DS_Store", "thumbs.db", "pagefile.sys", "hiberfil.sys", "swapfile.sys"]:
        ctk.CTkButton(preset_file_box, text=f"+ {pf_name}", command=lambda n=pf_name: _add_file_preset(n), font=ctk.CTkFont(size=9), height=22, fg_color=("gray75", "gray30"), text_color=("gray10", "gray90")).pack(side="left", padx=2)

    # ── SECTION 3: EXCLUDED FILE EXTENSIONS ──
    ext_card = ctk.CTkFrame(scroll, corner_radius=16)
    ext_card.grid(row=3, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    ext_card.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(ext_card, text="3. Excluded File Extensions", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(6, 4))

    ctk.CTkLabel(ext_card, text="Excluded Exts:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.exc_ext_entry_global = ctk.CTkEntry(ext_card, textvariable=gui_instance.exclude_ext_var, placeholder_text="e.g. .tmp, .log, .bak, .part, .crdownload", font=ctk.CTkFont(size=11), height=32)
    gui_instance.exc_ext_entry_global.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)

    ctk.CTkButton(ext_card, text="🧹 Clear All", command=lambda: gui_instance.exclude_ext_var.set(""), font=ctk.CTkFont(size=10), height=32, width=65, fg_color=("gray75", "gray30"), text_color=("gray10", "gray90")).grid(row=1, column=2, sticky="e", padx=(0, 12), pady=4)

    # Preset Junk Extension Toggles
    junk_ext_frame = ctk.CTkFrame(ext_card, fg_color=("gray90", "gray18"), corner_radius=8)
    junk_ext_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=12, pady=(4, 6))

    junk_hdr = ctk.CTkFrame(junk_ext_frame, fg_color="transparent")
    junk_hdr.pack(fill="x", padx=8, pady=(4, 2))
    ctk.CTkLabel(junk_hdr, text="Quick Junk Extension Checkboxes:", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray60").pack(side="left")

    common_junk = [".tmp", ".log", ".bak", ".old", ".chk", ".part", ".crdownload", ".dmp", ".swp", ".temp", ".cache"]
    junk_grid = ctk.CTkFrame(junk_ext_frame, fg_color="transparent")
    junk_grid.pack(fill="x", padx=8, pady=(0, 6))

    def _toggle_junk_ext(ext):
        curr = set(gui_instance.parse_comma_list(gui_instance.exclude_ext_var.get().strip()))
        if ext in curr:
            curr.remove(ext)
        else:
            curr.add(ext)
        gui_instance.exclude_ext_var.set(", ".join(sorted(curr)))

    col_i = 0
    row_i = 0
    for j_ext in common_junk:
        btn = ctk.CTkButton(
            junk_grid, text=f"🚫 {j_ext}",
            command=lambda e=j_ext: _toggle_junk_ext(e),
            font=ctk.CTkFont(size=10),
            height=24, width=75,
            fg_color="#c62828"
        )
        btn.grid(row=row_i, column=col_i, padx=3, pady=2)
        col_i += 1
        if col_i > 5:
            col_i = 0
            row_i += 1

    # ── SECTION 4: WINDOWS EXPLORER CONTEXT MENU INTEGRATION ──
    ctx_card = ctk.CTkFrame(scroll, corner_radius=16)
    ctx_card.grid(row=4, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    ctx_card.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(ctx_card, text="4. Windows Explorer Right-Click Context Menu Integration", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(6, 4))

    from gui_modules.context_menu import install_context_menu, uninstall_context_menu, check_context_menu_status

    status_str = "🟢 ACTIVE" if check_context_menu_status() else "🔴 NOT INSTALLED"
    ctx_status_lbl = ctk.CTkLabel(ctx_card, text=f"Status: {status_str}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#81c784" if "ACTIVE" in status_str else "#e57373")
    ctx_status_lbl.grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)

    ctx_btn_box = ctk.CTkFrame(ctx_card, fg_color="transparent")
    ctx_btn_box.grid(row=1, column=1, columnspan=2, sticky="e", padx=(0, 12), pady=4)

    def _do_install_ctx():
        ok, msg = install_context_menu()
        if ok:
            ctx_status_lbl.configure(text="Status: 🟢 ACTIVE", text_color="#81c784")
            messagebox.showinfo("Context Menu Installed", msg)
        else:
            messagebox.showerror("Error", msg)

    def _do_uninstall_ctx():
        ok, msg = uninstall_context_menu()
        if ok:
            ctx_status_lbl.configure(text="Status: 🔴 NOT INSTALLED", text_color="#e57373")
            messagebox.showinfo("Context Menu Removed", msg)
        else:
            messagebox.showinfo("Info", msg)

    ctk.CTkButton(
        ctx_btn_box,
        text="➕ Add to Windows Right-Click Menu",
        command=_do_install_ctx,
        font=ctk.CTkFont(size=10, weight="bold"),
        fg_color=("#007AFF", "#0A84FF") if HAS_THEME else "#0288d1",
        height=32
    ).pack(side="left", padx=(0, 4))

    ctk.CTkButton(
        ctx_btn_box,
        text="🗑️ Remove from Right-Click Menu",
        command=_do_uninstall_ctx,
        font=ctk.CTkFont(size=10),
        fg_color=("gray75", "gray30"),
        text_color=("gray10", "gray90"),
        height=32
    ).pack(side="left")

