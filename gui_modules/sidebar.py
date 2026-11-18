"""
sidebar.py — Left-Side Collapsible Toolbar Navigation
Smart File Organizer Suite Pro

Implements a sleek vertical sidebar toolbar on the left side of the window
with Apple Glassmorphism styling, tool switching buttons, and one-click expand/collapse.
Uses separate, fixed-width icon cells and text labels so all navigation items are
100% pixel-aligned vertically regardless of OS font fallbacks or emoji width variations.
"""

import tkinter as tk

try:
    import customtkinter as ctk
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

try:
    from gui_modules.theme_manager import GLASS, FONTS, resolve_accent
    HAS_THEME = True
except ImportError:
    HAS_THEME = False

try:
    from gui_modules.components import CTkToolTip
    HAS_TOOLTIP = True
except ImportError:
    HAS_TOOLTIP = False


# Tool definitions: Using standard Unicode icons
TOOLS = [
    {"key": "organizer",   "icon": "🗂",  "short": "Organizer",  "title": "🗂 File Organizer"},
    {"key": "duplicates",  "icon": "🔍", "short": "Duplicates", "title": "🔍 Duplicates Finder"},
    {"key": "people",      "icon": "👥", "short": "People",     "title": "👥 People Sorter"},
    {"key": "extractor",   "icon": "📦", "short": "Extractor",  "title": "📦 Subfolder Extractor"},
    {"key": "converter",   "icon": "🪄", "short": "Converter",  "title": "🪄 Magic Converter"},
    {"key": "renamer",     "icon": "🏷",  "short": "Renamer",    "title": "🏷 Bulk Renamer"},
    {"key": "cleaner",     "icon": "🧹", "short": "Cleaner",    "title": "🧹 Storage Cleaner"},
    {"key": "analytics",   "icon": "📊", "short": "Analytics",  "title": "📊 Analytics"},
    {"key": "watcher",     "icon": "👁",  "short": "Watcher",    "title": "👁 Auto Watcher"},
    {"key": "exclusions",  "icon": "🚫", "short": "Exclusions", "title": "🚫 Exclusions Rules"},
]


class SidebarNavButton(ctk.CTkFrame if HAS_CTK else object):
    """
    Two-component navigation button widget:
    - Fixed 28px centered icon container
    - Left-aligned text label starting at a guaranteed identical offset
    Guarantees perfectly aligned text columns without emoji spacing drift.
    """
    def __init__(self, parent, tool, command, **kwargs):
        if not HAS_CTK:
            return

        super().__init__(
            parent,
            height=36,
            corner_radius=10,
            fg_color="transparent",
            cursor="hand2",
            **kwargs
        )
        self.tool = tool
        self.command = command
        self.is_active = False
        self.is_collapsed = False
        self.pack_propagate(False)

        self.accent_fg = ("#007AFF", "#0A84FF")
        self.accent_hover_fg = ("#0062cc", "#0071e3")
        self.normal_fg = "transparent"
        self.normal_hover_fg = GLASS["bg_hover"] if HAS_THEME else ("gray80", "gray28")
        self.normal_tc = GLASS["text_primary"] if HAS_THEME else ("gray15", "gray90")
        self.active_tc = "#FFFFFF"

        # Fixed 28px icon cell guarantees identical horizontal start for all labels
        self.icon_label = ctk.CTkLabel(
            self,
            text=tool["icon"],
            width=28,
            font=ctk.CTkFont(family="Segoe UI Emoji", size=13),
            anchor="center",
            text_color=self.normal_tc,
            cursor="hand2"
        )
        self.icon_label.pack(side="left", padx=(8, 6), fill="y")

        # Text label starts at exact same coordinate (42px) for every button
        self.text_label = ctk.CTkLabel(
            self,
            text=tool["short"],
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            anchor="w",
            text_color=self.normal_tc,
            cursor="hand2"
        )
        self.text_label.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Event bindings on container and both labels
        for w in (self, self.icon_label, self.text_label):
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def _on_click(self, event=None):
        if self.command:
            self.command(self.tool["key"])

    def _on_enter(self, event=None):
        if self.is_active:
            self.configure(fg_color=self.accent_hover_fg)
        else:
            self.configure(fg_color=self.normal_hover_fg)

    def _on_leave(self, event=None):
        if self.is_active:
            self.configure(fg_color=self.accent_fg)
        else:
            self.configure(fg_color=self.normal_fg)

    def set_active(self, active: bool):
        self.is_active = active
        if active:
            self.configure(fg_color=self.accent_fg)
            self.icon_label.configure(text_color=self.active_tc)
            self.text_label.configure(text_color=self.active_tc)
        else:
            self.configure(fg_color=self.normal_fg)
            self.icon_label.configure(text_color=self.normal_tc)
            self.text_label.configure(text_color=self.normal_tc)

    def set_collapsed(self, collapsed: bool):
        self.is_collapsed = collapsed
        if collapsed:
            self.text_label.pack_forget()
            self.icon_label.pack_configure(padx=0, fill="both", expand=True)
        else:
            self.icon_label.pack_configure(padx=(8, 6), fill="y", expand=False)
            self.text_label.pack(side="left", fill="both", expand=True, padx=(0, 8))


class LeftSidebarToolbar(ctk.CTkFrame if HAS_CTK else object):
    """
    Vertical sidebar toolbar positioned on the side of the main application.
    Supports full mode (Icons + Labels, width ~160px) and collapsed mode (Icons only, width ~52px).
    """
    EXPANDED_WIDTH = 160
    COLLAPSED_WIDTH = 52

    def __init__(self, parent, app_instance, **kwargs):
        if not HAS_CTK:
            return

        bg_card = GLASS["bg_card"] if HAS_THEME else ("gray90", "gray17")
        border = GLASS["border"] if HAS_THEME else ("gray75", "gray30")

        defaults = {
            "corner_radius": 16,
            "fg_color": bg_card,
            "border_color": border,
            "border_width": 1,
            "width": self.EXPANDED_WIDTH,
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

        self.app = app_instance
        self.is_collapsed = False
        self.buttons = {}
        self.active_key = "organizer"

        self.grid_propagate(False)
        self.pack_propagate(False)

        self._setup_ui()

    def _setup_ui(self):
        # Header / Collapse Toggle Row (Latin-1 « / » ensures zero glyph missing boxes on any Windows font)
        hdr_frame = ctk.CTkFrame(self, fg_color="transparent")
        hdr_frame.pack(fill="x", padx=8, pady=(10, 8))

        self.toggle_btn = ctk.CTkButton(
            hdr_frame,
            text="«  Collapse",
            command=self.toggle_collapse,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            height=28,
            corner_radius=8,
            fg_color=GLASS["bg_card_alt"] if HAS_THEME else ("gray80", "gray25"),
            text_color=GLASS["text_primary"] if HAS_THEME else ("gray10", "gray90"),
            hover_color=GLASS["bg_hover"] if HAS_THEME else ("gray70", "gray35")
        )
        self.toggle_btn.pack(fill="x")

        # Tool buttons container
        self.btn_container = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_container.pack(fill="both", expand=True, padx=6, pady=(0, 8))

        for idx, tool in enumerate(TOOLS):
            btn = SidebarNavButton(
                self.btn_container,
                tool=tool,
                command=self.select_tool
            )
            btn.pack(fill="x", pady=2)

            tooltip = None
            if HAS_TOOLTIP:
                tooltip = CTkToolTip(btn, text=tool["title"], delay=0.4)

            self.buttons[tool["key"]] = {
                "widget": btn,
                "tool": tool,
                "tooltip": tooltip
            }

        self.update_active_highlight("organizer")

    def select_tool(self, key):
        self.active_key = key
        self.update_active_highlight(key)
        if hasattr(self.app, "show_panel"):
            self.app.show_panel(key)

    def update_active_highlight(self, active_key):
        self.active_key = active_key
        for key, item in self.buttons.items():
            btn = item["widget"]
            btn.set_active(key == active_key)

    def toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed
        if self.is_collapsed:
            self.configure(width=self.COLLAPSED_WIDTH)
            self.toggle_btn.configure(text="»")
            for item in self.buttons.values():
                btn = item["widget"]
                btn.set_collapsed(True)
        else:
            self.configure(width=self.EXPANDED_WIDTH)
            self.toggle_btn.configure(text="«  Collapse")
            for item in self.buttons.values():
                btn = item["widget"]
                btn.set_collapsed(False)


# Aliases for compatibility
RightSidebarToolbar = LeftSidebarToolbar
SidebarToolbar = LeftSidebarToolbar
