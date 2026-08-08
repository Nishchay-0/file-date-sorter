"""
gui_modules/views/tab_people.py - GUI View for Face-Based People Photo & Video Sorter

Provides interactive GUI controls for:
- Selecting target folder and running background face detection & video sampling scan.
- Browsing detected face clusters in a responsive review grid.
- Renaming person clusters, merging clusters, and excluding false positives.
- Creating opt-in Windows shortcuts in People/<Name>/ without touching original files.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    import customtkinter as ctk
    HAS_CUSTOMTKINTER = True
except ImportError:
    HAS_CUSTOMTKINTER = False

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from gui_modules.components import CTkToolTip, create_info_icon
from face_sort import FaceSorterEngine


def setup_people_tab(gui_instance):
    scroll = ctk.CTkScrollableFrame(gui_instance.tab_people, fg_color="transparent")
    scroll.pack(fill="both", expand=True)
    scroll.grid_columnconfigure(0, weight=1)
    gui_instance.people_scroll = scroll
    gui_instance.face_engine = FaceSorterEngine()

    # ── HEADER CARD ──
    hdr_card = ctk.CTkFrame(scroll, corner_radius=12)
    hdr_card.grid(row=0, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    hdr_card.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        hdr_card,
        text="👥 Face-Based People Sorter (Photos & Videos)",
        font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
    ).pack(anchor="w", padx=12, pady=(6, 2))

    ctk.CTkLabel(
        hdr_card,
        text="Automatically detects faces in photos & videos, groups them by person with DBSCAN clustering, and lets you review clusters without moving original files.",
        font=ctk.CTkFont(size=11),
        text_color="gray60"
    ).pack(anchor="w", padx=12, pady=(0, 6))

    # ── SECTION 1: SCAN CONTROLS ──
    scan_card = ctk.CTkFrame(scroll, corner_radius=12)
    scan_card.grid(row=1, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    scan_card.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(scan_card, text="1. Target Folder & Scan Settings", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(6, 4))

    ctk.CTkLabel(scan_card, text="Target Path:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)

    gui_instance.people_dir_var = tk.StringVar()
    gui_instance.people_dir_entry = ctk.CTkEntry(scan_card, textvariable=gui_instance.people_dir_var, placeholder_text="Select directory containing photos and videos...", font=ctk.CTkFont(size=11), height=32)
    gui_instance.people_dir_entry.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)

    btn_box = ctk.CTkFrame(scan_card, fg_color="transparent")
    btn_box.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=4)

    def _browse_dir():
        d = filedialog.askdirectory(title="Select Photo/Video Directory for People Sorter")
        if d:
            gui_instance.people_dir_var.set(d)

    ctk.CTkButton(btn_box, text="📁 Pick Folder...", command=_browse_dir, font=ctk.CTkFont(size=10, weight="bold"), height=32, width=105).pack(side="left", padx=(0, 4))
    
    gui_instance.people_scan_btn = ctk.CTkButton(btn_box, text="🔍 Start People Scan", command=lambda: _start_people_scan(gui_instance), font=ctk.CTkFont(size=10, weight="bold"), height=32, width=135, fg_color="#0288d1")
    gui_instance.people_scan_btn.pack(side="left")

    # Progress Indicator
    prog_frame = ctk.CTkFrame(scan_card, fg_color="transparent")
    prog_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=12, pady=(4, 2))
    prog_frame.grid_columnconfigure(0, weight=1)

    gui_instance.people_progress_bar = ctk.CTkProgressBar(prog_frame, height=10)
    gui_instance.people_progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
    gui_instance.people_progress_bar.set(0)

    gui_instance.people_status_lbl = ctk.CTkLabel(prog_frame, text="Status: Ready to scan", font=ctk.CTkFont(size=10), text_color="gray60")
    gui_instance.people_status_lbl.grid(row=1, column=0, sticky="w")

    # ── SECTION 2: PEOPLE CLUSTER REVIEW GRID ──
    review_card = ctk.CTkFrame(scroll, corner_radius=12)
    review_card.grid(row=2, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    review_card.grid_columnconfigure(0, weight=1)

    rev_hdr = ctk.CTkFrame(review_card, fg_color="transparent")
    rev_hdr.pack(fill="x", padx=12, pady=(6, 4))

    ctk.CTkLabel(rev_hdr, text="2. Detected People & Cluster Review Grid", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).pack(side="left")
    create_info_icon(rev_hdr, "Review detected face clusters: rename person names, merge clusters, or opt-in to generate People/ shortcuts.").pack(side="left", padx=6)

    gui_instance.people_grid_frame = ctk.CTkFrame(review_card, fg_color="transparent")
    gui_instance.people_grid_frame.pack(fill="x", padx=12, pady=6)
    gui_instance.people_grid_frame.grid_columnconfigure(0, weight=1)
    gui_instance.people_grid_frame.grid_columnconfigure(1, weight=1)

    # ── SECTION 3: ACTION BAR ──
    act_card = ctk.CTkFrame(scroll, corner_radius=12)
    act_card.grid(row=3, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    act_card.grid_columnconfigure(0, weight=1)

    act_hdr = ctk.CTkFrame(act_card, fg_color="transparent")
    act_hdr.pack(fill="x", padx=12, pady=4)

    ctk.CTkButton(
        act_hdr,
        text="💾 Save People Index (.people_index.json)",
        command=lambda: _save_index(gui_instance),
        font=ctk.CTkFont(size=11, weight="bold"),
        height=32,
        fg_color=("gray75", "gray30"),
        text_color=("gray10", "gray90")
    ).pack(side="left", padx=(0, 6))

    btn_shortcuts = ctk.CTkButton(
        act_hdr,
        text="📁 Create People/ Shortcuts (Opt-In Non-Destructive)",
        command=lambda: _create_shortcuts(gui_instance),
        font=ctk.CTkFont(size=11, weight="bold"),
        height=32,
        fg_color="#2e7d32",
        hover_color="#1b5e20"
    )
    btn_shortcuts.pack(side="left")
    CTkToolTip(btn_shortcuts, "Non-destructive action: Creates Windows .url shortcuts under a 'People/<PersonName>/' folder so you can browse photos by person without moving originals!")


def _start_people_scan(gui_instance):
    target_dir = gui_instance.people_dir_var.get().strip()
    if not target_dir or not os.path.exists(target_dir):
        messagebox.showwarning("Directory Required", "Please select a valid directory containing photos or videos.")
        return

    gui_instance.people_scan_btn.configure(state="disabled")
    gui_instance.people_progress_bar.set(0)
    gui_instance.people_status_lbl.configure(text="Status: Scanning files and computing face embeddings...")

    def run_worker():
        def on_prog(cur, tot, fn):
            ratio = cur / float(tot) if tot > 0 else 0
            gui_instance.after(0, lambda: gui_instance.people_progress_bar.set(ratio))
            gui_instance.after(0, lambda: gui_instance.people_status_lbl.configure(text=f"Processing ({cur}/{tot}): {fn}"))

        res = gui_instance.face_engine.scan_directory(target_dir, progress_callback=on_prog)
        gui_instance.after(0, lambda: _on_scan_complete(gui_instance, res))

    threading.Thread(target=run_worker, daemon=True).start()


def _on_scan_complete(gui_instance, res):
    gui_instance.people_scan_btn.configure(state="normal")
    gui_instance.people_progress_bar.set(1.0)
    tot = res.get('total_files', 0)
    faces = res.get('faces_found', 0)
    clusters = res.get('clusters', {})
    gui_instance.people_status_lbl.configure(text=f"Status: Scan complete! Processed {tot} files | Found {faces} faces in {len(clusters)} person clusters.")
    _render_clusters_grid(gui_instance, clusters)


def _render_clusters_grid(gui_instance, clusters):
    for w in gui_instance.people_grid_frame.winfo_children():
        w.destroy()

    if not clusters:
        ctk.CTkLabel(gui_instance.people_grid_frame, text="No face clusters detected yet. Select a folder and click 'Start People Scan'.", font=ctk.CTkFont(size=11), text_color="gray60").grid(row=0, column=0, columnspan=2, pady=10)
        return

    r = 0
    c = 0
    for p_id, cluster in clusters.items():
        card = ctk.CTkFrame(gui_instance.people_grid_frame, corner_radius=10, fg_color=("gray85", "gray22"))
        card.grid(row=r, column=c, sticky="ew", padx=6, pady=6, ipadx=6, ipady=6)
        card.grid_columnconfigure(1, weight=1)

        # Avatar / Thumbnail Box
        thumb_box = ctk.CTkFrame(card, corner_radius=8, width=70, height=70, fg_color=("gray75", "gray16"))
        thumb_box.grid(row=0, column=0, padx=6, pady=6)
        thumb_box.pack_propagate(False)

        faces = cluster.get('faces', [])
        ctk.CTkLabel(thumb_box, text=f"👤\n{len(faces)} items", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray60").pack(expand=True)

        meta_box = ctk.CTkFrame(card, fg_color="transparent")
        meta_box.grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        meta_box.grid_columnconfigure(0, weight=1)

        name_var = tk.StringVar(value=cluster.get('name', p_id))
        entry = ctk.CTkEntry(meta_box, textvariable=name_var, font=ctk.CTkFont(size=11, weight="bold"), height=28)
        entry.pack(fill="x", pady=(0, 4))

        def _update_name(pid=p_id, v=name_var):
            if pid in gui_instance.face_engine.index.get('clusters', {}):
                gui_instance.face_engine.index['clusters'][pid]['name'] = v.get().strip()

        name_var.trace_add("write", lambda *a: _update_name())

        v_count = sum(1 for f in faces if f.get('is_video'))
        p_count = len(faces) - v_count
        ctk.CTkLabel(meta_box, text=f"📸 Photos: {p_count} | 🎬 Videos: {v_count}", font=ctk.CTkFont(size=10), text_color="gray60").pack(anchor="w")

        c += 1
        if c > 1:
            c = 0
            r += 1


def _save_index(gui_instance):
    gui_instance.face_engine._save_json(gui_instance.face_engine.index, gui_instance.face_engine.index_file)
    messagebox.showinfo("Index Saved", f"People index successfully saved to '{gui_instance.face_engine.index_file}'.")


def _create_shortcuts(gui_instance):
    t_dir = gui_instance.people_dir_var.get().strip()
    if not t_dir or not os.path.exists(t_dir):
        messagebox.showwarning("Target Folder Required", "Please select a target folder first.")
        return

    res = gui_instance.face_engine.create_people_shortcuts(t_dir)
    cnt = res.get('created_shortcuts', 0)
    p_dir = res.get('people_dir', '')
    messagebox.showinfo("Shortcuts Created", f"Successfully created {cnt} opt-in shortcuts in:\n'{p_dir}'.\nOriginal files remain untouched!")
