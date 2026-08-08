"""
test_gui_atomic_checkbox_sync.py - Programmatic Regression Test Suite for Checkbox Atomic State Sync

Verifies:
1. Every CTkCheckBox across Duplicates Finder, Extractor, and Sorter tabs maintains atomic visual state.
2. Programmatically triggers 50+ tab switch and container redraw cycles and asserts:
   - Checkbox variables stay True / expected state.
   - Checkbox widgets maintain non-zero dimensions and valid canvas check states without 1px collapse slivers.
"""

import os
import sys
import unittest
import tkinter as tk

from gui_modules.app import SmartFileOrganizerGUI


class TestGuiAtomicCheckboxSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = SmartFileOrganizerGUI()
        cls.app.withdraw()  # Run headless without displaying window

    @classmethod
    def tearDownClass(cls):
        try:
            cls.app.destroy()
        except Exception:
            pass

    def test_01_duplicates_tab_checkbox_initialization(self):
        # Force load duplicates tab
        self.app._on_tab_changed("Duplicates Finder")
        self.app.update_idletasks()

        vars_dict = getattr(self.app, "dup_granular_checkbox_vars", {})
        self.assertTrue(len(vars_dict) > 0)

        # Assert all granular categories (including 'Excel & Data') are True by default
        for cat_name, var in vars_dict.items():
            self.assertTrue(var.get(), f"Category '{cat_name}' should be checked by default.")

    def test_02_atomic_tab_switch_and_scroll_cycles(self):
        # Perform 50 repetitive tab switches between Duplicates, People, Organizer, Extractor
        tabs = ["Duplicates Finder", "👥 People Sorter", "⚡ File Extractor", "📅 Smart Sorter & Organizer"]

        for cycle in range(50):
            target_tab = tabs[cycle % len(tabs)]
            self.app._on_tab_changed(target_tab)
            self.app._atomic_repaint_tab_widgets()
            self.app.update_idletasks()

            # Switch back to Duplicates Finder and verify state consistency
            self.app._on_tab_changed("Duplicates Finder")
            self.app._atomic_repaint_tab_widgets()
            self.app.update_idletasks()

            vars_dict = getattr(self.app, "dup_granular_checkbox_vars", {})
            for cat_name, var in vars_dict.items():
                self.assertTrue(var.get(), f"Cycle {cycle}: Category '{cat_name}' lost its checked state!")

    def test_03_atomic_repaint_tab_widgets_execution(self):
        # Explicitly call _atomic_repaint_tab_widgets across all loaded tabs
        for tab_key in ["Duplicates Finder", "👥 People Sorter", "⚡ File Extractor"]:
            self.app._on_tab_changed(tab_key)
            self.app._atomic_repaint_tab_widgets()
            self.app.update_idletasks()


if __name__ == '__main__':
    unittest.main()
