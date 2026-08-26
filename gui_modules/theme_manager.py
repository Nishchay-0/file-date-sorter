"""
theme_manager.py — Apple Glassmorphism Design System
Smart File Organizer Suite Pro

Central design token registry and widget factory helpers.
All color tokens, font sizes, corner radii, and factory functions live here.
Import from any gui_modules file to keep consistent styling.
"""

try:
    import customtkinter as ctk
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

# ---------------------------------------------------------------------------
# Design Tokens
# ---------------------------------------------------------------------------

# (light_value, dark_value) tuples — pass directly to CTkWidget fg_color etc.
GLASS = {
    # Backgrounds
    "bg_primary":      ("#F2F2F7", "#1C1C1E"),
    "bg_card":         ("#FFFFFF", "#2C2C2E"),
    "bg_card_alt":     ("#F5F5F7", "#242426"),
    "bg_hover":        ("#E8E8ED", "#38383A"),
    "bg_selected":     ("#D1D1D6", "#48484A"),

    # Accent colors
    "accent_blue":     "#007AFF",
    "accent_blue_dk":  "#0A84FF",
    "accent_purple":   "#AF52DE",
    "accent_purple_dk": "#BF5AF2",
    "accent_teal":     "#32ADE6",
    "accent_teal_dk":  "#64D2FF",
    "accent_green":    "#34C759",
    "accent_green_dk": "#30D158",
    "accent_orange":   "#FF9500",
    "accent_orange_dk": "#FF9F0A",
    "accent_red":      "#FF3B30",
    "accent_red_dk":   "#FF453A",

    # Text
    "text_primary":    ("#1C1C1E", "#F2F2F7"),
    "text_secondary":  ("#8E8E93", "#98989D"),
    "text_hint":       ("#AEAEB2", "#636366"),

    # Borders & Shadows
    "border":          ("#D1D1D6", "#38383A"),
    "border_accent":   ("#007AFF", "#0A84FF"),
    "shadow":          ("rgba(0,0,0,0.06)", "rgba(0,0,0,0.3)"),
    "hover_bg":        ("#E8E8ED", "#38383A"),
    "selected_bg":     ("#D1D1D6", "#48484A"),

    # Corner radii
    "r_window":  16,
    "r_card":    16,
    "r_button":  10,
    "r_entry":   8,
    "r_badge":   20,
    "r_tab":     12,
    "r_status":  8,
}


def _font(size=12, weight="normal", family="Segoe UI"):
    if not HAS_CTK:
        return None
    return ctk.CTkFont(family=family, size=size, weight=weight)


FONTS = {
    "title":   lambda: _font(22, "bold"),
    "h1":      lambda: _font(15, "bold"),
    "h2":      lambda: _font(13, "bold"),
    "body":    lambda: _font(12, "normal"),
    "caption": lambda: _font(11, "normal"),
    "badge":   lambda: _font(10, "bold"),
    "mono":    lambda: _font(11, "normal", "Consolas"),
}


def resolve_accent(name: str):
    """Return (light_hex, dark_hex) for a named accent."""
    light = GLASS.get(f"accent_{name}", "#007AFF")
    dark  = GLASS.get(f"accent_{name}_dk", light)
    return (light, dark)


def glass_frame(parent, corner_radius=None, border_width=1, **kw):
    if not HAS_CTK:
        return None
    r = corner_radius if corner_radius is not None else GLASS["r_card"]
    defaults = dict(fg_color=GLASS["bg_card"], border_color=GLASS["border"],
                    border_width=border_width, corner_radius=r)
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


def glass_frame_alt(parent, corner_radius=None, **kw):
    if not HAS_CTK:
        return None
    r = corner_radius if corner_radius is not None else GLASS["r_card"]
    defaults = dict(fg_color=GLASS["bg_card_alt"], border_color=GLASS["border"],
                    border_width=1, corner_radius=r)
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


def _attach_hover_pulse(widget):
    def on_enter(e):
        try:
            widget.configure(border_width=2, border_color=GLASS["border_accent"])
        except Exception:
            pass
    def on_leave(e):
        try:
            widget.configure(border_width=0)
        except Exception:
            pass
    try:
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    except Exception:
        pass


def accent_button(parent, text, command=None, accent="blue", width=120, height=32,
                  icon="", corner_radius=None, font=None, **kw):
    if not HAS_CTK:
        return None
    r = corner_radius if corner_radius is not None else GLASS["r_button"]
    fg_light, fg_dark = resolve_accent(accent)
    label = f"{icon} {text}".strip() if icon else text
    btn = ctk.CTkButton(parent, text=label, command=command,
                        fg_color=(fg_light, fg_dark),
                        hover_color=(fg_light, fg_dark),
                        corner_radius=r, width=width, height=height,
                        font=font or FONTS["body"](), **kw)
    _attach_hover_pulse(btn)
    return btn


def primary_button(parent, text, command=None, accent="blue", width=120, height=32,
                   icon="", corner_radius=None, font=None, **kw):
    """Primary action button with solid accent background and hover pulse."""
    return accent_button(parent, text, command=command, accent=accent, width=width,
                         height=height, icon=icon, corner_radius=corner_radius,
                         font=font, **kw)


def secondary_button(parent, text, command=None, width=110, height=30, icon="", **kw):
    if not HAS_CTK:
        return None
    label = f"{icon} {text}".strip() if icon else text
    return ctk.CTkButton(parent, text=label, command=command,
                         fg_color="transparent", hover_color=GLASS["bg_hover"],
                         border_color=GLASS["border"], border_width=1,
                         corner_radius=GLASS["r_button"], width=width, height=height,
                         font=FONTS["body"](), text_color=GLASS["text_primary"], **kw)


def section_label(parent, text, **kw):
    if not HAS_CTK:
        return None
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(frame, text=text, font=FONTS["h2"](), anchor="w", **kw).pack(side="left")
    return frame


def status_badge(parent, text, accent="blue", **kw):
    if not HAS_CTK:
        return None
    fg_light, fg_dark = resolve_accent(accent)
    return ctk.CTkLabel(parent, text=f"  {text}  ", font=FONTS["badge"](),
                        fg_color=(fg_light, fg_dark), text_color="#FFFFFF",
                        corner_radius=GLASS["r_badge"], **kw)


def styled_entry(parent, textvariable=None, placeholder="", width=None, **kw):
    if not HAS_CTK:
        return None
    defaults = dict(textvariable=textvariable, placeholder_text=placeholder,
                    corner_radius=GLASS["r_entry"], border_width=1,
                    border_color=GLASS["border"], fg_color=GLASS["bg_card"],
                    font=FONTS["body"](), height=32)
    if width:
        defaults["width"] = width
    defaults.update(kw)
    return ctk.CTkEntry(parent, **defaults)


def styled_progress(parent, height=8, accent="blue", **kw):
    if not HAS_CTK:
        return None
    fg_light, fg_dark = resolve_accent(accent)
    return ctk.CTkProgressBar(parent, height=height, corner_radius=height // 2,
                              progress_color=(fg_light, fg_dark),
                              fg_color=GLASS["bg_card_alt"], **kw)


def animate_hover(widget, enter_color, leave_color):
    def on_enter(e):
        try: widget.configure(fg_color=enter_color)
        except Exception: pass
    def on_leave(e):
        try: widget.configure(fg_color=leave_color)
        except Exception: pass
    try:
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    except Exception:
        pass


LIGHT_THEME = {
    "bg_primary": "#F2F2F7",
    "bg_card": "#FFFFFF",
    "bg_card_alt": "#F5F5F7",
    "bg_hover": "#E8E8ED",
    "bg_selected": "#D1D1D6",
    "accent": "#007AFF",
    "text_primary": "#1C1C1E",
    "text_secondary": "#8E8E93",
    "border": "#C6C6C8",
}

DARK_THEME = {
    "bg_primary": "#1C1C1E",
    "bg_card": "#2C2C2E",
    "bg_card_alt": "#242426",
    "bg_hover": "#38383A",
    "bg_selected": "#48484A",
    "accent": "#0A84FF",
    "text_primary": "#F2F2F7",
    "text_secondary": "#98989D",
    "border": "#38383A",
}


def configure_treeview_glass_style(mode: str = "dark"):
    """
    Configures ttk.Treeview with modern Apple Big Sur glass styling:
    comfortable row heights (28px), subtle borders, clean headers,
    and adaptive light/dark mode palettes.
    """
    try:
        import tkinter.ttk as ttk
        style = ttk.Style()
        is_dark = str(mode).lower() == "dark"

        # Colors matching Apple Big Sur glass tokens
        bg_card = "#242426" if is_dark else "#FFFFFF"
        fg_text = "#F2F2F7" if is_dark else "#1C1C1E"
        bg_hdr  = "#2C2C2E" if is_dark else "#E5E5EA"
        fg_hdr  = "#F2F2F7" if is_dark else "#1C1C1E"
        sel_bg  = "#0A84FF" if is_dark else "#007AFF"
        sel_fg  = "#FFFFFF"

        # Apply to default clam theme for custom coloring
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Treeview",
            background=bg_card,
            foreground=fg_text,
            fieldbackground=bg_card,
            rowheight=28,
            font=("Segoe UI", 10),
            borderwidth=0,
            relief="flat"
        )
        style.map(
            "Treeview",
            background=[("selected", sel_bg)],
            foreground=[("selected", sel_fg)]
        )
        style.configure(
            "Treeview.Heading",
            background=bg_hdr,
            foreground=fg_hdr,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padding=(6, 4)
        )
        style.map(
            "Treeview.Heading",
            background=[("active", sel_bg), ("pressed", sel_bg)],
            foreground=[("active", "#FFFFFF"), ("pressed", "#FFFFFF")]
        )
    except Exception:
        pass


def apply_theme(mode: str = "dark"):
    """Applies global appearance mode (light / dark)."""
    if not HAS_CTK:
        return
    m = mode.lower()
    if m in ["light", "dark", "system"]:
        ctk.set_appearance_mode(m.capitalize())


def apply_glass_theme(mode: str = "dark"):
    """Applies global appearance mode and configures Treeview glass styles."""
    if not HAS_CTK:
        return
    apply_theme(mode)
    ctk.set_default_color_theme("blue")
    configure_treeview_glass_style(mode)


def apply_theme_to_widget(widget, theme: str = "dark"):
    """Recursively updates appearance and theme tokens."""
    apply_glass_theme(theme)
