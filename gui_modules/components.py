import os
import sys
import tkinter as tk
from datetime import datetime
from tkinter import ttk

from sorter_core import format_bytes, fix_win_long_path

# Granular common file types for multi-tick extraction selector
GRANULAR_FILE_TYPES = {
    "📄 PDF Files (.pdf)": [".pdf"],
    "📝 Word Documents (.docx, .doc, .odt)": [".docx", ".doc", ".odt"],
    "📊 Excel & Data (.xlsx, .xls, .csv, .cvv, .tsv)": [".xlsx", ".xls", ".csv", ".cvv", ".tsv", ".ods"],
    "🖥️ PowerPoint (.pptx, .ppt)": [".pptx", ".ppt"],
    "📝 Text & Notes (.txt, .md, .rtf)": [".txt", ".md", ".rtf"],
    "📦 Archives (.zip, .rar, .7z, .iso)": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".iso", ".img", ".vmdk"],
    "🖼️ Photos & Images (.jpg, .png, .gif, .webp, .raw)": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".heic", ".raw", ".tiff", ".ico", ".cr2", ".nef", ".dng"],
    "🎨 Design & Photoshop (.psd, .ai, .eps, .sketch, .fig)": [".psd", ".ai", ".eps", ".sketch", ".fig", ".xd", ".xcf", ".indd"],
    "🧊 3D Models & CAD (.stl, .obj, .fbx, .blend, .dwg)": [".stl", ".obj", ".fbx", ".blend", ".dwg", ".dxf", ".step", ".3ds", ".gcode", ".dae"],
    "📚 E-Books & Comics (.epub, .mobi, .azw3, .cbz)": [".epub", ".mobi", ".azw3", ".cbz", ".cbr"],
    "🎬 Videos (.mp4, .mkv, .mov, .avi, .vob, .3gp...)": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".3gp", ".ts", ".m2ts", ".vob", ".mpg", ".mpeg", ".m2v", ".divx", ".ogv"],
    "🎵 Audio (.mp3, .wav, .flac, .m4a, .3ga, .opus...)": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".mid", ".midi", ".3ga", ".amr", ".opus", ".ape", ".wv", ".mka", ".ra"],
    "💻 Code & Data (.py, .js, .html, .json, .sql...)": [".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".json", ".java", ".cpp", ".c", ".h", ".sql", ".xml", ".sh", ".bat", ".ps1", ".php", ".rb", ".go", ".rs"],
    "🔤 Fonts (.ttf, .otf, .woff)": [".ttf", ".otf", ".woff", ".woff2", ".eot"],
    "⚙️ System, Config & Logs (.ini, .cfg, .log, .bak)": [".ini", ".cfg", ".env", ".yaml", ".yml", ".log", ".bak", ".dat", ".bin"],
    "⚙️ Executables & Installers (.exe, .msi, .apk)": [".exe", ".msi", ".apk", ".dmg", ".deb"]
}

try:
    import customtkinter as ctk
    HAS_CUSTOMTKINTER = True
    _BaseToplevel = ctk.CTkToplevel
except ImportError:
    ctk = None
    HAS_CUSTOMTKINTER = False
    _BaseToplevel = tk.Toplevel

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


def get_user_folder(name):
    home = os.path.expanduser("~")
    path = os.path.join(home, name)
    return path if os.path.exists(path) else home


class CTkToolTip:
    def __init__(self, widget, text, delay=250):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window = None
        self.timer_id = None
        self._safe_bind(self.widget)

    def _safe_bind(self, target_widget):
        try:
            target_widget.bind("<Enter>", self.on_enter)
            target_widget.bind("<Leave>", self.on_leave)
        except (NotImplementedError, AttributeError):
            if hasattr(target_widget, "_canvas"):
                try:
                    target_widget._canvas.bind("<Enter>", self.on_enter)
                    target_widget._canvas.bind("<Leave>", self.on_leave)
                except Exception:
                    pass
            elif hasattr(target_widget, "_buttons_dict"):
                try:
                    for btn in target_widget._buttons_dict.values():
                        btn.bind("<Enter>", self.on_enter)
                        btn.bind("<Leave>", self.on_leave)
                except Exception:
                    pass

    def on_enter(self, event=None):
        self.schedule()

    def on_leave(self, event=None):
        self.unschedule()
        self.hide_tooltip()

    def schedule(self):
        self.unschedule()
        self.timer_id = self.widget.after(self.delay, self.show_tooltip)

    def unschedule(self):
        if self.timer_id:
            self.widget.after_cancel(self.timer_id)
            self.timer_id = None

    def show_tooltip(self):
        if self.tip_window or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 15
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8

            self.tip_window = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            tw.attributes("-topmost", True)

            frame = ctk.CTkFrame(tw, fg_color=("gray20", "gray10"), border_color=("#0288d1", "#0288d1"), border_width=1, corner_radius=6)
            frame.pack()

            lbl = ctk.CTkLabel(
                frame,
                text=self.text,
                font=ctk.CTkFont(size=11),
                text_color="white",
                padx=10,
                pady=6,
                justify="left"
            )
            lbl.pack()
        except Exception:
            pass

    def hide_tooltip(self):
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None


def create_info_icon(parent, tooltip_text, fg_color=("#e0e0e0", "#333333")):
    """Renders a sleek 'ℹ️' info badge button with an attached hover tooltip."""
    btn = ctk.CTkButton(
        parent,
        text="ℹ️",
        font=ctk.CTkFont(size=10, weight="bold"),
        width=20,
        height=20,
        corner_radius=10,
        fg_color=fg_color,
        hover_color=("#0288d1", "#0288d1"),
        text_color=("gray20", "gray90")
    )
    CTkToolTip(btn, tooltip_text)
    return btn


class Windows11ConflictDialog(_BaseToplevel):
    def __init__(self, parent, src_path, dst_path, thumbnail_loader_func=None):
        if not HAS_CUSTOMTKINTER:
            raise RuntimeError("CustomTkinter is required for Windows11ConflictDialog. Install customtkinter with: pip install customtkinter")
        super().__init__(parent)

        self.src_path = src_path
        self.dst_path = dst_path
        self.thumbnail_loader_func = thumbnail_loader_func
        self.result_action = "skip"
        self.apply_all = False

        self.title("1 File Conflict")
        self.geometry("640x520")
        self.minsize(580, 480)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        filename = os.path.basename(self.src_path)
        src_dir_name = os.path.basename(os.path.dirname(self.src_path)) or "Source"
        dst_dir_name = os.path.basename(os.path.dirname(self.dst_path)) or "Destination"

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(
            container,
            text="Which files do you want to keep?",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#64b5f6",
            anchor="w"
        ).pack(fill="x", pady=(0, 2))

        ctk.CTkLabel(
            container,
            text="If you select both versions, the moved file will have a number added to its name.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("gray50", "gray70"),
            anchor="w"
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            container,
            text=f"📄 {filename}",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 8))

        hdr_grid = ctk.CTkFrame(container, fg_color="transparent")
        hdr_grid.pack(fill="x", pady=(0, 4))
        hdr_grid.grid_columnconfigure(0, weight=1)
        hdr_grid.grid_columnconfigure(1, weight=1)

        self.src_chk_var = tk.BooleanVar(value=False)
        self.dst_chk_var = tk.BooleanVar(value=True)

        chk_src_hdr = ctk.CTkCheckBox(
            hdr_grid,
            text=f"Files from {src_dir_name}",
            variable=self.src_chk_var,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.on_checkbox_changed
        )
        chk_src_hdr.grid(row=0, column=0, sticky="w", padx=5)

        chk_dst_hdr = ctk.CTkCheckBox(
            hdr_grid,
            text=f"Files already in {dst_dir_name}",
            variable=self.dst_chk_var,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.on_checkbox_changed
        )
        chk_dst_hdr.grid(row=0, column=1, sticky="w", padx=5)

        cards_grid = ctk.CTkFrame(container, fg_color="transparent")
        cards_grid.pack(fill="x", pady=(0, 12))
        cards_grid.grid_columnconfigure(0, weight=1)
        cards_grid.grid_columnconfigure(1, weight=1)

        self.render_file_panel(cards_grid, 0, self.src_path, self.src_chk_var, f"Files from {src_dir_name}")
        self.render_file_panel(cards_grid, 1, self.dst_path, self.dst_chk_var, f"Files already in {dst_dir_name}")

        actions_frame = ctk.CTkFrame(container, corner_radius=10, fg_color=("gray90", "gray20"))
        actions_frame.pack(fill="x", pady=(0, 10), ipadx=8, ipady=6)

        self.action_radio_var = tk.StringVar(value="skip")

        rb_replace = ctk.CTkRadioButton(
            actions_frame,
            text="✓ Replace the file in the destination",
            variable=self.action_radio_var,
            value="replace",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.on_radio_changed
        )
        rb_replace.pack(anchor="w", padx=12, pady=4)

        rb_skip = ctk.CTkRadioButton(
            actions_frame,
            text="↩ Skip this file (Keep existing file untouched)",
            variable=self.action_radio_var,
            value="skip",
            font=ctk.CTkFont(size=11),
            command=self.on_radio_changed
        )
        rb_skip.pack(anchor="w", padx=12, pady=4)

        rb_number = ctk.CTkRadioButton(
            actions_frame,
            text="🔀 Keep both files (Add a number to moved file)",
            variable=self.action_radio_var,
            value="number",
            font=ctk.CTkFont(size=11),
            command=self.on_radio_changed
        )
        rb_number.pack(anchor="w", padx=12, pady=4)

        bottom_frame = ctk.CTkFrame(container, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(5, 0))
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.apply_all_var = tk.BooleanVar(value=False)
        chk_all = ctk.CTkCheckBox(
            bottom_frame,
            text="Apply this choice for all remaining conflicts",
            variable=self.apply_all_var,
            font=ctk.CTkFont(size=11)
        )
        chk_all.grid(row=0, column=0, sticky="w")

        btn_box = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_box.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            btn_box,
            text="Continue",
            command=self.on_continue,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0288d1",
            height=32,
            width=100
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_box,
            text="Cancel",
            command=self.on_cancel,
            font=ctk.CTkFont(size=12),
            fg_color=("gray75", "gray30"),
            text_color=("gray10", "gray90"),
            height=32,
            width=80
        ).pack(side="left", padx=4)

    def render_file_panel(self, parent_grid, col_idx, file_path, chk_var, label_title):
        panel = ctk.CTkFrame(parent_grid, corner_radius=10, fg_color=("gray88", "gray24"))
        panel.grid(row=0, column=col_idx, sticky="nsew", padx=4, pady=2)
        panel.grid_columnconfigure(0, weight=1)

        thumb_frame = ctk.CTkFrame(panel, fg_color=("gray80", "gray18"), corner_radius=8, height=110)
        thumb_frame.pack(fill="x", padx=8, pady=8)
        thumb_frame.pack_propagate(False)

        ctk_thumb = None
        if self.thumbnail_loader_func:
            ctk_thumb = self.thumbnail_loader_func(file_path, target_size=(180, 100))

        if ctk_thumb:
            lbl_img = ctk.CTkLabel(thumb_frame, image=ctk_thumb, text="")
            lbl_img.pack(expand=True)
        else:
            ext = os.path.splitext(file_path)[1].upper()
            lbl_icon = ctk.CTkLabel(
                thumb_frame,
                text=f"📄\n{ext if ext else 'FILE'}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="gray60"
            )
            lbl_icon.pack(expand=True)

        try:
            stat = os.stat(fix_win_long_path(file_path))
            mtime_str = datetime.fromtimestamp(stat.st_mtime).strftime("%d-%m-%Y %I:%M %p")
            sz_str = format_bytes(stat.st_size)
        except Exception:
            mtime_str = "Unknown Date"
            sz_str = "Unknown Size"

        meta_box = ctk.CTkFrame(panel, fg_color="transparent")
        meta_box.pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkCheckBox(meta_box, text="Select Version", variable=chk_var, font=ctk.CTkFont(size=10), command=self.on_checkbox_changed).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(meta_box, text=f"📅 {mtime_str}", font=ctk.CTkFont(size=10), text_color=("gray40", "gray70")).pack(anchor="w")
        ctk.CTkLabel(meta_box, text=f"⚖️ {sz_str}", font=ctk.CTkFont(size=10), text_color=("gray40", "gray70")).pack(anchor="w")

    def on_checkbox_changed(self):
        s = self.src_chk_var.get()
        d = self.dst_chk_var.get()
        if s and d:
            self.action_radio_var.set("number")
        elif s and not d:
            self.action_radio_var.set("replace")
        elif not s and d:
            self.action_radio_var.set("skip")

    def on_radio_changed(self):
        val = self.action_radio_var.get()
        if val == "replace":
            self.src_chk_var.set(True)
            self.dst_chk_var.set(False)
        elif val == "skip":
            self.src_chk_var.set(False)
            self.dst_chk_var.set(True)
        elif val == "number":
            self.src_chk_var.set(True)
            self.dst_chk_var.set(True)

    def on_continue(self):
        self.result_action = self.action_radio_var.get()
        self.apply_all = self.apply_all_var.get()
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def on_cancel(self):
        self.result_action = "skip"
        self.apply_all = self.apply_all_var.get()
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
