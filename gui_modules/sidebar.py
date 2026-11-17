"""
sidebar.py — Left-Side Collapsible Toolbar Navigation
Smart File Organizer Suite Pro

Implements a sleek vertical sidebar toolbar on the left side of the window
with glassmorphism styling, tool switching buttons, and one-click expand/collapse.
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


# Tool definitions: Using clean, uniform single-width glyphs (no trailing \ufe0f variation selectors)
# so that all icons measure an exact, identical pixel width across all fonts.
TOOLS = [
    {"key": "organizer",   "icon": "📅", "short": "Organizer",  "title": "📅 File Organizer"},
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
        # Header / Collapse Toggle Row
        hdr_frame = ctk.CTkFrame(self, fg_color="transparent")
        hdr_frame.pack(fill="x", padx=8, pady=(10, 8))

        self.toggle_btn = ctk.CTkButton(
            hdr_frame,
            text="◂  Collapse",
            command=self.toggle_collapse,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            height=28,
            corner_radius=8,
            fg_color=GLASS["bg_card_alt"] if HAS_THEME else ("gray80", "gray25"),
            text_color=GLASS["text_primary"] if HAS_THEME else ("gray10", "gray90"),
            hover_color=GLASS["bg_hover"] if HAS_THEME else ("gray70", "gray35")
        )
        self.toggle_btn.pack(fill="x")

        # Tool buttons container (clean frame with uniform margin, no scrollbar clipping)
        self.btn_container = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_container.pack(fill="both", expand=True, padx=6, pady=(0, 8))

        for idx, tool in enumerate(TOOLS):
            btn = ctk.CTkButton(
                self.btn_container,
                text=f"  {tool['icon']}   {tool['short']}",
                anchor="w",
                command=lambda t=tool: self.select_tool(t["key"]),
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                height=36,
                corner_radius=10,
                fg_color="transparent",
                text_color=GLASS["text_primary"] if HAS_THEME else ("gray15", "gray90"),
                hover_color=GLASS["bg_hover"] if HAS_THEME else ("gray80", "gray28")
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
        accent = ("#007AFF", "#0A84FF")
        accent_hover = ("#0062cc", "#0071e3")
        normal_hover = GLASS["bg_hover"] if HAS_THEME else ("gray80", "gray28")
        normal_text = GLASS["text_primary"] if HAS_THEME else ("gray15", "gray90")

        for key, item in self.buttons.items():
            btn = item["widget"]
            if key == active_key:
                btn.configure(
                    fg_color=accent,
                    hover_color=accent_hover,
                    text_color="#FFFFFF"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    hover_color=normal_hover,
                    text_color=normal_text
                )

    def toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed
        if self.is_collapsed:
            self.configure(width=self.COLLAPSED_WIDTH)
            self.toggle_btn.configure(text="☰")
            for item in self.buttons.values():
                btn = item["widget"]
                tool = item["tool"]
                btn.configure(text=tool["icon"], anchor="center")
        else:
            self.configure(width=self.EXPANDED_WIDTH)
            self.toggle_btn.configure(text="◂  Collapse")
            for item in self.buttons.values():
                btn = item["widget"]
                tool = item["tool"]
                btn.configure(text=f"  {tool['icon']}   {tool['short']}", anchor="w")


# Aliases for compatibility
RightSidebarToolbar = LeftSidebarToolbar
SidebarToolbar = LeftSidebarToolbar
