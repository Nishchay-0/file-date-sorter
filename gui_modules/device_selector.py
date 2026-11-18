"""
device_selector.py — Connected Devices & External Storage Selector
Smart File Organizer Suite Pro

Provides a unified interface for selecting files, folders, and storage targets
from any connected device:
- USB Flash Drives, External HDDs/SSDs, SD Cards
- Mobile Phones & Tablets (Android ADB / Windows MTP)
- Secondary Partitions and Network Drives

Allows users to pick files/folders directly from connected devices so that all
organizer tools (Date sorting, Duplicates, People, Extractor, Renamer, Cleaner, Analytics)
work seamlessly on external and mobile media.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    import customtkinter as ctk
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

from device_bridge import DeviceInfo, DeviceType, StorageDriveInfo, UnifiedDeviceManager

try:
    from gui_modules.theme_manager import GLASS, FONTS
    HAS_THEME = True
except ImportError:
    HAS_THEME = False


class ConnectedDevicesDialog(ctk.CTkToplevel if HAS_CTK else object):
    """
    Apple Glassmorphism modal window showing all connected devices & drives
    with one-click actions to select folders, pick specific files, or manage mobile media.
    """
    def __init__(self, parent_gui):
        if not HAS_CTK:
            return

        super().__init__()
        self.gui = parent_gui
        self.device_mgr = UnifiedDeviceManager()

        self.title("🔌 Connected Devices & External Storage")
        self.geometry("740x640")
        self.minsize(620, 500)

        self.after(10, self._center_window)

        self.phones: list = []
        self.removable_drives: list = []
        self.fixed_drives: list = []
        self.is_scanning = False

        self._setup_ui()
        self.refresh_devices()

    def _center_window(self):
        try:
            self.lift()
            self.attributes("-topmost", True)
            self.after_idle(lambda: self.attributes("-topmost", False))
            self.focus_force()

            p_x = self.gui.winfo_rootx()
            p_y = self.gui.winfo_rooty()
            p_w = self.gui.winfo_width()
            p_h = self.gui.winfo_height()
            w, h = 740, 640
            x = max(50, p_x + (p_w - w) // 2)
            y = max(50, p_y + (p_h - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def _setup_ui(self):
        bg = GLASS["bg_primary"] if HAS_THEME else ("gray95", "gray14")
        self.configure(fg_color=bg)

        # ── Header Bar ───────────────────────────────────────────────────────
        header_card = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=GLASS["bg_card"] if HAS_THEME else ("white", "gray20"),
            border_color=GLASS["border"] if HAS_THEME else ("gray80", "gray30"),
            border_width=1
        )
        header_card.pack(fill="x", padx=14, pady=(14, 8))

        top_row = ctk.CTkFrame(header_card, fg_color="transparent")
        top_row.pack(fill="x", padx=12, pady=10)

        title_box = ctk.CTkFrame(top_row, fg_color="transparent")
        title_box.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            title_box,
            text="🔌 Connected Devices & External Storage",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=GLASS["text_primary"] if HAS_THEME else ("gray10", "gray95")
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Select files, folders, or drives directly from USB storage, SD cards, and mobile phones.",
            font=ctk.CTkFont(size=11),
            text_color=GLASS["text_secondary"] if HAS_THEME else "gray50"
        ).pack(anchor="w", pady=(2, 0))

        self.btn_rescan = ctk.CTkButton(
            top_row,
            text="🔄 Rescan Devices",
            command=self.refresh_devices,
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            width=135,
            fg_color=("#007AFF", "#0A84FF") if HAS_THEME else "#0288d1",
            hover_color=("#0062cc", "#0071e3")
        )
        self.btn_rescan.pack(side="right")

        # Status badge row
        self.status_lbl = ctk.CTkLabel(
            header_card,
            text="Scanning connected devices...",
            font=ctk.CTkFont(size=11),
            text_color=GLASS["text_secondary"] if HAS_THEME else "gray50"
        )
        self.status_lbl.pack(anchor="w", padx=12, pady=(0, 8))

        # ── Scrollable Device List Container ─────────────────────────────────
        self.scroll_list = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.scroll_list.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    def refresh_devices(self):
        if self.is_scanning:
            return
        self.is_scanning = True
        self.btn_rescan.configure(state="disabled", text="Scanning...")
        self.status_lbl.configure(text="Scanning USB buses, mobile devices, and storage drives...")

        def _worker():
            try:
                res = self.device_mgr.scan_all_connected_devices()
                phones = res.get("phones", [])
                removable = res.get("removable_drives", [])
                fixed = res.get("fixed_drives", [])
            except Exception as e:
                phones, removable, fixed = [], [], []

            self.after(0, lambda: self._on_scan_finished(phones, removable, fixed))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_scan_finished(self, phones, removable, fixed):
        self.is_scanning = False
        self.btn_rescan.configure(state="normal", text="🔄 Rescan Devices")
        self.phones = phones
        self.removable_drives = removable
        self.fixed_drives = fixed

        summary = f"Detected: {len(self.phones)} Mobile Phone(s) • {len(self.removable_drives)} USB / Removable Drive(s) • {len(self.fixed_drives)} Local Partition(s)"
        self.status_lbl.configure(text=summary)

        # Clear scroll container
        for w in self.scroll_list.winfo_children():
            w.destroy()

        # ── 1. Mobile Devices Section ─────────────────────────────────────────
        self._build_section_header("📱 Mobile Phones & Tablets (USB)", count=len(phones))
        if phones:
            for phone in phones:
                self._build_phone_card(phone)
        else:
            self._build_empty_card(
                "No mobile phone detected via USB.",
                "Connect your phone with a USB cable and ensure screen is unlocked / USB Debugging enabled."
            )

        # ── 2. Removable USB Drives & SD Cards Section ────────────────────────
        self._build_section_header("💾 Removable Storage (USB Flash Drives & SD Cards)", count=len(removable))
        if removable:
            for drv in removable:
                self._build_drive_card(drv, is_removable=True)
        else:
            self._build_empty_card(
                "No removable USB flash drive or SD card detected.",
                "Insert a USB flash drive, external SSD/HDD, or memory card to select and organize external files."
            )

        # ── 3. Local Partitions & Disks Section ──────────────────────────────
        self._build_section_header("💻 Fixed Disks & Local Partitions", count=len(fixed))
        for drv in fixed:
            self._build_drive_card(drv, is_removable=False)

    def _build_section_header(self, text, count=0):
        f = ctk.CTkFrame(self.scroll_list, fg_color="transparent")
        f.pack(fill="x", padx=2, pady=(12, 4))

        ctk.CTkLabel(
            f,
            text=text,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=GLASS["text_primary"] if HAS_THEME else ("gray15", "gray90")
        ).pack(side="left")

        badge_txt = f"{count} active" if count > 0 else "0 connected"
        badge_fg = ("#34C759", "#30D158") if count > 0 else ("gray60", "gray40")
        ctk.CTkLabel(
            f,
            text=f" ({badge_txt})",
            font=ctk.CTkFont(size=11),
            text_color=badge_fg
        ).pack(side="left", padx=(4, 0))

    def _build_empty_card(self, title, desc):
        card = ctk.CTkFrame(
            self.scroll_list,
            corner_radius=10,
            fg_color=GLASS["bg_card_alt"] if HAS_THEME else ("gray90", "gray18"),
            border_color=GLASS["border"] if HAS_THEME else ("gray80", "gray28"),
            border_width=1
        )
        card.pack(fill="x", pady=3)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            inner,
            text=f"ℹ  {title}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=GLASS["text_secondary"] if HAS_THEME else "gray50"
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner,
            text=desc,
            font=ctk.CTkFont(size=10),
            text_color=GLASS["text_secondary"] if HAS_THEME else "gray50"
        ).pack(anchor="w", pady=(2, 0))

    def _build_phone_card(self, phone: DeviceInfo):
        card = ctk.CTkFrame(
            self.scroll_list,
            corner_radius=12,
            fg_color=GLASS["bg_card"] if HAS_THEME else ("white", "gray20"),
            border_color=GLASS["border"] if HAS_THEME else ("gray80", "gray30"),
            border_width=1
        )
        card.pack(fill="x", pady=4)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=10)

        # Phone Icon & Details
        info_col = ctk.CTkFrame(row, fg_color="transparent")
        info_col.pack(side="left", fill="both", expand=True)

        title_frame = ctk.CTkFrame(info_col, fg_color="transparent")
        title_frame.pack(fill="x")

        proto_badge = "⚡ ADB High-Speed" if phone.type == DeviceType.ADB else "🔌 MTP Portable"
        ctk.CTkLabel(
            title_frame,
            text=f"📱  {phone.name}",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=GLASS["text_primary"] if HAS_THEME else ("gray10", "gray95")
        ).pack(side="left")

        ctk.CTkLabel(
            title_frame,
            text=f"  [{proto_badge}]",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("#007AFF", "#0A84FF") if HAS_THEME else "#1565c0"
        ).pack(side="left")

        ctk.CTkLabel(
            info_col,
            text=f"Status: {phone.status} • Serial/ID: {phone.id}",
            font=ctk.CTkFont(size=10),
            text_color=GLASS["text_secondary"] if HAS_THEME else "gray50"
        ).pack(anchor="w", pady=(2, 0))

        # Actions
        btn_box = ctk.CTkFrame(row, fg_color="transparent")
        btn_box.pack(side="right", padx=(8, 0))

        # Open full phone manager dialog
        btn_mgr = ctk.CTkButton(
            btn_box,
            text="📱 Manage Phone Media...",
            command=lambda p=phone: self._open_phone_tools(p),
            font=ctk.CTkFont(size=10, weight="bold"),
            height=28,
            width=150,
            fg_color=("#34C759", "#30D158") if HAS_THEME else "#2e7d32",
            hover_color=("#28a745", "#248a3d")
        )
        btn_mgr.pack(side="left", padx=2)

    def _build_drive_card(self, drv: StorageDriveInfo, is_removable: bool = False):
        card = ctk.CTkFrame(
            self.scroll_list,
            corner_radius=12,
            fg_color=GLASS["bg_card"] if HAS_THEME else ("white", "gray20"),
            border_color=GLASS["border"] if HAS_THEME else ("gray80", "gray30"),
            border_width=1
        )
        card.pack(fill="x", pady=4)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=10)

        # Drive Icon & Info
        info_col = ctk.CTkFrame(row, fg_color="transparent")
        info_col.pack(side="left", fill="both", expand=True)

        header_frame = ctk.CTkFrame(info_col, fg_color="transparent")
        header_frame.pack(fill="x")

        icon = "💾" if is_removable else "💻"
        drive_name = f"{drv.label} ({drv.path.rstrip('\\')})" if drv.letter else drv.label

        ctk.CTkLabel(
            header_frame,
            text=f"{icon}  {drive_name}",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=GLASS["text_primary"] if HAS_THEME else ("gray10", "gray95")
        ).pack(side="left")

        ctk.CTkLabel(
            header_frame,
            text=f"  [{drv.type_desc}]",
            font=ctk.CTkFont(size=10),
            text_color=GLASS["text_secondary"] if HAS_THEME else "gray50"
        ).pack(side="left")

        # Free space meter
        space_txt = drv.free_str
        ctk.CTkLabel(
            info_col,
            text=f"Capacity: {space_txt}",
            font=ctk.CTkFont(size=10),
            text_color=GLASS["text_secondary"] if HAS_THEME else "gray50"
        ).pack(anchor="w", pady=(2, 0))

        # Actions Container
        btn_box = ctk.CTkFrame(row, fg_color="transparent")
        btn_box.pack(side="right", padx=(8, 0))

        # 1. Pick Folder inside this drive
        btn_folder = ctk.CTkButton(
            btn_box,
            text="📂 Pick Folder...",
            command=lambda p=drv.path: self._pick_folder_in_drive(p),
            font=ctk.CTkFont(size=10, weight="bold"),
            height=28,
            width=100,
            fg_color=("#007AFF", "#0A84FF") if HAS_THEME else "#0288d1",
            hover_color=("#0062cc", "#0071e3")
        )
        btn_folder.pack(side="left", padx=2)

        # 2. Pick specific Files inside this drive
        btn_files = ctk.CTkButton(
            btn_box,
            text="📄 Pick Files...",
            command=lambda p=drv.path: self._pick_files_in_drive(p),
            font=ctk.CTkFont(size=10, weight="bold"),
            height=28,
            width=95,
            fg_color=("#32ADE6", "#64D2FF") if HAS_THEME else "#00838f",
            hover_color=("#2295cc", "#4cc0f0")
        )
        btn_files.pack(side="left", padx=2)

        # 3. Select Entire Drive root
        btn_entire = ctk.CTkButton(
            btn_box,
            text="🎯 Entire Drive",
            command=lambda p=drv.path: self._select_entire_drive(p),
            font=ctk.CTkFont(size=10, weight="bold"),
            height=28,
            width=90,
            fg_color=GLASS["bg_card_alt"] if HAS_THEME else ("gray80", "gray25"),
            text_color=GLASS["text_primary"] if HAS_THEME else ("gray10", "gray90"),
            hover_color=GLASS["bg_hover"] if HAS_THEME else ("gray70", "gray35")
        )
        btn_entire.pack(side="left", padx=2)

    def _pick_folder_in_drive(self, drive_path):
        folder = filedialog.askdirectory(
            initialdir=drive_path,
            title=f"Select Target Folder on {drive_path}",
            parent=self
        )
        if folder:
            self.gui.selected_individual_files = []
            self.gui.set_target_dir(folder)
            self.destroy()

    def _pick_files_in_drive(self, drive_path):
        files = filedialog.askopenfilenames(
            initialdir=drive_path,
            title=f"Select Specific Files on {drive_path}",
            parent=self
        )
        if files:
            self.gui.selected_individual_files = list(files)
            dir_name = os.path.dirname(files[0])
            self.gui.dir_var.set(f"[Custom Selection] {len(files)} file(s) selected from {dir_name}")
            self.gui.refresh_preview()
            self.destroy()

    def _select_entire_drive(self, drive_path):
        self.gui.selected_individual_files = []
        self.gui.set_target_dir(drive_path)
        self.destroy()

    def _open_phone_tools(self, phone: DeviceInfo):
        self.destroy()
        try:
            from gui_modules.phone_dialog import open_phone_manager
            open_phone_manager(self.gui)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Phone Manager: {e}")


def open_connected_devices_dialog(parent_gui):
    """
    Public entry point to launch the Connected Devices & External Storage dialog.
    """
    return ConnectedDevicesDialog(parent_gui)


def show_devices_dropdown_menu(gui_instance, source_button):
    """
    Pops up a native quick-action menu right underneath the source_button,
    listing all currently detected drives and phones with 1-click select actions.
    """
    mgr = UnifiedDeviceManager()
    res = mgr.scan_all_connected_devices()
    phones = res.get("phones", [])
    removable = res.get("removable_drives", [])
    fixed = res.get("fixed_drives", [])

    menu = tk.Menu(gui_instance, tearoff=0)

    # 1. Removable USB Drives
    if removable:
        menu.add_command(label="── 💾 REMOVABLE USB DRIVES ──", state="disabled")
        for drv in removable:
            name = f"💾 {drv.label} ({drv.path.rstrip('\\')}) — {drv.free_str}"
            sub = tk.Menu(menu, tearoff=0)
            sub.add_command(
                label="📂 Pick Folder on this Drive...",
                command=lambda p=drv.path: _menu_pick_folder(gui_instance, p)
            )
            sub.add_command(
                label="📄 Pick Files on this Drive...",
                command=lambda p=drv.path: _menu_pick_files(gui_instance, p)
            )
            sub.add_command(
                label=f"🎯 Select Entire Drive ({drv.path})",
                command=lambda p=drv.path: _menu_select_drive(gui_instance, p)
            )
            menu.add_cascade(label=name, menu=sub)

    # 2. Mobile Devices
    if phones:
        menu.add_command(label="── 📱 CONNECTED PHONES ──", state="disabled")
        for ph in phones:
            menu.add_command(
                label=f"📱 {ph.name} ({ph.type.value.upper()}) → Manage Media...",
                command=lambda: _menu_open_phone(gui_instance)
            )

    # 3. Local Partitions
    if fixed:
        menu.add_command(label="── 💻 LOCAL PARTITIONS ──", state="disabled")
        for drv in fixed:
            name = f"💻 {drv.label} ({drv.path.rstrip('\\')}) — {drv.free_str}"
            sub = tk.Menu(menu, tearoff=0)
            sub.add_command(
                label="📂 Pick Folder on this Drive...",
                command=lambda p=drv.path: _menu_pick_folder(gui_instance, p)
            )
            sub.add_command(
                label="📄 Pick Files on this Drive...",
                command=lambda p=drv.path: _menu_pick_files(gui_instance, p)
            )
            sub.add_command(
                label=f"🎯 Select Entire Drive ({drv.path})",
                command=lambda p=drv.path: _menu_select_drive(gui_instance, p)
            )
            menu.add_cascade(label=name, menu=sub)

    menu.add_separator()
    menu.add_command(
        label="🔌 Manage All Devices & External Storage...",
        command=lambda: open_connected_devices_dialog(gui_instance)
    )

    # Show menu below button
    try:
        x = source_button.winfo_rootx()
        y = source_button.winfo_rooty() + source_button.winfo_height()
        menu.post(x, y)
    except Exception:
        menu.post(200, 200)


def _menu_pick_folder(gui_instance, drive_path):
    folder = filedialog.askdirectory(
        initialdir=drive_path,
        title=f"Select Target Folder on {drive_path}",
        parent=gui_instance
    )
    if folder:
        gui_instance.selected_individual_files = []
        gui_instance.set_target_dir(folder)


def _menu_pick_files(gui_instance, drive_path):
    files = filedialog.askopenfilenames(
        initialdir=drive_path,
        title=f"Select Specific Files on {drive_path}",
        parent=gui_instance
    )
    if files:
        gui_instance.selected_individual_files = list(files)
        dir_name = os.path.dirname(files[0])
        gui_instance.dir_var.set(f"[Custom Selection] {len(files)} file(s) selected from {dir_name}")
        gui_instance.refresh_preview()


def _menu_select_drive(gui_instance, drive_path):
    gui_instance.selected_individual_files = []
    gui_instance.set_target_dir(drive_path)


def _menu_open_phone(gui_instance):
    try:
        from gui_modules.phone_dialog import open_phone_manager
        open_phone_manager(gui_instance)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to launch Phone Manager: {e}")
