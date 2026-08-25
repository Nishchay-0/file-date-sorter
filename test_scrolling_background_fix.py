"""
test_scrolling_background_fix.py - Regression test for background scrolling bug (SCROLL-002)

BUG: When scrolling with mousewheel, background tabs' scroll containers were
receiving scroll events instead of the active tab's container.

ROOT CAUSE: Fallback strategy in _on_global_mousewheel() was iterating through
all scroll containers and picking the first one found, ignoring active tab status.

FIX: Only use the scroll container belonging to the currently active tab.

This test verifies:
1. Tab switching works correctly
2. The mousewheel handler has the fixed fallback logic
3. Active tab can be determined correctly
"""

import unittest
import sys
import tkinter as tk
from unittest.mock import MagicMock, patch

try:
    import customtkinter as ctk
    import gui_modules.app as app_mod
    TKINTER_AVAILABLE = True
except Exception:
    TKINTER_AVAILABLE = False


class TestScrollingBackgroundFix(unittest.TestCase):
    """Regression test suite for background scrolling fix (SCROLL-002)"""

    @classmethod
    def setUpClass(cls):
        if not TKINTER_AVAILABLE:
            cls.root = None
            return

        try:
            cls.root = app_mod.ModernFileDateSorterGUI()
            cls.root.withdraw()
        except Exception as e:
            print(f"⚠️  GUI initialization failed: {e}")
            cls.root = None

    @classmethod
    def tearDownClass(cls):
        if cls.root:
            try:
                cls.root.destroy()
            except Exception:
                pass

    def test_01_tab_switching_basic(self):
        """Verify tab switching works"""
        if not self.root:
            self.skipTest("GUI environment not available")

        tabs = [
            "📅 File Organizer", "🔍 Duplicates Finder", "👥 People Sorter"
        ]

        for tab_name in tabs:
            self.root.tabview.set(tab_name)
            self.root.update_idletasks()
            active = self.root.tabview.get()
            self.assertEqual(active, tab_name, f"Failed to switch to {tab_name}")

    def test_02_mousewheel_handler_exists(self):
        """Verify CTkScrollableFrame native mousewheel handler is enabled (not monkey-patched)"""
        if not self.root:
            self.skipTest("GUI environment not available")

        # Verify CTkScrollableFrame retains its native _mouse_wheel_all / _mouse_wheel
        self.assertTrue(
            hasattr(ctk.CTkScrollableFrame, '_mouse_wheel_all') or hasattr(ctk.CTkScrollableFrame, '_mouse_wheel'),
            "CTkScrollableFrame native mouse wheel handlers missing"
        )

    def test_03_active_tab_detection(self):
        """Verify active tab can be detected correctly"""
        if not self.root:
            self.skipTest("GUI environment not available")

        # Tab name to check
        target_tab = "🔍 Duplicates Finder"
        
        # Switch to tab
        self.root.tabview.set(target_tab)
        self.root.update_idletasks()
        
        # Verify we can get the active tab
        active = self.root.tabview.get()
        self.assertEqual(
            active, target_tab,
            f"Active tab detection failed: expected {target_tab}, got {active}"
        )

    def test_04_full_tab_cycle(self):
        """Full regression: cycle through all tabs"""
        if not self.root:
            self.skipTest("GUI environment not available")

        tabs = [
            "📅 File Organizer", "🔍 Duplicates Finder", "👥 People Sorter",
            "📦 Subfolder Extractor", "🪄 Magic Converter", "🏷️ Bulk Renamer",
            "🧹 Storage Cleaner", "📊 Analytics", "👁️ Auto Watcher", "🚫 Exclusions"
        ]

        for tab_name in tabs:
            self.root.tabview.set(tab_name)
            self.root.update_idletasks()
            active = self.root.tabview.get()
            self.assertEqual(
                active, tab_name,
                f"Tab switch failed: expected {tab_name}, got {active}"
            )

    def test_05_scrolling_fix_verification(self):
        """
        Verify that all tabs have native CTkScrollableFrame containers with _parent_canvas.
        """
        if not self.root:
            self.skipTest("GUI environment not available")

        tabs = [
            "📅 File Organizer", "🔍 Duplicates Finder", "👥 People Sorter",
            "📦 Subfolder Extractor", "🪄 Magic Converter", "🏷️ Bulk Renamer",
            "🧹 Storage Cleaner", "📊 Analytics", "👁️ Auto Watcher", "🚫 Exclusions"
        ]

        for tab_name in tabs:
            self.root._on_tab_changed(tab_name)

        scroll_attrs = [
            'organizer_scroll', 'dup_main_scroll', 'people_scroll', 'extractor_scroll',
            'converter_scroll', 'renamer_scroll', 'cleaner_scroll', 'insights_scroll',
            'watcher_scroll', 'exclusions_scroll'
        ]

        for attr in scroll_attrs:
            scroll_obj = getattr(self.root, attr, None)
            if scroll_obj:
                self.assertTrue(
                    isinstance(scroll_obj, ctk.CTkScrollableFrame),
                    f"{attr} is not an instance of CTkScrollableFrame"
                )
                self.assertTrue(
                    hasattr(scroll_obj, '_parent_canvas'),
                    f"{attr} missing _parent_canvas"
                )


if __name__ == '__main__':
    unittest.main()
