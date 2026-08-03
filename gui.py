"""
Smart File Organizer Suite Pro - Lightweight Facade Entry Point
Refactored into modular package structure under `gui_modules/`.
"""

import sys
from gui_modules import ModernFileDateSorterGUI, SmartFileOrganizerGUI, main

__all__ = ["ModernFileDateSorterGUI", "SmartFileOrganizerGUI", "main"]

if __name__ == "__main__":
    main()
