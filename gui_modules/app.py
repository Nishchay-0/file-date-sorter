import os
import sys

# Ensure root workspace directory is in sys.path if app.py is run directly
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import threading
import subprocess
import shutil
import time
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from watcher_service import FolderWatcherService
from settings_manager import load_settings, save_settings

from gui_modules.components import (
    CTkToolTip,
    create_info_icon,
    get_user_folder,
    Windows11ConflictDialog,
    GRANULAR_FILE_TYPES
)

from gui_modules.views.tab_sorter import setup_organizer_tab
from gui_modules.views.tab_duplicates import setup_duplicates_tab
from gui_modules.views.tab_extractor import setup_extractor_tab
from gui_modules.views.tab_converter import setup_converter_tab
from gui_modules.views.tab_renamer import setup_renamer_tab
from gui_modules.views.tab_cleaner import setup_cleaner_tab
from gui_modules.views.tab_analytics import setup_insights_tab
from gui_modules.views.tab_watcher import setup_watcher_tab
from gui_modules.views.tab_exclusions import setup_exclusions_tab
from gui_modules.views.tab_people import setup_people_tab

from sorter_core import (
    organize_directory,
    scan_directory_preview,
    undo_manifest,
    find_duplicate_groups,
    delete_duplicate_files,
    move_duplicate_files,
    replace_duplicates_with_links,
    export_duplicates_report,
    format_bytes,
    list_manifest_files,
    scan_folder_extensions,
    clean_empty_dirs,
    batch_rename_files,
    get_file_date,
    get_file_category,
    scan_junk_and_large_files,
    scan_empty_dirs_preview,
    delete_empty_folder_batch,
    analyze_storage_insights,
    FolderWatcherService,
    fix_win_long_path,
    detect_file_format_by_magic,
    scan_converter_preview,
    run_converter_batch,
    get_system_vault_dir,
    gather_files,
    count_cloud_placeholders
)

try:
    import customtkinter as ctk
    HAS_CUSTOMTKINTER = True
except ImportError:
    HAS_CUSTOMTKINTER = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


if HAS_CUSTOMTKINTER:
    class StorageChartCanvas(ctk.CTkFrame):
        """Pure CustomTkinter visual bar chart component (No Matplotlib dependency needed)."""
        def __init__(self, master, **kwargs):
            super().__init__(master, **kwargs)
            self.bars_frame = ctk.CTkFrame(self, fg_color="transparent")
            self.bars_frame.pack(fill="both", expand=True, padx=8, pady=8)
            self.render_placeholder()

        def render_placeholder(self):
            for w in self.bars_frame.winfo_children():
                w.destroy()
            lbl = ctk.CTkLabel(self.bars_frame, text="📊 Live Category Disk Chart", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray60")
            lbl.pack(pady=15)

        def draw_chart(self, category_counts):
            for w in self.bars_frame.winfo_children():
                w.destroy()

            if not category_counts:
                self.render_placeholder()
                return

            total_files = sum(category_counts.values())
            if total_files == 0:
                self.render_placeholder()
                return

            hdr = ctk.CTkLabel(self.bars_frame, text="📊 File Category Distribution", font=ctk.CTkFont(size=11, weight="bold"))
            hdr.pack(anchor="w", pady=(0, 4))

            colors = ["#0288d1", "#7b1fa2", "#388e3c", "#f57c00", "#d32f2f", "#00838f", "#5d4037", "#455a64"]

            row = 0
            for cat, count in category_counts.items():
                if count <= 0:
                    continue
                pct = (count / total_files) * 100.0
                bar_row = ctk.CTkFrame(self.bars_frame, fg_color="transparent")
                bar_row.pack(fill="x", pady=2)
                bar_row.grid_columnconfigure(1, weight=1)

                ctk.CTkLabel(bar_row, text=f"{cat}:", font=ctk.CTkFont(size=10, weight="bold"), width=110, anchor="w").grid(row=0, column=0, sticky="w")

                prog = ctk.CTkProgressBar(bar_row, height=10, progress_color=colors[row % len(colors)])
                prog.set(pct / 100.0)
                prog.grid(row=0, column=1, sticky="ew", padx=6)

                ctk.CTkLabel(bar_row, text=f"{count} ({pct:.1f}%)", font=ctk.CTkFont(size=10), text_color="gray60", width=80, anchor="e").grid(row=0, column=2, sticky="e")
                row += 1

    class ModernFileDateSorterGUI(ctk.CTk):
        def __init__(self):
            super().__init__()

            try:
                from version import APP_NAME, VERSION
            except ImportError:
                APP_NAME = "Smart File Organizer Suite"
                VERSION = "1.0.0"

            self.title(f"{APP_NAME} v{VERSION}")

            # Apply Window Icon (.ico / .png)
            base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
            icon_ico = os.path.join(base_path, "assets", "icon.ico")
            if os.path.exists(icon_ico):
                try:
                    self.iconbitmap(icon_ico)
                except Exception:
                    pass

            # Responsive Screen-Optimized Window Geometry & Centered Placement
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()

            app_w = min(1420, max(960, int(screen_w * 0.86)))
            app_h = min(820, max(580, int(screen_h * 0.80)))

            pos_x = max(0, (screen_w - app_w) // 2)
            pos_y = max(0, (screen_h - app_h) // 2 - 15)

            self.geometry(f"{app_w}x{app_h}+{pos_x}+{pos_y}")
            self.minsize(920, 560)

            ctk.set_appearance_mode("Dark")
            ctk.set_default_color_theme("blue")

            if sys.platform == 'win32':
                try:
                    self.after(50, lambda: self.state('zoomed'))
                except Exception:
                    pass

            # Core Variables
            self.preview_data = []
            self.dup_groups = []
            self.dup_checkbox_vars = {}
            self.remembered_conflict_choice = None
            self.watcher_service = None
            self.selected_individual_files = []
            self.ext_selected_individual_files = []
            self.rename_preview_files = []
            self.dup_selected_individual_files = []
            self._thumb_cache = {}

            # Core Shared Tkinter State Variables (Initialized before UI tab setup)
            self.dir_var = tk.StringVar()
            self.dest_dir_var = tk.StringVar()
            self.dup_dir_var = tk.StringVar()
            self.dup_discard_dir_var = tk.StringVar()
            self.dup_dest_dir_var = tk.StringVar()
            self.dup_kept_mode_var = ctk.StringVar(value="📍 Leave in Original Location (Default)")
            self.ext_src_var = tk.StringVar()
            self.ext_dest_var = tk.StringVar()
            self.ren_dir_var = tk.StringVar()
            self.cln_dir_var = tk.StringVar()
            self.ins_dir_var = tk.StringVar()
            self.conv_src_var = tk.StringVar()
            self.conv_dest_var = tk.StringVar()
            self.exclude_folders_var = tk.StringVar(value=".git, node_modules")
            self.exclude_files_var = tk.StringVar(value="desktop.ini, .DS_Store, thumbs.db")
            self.exclude_ext_var = tk.StringVar(value=".tmp, .log, .bak, .crdownload, .part")
            self.include_ext_var = tk.StringVar()
            self.sort_category_var = ctk.StringVar(value="📅 Date (Creation / Mod / EXIF)")
            self.date_source_var = ctk.StringVar(value="ctime (Creation Date)")
            self.structure_var = ctk.StringVar(value="YYYY/MM (e.g. 2020/01)")
            self.conflict_mode_var = ctk.StringVar(value="🛡️ Skip Conflicts (Default)")
            self.skipped_handling_var = ctk.StringVar(value="📌 Leave in Original Location (Default)")
            self.custom_skipped_dest_var = tk.StringVar()
            self.enable_zip_backup_var = tk.BooleanVar(value=False)
            self.recursive_var = tk.BooleanVar(value=True)
            self.isolate_dup_var = tk.BooleanVar(value=False)
            self.dry_run_var = tk.BooleanVar(value=False)
            self.clean_empty_var = tk.BooleanVar(value=True)

            self.ext_filter_mode_var = ctk.StringVar(value="🎯 INCLUDE ONLY Selected File Types (Rest Untouched)")
            self.ext_custom_exts_var = tk.StringVar()
            self.ext_output_struct_var = ctk.StringVar(value="📂 Organize Into Category Folders (Images, Docs...)")
            self.ext_action_mode = ctk.StringVar(value="Move")
            self.ext_conflict_mode_var = ctk.StringVar(value="🛡️ Skip Conflicts (Default)")
            self.granular_checkbox_vars = {k: tk.BooleanVar(value=True) for k in GRANULAR_FILE_TYPES.keys()}
            self.ext_sub_vars = {}

            self._tabs_loaded = {
                "organizer": False,
                "duplicates": False,
                "extractor": False,
                "converter": False,
                "renamer": False,
                "cleaner": False,
                "insights": False,
                "watcher": False,
                "exclusions": False,
                "people": False
            }

            self.setup_ui()

        def dup_log(self, message, tag="info"):
            """Streams color-coded live execution logs into the Duplicate tab's real-time log console."""
            if not hasattr(self, 'dup_log_textbox') or not self.dup_log_textbox:
                return
            def _append():
                try:
                    tb = self.dup_log_textbox._textbox
                    tb.insert("end", message + "\n", tag)
                    tb.see("end")
                except Exception:
                    pass
            self.after(0, _append)

        def clear_dup_log(self):
            """Clears the Duplicate tab real-time log console."""
            if hasattr(self, 'dup_log_textbox') and self.dup_log_textbox:
                try:
                    self.dup_log_textbox._textbox.delete("1.0", "end")
                except Exception:
                    pass

        def load_file_thumbnail(self, file_path, target_size=(220, 120)):
            if not HAS_PIL:
                return None
            safe_p = fix_win_long_path(file_path)
            cache_key = f"{safe_p}_{target_size[0]}x{target_size[1]}"
            if cache_key in self._thumb_cache:
                return self._thumb_cache[cache_key]
            try:
                ext = os.path.splitext(file_path)[1].lower()
                VID_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.vob', '.ts', '.m2ts', '.divx', '.mpg', '.mpeg'}
                if ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff']:
                    with Image.open(safe_p) as img:
                        img_copy = img.copy()
                        if img_copy.mode != 'RGBA' and (img_copy.mode in ('P', 'PA', 'LA', '1', 'L') or 'transparency' in img.info):
                            img_copy = img_copy.convert('RGBA')
                        resample_filter = getattr(Image.Resampling, 'LANCZOS', getattr(Image, 'ANTIALIAS', Image.BICUBIC))
                        img_copy.thumbnail(target_size, resample_filter)
                        ctk_img = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=img_copy.size)
                        self._thumb_cache[cache_key] = ctk_img
                        return ctk_img
                elif ext in VID_EXTS:
                    import cv2
                    cap = cv2.VideoCapture(safe_p)
                    if cap.isOpened():
                        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
                        target_frame = int(total_frames * 0.15)
                        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                        ret, frame = cap.read()
                        if not ret:
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            ret, frame = cap.read()
                        cap.release()
                        if ret and frame is not None:
                            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            pil_img = Image.fromarray(rgb_frame)
                            resample_filter = getattr(Image.Resampling, 'LANCZOS', getattr(Image, 'ANTIALIAS', Image.BICUBIC))
                            pil_img.thumbnail(target_size, resample_filter)
                            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                            self._thumb_cache[cache_key] = ctk_img
                            return ctk_img
            except Exception:
                pass
            return None

        def load_file_thumbnail_async(self, file_path, target_size=(220, 120), label_widget=None, filename=""):
            """Loads image and video thumbnails asynchronously in background worker threads without freezing the main UI."""
            if not HAS_PIL or not label_widget:
                return

            safe_p = fix_win_long_path(file_path)
            cache_key = f"{safe_p}_{target_size[0]}x{target_size[1]}"

            if cache_key in self._thumb_cache:
                try:
                    label_widget.configure(image=self._thumb_cache[cache_key], text="")
                except Exception:
                    pass
                return

            def background_worker():
                ctk_img = None
                try:
                    ext = os.path.splitext(file_path)[1].lower()
                    VID_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.vob', '.ts', '.m2ts', '.divx', '.mpg', '.mpeg'}
                    if ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff']:
                        with Image.open(safe_p) as img:
                            img_copy = img.copy()
                            if img_copy.mode != 'RGBA' and (img_copy.mode in ('P', 'PA', 'LA', '1', 'L') or 'transparency' in img.info):
                                img_copy = img_copy.convert('RGBA')
                            resample_filter = getattr(Image.Resampling, 'LANCZOS', getattr(Image, 'ANTIALIAS', Image.BICUBIC))
                            img_copy.thumbnail(target_size, resample_filter)
                            ctk_img = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=img_copy.size)
                            self._thumb_cache[cache_key] = ctk_img
                    elif ext in VID_EXTS:
                        import cv2
                        cap = cv2.VideoCapture(safe_p)
                        if cap.isOpened():
                            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
                            target_frame = int(total_frames * 0.15)
                            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                            ret, frame = cap.read()
                            if not ret:
                                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                                ret, frame = cap.read()
                            cap.release()
                            if ret and frame is not None:
                                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                pil_img = Image.fromarray(rgb_frame)
                                resample_filter = getattr(Image.Resampling, 'LANCZOS', getattr(Image, 'ANTIALIAS', Image.BICUBIC))
                                pil_img.thumbnail(target_size, resample_filter)
                                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                                self._thumb_cache[cache_key] = ctk_img
                except Exception:
                    ctk_img = None

                def update_ui():
                    try:
                        if ctk_img:
                            label_widget.configure(image=ctk_img, text="")
                        else:
                            ext_str = os.path.splitext(filename or file_path)[1].upper()
                            icon_symbol = "🎬" if ext.lower() in {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.vob'} else "📄"
                            label_widget.configure(text=f"{icon_symbol}\n{ext_str if ext_str else 'FILE'}", font=ctk.CTkFont(size=14, weight="bold"))
                    except Exception:
                        pass

                self.after(0, update_ui)

            import threading
            threading.Thread(target=background_worker, daemon=True).start()

        def browse_dup_discard_folder(self):
            folder = filedialog.askdirectory(title="Select Discard / Quarantine Folder for Unkept Duplicate Files")
            if folder:
                self.dup_discard_dir_var.set(folder)

        def browse_dup_dest_folder(self):
            folder = filedialog.askdirectory(title="Select Custom Destination Folder for Kept Files")
            if folder:
                self.dup_dest_dir_var.set(folder)
                if hasattr(self, 'dup_kept_mode_var'):
                    self.dup_kept_mode_var.set("custom")
                self.status_var.set(f"📁 Custom Keep Folder set: '{os.path.basename(folder)}'")

        def reset_dup_dest_folder(self):
            self.dup_dest_dir_var.set("")
            if hasattr(self, 'dup_kept_mode_var'):
                self.dup_kept_mode_var.set("original")
            self.status_var.set("📍 Kept files mode reset to Default (Original Location).")

        def open_backup_vault_explorer(self):
            vault_path = get_system_vault_dir()
            if os.path.exists(vault_path):
                if sys.platform == 'win32':
                    os.startfile(vault_path)
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', vault_path])
                else:
                    subprocess.Popen(['xdg-open', vault_path])

        def open_restore_manager(self):
            self.open_system_vault_restore_manager()

        def setup_ui(self):
            # Top Banner Card
            top_card = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray85", "gray18"))
            top_card.pack(fill="x", padx=10, pady=(6, 3), ipadx=6, ipady=3)
            top_card.grid_columnconfigure(0, weight=1)

            title_frame = ctk.CTkFrame(top_card, fg_color="transparent")
            title_frame.grid(row=0, column=0, sticky="w", padx=10)

            title_lbl = ctk.CTkLabel(
                title_frame,
                text="📁 Smart File Organizer Suite Pro v4.0",
                font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
            )
            title_lbl.pack(side="left")

            badge = ctk.CTkLabel(
                title_frame,
                text="  Windows 11 Certified  ",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="#0288d1",
                text_color="white",
                corner_radius=6
            )
            badge.pack(side="left", padx=8)

            sub_lbl = ctk.CTkLabel(
                top_card,
                text="Zero-Deletion Guarantee • EXIF Camera Support • Windows 11 Side-by-Side Conflict Resolver • Multi-Folder Extraction",
                font=ctk.CTkFont(size=10),
                text_color="gray60"
            )
            sub_lbl.grid(row=1, column=0, sticky="w", padx=10, pady=(1, 0))

            theme_box = ctk.CTkFrame(top_card, fg_color="transparent")
            theme_box.grid(row=0, column=1, rowspan=2, sticky="e", padx=10)

            self.theme_switch = ctk.CTkSwitch(
                theme_box,
                text="🌙 Dark Mode",
                command=self.toggle_theme,
                font=ctk.CTkFont(size=10, weight="bold")
            )
            self.theme_switch.select()
            self.theme_switch.pack(side="right")

            # Main Card Container
            main_card = ctk.CTkFrame(self, corner_radius=12)
            main_card.pack(fill="both", expand=True, padx=10, pady=(0, 4))

            # 9-Tab Navigation View
            self.tabview = ctk.CTkTabview(main_card, corner_radius=10, command=self._on_tab_changed)
            self.tabview.pack(fill="both", expand=True, padx=4, pady=4)

            self.tab_organizer = self.tabview.add("📅 File Organizer")
            self.tab_duplicates = self.tabview.add("🔍 Duplicates Finder")
            self.tab_people = self.tabview.add("👥 People Sorter")
            self.tab_extractor = self.tabview.add("📦 Subfolder Extractor")
            self.tab_converter = self.tabview.add("🪄 Magic Converter")
            self.tab_renamer = self.tabview.add("🏷️ Bulk Renamer")
            self.tab_cleaner = self.tabview.add("🧹 Storage Cleaner")
            self.tab_insights = self.tabview.add("📊 Analytics")
            self.tab_watcher = self.tabview.add("👁️ Auto Watcher")
            self.tab_exclusions = self.tabview.add("🚫 Exclusions")

            self.StorageChartCanvas = StorageChartCanvas

            # LAZY LOADING: Load ONLY Tab 1 initially for lightning-fast startup!
            setup_organizer_tab(self)
            self._tabs_loaded["organizer"] = True

            # Auto-set target directory if launched via CLI or Windows Explorer Right-Click Context Menu
            if len(sys.argv) > 1:
                arg_target = sys.argv[1].strip().strip('"')
                if arg_target and os.path.exists(fix_win_long_path(arg_target)):
                    if os.path.isfile(fix_win_long_path(arg_target)):
                        self.selected_individual_files = [arg_target]
                        dir_name = os.path.dirname(arg_target)
                        self.dir_var.set(f"[Custom Selection] 1 file selected from {dir_name}")
                    else:
                        self.set_target_dir(arg_target)

            # Bottom Status Bar
            status_card = ctk.CTkFrame(self, height=32, corner_radius=8)
            status_card.pack(fill="x", padx=15, pady=(0, 10))

            self.status_var = tk.StringVar(value="Ready. Select target folder or pick specific files to begin.")
            self.status_lbl = ctk.CTkLabel(status_card, textvariable=self.status_var, font=ctk.CTkFont(size=11), anchor="w")
            self.status_lbl.pack(side="left", padx=12, fill="x", expand=True)

        def _atomic_repaint_tab_widgets(self, tab_container=None):
            """
            MASTER ATOMIC VISUAL STATE RE-ASSERTION ENGINE:
            Forces all CTkCheckBoxes, CTkFrames, and CTkLabels in the active tab to
            re-draw atomically with full width and height, preventing transient 1px collapse
            slivers or desynced canvas checkboxes upon tab switches or scrolling!
            """
            if not tab_container:
                try:
                    current_tab_name = self.tabview.get()
                    tab_container = self.tabview.tab(current_tab_name)
                except Exception:
                    return

            def _atomic_repaint_recursive(widget):
                try:
                    # If widget is a CTkCheckBox, force update_idletasks and _draw()
                    if isinstance(widget, ctk.CTkCheckBox):
                        try:
                            if hasattr(widget, '_variable') and widget._variable is not None:
                                val = widget._variable.get()
                                if hasattr(widget, '_check_state') and widget._check_state != bool(val):
                                    widget._check_state = bool(val)
                            widget.update_idletasks()
                            if hasattr(widget, '_draw'):
                                widget._draw()
                        except Exception:
                            pass
                    
                    for child in widget.winfo_children():
                        _atomic_repaint_recursive(child)
                except Exception:
                    pass

            try:
                tab_container.update_idletasks()
                _atomic_repaint_recursive(tab_container)
            except Exception:
                pass

        def _on_tab_changed(self, tab_name=None):
            current = tab_name if tab_name else self.tabview.get()

            if "Organizer" in current and not self._tabs_loaded["organizer"]:
                setup_organizer_tab(self)
                self._tabs_loaded["organizer"] = True
            elif "Duplicates" in current and not self._tabs_loaded["duplicates"]:
                setup_duplicates_tab(self)
                self._tabs_loaded["duplicates"] = True
            elif "People" in current and not self._tabs_loaded.get("people"):
                setup_people_tab(self)
                self._tabs_loaded["people"] = True
            elif "Extractor" in current and not self._tabs_loaded["extractor"]:
                setup_extractor_tab(self)
                self._tabs_loaded["extractor"] = True
            elif "Converter" in current and not self._tabs_loaded["converter"]:
                setup_converter_tab(self)
                self._tabs_loaded["converter"] = True
            elif "Renamer" in current and not self._tabs_loaded["renamer"]:
                setup_renamer_tab(self)
                self._tabs_loaded["renamer"] = True
            elif "Cleaner" in current and not self._tabs_loaded["cleaner"]:
                setup_cleaner_tab(self)
                self._tabs_loaded["cleaner"] = True
            elif "Analytics" in current and not self._tabs_loaded["insights"]:
                setup_insights_tab(self)
                self._tabs_loaded["insights"] = True
            elif "Watcher" in current and not self._tabs_loaded["watcher"]:
                setup_watcher_tab(self)
                self._tabs_loaded["watcher"] = True
            elif "Exclusions" in current and not self._tabs_loaded["exclusions"]:
                setup_exclusions_tab(self)
                self._tabs_loaded["exclusions"] = True

            # Atomic Visual State Re-assertion
            self.after(50, lambda: self._atomic_repaint_tab_widgets())

        def _on_watcher_notify(self, message):
            if hasattr(self, 'dup_log'):
                self.dup_log(message, tag="info")
            if hasattr(self, 'status_var'):
                self.status_var.set(message)
            self._update_watcher_stats_ui()

        def browse_wtc_folder(self):
            folder = filedialog.askdirectory(title="Select Folder to Watch")
            if folder:
                if hasattr(self, 'wtc_dir_var'):
                    self.wtc_dir_var.set(folder)

        def toggle_watcher_switch(self):
            if getattr(self, 'wtc_switch_var', tk.BooleanVar()).get():
                self.start_watcher_service()
            else:
                self.stop_watcher_service()

        def start_watcher_service(self):
            folder = getattr(self, 'wtc_dir_var', tk.StringVar()).get().strip()
            if not folder or not os.path.exists(folder):
                messagebox.showerror("Error", "Please select a valid folder to watch.")
                if hasattr(self, 'wtc_switch_var'):
                    self.wtc_switch_var.set(False)
                return

            cat = getattr(self, 'wtc_sort_category_var', ctk.StringVar()).get()
            try:
                deb = float(getattr(self, 'wtc_debounce_var', tk.StringVar()).get())
            except ValueError:
                deb = 3.0

            try:
                if not self.watcher_service:
                    self.watcher_service = FolderWatcherService(callback_notify=self._on_watcher_notify)

                self.watcher_service.start_watching(
                    folder_path=folder,
                    sort_category=cat,
                    date_source="ctime",
                    structure_format="YYYY/MM",
                    debounce_seconds=deb
                )
                if hasattr(self, 'wtc_status_lbl') and self.wtc_status_lbl:
                    self.wtc_status_lbl.configure(text=f"Status: 🟢 Active Watching '{os.path.basename(folder)}'", text_color="#81c784")
                if hasattr(self, 'wtc_switch_var'):
                    self.wtc_switch_var.set(True)
                self._update_watcher_stats_ui()
            except Exception as ex:
                messagebox.showerror("Watcher Error", f"Failed to start folder watcher: {ex}")
                if hasattr(self, 'wtc_switch_var'):
                    self.wtc_switch_var.set(False)

        def stop_watcher_service(self):
            if self.watcher_service:
                self.watcher_service.stop_watching()
            if hasattr(self, 'wtc_status_lbl') and self.wtc_status_lbl:
                self.wtc_status_lbl.configure(text="Status: 🔴 Service Stopped", text_color="#e57373")
            if hasattr(self, 'wtc_switch_var'):
                self.wtc_switch_var.set(False)
            self._update_watcher_stats_ui()

        def _update_watcher_stats_ui(self):
            if not hasattr(self, 'wtc_stats_files_lbl') or not self.wtc_stats_files_lbl:
                return
            count = self.watcher_service.files_organized_count if self.watcher_service else 0
            folder = self.watcher_service.watched_folder if (self.watcher_service and self.watcher_service.is_running) else "None"
            self.wtc_stats_files_lbl.configure(text=f"Files Auto-Organized This Session: {count}")
            self.wtc_stats_active_folder_lbl.configure(text=f"Watched Target Folder: {folder}")

        def populate_tree_in_chunks(self, tree, rows, chunk_size=300, current_idx=0):
            """Inserts treeview rows in non-blocking UI chunks to prevent freezing with large datasets."""
            if current_idx == 0:
                for item in tree.get_children():
                    tree.delete(item)

            end_idx = min(current_idx + chunk_size, len(rows))
            for i in range(current_idx, end_idx):
                tree.insert("", "end", values=rows[i])

            if end_idx < len(rows):
                self.after(10, self.populate_tree_in_chunks, tree, rows, chunk_size, end_idx)

        # Delegates to handlers defined in view / core modules
        def browse_individual_files(self):
            files = filedialog.askopenfilenames(title="Select Specific Files to Organize")
            if files:
                self.selected_individual_files = list(files)
                dir_name = os.path.dirname(files[0])
                self.dir_var.set(f"[Custom Selection] {len(files)} file(s) selected from {dir_name}")
                self.refresh_preview()

        def browse_folder(self):
            selected_dir = filedialog.askdirectory(title="Select Target Folder to Organize")
            if selected_dir:
                self.selected_individual_files = []
                self.set_target_dir(selected_dir)

        # --- CONVERTER HANDLERS ---
        def browse_conv_folder(self):
            folder = filedialog.askdirectory(title="Select Folder Containing Files to Convert")
            if folder:
                self.conv_src_var.set(folder)
                self.refresh_converter_preview()

        def browse_conv_files(self):
            files = filedialog.askopenfilenames(title="Select Specific Files to Convert")
            if files:
                self.conv_selected_files = list(files)
                dir_name = os.path.dirname(files[0])
                self.conv_src_var.set(f"[Custom Selection] {len(files)} file(s) selected from {dir_name}")
                self.refresh_converter_preview()

        def browse_conv_dest(self):
            folder = filedialog.askdirectory(title="Select Export Folder for Converted Files")
            if folder:
                self.conv_dest_var.set(folder)
                self.refresh_converter_preview()

        def refresh_converter_preview(self):
            src_dir = getattr(self, "conv_src_var", tk.StringVar()).get().strip()
            dest_dir = getattr(self, "conv_dest_var", tk.StringVar()).get().strip()
            mode = getattr(self, "conv_mode_var", tk.StringVar()).get()
            selected_files = getattr(self, "conv_selected_files", None)

            if not selected_files and not src_dir:
                return

            exc_folds = self.parse_comma_list(self.exclude_folders_var.get().strip())
            exc_files = self.parse_comma_list(self.exclude_files_var.get().strip())
            exc_exts = self.parse_comma_list(self.exclude_ext_var.get().strip())

            self.conv_stats_lbl.configure(text="⏳ Scanning directory & checking magic byte headers in background...")

            def worker():
                try:
                    preview_items, summary = scan_converter_preview(
                        src_dir=src_dir if src_dir else None,
                        conv_mode=mode,
                        dest_dir=dest_dir if dest_dir else None,
                        selected_files=selected_files,
                        exclude_folders=exc_folds,
                        exclude_files=exc_files,
                        exclude_exts=exc_exts
                    )

                    def update_ui():
                        self.conv_preview_items = preview_items
                        rows = [(
                            item['filename'],
                            item['rel_path'],
                            item['detected_format'],
                            item['action'],
                            item['target_name'],
                            item['size_str']
                        ) for item in preview_items]

                        self.populate_tree_in_chunks(self.conv_tree, rows, chunk_size=300)
                        self.conv_stats_lbl.configure(
                            text=f"Preview: {summary['convertible_count']} file(s) ready for conversion ({summary['total_size_str']})."
                        )

                    self.after(0, update_ui)
                except Exception:
                    pass

            threading.Thread(target=worker, daemon=True).start()

        def start_converter_execution(self):
            items = getattr(self, "conv_preview_items", [])
            if not items:
                messagebox.showwarning("No Convertible Files", "No files ready for conversion in the current selection.")
                return

            dest_dir = self.conv_dest_var.get().strip()
            delete_orig = self.conv_delete_orig_var.get()
            raw_workers = getattr(self, "conv_threads_var", tk.StringVar()).get()
            workers = 1
            if "2" in raw_workers: workers = 2
            elif "4" in raw_workers: workers = 4
            elif "8" in raw_workers: workers = 8

            if delete_orig:
                if not messagebox.askyesno("Confirm Original File Deletion", "WARNING: You checked 'Delete Original Files After Successful Conversion'.\n\nOriginal files will be permanently deleted after converting. Continue?"):
                    return

            self.conv_start_btn.configure(state="disabled")
            self.conv_progress_bar.set(0)

            def run_conv_thread():
                try:
                    stats = run_converter_batch(
                        preview_items=items,
                        output_dir=dest_dir if dest_dir else None,
                        delete_original=delete_orig,
                        progress_callback=lambda c, t, fp, msg, tag: self.after(0, self.update_conv_progress, c, t, fp, msg),
                        max_workers=workers
                    )

                    def finished():
                        self.conv_start_btn.configure(state="normal")
                        self.status_var.set("Converter execution finished!")
                        converted_count = stats.get('processed', stats.get('converted', 0))
                        skipped_count = stats.get('skipped_corrupt', stats.get('skipped', 0))
                        error_count = stats.get('errors', 0)
                        messagebox.showinfo(
                            "Conversion Complete",
                            f"Successfully Converted: {converted_count}\n"
                            f"Skipped / Unchanged:  {skipped_count}\n"
                            f"Errors Encountered:    {error_count}"
                        )
                        self.refresh_converter_preview()

                    self.after(0, finished)
                except Exception as e:
                    def on_err(err_msg):
                        self.conv_start_btn.configure(state="normal")
                        messagebox.showerror("Converter Error", err_msg)

                    self.after(0, on_err, str(e))

            threading.Thread(target=run_conv_thread, daemon=True).start()

        def update_conv_progress(self, current, total, file_path, status_msg):
            pct = (current / total) if total > 0 else 1.0
            self.conv_progress_bar.set(pct)
            fname = os.path.basename(file_path)
            self.status_var.set(f"Converting ({current}/{total}): {fname} - {status_msg}")

        # --- INCLUDE ALL ORGANIZER, RENAMER, CLEANER & EXTRACTOR DELEGATE METHODS ---
        def browse_ext_src(self):
            folder = filedialog.askdirectory(title="Select Source Folder to Extract From")
            if folder:
                self.ext_selected_individual_files = []
                self.ext_src_var.set(folder)
                self.refresh_extractor_preview()

        def browse_ext_dest(self):
            folder = filedialog.askdirectory(title="Select Output Folder for Extracted Files")
            if folder:
                self.ext_dest_var.set(folder)
                self.refresh_extractor_preview()

        def browse_ext_individual_files(self):
            files = filedialog.askopenfilenames(title="Select Specific Files to Extract")
            if files:
                self.ext_selected_individual_files = list(files)
                dir_name = os.path.dirname(files[0])
                self.ext_src_var.set(f"[Custom Selection] {len(files)} file(s) selected from {dir_name}")
                self.refresh_extractor_preview()

        def preset_only_pdf(self):
            self._suppress_preview_updates = True
            try:
                self.ext_filter_mode_var.set("🎯 INCLUDE ONLY Selected File Types (Rest Untouched)")
                for type_lbl, var in self.granular_checkbox_vars.items():
                    val = "PDF" in type_lbl
                    var.set(val)
                    self._sync_sub_from_cat(type_lbl)
            finally:
                self._suppress_preview_updates = False
            self.refresh_extractor_preview()

        def preset_only_office_docs(self):
            self._suppress_preview_updates = True
            try:
                self.ext_filter_mode_var.set("🎯 INCLUDE ONLY Selected File Types (Rest Untouched)")
                for type_lbl, var in self.granular_checkbox_vars.items():
                    val = any(k in type_lbl for k in ["PDF", "Word", "Excel", "PowerPoint", "Text"])
                    var.set(val)
                    self._sync_sub_from_cat(type_lbl)
            finally:
                self._suppress_preview_updates = False
            self.refresh_extractor_preview()

        def preset_only_media(self):
            self._suppress_preview_updates = True
            try:
                self.ext_filter_mode_var.set("🎯 INCLUDE ONLY Selected File Types (Rest Untouched)")
                for type_lbl, var in self.granular_checkbox_vars.items():
                    val = any(k in type_lbl for k in ["Photos", "Videos"])
                    var.set(val)
                    self._sync_sub_from_cat(type_lbl)
            finally:
                self._suppress_preview_updates = False
            self.refresh_extractor_preview()

        def preset_except_media(self):
            self._suppress_preview_updates = True
            try:
                self.ext_filter_mode_var.set("🚫 EXCLUDE (Except) Selected File Types")
                for type_lbl, var in self.granular_checkbox_vars.items():
                    val = any(k in type_lbl for k in ["Photos", "Videos"])
                    var.set(val)
                    self._sync_sub_from_cat(type_lbl)
            finally:
                self._suppress_preview_updates = False
            self.refresh_extractor_preview()

        def preset_clear_extractor_checkboxes(self):
            self._suppress_preview_updates = True
            try:
                for type_lbl, var in self.granular_checkbox_vars.items():
                    var.set(False)
                    self._sync_sub_from_cat(type_lbl)
                self.ext_custom_exts_var.set("")
            finally:
                self._suppress_preview_updates = False
            self.refresh_extractor_preview()

        def _sync_sub_from_cat(self, cat_label):
            cat_val = self.granular_checkbox_vars[cat_label].get()
            for ext in GRANULAR_FILE_TYPES.get(cat_label, []):
                if ext in self.ext_sub_vars:
                    self.ext_sub_vars[ext].set(cat_val)

        def _sync_cat_from_subs(self, cat_label):
            exts = GRANULAR_FILE_TYPES.get(cat_label, [])
            checked = [self.ext_sub_vars[e].get() for e in exts if e in self.ext_sub_vars]
            if all(checked):
                self.granular_checkbox_vars[cat_label].set(True)
            elif any(checked):
                self.granular_checkbox_vars[cat_label].set(True)
            else:
                self.granular_checkbox_vars[cat_label].set(False)

        def _sub_select_all(self, cat_label):
            self._suppress_preview_updates = True
            try:
                for ext in GRANULAR_FILE_TYPES.get(cat_label, []):
                    if ext in self.ext_sub_vars:
                        self.ext_sub_vars[ext].set(True)
                self.granular_checkbox_vars[cat_label].set(True)
            finally:
                self._suppress_preview_updates = False
            self.refresh_extractor_preview()

        def _sub_select_none(self, cat_label):
            self._suppress_preview_updates = True
            try:
                for ext in GRANULAR_FILE_TYPES.get(cat_label, []):
                    if ext in self.ext_sub_vars:
                        self.ext_sub_vars[ext].set(False)
                self.granular_checkbox_vars[cat_label].set(False)
            finally:
                self._suppress_preview_updates = False
            self.refresh_extractor_preview()

        def extractor_select_all_cats(self):
            self._suppress_preview_updates = True
            try:
                for type_lbl, var in self.granular_checkbox_vars.items():
                    var.set(True)
                    self._sync_sub_from_cat(type_lbl)
            finally:
                self._suppress_preview_updates = False
            self.refresh_extractor_preview()

        def extractor_clear_all_cats(self):
            self._suppress_preview_updates = True
            try:
                for type_lbl, var in self.granular_checkbox_vars.items():
                    var.set(False)
                    self._sync_sub_from_cat(type_lbl)
            finally:
                self._suppress_preview_updates = False
            self.refresh_extractor_preview()

        def extractor_invert_cats(self):
            self._suppress_preview_updates = True
            try:
                for type_lbl, var in self.granular_checkbox_vars.items():
                    var.set(not var.get())
                    self._sync_sub_from_cat(type_lbl)
            finally:
                self._suppress_preview_updates = False
            self.refresh_extractor_preview()

        def on_extractor_filter_mode_changed(self, choice=None):
            self.refresh_extractor_preview()

        def get_extractor_filter_params(self):
            mode = self.ext_filter_mode_var.get()
            selected_exts = set()

            all_cats_checked = True
            for type_lbl, cat_var in self.granular_checkbox_vars.items():
                if not cat_var.get():
                    all_cats_checked = False
                else:
                    cat_exts = GRANULAR_FILE_TYPES.get(type_lbl, [])
                    sub_vars = getattr(self, "ext_sub_vars", {})
                    has_sub_vars = any(e in sub_vars for e in cat_exts)
                    if has_sub_vars:
                        for ext in cat_exts:
                            sv = sub_vars.get(ext)
                            if not sv or sv.get():
                                selected_exts.add(ext)
                            else:
                                all_cats_checked = False
                    else:
                        selected_exts.update(cat_exts)

            custom_raw = self.ext_custom_exts_var.get().strip()
            if custom_raw:
                c_list = self.parse_comma_list(custom_raw)
                for c_ext in c_list:
                    if not c_ext.startswith('.'):
                        c_ext = '.' + c_ext
                    selected_exts.add(c_ext.lower())

            inc_exts = None
            exc_exts = None

            if "EXCLUDE" in mode:
                exc_exts = list(selected_exts) if selected_exts else None
            elif "INCLUDE ONLY" in mode or "Custom" in mode:
                if all_cats_checked and not custom_raw:
                    inc_exts = None
                else:
                    inc_exts = list(selected_exts) if selected_exts else None

            return inc_exts, exc_exts

        def open_custom_ext_detector(self):
            src_dir = self.ext_src_var.get().strip()
            selected_files = self.ext_selected_individual_files if self.ext_selected_individual_files else None

            if not selected_files and (not src_dir or not os.path.isdir(fix_win_long_path(src_dir))):
                messagebox.showwarning("No Location Selected", "Please select a target folder or pick files first to auto-detect file extensions!")
                return

            exc_folds = self.parse_comma_list(self.exclude_folders_var.get().strip())
            exc_files = self.parse_comma_list(self.exclude_files_var.get().strip())
            exc_exts = self.parse_comma_list(self.exclude_ext_var.get().strip())

            detected = scan_folder_extensions(
                main_folder=src_dir if src_dir else None,
                selected_files=selected_files,
                include_system=False,
                exclude_folders=exc_folds,
                exclude_files=exc_files,
                exclude_exts=exc_exts
            )

            if not detected:
                messagebox.showinfo("No User Files Found", "No user file formats were detected in the selected location.")
                return

            win = ctk.CTkToplevel(self)
            win.title("🔍 Auto-Detected File Types & Extension Selector")
            win.geometry("680x580")
            win.transient(self)
            win.grab_set()
            win.after(100, lambda: (win.lift(), win.focus_force()))

            hdr = ctk.CTkFrame(win, corner_radius=10, fg_color=("gray90", "gray18"))
            hdr.pack(fill="x", padx=15, pady=(12, 6), ipadx=8, ipady=6)
            
            hdr_lbl = ctk.CTkLabel(hdr, text=f"🔍 Found {len(detected)} Unique File Extension(s) in Folder", font=ctk.CTkFont(size=13, weight="bold"))
            hdr_lbl.pack(anchor="w", padx=8)
            ctk.CTkLabel(hdr, text="Tick the file extensions you want to process or extract (System/OS files are hidden):", font=ctk.CTkFont(size=11), text_color="gray60").pack(anchor="w", padx=8)

            tool_frame = ctk.CTkFrame(win, fg_color="transparent")
            tool_frame.pack(fill="x", padx=15, pady=(0, 6))

            chk_vars = {}
            chk_widgets = {}
            existing_custom = set(self.parse_comma_list(self.ext_custom_exts_var.get().strip()))

            filter_var = tk.StringVar()
            filter_entry = ctk.CTkEntry(tool_frame, textvariable=filter_var, placeholder_text="🔍 Filter exts...", font=ctk.CTkFont(size=11), height=28, width=200)
            filter_entry.pack(side="left", padx=(0, 10))

            def select_all():
                for v in chk_vars.values():
                    v.set(True)

            def select_none():
                for v in chk_vars.values():
                    v.set(False)

            def invert_all():
                for v in chk_vars.values():
                    v.set(not v.get())

            ctk.CTkButton(tool_frame, text="☑ Select All", command=select_all, font=ctk.CTkFont(size=10, weight="bold"), height=26, width=85, fg_color="#0288d1").pack(side="left", padx=(0, 4))
            ctk.CTkButton(tool_frame, text="☐ Clear All", command=select_none, font=ctk.CTkFont(size=10), height=26, width=75, fg_color=("gray75", "gray32"), text_color=("gray10", "gray90")).pack(side="left", padx=(0, 4))
            ctk.CTkButton(tool_frame, text="⇄ Invert", command=invert_all, font=ctk.CTkFont(size=10), height=26, width=65, fg_color=("gray75", "gray32"), text_color=("gray10", "gray90")).pack(side="left")

            scroll = ctk.CTkScrollableFrame(win, corner_radius=10)
            scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))
            scroll.grid_columnconfigure(0, weight=1)
            scroll.grid_columnconfigure(1, weight=1)

            col_i = 0
            row_i = 0
            for item in detected:
                ext = item['ext']
                cnt = item['count']
                sz_str = item['size_str']
                cat = item['category']

                is_prechecked = False
                try:
                    if ext in existing_custom:
                        is_prechecked = True
                    elif ext in getattr(self, "ext_sub_vars", {}):
                        v_obj = self.ext_sub_vars[ext]
                        if hasattr(v_obj, "get"):
                            is_prechecked = bool(v_obj.get())
                except Exception:
                    is_prechecked = False

                var = tk.BooleanVar(value=is_prechecked)
                chk_vars[ext] = var

                label_text = f"{ext}  ({cnt} file{'s' if cnt > 1 else ''}, {sz_str}) [{cat}]"
                chk = ctk.CTkCheckBox(scroll, text=label_text, variable=var, font=ctk.CTkFont(size=11, weight="bold" if is_prechecked else "normal"))
                chk.grid(row=row_i, column=col_i, sticky="w", padx=12, pady=6)
                chk_widgets[ext] = (chk, label_text)

                col_i += 1
                if col_i > 1:
                    col_i = 0
                    row_i += 1

            def on_filter_change(*args):
                q = filter_var.get().strip().lower()
                for ext, (chk_widget, lbl) in chk_widgets.items():
                    if not q or q in ext.lower() or q in lbl.lower():
                        chk_widget.grid()
                    else:
                        chk_widget.grid_remove()

            filter_var.trace_add("write", on_filter_change)

            act_bar = ctk.CTkFrame(win, fg_color="transparent")
            act_bar.pack(fill="x", padx=15, pady=(0, 15))

            def apply_choices():
                selected = [ext for ext, v in chk_vars.items() if v.get()]
                self.ext_custom_exts_var.set(", ".join(selected))
                for ext in selected:
                    if ext in getattr(self, "ext_sub_vars", {}):
                        self.ext_sub_vars[ext].set(True)
                win.destroy()
                self.refresh_extractor_preview()
                messagebox.showinfo("Custom Extensions Applied", f"Applied {len(selected)} extension(s) to Extractor:\n{', '.join(selected) if selected else 'None'}")

            ctk.CTkButton(
                act_bar,
                text="✅ Apply Selected Extensions",
                command=apply_choices,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#1b5e20",
                hover_color="#2e7d32",
                height=34
            ).pack(side="right", padx=(8, 0))

            ctk.CTkButton(
                act_bar,
                text="Cancel",
                command=win.destroy,
                font=ctk.CTkFont(size=11),
                fg_color=("gray75", "gray30"),
                text_color=("gray10", "gray90"),
                height=34,
                width=80
            ).pack(side="right")

        def detect_all_exts_in_dup_folder(self):
            """Auto-detects unique file extensions in the duplicate scanner target folder and launches popup selector."""
            src_dir = self.dup_dir_var.get().strip()
            if not src_dir or not os.path.isdir(fix_win_long_path(src_dir)):
                messagebox.showwarning("No Location Selected", "Please select a scan folder first to auto-detect file extensions!")
                return

            exc_folds = self.parse_comma_list(self.exclude_folders_var.get().strip())
            exc_files = self.parse_comma_list(self.exclude_files_var.get().strip())
            exc_exts = self.parse_comma_list(self.exclude_ext_var.get().strip())

            detected = scan_folder_extensions(
                main_folder=src_dir if src_dir else None,
                include_system=False,
                exclude_folders=exc_folds,
                exclude_files=exc_files,
                exclude_exts=exc_exts
            )

            if not detected:
                messagebox.showinfo("No User Files Found", "No user file formats were detected in the selected location.")
                return

            win = ctk.CTkToplevel(self)
            win.title("🔍 Auto-Detected File Types & Extension Selector (Duplicates)")
            win.geometry("680x580")
            win.transient(self)
            win.grab_set()
            win.after(100, lambda: (win.lift(), win.focus_force()))

            hdr = ctk.CTkFrame(win, corner_radius=10, fg_color=("gray90", "gray18"))
            hdr.pack(fill="x", padx=15, pady=(12, 6), ipadx=8, ipady=6)
            
            hdr_lbl = ctk.CTkLabel(hdr, text=f"🔍 Found {len(detected)} Unique File Extension(s) in Folder", font=ctk.CTkFont(size=13, weight="bold"))
            hdr_lbl.pack(anchor="w", padx=8)
            ctk.CTkLabel(hdr, text="Tick the file extensions you want to filter/include in duplicate search:", font=ctk.CTkFont(size=11), text_color="gray60").pack(anchor="w", padx=8)

            tool_frame = ctk.CTkFrame(win, fg_color="transparent")
            tool_frame.pack(fill="x", padx=15, pady=(0, 6))

            chk_vars = {}
            chk_widgets = {}
            existing_custom = set(self.parse_comma_list(self.dup_sub_exts_var.get().strip()))

            filter_var = tk.StringVar()
            filter_entry = ctk.CTkEntry(tool_frame, textvariable=filter_var, placeholder_text="🔍 Filter exts...", font=ctk.CTkFont(size=11), height=28, width=200)
            filter_entry.pack(side="left", padx=(0, 10))

            def select_all():
                for v in chk_vars.values():
                    v.set(True)

            def select_none():
                for v in chk_vars.values():
                    v.set(False)

            def invert_all():
                for v in chk_vars.values():
                    v.set(not v.get())

            ctk.CTkButton(tool_frame, text="☑ Select All", command=select_all, font=ctk.CTkFont(size=10, weight="bold"), height=26, width=85, fg_color="#0288d1").pack(side="left", padx=(0, 4))
            ctk.CTkButton(tool_frame, text="☐ Clear All", command=select_none, font=ctk.CTkFont(size=10), height=26, width=75, fg_color=("gray75", "gray32"), text_color=("gray10", "gray90")).pack(side="left", padx=(0, 4))
            ctk.CTkButton(tool_frame, text="⇄ Invert", command=invert_all, font=ctk.CTkFont(size=10), height=26, width=65, fg_color=("gray75", "gray32"), text_color=("gray10", "gray90")).pack(side="left")

            scroll = ctk.CTkScrollableFrame(win, corner_radius=10)
            scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))
            scroll.grid_columnconfigure(0, weight=1)
            scroll.grid_columnconfigure(1, weight=1)

            col_i = 0
            row_i = 0
            for item in detected:
                ext = item['ext']
                cnt = item['count']
                sz_str = item['size_str']
                cat = item['category']

                is_prechecked = (ext in existing_custom)
                var = tk.BooleanVar(value=is_prechecked)
                chk_vars[ext] = var

                label_text = f"{ext}  ({cnt} file{'s' if cnt > 1 else ''}, {sz_str}) [{cat}]"
                chk = ctk.CTkCheckBox(scroll, text=label_text, variable=var, font=ctk.CTkFont(size=11, weight="bold" if is_prechecked else "normal"))
                chk.grid(row=row_i, column=col_i, sticky="w", padx=12, pady=6)
                chk_widgets[ext] = (chk, label_text)

                col_i += 1
                if col_i > 1:
                    col_i = 0
                    row_i += 1

            def on_filter_change(*args):
                q = filter_var.get().strip().lower()
                for ext, (chk_widget, lbl) in chk_widgets.items():
                    if not q or q in ext.lower() or q in lbl.lower():
                        chk_widget.grid()
                    else:
                        chk_widget.grid_remove()

            filter_var.trace_add("write", on_filter_change)

            act_bar = ctk.CTkFrame(win, fg_color="transparent")
            act_bar.pack(fill="x", padx=15, pady=(0, 15))

            def apply_choices():
                selected = [ext for ext, v in chk_vars.items() if v.get()]
                self.dup_sub_exts_var.set(", ".join(selected))
                win.destroy()
                messagebox.showinfo("Custom Extensions Applied", f"Applied {len(selected)} extension(s) to Duplicate Scanner:\n{', '.join(selected) if selected else 'None'}")

            ctk.CTkButton(
                act_bar,
                text="✅ Apply Selected Extensions",
                command=apply_choices,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#1b5e20",
                hover_color="#2e7d32",
                height=34
            ).pack(side="right", padx=(8, 0))

            ctk.CTkButton(
                act_bar,
                text="Cancel",
                command=win.destroy,
                font=ctk.CTkFont(size=11),
                fg_color=("gray75", "gray30"),
                text_color=("gray10", "gray90"),
                height=34,
                width=80
            ).pack(side="right")

        def refresh_extractor_preview(self):
            if getattr(self, "_suppress_preview_updates", False):
                return

            if hasattr(self, "_ext_debounce_timer") and self._ext_debounce_timer:
                try:
                    self.after_cancel(self._ext_debounce_timer)
                except Exception:
                    pass

            self._ext_debounce_timer = self.after(120, self._do_async_extractor_preview)

        def _do_async_extractor_preview(self):
            src_dir = self.ext_src_var.get().strip()
            if not self.ext_selected_individual_files and not src_dir:
                return

            inc_exts, exc_exts = self.get_extractor_filter_params()
            dest_dir = self.ext_dest_var.get().strip()

            struct_choice = self.ext_output_struct_var.get()
            if "Category" in struct_choice:
                sort_cat_key = "category"
            elif "Extension" in struct_choice:
                sort_cat_key = "extension"
            else:
                sort_cat_key = "flat"

            exc_folds = self.parse_comma_list(self.exclude_folders_var.get().strip())
            exc_files = self.parse_comma_list(self.exclude_files_var.get().strip())
            sel_files = self.ext_selected_individual_files if self.ext_selected_individual_files else None

            self.ext_preview_stats_lbl.configure(text="⏳ Scanning subfolders in background...")

            def worker():
                try:
                    preview_items, cat_counts, summary = scan_directory_preview(
                        main_folder=src_dir if src_dir else None,
                        sort_category=sort_cat_key,
                        recursive=True,
                        include_exts=inc_exts,
                        exclude_exts=exc_exts,
                        exclude_folders=exc_folds,
                        exclude_files=exc_files,
                        dest_folder=dest_dir if dest_dir else None,
                        selected_files=sel_files
                    )

                    def update_ui():
                        self.ext_preview_stats_lbl.configure(
                            text=f"Matching Files: {summary['total_files']} | Total Size: {summary['total_size_str']}"
                        )

                        rows = [(
                            item['filename'],
                            item['rel_src'],
                            item['rel_target'],
                            item['category'],
                            item['size_str'],
                            item.get("status_str", "Ready to Extract")
                        ) for item in preview_items]

                        self.populate_tree_in_chunks(self.ext_tree, rows, chunk_size=300)

                    self.after(0, update_ui)
                except Exception:
                    pass

            threading.Thread(target=worker, daemon=True).start()

        def run_delete_empty_folders(self, target_dir):
            if not target_dir:
                messagebox.showwarning("Missing Directory", "Please select a valid directory first.")
                return
            target_dir = str(target_dir).strip().strip('\'"')
            if not os.path.isdir(fix_win_long_path(target_dir)):
                messagebox.showwarning("Missing Directory", "Please select a valid directory first.")
                return

            self.status_var.set(f"Cleaning empty folders in {target_dir}...")
            exc_folds = self.parse_comma_list(self.exclude_folders_var.get().strip())
            cleaned = clean_empty_dirs(target_dir, remove_os_junk=True, exclude_folders=exc_folds)
            self.status_var.set(f"Cleanup complete. Removed {cleaned} empty folder(s).")
            messagebox.showinfo("Empty Folder Cleanup Complete", f"Successfully cleaned {cleaned} empty folder(s) (including OS junk files like desktop.ini)!")
            self.refresh_preview()
            self.refresh_extractor_preview()

        def start_extractor(self):
            src_dir = self.ext_src_var.get().strip()
            if not self.ext_selected_individual_files and (not src_dir or not os.path.isdir(fix_win_long_path(src_dir))):
                messagebox.showwarning("Missing Directory", "Please select a valid source directory or pick files.")
                return

            dest_dir = self.ext_dest_var.get().strip()
            if dest_dir and not os.path.exists(fix_win_long_path(dest_dir)):
                os.makedirs(fix_win_long_path(dest_dir), exist_ok=True)

            inc_exts, exc_exts = self.get_extractor_filter_params()
            struct_choice = self.ext_output_struct_var.get()
            if "Category" in struct_choice:
                sort_cat_key = "category"
            elif "Extension" in struct_choice:
                sort_cat_key = "extension"
            else:
                sort_cat_key = "flat"

            mode = "move" if "Move" in self.ext_action_mode.get() else "copy"

            raw_conflict = self.ext_conflict_mode_var.get()
            if "Interactive" in raw_conflict:
                conflict_mode = "ask"
            elif "Keep Both" in raw_conflict:
                conflict_mode = "number"
            elif "Replace" in raw_conflict:
                conflict_mode = "replace"
            else:
                conflict_mode = "skip"

            raw_skip = self.skipped_handling_var.get()
            if "Move Skipped" in raw_skip:
                skip_mode = "move"
                skip_dest = self.custom_skipped_dest_var.get().strip() if self.custom_skipped_dest_var.get().strip() else None
            else:
                skip_mode = "stay"
                skip_dest = None

            self.remembered_conflict_choice = None

            self.clear_log()
            self.log("==========================================", "header")
            self.log("    STARTING SUBFOLDER FILE EXTRACTION", "header")
            self.log("==========================================", "header")

            self.ext_start_btn.configure(state="disabled")
            self.ext_undo_btn.configure(state="disabled")
            self.ext_progress_bar.set(0)

            def run_ext_thread():
                try:
                    stats, manifest = organize_directory(
                        main_folder=src_dir if src_dir else None,
                        sort_category=sort_cat_key,
                        recursive=True,
                        include_exts=inc_exts,
                        exclude_exts=exc_exts,
                        exclude_folders=self.parse_comma_list(self.exclude_folders_var.get().strip()),
                        exclude_files=self.parse_comma_list(self.exclude_files_var.get().strip()),
                        mode=mode,
                        dest_folder=dest_dir if dest_dir else None,
                        enable_zip_backup=self.enable_zip_backup_var.get(),
                        clean_empty=self.ext_clean_empty_var.get(),
                        on_conflict=conflict_mode,
                        conflict_resolver_callback=self.prompt_interactive_conflict,
                        progress_callback=lambda c, t, fp, st, tag: self.after(0, self.update_ext_progress, c, t, fp, st, tag),
                        selected_files=self.ext_selected_individual_files if self.ext_selected_individual_files else None,
                        skipped_handling=skip_mode,
                        skipped_dest_folder=skip_dest
                    )

                    def finished():
                        self.log("\n==========================================", "header")
                        self.log("            EXTRACTION SUMMARY", "header")
                        self.log("==========================================", "header")
                        self.log(f"Total Files Extracted: {stats['processed']}", "success")
                        self.log(f"Skipped (Conflicts):   {stats['skipped']}", "skipped")
                        self.log(f"Errors Encountered:    {stats['errors']}", "error" if stats['errors'] > 0 else "info")

                        self.status_var.set("Subfolder Extraction complete!")
                        self.ext_start_btn.configure(state="normal")
                        self.ext_undo_btn.configure(state="normal")
                        self.refresh_extractor_preview()
                        messagebox.showinfo("Extraction Complete", f"Extracted: {stats['processed']}\nSkipped: {stats['skipped']}\nErrors: {stats['errors']}")

                    self.after(0, finished)
                except Exception as e:
                    def on_ext_error(err_msg):
                        self.log(f"\nEXTRACTION ERROR: {err_msg}", "error")
                        self.status_var.set("Error during extraction.")
                        self.ext_start_btn.configure(state="normal")
                        self.ext_undo_btn.configure(state="normal")
                        messagebox.showerror("Extraction Error", str(e))

                    self.after(0, on_ext_error, str(e))

            threading.Thread(target=run_ext_thread, daemon=True).start()

        def update_ext_progress(self, current, total, file_path, status_msg, status_tag):
            pct = (current / total) if total > 0 else 1.0
            self.ext_progress_bar.set(pct)
            fname = os.path.basename(file_path)
            self.status_var.set(f"Extracting ({current}/{total}): {fname}")
            self.log(f"[{current}/{total}] {fname}: {status_msg}", status_tag)

        def add_exclude_folder_picker(self):
            folder = filedialog.askdirectory(title="Select Folder to EXCLUDE (It & All Subfolders Will Be Skipped)")
            if folder:
                folder_abs = os.path.normpath(os.path.abspath(folder))
                curr = self.parse_comma_list(self.exclude_folders_var.get().strip())
                if folder_abs not in curr and folder not in curr:
                    curr.append(folder_abs)
                self.exclude_folders_var.set(", ".join(curr))
                self.status_var.set(f"🚫 Excluded folder: '{os.path.basename(folder)}' & all its subfolders.")
                messagebox.showinfo(
                    "Folder Excluded",
                    f"Folder Excluded Successfully!\n\nPath:\n{folder}\n\nThis folder and ALL its subfolders deep down will be skipped while processing."
                )
                self.refresh_preview()
                self.refresh_extractor_preview()

        def add_exclude_file_picker(self):
            files = filedialog.askopenfilenames(title="Select File(s) to EXCLUDE from Processing")
            if files:
                curr = self.parse_comma_list(self.exclude_files_var.get().strip())
                added = 0
                for f in files:
                    fname = os.path.basename(f)
                    if fname not in curr:
                        curr.append(fname)
                        added += 1
                self.exclude_files_var.set(", ".join(curr))
                self.status_var.set(f"🚫 Excluded {added} file(s) from operations.")
                messagebox.showinfo(
                    "Files Excluded",
                    f"Excluded {added} file(s) successfully!"
                )
                self.refresh_preview()

        def set_onedrive_dup_mode(self):
            self.dup_match_var.set("name_size")
            messagebox.showinfo(
                "☁️ OneDrive Zero-Download Mode Activated",
                "OneDrive Cloud Mode is NOW ACTIVE!\n\n"
                "• Matching Rule: Same Name & Size (Metadata Scan)\n"
                "• Reads NTFS file headers directly without opening file contents.\n"
                "• ZERO Bytes are downloaded from Microsoft OneDrive!"
            )

        def browse_cln_folder(self):
            folder = filedialog.askdirectory(title="Select Directory to Scan for Junk & Large Files")
            if folder:
                self.cln_dir_var.set(folder)

        def browse_cln_files(self):
            files = filedialog.askopenfilenames(title="Select Specific Files to Scan for Junk")
            if files:
                dir_name = os.path.dirname(files[0])
                self.cln_dir_var.set(f"[Custom Selection] {len(files)} file(s) from {dir_name}")
                self.run_cleaner_scan()

        def browse_ins_folder(self):
            folder = filedialog.askdirectory(title="Select Directory for Storage Analytics")
            if folder:
                self.ins_dir_var.set(folder)

        def browse_wtc_folder(self):
            folder = filedialog.askdirectory(title="Select Folder to Auto-Watch for New Downloads")
            if folder:
                self.wtc_dir_var.set(folder)

        def browse_dup_folder(self):
            folder = filedialog.askdirectory(title="Select Folder to Scan for Duplicate Conflicts")
            if folder:
                self.dup_dir_var.set(folder)
                self.dup_selected_individual_files = []

        def browse_dup_files(self):
            files = filedialog.askopenfilenames(title="Select Specific Files to Scan for Duplicates")
            if files:
                file_list = list(files)
                self.dup_selected_individual_files = file_list
                # Set scan root to the common ancestor folder of all selected files
                dirs = set(os.path.dirname(p) for p in file_list)
                if len(dirs) == 1:
                    self.dup_dir_var.set(list(dirs)[0])
                else:
                    # Multiple source dirs: use the longest common prefix
                    common = os.path.commonpath(file_list) if len(file_list) > 1 else os.path.dirname(file_list[0])
                    self.dup_dir_var.set(common if os.path.isdir(fix_win_long_path(common)) else os.path.dirname(file_list[0]))

        def add_exclude_folder_picker(self):
            folder = filedialog.askdirectory(title="Select Subfolder to Exclude from Scans")
            if folder:
                curr = self.parse_comma_list(self.exclude_folders_var.get().strip()) or []
                folder_name = os.path.basename(folder) or folder
                if folder_name not in curr:
                    curr.append(folder_name)
                    self.exclude_folders_var.set(", ".join(curr))

        def add_exclude_file_picker(self):
            file_path = filedialog.askopenfilename(title="Select Specific File Name to Exclude")
            if file_path:
                curr = self.parse_comma_list(self.exclude_files_var.get().strip()) or []
                filename = os.path.basename(file_path)
                if filename not in curr:
                    curr.append(filename)
                    self.exclude_files_var.set(", ".join(curr))

        def browse_multiple_folders(self, target_var=None, callback=None):
            folders = []
            while True:
                title = f"Select Folder #{len(folders)+1} (Click 'Cancel' when finished selecting folders)"
                folder = filedialog.askdirectory(title=title)
                if not folder:
                    break
                if folder not in folders:
                    folders.append(folder)
            
            if folders:
                joined = "; ".join(folders)
                if target_var is not None:
                    target_var.set(joined)
                else:
                    self.dir_var.set(joined)
                    self.dup_dir_var.set(joined)
                if callback:
                    callback()

        def dup_select_all_cats(self):
            for var in getattr(self, "dup_granular_checkbox_vars", {}).values():
                var.set(True)
            for sub_dict in getattr(self, "dup_sub_vars", {}).values():
                for sub_v in sub_dict.values():
                    sub_v.set(True)

        def run_universal_duplicate_scan(self):
            """Universal shortcut to auto-select ALL file types (Images, Videos, Docs, PDFs, Audio, Code, Zip, etc.) and launch duplicate scanner immediately."""
            self.dup_select_all_cats()
            if hasattr(self, "dup_sub_exts_var"):
                self.dup_sub_exts_var.set("")
            self.run_find_duplicates()

        def dup_clear_all_cats(self):
            for var in getattr(self, "dup_granular_checkbox_vars", {}).values():
                var.set(False)
            for sub_dict in getattr(self, "dup_sub_vars", {}).values():
                for sub_v in sub_dict.values():
                    sub_v.set(False)

        def dup_invert_cats(self):
            for var in getattr(self, "dup_granular_checkbox_vars", {}).values():
                var.set(not var.get())

        def _sync_dup_sub_from_cat(self, cat_label):
            cat_var = getattr(self, "dup_granular_checkbox_vars", {}).get(cat_label)
            if not cat_var:
                return
            val = cat_var.get()
            sub_dict = getattr(self, "dup_sub_vars", {}).get(cat_label, {})
            for sub_v in sub_dict.values():
                sub_v.set(val)

        def _dup_sub_select_all(self, cat_label):
            sub_dict = getattr(self, "dup_sub_vars", {}).get(cat_label, {})
            for sub_v in sub_dict.values():
                sub_v.set(True)

        def _dup_sub_clear_all(self, cat_label):
            sub_dict = getattr(self, "dup_sub_vars", {}).get(cat_label, {})
            for sub_v in sub_dict.values():
                sub_v.set(False)

        def detect_all_exts_in_dup_folder(self):
            folder = self.dup_dir_var.get().strip()
            if not folder or not os.path.isdir(fix_win_long_path(folder)):
                messagebox.showwarning("Folder Required", "Please select a valid scan folder first to detect extensions.")
                return

            def detect_bg():
                found_exts = set()
                try:
                    for root, dirs, files in os.walk(fix_win_long_path(folder)):
                        for f in files:
                            ext = os.path.splitext(f)[1].lower()
                            if ext and len(ext) < 12:
                                found_exts.add(ext)
                except Exception:
                    pass

                def update_ui():
                    if found_exts:
                        ext_str = ", ".join(sorted(found_exts))
                        if hasattr(self, "dup_sub_exts_var"):
                            self.dup_sub_exts_var.set(ext_str)
                        messagebox.showinfo("Extensions Detected", f"Found {len(found_exts)} file extensions in folder:\n\n{ext_str}")
                    else:
                        messagebox.showinfo("No Extensions", "No file extensions found in the selected folder.")

                self.after(0, update_ui)

            threading.Thread(target=detect_bg, daemon=True).start()

        def set_onedrive_dup_mode(self):
            self.dup_match_var.set("name_size_mtime")
            self.dup_recursive_var.set(True)
            messagebox.showinfo(
                "OneDrive Files On-Demand Mode Active",
                "Duplicate Scanner is now configured for Microsoft OneDrive!\n\n"
                "Matching Rule set to 'Name + Size + Date' (NTFS Metadata).\n"
                "0 Bytes will be downloaded from OneDrive cloud storage during scan!"
            )

        def run_find_duplicates(self):
            target_dir = self.dup_dir_var.get().strip().strip('\'"')
            selected_files = getattr(self, "dup_selected_individual_files", None)

            if not selected_files and not target_dir:
                messagebox.showwarning("Missing Directory", "Please select a valid directory to scan for duplicates.")
                return

            match_mode = self.dup_match_var.get()
            is_recursive = self.dup_recursive_var.get()

            # Cloud-Aware Pre-Check & Informed Consent Dialog
            if match_mode in ('content', 'perceptual_image', 'text_similarity'):
                try:
                    cand_files = gather_files(target_dir, is_recursive, selected_files=selected_files)
                    cloud_info = count_cloud_placeholders(cand_files)
                    if cloud_info['cloud_count'] > 0:
                        sz_mb = round(cloud_info['total_bytes'] / (1024.0 * 1024.0), 1)
                        sz_str = f"{sz_mb} MB" if sz_mb < 1024 else f"{round(sz_mb/1024.0, 2)} GB"
                        msg = (
                            f"☁️ Cloud-Only Files Detected!\n\n"
                            f"Definitive duplicate matching ({match_mode}) requires reading file contents.\n"
                            f"This scan will download {cloud_info['cloud_count']} cloud-only placeholder file(s) "
                            f"totaling approximately {sz_str}.\n\n"
                            f"Do you want to proceed and download these cloud files?\n\n"
                            f"(Tip: Choose 'No' and select '⚡ Quick Scan (Name + Size)' for 0-download scanning!)"
                        )
                        if not messagebox.askyesno("Cloud Download Confirmation", msg):
                            return
                except Exception as _cloud_err:
                    pass  # Non-blocking: proceed with scan even if cloud check fails
            
            raw_thresh = getattr(self, "dup_threshold_var", None)
            thresh_val = 0.9
            if raw_thresh:
                try:
                    thresh_val = float(raw_thresh.get().replace('% Match', '').strip()) / 100.0
                except Exception:
                    thresh_val = 0.9

            self.status_var.set("Scanning deep subfolders for duplicate files...")

            if hasattr(self, 'dup_progress_frame'):
                self.dup_progress_frame.pack(fill="x", pady=(0, 6), ipadx=8, ipady=6)
                self.dup_progress_bar.set(0.0)
                self.dup_progress_pct_lbl.configure(text="0%")
                self.dup_progress_title.configure(text="⚡ Initializing scanner engine...")
                self.dup_progress_detail_lbl.configure(text="📄 Gathering file entries...")

            for widget in self.dup_cards_scroll.winfo_children():
                widget.destroy()

            loading_lbl = ctk.CTkLabel(self.dup_cards_scroll, text="🔍 Scanning nested subfolders & finding duplicate conflicts... Please wait...", font=ctk.CTkFont(size=12, weight="bold"))
            loading_lbl.pack(pady=40)

            def scan_thread():
                try:
                    exc_folds = self.parse_comma_list(self.exclude_folders_var.get().strip())
                    exc_files = self.parse_comma_list(self.exclude_files_var.get().strip())
                    exc_exts = self.parse_comma_list(self.exclude_ext_var.get().strip())

                    # Build extension set from Granular Category checkboxes & Custom Extension field
                    include_exts = set()
                    granular_vars = getattr(self, "dup_granular_checkbox_vars", {})
                    sub_vars = getattr(self, "dup_sub_vars", {})

                    all_cats_checked = granular_vars and all(v.get() for v in granular_vars.values())

                    for cat_lbl, cat_var in granular_vars.items():
                        cat_exts = GRANULAR_FILE_TYPES.get(cat_lbl, [])
                        if cat_var.get():
                            sub_dict = sub_vars.get(cat_lbl, {})
                            if sub_dict:
                                checked_sub = [ext for ext, sv in sub_dict.items() if sv.get()]
                                if checked_sub:
                                    include_exts.update(checked_sub)
                                else:
                                    include_exts.update(cat_exts)
                            else:
                                include_exts.update(cat_exts)
                        else:
                            sub_dict = sub_vars.get(cat_lbl, {})
                            checked_sub = [ext for ext, sv in sub_dict.items() if sv.get()]
                            if checked_sub:
                                include_exts.update(checked_sub)

                    raw_sub_exts = getattr(self, "dup_sub_exts_var", tk.StringVar()).get().strip()
                    if raw_sub_exts:
                        for token in self.parse_comma_list(raw_sub_exts):
                            token = token.strip().lower()
                            if token:
                                if not token.startswith('.'):
                                    token = '.' + token
                                include_exts.add(token)

                    if (all_cats_checked or not granular_vars) and not raw_sub_exts:
                        include_exts = None
                        allow_other_exts = True
                    elif not include_exts:
                        include_exts = None
                        allow_other_exts = True
                    else:
                        allow_other_exts = False

                    self.clear_dup_log()
                    self.dup_log("==========================================", tag="header")
                    self.dup_log("      DUPLICATE CONFLICT SCAN STARTED", tag="header")
                    self.dup_log("==========================================", tag="header")
                    self.dup_log(f"📁 Scan Target: {target_dir or 'Selected Files List'}", tag="info")
                    self.dup_log(f"⚙️ Match Rule:  {match_mode} (Recursive: {is_recursive})", tag="info")

                    def on_progress(processed, total, stage_name, filename):
                        def update_prog_ui():
                            if not hasattr(self, 'dup_progress_bar'):
                                return
                            pct = (processed / float(total)) if total > 0 else 0.0
                            pct_int = int(pct * 100)
                            try:
                                self.dup_progress_bar.set(pct)
                                self.dup_progress_pct_lbl.configure(text=f"{pct_int}%")
                                self.dup_progress_title.configure(text=f"⚡ {stage_name}")
                                fn_str = f" Currently: {filename}" if filename else ""
                                self.dup_progress_detail_lbl.configure(text=f"📄 [{processed}/{total}] files scanned.{fn_str}")
                                self.status_var.set(f"Scanning... {pct_int}% ({processed}/{total} files)")
                            except Exception:
                                pass
                        self.after(0, update_prog_ui)
                        if filename:
                            self.dup_log(f"[{stage_name}] {filename}", tag="info")

                    groups = find_duplicate_groups(
                        target_dir,
                        match_mode=match_mode,
                        recursive=is_recursive,
                        exclude_folders=exc_folds,
                        exclude_files=exc_files,
                        exclude_exts=exc_exts,
                        include_exts=include_exts,
                        allow_other_exts=allow_other_exts,
                        selected_files=selected_files,
                        similarity_threshold=thresh_val,
                        progress_callback=on_progress
                    )

                    def update_ui():
                        try:
                            self.dup_groups = groups
                            self.dup_checkbox_vars.clear()
                            self.dup_card_widgets = []

                            # Destroy loading animation label from scroll container
                            for widget in self.dup_cards_scroll.winfo_children():
                                widget.destroy()

                            # Pre-register BooleanVar entries for all files across all groups
                            for g in groups:
                                for f in g['files']:
                                    p = f['path']
                                    var = tk.BooleanVar(value=False)
                                    self.dup_checkbox_vars[p] = var

                            if hasattr(self, 'dup_progress_frame'):
                                self.dup_progress_bar.set(1.0)
                                self.dup_progress_pct_lbl.configure(text="100%")
                                self.dup_progress_title.configure(text="🎉 Scanning Complete!")
                                self.after(1200, lambda: self.dup_progress_frame.pack_forget())

                            total_files_count = sum(len(g['files']) for g in groups)
                            total_extra_files = sum(len(g['files']) - 1 for g in groups)
                            total_wasted = sum(sum(f['size_bytes'] for f in g['files'][1:]) for g in groups)
                            wasted_str = format_bytes(total_wasted)

                            cat_counts = {}
                            for g in groups:
                                for f in g['files']:
                                    ext = os.path.splitext(f['filename'])[1].lower()
                                    cat_counts[ext] = cat_counts.get(ext, 0) + 1
                            top_exts = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                            cat_str = ", ".join(f"{ext} ({cnt})" for ext, cnt in top_exts) if top_exts else "None"

                            if hasattr(self, 'dup_lbl_total_scanned'):
                                self.dup_lbl_total_scanned.configure(text=f"📁 Files Scanned:\n{total_files_count:,}")
                            if hasattr(self, 'dup_lbl_groups_found'):
                                self.dup_lbl_groups_found.configure(text=f"👯 Duplicate Groups:\n{len(groups):,}")
                            if hasattr(self, 'dup_lbl_reclaimable'):
                                self.dup_lbl_reclaimable.configure(text=f"💾 Reclaimable Space:\n{wasted_str}")
                            if hasattr(self, 'dup_lbl_cat_breakdown'):
                                self.dup_lbl_cat_breakdown.configure(text=f"🖼️ Top Categories:\n{cat_str}")

                            self.dup_log("\n==========================================", tag="header")
                            self.dup_log("        DUPLICATE SCAN RESULTS SUMMARY", tag="header")
                            self.dup_log("==========================================", tag="header")
                            self.dup_log(f"📁 Target Directory:  {target_dir or 'Selected Files'}", tag="info")
                            self.dup_log(f"👯 Duplicate Groups: {len(groups):,} found", tag="success" if groups else "info")
                            self.dup_log(f"📄 Redundant Copies:  {total_extra_files:,} files", tag="warning" if total_extra_files > 0 else "info")
                            self.dup_log(f"💾 Reclaimable Space: {wasted_str}", tag="success" if total_wasted > 0 else "info")

                            if not groups:
                                ctk.CTkLabel(
                                    self.dup_cards_scroll,
                                    text="🎉 No duplicate file conflicts found in the target directory!",
                                    font=ctk.CTkFont(size=13, weight="bold"),
                                    text_color="#81c784"
                                ).pack(pady=40)
                                self.status_var.set("Scan complete. 0 duplicates found.")
                                self.update_dup_action_label()
                                return

                            if match_mode == 'perceptual_image':
                                self.auto_select_keep_highest_res()
                            else:
                                self.auto_select_keep_oldest()

                            self.status_var.set(f"Scan complete. Found {len(groups)} duplicate conflict groups ({total_extra_files} extra files, {format_bytes(total_wasted)} wasted).")
                            
                            # Render paginated batch cards smoothly
                            self.render_dup_cards_page(reset=True)

                            # Auto-launch side-by-side interactive popup resolver window
                            # Only open if resolver is not already open (guard)
                            if len(groups) > 0 and not getattr(self, '_resolver_modal_open', False):
                                self.after(300, lambda: self.open_dup_resolver_modal())
                        except Exception as ex_ui:
                            print(f"[Error rendering Duplicate UI]: {ex_ui}")

                    self.after(0, update_ui)
                except Exception as err:
                    def on_err():
                        if hasattr(self, 'dup_progress_frame'):
                            self.dup_progress_frame.pack_forget()
                        for widget in self.dup_cards_scroll.winfo_children():
                            widget.destroy()
                        ctk.CTkLabel(
                            self.dup_cards_scroll,
                            text=f"⚠️ Error during duplicate scan: {err}",
                            font=ctk.CTkFont(size=12, weight="bold"),
                            text_color="#ef5350"
                        ).pack(pady=40)
                        self.status_var.set(f"Scan error: {err}")
                    self.after(0, on_err)

            threading.Thread(target=scan_thread, daemon=True).start()

        def render_group_card(self, group):
            g_id = group['group_id']
            files = group['files']
            total_size = sum(f['size_bytes'] for f in files)
            wasted_bytes = sum(f['size_bytes'] for f in files[1:])

            card = ctk.CTkFrame(self.dup_cards_scroll, corner_radius=12, fg_color=("gray93", "gray17"))
            card.pack(fill="x", pady=8, padx=4)

            hdr = ctk.CTkFrame(card, corner_radius=8, fg_color=("gray85", "gray22"))
            hdr.pack(fill="x", padx=10, pady=10)
            hdr.grid_columnconfigure(0, weight=1)

            fn_title = files[0]['filename'] if files else "Conflict Item"
            sig_text = group.get('signature', f"Group #{g_id}")
            ctk.CTkLabel(
                hdr,
                text=f"📁 Group #{g_id} — {fn_title} ({sig_text})",
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
            ).grid(row=0, column=0, sticky="w", padx=12, pady=(6, 2))

            sub_hdr = f"{len(files)} Matching Copies • {format_bytes(total_size)} Total File Size"
            ctk.CTkLabel(
                hdr,
                text=sub_hdr,
                font=ctk.CTkFont(size=11),
                text_color=("gray40", "gray70")
            ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 6))

            badge_box = ctk.CTkFrame(hdr, fg_color="transparent")
            badge_box.grid(row=0, column=1, rowspan=2, sticky="e", padx=12, pady=6)

            ctk.CTkButton(
                badge_box,
                text="🔥 Delete Both/All",
                command=lambda grp=files: self.delete_entire_group(grp),
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="#c62828",
                hover_color="#b71c1c",
                height=26,
                width=110
            ).pack(side="right", padx=(4, 0))

            ctk.CTkButton(
                badge_box,
                text="📁 Move Both/All...",
                command=lambda grp=files: self.move_entire_group(grp),
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="#f57c00",
                hover_color="#e65100",
                height=26,
                width=110
            ).pack(side="right", padx=4)

            ctk.CTkLabel(
                badge_box,
                text=f"🔥 {format_bytes(wasted_bytes)} Wasted",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#c62828",
                text_color="white",
                corner_radius=6,
                padx=8,
                pady=3
            ).pack(side="right", padx=4)

            grid_frame = ctk.CTkFrame(card, fg_color="transparent")
            grid_frame.pack(fill="x", padx=10, pady=(0, 10))

            for idx, f in enumerate(files):
                grid_frame.grid_columnconfigure(idx, weight=1)
                f_path = f['path']
                if f_path not in self.dup_checkbox_vars:
                    var = tk.BooleanVar(value=False)
                    self.dup_checkbox_vars[f_path] = var
                    var.trace_add("write", lambda *args: self.update_dup_action_label())
                else:
                    var = self.dup_checkbox_vars[f_path]

                panel = ctk.CTkFrame(grid_frame, corner_radius=10, fg_color=("gray88", "gray22"))
                panel.grid(row=0, column=idx, sticky="nsew", padx=5, pady=2)
                panel.grid_columnconfigure(0, weight=1)

                # Top Direct Action Bar on Every Image Card
                top_row = ctk.CTkFrame(panel, fg_color="transparent")
                top_row.pack(fill="x", padx=10, pady=(8, 4))

                chk = ctk.CTkCheckBox(top_row, text="Mark Copy", variable=var, font=ctk.CTkFont(size=10, weight="bold"))
                chk.pack(side="left")

                sim_pct = f.get('match_percent', 100.0)
                if f['is_original']:
                    ctk.CTkLabel(top_row, text="⭐ ORIGINAL", font=ctk.CTkFont(size=9, weight="bold"), fg_color="#1b5e20", text_color="white", corner_radius=5, padx=7, pady=2).pack(side="right")
                else:
                    badge_txt = f"👯 DUPLICATE ({sim_pct}%)" if sim_pct < 100 else "👯 DUPLICATE"
                    ctk.CTkLabel(top_row, text=badge_txt, font=ctk.CTkFont(size=9, weight="bold"), fg_color="#6a1b9a", text_color="white", corner_radius=5, padx=7, pady=2).pack(side="right")

                # Direct Actions Toolbar
                act_toolbar = ctk.CTkFrame(panel, fg_color="transparent")
                act_toolbar.pack(fill="x", padx=8, pady=(0, 4))

                ctk.CTkButton(
                    act_toolbar,
                    text="⭐ Keep Only This",
                    command=lambda p=f_path, grp=files: self.keep_only_this_copy(grp, p),
                    font=ctk.CTkFont(size=9, weight="bold"),
                    fg_color="#1b5e20",
                    hover_color="#2e7d32",
                    height=22,
                    width=95
                ).pack(side="left", padx=1)

                ctk.CTkButton(
                    act_toolbar,
                    text="🗑️ Delete",
                    command=lambda p=f_path: self.delete_single_copy(p),
                    font=ctk.CTkFont(size=9, weight="bold"),
                    fg_color="#c62828",
                    hover_color="#b71c1c",
                    height=22,
                    width=55
                ).pack(side="left", padx=1)

                ctk.CTkButton(
                    act_toolbar,
                    text="📁 Move",
                    command=lambda p=f_path: self.move_single_copy(p),
                    font=ctk.CTkFont(size=9, weight="bold"),
                    fg_color="#f57c00",
                    hover_color="#e65100",
                    height=22,
                    width=55
                ).pack(side="left", padx=1)

                ext_lower = os.path.splitext(f_path)[1].lower()
                is_vid = f.get('is_video', False) or ext_lower in {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.vob', '.ts', '.m2ts'}

                if is_vid:
                    ctk.CTkButton(
                        act_toolbar,
                        text="▶ Play",
                        command=lambda p=f_path: self.open_file_item(p),
                        font=ctk.CTkFont(size=9, weight="bold"),
                        fg_color="#1565c0",
                        hover_color="#0d47a1",
                        height=22,
                        width=50
                    ).pack(side="left", padx=1)
                else:
                    ctk.CTkButton(
                        act_toolbar,
                        text="👁️ Zoom",
                        command=lambda p=f_path, g_f=files: self.open_image_zoom_modal(p, group_files=g_f),
                        font=ctk.CTkFont(size=9, weight="bold"),
                        fg_color="#00838f",
                        hover_color="#006064",
                        height=22,
                        width=50
                    ).pack(side="left", padx=1)

                ctk.CTkButton(
                    act_toolbar,
                    text="✏️ Rename",
                    command=lambda p=f_path: [self.rename_file_in_session(p), self.render_dup_cards()],
                    font=ctk.CTkFont(size=9, weight="bold"),
                    fg_color="#00838f",
                    hover_color="#006064",
                    height=22,
                    width=55
                ).pack(side="left", padx=1)

                preview_frame = ctk.CTkFrame(panel, fg_color=("gray80", "gray18"), corner_radius=8, height=130)
                preview_frame.pack(fill="x", padx=10, pady=4)
                preview_frame.pack_propagate(False)

                img_lbl = ctk.CTkLabel(preview_frame, text="📷 Loading...", font=ctk.CTkFont(size=10), text_color="gray50")
                img_lbl.pack(expand=True)
                img_lbl.bind("<Button-1>", lambda e, p=f_path, g_f=files, is_v=is_vid: self.open_file_item(p) if is_v else self.open_image_zoom_modal(p, group_files=g_f))
                img_lbl.configure(cursor="hand2")
                CTkToolTip(img_lbl, "Click thumbnail to Play Video in Media Player" if is_vid else "Click thumbnail to Open Lightbox Preview")

                self.load_file_thumbnail_async(f_path, target_size=(220, 120), label_widget=img_lbl, filename=f['filename'])

                # Video Duration Overlay Badge & Info Extraction
                dur_str = f.get('duration_str')
                if (not dur_str or not f.get('res_str')) and is_vid:
                    try:
                        from sorter_core import get_video_file_info
                        v_i = get_video_file_info(f_path)
                        if v_i:
                            dur_str = v_i.get('duration_str', '') or dur_str
                            f['duration_str'] = dur_str
                            if v_i.get('res_str'):
                                f['res_str'] = v_i.get('res_str')
                    except Exception:
                        pass

                if dur_str:
                    try:
                        dur_badge = ctk.CTkLabel(
                            preview_frame,
                            text=f"⏱️ {dur_str}",
                            font=ctk.CTkFont(size=9, weight="bold"),
                            fg_color=("#212121", "#0a0a0a"),
                            text_color="#ffcc80",
                            corner_radius=4,
                            padx=6,
                            pady=1
                        )
                        dur_badge.place(relx=0.96, rely=0.92, anchor="se")
                    except Exception:
                        pass

                meta_box = ctk.CTkFrame(panel, fg_color="transparent")
                meta_box.pack(fill="x", padx=10, pady=6)

                rel_dir = os.path.dirname(f['rel_path']) or "Root Directory"
                ctk.CTkLabel(meta_box, text=f"📁 Location: {rel_dir}", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").pack(fill="x", pady=(2, 2))

                name_lbl = ctk.CTkLabel(meta_box, text=f"📄 {f['filename']}", font=ctk.CTkFont(size=10, weight="bold"), text_color="#64b5f6", anchor="w", cursor="hand2")
                name_lbl.pack(fill="x", pady=(0, 2))
                name_lbl.bind("<Button-1>", lambda e, p=f_path: [self.rename_file_in_session(p), self.render_dup_cards()])
                CTkToolTip(name_lbl, "Click to rename this file on disk")
                ctk.CTkLabel(meta_box, text=f"📅 Modified: {f['mtime_str']}", font=ctk.CTkFont(size=10), text_color=("gray40", "gray65"), anchor="w").pack(fill="x", pady=1)
                ctk.CTkLabel(meta_box, text=f"⚖️ Size: {f['size_str']}", font=ctk.CTkFont(size=10), text_color=("gray40", "gray65"), anchor="w").pack(fill="x", pady=(1, 2))
                
                if is_vid:
                    display_dur = dur_str if dur_str else "00:15"
                    ctk.CTkLabel(meta_box, text=f"⏱️ Video Duration: {display_dur}", font=ctk.CTkFont(size=10, weight="bold"), text_color="#ffb74d", anchor="w").pack(fill="x", pady=(1, 2))

                if f.get('res_str'):
                    lbl_prefix = "🎥 Video Res:" if is_vid else "📷 Resolution:"
                    ctk.CTkLabel(meta_box, text=f"{lbl_prefix} {f['res_str']}", font=ctk.CTkFont(size=10, weight="bold"), text_color="#00acc1", anchor="w").pack(fill="x", pady=(1, 4))

                ctk.CTkButton(
                    panel,
                    text="Open File Location ↗",
                    command=lambda p=f_path: self.open_file_item(p),
                    font=ctk.CTkFont(size=11, weight="bold"),
                    height=28,
                    fg_color=("gray75", "gray32"),
                    text_color=("gray10", "gray90")
                ).pack(fill="x", padx=10, pady=(0, 10))

        def keep_only_this_copy(self, group_files, keep_file_path):
            """Marks one copy as Keep (Original) and all other copies in the group for deletion/cleanup."""
            for f in group_files:
                p = f['path']
                f['is_original'] = (p == keep_file_path)
                if p in self.dup_checkbox_vars:
                    self.dup_checkbox_vars[p].set(p != keep_file_path)
                else:
                    self.dup_checkbox_vars[p] = tk.BooleanVar(value=(p != keep_file_path))

            if hasattr(self, 'dup_groups'):
                for g in self.dup_groups:
                    group_paths = set(item['path'] for item in g.get('files', []))
                    if keep_file_path in group_paths:
                        g['kept_file_path'] = keep_file_path
                        g['needs_review'] = False
                        break

            self.update_dup_action_label()
            self.render_dup_cards_page(reset=True)

        def delete_single_copy(self, file_path, rescan=True):
            """Deletes a single copy immediately on disk (moves to _Deleted_Files for safety)."""
            if not os.path.exists(fix_win_long_path(file_path)):
                messagebox.showerror("Error", "File no longer exists.")
                return False
            fn = os.path.basename(file_path)
            confirm = messagebox.askyesno("Confirm Delete", f"Move copy to '_Deleted_Files/' folder?\n\n{fn}")
            if not confirm:
                return False
            scan_root = self.dup_dir_var.get().strip()
            deleted_folder = os.path.join(scan_root, "_Deleted_Files") if (scan_root and os.path.isdir(fix_win_long_path(scan_root))) else get_system_vault_dir("TrashDuplicates")
            os.makedirs(fix_win_long_path(deleted_folder), exist_ok=True)
            res = move_duplicate_files([file_path], deleted_folder)
            if res['moved'] > 0:
                messagebox.showinfo("Moved to _Deleted_Files", f"Successfully moved single copy:\n{fn}")
                if rescan:
                    self.run_find_duplicates()
                return True
            return False

        def move_single_copy(self, file_path, target_folder=None, rescan=True, confirm=True, show_info=True):
            """Moves ONLY the single specific file copy in view into the selected destination folder."""
            safe_p = fix_win_long_path(file_path)
            if not os.path.exists(safe_p):
                if show_info:
                    messagebox.showerror("Error", "File no longer exists on disk.")
                return False

            fn = os.path.basename(file_path)
            if not target_folder:
                target_folder = filedialog.askdirectory(title=f"Select Destination Folder to Move '{fn}' Only")
            if not target_folder:
                return False

            res = move_duplicate_files([file_path], target_folder)
            if res['moved'] > 0:
                if show_info:
                    messagebox.showinfo("Single File Moved", f"Successfully moved '{fn}' to:\n{target_folder}")
                if rescan:
                    self.run_find_duplicates()
                return True
            return False

        def delete_single_copy_to_folder(self, file_path, rescan=True, confirm=True, show_info=True):
            """
            Moves a single specific file copy into a dedicated '_Deleted_Files' quarantine folder
            in the scan root directory (or AppData Vault Trash), ensuring zero permanent data loss!
            """
            safe_p = fix_win_long_path(file_path)
            if not os.path.exists(safe_p):
                if show_info:
                    messagebox.showerror("Error", "File no longer exists on disk.")
                return False

            fn = os.path.basename(file_path)
            scan_root = self.dup_dir_var.get().strip()
            if scan_root and os.path.isdir(fix_win_long_path(scan_root)):
                deleted_folder = os.path.join(scan_root, "_Deleted_Files")
            else:
                deleted_folder = get_system_vault_dir("TrashDuplicates")

            os.makedirs(fix_win_long_path(deleted_folder), exist_ok=True)

            if confirm:
                confirm_ok = messagebox.askyesno(
                    "Confirm Quarantine Move",
                    f"Move single file '{fn}' to '_Deleted_Files/' folder?\n\n(File is safely preserved and recoverable anytime!)"
                )
                if not confirm_ok:
                    return False

            target_path = os.path.join(deleted_folder, fn)
            safe_target = fix_win_long_path(target_path)
            if os.path.exists(safe_target):
                name, ext = os.path.splitext(fn)
                target_path = os.path.join(deleted_folder, f"{name}_{int(time.time())}{ext}")
                safe_target = fix_win_long_path(target_path)

            try:
                shutil.move(safe_p, safe_target)
                if show_info:
                    messagebox.showinfo("Moved to _Deleted_Files", f"File '{fn}' safely moved to:\n{deleted_folder}")
                if rescan:
                    self.run_find_duplicates()
                return True
            except Exception as e:
                if show_info:
                    messagebox.showerror("Error", f"Failed to move file: {e}")
                return False

        def remove_group_from_memory(self, group_files):
            """
            Removes the duplicate group containing the given file list from self.dup_groups.
            Also cleans up self.dup_checkbox_vars for all removed file paths.
            """
            if not hasattr(self, 'dup_groups'):
                return
            paths_in_group = set(f['path'] for f in group_files if isinstance(f, dict))
            self.dup_groups = [
                g for g in self.dup_groups
                if not (set(f['path'] for f in g.get('files', [])) & paths_in_group)
            ]
            for p in paths_in_group:
                self.dup_checkbox_vars.pop(p, None)

        def delete_entire_group(self, group_files, rescan=True, confirm=True, show_info=True):
            """Moves ALL file copies in the specified duplicate group to _Deleted_Files/."""
            if not group_files:
                return False
            paths = [f['path'] for f in group_files if os.path.exists(fix_win_long_path(f['path']))]
            if not paths:
                if show_info:
                    messagebox.showerror("Error", "No valid files found in this group.")
                return False
            fn = group_files[0]['filename']
            if confirm:
                confirm_ok = messagebox.askyesno("Confirm Delete Group", f"Move ALL {len(paths)} copies of '{fn}' to '_Deleted_Files/'?")
                if not confirm_ok:
                    return False
            
            scan_root = self.dup_dir_var.get().strip()
            if scan_root and os.path.isdir(fix_win_long_path(scan_root)):
                deleted_folder = os.path.join(scan_root, "_Deleted_Files")
            else:
                deleted_folder = get_system_vault_dir("TrashDuplicates")
            os.makedirs(fix_win_long_path(deleted_folder), exist_ok=True)

            res = move_duplicate_files(paths, deleted_folder)
            if show_info:
                messagebox.showinfo("Group Deleted", f"Successfully moved ALL {res['moved']} copies of '{fn}' to _Deleted_Files/!")
            self.remove_group_from_memory(group_files)
            if rescan:
                self.run_find_duplicates()
            return True

        def move_entire_group(self, group_files, target_folder=None, rescan=True, confirm=True, show_info=True):
            """Moves ALL file copies in the specified duplicate group to a destination folder."""
            if not group_files:
                return False
            paths = [f['path'] for f in group_files if os.path.exists(fix_win_long_path(f['path']))]
            if not paths:
                if show_info:
                    messagebox.showerror("Error", "No valid files found in this group.")
                return False
            fn = group_files[0]['filename']
            if not target_folder:
                target_folder = filedialog.askdirectory(title=f"Select Destination Folder for ALL {len(paths)} copies of {fn}")
            if not target_folder:
                return False
            res = move_duplicate_files(paths, target_folder)
            if show_info:
                messagebox.showinfo("Group Moved", f"Successfully moved ALL {res['moved']} copies of '{fn}' into:\n{target_folder}")
            self.remove_group_from_memory(group_files)
            if rescan:
                self.run_find_duplicates()
            return True

        def rename_file_in_session(self, current_path, parent_window=None):
            """Prompts user to rename a file on disk with pre-filled editable text, updating dup_groups and UI cards."""
            safe_old = fix_win_long_path(current_path)
            if not os.path.exists(safe_old):
                messagebox.showerror("File Error", f"File not found:\n{current_path}")
                return None

            old_name = os.path.basename(current_path)
            dir_name = os.path.dirname(current_path)

            target_parent = parent_window if (parent_window and parent_window.winfo_exists()) else self
            has_parent_modal = (parent_window and parent_window.winfo_exists())

            # Release parent modal grab temporarily to avoid focus lockup
            if has_parent_modal:
                try:
                    parent_window.grab_release()
                except Exception:
                    pass

            dlg_win = ctk.CTkToplevel(target_parent)
            dlg_win.title("✏️ Edit Filename")
            dlg_win.geometry("480x210")
            dlg_win.resizable(False, False)
            dlg_win.transient(target_parent)

            # Center on screen / parent
            try:
                dlg_win.update_idletasks()
                w = dlg_win.winfo_width()
                h = dlg_win.winfo_height()
                ws = dlg_win.winfo_screenwidth()
                hs = dlg_win.winfo_screenheight()
                dlg_win.geometry(f"+{(ws // 2) - (w // 2)}+{(hs // 2) - (h // 2)}")
            except Exception:
                pass

            ctk.CTkLabel(
                dlg_win,
                text=f"Edit filename for:\n📁 {dir_name}",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                anchor="w",
                justify="left"
            ).pack(fill="x", padx=16, pady=(14, 6))

            entry_var = tk.StringVar(value=old_name)
            entry = ctk.CTkEntry(dlg_win, textvariable=entry_var, font=ctk.CTkFont(size=12), height=34)
            entry.pack(fill="x", padx=16, pady=6)

            # Select text up to extension for quick editing
            name_no_ext, ext = os.path.splitext(old_name)
            entry.focus_set()
            try:
                entry.icursor(len(name_no_ext))
                entry.select_range(0, len(name_no_ext))
            except Exception:
                pass

            result_name = [None]

            def on_confirm():
                val = entry_var.get().strip()
                if val:
                    result_name[0] = val
                on_close_dlg()

            def on_close_dlg():
                try:
                    dlg_win.grab_release()
                except Exception:
                    pass
                dlg_win.destroy()
                if has_parent_modal and parent_window.winfo_exists():
                    try:
                        parent_window.grab_set()
                        parent_window.focus_force()
                    except Exception:
                        pass

            dlg_win.protocol("WM_DELETE_WINDOW", on_close_dlg)
            dlg_win.bind("<Return>", lambda e: on_confirm())
            dlg_win.bind("<Escape>", lambda e: on_close_dlg())

            btn_box = ctk.CTkFrame(dlg_win, fg_color="transparent")
            btn_box.pack(fill="x", padx=16, pady=(10, 14))

            ctk.CTkButton(
                btn_box,
                text="✅ Save New Name",
                command=on_confirm,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#00838f",
                height=32,
                width=140
            ).pack(side="right", padx=4)

            ctk.CTkButton(
                btn_box,
                text="❌ Cancel",
                command=on_close_dlg,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=("gray65", "gray35"),
                height=32,
                width=90
            ).pack(side="right", padx=4)

            dlg_win.grab_set()
            target_parent.wait_window(dlg_win)

            new_name = result_name[0]
            if not new_name or new_name == old_name:
                return None

            new_path = os.path.join(dir_name, new_name)
            safe_new = fix_win_long_path(new_path)

            if os.path.exists(safe_new):
                messagebox.showerror("Rename Collision", f"A file named '{new_name}' already exists in this directory.")
                return None

            try:
                os.rename(safe_old, safe_new)
                self.status_var.set(f"✏️ File renamed: '{old_name}' -> '{new_name}'")

                # Update dup_groups references
                all_groups = getattr(self, "dup_groups", [])
                for g in all_groups:
                    if g.get('kept_file_path') == current_path:
                        g['kept_file_path'] = new_path
                    for f in g.get('files', []):
                        if f['path'] == current_path:
                            f['path'] = new_path
                            f['filename'] = new_name
                            try:
                                f['rel_path'] = os.path.relpath(new_path, self.dup_dir_var.get().strip() or dir_name)
                            except Exception:
                                f['rel_path'] = new_name

                # Update checkbox vars dictionary
                if current_path in self.dup_checkbox_vars:
                    val = self.dup_checkbox_vars.pop(current_path)
                    self.dup_checkbox_vars[new_path] = val

                return new_path
            except Exception as e:
                messagebox.showerror("Rename Failed", f"Could not rename file: {e}")
                return None

        def open_image_zoom_modal(self, file_path, group_files=None, parent_win=None):
            """
            Windows 11 'Sneak View' Lightbox & Inspector Modal.
            Features: High-Res Zoom, File Rename, Group Image Navigation, File Info, Mark Keep.
            Fixes modal grab conflict / instant close bug by managing transient parent & grab_set.
            """
            safe_p = fix_win_long_path(file_path)
            if not os.path.exists(safe_p):
                messagebox.showerror("File Error", "File no longer exists on disk.")
                return

            target_parent = parent_win if (parent_win and parent_win.winfo_exists()) else self
            has_parent_modal = (parent_win and parent_win.winfo_exists())

            zoom_win = ctk.CTkToplevel(target_parent)
            zoom_win.title(f"📷 Windows Sneak View — {os.path.basename(file_path)}")
            zoom_win.geometry("980x740")

            if has_parent_modal:
                try:
                    parent_win.grab_release()
                except Exception:
                    pass

            zoom_win.transient(target_parent)

            # ── Video Player Controller Engine State (WMP Audio + OpenCV Sync) ──
            VID_PREVIEW_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.vob', '.ts', '.m2ts', '.divx', '.mpg', '.mpeg'}
            v_state = {
                'cap': None,
                'wmp': None,
                'is_playing': False,
                'curr_frame': 0,
                'total_frames': 1,
                'fps': 30.0,
                'after_id': None,
                'is_seeking': False,
                'volume': 80,
                'is_muted': False
            }

            def stop_video_engine():
                if v_state['after_id']:
                    try:
                        zoom_win.after_cancel(v_state['after_id'])
                    except Exception:
                        pass
                    v_state['after_id'] = None
                v_state['is_playing'] = False
                if v_state['wmp']:
                    try:
                        v_state['wmp'].controls.stop()
                        v_state['wmp'].close()
                    except Exception:
                        pass
                    v_state['wmp'] = None
                if v_state['cap']:
                    try:
                        v_state['cap'].release()
                    except Exception:
                        pass
                    v_state['cap'] = None

            def on_close_zoom():
                stop_video_engine()
                try:
                    zoom_win.grab_release()
                except Exception:
                    pass
                zoom_win.destroy()
                if has_parent_modal and parent_win.winfo_exists():
                    try:
                        parent_win.grab_set()
                        parent_win.focus_force()
                    except Exception:
                        pass

            zoom_win.protocol("WM_DELETE_WINDOW", on_close_zoom)

            try:
                zoom_win.update_idletasks()
                w = zoom_win.winfo_width()
                h = zoom_win.winfo_height()
                ws = zoom_win.winfo_screenwidth()
                hs = zoom_win.winfo_screenheight()
                zoom_win.geometry(f"+{(ws // 2) - (w // 2)}+{(hs // 2) - (h // 2)}")
            except Exception:
                pass

            curr_file_path = [file_path]
            files_list = group_files if (group_files and isinstance(group_files, list)) else []

            hdr = ctk.CTkFrame(zoom_win, fg_color="transparent")
            hdr.pack(fill="x", padx=16, pady=10)

            title_lbl = ctk.CTkLabel(hdr, text=f"📷 Windows Sneak View — {os.path.basename(file_path)}", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"))
            title_lbl.pack(side="left")

            def handle_header_rename():
                res_path = self.rename_file_in_session(curr_file_path[0], parent_window=zoom_win)
                if res_path:
                    curr_file_path[0] = res_path
                    render_sneak_preview()

            ctk.CTkButton(hdr, text="✏️ Rename", command=handle_header_rename, font=ctk.CTkFont(size=10, weight="bold"), height=26, width=75, fg_color="#00838f").pack(side="left", padx=10)

            ctk.CTkButton(hdr, text="❌ Close", command=on_close_zoom, font=ctk.CTkFont(size=11, weight="bold"), height=28, width=70, fg_color=("gray60", "gray40")).pack(side="right")

            main_view = ctk.CTkFrame(zoom_win, fg_color=("gray85", "gray15"), corner_radius=12)
            main_view.pack(fill="both", expand=True, padx=16, pady=(0, 6))

            img_container = ctk.CTkFrame(main_view, fg_color="transparent")
            img_container.pack(fill="both", expand=True, padx=10, pady=6)

            img_lbl = ctk.CTkLabel(img_container, text="📷 Loading preview...", font=ctk.CTkFont(size=12))
            img_lbl.pack(expand=True)

            # ── Dedicated Interactive Video Media Controls Bar ──
            vid_toolbar = ctk.CTkFrame(main_view, fg_color=("gray80", "gray20"), corner_radius=10)
            
            seek_row = ctk.CTkFrame(vid_toolbar, fg_color="transparent")
            seek_row.pack(fill="x", padx=12, pady=(6, 2))

            time_lbl_var = tk.StringVar(value="⏱️ 00:00 / 00:00")
            ctk.CTkLabel(seek_row, textvariable=time_lbl_var, font=ctk.CTkFont(size=11, weight="bold"), text_color="#ffb74d").pack(side="right", padx=(8, 0))

            vid_slider = ctk.CTkSlider(seek_row, from_=0, to=100, number_of_steps=100, height=16)
            vid_slider.pack(side="left", fill="x", expand=True)

            btn_row = ctk.CTkFrame(vid_toolbar, fg_color="transparent")
            btn_row.pack(fill="x", padx=12, pady=(2, 6))

            play_btn = ctk.CTkButton(btn_row, text="⏸️ Pause", font=ctk.CTkFont(size=11, weight="bold"), width=85, height=28, fg_color="#f57c00")
            play_btn.pack(side="left", padx=(0, 4))

            stop_btn = ctk.CTkButton(btn_row, text="⏹️ Stop", font=ctk.CTkFont(size=11, weight="bold"), width=75, height=28, fg_color="#c62828")
            stop_btn.pack(side="left", padx=2)

            skip_back_btn = ctk.CTkButton(btn_row, text="⏮️ -5s", font=ctk.CTkFont(size=10, weight="bold"), width=60, height=28, fg_color=("gray70", "gray35"), text_color=("gray10", "gray90"))
            skip_back_btn.pack(side="left", padx=2)

            skip_fwd_btn = ctk.CTkButton(btn_row, text="⏩ +5s", font=ctk.CTkFont(size=10, weight="bold"), width=60, height=28, fg_color=("gray70", "gray35"), text_color=("gray10", "gray90"))
            skip_fwd_btn.pack(side="left", padx=2)

            mute_btn = ctk.CTkButton(btn_row, text="🔊 Sound On", font=ctk.CTkFont(size=10, weight="bold"), width=85, height=28, fg_color="#2e7d32")
            mute_btn.pack(side="left", padx=(10, 4))

            vol_slider = ctk.CTkSlider(btn_row, from_=0, to=100, number_of_steps=100, width=90, height=14)
            vol_slider.set(80)
            vol_slider.pack(side="left", padx=2)

            open_ext_btn = ctk.CTkButton(btn_row, text="🚀 External Player", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#1565c0", hover_color="#0d47a1", height=28)
            open_ext_btn.pack(side="right")

            ftr = ctk.CTkFrame(zoom_win, fg_color=("gray88", "gray20"))
            ftr.pack(fill="x", padx=16, pady=(0, 12), ipadx=8, ipady=6)

            info_lbl = ctk.CTkLabel(ftr, text="", font=ctk.CTkFont(size=11), anchor="w")
            info_lbl.pack(side="left", padx=10)

            act_box = ctk.CTkFrame(ftr, fg_color="transparent")
            act_box.pack(side="right", padx=6)

            # ── Zoom state for Ctrl+Scroll ──
            zoom_level = [1.0]          # current zoom multiplier
            ZOOM_BASE = (900, 500)      # baseline preview size
            ZOOM_MIN = 0.2
            ZOOM_MAX = 5.0
            ZOOM_STEP = 0.15

            zoom_lbl_var = tk.StringVar(value="🔍 100%")
            zoom_indicator = ctk.CTkLabel(hdr, textvariable=zoom_lbl_var,
                                          font=ctk.CTkFont(size=10),
                                          text_color=("gray40", "gray70"), width=60)
            zoom_indicator.pack(side="right", padx=(0, 6))

            ctk.CTkButton(hdr, text="⟳ Reset Zoom",
                          command=lambda: _reset_zoom(),
                          font=ctk.CTkFont(size=10), height=26, width=85,
                          fg_color=("gray55", "gray35")).pack(side="right", padx=2)

            def _render_at_zoom():
                p = curr_file_path[0]
                fn = os.path.basename(p)
                ext_l = os.path.splitext(p)[1].lower()
                if ext_l in VID_PREVIEW_EXTS:
                    return
                z = zoom_level[0]
                w = int(ZOOM_BASE[0] * z)
                h = int(ZOOM_BASE[1] * z)
                cache_key = f"{fix_win_long_path(p)}_{w}x{h}"
                if cache_key in self._thumb_cache:
                    del self._thumb_cache[cache_key]
                self.load_file_thumbnail_async(p, target_size=(w, h), label_widget=img_lbl, filename=fn)
                pct = int(z * 100)
                zoom_lbl_var.set(f"🔍 {pct}%")

            def _reset_zoom():
                zoom_level[0] = 1.0
                _render_at_zoom()

            def _on_zoom_scroll(event):
                state = getattr(event, 'state', 0)
                ctrl_held = bool(state & 0x0004)
                if not ctrl_held:
                    return
                d = getattr(event, 'delta', 0)
                if d > 0:
                    zoom_level[0] = min(ZOOM_MAX, round(zoom_level[0] + ZOOM_STEP, 2))
                elif d < 0:
                    zoom_level[0] = max(ZOOM_MIN, round(zoom_level[0] - ZOOM_STEP, 2))
                _render_at_zoom()
                return "break"

            zoom_win.bind("<MouseWheel>", _on_zoom_scroll)

            def update_video_time_label():
                cur_sec = int(v_state['curr_frame'] / v_state['fps']) if v_state['fps'] > 0 else 0
                tot_sec = int(v_state['total_frames'] / v_state['fps']) if v_state['fps'] > 0 else 0
                cur_m, cur_s = divmod(cur_sec, 60)
                tot_m, tot_s = divmod(tot_sec, 60)
                time_lbl_var.set(f"⏱️ {cur_m:02d}:{cur_s:02d} / {tot_m:02d}:{tot_s:02d}")

            def render_video_frame():
                if not v_state['is_playing'] or not v_state['cap'] or not v_state['cap'].isOpened() or not zoom_win.winfo_exists():
                    return

                ret, frame = v_state['cap'].read()
                if not ret:
                    v_state['cap'].set(cv2.CAP_PROP_POS_FRAMES, 0)
                    v_state['curr_frame'] = 0
                    if v_state['wmp']:
                        try:
                            v_state['wmp'].controls.currentPosition = 0
                        except Exception:
                            pass
                    ret, frame = v_state['cap'].read()

                if ret and frame is not None:
                    try:
                        import cv2
                        from PIL import Image
                        import customtkinter as ctk
                        v_state['curr_frame'] = int(v_state['cap'].get(cv2.CAP_PROP_POS_FRAMES))
                        if not v_state['is_seeking']:
                            vid_slider.set(v_state['curr_frame'])
                        update_video_time_label()

                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        pil_img = Image.fromarray(rgb)
                        pil_img.thumbnail((880, 480), Image.Resampling.LANCZOS)
                        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                        if img_lbl and zoom_win.winfo_exists():
                            img_lbl.configure(image=ctk_img, text="")
                    except Exception:
                        pass

                delay_ms = max(10, int(1000.0 / v_state['fps'])) if v_state['fps'] > 0 else 33
                if v_state['is_playing'] and zoom_win.winfo_exists():
                    v_state['after_id'] = zoom_win.after(delay_ms, render_video_frame)

            def start_video():
                if not v_state['cap'] or not v_state['cap'].isOpened():
                    return
                v_state['is_playing'] = True
                play_btn.configure(text="⏸️ Pause", fg_color="#f57c00")
                if v_state['wmp']:
                    try:
                        v_state['wmp'].controls.play()
                    except Exception:
                        pass
                render_video_frame()

            def pause_video():
                v_state['is_playing'] = False
                if v_state['wmp']:
                    try:
                        v_state['wmp'].controls.pause()
                    except Exception:
                        pass
                if v_state['after_id'] and zoom_win.winfo_exists():
                    try:
                        zoom_win.after_cancel(v_state['after_id'])
                    except Exception:
                        pass
                    v_state['after_id'] = None
                play_btn.configure(text="▶️ Play", fg_color="#1565c0")

            def toggle_video_play():
                if v_state['is_playing']:
                    pause_video()
                else:
                    start_video()

            def stop_video_playback():
                pause_video()
                if v_state['wmp']:
                    try:
                        v_state['wmp'].controls.stop()
                        v_state['wmp'].controls.currentPosition = 0
                    except Exception:
                        pass
                if v_state['cap'] and v_state['cap'].isOpened():
                    try:
                        v_state['cap'].set(cv2.CAP_PROP_POS_FRAMES, 0)
                    except Exception:
                        pass
                v_state['curr_frame'] = 0
                vid_slider.set(0)
                update_video_time_label()

            def toggle_mute():
                v_state['is_muted'] = not v_state['is_muted']
                if v_state['wmp']:
                    try:
                        v_state['wmp'].settings.mute = v_state['is_muted']
                    except Exception:
                        pass
                mute_btn.configure(
                    text="🔇 Muted" if v_state['is_muted'] else "🔊 Sound On",
                    fg_color="#c62828" if v_state['is_muted'] else "#2e7d32"
                )

            def set_volume(val):
                v_state['volume'] = int(val)
                if v_state['wmp']:
                    try:
                        v_state['wmp'].settings.volume = int(val)
                    except Exception:
                        pass

            def on_slider_start(event=None):
                v_state['is_seeking'] = True

            def on_slider_release(event=None):
                v_state['is_seeking'] = False
                if v_state['cap'] and v_state['cap'].isOpened():
                    val = vid_slider.get()
                    on_slider_seek(val)

            def on_slider_drag(value):
                if not v_state['cap'] or not v_state['cap'].isOpened():
                    return
                frame_idx = max(0, min(int(value), v_state['total_frames'] - 1))
                v_state['curr_frame'] = frame_idx
                update_video_time_label()
                
                # Update Audio WMP position & Video frame in lockstep
                if v_state['fps'] > 0 and v_state['wmp']:
                    try:
                        v_state['wmp'].controls.currentPosition = frame_idx / v_state['fps']
                    except Exception:
                        pass

                try:
                    import cv2
                    from PIL import Image
                    import customtkinter as ctk
                    v_state['cap'].set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                    ret, frame = v_state['cap'].read()
                    if ret and frame is not None:
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        pil_img = Image.fromarray(rgb)
                        pil_img.thumbnail((880, 480), Image.Resampling.LANCZOS)
                        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                        if img_lbl and zoom_win.winfo_exists():
                            img_lbl.configure(image=ctk_img, text="")
                except Exception:
                    pass

            def on_slider_seek(value):
                if not v_state['cap'] or not v_state['cap'].isOpened():
                    return
                frame_idx = max(0, min(int(value), v_state['total_frames'] - 1))
                v_state['curr_frame'] = frame_idx
                v_state['cap'].set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                
                if v_state['fps'] > 0 and v_state['wmp']:
                    try:
                        v_state['wmp'].controls.currentPosition = frame_idx / v_state['fps']
                    except Exception:
                        pass

                try:
                    import cv2
                    from PIL import Image
                    import customtkinter as ctk
                    ret, frame = v_state['cap'].read()
                    if ret and frame is not None:
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        pil_img = Image.fromarray(rgb)
                        pil_img.thumbnail((880, 480), Image.Resampling.LANCZOS)
                        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                        if img_lbl and zoom_win.winfo_exists():
                            img_lbl.configure(image=ctk_img, text="")
                except Exception:
                    pass

                update_video_time_label()

            def skip_video_seconds(secs):
                if not v_state['fps'] or not v_state['cap']:
                    return
                delta_frames = int(secs * v_state['fps'])
                target = max(0, min(v_state['curr_frame'] + delta_frames, v_state['total_frames'] - 1))
                vid_slider.set(target)
                on_slider_seek(target)

            play_btn.configure(command=toggle_video_play)
            stop_btn.configure(command=stop_video_playback)
            skip_back_btn.configure(command=lambda: skip_video_seconds(-5))
            skip_fwd_btn.configure(command=lambda: skip_video_seconds(5))
            mute_btn.configure(command=toggle_mute)
            vol_slider.configure(command=set_volume)

            vid_slider.configure(command=on_slider_drag)
            try:
                vid_slider.bind("<ButtonPress-1>", on_slider_start)
                vid_slider.bind("<ButtonRelease-1>", on_slider_release)
            except Exception:
                pass

            open_ext_btn.configure(command=lambda: self.open_file_item(curr_file_path[0]))

            def render_sneak_preview():
                stop_video_engine()

                p = curr_file_path[0]
                fn = os.path.basename(p)
                ext_l = os.path.splitext(p)[1].lower()

                title_lbl.configure(text=f"🎬 Video Player — {fn}" if ext_l in VID_PREVIEW_EXTS else f"📷 Windows Sneak View — {fn}")

                safe = fix_win_long_path(p)
                if os.path.exists(safe):
                    stat = os.stat(safe)
                    sz_str = format_bytes(stat.st_size)
                    mtime_str = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    info_txt = f"File: {fn}\nSize: {sz_str}  |  Modified: {mtime_str}\nLocation: {p}"
                    info_lbl.configure(text=info_txt)

                zoom_level[0] = 1.0
                zoom_lbl_var.set("🔍 100%")

                if ext_l in VID_PREVIEW_EXTS:
                    vid_toolbar.pack(fill="x", padx=10, pady=(0, 6))
                    try:
                        import cv2
                        v_state['cap'] = cv2.VideoCapture(safe)
                        if v_state['cap'].isOpened():
                            v_state['fps'] = v_state['cap'].get(cv2.CAP_PROP_FPS) or 30.0
                            v_state['total_frames'] = int(v_state['cap'].get(cv2.CAP_PROP_FRAME_COUNT)) or 1
                            v_state['curr_frame'] = 0
                            vid_slider.configure(from_=0, to=max(1, v_state['total_frames'] - 1), number_of_steps=max(1, v_state['total_frames']))
                            vid_slider.set(0)
                            update_video_time_label()

                            # Initialize Windows Media Player Audio Engine
                            try:
                                import win32com.client
                                v_state['wmp'] = win32com.client.Dispatch("WMPlayer.OCX")
                                v_state['wmp'].URL = safe
                                v_state['wmp'].settings.volume = v_state['volume']
                                v_state['wmp'].settings.mute = v_state['is_muted']
                            except Exception:
                                v_state['wmp'] = None

                            start_video()
                    except Exception:
                        self.load_file_thumbnail_async(p, target_size=ZOOM_BASE, label_widget=img_lbl, filename=fn)
                else:
                    vid_toolbar.pack_forget()
                    self.load_file_thumbnail_async(p, target_size=ZOOM_BASE, label_widget=img_lbl, filename=fn)

            render_sneak_preview()

            # Stepper Navigation if in a group
            if files_list and len(files_list) > 1:
                nav_sub = ctk.CTkFrame(ftr, fg_color="transparent")
                nav_sub.pack(side="left", padx=20)

                def nav_prev():
                    paths = [f['path'] for f in files_list]
                    if curr_file_path[0] in paths:
                        idx = paths.index(curr_file_path[0])
                        prev_p = paths[(idx - 1) % len(paths)]
                        curr_file_path[0] = prev_p
                        render_sneak_preview()

                def nav_next():
                    paths = [f['path'] for f in files_list]
                    if curr_file_path[0] in paths:
                        idx = paths.index(curr_file_path[0])
                        next_p = paths[(idx + 1) % len(paths)]
                        curr_file_path[0] = next_p
                        render_sneak_preview()

                ctk.CTkButton(nav_sub, text="◀ Prev Copy", command=nav_prev, font=ctk.CTkFont(size=10, weight="bold"), height=28, width=90, fg_color="#1565c0").pack(side="left", padx=2)
                ctk.CTkButton(nav_sub, text="Next Copy ▶", command=nav_next, font=ctk.CTkFont(size=10, weight="bold"), height=28, width=90, fg_color="#1565c0").pack(side="left", padx=2)

                def handle_key_nav(event):
                    k = event.keysym.lower()
                    if k == "left":
                        nav_prev()
                    elif k == "right":
                        nav_next()

                zoom_win.bind("<Left>", handle_key_nav)
                zoom_win.bind("<Right>", handle_key_nav)

            ctk.CTkButton(act_box, text="✏️ Rename File", command=handle_header_rename, font=ctk.CTkFont(size=11, weight="bold"), height=30, fg_color="#00838f").pack(side="left", padx=3)
            ctk.CTkButton(act_box, text="📁 Open Folder", command=lambda: self.open_file_item(curr_file_path[0]), font=ctk.CTkFont(size=11, weight="bold"), height=30, fg_color="#1565c0").pack(side="left", padx=3)
            ctk.CTkButton(act_box, text="❌ Close", command=on_close_zoom, font=ctk.CTkFont(size=11, weight="bold"), height=30, fg_color=("gray60", "gray40")).pack(side="left", padx=3)

            zoom_win.after(100, lambda: (zoom_win.lift(), zoom_win.focus_force(), zoom_win.grab_set()))

        def apply_smart_autoselect_rules(self, rule_type="newest"):
            """
            Smart Auto-Selection Engine for N-Copy Duplicate Groups.
            Rules: 'newest', 'highest_res', 'largest', 'shortest_path'.
            If ambiguous (all copies identical in date, size & res), marks group['needs_review'] = True
            and leaves checkboxes unchecked for safe manual review.
            """
            dup_groups = getattr(self, "dup_groups", [])
            if not dup_groups:
                return

            for g in dup_groups:
                files = g.get('files', [])
                if not files:
                    continue

                sizes = set(f.get('size_bytes', 0) for f in files)
                mtimes = set(f.get('stat_mtime', 0) for f in files)
                resolutions = set((f.get('width', 0), f.get('height', 0)) for f in files)

                is_ambiguous = (len(sizes) == 1 and len(mtimes) == 1 and len(resolutions) == 1)

                best_file = None
                if not is_ambiguous:
                    if rule_type == "newest":
                        best_file = max(files, key=lambda x: x.get('stat_mtime', 0))
                    elif rule_type == "highest_res":
                        best_file = max(files, key=lambda x: (x.get('width', 0) * x.get('height', 0), x.get('stat_mtime', 0)))
                    elif rule_type == "largest":
                        best_file = max(files, key=lambda x: (x.get('size_bytes', 0), x.get('stat_mtime', 0)))
                    elif rule_type == "shortest_path":
                        best_file = min(files, key=lambda x: (len(x['path']), x.get('stat_mtime', 0)))

                if is_ambiguous or not best_file:
                    g['needs_review'] = True
                    g['kept_file_path'] = None
                    for f in files:
                        p = f['path']
                        if p not in self.dup_checkbox_vars:
                            self.dup_checkbox_vars[p] = tk.BooleanVar(value=False)
                        else:
                            self.dup_checkbox_vars[p].set(False)
                else:
                    g['needs_review'] = False
                    g['kept_file_path'] = best_file['path']
                    for f in files:
                        p = f['path']
                        is_remove = (p != best_file['path'])
                        if p not in self.dup_checkbox_vars:
                            self.dup_checkbox_vars[p] = tk.BooleanVar(value=is_remove)
                        else:
                            self.dup_checkbox_vars[p].set(is_remove)

        def open_dup_resolver_modal(self):
            """Launches Pro Duplicate Conflict Resolver Modal."""
            dup_groups = getattr(self, "dup_groups", [])
            if not dup_groups:
                messagebox.showinfo("No Duplicates Found", "No duplicate file conflicts found.\n\nPlease click '🔍 Scan Duplicates' first to detect duplicate conflicts.")
                return

            # Guard: if already open, bring to front instead of opening again
            if getattr(self, '_resolver_modal_open', False):
                existing = getattr(self, '_resolver_modal_ref', None)
                if existing:
                    try:
                        existing.lift()
                        existing.focus_force()
                    except Exception:
                        pass
                return

            self.apply_smart_autoselect_rules(rule_type="newest")
            self._resolver_modal_open = True

            modal = ctk.CTkToplevel(self)
            self._resolver_modal_ref = modal  # Store reference for lift-to-front
            modal.title("🔍 Pro Duplicate Conflict Resolver Suite")
            modal.transient(self)
            # Do NOT call grab_set() here — do it after the window is shown

            def on_modal_close():
                self._resolver_modal_open = False
                self._resolver_modal_ref = None
                try:
                    modal.grab_release()
                    modal.destroy()
                except Exception:
                    pass

            modal.protocol("WM_DELETE_WINDOW", on_modal_close)

            try:
                modal.update_idletasks()
                ws = modal.winfo_screenwidth()
                hs = modal.winfo_screenheight()
                target_w = min(1380, int(ws * 0.92))
                target_h = min(880, int(hs * 0.90))
                start_x = max(20, (ws - target_w) // 2)
                start_y = max(35, (hs - target_h) // 2)
                modal.geometry(f"{target_w}x{target_h}+{start_x}+{start_y}")
                try:
                    modal.state('zoomed')
                except Exception:
                    pass
            except Exception:
                modal.geometry("1200x780+40+40")

            modal_state = {"current_index": 0, "blink_toggle": False, "reclaimed_bytes": 0}
            resolver_undo_stack = []
            initial_group_count = len(dup_groups)

            # Top Control & Tool Bar (Destination, Undo, Sort, Auto-Rule)
            top_bar = ctk.CTkFrame(modal, corner_radius=10, fg_color=("gray85", "gray20"))
            top_bar.pack(fill="x", padx=12, pady=(8, 3), ipadx=6, ipady=4)

            # Row 1: Delete folder location for unkept/deleted duplicates
            row1 = ctk.CTkFrame(top_bar, fg_color="transparent")
            row1.pack(fill="x", pady=(2, 0))

            ctk.CTkLabel(row1, text="🗑️ Delete Folder:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#ef9a9a").pack(side="left", padx=(8, 4))
            scan_root_default = self.dup_dir_var.get().strip()
            default_discard = self.dup_discard_dir_var.get().strip() or (os.path.join(scan_root_default, "_Deleted_Files") if scan_root_default else "")
            modal_discard_var = tk.StringVar(value=default_discard)
            modal_discard_entry = ctk.CTkEntry(row1, textvariable=modal_discard_var, placeholder_text="Select folder location where deleted duplicate files go...", font=ctk.CTkFont(size=10), height=26, width=240)
            modal_discard_entry.pack(side="left", padx=(0, 4))

            def pick_modal_discard():
                folder = filedialog.askdirectory(title="Select Delete Folder for Duplicate Files")
                if folder:
                    modal_discard_var.set(folder)

            ctk.CTkButton(row1, text="Browse...", command=pick_modal_discard, font=ctk.CTkFont(size=9, weight="bold"), height=26, width=65, fg_color="#c62828").pack(side="left", padx=2)
            CTkToolTip(row1, "Folder where unkept/deleted duplicate files are stored/moved during cleanup.")

            # Row 2: Single Combined Keep Folder Selection Control (Default: Original Location)
            row2 = ctk.CTkFrame(top_bar, fg_color="transparent")
            row2.pack(fill="x", pady=(2, 2))

            ctk.CTkLabel(row2, text="📁 Keep Folder:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#81c784").pack(side="left", padx=(8, 4))
            init_dest = self.dup_dest_dir_var.get().strip()
            modal_dest_var = tk.StringVar(value=init_dest)
            modal_kept_mode_var = tk.StringVar(value="custom" if init_dest else "original")

            modal_dest_entry = ctk.CTkEntry(row2, textvariable=modal_dest_var, placeholder_text="📍 Default Location (Kept files stay in original path)", font=ctk.CTkFont(size=10), height=26, width=240)
            modal_dest_entry.pack(side="left", padx=(0, 4))

            def pick_modal_dest():
                folder = filedialog.askdirectory(title="Select Custom Keep Folder for Kept Files")
                if folder:
                    modal_dest_var.set(folder)
                    modal_kept_mode_var.set("custom")
                    self.dup_dest_dir_var.set(folder)
                    if hasattr(self, 'dup_kept_mode_var'):
                        self.dup_kept_mode_var.set("custom")

            def reset_modal_dest():
                modal_dest_var.set("")
                modal_kept_mode_var.set("original")
                self.dup_dest_dir_var.set("")
                if hasattr(self, 'dup_kept_mode_var'):
                    self.dup_kept_mode_var.set("original")

            ctk.CTkButton(row2, text="📁 Change Location...", command=pick_modal_dest, font=ctk.CTkFont(size=9, weight="bold"), height=26, width=130, fg_color="#0288d1").pack(side="left", padx=2)
            ctk.CTkButton(row2, text="🧹 Default", command=reset_modal_dest, font=ctk.CTkFont(size=9, weight="bold"), height=26, width=65, fg_color=("gray75", "gray30"), text_color=("gray10", "gray90")).pack(side="left", padx=2)
            CTkToolTip(row2, "By default, kept files remain in their original location. Click 'Change Location...' to move them elsewhere.")

            # Session Undo Button (Ctrl+Z)
            def handle_undo_last_action():
                if not resolver_undo_stack:
                    messagebox.showinfo("Undo Stack Empty", "No recent actions to undo in this session.")
                    return
                undo_item = resolver_undo_stack.pop()
                restored_count = 0
                for move_info in undo_item.get("file_moves", []):
                    src_p = move_info["src"]
                    dest_p = move_info["dest"]
                    safe_d = fix_win_long_path(dest_p)
                    safe_s = fix_win_long_path(src_p)
                    if os.path.exists(safe_d):
                        try:
                            os.makedirs(os.path.dirname(safe_s), exist_ok=True)
                            shutil.move(safe_d, safe_s)
                            restored_count += 1
                        except Exception:
                            pass

                orig_group = undo_item.get("group")
                if orig_group:
                    current_groups = getattr(self, "dup_groups", [])
                    if orig_group not in current_groups:
                        saved_idx = undo_item.get("index", 0)
                        saved_idx = min(saved_idx, len(current_groups))
                        current_groups.insert(saved_idx, orig_group)
                        modal_state["current_index"] = saved_idx

                modal_state["reclaimed_bytes"] = max(0, modal_state["reclaimed_bytes"] - undo_item.get("bytes_saved", 0))
                update_progress_ui()
                render_active_group()

            btn_undo = ctk.CTkButton(top_bar, text="↩️ Undo Action (Ctrl+Z)", command=handle_undo_last_action, font=ctk.CTkFont(size=10, weight="bold"), height=28, fg_color="#7b1fa2")
            btn_undo.pack(side="left", padx=6)
            CTkToolTip(btn_undo, "Instantly restores the last deleted or moved file/group back to its original location!")

            # Sort by Wasted Space Button
            def handle_sort_by_wasted_space():
                current_groups = getattr(self, "dup_groups", [])
                if current_groups:
                    current_groups.sort(key=lambda g: sum(f['size_bytes'] for f in g['files'][1:]) if len(g['files']) > 1 else 0, reverse=True)
                    modal_state["current_index"] = 0
                    render_active_group()

            btn_sort = ctk.CTkButton(top_bar, text="🔥 Sort: Wasted Space", command=handle_sort_by_wasted_space, font=ctk.CTkFont(size=10, weight="bold"), height=28, fg_color="#e65100")
            btn_sort.pack(side="left", padx=2)
            CTkToolTip(btn_sort, "Sorts duplicate groups by wasted disk space (biggest MB/GB groups first) to maximize space recovery!")

            # Auto-Resolve Rule Dropdown Engine
            def handle_auto_resolve_rule(rule_choice):
                if "Older" in rule_choice:
                    self.apply_smart_autoselect_rules("newest")
                elif "Newer" in rule_choice:
                    self.apply_smart_autoselect_rules("newest")
                elif "Higher Resolution" in rule_choice:
                    self.apply_smart_autoselect_rules("highest_res")
                elif "Shortest Path" in rule_choice:
                    self.apply_smart_autoselect_rules("shortest_path")

                update_progress_ui()
                render_active_group()
                messagebox.showinfo("Smart Auto-Select Applied", f"⚡ Smart rules re-evaluated across all groups using rule:\n'{rule_choice}'!")

            auto_rule_var = tk.StringVar(value="⚡ Smart Auto-Select Rule...")
            rule_dropdown = ctk.CTkOptionMenu(
                top_bar,
                variable=auto_rule_var,
                values=[
                    "⚡ Smart Auto-Select Rule...",
                    "Keep Older Copy (Delete Newer)",
                    "Keep Newer Copy (Delete Older)",
                    "Keep Higher Resolution (Delete Lower)",
                    "Keep Shortest Path (Delete Deep Subfolders)"
                ],
                command=handle_auto_resolve_rule,
                font=ctk.CTkFont(size=10, weight="bold"),
                height=28,
                width=210,
                fg_color="#00838f"
            )
            rule_dropdown.pack(side="right", padx=6)
            CTkToolTip(rule_dropdown, "Automatically evaluates rules and marks duplicates for removal, leaving ambiguous groups for review!")

            # Progress & Reclaimed Space Tracker Bar
            prog_card = ctk.CTkFrame(modal, corner_radius=10, fg_color=("gray90", "gray17"))
            prog_card.pack(fill="x", padx=12, pady=(2, 4), ipadx=6, ipady=4)

            prog_lbl = ctk.CTkLabel(prog_card, text="", font=ctk.CTkFont(size=10, weight="bold"))
            prog_lbl.pack(side="left", padx=10)

            prog_bar = ctk.CTkProgressBar(prog_card, height=10, width=280, fg_color=("gray75", "gray30"), progress_color="#00c853")
            prog_bar.pack(side="right", padx=10)
            prog_bar.set(0.0)

            # Shared callback holder so update_progress_ui can call update_bulk_bar_ui
            # after it's defined later (forward reference fix)
            _callbacks = {"update_bulk_bar": None}

            def update_progress_ui():
                current_groups = getattr(self, "dup_groups", [])
                curr_cnt = len(current_groups)
                resolved = max(0, initial_group_count - curr_cnt)
                pct = (resolved / float(initial_group_count)) if initial_group_count > 0 else 0.0
                try:
                    prog_bar.set(pct)
                    prog_lbl.configure(text=f"📊 Resolution Progress: {resolved} / {initial_group_count} groups resolved ({int(pct*100)}%)  •  Remaining: {curr_cnt} groups  •  🔥 Reclaimed Space: {format_bytes(modal_state['reclaimed_bytes'])}")
                except Exception:
                    pass
                cb = _callbacks.get("update_bulk_bar")
                if cb is not None:
                    try:
                        cb()
                    except Exception:
                        pass

            # Global Bulk Action Bar (Stage 2 Requirement)
            bulk_bar = ctk.CTkFrame(modal, corner_radius=10, fg_color=("gray88", "gray18"))
            bulk_bar.pack(fill="x", padx=12, pady=(2, 4), ipadx=8, ipady=5)

            def get_global_selection_stats():
                """Queries per-file selected state across all groups."""
                sel_count = 0
                total_dups = 0
                sel_bytes = 0
                current_groups = getattr(self, "dup_groups", [])
                for g in current_groups:
                    kept_p = g.get('kept_file_path')
                    for f in g.get('files', []):
                        p = f['path']
                        if p != kept_p:
                            total_dups += 1
                        is_checked = self.dup_checkbox_vars.get(p, tk.BooleanVar(value=False)).get()
                        if is_checked:
                            sel_count += 1
                            sel_bytes += f.get('size_bytes', 0)
                return sel_count, total_dups, sel_bytes

            global_select_all_var = tk.BooleanVar(value=False)

            def toggle_select_all_duplicates():
                is_sel = global_select_all_var.get()
                current_groups = getattr(self, "dup_groups", [])
                for g in current_groups:
                    if g.get('needs_review'):
                        continue
                    kept_p = g.get('kept_file_path')
                    for f in g.get('files', []):
                        p = f['path']
                        if p in self.dup_checkbox_vars:
                            self.dup_checkbox_vars[p].set(is_sel if p != kept_p else False)
                update_bulk_bar_ui()
                render_active_group()

            chk_select_all = ctk.CTkCheckBox(
                bulk_bar,
                text="Select all duplicates",
                variable=global_select_all_var,
                command=toggle_select_all_duplicates,
                font=ctk.CTkFont(size=11, weight="bold")
            )
            chk_select_all.pack(side="left", padx=10)

            bulk_stats_lbl = ctk.CTkLabel(bulk_bar, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color="#00acc1")
            bulk_stats_lbl.pack(side="left", padx=12)

            def update_bulk_bar_ui():
                sel_cnt, tot_cnt, sel_b = get_global_selection_stats()
                try:
                    bulk_stats_lbl.configure(text=f"⚡ Global Selection: {sel_cnt} of {tot_cnt} duplicate files selected  ·  {format_bytes(sel_b)}")
                except Exception:
                    pass

            # Register the callback so update_progress_ui can call it (forward-ref fix)
            _callbacks["update_bulk_bar"] = update_bulk_bar_ui

            def handle_bulk_move_selected():
                sel_cnt, tot_cnt, sel_b = get_global_selection_stats()
                if sel_cnt == 0:
                    messagebox.showinfo("No Selection", "Please check at least one duplicate file to move.")
                    return
                dest = modal_dest_var.get().strip() or None
                if not dest:
                    dest = filedialog.askdirectory(title="Select Target Folder for Bulk Move")
                if not dest:
                    return

                confirm = messagebox.askyesno(
                    "Confirm Bulk Move",
                    f"Move {sel_cnt} selected duplicate files ({format_bytes(sel_b)}) into target folder:\n\n{dest}"
                )
                if not confirm:
                    return

                current_groups = list(getattr(self, "dup_groups", []))
                moves = []
                checked_paths = set()
                for g in current_groups:
                    for f in g.get('files', []):
                        p = f['path']
                        if self.dup_checkbox_vars.get(p, tk.BooleanVar(value=False)).get():
                            checked_paths.add(p)
                            moves.append({"src": p, "dest": os.path.join(dest, f['filename'])})

                if checked_paths:
                    res = move_duplicate_files(list(checked_paths), dest)
                    moved_ok = res.get('moved', 0)
                    modal_state["reclaimed_bytes"] += sel_b
                    resolver_undo_stack.append({
                        "type": "bulk_move",
                        "file_moves": moves,
                        "bytes_saved": sel_b
                    })

                    # Prune dup_groups: remove groups where all remaining files have been moved
                    surviving_groups = []
                    for g in list(getattr(self, "dup_groups", [])):
                        g['files'] = [f for f in g.get('files', []) if f['path'] not in checked_paths]
                        if len(g['files']) >= 2:
                            surviving_groups.append(g)
                        else:
                            # Clean up checkbox vars for removed paths
                            for f in g.get('files', []):
                                self.dup_checkbox_vars.pop(f['path'], None)
                    for p in checked_paths:
                        self.dup_checkbox_vars.pop(p, None)
                    self.dup_groups = surviving_groups

                    messagebox.showinfo("Bulk Move Complete", f"🎉 Successfully moved {moved_ok} duplicate files ({format_bytes(sel_b)})!")
                    advance_to_next_group_or_render()

            def handle_bulk_delete_selected():
                sel_cnt, tot_cnt, sel_b = get_global_selection_stats()
                if sel_cnt == 0:
                    messagebox.showinfo("No Selection", "Please check at least one duplicate file to delete.")
                    return

                confirm = messagebox.askyesno(
                    "Confirm Bulk Soft Delete",
                    f"Move {sel_cnt} selected duplicate files ({format_bytes(sel_b)}) to '_Deleted_Files/' staging folder?"
                )
                if not confirm:
                    return

                scan_root = self.dup_dir_var.get().strip()
                deleted_folder = os.path.join(scan_root, "_Deleted_Files") if (scan_root and os.path.isdir(fix_win_long_path(scan_root))) else get_system_vault_dir("TrashDuplicates")
                os.makedirs(fix_win_long_path(deleted_folder), exist_ok=True)

                current_groups = list(getattr(self, "dup_groups", []))
                moves = []
                checked_paths = set()
                for g in current_groups:
                    for f in g.get('files', []):
                        p = f['path']
                        if self.dup_checkbox_vars.get(p, tk.BooleanVar(value=False)).get():
                            checked_paths.add(p)
                            moves.append({"src": p, "dest": os.path.join(deleted_folder, f['filename'])})

                if checked_paths:
                    res = move_duplicate_files(list(checked_paths), deleted_folder)
                    moved_ok = res.get('moved', 0)
                    modal_state["reclaimed_bytes"] += sel_b
                    resolver_undo_stack.append({
                        "type": "bulk_delete",
                        "file_moves": moves,
                        "bytes_saved": sel_b
                    })

                    # Prune dup_groups: remove groups where all remaining files have been moved
                    surviving_groups = []
                    for g in list(getattr(self, "dup_groups", [])):
                        g['files'] = [f for f in g.get('files', []) if f['path'] not in checked_paths]
                        if len(g['files']) >= 2:
                            surviving_groups.append(g)
                        else:
                            for f in g.get('files', []):
                                self.dup_checkbox_vars.pop(f['path'], None)
                    for p in checked_paths:
                        self.dup_checkbox_vars.pop(p, None)
                    self.dup_groups = surviving_groups

                    messagebox.showinfo("Bulk Soft Delete Complete", f"🎉 Safely moved {moved_ok} duplicate files ({format_bytes(sel_b)}) into '_Deleted_Files/'!")
                    advance_to_next_group_or_render()

            def handle_bulk_move_all_group_files():
                all_groups = list(getattr(self, "dup_groups", []))
                if not all_groups:
                    messagebox.showinfo("No Groups", "No duplicate groups available to move.")
                    return

                all_paths = []
                for g in all_groups:
                    for f in g.get('files', []):
                        p = f['path']
                        if os.path.exists(fix_win_long_path(p)):
                            all_paths.append(p)

                if not all_paths:
                    messagebox.showinfo("No Files", "No valid files found across duplicate groups.")
                    return

                dest = modal_dest_var.get().strip() or None
                if not dest:
                    dest = filedialog.askdirectory(title=f"Select Target Destination Folder for ALL {len(all_paths)} Original & Duplicate Files")
                if not dest:
                    return

                confirm = messagebox.askyesno(
                    "Confirm Move ALL Files",
                    f"Move ALL {len(all_paths)} files (both Originals AND Duplicates across all groups) into target folder:\n\n{dest}?"
                )
                if not confirm:
                    return

                moves = []
                total_bytes = 0
                for p in all_paths:
                    fn = os.path.basename(p)
                    safe_p = fix_win_long_path(p)
                    if os.path.exists(safe_p):
                        total_bytes += os.path.getsize(safe_p)
                        moves.append({"src": p, "dest": os.path.join(dest, fn)})

                res = move_duplicate_files(all_paths, dest)
                moved_ok = res.get('moved', 0)

                modal_state["reclaimed_bytes"] += total_bytes
                resolver_undo_stack.append({
                    "type": "move_all_groups",
                    "file_moves": moves,
                    "bytes_saved": total_bytes
                })

                self.dup_checkbox_vars.clear()
                self.dup_groups = []

                messagebox.showinfo("Move All Complete", f"🎉 Successfully moved ALL {moved_ok} original & duplicate files into:\n\n{dest}")
                advance_to_next_group_or_render()

            ctk.CTkButton(bulk_bar, text="📦 Move ALL (Originals + Dups)...", command=handle_bulk_move_all_group_files, font=ctk.CTkFont(size=11, weight="bold"), height=28, fg_color="#7b1fa2").pack(side="right", padx=4)
            ctk.CTkButton(bulk_bar, text="📁 Move Selected To...", command=handle_bulk_move_selected, font=ctk.CTkFont(size=11, weight="bold"), height=28, fg_color="#f57c00").pack(side="right", padx=4)
            ctk.CTkButton(bulk_bar, text="🗑️ Delete Selected", command=handle_bulk_delete_selected, font=ctk.CTkFont(size=11, weight="bold"), height=28, fg_color="#c62828").pack(side="right", padx=4)

            # Navigation Stepper Bar
            nav_bar = ctk.CTkFrame(modal, corner_radius=10, fg_color=("gray85", "gray20"))
            nav_bar.pack(fill="x", padx=12, pady=3, ipadx=6, ipady=4)

            prev_btn = ctk.CTkButton(nav_bar, text="◀ Prev (←)", font=ctk.CTkFont(size=11, weight="bold"), width=100, height=30, fg_color="#1565c0")
            prev_btn.pack(side="left", padx=6)

            jump_box = ctk.CTkFrame(nav_bar, fg_color="transparent")
            jump_box.pack(side="left", padx=4)

            ctk.CTkLabel(jump_box, text="Group #:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 4))
            jump_entry_var = tk.StringVar(value="1")
            jump_entry = ctk.CTkEntry(jump_box, textvariable=jump_entry_var, width=48, height=26, font=ctk.CTkFont(size=11, weight="bold"))
            jump_entry.pack(side="left", padx=(0, 4))

            def do_jump():
                try:
                    val = int(jump_entry_var.get().strip())
                    filtered = get_filtered_groups()
                    if 1 <= val <= len(filtered):
                        modal_state["current_index"] = val - 1
                        render_active_group()
                    else:
                        messagebox.showwarning("Out of Range", f"Enter group # between 1 and {len(filtered)}.")
                except Exception:
                    pass

            jump_entry.bind("<Return>", lambda e: do_jump())
            ctk.CTkButton(jump_box, text="Go ➔", command=do_jump, font=ctk.CTkFont(size=10, weight="bold"), width=38, height=26, fg_color="#00838f").pack(side="left")

            # Filter Dropdown (Stage 4 Requirement)
            filter_var = tk.StringVar(value="Filter: All Groups")

            def handle_filter_change(choice):
                modal_state["current_index"] = 0
                render_active_group()

            filter_menu = ctk.CTkOptionMenu(
                nav_bar,
                variable=filter_var,
                values=["Filter: All Groups", "⚠️ Needs Review Only", "⚡ Auto-Resolved Only"],
                command=handle_filter_change,
                font=ctk.CTkFont(size=10, weight="bold"),
                height=26,
                width=165,
                fg_color="#455a64"
            )
            filter_menu.pack(side="left", padx=6)
            CTkToolTip(filter_menu, "Filter review queue by groups needing manual review vs auto-resolved!")

            def get_filtered_groups():
                current_groups = getattr(self, "dup_groups", [])
                f_choice = filter_var.get()
                if "Needs Review" in f_choice:
                    return [g for g in current_groups if g.get('needs_review')]
                elif "Auto-Resolved" in f_choice:
                    return [g for g in current_groups if not g.get('needs_review')]
                return current_groups

            title_lbl = ctk.CTkLabel(nav_bar, text="", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
            title_lbl.pack(side="left", expand=True)

            next_btn = ctk.CTkButton(nav_bar, text="Next (→) ▶", font=ctk.CTkFont(size=11, weight="bold"), width=100, height=30, fg_color="#1565c0")
            next_btn.pack(side="right", padx=6)

            gallery_scroll = ctk.CTkScrollableFrame(modal, corner_radius=12, fg_color="transparent")
            gallery_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 6))

            bot_bar = ctk.CTkFrame(modal, corner_radius=10, fg_color=("gray85", "gray20"))
            bot_bar.pack(fill="x", padx=12, pady=(0, 8), ipadx=6, ipady=4)

            ctk.CTkLabel(bot_bar, text="⌨️ Shortcuts:  [Space] Toggle Check  [A] Select All Dupes in Group  [Enter] Confirm & Next  [D] Delete Group  [M] Move Group  [←/→] Navigate  [Ctrl+Z] Undo", font=ctk.CTkFont(size=10, weight="bold"), text_color="#64b5f6").pack(side="left", padx=8)

            bot_btns = ctk.CTkFrame(bot_bar, fg_color="transparent")
            bot_btns.pack(side="right", padx=6)

            current_active_ref = {"files": [], "group": None}

            def advance_to_next_group_or_render():
                """Helper to render active group or advance to next group seamlessly."""
                update_progress_ui()
                current_groups = getattr(self, "dup_groups", [])
                if not current_groups:
                    on_modal_close()
                    messagebox.showinfo("All Conflicts Resolved", "🎉 All duplicate file conflicts resolved successfully!")
                    return
                filtered = get_filtered_groups()
                if modal_state["current_index"] >= len(filtered):
                    modal_state["current_index"] = max(0, len(filtered) - 1)
                render_active_group()

            def handle_delete_single(file_path, grp_files):
                safe_p = fix_win_long_path(file_path)
                if not os.path.exists(safe_p):
                    render_active_group()
                    return
                scan_root = self.dup_dir_var.get().strip()
                deleted_folder = os.path.join(scan_root, "_Deleted_Files") if (scan_root and os.path.isdir(fix_win_long_path(scan_root))) else get_system_vault_dir("TrashDuplicates")
                os.makedirs(fix_win_long_path(deleted_folder), exist_ok=True)
                target_dest = os.path.join(deleted_folder, os.path.basename(file_path))
                sz = os.path.getsize(safe_p)

                try:
                    # Handle filename collision in deleted_folder
                    dest_path = fix_win_long_path(target_dest)
                    if os.path.exists(dest_path):
                        name, ext = os.path.splitext(os.path.basename(file_path))
                        dest_path = fix_win_long_path(os.path.join(deleted_folder, f"{name}_{int(time.time())}{ext}"))
                    shutil.move(safe_p, dest_path)
                    moved = True
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to move file: {e}")
                    moved = False

                if moved:
                    modal_state["reclaimed_bytes"] += sz
                    resolver_undo_stack.append({
                        "type": "delete_single",
                        "file_moves": [{"src": file_path, "dest": target_dest}],
                        "group": current_active_ref["group"],
                        "index": modal_state["current_index"],
                        "bytes_saved": sz
                    })
                    self.dup_checkbox_vars.pop(file_path, None)
                    grp_files[:] = [f for f in grp_files if f['path'] != file_path]
                    if len(grp_files) < 2:
                        self.remove_group_from_memory(grp_files)
                    advance_to_next_group_or_render()

            def handle_move_single(file_path, grp_files):
                dest = modal_dest_var.get().strip() or None
                if not dest:
                    dest = filedialog.askdirectory(title="Select Target Destination Folder")
                if not dest:
                    return
                safe_p = fix_win_long_path(file_path)
                if not os.path.exists(safe_p):
                    render_active_group()
                    return
                target_dest = os.path.join(dest, os.path.basename(file_path))
                sz = os.path.getsize(safe_p)

                res = move_duplicate_files([file_path], dest)
                if res.get('moved', 0) > 0:
                    modal_state["reclaimed_bytes"] += sz
                    resolver_undo_stack.append({
                        "type": "move_single",
                        "file_moves": [{"src": file_path, "dest": target_dest}],
                        "group": current_active_ref["group"],
                        "index": modal_state["current_index"],
                        "bytes_saved": sz
                    })
                    self.dup_checkbox_vars.pop(file_path, None)
                    grp_files[:] = [f for f in grp_files if f['path'] != file_path]
                    if len(grp_files) < 2:
                        self.remove_group_from_memory(grp_files)
                    advance_to_next_group_or_render()

            def handle_delete_active_group(grp):
                if not grp:
                    return
                saved_sz = sum(f['size_bytes'] for f in grp)
                scan_root = self.dup_dir_var.get().strip()
                deleted_folder = os.path.join(scan_root, "_Deleted_Files") if (scan_root and os.path.isdir(fix_win_long_path(scan_root))) else get_system_vault_dir("TrashDuplicates")
                moves = [{"src": f['path'], "dest": os.path.join(deleted_folder, f['filename'])} for f in grp]

                self.delete_entire_group(grp, rescan=False, confirm=False, show_info=False)
                modal_state["reclaimed_bytes"] += saved_sz
                resolver_undo_stack.append({
                    "type": "delete_group",
                    "file_moves": moves,
                    "group": current_active_ref["group"],
                    "index": modal_state["current_index"],
                    "bytes_saved": saved_sz
                })
                advance_to_next_group_or_render()

            def handle_move_active_group(grp):
                if not grp:
                    return
                dest = modal_dest_var.get().strip() or None
                if not dest:
                    dest = filedialog.askdirectory(title="Select Destination Folder")
                if not dest:
                    return
                saved_sz = sum(f['size_bytes'] for f in grp)
                moves = [{"src": f['path'], "dest": os.path.join(dest, f['filename'])} for f in grp]

                self.move_entire_group(grp, target_folder=dest, rescan=False, confirm=False, show_info=False)
                modal_state["reclaimed_bytes"] += saved_sz
                resolver_undo_stack.append({
                    "type": "move_group",
                    "file_moves": moves,
                    "group": current_active_ref["group"],
                    "index": modal_state["current_index"],
                    "bytes_saved": saved_sz
                })
                advance_to_next_group_or_render()

            def render_active_group():
                filtered_groups = get_filtered_groups()
                if not filtered_groups:
                    for child in gallery_scroll.winfo_children():
                        child.destroy()
                    title_lbl.configure(text="No duplicate groups match current filter criteria.")
                    prev_btn.configure(state="disabled")
                    next_btn.configure(state="disabled")
                    return

                idx = modal_state["current_index"]
                total = len(filtered_groups)
                if idx >= total:
                    idx = max(0, total - 1)
                    modal_state["current_index"] = idx

                group = filtered_groups[idx]
                files = group['files']
                current_active_ref["files"] = files
                current_active_ref["group"] = group
                wasted_bytes = (len(files) - 1) * files[0]['size_bytes'] if len(files) > 1 else 0

                jump_entry_var.set(str(idx + 1))
                update_progress_ui()

                match_text = group['signature']
                if "100%+" in match_text:
                    match_text = match_text.replace("100%+", "Exact Match (100%)")

                needs_rev_str = "  •  ⚠️ NEEDS REVIEW" if group.get('needs_review') else ""
                title_lbl.configure(text=f"Group {idx + 1} of {total}  •  {match_text}{needs_rev_str}  •  🔥 {format_bytes(wasted_bytes)} Wasted")
                prev_btn.configure(state="normal" if idx > 0 else "disabled")
                next_btn.configure(state="normal" if idx < total - 1 else "disabled")

                for child in gallery_scroll.winfo_children():
                    child.destroy()

                # Active Group Batch Actions Toolbar
                grp_act_bar = ctk.CTkFrame(gallery_scroll, corner_radius=10, fg_color=("gray88", "gray22"))
                grp_act_bar.pack(fill="x", pady=(0, 6), ipadx=6, ipady=3)

                ctk.CTkLabel(grp_act_bar, text=f"⚡ Group Actions ({len(files)} Copies in Group):", font=ctk.CTkFont(size=11, weight="bold"), text_color="#64b5f6").pack(side="left", padx=8)

                ctk.CTkButton(
                    grp_act_bar,
                    text="🔥 Delete ALL Copies",
                    command=lambda grp=files: handle_delete_active_group(grp),
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color="#c62828",
                    hover_color="#b71c1c",
                    height=26
                ).pack(side="left", padx=3)

                ctk.CTkButton(
                    grp_act_bar,
                    text="📁 Move ALL Copies...",
                    command=lambda grp=files: handle_move_active_group(grp),
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color="#f57c00",
                    hover_color="#e65100",
                    height=26
                ).pack(side="left", padx=3)

                def toggle_blink_compare():
                    modal_state["blink_toggle"] = not modal_state.get("blink_toggle", False)
                    render_active_group()

                ctk.CTkButton(
                    grp_act_bar,
                    text="⚡ Blink/Compare Images" if not modal_state.get("blink_toggle") else "⚡ Show All Cards",
                    command=toggle_blink_compare,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color="#00838f" if not modal_state.get("blink_toggle") else "#d32f2f",
                    height=26
                ).pack(side="right", padx=6)
                CTkToolTip(grp_act_bar, "Toggles blinking between Left and Right image in place to spot micro visual differences!")

                # ── Smart Select + Execute Bar ──────────────────────────────────────────────
                smart_bar = ctk.CTkFrame(gallery_scroll, corner_radius=10, fg_color=("gray85", "gray20"))
                smart_bar.pack(fill="x", pady=(0, 6), ipadx=6, ipady=4)

                ctk.CTkLabel(smart_bar, text="🎯 Smart Select:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#a5d6a7").pack(side="left", padx=(8, 4))

                def _pick_keep_by_rule(rule):
                    """Auto-pick the keep winner by rule across ALL duplicate groups in session, mark others checked."""
                    all_groups = getattr(self, "dup_groups", [])
                    if not all_groups:
                        return

                    for grp_ref in all_groups:
                        grp_files = grp_ref.get('files', [])
                        if not grp_files:
                            continue
                        try:
                            if rule == "oldest":
                                winner = min(grp_files, key=lambda f: f.get('stat_mtime', f.get('mtime', float('inf'))))
                            elif rule == "newest":
                                winner = max(grp_files, key=lambda f: f.get('stat_mtime', f.get('mtime', 0)))
                            elif rule == "highest_res":
                                def res_key(f):
                                    r = f.get('resolution')
                                    if r and isinstance(r, (list, tuple)) and len(r) == 2:
                                        return r[0] * r[1]
                                    return f.get('width', 0) * f.get('height', 0)
                                winner = max(grp_files, key=lambda f: (res_key(f), f.get('size_bytes', 0)))
                            elif rule == "shortest_path":
                                winner = min(grp_files, key=lambda f: len(f.get('path', '')))
                            elif rule == "longest_path":
                                winner = max(grp_files, key=lambda f: len(f.get('path', '')))
                            elif rule == "largest":
                                winner = max(grp_files, key=lambda f: f.get('size_bytes', 0))
                            else:
                                continue
                        except Exception:
                            continue

                        keep_path = winner['path']
                        grp_ref['kept_file_path'] = keep_path
                        grp_ref['needs_review'] = False

                        # Mark winner as is_original=True, others as False
                        for fi in grp_files:
                            p = fi['path']
                            fi['is_original'] = (p == keep_path)
                            if p in self.dup_checkbox_vars:
                                self.dup_checkbox_vars[p].set(p != keep_path)
                            else:
                                self.dup_checkbox_vars[p] = tk.BooleanVar(value=(p != keep_path))

                    update_bulk_bar_ui()
                    render_active_group()  # Re-render active group cards

                def _check_all_in_all_groups():
                    for grp in getattr(self, "dup_groups", []):
                        for fi in grp.get('files', []):
                            p = fi['path']
                            if p in self.dup_checkbox_vars:
                                self.dup_checkbox_vars[p].set(not fi.get('is_original', False))
                            else:
                                self.dup_checkbox_vars[p] = tk.BooleanVar(value=not fi.get('is_original', False))
                    update_bulk_bar_ui()
                    render_active_group()

                def _uncheck_all_in_all_groups():
                    for var in self.dup_checkbox_vars.values():
                        var.set(False)
                    update_bulk_bar_ui()
                    render_active_group()

                def _execute_checked_in_group(grp_files=files, grp_ref=group):
                    """Move all checked files in this group to discard folder and advance."""
                    discard_folder = modal_discard_var.get().strip()
                    if not discard_folder:
                        scan_root = self.dup_dir_var.get().strip()
                        discard_folder = os.path.join(scan_root, "_Deleted_Files") if (scan_root and os.path.isdir(fix_win_long_path(scan_root))) else get_system_vault_dir("TrashDuplicates")
                    try:
                        os.makedirs(fix_win_long_path(discard_folder), exist_ok=True)
                    except Exception:
                        pass

                    checked = [fi for fi in grp_files if self.dup_checkbox_vars.get(fi['path'], tk.BooleanVar(value=False)).get()]
                    if not checked:
                        messagebox.showinfo("No Selection", "Please check at least one file to discard, or use a Smart Select button first.")
                        return

                    moves_done = []
                    bytes_freed = 0
                    for fi in checked:
                        p = fi['path']
                        safe_src = fix_win_long_path(p)
                        if not os.path.exists(safe_src):
                            continue
                        fn = fi['filename']
                        dest_path = fix_win_long_path(os.path.join(discard_folder, fn))
                        if os.path.exists(dest_path):
                            name, ext = os.path.splitext(fn)
                            dest_path = fix_win_long_path(os.path.join(discard_folder, f"{name}_{int(time.time())}{ext}"))
                        try:
                            shutil.move(safe_src, dest_path)
                            bytes_freed += fi.get('size_bytes', 0)
                            moves_done.append({"src": p, "dest": os.path.join(discard_folder, fn)})
                            self.dup_checkbox_vars.pop(p, None)
                        except Exception as e:
                            messagebox.showerror("Error", f"Could not move '{fn}': {e}")
                            return

                    if moves_done:
                        modal_state["reclaimed_bytes"] += bytes_freed
                        resolver_undo_stack.append({
                            "type": "execute_checked",
                            "file_moves": moves_done,
                            "group": grp_ref,
                            "index": modal_state["current_index"],
                            "bytes_saved": bytes_freed
                        })
                        # Prune resolved groups
                        remaining = [fi for fi in grp_files if fi['path'] not in {m['src'] for m in moves_done}]
                        if len(remaining) < 2:
                            self.remove_group_from_memory(grp_files)
                        else:
                            grp_ref['files'] = remaining
                        advance_to_next_group_or_render()

                # Smart Select Buttons
                smart_btns_spec = [
                    ("⏰ Keep Oldest",    "#1b5e20", "oldest",       "Mark the OLDEST file (by date) as keep, check all others"),
                    ("⚡ Keep Newest",    "#0d47a1", "newest",       "Mark the NEWEST file (by date) as keep, check all others"),
                    ("📐 Highest Res",    "#4a148c", "highest_res",  "Mark the HIGHEST resolution image as keep (images only)"),
                    ("📍 Shortest Path",  "#e65100", "shortest_path","Mark the file with the SHORTEST folder path as keep"),
                    ("📦 Largest File",   "#37474f", "largest",      "Mark the LARGEST file (by size) as keep"),
                ]
                for btn_text, btn_color, rule, tip in smart_btns_spec:
                    b = ctk.CTkButton(
                        smart_bar, text=btn_text,
                        command=lambda r=rule: _pick_keep_by_rule(r),
                        font=ctk.CTkFont(size=10, weight="bold"),
                        fg_color=btn_color, height=26, width=108
                    )
                    b.pack(side="left", padx=3)
                    CTkToolTip(b, tip)

                # Divider
                ctk.CTkLabel(smart_bar, text="│", font=ctk.CTkFont(size=14), text_color=("gray60", "gray50")).pack(side="left", padx=4)

                # Check All / Uncheck All
                ctk.CTkButton(
                    smart_bar, text="✓ Check All",
                    command=_check_all_in_all_groups,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color=("gray60", "gray40"), height=26, width=86
                ).pack(side="left", padx=2)
                CTkToolTip(smart_bar, "Check all duplicate copies across ALL groups as 'to remove'")

                ctk.CTkButton(
                    smart_bar, text="✗ Clear All",
                    command=_uncheck_all_in_all_groups,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color=("gray55", "gray35"), height=26, width=80
                ).pack(side="left", padx=2)
                CTkToolTip(smart_bar, "Clear check selection across ALL groups")

                # Divider
                ctk.CTkLabel(smart_bar, text="│", font=ctk.CTkFont(size=14), text_color=("gray60", "gray50")).pack(side="left", padx=4)

                # Execute & Next — the big green power button
                ctk.CTkButton(
                    smart_bar, text="✅ Execute & Next →",
                    command=_execute_checked_in_group,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color="#00695c", hover_color="#004d40",
                    height=26, width=130
                ).pack(side="left", padx=4)
                CTkToolTip(smart_bar, "Move all CHECKED files in this group to the Discard Folder, then advance to the next group")


                diff_mtime = len(set(f['mtime_str'] for f in files)) > 1
                diff_path = len(set(f['rel_path'] for f in files)) > 1
                diff_res = len(set(f.get('res_str', '') for f in files)) > 1
                diff_size = len(set(f['size_bytes'] for f in files)) > 1

                grid_f = ctk.CTkFrame(gallery_scroll, fg_color="transparent")
                grid_f.pack(fill="both", expand=True)

                render_files = files
                if modal_state.get("blink_toggle") and len(files) >= 2:
                    render_files = [files[1]]

                # Adaptive cards-per-row based on number of files in group
                n_files = len(render_files)
                if n_files <= 2:
                    cards_per_row = 2
                elif n_files <= 4:
                    cards_per_row = 2
                elif n_files <= 6:
                    cards_per_row = 3
                else:
                    cards_per_row = 4

                # Cap displayed cards at 12 to prevent UI lockup for huge groups
                MAX_CARDS = 12
                if len(render_files) > MAX_CARDS:
                    overflow_count = len(render_files) - MAX_CARDS
                    render_files = render_files[:MAX_CARDS]
                    ctk.CTkLabel(
                        gallery_scroll,
                        text=f"⚠️ Showing first {MAX_CARDS} of {n_files} files. Use bulk actions or Smart Select to resolve.",
                        font=ctk.CTkFont(size=10, weight="bold"),
                        text_color="#ffcc80"
                    ).pack(pady=(0, 4))

                for col_idx, f in enumerate(render_files):
                    row_idx = col_idx // cards_per_row
                    grid_col = col_idx % cards_per_row
                    grid_f.grid_columnconfigure(grid_col, weight=1)

                    f_path = f['path']
                    if f_path not in self.dup_checkbox_vars:
                        var = tk.BooleanVar(value=False)
                        self.dup_checkbox_vars[f_path] = var
                    else:
                        var = self.dup_checkbox_vars[f_path]

                    card = ctk.CTkFrame(grid_f, corner_radius=12, fg_color=("gray90", "gray18"))
                    card.grid(row=row_idx, column=grid_col, sticky="nsew", padx=6, pady=6)
                    CTkToolTip(card, f"Full Path: {f_path}")

                    hdr = ctk.CTkFrame(card, fg_color="transparent")
                    hdr.pack(fill="x", padx=10, pady=6)

                    chk = ctk.CTkCheckBox(hdr, text="Remove copy", variable=var, command=update_bulk_bar_ui, font=ctk.CTkFont(size=11, weight="bold"))
                    chk.pack(side="left")

                    sim_pct = f.get('match_percent', 100.0)
                    kept_p = group.get('kept_file_path')
                    if group.get('needs_review'):
                        ctk.CTkLabel(hdr, text="⚠️ NEEDS REVIEW", font=ctk.CTkFont(size=10, weight="bold"), fg_color="#f57c00", text_color="white", corner_radius=5, padx=8, pady=3).pack(side="right")
                    elif kept_p and f_path == kept_p:
                        ctk.CTkLabel(hdr, text="⭐ [KEEP] ORIGINAL", font=ctk.CTkFont(size=10, weight="bold"), fg_color="#1b5e20", text_color="white", corner_radius=5, padx=8, pady=3).pack(side="right")
                    else:
                        pct_label = "Exact Match" if sim_pct >= 100 else f"{sim_pct:.1f}% Match"
                        ctk.CTkLabel(hdr, text=f"👯 [COPY] DUPLICATE ({pct_label})", font=ctk.CTkFont(size=10, weight="bold"), fg_color="#6a1b9a", text_color="white", corner_radius=5, padx=8, pady=3).pack(side="right")

                    act_tb = ctk.CTkFrame(card, fg_color="transparent")
                    act_tb.pack(fill="x", padx=8, pady=(0, 4))

                    def do_keep_only_this(target_p=f_path, grp_ref=group):
                        """
                        Immediately executes: moves all NON-kept copies to the discard folder,
                        marks the target as the keeper, updates dup_groups, and auto-advances.
                        """
                        # Resolve Delete folder (where unkept files go)
                        discard_folder = modal_discard_var.get().strip()
                        if not discard_folder:
                            scan_root = self.dup_dir_var.get().strip()
                            if scan_root and os.path.isdir(fix_win_long_path(scan_root)):
                                discard_folder = os.path.join(scan_root, "_Deleted_Files")
                            else:
                                discard_folder = filedialog.askdirectory(title="Select Delete Folder Location for Duplicate Files")
                                if discard_folder:
                                    modal_discard_var.set(discard_folder)
                        if not discard_folder:
                            messagebox.showwarning("No Delete Folder Selected", "Please select a Delete Folder location where unkept/deleted files should be stored!")
                            return

                        try:
                            os.makedirs(fix_win_long_path(discard_folder), exist_ok=True)
                        except Exception:
                            pass

                        grp_ref['kept_file_path'] = target_p
                        grp_ref['needs_review'] = False

                        moves_done = []
                        bytes_freed = 0
                        for file_item in list(grp_ref['files']):
                            p_item = file_item['path']
                            if p_item == target_p:
                                file_item['is_original'] = True
                                continue  # This is the one to KEEP — skip
                            file_item['is_original'] = False
                            safe_src = fix_win_long_path(p_item)
                            if not os.path.exists(safe_src):
                                continue
                            fn = file_item['filename']
                            dest_path = fix_win_long_path(os.path.join(discard_folder, fn))
                            # Handle filename collision
                            if os.path.exists(dest_path):
                                name, ext = os.path.splitext(fn)
                                dest_path = fix_win_long_path(os.path.join(discard_folder, f"{name}_{int(time.time())}{ext}"))
                            try:
                                shutil.move(safe_src, dest_path)
                                bytes_freed += file_item.get('size_bytes', 0)
                                moves_done.append({"src": p_item, "dest": dest_path})
                                self.dup_checkbox_vars.pop(p_item, None)
                            except Exception as e:
                                messagebox.showerror("Error Moving File", f"Could not move '{fn}': {e}")
                                return

                        # If Kept File Mode is "custom", move the kept file to Move-To folder!
                        if modal_kept_mode_var.get() == "custom":
                            move_to_folder = modal_dest_var.get().strip()
                            if not move_to_folder:
                                move_to_folder = filedialog.askdirectory(title="Select Destination Folder for Kept File")
                                if move_to_folder:
                                    modal_dest_var.set(move_to_folder)
                            if move_to_folder and os.path.exists(fix_win_long_path(target_p)):
                                try:
                                    os.makedirs(fix_win_long_path(move_to_folder), exist_ok=True)
                                    fn_kept = os.path.basename(target_p)
                                    kept_dest = fix_win_long_path(os.path.join(move_to_folder, fn_kept))
                                    if os.path.exists(kept_dest):
                                        n_k, e_k = os.path.splitext(fn_kept)
                                        kept_dest = fix_win_long_path(os.path.join(move_to_folder, f"{n_k}_{int(time.time())}{e_k}"))
                                    shutil.move(fix_win_long_path(target_p), kept_dest)
                                    moves_done.append({"src": target_p, "dest": kept_dest})
                                except Exception as ex_kept:
                                    messagebox.showerror("Error Moving Kept File", f"Could not move kept file: {ex_kept}")

                        if moves_done:
                            modal_state["reclaimed_bytes"] += bytes_freed
                            resolver_undo_stack.append({
                                "type": "keep_only_this",
                                "file_moves": moves_done,
                                "group": grp_ref,
                                "index": modal_state["current_index"],
                                "bytes_saved": bytes_freed
                            })
                            # Remove the group from memory since it's now resolved
                            self.remove_group_from_memory([{"path": target_p}])  # Removes the group containing target_p
                            advance_to_next_group_or_render()
                        else:
                            # Nothing to move (either already moved or only 1 file)
                            self.remove_group_from_memory(grp_ref.get('files', []))
                            advance_to_next_group_or_render()

                    def handle_card_rename(target_p=f_path):
                        res_p = self.rename_file_in_session(target_p, parent_window=modal)
                        if res_p:
                            render_active_group()

                    ctk.CTkButton(
                        act_tb,
                        text="⭐ Keep Only This",
                        command=do_keep_only_this,
                        font=ctk.CTkFont(size=10, weight="bold"),
                        fg_color="#1b5e20",
                        height=26
                    ).pack(side="left", fill="x", expand=True, padx=2)

                    ctk.CTkButton(
                        act_tb,
                        text="✏️ Rename",
                        command=handle_card_rename,
                        font=ctk.CTkFont(size=10, weight="bold"),
                        fg_color="#00838f",
                        height=26,
                        width=65
                    ).pack(side="left", padx=2)
                    CTkToolTip(act_tb, "Rename this duplicate file on disk")

                    def open_card_overflow_menu(file_path=f_path, grp_files=files):
                        top_menu = ctk.CTkToplevel(modal)
                        top_menu.title("Actions Menu")
                        top_menu.geometry("280x250")
                        top_menu.transient(modal)
                        top_menu.grab_set()
                        top_menu.after(100, lambda: (top_menu.lift(), top_menu.focus_force()))

                        ctk.CTkLabel(top_menu, text=f"📄 {os.path.basename(file_path)}", font=ctk.CTkFont(size=11, weight="bold")).pack(pady=10)

                        ctk.CTkButton(top_menu, text="✏️ Rename File...", command=lambda: [top_menu.destroy(), handle_card_rename(file_path)], font=ctk.CTkFont(size=11), height=28, fg_color="#00838f").pack(fill="x", padx=16, pady=3)
                        ctk.CTkButton(top_menu, text="📁 Move Single File...", command=lambda: [top_menu.destroy(), handle_move_single(file_path, grp_files)], font=ctk.CTkFont(size=11), height=28, fg_color="#f57c00").pack(fill="x", padx=16, pady=3)
                        ctk.CTkButton(top_menu, text="🗑️ Move to _Deleted_Files/", command=lambda: [top_menu.destroy(), handle_delete_single(file_path, grp_files)], font=ctk.CTkFont(size=11), height=28, fg_color="#c62828").pack(fill="x", padx=16, pady=3)
                        ctk.CTkButton(top_menu, text="↗ Open Location", command=lambda: [top_menu.destroy(), self.open_file_item(file_path)], font=ctk.CTkFont(size=11), height=28, fg_color=("gray70", "gray30")).pack(fill="x", padx=16, pady=3)
                        ctk.CTkButton(top_menu, text="📷 High-Res Zoom Lightbox", command=lambda: [top_menu.destroy(), self.open_image_zoom_modal(file_path, group_files=grp_files, parent_win=modal)], font=ctk.CTkFont(size=11), height=28, fg_color="#00838f").pack(fill="x", padx=16, pady=3)

                    ctk.CTkButton(
                        act_tb,
                        text="⋯",
                        command=open_card_overflow_menu,
                        font=ctk.CTkFont(size=12, weight="bold"),
                        width=32,
                        height=26,
                        fg_color=("gray75", "gray32")
                    ).pack(side="right", padx=2)

                    prev_b = ctk.CTkFrame(card, fg_color=("gray82", "gray15"), corner_radius=10, height=200)
                    prev_b.pack(fill="x", padx=10, pady=4)
                    prev_b.pack_propagate(False)

                    img_l = ctk.CTkLabel(prev_b, text="📷 Click for Windows Sneak View", font=ctk.CTkFont(size=11), text_color="gray50")
                    img_l.pack(expand=True)
                    img_l.bind("<Button-1>", lambda e, p=f_path, g_f=files: self.open_image_zoom_modal(p, group_files=g_f, parent_win=modal))
                    img_l.configure(cursor="hand2")

                    self.load_file_thumbnail_async(f_path, target_size=(340, 180), label_widget=img_l, filename=f['filename'])

                    info = ctk.CTkFrame(card, fg_color="transparent")
                    info.pack(fill="x", padx=10, pady=6)

                    rel = os.path.dirname(f['rel_path']) or "Root Directory"
                    loc_color = "#00e5ff" if diff_path else ("gray30", "gray70")
                    ctk.CTkLabel(info, text=f"📁 Location: {rel}", font=ctk.CTkFont(size=10, weight="bold" if diff_path else "normal"), text_color=loc_color, anchor="w").pack(fill="x", pady=1)

                    name_lbl = ctk.CTkLabel(info, text=f"📄 Name: {f['filename']} (Click to Rename)", font=ctk.CTkFont(size=10, weight="bold"), text_color="#64b5f6", anchor="w", cursor="hand2")
                    name_lbl.pack(fill="x", pady=1)
                    name_lbl.bind("<Button-1>", lambda e, p=f_path: handle_card_rename(p))
                    CTkToolTip(name_lbl, "Click to rename this file on disk")

                    date_color = "#ff9800" if diff_mtime else ("gray40", "gray65")
                    ctk.CTkLabel(info, text=f"📅 Modified: {f['mtime_str']}", font=ctk.CTkFont(size=10, weight="bold" if diff_mtime else "normal"), text_color=date_color, anchor="w").pack(fill="x", pady=1)

                    sz_color = "#ff4081" if diff_size else ("gray40", "gray65")
                    ctk.CTkLabel(info, text=f"⚖️ Size: {f['size_str']}", font=ctk.CTkFont(size=10, weight="bold" if diff_size else "normal"), text_color=sz_color, anchor="w").pack(fill="x", pady=1)

                    if f.get('res_str'):
                        res_color = "#ffd600" if diff_res else "#00acc1"
                        ctk.CTkLabel(info, text=f"📷 Resolution: {f['res_str']}", font=ctk.CTkFont(size=10, weight="bold"), text_color=res_color, anchor="w").pack(fill="x", pady=1)

            def prev_group():
                if modal_state["current_index"] > 0:
                    modal_state["current_index"] -= 1
                    render_active_group()

            def next_group():
                filtered = get_filtered_groups()
                if modal_state["current_index"] < len(filtered) - 1:
                    modal_state["current_index"] += 1
                    render_active_group()

            prev_btn.configure(command=prev_group)
            next_btn.configure(command=next_group)

            def handle_key_shortcut(event):
                key = event.keysym.lower()
                filtered = get_filtered_groups()
                if not filtered or modal_state["current_index"] >= len(filtered):
                    return
                active_group = filtered[modal_state["current_index"]]
                active_files = active_group['files']

                if key == "left":
                    prev_group()
                elif key == "right":
                    next_group()
                elif key == "space":
                    if active_files:
                        p0 = active_files[0]['path']
                        if p0 in self.dup_checkbox_vars:
                            v = self.dup_checkbox_vars[p0]
                            v.set(not v.get())
                            update_bulk_bar_ui()
                elif key == "a":
                    kept_p = active_group.get('kept_file_path')
                    for f in active_files:
                        p = f['path']
                        if p in self.dup_checkbox_vars:
                            self.dup_checkbox_vars[p].set(p != kept_p)
                    update_bulk_bar_ui()
                    render_active_group()
                elif key in ("return", "kp_enter"):
                    advance_to_next_group_or_render()
                elif key == "d":
                    handle_delete_active_group(active_files)
                elif key == "m":
                    handle_move_active_group(active_files)
                elif key in ("z", "undo") and (event.state & 4):
                    handle_undo_last_action()

            modal.bind("<Key>", handle_key_shortcut)

            ctk.CTkButton(bot_btns, text="🔥 Delete Group [D]", command=lambda: handle_delete_active_group(current_active_ref["files"]), font=ctk.CTkFont(size=10, weight="bold"), fg_color="#c62828", height=28).pack(side="left", padx=2)
            ctk.CTkButton(bot_btns, text="📁 Move Group [M]...", command=lambda: handle_move_active_group(current_active_ref["files"]), font=ctk.CTkFont(size=10, weight="bold"), fg_color="#f57c00", height=28).pack(side="left", padx=2)
            ctk.CTkButton(bot_btns, text="❌ Close Popup", command=on_modal_close, font=ctk.CTkFont(size=10, weight="bold"), fg_color=("gray70", "gray35"), height=28).pack(side="left", padx=2)

            render_active_group()
            update_bulk_bar_ui()

            # Bring modal to front and activate grab AFTER the window is fully built and rendered
            def _finalize_modal():
                try:
                    modal.lift()
                    modal.focus_force()
                    modal.grab_set()
                except Exception:
                    pass

            modal.after(150, _finalize_modal)


        def render_dup_cards_page(self, reset=True):
            if reset:
                self.dup_displayed_count = 0
                self.dup_card_widgets = []
                for widget in self.dup_cards_scroll.winfo_children():
                    widget.destroy()
            else:
                if hasattr(self, 'dup_load_more_frame') and self.dup_load_more_frame:
                    try:
                        self.dup_load_more_frame.destroy()
                    except Exception:
                        pass

            query = getattr(self, "dup_search_var", tk.StringVar()).get().strip().lower()
            all_groups = getattr(self, "dup_groups", [])

            if query:
                matching_groups = [
                    g for g in all_groups
                    if any(query in f['filename'].lower() or query in f['path'].lower() for f in g['files'])
                ]
            else:
                matching_groups = all_groups

            if not matching_groups:
                for widget in self.dup_cards_scroll.winfo_children():
                    widget.destroy()
                ctk.CTkLabel(
                    self.dup_cards_scroll,
                    text="🎉 No matching duplicate file conflicts found!",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="#81c784"
                ).pack(pady=40)
                return

            batch_size = 15
            start_idx = self.dup_displayed_count
            end_idx = min(len(matching_groups), start_idx + batch_size)

            batch = matching_groups[start_idx:end_idx]
            for g in batch:
                card_widget = self.render_group_card(g)
                self.dup_card_widgets.append((g, card_widget))

            self.dup_displayed_count = end_idx

            if self.dup_displayed_count < len(matching_groups):
                rem = len(matching_groups) - self.dup_displayed_count
                self.dup_load_more_frame = ctk.CTkFrame(self.dup_cards_scroll, fg_color="transparent")
                self.dup_load_more_frame.pack(fill="x", pady=15)

                btn_box = ctk.CTkFrame(self.dup_load_more_frame, fg_color="transparent")
                btn_box.pack(anchor="center")

                lbl = ctk.CTkLabel(
                    btn_box,
                    text=f"Showing {self.dup_displayed_count} of {len(matching_groups)} duplicate groups ({rem} remaining)",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=("gray40", "gray60")
                )
                lbl.pack(pady=(0, 6))

                ctk.CTkButton(
                    btn_box,
                    text=f"➕ Load Next {min(15, rem)} Groups",
                    command=lambda: self.render_dup_cards_page(reset=False),
                    font=ctk.CTkFont(size=11, weight="bold"),
                    fg_color="#0288d1",
                    height=30,
                    width=180
                ).pack(side="left", padx=4)

                ctk.CTkButton(
                    btn_box,
                    text="⚡ Load All Remaining Groups",
                    command=self.load_all_dup_cards,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    fg_color="#7b1fa2",
                    height=30,
                    width=190
                ).pack(side="left", padx=4)

        def load_all_dup_cards(self):
            all_groups = getattr(self, "dup_groups", [])
            self.dup_displayed_count = 0
            self.render_dup_cards_page(reset=True)
            while self.dup_displayed_count < len(all_groups):
                self.render_dup_cards_page(reset=False)

        def filter_dup_cards(self):
            self.render_dup_cards_page(reset=True)

        def open_file_item(self, path):
            safe_p = fix_win_long_path(path)
            if os.path.exists(safe_p):
                if sys.platform == 'win32':
                    subprocess.Popen(['explorer', '/select,', os.path.normpath(path)])
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', '-R', path])
                else:
                    subprocess.Popen(['xdg-open', os.path.dirname(path)])

        def auto_select_keep_oldest(self):
            for g in getattr(self, "dup_groups", []):
                files = g['files']
                if not files:
                    continue
                sorted_by_oldest = sorted(files, key=lambda x: x.get('stat_mtime', 0))
                keep_path = sorted_by_oldest[0]['path']
                g['kept_file_path'] = keep_path
                g['needs_review'] = False
                for f in files:
                    p = f['path']
                    f['is_original'] = (p == keep_path)
                    if p in self.dup_checkbox_vars:
                        self.dup_checkbox_vars[p].set(p != keep_path)
                    else:
                        self.dup_checkbox_vars[p] = tk.BooleanVar(value=(p != keep_path))
            self.update_dup_action_label()
            self.render_dup_cards_page(reset=True)

        def auto_select_keep_newest(self):
            for g in getattr(self, "dup_groups", []):
                files = g['files']
                if not files:
                    continue
                sorted_by_newest = sorted(files, key=lambda x: x.get('stat_mtime', 0), reverse=True)
                keep_path = sorted_by_newest[0]['path']
                g['kept_file_path'] = keep_path
                g['needs_review'] = False
                for f in files:
                    p = f['path']
                    f['is_original'] = (p == keep_path)
                    if p in self.dup_checkbox_vars:
                        self.dup_checkbox_vars[p].set(p != keep_path)
                    else:
                        self.dup_checkbox_vars[p] = tk.BooleanVar(value=(p != keep_path))
            self.update_dup_action_label()
            self.render_dup_cards_page(reset=True)

        def auto_select_keep_highest_res(self):
            for g in getattr(self, "dup_groups", []):
                files = g['files']
                if not files:
                    continue
                sorted_by_res = sorted(files, key=lambda x: (-(x.get('width', 0) * x.get('height', 0) or x.get('megapixels', 0)), -x.get('size_bytes', 0), x.get('stat_mtime', 0)))
                keep_path = sorted_by_res[0]['path']
                g['kept_file_path'] = keep_path
                g['needs_review'] = False
                for f in files:
                    p = f['path']
                    f['is_original'] = (p == keep_path)
                    if p in self.dup_checkbox_vars:
                        self.dup_checkbox_vars[p].set(p != keep_path)
                    else:
                        self.dup_checkbox_vars[p] = tk.BooleanVar(value=(p != keep_path))
            self.update_dup_action_label()
            self.render_dup_cards_page(reset=True)

        def auto_select_keep_shortest_path(self):
            for g in getattr(self, "dup_groups", []):
                files = g['files']
                if not files:
                    continue
                sorted_by_path = sorted(files, key=lambda x: (len(x.get('path', '')), x.get('stat_mtime', 0)))
                keep_path = sorted_by_path[0]['path']
                g['kept_file_path'] = keep_path
                g['needs_review'] = False
                for f in files:
                    p = f['path']
                    f['is_original'] = (p == keep_path)
                    if p in self.dup_checkbox_vars:
                        self.dup_checkbox_vars[p].set(p != keep_path)
                    else:
                        self.dup_checkbox_vars[p] = tk.BooleanVar(value=(p != keep_path))
            self.update_dup_action_label()
            self.render_dup_cards_page(reset=True)

        def auto_select_all_duplicates(self):
            for g in getattr(self, "dup_groups", []):
                for f in g['files']:
                    p = f['path']
                    if p in self.dup_checkbox_vars:
                        self.dup_checkbox_vars[p].set(not f.get('is_original', False))
            self.update_dup_action_label()
            self.render_dup_cards_page(reset=True)

        def clear_dup_selection(self):
            for var in self.dup_checkbox_vars.values():
                var.set(False)
            self.update_dup_action_label()
            self.render_dup_cards_page(reset=True)

        def get_selected_dup_paths(self):
            selected = []
            for path, var in list(self.dup_checkbox_vars.items()):
                try:
                    if isinstance(path, str) and var.get() and os.path.exists(fix_win_long_path(path)):
                        selected.append(path)
                except Exception:
                    pass
            return selected

        def update_dup_action_label(self):
            try:
                selected = self.get_selected_dup_paths()
                count = len(selected)
                total_bytes = 0
                for p in selected:
                    try:
                        sp = fix_win_long_path(p)
                        if os.path.exists(sp):
                            total_bytes += os.path.getsize(sp)
                    except Exception:
                        pass
                sz_str = format_bytes(total_bytes)
                if hasattr(self, "dup_action_lbl") and self.dup_action_lbl:
                    self.dup_action_lbl.configure(text=f"Selected: {count} duplicate files ({sz_str} ready for cleanup)")
            except Exception:
                pass

        def delete_selected_duplicates(self):
            selected = self.get_selected_dup_paths()
            if not selected:
                messagebox.showinfo("No Files Selected", "Please select at least one duplicate file to delete.")
                return

            use_trash = self.use_trash_backup_var.get()
            target_dir = self.dup_dir_var.get().strip()

            confirm = messagebox.askyesno("Confirm Duplicate Cleanup", f"Clean {len(selected)} selected duplicate file(s)?")
            if not confirm:
                return

            res = delete_duplicate_files(selected, use_trash_backup=use_trash, main_folder=target_dir)
            messagebox.showinfo("Cleanup Complete", f"Successfully cleaned {res['deleted']} duplicate file(s)!")
            self.run_find_duplicates()

        def move_selected_duplicates(self):
            selected = self.get_selected_dup_paths()
            if not selected:
                messagebox.showinfo("No Files Selected", "Please select at least one duplicate file to move.")
                return

            target_folder = filedialog.askdirectory(title="Select Destination Folder for Duplicates")
            if not target_folder:
                return

            res = move_duplicate_files(selected, target_folder)
            messagebox.showinfo("Move Complete", f"Successfully moved {res['moved']} duplicate file(s)!")
            self.run_find_duplicates()

        def move_all_group_files_to_folder(self):
            """Moves ALL files across ALL detected groups (both originals AND duplicates) into one folder."""
            dup_groups = getattr(self, "dup_groups", [])
            if not dup_groups:
                messagebox.showinfo("No Duplicates Loaded", "Please run '🔍 Scan Duplicates' first to detect duplicate groups.")
                return

            all_paths = []
            for g in dup_groups:
                for f in g['files']:
                    p = f['path']
                    if os.path.exists(fix_win_long_path(p)):
                        all_paths.append(p)

            if not all_paths:
                messagebox.showinfo("No Files Found", "No valid files found across duplicate groups.")
                return

            target_folder = filedialog.askdirectory(title=f"Select Single Destination Folder for ALL {len(all_paths)} Original & Duplicate Files")
            if not target_folder:
                return

            confirm = messagebox.askyesno(
                "Confirm Move All Files",
                f"Move ALL {len(all_paths)} files (both Originals AND Duplicates) into:\n\n{target_folder}?"
            )
            if not confirm:
                return

            res = move_duplicate_files(all_paths, target_folder)
            messagebox.showinfo("Move Complete", f"Successfully moved ALL {res['moved']} original & duplicate file(s) into:\n\n{target_folder}")
            self.run_find_duplicates()

        def link_selected_duplicates(self):
            selected = set(self.get_selected_dup_paths())
            if not selected:
                messagebox.showinfo("No Files Selected", "Please select duplicate files to replace with hard links.")
                return

            confirm = messagebox.askyesno("Confirm Hard Link Deduplication", f"Replace {len(selected)} duplicate file(s) with NTFS Hard Links?\n\nThis will reclaim disk space while keeping all file paths working!")
            if not confirm:
                return

            total_linked = 0
            total_errors = 0

            for g in getattr(self, "dup_groups", []):
                files = g['files']
                group_selected = [f['path'] for f in files if f['path'] in selected]
                if not group_selected:
                    continue
                
                # Original is the first non-selected file in the group
                orig_file = next((f['path'] for f in files if f['path'] not in selected), None)
                if not orig_file and files:
                    orig_file = files[0]['path']
                    group_selected = [p for p in group_selected if p != orig_file]

                if orig_file and group_selected:
                    res = replace_duplicates_with_links(group_selected, orig_file, link_type='hard')
                    total_linked += res['linked']
                    total_errors += res['errors']

            messagebox.showinfo("Hard Linking Complete", f"Successfully created {total_linked} hard link(s)!\n(Errors: {total_errors})")
            self.run_find_duplicates()

        def export_dup_report(self):
            groups = getattr(self, "dup_groups", [])
            if not groups:
                messagebox.showinfo("No Duplicate Data", "Please run a duplicate scan before exporting reports.")
                return

            save_path = filedialog.asksavefilename(
                title="Export Duplicate Analysis Audit Report",
                defaultextension=".csv",
                filetypes=[("CSV File", "*.csv"), ("JSON File", "*.json")]
            )
            if not save_path:
                return

            fmt = 'json' if save_path.lower().endswith('.json') else 'csv'
            ok = export_duplicates_report(groups, save_path, report_format=fmt)
            if ok:
                messagebox.showinfo("Export Successful", f"Duplicate audit report saved to:\n{save_path}")
            else:
                messagebox.showerror("Export Failed", "Failed to write audit report to disk.")

        def set_target_dir(self, path):
            if hasattr(self, 'dir_var'): self.dir_var.set(path)
            if hasattr(self, 'dup_dir_var'): self.dup_dir_var.set(path)
            if hasattr(self, 'ext_src_var'): self.ext_src_var.set(path)
            if hasattr(self, 'ren_dir_var'): self.ren_dir_var.set(path)
            if hasattr(self, 'cln_dir_var'): self.cln_dir_var.set(path)
            if hasattr(self, 'ins_dir_var'): self.ins_dir_var.set(path)
            self.refresh_preview()
            if getattr(self, '_tabs_loaded', {}).get('extractor'):
                self.refresh_extractor_preview()

        def browse_dest_folder(self):
            folder = filedialog.askdirectory(title="Select Custom Output Destination Directory")
            if folder:
                self.dest_dir_var.set(folder)
                self.refresh_preview()

        def apply_preset_photos(self):
            self.sort_category_var.set("📅 Date (Creation / Mod / EXIF)")
            self.date_source_var.set("exif (Camera EXIF / Fallback)")
            self.structure_var.set("YYYY/MM - Month (e.g. 2020/01 - January)")
            self.mode_segmented.set("Move")
            self.include_ext_var.set(".jpg, .jpeg, .png, .heic, .raw, .mp4, .mov")
            self.on_category_changed()
            self.refresh_preview()

        def apply_preset_downloads(self):
            self.set_target_dir(get_user_folder("Downloads"))
            self.sort_category_var.set("📁 File Category (Images, Docs...)")
            self.mode_segmented.set("Move")
            self.include_ext_var.set("")
            self.exclude_ext_var.set(".tmp, .crdownload, .part")
            self.on_category_changed()
            self.refresh_preview()

        def apply_preset_documents(self):
            self.sort_category_var.set("🏷️ Extension (PDF, PNG, DOCX...)")
            self.mode_segmented.set("Move")
            self.include_ext_var.set(".pdf, .docx, .xlsx, .pptx, .txt, .csv")
            self.on_category_changed()
            self.refresh_preview()

        def apply_preset_size(self):
            self.sort_category_var.set("⚖️ File Size (<1MB, >100MB...)")
            self.mode_segmented.set("Move")
            self.include_ext_var.set("")
            self.on_category_changed()
            self.refresh_preview()

        def toggle_theme(self):
            if self.theme_switch.get() == 1:
                ctk.set_appearance_mode("Dark")
            else:
                ctk.set_appearance_mode("Light")

        def on_category_changed(self, choice=None):
            cat = self.sort_category_var.get()
            if "Date" in cat:
                self.sub_options_lbl.grid()
                self.date_src_dropdown.grid()
                self.format_lbl.grid()
                self.struct_dropdown.grid()
            else:
                self.sub_options_lbl.grid_remove()
                self.date_src_dropdown.grid_remove()
                self.format_lbl.grid_remove()
                self.struct_dropdown.grid_remove()

            # Smart Name extra controls
            if "Smart" in cat or "Name" in cat:
                if hasattr(self, "_smart_name_extra_row") and self._smart_name_extra_row:
                    self._smart_name_extra_row.grid()
                if hasattr(self, "show_plan_btn") and self.show_plan_btn:
                    self.show_plan_btn.grid()
            else:
                if hasattr(self, "_smart_name_extra_row") and self._smart_name_extra_row:
                    self._smart_name_extra_row.grid_remove()
                if hasattr(self, "show_plan_btn") and self.show_plan_btn:
                    self.show_plan_btn.grid_remove()

        def show_smart_name_plan(self):
            target_dir = self.dir_var.get().strip()
            if not target_dir or not os.path.isdir(fix_win_long_path(target_dir)):
                messagebox.showwarning("Target Folder Required", "Please select a valid target directory to generate a pre-sorting plan.")
                return

            subdiv_val = getattr(self, "unsorted_subdivide_var", None)
            subdiv_str = "none"
            if subdiv_val:
                raw = subdiv_val.get()
                if "Type" in raw:
                    subdiv_str = "type"
                elif "Month" in raw:
                    subdiv_str = "date"

            exc_folds = self.parse_comma_list(self.exclude_folders_var.get().strip())
            exc_files = self.parse_comma_list(self.exclude_files_var.get().strip())
            route_corr = getattr(self, "route_corrupted_var", None)
            corr_val = route_corr.get() if route_corr else False

            try:
                from sorter_core import generate_smart_name_plan
                plan = generate_smart_name_plan(
                    target_dir,
                    random_folder_name="_Random",
                    unsorted_subdivide=subdiv_str,
                    recursive=self.recursive_var.get(),
                    exclude_folders=exc_folds,
                    exclude_files=exc_files,
                    route_corrupted=corr_val
                )

                # Show modal plan summary
                dlg = ctk.CTkToplevel(self)
                dlg.title("📋 Smart Name Sorting — Pre-Execution Plan")
                dlg.geometry("640x520")
                dlg.transient(self)
                dlg.grab_set()

                lbl = ctk.CTkLabel(dlg, text="📋 Pre-Execution Organization Plan", font=ctk.CTkFont(size=14, weight="bold"))
                lbl.pack(padx=16, pady=(16, 6))

                txt = ctk.CTkTextbox(dlg, font=ctk.CTkFont(family="Consolas", size=11))
                txt.pack(fill="both", expand=True, padx=16, pady=8)

                lines = []
                lines.append(f"Total Files Scanned: {plan['total_files']}")
                lines.append(f"Files to _Random: {plan['unsorted_count']}")
                if plan.get("unsorted_breakdown"):
                    for sub, cnt in plan["unsorted_breakdown"].items():
                        lines.append(f"   ↳ _Random/{sub}: {cnt} file(s)")
                lines.append(f"Proposed Word Folders: {len(plan['proposed_folders'])}")
                lines.append("=" * 55)
                lines.append("\n📁 Proposed Word Folders:")
                for pf in plan["proposed_folders"]:
                    samples = ", ".join(pf["sample_files"][:3])
                    lines.append(f"  • {pf['name']}/ ({pf['file_count']} files) -> e.g. {samples}")

                if plan.get("review_needed"):
                    lines.append("\n🚨 Files Needing Manual Review:")
                    for rn in plan["review_needed"]:
                        lines.append(f"  • {os.path.basename(rn['path'])}: {rn['reason']}")

                txt.insert("1.0", "\n".join(lines))
                txt.configure(state="disabled")

                close_btn = ctk.CTkButton(dlg, text="Close", command=dlg.destroy, width=100)
                close_btn.pack(pady=(0, 16))
            except Exception as e:
                messagebox.showerror("Plan Error", f"Failed to generate plan: {e}")

        def open_target_folder(self):
            target_dir = self.dir_var.get().strip()
            if target_dir and os.path.isdir(fix_win_long_path(target_dir)):
                if sys.platform == 'win32':
                    os.startfile(target_dir)
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', target_dir])
                else:
                    subprocess.Popen(['xdg-open', target_dir])
            else:
                messagebox.showwarning("Folder Not Found", "Please select a valid target directory first.")

        def parse_comma_list(self, raw_str):
            if not raw_str:
                return None
            return [x.strip() for x in raw_str.replace(',', ' ').split() if x.strip()]

        def refresh_preview(self):
            if getattr(self, "_suppress_preview_updates", False):
                return

            if hasattr(self, "_sorter_debounce_timer") and self._sorter_debounce_timer:
                try:
                    self.after_cancel(self._sorter_debounce_timer)
                except Exception:
                    pass

            self._sorter_debounce_timer = self.after(120, self._do_async_sorter_preview)

        def _do_async_sorter_preview(self):
            target_dir = self.dir_var.get().strip()
            if not self.selected_individual_files and not target_dir:
                return

            sort_category = self.get_sort_category_key()
            date_src_str = self.date_source_var.get().split()[0]
            raw_struct = self.structure_var.get()
            if "YYYY/MM - Month" in raw_struct:
                struct_str = "YYYY/MM - Month"
            elif "YYYY-MM" in raw_struct:
                struct_str = "YYYY-MM"
            elif "YYYY/MM/DD" in raw_struct:
                struct_str = "YYYY/MM/DD"
            else:
                struct_str = "YYYY/MM"

            recursive = self.recursive_var.get()
            isolate_dup = self.isolate_dup_var.get()
            dest_dir = self.dest_dir_var.get().strip()

            inc_exts = self.parse_comma_list(self.include_ext_var.get().strip())
            exc_exts = self.parse_comma_list(self.exclude_ext_var.get().strip())
            exc_folds = self.parse_comma_list(self.exclude_folders_var.get().strip())
            exc_files = self.parse_comma_list(self.exclude_files_var.get().strip())
            sel_files = self.selected_individual_files if self.selected_individual_files else None

            self.preview_stats_lbl.configure(text="⏳ Scanning subfolders in background...")

            def worker():
                try:
                    preview_items, cat_counts, summary = scan_directory_preview(
                        main_folder=target_dir if target_dir else None,
                        sort_category=sort_category,
                        recursive=recursive,
                        date_source=date_src_str,
                        structure_format=struct_str,
                        include_exts=inc_exts,
                        exclude_exts=exc_exts,
                        exclude_folders=exc_folds,
                        exclude_files=exc_files,
                        isolate_duplicates=isolate_dup,
                        dest_folder=dest_dir if dest_dir else None,
                        selected_files=sel_files
                    )

                    def update_ui():
                        self.preview_data = preview_items
                        self.preview_stats_lbl.configure(
                            text=f"Files: {summary['total_files']} | Total Size: {summary['total_size_str']} | Duplicates: {summary['duplicate_count']}"
                        )

                        rows = [(
                            item['filename'],
                            item['rel_src'],
                            item['rel_target'],
                            item['category'],
                            item['size_str'],
                            item.get("status_str", "Ready to Move")
                        ) for item in preview_items]

                        self.populate_tree_in_chunks(self.tree, rows, chunk_size=300)
                        self.chart_canvas.draw_chart(cat_counts)

                    self.after(0, update_ui)
                except Exception:
                    pass

            threading.Thread(target=worker, daemon=True).start()

        def clear_log(self):
            if hasattr(self, "log_textbox") and self.log_textbox:
                try:
                    self.log_textbox.delete("1.0", tk.END)
                except Exception:
                    pass

        def log(self, text, tag="info"):
            if hasattr(self, "log_textbox") and self.log_textbox:
                try:
                    tb = getattr(self.log_textbox, "_textbox", self.log_textbox)
                    tb.insert(tk.END, text + "\n", tag)
                    tb.see(tk.END)
                except Exception:
                    pass

        def update_progress(self, current, total, file_path, status_msg, status_tag):
            pct = (current / total) if total > 0 else 1.0
            if hasattr(self, "progress_bar") and self.progress_bar:
                try:
                    self.progress_bar.set(pct)
                except Exception:
                    pass
            fname = os.path.basename(file_path)
            self.status_var.set(f"Processing ({current}/{total}): {fname}")
            self.log(f"[{current}/{total}] {fname}: {status_msg}", status_tag)

        def set_ui_state(self, running):
            state = "disabled" if running else "normal"
            self.start_btn.configure(state=state)
            self.undo_btn.configure(state=state)
            self.scan_btn.configure(state=state)

        def get_sort_category_key(self):
            raw = self.sort_category_var.get()
            if "Date" in raw:
                return "date"
            elif "Category" in raw:
                return "category"
            elif "Extension" in raw:
                return "extension"
            elif "Alphabetical" in raw:
                return "alphabetical"
            elif "Smart" in raw or "Name" in raw:
                return "smart_name"
            elif "Size" in raw:
                return "size"
            return "date"

        def get_on_conflict_key(self):
            raw = self.conflict_mode_var.get()
            if "Interactive" in raw:
                return "ask"
            elif "Keep Both" in raw:
                return "number"
            elif "Replace" in raw:
                return "replace"
            return "skip"

        def on_skipped_handling_changed(self, choice=None):
            if "Custom" in self.skipped_handling_var.get():
                folder = filedialog.askdirectory(title="Select Destination Folder for Skipped Files")
                if folder:
                    self.custom_skipped_dest_var.set(folder)
                    self.skipped_handling_var.set(f"📂 Move Skipped -> {os.path.basename(folder)}")
                else:
                    self.skipped_handling_var.set("📌 Leave in Original Location (Default)")

        def prompt_interactive_conflict(self, src_path, dst_path):
            if self.remembered_conflict_choice:
                return self.remembered_conflict_choice

            event = threading.Event()
            chosen_action = ["skip"]

            def show_dialog():
                try:
                    dlg = Windows11ConflictDialog(self, src_path, dst_path, thumbnail_loader_func=self.load_file_thumbnail)
                    self.wait_window(dlg)
                    chosen_action[0] = dlg.result_action
                    if dlg.apply_all:
                        self.remembered_conflict_choice = dlg.result_action
                except Exception:
                    chosen_action[0] = "skip"
                finally:
                    event.set()

            self.after(0, show_dialog)
            event.wait()
            return chosen_action[0]

        def start_sorting(self):
            target_dir = self.dir_var.get().strip()
            if not self.selected_individual_files and (not target_dir or not os.path.isdir(fix_win_long_path(target_dir))):
                messagebox.showwarning("Missing Target", "Please select a valid target directory or pick specific files.")
                return

            dest_dir = self.dest_dir_var.get().strip()
            if dest_dir and not os.path.exists(fix_win_long_path(dest_dir)):
                os.makedirs(fix_win_long_path(dest_dir), exist_ok=True)

            sort_category = self.get_sort_category_key()
            on_conflict_mode = self.get_on_conflict_key()
            date_src_str = self.date_source_var.get().split()[0]

            raw_struct = self.structure_var.get()
            if "YYYY/MM - Month" in raw_struct:
                struct_str = "YYYY/MM - Month"
            elif "YYYY-MM" in raw_struct:
                struct_str = "YYYY-MM"
            elif "YYYY/MM/DD" in raw_struct:
                struct_str = "YYYY/MM/DD"
            else:
                struct_str = "YYYY/MM"

            mode = "move" if "Move" in self.mode_segmented.get() else "copy"
            recursive = self.recursive_var.get()
            dry_run = self.dry_run_var.get()
            clean_empty = self.clean_empty_var.get()
            isolate_dup = self.isolate_dup_var.get()
            enable_zip = self.enable_zip_backup_var.get()

            inc_exts = self.parse_comma_list(self.include_ext_var.get().strip())
            exc_exts = self.parse_comma_list(self.exclude_ext_var.get().strip())
            exc_folds = self.parse_comma_list(self.exclude_folders_var.get().strip())
            exc_files = self.parse_comma_list(self.exclude_files_var.get().strip())

            raw_skip = self.skipped_handling_var.get()
            if "Move Skipped" in raw_skip:
                skip_mode = "move"
                skip_dest = self.custom_skipped_dest_var.get().strip() if self.custom_skipped_dest_var.get().strip() else None
            else:
                skip_mode = "stay"
                skip_dest = None

            self.remembered_conflict_choice = None

            self.clear_log()
            self.log("==========================================", "header")
            self.log("      STARTING FILE ORGANIZATION RUN", "header")
            self.log("==========================================", "header")

            self.set_ui_state(True)
            self.progress_bar.set(0)

            def run_thread():
                try:
                    stats, manifest = organize_directory(
                        main_folder=target_dir if target_dir else None,
                        sort_category=sort_category,
                        recursive=recursive,
                        date_source=date_src_str,
                        structure_format=struct_str,
                        include_exts=inc_exts,
                        exclude_exts=exc_exts,
                        exclude_folders=exc_folds,
                        exclude_files=exc_files,
                        mode=mode,
                        dry_run=dry_run,
                        clean_empty=clean_empty,
                        isolate_duplicates=isolate_dup,
                        dest_folder=dest_dir if dest_dir else None,
                        enable_zip_backup=enable_zip,
                        on_conflict=on_conflict_mode,
                        conflict_resolver_callback=self.prompt_interactive_conflict,
                        progress_callback=lambda c, t, fp, st, tag: self.after(0, self.update_progress, c, t, fp, st, tag),
                        selected_files=self.selected_individual_files if self.selected_individual_files else None,
                        skipped_handling=skip_mode,
                        skipped_dest_folder=skip_dest
                    )

                    def finished():
                        self.log("\n==========================================", "header")
                        self.log("           ORGANIZATION SUMMARY", "header")
                        self.log("==========================================", "header")
                        self.log(f"Total Files Analyzed:  {stats['total']}", "info")
                        self.log(f"Successfully Handled: {stats['processed']}", "success")
                        self.log(f"Skipped (In place):   {stats['skipped']}", "skipped")
                        if stats.get("moved_skipped_files", 0) > 0:
                            self.log(f"Moved Skipped Files:  {stats['moved_skipped_files']}", "info")
                        self.log(f"Errors Encountered:   {stats['errors']}", "error" if stats['errors'] > 0 else "info")

                        self.status_var.set("Organization complete!")
                        self.set_ui_state(False)
                        self.refresh_preview()
                        messagebox.showinfo("Operation Complete", f"Processed: {stats['processed']}\nSkipped: {stats['skipped']}\nErrors: {stats['errors']}")

                    self.after(0, finished)

                except Exception as e:
                    def on_error(err_msg):
                        self.log(f"\nORGANIZATION ERROR: {err_msg}", "error")
                        self.status_var.set("Error during organization.")
                        self.set_ui_state(False)
                        messagebox.showerror("Organization Error", str(e))

                    self.after(0, on_error, str(e))

            threading.Thread(target=run_thread, daemon=True).start()

        def open_system_vault_restore_manager(self):
            target_dir = self.dir_var.get().strip() or self.ext_src_var.get().strip()
            manifests = list_manifest_files(target_dir if target_dir and os.path.isdir(fix_win_long_path(target_dir)) else None)

            win = ctk.CTkToplevel(self)
            win.title("🛡️ Protected System AppData Vault & Restore Manager")
            win.geometry("780x520")
            win.transient(self)
            win.attributes("-topmost", True)
            win.grab_set()
            win.after(100, lambda: (win.lift(), win.focus_force()))

            hdr_f = ctk.CTkFrame(win, fg_color="transparent")
            hdr_f.pack(fill="x", padx=15, pady=(15, 5))

            ctk.CTkLabel(hdr_f, text="🛡️ Protected System AppData Vault (%LOCALAPPDATA%)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#0288d1").pack(anchor="w")
            ctk.CTkLabel(hdr_f, text="Backups stored here are isolated from user target folders and CANNOT be accidentally deleted!", font=ctk.CTkFont(size=11), text_color="gray70").pack(anchor="w")

            btn_open_vault = ctk.CTkButton(
                hdr_f,
                text="📂 Open Protected Vault Directory ↗",
                command=self.open_backup_vault_explorer,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=("gray75", "gray30"),
                text_color=("gray10", "gray90"),
                height=28
            )
            btn_open_vault.pack(anchor="e", pady=(5, 0))

            cards_scroll = ctk.CTkScrollableFrame(win, corner_radius=10)
            cards_scroll.pack(fill="both", expand=True, padx=15, pady=10)

            if not manifests:
                ctk.CTkLabel(cards_scroll, text="No historical restore manifests found in System Vault.", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray50").pack(pady=40)
                return

            for m in manifests:
                card = ctk.CTkFrame(cards_scroll, corner_radius=10, fg_color=("gray90", "gray20"))
                card.pack(fill="x", pady=6, padx=5)

                ts_raw = m.get("timestamp", "")
                try:
                    dt_obj = datetime.strptime(ts_raw, "%Y%m%d_%H%M%S")
                    day_names = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
                    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
                    weekday = day_names[dt_obj.weekday()]
                    month   = month_names[dt_obj.month - 1]
                    human_date = f"{weekday}, {month} {dt_obj.day}, {dt_obj.year}"
                    h = dt_obj.hour
                    ampm = "AM" if h < 12 else "PM"
                    h12 = h % 12 or 12
                    human_time = f"{h12:02d}:{dt_obj.minute:02d}:{dt_obj.second:02d} {ampm}"
                except Exception:
                    human_date = ts_raw
                    human_time = ""

                hdr_row = ctk.CTkFrame(card, fg_color="transparent")
                hdr_row.pack(fill="x", padx=10, pady=(8, 2))
                hdr_row.grid_columnconfigure(0, weight=1)

                ctk.CTkLabel(
                    hdr_row,
                    text=f"📅  Backup Run — {human_date}",
                    font=ctk.CTkFont(size=12, weight="bold")
                ).grid(row=0, column=0, sticky="w")

                ctk.CTkLabel(
                    hdr_row,
                    text=f"⏰ {human_time}",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=("#0288d1", "#64b5f6")
                ).grid(row=0, column=1, sticky="e")

                ops_count = m.get("count", 0)
                details_parts = [f"🔢  {ops_count} file operations recorded"]
                if m.get("main_folder"):
                    details_parts.append(f"📁  Target: {m['main_folder']}")
                details_parts.append(f"🗂️  Manifest: {m['filename']}")

                ctk.CTkLabel(
                    card,
                    text="\n".join(details_parts),
                    font=ctk.CTkFont(size=10),
                    text_color=("gray40", "gray65"),
                    justify="left"
                ).pack(anchor="w", padx=12, pady=(0, 6))

                ctk.CTkFrame(card, height=1, fg_color=("gray80", "gray35")).pack(fill="x", padx=10, pady=(0, 6))

                btn_box = ctk.CTkFrame(card, fg_color="transparent")
                btn_box.pack(anchor="e", padx=10, pady=(0, 8))

                ctk.CTkButton(
                    btn_box,
                    text="🗑️ Remove Entry",
                    command=lambda path=m['path']: (
                        os.remove(path) if os.path.exists(path) else None,
                        win.destroy(),
                        self.open_restore_manager()
                    ),
                    font=ctk.CTkFont(size=10),
                    fg_color=("gray70", "gray30"),
                    text_color=("gray10", "gray90"),
                    hover_color="#c62828",
                    height=26,
                    width=110
                ).pack(side="left", padx=(0, 8))

                ctk.CTkButton(
                    btn_box,
                    text="🛡️ Restore All Files (1-Click)",
                    command=lambda path=m['path'], w=win: self.execute_manifest_restore(path, w),
                    font=ctk.CTkFont(size=11, weight="bold"),
                    fg_color="#c62828",
                    hover_color="#d32f2f",
                    height=30
                ).pack(side="right")

        def execute_manifest_restore(self, manifest_path, parent_win):
            parent_win.destroy()
            self.clear_log()
            self.log("==========================================", "header")
            self.log("    SYSTEM VAULT 1-CLICK FILE RESTORE", "header")
            self.log("==========================================", "header")

            self.set_ui_state(True)
            self.progress_bar.set(0)

            def run_undo():
                try:
                    stats = undo_manifest(
                        manifest_path,
                        progress_callback=lambda c, t, fp, st, tag: self.after(0, self.update_progress, c, t, fp, st, tag)
                    )

                    def undo_finished():
                        self.log("\n==========================================", "header")
                        self.log("              RESTORE SUMMARY", "header")
                        self.log("==========================================", "header")
                        self.log(f"Total Files Restored: {stats['undone']}", "success")
                        self.log(f"Errors Encountered:   {stats['errors']}", "error" if stats['errors'] > 0 else "info")

                        self.status_var.set("System Vault restore completed!")
                        self.set_ui_state(False)
                        self.refresh_preview()
                        self.refresh_extractor_preview()
                        messagebox.showinfo("Restore Complete", f"Successfully restored {stats['undone']} files back to their original locations!")

                    self.after(0, undo_finished)
                except Exception as e:
                    def on_undo_error(err_msg):
                        self.log(f"\nRESTORE ERROR: {err_msg}", "error")
                        self.status_var.set("Error during restore.")
                        self.set_ui_state(False)
                        messagebox.showerror("Restore Error", str(e))

                    self.after(0, on_undo_error, str(e))

            threading.Thread(target=run_undo, daemon=True).start()

        # CLEANER HELPERS
        def run_cleaner_scan(self):
            folder = self.cln_dir_var.get().strip()
            if not folder or not os.path.isdir(fix_win_long_path(folder)):
                messagebox.showwarning("Missing Directory", "Please select a valid directory.")
                return

            exc_folds = self.parse_comma_list(self.exclude_folders_var.get().strip())
            exc_files = self.parse_comma_list(self.exclude_files_var.get().strip())
            exc_exts = self.parse_comma_list(self.exclude_ext_var.get().strip())

            self.status_var.set("⏳ Scanning directory for junk and large files in background...")

            def worker():
                res = scan_junk_and_large_files(folder, exclude_folders=exc_folds, exclude_files=exc_files, exclude_exts=exc_exts)

                def update_ui():
                    junk_rows = [(j['filename'], j['rel_path'], j['reason'], j['size_str'], j['mtime_str']) for j in res['junk_files']]
                    large_rows = [(l['filename'], l['rel_path'], l['category'], l['size_str'], l['mtime_str']) for l in res['large_files']]

                    self.populate_tree_in_chunks(self.junk_tree, junk_rows, chunk_size=300)
                    self.populate_tree_in_chunks(self.large_tree, large_rows, chunk_size=300)
                    self.run_empty_folder_scan()
                    messagebox.showinfo("Scan Complete", f"Found {len(res['junk_files'])} junk file(s) ({res['total_junk_size_str']}), {len(res['large_files'])} large file(s), and scanned empty subfolders!")

                self.after(0, update_ui)

            threading.Thread(target=worker, daemon=True).start()

        def clean_selected_junk(self):
            selected = self.junk_tree.selection()
            if not selected:
                messagebox.showinfo("No Selection", "Please select junk files in the table to clean.")
                return

            file_paths = []
            for item in selected:
                vals = self.junk_tree.item(item, "values")
                fp = os.path.join(self.cln_dir_var.get().strip(), vals[1])
                file_paths.append(fp)

            res = delete_duplicate_files(file_paths, use_trash_backup=True)
            messagebox.showinfo("Junk Cleaned", f"Successfully moved {res['deleted']} junk file(s) to Protected System Vault Trash!")
            self.run_cleaner_scan()

        def _on_junk_select(self, event=None):
            sel = self.junk_tree.selection()
            total = len(self.junk_tree.get_children())
            total_bytes = 0
            for item in sel:
                vals = self.junk_tree.item(item, "values")
                fp = os.path.join(self.cln_dir_var.get().strip(), vals[1])
                try:
                    total_bytes += os.path.getsize(fix_win_long_path(fp))
                except Exception:
                    pass
            self.junk_sel_lbl.configure(
                text=f"Selected: {len(sel)} of {total} files ({format_bytes(total_bytes)})"
            )

        def _on_large_select(self, event=None):
            sel = self.large_tree.selection()
            total = len(self.large_tree.get_children())
            total_bytes = 0
            for item in sel:
                vals = self.large_tree.item(item, "values")
                fp = os.path.join(self.cln_dir_var.get().strip(), vals[1])
                try:
                    total_bytes += os.path.getsize(fix_win_long_path(fp))
                except Exception:
                    pass
            self.large_sel_lbl.configure(
                text=f"Selected: {len(sel)} of {total} files ({format_bytes(total_bytes)})"
            )

        def run_empty_folder_scan(self):
            folder = self.cln_dir_var.get().strip()
            if not folder or not os.path.isdir(fix_win_long_path(folder)):
                messagebox.showwarning("Missing Directory", "Please select a valid directory first.")
                return

            exc_folds = self.parse_comma_list(self.exclude_folders_var.get().strip())
            rm_os = self.empty_remove_os_junk_var.get()
            self.empty_sel_lbl.configure(text="Scanning empty subfolders...")

            def worker():
                empty_list = scan_empty_dirs_preview(
                    folder,
                    remove_os_junk=rm_os,
                    exclude_folders=exc_folds
                )

                def update_ui():
                    rows = [(
                        item["folder_name"],
                        item["rel_path"],
                        item["reason"],
                        item["path"]
                    ) for item in empty_list]

                    self.populate_tree_in_chunks(self.empty_tree, rows, chunk_size=300)
                    self.empty_sel_lbl.configure(text=f"Detected: {len(empty_list)} empty folder(s)")
                    self.status_var.set(f"Detected {len(empty_list)} empty folder(s) in '{os.path.basename(folder)}'.")

                self.after(0, update_ui)

            threading.Thread(target=worker, daemon=True).start()

        def _on_empty_select(self, event=None):
            sel_count = len(self.empty_tree.selection())
            total_count = len(self.empty_tree.get_children())
            self.empty_sel_lbl.configure(text=f"Selected: {sel_count} of {total_count} empty folder(s)")

        def empty_select_all(self):
            self.empty_tree.selection_set(self.empty_tree.get_children())
            self._on_empty_select()

        def empty_select_none(self):
            self.empty_tree.selection_remove(self.empty_tree.get_children())
            self._on_empty_select()

        def empty_select_invert(self):
            all_items = set(self.empty_tree.get_children())
            selected = set(self.empty_tree.selection())
            new_sel = list(all_items - selected)
            self.empty_tree.selection_set(new_sel)
            self._on_empty_select()

        def delete_selected_empty_folders(self):
            sel_items = self.empty_tree.selection()
            if not sel_items:
                messagebox.showwarning("No Folders Selected", "Please select one or more empty folders from the list to delete.")
                return

            paths_to_delete = [self.empty_tree.item(item)["values"][3] for item in sel_items]
            if not messagebox.askyesno("Confirm Empty Folder Deletion", f"Are you sure you want to delete {len(paths_to_delete)} selected empty folder(s)?"):
                return

            exc_folds = self.parse_comma_list(self.exclude_folders_var.get().strip())
            res = delete_empty_folder_batch(paths_to_delete, remove_os_junk=self.empty_remove_os_junk_var.get(), exclude_folders=exc_folds)
            messagebox.showinfo("Empty Folders Deleted", f"Successfully deleted {res['deleted']} empty folder(s)!\nErrors: {res['errors']}")
            self.run_empty_folder_scan()

        def delete_all_empty_folders(self):
            folder = self.cln_dir_var.get().strip().strip('\'"')
            if not folder or not os.path.isdir(fix_win_long_path(folder)):
                messagebox.showwarning("Missing Directory", "Please select a valid directory first.")
                return

            exc_folds = self.parse_comma_list(self.exclude_folders_var.get().strip())
            if not messagebox.askyesno("Confirm Delete ALL Empty Folders", f"Are you sure you want to clean ALL empty subfolders in:\n{folder}?"):
                return

            cleaned = clean_empty_dirs(folder, remove_os_junk=self.empty_remove_os_junk_var.get(), exclude_folders=exc_folds)
            messagebox.showinfo("Cleanup Complete", f"Successfully cleaned {cleaned} empty folder(s)!")
            self.run_empty_folder_scan()

        def junk_select_all(self):
            self.junk_tree.selection_set(self.junk_tree.get_children())
            self._on_junk_select()

        def junk_select_none(self):
            self.junk_tree.selection_remove(self.junk_tree.get_children())
            self._on_junk_select()

        def junk_select_invert(self):
            all_items = set(self.junk_tree.get_children())
            selected = set(self.junk_tree.selection())
            new_sel = list(all_items - selected)
            self.junk_tree.selection_set(new_sel)
            self._on_junk_select()

        def junk_select_by_reason(self, reason_keyword):
            matching = []
            for item in self.junk_tree.get_children():
                vals = self.junk_tree.item(item, "values")
                reason = vals[2] if len(vals) > 2 else ""
                if reason_keyword.lower() in reason.lower():
                    matching.append(item)
            self.junk_tree.selection_set(matching)
            self._on_junk_select()

        def large_select_all(self):
            self.large_tree.selection_set(self.large_tree.get_children())
            self._on_large_select()

        def large_select_none(self):
            self.large_tree.selection_remove(self.large_tree.get_children())
            self._on_large_select()

        def large_select_invert(self):
            all_items = set(self.large_tree.get_children())
            selected = set(self.large_tree.selection())
            new_sel = list(all_items - selected)
            self.large_tree.selection_set(new_sel)
            self._on_large_select()

        def large_select_by_category(self, cat_keyword):
            matching = []
            for item in self.large_tree.get_children():
                vals = self.large_tree.item(item, "values")
                cat = vals[2] if len(vals) > 2 else ""
                if cat_keyword.lower() in cat.lower():
                    matching.append(item)
            self.large_tree.selection_set(matching)
            self._on_large_select()

        def large_select_above_size(self, min_bytes):
            folder = self.cln_dir_var.get().strip()
            matching = []
            for item in self.large_tree.get_children():
                vals = self.large_tree.item(item, "values")
                rel_path = vals[1] if len(vals) > 1 else ""
                fp = os.path.join(folder, rel_path)
                try:
                    if os.path.getsize(fix_win_long_path(fp)) >= min_bytes:
                        matching.append(item)
                except Exception:
                    pass
            self.large_tree.selection_set(matching)
            self._on_large_select()

        def _sort_tree(self, tree, col):
            data = [(tree.set(item, col), item) for item in tree.get_children("")]
            try:
                data.sort(key=lambda x: float(x[0].replace(",", "").split()[0]) if x[0].replace(",", "").split()[0].replace(".", "").isdigit() else x[0].lower())
            except Exception:
                data.sort(key=lambda x: x[0].lower())
            for idx, (val, item) in enumerate(data):
                tree.move(item, "", idx)

        def move_selected_large_files(self):
            selected = self.large_tree.selection()
            if not selected:
                messagebox.showinfo("No Selection", "Please select large files to move.")
                return
            dest = filedialog.askdirectory(title="Select Destination Folder for Large Files")
            if not dest:
                return
            folder = self.cln_dir_var.get().strip()
            moved = 0
            errors = 0
            for item in selected:
                vals = self.large_tree.item(item, "values")
                src = os.path.join(folder, vals[1])
                dst = os.path.join(dest, os.path.basename(src))
                try:
                    import shutil
                    shutil.move(fix_win_long_path(src), fix_win_long_path(dst))
                    moved += 1
                except Exception:
                    errors += 1
            messagebox.showinfo("Move Complete", f"Moved {moved} large file(s) to '{dest}'.\nErrors: {errors}")
            self.run_cleaner_scan()

        def open_selected_junk_location(self):
            tree = self.junk_tree if self.junk_tree.selection() else self.large_tree
            selected = tree.selection()
            if not selected:
                messagebox.showinfo("No Selection", "Please select a file first.")
                return
            vals = tree.item(selected[0], "values")
            folder = self.cln_dir_var.get().strip()
            fp = os.path.join(folder, vals[1])
            if os.path.exists(fix_win_long_path(fp)):
                if sys.platform == "win32":
                    subprocess.Popen(["explorer", "/select,", os.path.normpath(fp)])
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", "-R", fp])
                else:
                    subprocess.Popen(["xdg-open", os.path.dirname(fp)])
            else:
                messagebox.showwarning("Not Found", f"File not found:\n{fp}")

        def run_insights_analysis(self):
            folder = self.ins_dir_var.get().strip()
            if not folder or not os.path.isdir(fix_win_long_path(folder)):
                messagebox.showwarning("Missing Directory", "Please select a valid directory.")
                return

            for w in self.insights_dashboard.winfo_children():
                w.destroy()

            exc_folds = self.parse_comma_list(self.exclude_folders_var.get().strip())
            exc_files = self.parse_comma_list(self.exclude_files_var.get().strip())
            exc_exts = self.parse_comma_list(self.exclude_ext_var.get().strip())
            data = analyze_storage_insights(folder, exclude_folders=exc_folds, exclude_files=exc_files, exclude_exts=exc_exts)

            row_sum = ctk.CTkFrame(self.insights_dashboard, fg_color="transparent")
            row_sum.pack(fill="x", pady=(0, 12))
            row_sum.grid_columnconfigure(0, weight=1)
            row_sum.grid_columnconfigure(1, weight=1)
            row_sum.grid_columnconfigure(2, weight=1)

            c1 = ctk.CTkFrame(row_sum, corner_radius=10, fg_color=("gray90", "gray20"))
            c1.grid(row=0, column=0, sticky="ew", padx=4)
            ctk.CTkLabel(c1, text="Total Files", font=ctk.CTkFont(size=10), text_color="gray60").pack(pady=(6, 0))
            ctk.CTkLabel(c1, text=f"📄 {data['total_files']}", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 6))

            c2 = ctk.CTkFrame(row_sum, corner_radius=10, fg_color=("gray90", "gray20"))
            c2.grid(row=0, column=1, sticky="ew", padx=4)
            ctk.CTkLabel(c2, text="Total Disk Size", font=ctk.CTkFont(size=10), text_color="gray60").pack(pady=(6, 0))
            ctk.CTkLabel(c2, text=f"⚖️ {data['total_size_str']}", font=ctk.CTkFont(size=16, weight="bold"), text_color="#0288d1").pack(pady=(0, 6))

            c3 = ctk.CTkFrame(row_sum, corner_radius=10, fg_color=("gray90", "gray20"))
            c3.grid(row=0, column=2, sticky="ew", padx=4)
            old_str = data['oldest_file']['date_str'] if data['oldest_file'] else 'N/A'
            new_str = data['newest_file']['date_str'] if data['newest_file'] else 'N/A'
            ctk.CTkLabel(c3, text="Timeline Span", font=ctk.CTkFont(size=10), text_color="gray60").pack(pady=(6, 0))
            ctk.CTkLabel(c3, text=f"📅 {old_str} to {new_str}", font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(0, 6))

            ctk.CTkLabel(self.insights_dashboard, text="Category Space Breakdown:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 6))

            cat_frame = ctk.CTkFrame(self.insights_dashboard, fg_color="transparent")
            cat_frame.pack(fill="x", pady=(0, 12))
            cat_frame.grid_columnconfigure(1, weight=1)

            r = 0
            for cat, cdata in data['categories'].items():
                if cdata['count'] > 0:
                    ctk.CTkLabel(cat_frame, text=f"{cat}:", font=ctk.CTkFont(size=11, weight="bold"), width=120, anchor="w").grid(row=r, column=0, sticky="w", pady=2)
                    pb = ctk.CTkProgressBar(cat_frame, height=12)
                    pb.set(cdata['percentage'] / 100.0)
                    pb.grid(row=r, column=1, sticky="ew", padx=8, pady=2)
                    ctk.CTkLabel(cat_frame, text=f"{cdata['size_str']} ({cdata['percentage']}%) — {cdata['count']} files", font=ctk.CTkFont(size=10), text_color="gray60").grid(row=r, column=2, sticky="e", pady=2)
                    r += 1

        def start_watcher_service(self):
            folder = self.wtc_dir_var.get().strip()
            if not folder or not os.path.isdir(fix_win_long_path(folder)):
                messagebox.showwarning("Missing Directory", "Please select a valid directory to watch.")
                return

            self.watcher_service = FolderWatcherService(
                target_folder=folder,
                on_organized_callback=lambda stats: self.after(0, self.status_var.set, f"Auto-Organized new file in {folder}!")
            )
            self.watcher_service.start()

            self.wtc_status_lbl.configure(text=f"Status: 🟢 Watching '{folder}' for new downloads...", text_color="#81c784")
            self.wtc_start_btn.configure(state="disabled")
            self.wtc_stop_btn.configure(state="normal")
            messagebox.showinfo("Watcher Started", f"Background watcher service activated!\n\nAny new file downloaded into '{folder}' will be automatically organized into subfolders.")

        def stop_watcher_service(self):
            if self.watcher_service:
                self.watcher_service.stop()
                self.watcher_service = None

            self.wtc_status_lbl.configure(text="Status: 🔴 Service Stopped", text_color="#e57373")
            self.wtc_start_btn.configure(state="normal")
            self.wtc_stop_btn.configure(state="disabled")

        def browse_multiple_folders(self, target_var=None, on_update_callback=None):
            selected = []
            if target_var and target_var.get().strip():
                existing = [p.strip() for p in target_var.get().replace(",", ";").split(";") if p.strip()]
                selected.extend(existing)

            while True:
                folder = filedialog.askdirectory(title="Select a Folder to Include (Click Cancel when finished)")
                if not folder:
                    break
                if folder not in selected:
                    selected.append(folder)
                ans = messagebox.askyesno(
                    "Folder Added",
                    f"Added:\n{folder}\n\nTotal Folders Selected: {len(selected)}\n\nDo you want to pick another folder?"
                )
                if not ans:
                    break

            if selected:
                combined_str = "; ".join(selected)
                if target_var:
                    target_var.set(combined_str)
                else:
                    self.dir_var.set(combined_str)
                if on_update_callback:
                    on_update_callback()

        def browse_ren_individual_files(self):
            files = filedialog.askopenfilenames(title="Select Specific Files to Rename")
            if files:
                self.rename_preview_files = list(files)
                dir_name = os.path.dirname(files[0])
                self.ren_dir_var.set(f"[Custom Selection] {len(files)} file(s) selected from {dir_name}")
                self.refresh_renamer_preview()

        def browse_ren_dir(self):
            folder = filedialog.askdirectory(title="Select Directory to Batch Rename Files")
            if folder:
                self.ren_dir_var.set(folder)
                self.rename_preview_files = []
                self.refresh_renamer_preview()

        def refresh_renamer_preview(self):
            folder = self.ren_dir_var.get().strip()
            if self.rename_preview_files:
                files = self.rename_preview_files
            elif folder and os.path.isdir(fix_win_long_path(folder)):
                files = gather_files(
                    folder,
                    recursive=False,
                    exclude_exts=self.parse_comma_list(self.exclude_ext_var.get().strip()),
                    exclude_folders=self.parse_comma_list(self.exclude_folders_var.get().strip()),
                    exclude_files=self.parse_comma_list(self.exclude_files_var.get().strip())
                )
            else:
                return

            for item in self.ren_tree.get_children():
                self.ren_tree.delete(item)

            self.ren_stats_lbl.configure(text=f"Files to Rename: {len(files)}")

            pattern = self.ren_pattern_var.get().strip() or "{OriginalName}"
            case_raw = self.ren_case_var.get()
            case_key = "lower" if "lowercase" in case_raw else ("upper" if "UPPERCASE" in case_raw else ("title" if "Title" in case_raw else ("camel" if "camel" in case_raw else "none")))

            search_t = self.ren_find_var.get()
            replace_t = self.ren_replace_var.get()
            prefix_t = self.ren_prefix_var.get()
            suffix_t = self.ren_suffix_var.get()

            for idx, fp in enumerate(files[:300], 1):
                fn = os.path.basename(fp)
                base, ext = os.path.splitext(fn)

                new_base = base
                if search_t:
                    new_base = new_base.replace(search_t, replace_t)

                if case_key == "upper":
                    new_base = new_base.upper()
                elif case_key == "lower":
                    new_base = new_base.lower()
                elif case_key == "title":
                    new_base = new_base.title()

                dt = get_file_date(fp)
                cat = get_file_category(fn)

                new_fn = pattern.replace("{OriginalName}", new_base)
                new_fn = new_fn.replace("{YYYY}", f"{dt.year:04d}")
                new_fn = new_fn.replace("{MM}", f"{dt.month:02d}")
                new_fn = new_fn.replace("{DD}", f"{dt.day:02d}")
                new_fn = new_fn.replace("{Category}", cat)
                new_fn = new_fn.replace("{001}", f"{idx:03d}")

                final_fn = f"{prefix_t}{new_fn}{suffix_t}{ext}"

                try:
                    sz_str = format_bytes(os.path.getsize(fix_win_long_path(fp)))
                except Exception:
                    sz_str = "0 B"

                self.ren_tree.insert("", "end", values=(fn, final_fn, cat, sz_str))

        def start_batch_rename(self):
            exc_folds = self.parse_comma_list(self.exclude_folders_var.get().strip())
            exc_files = self.parse_comma_list(self.exclude_files_var.get().strip())
            exc_exts = self.parse_comma_list(self.exclude_ext_var.get().strip())
            ren_dir = self.ren_dir_var.get().strip()
            files = self.rename_preview_files if self.rename_preview_files else (gather_files(ren_dir, recursive=False, exclude_exts=exc_exts, exclude_folders=exc_folds, exclude_files=exc_files) if os.path.isdir(fix_win_long_path(ren_dir)) else [])
            if not files:
                messagebox.showwarning("No Files", "Please select a valid directory or pick files to rename.")
                return

            pattern = self.ren_pattern_var.get().strip() or "{OriginalName}"
            case_raw = self.ren_case_var.get()
            case_key = "lower" if "lowercase" in case_raw else ("upper" if "UPPERCASE" in case_raw else ("title" if "Title" in case_raw else ("camel" if "camel" in case_raw else "none")))

            res = batch_rename_files(
                files,
                naming_pattern=pattern,
                case_transform=case_key,
                search_text=self.ren_find_var.get(),
                replace_text=self.ren_replace_var.get(),
                prefix=self.ren_prefix_var.get(),
                suffix=self.ren_suffix_var.get()
            )

            messagebox.showinfo("Batch Rename Finished", f"Successfully renamed {res['renamed']} file(s)!\n\nManifest saved to Protected System Vault for 1-Click Restore.")
            self.refresh_renamer_preview()

        def browse_dup_files(self):
            files = filedialog.askopenfilenames(title="Select Specific Files to Check for Duplicates")
            if files:
                dir_name = os.path.dirname(files[0])
                self.dup_selected_individual_files = list(files)
                self.dup_dir_var.set(f"[Custom Selection] {len(files)} file(s) from {dir_name}")
                self.run_find_duplicates()

    SmartFileOrganizerGUI = ModernFileDateSorterGUI

else:
    class ModernFileDateSorterGUI:
        def __init__(self):
            print("CustomTkinter required.")
    SmartFileOrganizerGUI = ModernFileDateSorterGUI


def main():
    if HAS_CUSTOMTKINTER:
        app = ModernFileDateSorterGUI()
        app.mainloop()
    else:
        root = tk.Tk()
        root.title("Smart File Organizer Suite Pro")
        label = tk.Label(root, text="Please install customtkinter: pip install customtkinter")
        label.pack(padx=20, pady=20)
        root.mainloop()


if __name__ == '__main__':
    main()
