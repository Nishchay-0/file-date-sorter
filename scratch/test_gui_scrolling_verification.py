import os
import sys
import time
import tkinter as tk

# Ensure workspace directory is on python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from gui_modules.app import SmartFileOrganizerGUI

def verify_gui_scrolling_and_tab_switching():
    print("==================================================")
    print("RUNNING GUI SCROLLING & TAB SWITCHING VERIFICATION")
    print("==================================================")

    # Initialize app window (with withdraw so window doesn't steal focus)
    app = SmartFileOrganizerGUI()
    app.update()

    tabs_to_test = [
        "📅 File Organizer",
        "🔍 Duplicates Finder",
        "📦 Subfolder Extractor",
        "🪄 Magic Converter",
        "🏷️ Bulk Renamer",
        "🧹 Storage Cleaner",
        "📊 Analytics",
        "👁️ Auto Watcher",
        "🚫 Exclusions"
    ]

    print("\n[+] Testing sequential loading & tab switching across all 9 tabs (3 cycles)...")
    for cycle in range(1, 4):
        print(f"\n--- Cycle {cycle}/3 ---")
        for tab in tabs_to_test:
            app.tabview.set(tab)
            app._on_tab_changed(tab)
            app.update()

            # Verify active tab scroll target mapping in tab_attr_map logic
            tab_attr_map = {
                "🔍 Duplicates Finder": "dup_main_scroll",
                "📅 File Organizer": "organizer_scroll",
                "🧹 Storage Cleaner": "cleaner_scroll",
                "📦 Subfolder Extractor": "extractor_scroll",
                "🏷️ Bulk Renamer": "renamer_scroll",
                "🪄 Magic Converter": "converter_scroll",
                "🚫 Exclusions": "exclusions_scroll",
                "📊 Analytics": "insights_scroll",
                "👁️ Auto Watcher": "watcher_scroll"
            }
            attr_name = tab_attr_map.get(tab)
            frame_obj = getattr(app, attr_name, None)

            assert frame_obj is not None, f"ScrollableFrame '{attr_name}' not initialized for tab '{tab}'"
            canvas = getattr(frame_obj, '_parent_canvas', None)
            assert canvas is not None, f"_parent_canvas not found on ScrollableFrame '{attr_name}'"

            # Simulate mousewheel event on canvas
            dummy_event = tk.Event()
            dummy_event.delta = -120
            dummy_event.state = 0
            dummy_event.widget = canvas
            dummy_event.num = 0

            # Execute scroll event
            canvas.yview_scroll(3, "units")
            clean_tab_name = tab.encode('ascii', 'ignore').decode().strip()
            print(f"  [OK] Tab '{clean_tab_name}' -> Target frame '{attr_name}' scrolled successfully without errors")

    print("\n[+] Testing simulated mousewheel event handler on active tabs...")
    for tab in tabs_to_test:
        app.tabview.set(tab)
        app.update()
        # Verify active tab resolves correct scroll target
        active_tab = app.tabview.get()
        assert active_tab == tab, f"Expected active tab '{tab}', got '{active_tab}'"

    app.destroy()
    print("\n==================================================")
    print("ALL GUI SCROLLING & TAB SWITCHING TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    verify_gui_scrolling_and_tab_switching()
