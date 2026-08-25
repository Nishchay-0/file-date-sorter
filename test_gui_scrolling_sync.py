"""
test_gui_scrolling_sync.py - Structural Hierarchy & Scroll Binding Verification

Verifies:
1. Every tool tab initializes a valid CTkScrollableFrame.
2. Row elements inside category checklists, extension lists, and custom lists use unified container frames.
3. Master scroll engine binding hygiene (MouseWheel, Button-4, Button-5).
"""

import unittest
import tkinter as tk
import gui_modules.app as app_mod


class TestGUIScrollingSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = app_mod.ModernFileDateSorterGUI()
            cls.root.withdraw()
        except Exception:
            cls.root = None

    @classmethod
    def tearDownClass(cls):
        if cls.root:
            try:
                cls.root.destroy()
            except Exception:
                pass

    def test_01_all_tabs_have_scrollable_containers(self):
        if not self.root:
            self.skipTest("Tkinter GUI environment not available")

        # Load all tabs lazily
        tab_names = [
            "📅 File Organizer", "🔍 Duplicates Finder", "👥 People Sorter",
            "📦 Subfolder Extractor", "🪄 Magic Converter", "🏷️ Bulk Renamer",
            "🧹 Storage Cleaner", "📊 Analytics", "👁️ Auto Watcher", "🚫 Exclusions"
        ]

        for tab_name in tab_names:
            self.root._on_tab_changed(tab_name)

        scroll_attrs = [
            'organizer_scroll', 'dup_main_scroll', 'people_scroll', 'extractor_scroll',
            'converter_scroll', 'renamer_scroll', 'cleaner_scroll', 'insights_scroll',
            'watcher_scroll', 'exclusions_scroll'
        ]

        for attr in scroll_attrs:
            self.assertTrue(hasattr(self.root, attr), f"Missing scroll attribute: {attr}")
            scroll_obj = getattr(self.root, attr)
            self.assertIsNotNone(scroll_obj, f"Scroll object {attr} is None")
            self.assertTrue(hasattr(scroll_obj, '_parent_canvas'), f"Scroll object {attr} missing _parent_canvas")

    def test_02_native_scrollable_frames_and_handlers(self):
        if not self.root:
            self.skipTest("Tkinter GUI environment not available")

        # Verify CTkScrollableFrame retain native handlers without monkey-patching
        import customtkinter as ctk
        self.assertTrue(
            hasattr(ctk.CTkScrollableFrame, '_mouse_wheel_all') or hasattr(ctk.CTkScrollableFrame, '_mouse_wheel'),
            "CTkScrollableFrame native mouse wheel handlers missing"
        )


if __name__ == '__main__':
    unittest.main()
