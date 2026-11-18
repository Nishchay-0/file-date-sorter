"""
phone_dialog.py — USB Phone & Mobile Device Integration Dialog
Smart File Organizer Suite Pro

Provides an Apple Glassmorphism modal interface for:
- Detecting Android & iPhone mobile devices connected via USB (ADB & MTP)
- High-speed direct sorting on Android internal storage
- Automated phone-to-PC photo/video import & date organization
"""

import os
import threading
import tkinter as tk
from tkinter import messagebox

try:
    import customtkinter as ctk
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

from device_bridge import DeviceInfo, DeviceType, UnifiedDeviceManager

try:
    from gui_modules.theme_manager import GLASS, FONTS
    HAS_THEME = True
except ImportError:
    HAS_THEME = False


class PhoneManagerDialog(ctk.CTkToplevel if HAS_CTK else object):
    def __init__(self, parent_gui):
        if not HAS_CTK:
            return

        super().__init__()
        self.gui = parent_gui
        self.device_mgr = UnifiedDeviceManager()

        self.title("📱 USB Phone & Mobile Device Manager")
        self.geometry("680x620")
        self.minsize(580, 520)

        # Center on parent window
        self.after(10, self._center_window)

        self.detected_devices = []
        self.selected_device = None
        self.is_busy = False

        self._build_ui()
        self.rescan_devices()

    def _center_window(self):
        self.lift()
        self.focus_force()
        self.grab_set()

    def _build_ui(self):
        bg_card = GLASS["bg_card"] if HAS_THEME else ("gray90", "gray17")
        bg_card_alt = GLASS["bg_card_alt"] if HAS_THEME else ("gray85", "gray22")
        border = GLASS["border"] if HAS_THEME else ("gray75", "gray30")

        # ── Header Card ────────────────────────────────────────────────────────
        hdr_card = ctk.CTkFrame(self, corner_radius=12, fg_color=bg_card, border_color=border, border_width=1)
        hdr_card.pack(fill="x", padx=14, pady=(14, 8))

        ctk.CTkLabel(
            hdr_card,
            text="📱 Mobile Phone & USB Storage Organizer",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
        ).pack(side="left", padx=14, pady=12)

        self.rescan_btn = ctk.CTkButton(
            hdr_card,
            text="🔄 Rescan USB",
            command=self.rescan_devices,
            font=ctk.CTkFont(size=11, weight="bold"),
            height=28,
            width=100,
        )
        self.rescan_btn.pack(side="right", padx=14, pady=12)

        # ── Device Selection Card ──────────────────────────────────────────────
        dev_card = ctk.CTkFrame(self, corner_radius=12, fg_color=bg_card, border_color=border, border_width=1)
        dev_card.pack(fill="x", padx=14, pady=6)

        ctk.CTkLabel(
            dev_card,
            text="1. Connected Mobile Device:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(10, 4))

        self.device_combo = ctk.CTkComboBox(
            dev_card,
            values=["Searching for connected USB phones..."],
            command=self._on_device_selected,
            font=ctk.CTkFont(size=11),
            height=32,
        )
        self.device_combo.pack(fill="x", padx=14, pady=(0, 6))

        self.status_lbl = ctk.CTkLabel(
            dev_card,
            text="● Plug in your Android or iPhone via USB cable to begin.",
            font=ctk.CTkFont(size=10),
            text_color="gray60",
        )
        self.status_lbl.pack(anchor="w", padx=14, pady=(0, 10))

        # ── Operation Mode Tabs ────────────────────────────────────────────────
        self.tabview = ctk.CTkTabview(self, corner_radius=12, fg_color=bg_card, border_color=border, border_width=1)
        self.tabview.pack(fill="both", expand=True, padx=14, pady=6)

        tab_direct = self.tabview.add("⚡ Direct Sort on Phone (ADB)")
        tab_import = self.tabview.add("📥 Import & Sort to PC")

        # ── Tab 1: Direct Sort on Phone ────────────────────────────────────────
        ctk.CTkLabel(
            tab_direct,
            text="Organize files directly inside phone storage without copying to PC:",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(8, 4))

        folder_frame = ctk.CTkFrame(tab_direct, fg_color="transparent")
        folder_frame.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(folder_frame, text="Phone Folder:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 6))

        self.remote_folder_var = tk.StringVar(value="/sdcard/DCIM/Camera")
        self.remote_folder_combo = ctk.CTkComboBox(
            folder_frame,
            values=[
                "/sdcard/DCIM/Camera",
                "/sdcard/DCIM",
                "/sdcard/Download",
                "/sdcard/Pictures",
                "/sdcard/Documents",
            ],
            variable=self.remote_folder_var,
            width=260,
            font=ctk.CTkFont(size=11),
        )
        self.remote_folder_combo.pack(side="left", fill="x", expand=True)

        self.adb_dry_run_var = tk.BooleanVar(value=True)
        self.adb_dry_run_cb = ctk.CTkCheckBox(
            tab_direct,
            text="Preview Simulation (Dry Run) — test sort plan without moving files",
            variable=self.adb_dry_run_var,
            font=ctk.CTkFont(size=11),
        )
        self.adb_dry_run_cb.pack(anchor="w", padx=10, pady=8)

        self.btn_adb_sort = ctk.CTkButton(
            tab_direct,
            text="🚀 Execute Phone Organize",
            command=self._start_adb_organize,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#007AFF", "#0A84FF"),
            height=36,
        )
        self.btn_adb_sort.pack(fill="x", padx=10, pady=(6, 10))

        # ── Tab 2: Import & Sort to PC ─────────────────────────────────────────
        ctk.CTkLabel(
            tab_import,
            text="Transfer phone photos/media to PC and organize into Year/Month folders:",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(8, 4))

        dest_frame = ctk.CTkFrame(tab_import, fg_color="transparent")
        dest_frame.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(dest_frame, text="PC Destination:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 6))

        default_dest = os.path.join(os.path.expanduser("~"), "Pictures", "Phone_Organized")
        self.import_dest_var = tk.StringVar(value=default_dest)
        self.import_dest_entry = ctk.CTkEntry(
            dest_frame, textvariable=self.import_dest_var, font=ctk.CTkFont(size=11)
        )
        self.import_dest_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            dest_frame,
            text="Browse...",
            width=70,
            command=self._browse_import_dest,
            font=ctk.CTkFont(size=10),
        ).pack(side="right")

        self.delete_after_var = tk.BooleanVar(value=False)
        self.delete_after_cb = ctk.CTkCheckBox(
            tab_import,
            text="Free Phone Storage: Delete from phone after successful import to PC",
            variable=self.delete_after_var,
            font=ctk.CTkFont(size=11),
            text_color="#ef5350",
        )
        self.delete_after_cb.pack(anchor="w", padx=10, pady=8)

        self.btn_import = ctk.CTkButton(
            tab_import,
            text="📥 Start Phone Import & Sort",
            command=self._start_phone_import,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2e7d32",
            height=36,
        )
        self.btn_import.pack(fill="x", padx=10, pady=(6, 10))

        # ── Progress Bar & Real-Time Log ───────────────────────────────────────
        self.prog_bar = ctk.CTkProgressBar(self, height=10)
        self.prog_bar.pack(fill="x", padx=14, pady=(4, 2))
        self.prog_bar.set(0)

        self.log_box = ctk.CTkTextbox(self, height=110, font=ctk.CTkFont(family="Consolas", size=10))
        self.log_box.pack(fill="x", padx=14, pady=(2, 14))
        self.log("Ready. Connect your phone via USB cable.")

    def log(self, text: str):
        self.log_box.insert("end", f"{text}\n")
        self.log_box.see("end")

    def rescan_devices(self):
        self.log("Scanning for USB connected phones (ADB & MTP)...")
        self.rescan_btn.configure(state="disabled")

        def _scan():
            devs = self.device_mgr.scan_all_devices()
            self.after(0, lambda: self._on_scan_completed(devs))

        threading.Thread(target=_scan, daemon=True).start()

    def _on_scan_completed(self, devices):
        self.rescan_btn.configure(state="normal")
        self.detected_devices = devices

        if not devices:
            self.device_combo.configure(values=["No phones detected. Re-plug USB & tap 'File Transfer'."])
            self.device_combo.set("No phones detected. Re-plug USB & tap 'File Transfer'.")
            self.status_lbl.configure(
                text="⚠️ No phone found. Ensure USB cable is plugged in. For Android: enable USB Debugging or choose 'MTP/File Transfer'.",
                text_color="#ef5350",
            )
            self.selected_device = None
            self.log("No devices found.")
        else:
            names = [f"[{d.type.value.upper()}] {d.name}" for d in devices]
            self.device_combo.configure(values=names)
            self.device_combo.set(names[0])
            self.selected_device = devices[0]
            self.status_lbl.configure(
                text=f"● Device ready: {self.selected_device.name} (Status: {self.selected_device.status})",
                text_color="#4caf50",
            )
            self.log(f"Found {len(devices)} device(s): {names[0]}")

    def _on_device_selected(self, choice):
        for d in self.detected_devices:
            if d.name in choice:
                self.selected_device = d
                self.status_lbl.configure(text=f"● Selected: {d.name}", text_color="#4caf50")
                break

    def _browse_import_dest(self):
        from tkinter import filedialog

        d = filedialog.askdirectory(title="Select Destination Folder on PC", parent=self)
        if d:
            self.import_dest_var.set(d)

    def _start_adb_organize(self):
        if not self.selected_device:
            messagebox.showwarning("No Device", "Please connect and select a device first.", parent=self)
            return

        if self.selected_device.type != DeviceType.ADB:
            messagebox.showinfo(
                "MTP Notice",
                "Direct in-phone organizing is supported on ADB mode. For standard MTP, please use the 'Import & Sort to PC' tab.",
                parent=self,
            )
            return

        serial = self.selected_device.id
        remote_dir = self.remote_folder_var.get().strip()
        dry_run = self.adb_dry_run_var.get()

        self.btn_adb_sort.configure(state="disabled")
        self.log(f"Starting organize on {remote_dir} (Dry-run: {dry_run})...")

        def _run():
            def _prog(curr, total, fname):
                self.after(0, lambda: self._update_progress(curr, total, fname))

            res = self.device_mgr.organize_phone_folder_adb(
                serial, remote_dir, dry_run=dry_run, progress_callback=_prog
            )
            self.after(0, lambda: self._on_adb_organize_done(res))

        threading.Thread(target=_run, daemon=True).start()

    def _update_progress(self, curr, total, fname):
        if total > 0:
            pct = curr / total
            self.prog_bar.set(pct)
        self.log(f"[{curr}/{total}] {fname}")

    def _on_adb_organize_done(self, res):
        self.btn_adb_sort.configure(state="normal")
        self.prog_bar.set(1.0)
        total = res["total_files"]
        moved = res["moved_count"]
        dry_run = res["dry_run"]

        if dry_run:
            self.log(f"✓ Simulation complete! {total} files evaluated. 0 files modified.")
            messagebox.showinfo(
                "Dry Run Finished",
                f"Evaluation Complete!\n\nFound {total} files in phone folder.\nUncheck 'Preview Simulation' and click Execute to perform real moves on phone.",
                parent=self,
            )
        else:
            self.log(f"✓ Organize complete! {moved}/{total} files moved on phone.")
            messagebox.showinfo(
                "Organize Complete",
                f"Successfully organized {moved} files directly inside your phone's storage!",
                parent=self,
            )

    def _start_phone_import(self):
        if not self.selected_device:
            messagebox.showwarning("No Device", "Please connect and select a device first.", parent=self)
            return

        serial = self.selected_device.id
        remote_dir = self.remote_folder_var.get().strip()
        local_dest = self.import_dest_var.get().strip()
        del_phone = self.delete_after_var.get()

        self.btn_import.configure(state="disabled")
        self.log(f"Importing from phone [{remote_dir}] -> PC [{local_dest}]...")

        def _run():
            def _prog(curr, total, fname):
                self.after(0, lambda: self._update_progress(curr, total, fname))

            res = self.device_mgr.import_and_organize_to_pc(
                serial,
                remote_dir,
                local_dest,
                device_type=self.selected_device.type,
                delete_from_phone=del_phone,
                progress_callback=_prog,
            )
            self.after(0, lambda: self._on_import_done(res))

        threading.Thread(target=_run, daemon=True).start()

    def _on_import_done(self, res):
        self.btn_import.configure(state="normal")
        self.prog_bar.set(1.0)

        if "error" in res:
            self.log(f"❌ Error: {res['error']}")
            messagebox.showerror("Import Error", res["error"], parent=self)
            return

        imported = res.get("imported", 0)
        dest = res.get("local_directory", "")
        self.log(f"✓ Import complete! {imported} files safely organized to {dest}.")
        messagebox.showinfo(
            "Import Succeeded",
            f"Successfully imported and organized {imported} phone files into:\n{dest}",
            parent=self,
        )


def open_phone_manager(parent_gui):
    """
    Public entry point to launch the Phone Manager dialog.
    """
    return PhoneManagerDialog(parent_gui)
