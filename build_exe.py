"""
Build Script for Smart File Organizer & Sorter
Converts the CustomTkinter GUI into a standalone Windows .exe using PyInstaller.
"""

import subprocess
import sys
import os

def build_executable():
    print("==========================================================")
    print("   BUILDING STANDALONE WINDOWS EXECUTABLE (.EXE)")
    print("==========================================================")

    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("[!] PyInstaller is not installed. Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Determine customtkinter package path for data inclusion
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    add_data_flag = f"{ctk_path}{os.path.pathsep}customtkinter"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=SmartFileOrganizer",
        f"--add-data={add_data_flag}",
        "--collect-all=gui_modules",
        "--hidden-import=gui_modules",
        "--hidden-import=sorter_core",
        "--hidden-import=PIL",
        "--hidden-import=cv2",
        "gui.py"
    ]

    print(f"[+] Executing command: {' '.join(cmd)}")
    ret = subprocess.call(cmd)
    
    if ret == 0:
        print("\n==========================================================")
        print("🎉 BUILD SUCCESSFUL!")
        print(f"Standalone application folder created in: {os.path.abspath('dist/SmartFileOrganizer')}")
        print("Executable: dist/SmartFileOrganizer/SmartFileOrganizer.exe")
        print("==========================================================")
    else:
        print("\n[!] Build failed with return code:", ret)

if __name__ == "__main__":
    build_executable()
