"""
gui_modules/views/tab_people.py - GUI View for Face-Based People Photo & Video Sorter

Provides rich interactive GUI controls for:
- Target folder selection, cloud placeholder pre-check, and background face scanning.
- Review grid with search, sort (most items, fewest items, name, date), and 1-item filter.
- Real face crop thumbnail strips (3-4 face crops per card) rendered using PIL & Base64 thumbnails.
- Outlier warning badges for unusually large clusters.
- Date ranges per person cluster (e.g. "Jan 2023 – Aug 2026").
- Merge selected clusters action.
- "View All" modal gallery window with "Remove from Person" split control.
- Opt-in Windows shortcut generator in People/<Name>/ without touching original files.
"""

import os
import sys
import io
import base64
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
from face_sort import FaceSorterEngine, fix_win_long_path


def setup_people_tab(gui_instance):
    scroll = ctk.CTkScrollableFrame(gui_instance.tab_people, fg_color="transparent")
    scroll.pack(fill="both", expand=True)
    scroll.grid_columnconfigure(0, weight=1)
    gui_instance.people_scroll = scroll
    gui_instance.face_engine = FaceSorterEngine()

    # Track selected cluster checkboxes for merge
    gui_instance.people_selected_clusters = set()

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
        text="Automatically detects faces in photos & videos, groups them by person with Complete-Linkage Cosine clustering, and lets you review clusters without moving original files.",
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

    # ── SECTION 2: SEARCH, SORT & FILTER TOOLBAR ──
    review_card = ctk.CTkFrame(scroll, corner_radius=12)
    review_card.grid(row=2, column=0, sticky="ew", pady=(0, 8), ipadx=8, ipady=8)
    review_card.grid_columnconfigure(0, weight=1)

    rev_hdr = ctk.CTkFrame(review_card, fg_color="transparent")
    rev_hdr.pack(fill="x", padx=12, pady=(6, 4))

    ctk.CTkLabel(rev_hdr, text="2. Detected People & Cluster Review Grid", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).pack(side="left")
    create_info_icon(rev_hdr, "Review detected face clusters: view face thumbnails, rename persons, merge clusters, or exclude false positives.").pack(side="left", padx=6)

    # Search & Sort Toolbar Row
    toolbar = ctk.CTkFrame(review_card, fg_color=("gray90", "gray18"), corner_radius=8)
    toolbar.pack(fill="x", padx=12, pady=(4, 8), ipadx=4, ipady=4)

    gui_instance.people_search_var = tk.StringVar()
    gui_instance.people_search_var.trace_add("write", lambda *a: _refresh_grid_view(gui_instance))
    search_entry = ctk.CTkEntry(toolbar, textvariable=gui_instance.people_search_var, placeholder_text="🔍 Search person by name...", font=ctk.CTkFont(size=11), width=180, height=28)
    search_entry.pack(side="left", padx=(6, 8))

    ctk.CTkLabel(toolbar, text="Sort by:", font=ctk.CTkFont(size=10, weight="bold")).pack(side="left", padx=(4, 4))

    gui_instance.people_sort_var = tk.StringVar(value="Most Items")
    sort_menu = ctk.CTkOptionMenu(
        toolbar,
        values=["Most Items", "Fewest Items", "Name (A-Z)", "Newest Date", "Oldest Date"],
        variable=gui_instance.people_sort_var,
        command=lambda e: _refresh_grid_view(gui_instance),
        font=ctk.CTkFont(size=10),
        width=120,
        height=28
    )
    sort_menu.pack(side="left", padx=(0, 10))

    gui_instance.people_hide_singletons_var = tk.BooleanVar(value=False)
    hide_sw = ctk.CTkSwitch(
        toolbar,
        text="Hide 1-Item Clusters",
        variable=gui_instance.people_hide_singletons_var,
        command=lambda: _refresh_grid_view(gui_instance),
        font=ctk.CTkFont(size=10, weight="bold")
    )
    hide_sw.pack(side="left", padx=(0, 10))

    gui_instance.people_merge_btn = ctk.CTkButton(
        toolbar,
        text="🔀 Merge Selected (0)",
        command=lambda: _merge_selected_clusters(gui_instance),
        font=ctk.CTkFont(size=10, weight="bold"),
        fg_color="#8e24aa",
        hover_color="#6a1b9a",
        height=28,
        width=135,
        state="disabled"
    )
    gui_instance.people_merge_btn.pack(side="right", padx=(0, 6))

    # Grid Container
    gui_instance.people_grid_frame = ctk.CTkFrame(review_card, fg_color="transparent")
    gui_instance.people_grid_frame.pack(fill="x", padx=12, pady=4)
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

    # Check if saved index exists to prevent accidental overwrites
    index_file = gui_instance.face_engine.index_file
    if os.path.exists(index_file):
        if not messagebox.askyesno(
            "Re-Scan Directory?",
            f"A saved People index already exists in '{index_file}'.\n\n"
            f"Re-scanning will update cluster assignments. Do you want to proceed?"
        ):
            return

    # Cloud Placeholder Pre-Check & Informed Consent Dialog
    from hashing import count_cloud_placeholders
    from sorter_core import gather_files
    from face_sort import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS

    all_files = gather_files(target_dir, recursive=True)
    target_media = [fp for fp in all_files if os.path.splitext(fp)[1].lower() in (IMAGE_EXTENSIONS | VIDEO_EXTENSIONS)]
    cloud_info = count_cloud_placeholders(target_media)

    if cloud_info['cloud_count'] > 0:
        sz_mb = round(cloud_info['total_bytes'] / (1024.0 * 1024.0), 1)
        sz_str = f"{sz_mb} MB" if sz_mb < 1024 else f"{round(sz_mb/1024.0, 2)} GB"
        msg = (
            f"☁️ Cloud-Only Files Detected!\n\n"
            f"Scanning for faces requires reading image pixel bytes.\n"
            f"This folder contains {cloud_info['cloud_count']} cloud-only placeholder file(s) "
            f"totaling approximately {sz_str}.\n\n"
            f"Do you want to proceed and download these files from your cloud storage?"
        )
        if not messagebox.askyesno("Cloud Download Confirmation", msg):
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
    _refresh_grid_view(gui_instance)


def _refresh_grid_view(gui_instance):
    clusters = gui_instance.face_engine.index.get('clusters', {})
    if not clusters:
        # Load from disk if index loaded
        clusters = gui_instance.face_engine.index.get('clusters', {})

    # Reset selections
    gui_instance.people_selected_clusters.clear()
    _update_merge_button_state(gui_instance)

    _render_clusters_grid(gui_instance, clusters)


def _decode_b64_image(b64_str, size=(64, 64)):
    """Decodes JPEG Base64 thumbnail string to CTkImage."""
    if not HAS_PIL or not b64_str:
        return None
    try:
        raw_bytes = base64.b64decode(b64_str)
        img = Image.open(io.BytesIO(raw_bytes))
        img = img.resize(size, Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except Exception:
        return None


def _render_clusters_grid(gui_instance, clusters):
    for w in gui_instance.people_grid_frame.winfo_children():
        w.destroy()

    if not clusters:
        ctk.CTkLabel(gui_instance.people_grid_frame, text="No face clusters detected yet. Select a folder and click 'Start People Scan'.", font=ctk.CTkFont(size=11), text_color="gray60").grid(row=0, column=0, columnspan=2, pady=10)
        return

    # Filter & Sort Clusters
    query = gui_instance.people_search_var.get().strip().lower()
    sort_mode = gui_instance.people_sort_var.get()
    hide_singletons = gui_instance.people_hide_singletons_var.get()

    filtered_items = []
    for pid, c in clusters.items():
        name = c.get('name', pid)
        faces = c.get('faces', [])

        if hide_singletons and len(faces) <= 1:
            continue

        if query and query not in name.lower() and query not in pid.lower():
            continue

        filtered_items.append((pid, c))

    # Apply Sorting
    if sort_mode == "Most Items":
        filtered_items.sort(key=lambda x: len(x[1].get('faces', [])), reverse=True)
    elif sort_mode == "Fewest Items":
        filtered_items.sort(key=lambda x: len(x[1].get('faces', [])))
    elif sort_mode == "Name (A-Z)":
        filtered_items.sort(key=lambda x: x[1].get('name', x[0]).lower())
    elif sort_mode == "Newest Date":
        filtered_items.sort(key=lambda x: x[1].get('max_timestamp', 0), reverse=True)
    elif sort_mode == "Oldest Date":
        filtered_items.sort(key=lambda x: x[1].get('min_timestamp', 0))

    if not filtered_items:
        ctk.CTkLabel(gui_instance.people_grid_frame, text="No clusters match your search/filter criteria.", font=ctk.CTkFont(size=11), text_color="gray60").grid(row=0, column=0, columnspan=2, pady=10)
        return

    r = 0
    c = 0
    for p_id, cluster in filtered_items:
        card = ctk.CTkFrame(gui_instance.people_grid_frame, corner_radius=10, fg_color=("gray85", "gray22"))
        card.grid(row=r, column=c, sticky="ew", padx=6, pady=6, ipadx=6, ipady=6)
        card.grid_columnconfigure(1, weight=1)

        # 1. Outlier Warning Badge (if cluster is unusually large)
        if cluster.get('is_outlier'):
            warn_lbl = ctk.CTkLabel(
                card,
                text="⚠️ Unusually large — review for mixed people",
                font=ctk.CTkFont(size=9, weight="bold"),
                fg_color=("#fff3cd", "#4a3c00"),
                text_color=("#856404", "#ffecb3"),
                corner_radius=4,
                height=18
            )
            warn_lbl.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=(4, 2))

        main_row = 1 if cluster.get('is_outlier') else 0

        # 2. Thumbnail Strip Container (Displays up to 4 real face crop thumbnails!)
        strip_frame = ctk.CTkFrame(card, fg_color="transparent")
        strip_frame.grid(row=main_row, column=0, padx=6, pady=4, sticky="nw")

        faces = cluster.get('faces', [])
        sample_faces = faces[:4]

        has_rendered_thumb = False
        for sf in sample_faces:
            b64_str = sf.get('thumbnail_b64', '')
            ctk_img = _decode_b64_image(b64_str, size=(48, 48))
            if ctk_img:
                lbl = ctk.CTkLabel(strip_frame, image=ctk_img, text="")
                lbl.pack(side="left", padx=1)
                has_rendered_thumb = True

        if not has_rendered_thumb:
            thumb_box = ctk.CTkFrame(strip_frame, corner_radius=6, width=64, height=64, fg_color=("gray75", "gray16"))
            thumb_box.pack(side="left")
            thumb_box.pack_propagate(False)
            ctk.CTkLabel(thumb_box, text=f"👤\n{len(faces)} items", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray60").pack(expand=True)

        # 3. Card Meta & Controls Box
        meta_box = ctk.CTkFrame(card, fg_color="transparent")
        meta_box.grid(row=main_row, column=1, sticky="ew", padx=6, pady=2)
        meta_box.grid_columnconfigure(0, weight=1)

        # Name Entry Header
        name_var = tk.StringVar(value=cluster.get('name', p_id))
        entry = ctk.CTkEntry(meta_box, textvariable=name_var, font=ctk.CTkFont(size=11, weight="bold"), height=26)
        entry.pack(fill="x", pady=(0, 2))

        def _update_name(pid=p_id, v=name_var):
            if pid in gui_instance.face_engine.index.get('clusters', {}):
                gui_instance.face_engine.index['clusters'][pid]['name'] = v.get().strip()

        name_var.trace_add("write", lambda *a: _update_name())

        # Item Counts & Date Range Labels
        v_count = sum(1 for f in faces if f.get('is_video'))
        p_count = len(faces) - v_count
        date_str = cluster.get('date_range_str', 'Date Unknown')

        ctk.CTkLabel(meta_box, text=f"📸 {p_count} photos | 🎬 {v_count} videos", font=ctk.CTkFont(size=10), text_color="gray60").pack(anchor="w")
        ctk.CTkLabel(meta_box, text=f"📅 {date_str}", font=ctk.CTkFont(size=10, weight="bold"), text_color="#0288d1").pack(anchor="w", pady=(1, 2))

        # Action Strip
        act_strip = ctk.CTkFrame(meta_box, fg_color="transparent")
        act_strip.pack(fill="x", pady=(2, 0))

        # Select Checkbox for Merge
        chk_var = tk.BooleanVar(value=p_id in gui_instance.people_selected_clusters)
        def _on_chk_toggle(pid=p_id, cv=chk_var):
            if cv.get():
                gui_instance.people_selected_clusters.add(pid)
            else:
                gui_instance.people_selected_clusters.discard(pid)
            _update_merge_button_state(gui_instance)

        chk = ctk.CTkCheckBox(act_strip, text="Merge", variable=chk_var, command=_on_chk_toggle, font=ctk.CTkFont(size=10), width=60, checkbox_width=16, checkbox_height=16)
        chk.pack(side="left", padx=(0, 4))

        # View All Action Button
        ctk.CTkButton(
            act_strip,
            text=f"👁️ View All ({len(faces)})",
            command=lambda pid=p_id: _open_person_gallery_modal(gui_instance, pid),
            font=ctk.CTkFont(size=10, weight="bold"),
            height=22,
            fg_color=("gray70", "gray35"),
            text_color=("gray10", "gray95")
        ).pack(side="right")

        c += 1
        if c > 1:
            c = 0
            r += 1


def _update_merge_button_state(gui_instance):
    cnt = len(gui_instance.people_selected_clusters)
    if cnt >= 2:
        gui_instance.people_merge_btn.configure(state="normal", text=f"🔀 Merge Selected ({cnt})")
    else:
        gui_instance.people_merge_btn.configure(state="disabled", text=f"🔀 Merge Selected ({cnt})")


def _merge_selected_clusters(gui_instance):
    selected = list(gui_instance.people_selected_clusters)
    if len(selected) < 2:
        return

    target_pid = selected[0]
    target_name = gui_instance.face_engine.index.get('clusters', {}).get(target_pid, {}).get('name', target_pid)

    if messagebox.askyesno(
        "Confirm Merge",
        f"Are you sure you want to merge {len(selected)} selected clusters into '{target_name}'?"
    ):
        gui_instance.face_engine.merge_clusters(selected[1:], target_pid)
        gui_instance.people_selected_clusters.clear()
        messagebox.showinfo("Clusters Merged", f"Successfully merged clusters into '{target_name}'.")
        _refresh_grid_view(gui_instance)


def _open_person_gallery_modal(gui_instance, person_id):
    """Opens a full scrollable photo/video gallery modal for a specific person cluster."""
    clusters = gui_instance.face_engine.index.get('clusters', {})
    cluster = clusters.get(person_id)
    if not cluster:
        return

    person_name = cluster.get('name', person_id)
    faces = cluster.get('faces', [])

    win = ctk.CTkToplevel(gui_instance)
    win.title(f"Gallery - {person_name} ({len(faces)} items)")
    win.geometry("780x560")
    win.grab_set()

    # Header
    hdr = ctk.CTkFrame(win, fg_color=("gray85", "gray20"))
    hdr.pack(fill="x", padx=12, pady=(12, 6), ipadx=8, ipady=6)

    ctk.CTkLabel(hdr, text=f"👤 {person_name}", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=8)
    ctk.CTkLabel(hdr, text=f"Total: {len(faces)} item(s) | Date: {cluster.get('date_range_str', 'Unknown')}", font=ctk.CTkFont(size=11), text_color="gray60").pack(side="right", padx=8)

    # Scrollable Gallery Grid
    gal_scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
    gal_scroll.pack(fill="both", expand=True, padx=12, pady=6)
    gal_scroll.grid_columnconfigure(0, weight=1)
    gal_scroll.grid_columnconfigure(1, weight=1)
    gal_scroll.grid_columnconfigure(2, weight=1)

    def _render_gallery_items():
        for w in gal_scroll.winfo_children():
            w.destroy()

        cur_faces = clusters.get(person_id, {}).get('faces', [])
        if not cur_faces:
            ctk.CTkLabel(gal_scroll, text="No items remaining in this person cluster.", font=ctk.CTkFont(size=11)).pack(pady=20)
            return

        r, c = 0, 0
        for f_idx_item, f_meta in enumerate(cur_faces):
            item_card = ctk.CTkFrame(gal_scroll, corner_radius=8, fg_color=("gray90", "gray25"))
            item_card.grid(row=r, column=c, padx=4, pady=4, sticky="ew")

            # Thumbnail
            b64_str = f_meta.get('thumbnail_b64', '')
            ctk_img = _decode_b64_image(b64_str, size=(80, 80))
            if ctk_img:
                ctk.CTkLabel(item_card, image=ctk_img, text="").pack(pady=(6, 2))
            else:
                ctk.CTkLabel(item_card, text="👤", font=ctk.CTkFont(size=24)).pack(pady=(12, 6))

            fp = f_meta.get('filepath', '')
            fname = os.path.basename(fp)
            if len(fname) > 22:
                fname = fname[:19] + "..."

            is_vid = f_meta.get('is_video')
            tag = f"🎬 {fname}" if is_vid else f"📸 {fname}"
            ctk.CTkLabel(item_card, text=tag, font=ctk.CTkFont(size=10, weight="bold")).pack(padx=4)

            # Split / Remove Action Button
            def _remove_item(target_fp=fp, target_fidx=f_meta.get('face_idx', 0)):
                if messagebox.askyesno("Remove Face", f"Remove '{os.path.basename(target_fp)}' from '{person_name}'?\n(File will not be deleted from disk)"):
                    gui_instance.face_engine.remove_face_from_cluster(person_id, target_fp, target_fidx)
                    _render_gallery_items()
                    _refresh_grid_view(gui_instance)

            ctk.CTkButton(
                item_card,
                text="❌ Remove",
                command=_remove_item,
                font=ctk.CTkFont(size=9, weight="bold"),
                height=20,
                width=75,
                fg_color="#c62828",
                hover_color="#8e0000"
            ).pack(pady=(4, 6))

            c += 1
            if c > 2:
                c = 0
                r += 1

    _render_gallery_items()


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
