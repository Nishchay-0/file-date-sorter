"""
Build Script for Smart File Organizer Suite Pro
Converts the CustomTkinter GUI into a standalone Windows .exe using PyInstaller.
Supports building a portable 1-click single-file (.exe) or an unpacked directory.
"""

import argparse
import os
import subprocess
import sys

try:
    from version import APP_NAME, VERSION
except ImportError:
    APP_NAME = "Smart File Organizer Suite"
    VERSION = "1.0.1"


def sign_executable(exe_path, cert_pfx_path=None, cert_password=None):
    """
    Code-signing placeholder hook.
    """
    if cert_pfx_path and os.path.exists(cert_pfx_path):
        print(f"[+] Code Signing Executable: {exe_path}")
        cmd = [
            "signtool", "sign",
            "/f", cert_pfx_path,
            "/p", cert_password or "",
            "/tr", "http://timestamp.digicert.com",
            "/td", "sha256",
            exe_path
        ]
        try:
            subprocess.check_call(cmd)
            print("[✓] Code signing complete!")
        except Exception as e:
            print(f"[!] Code signing failed: {e}")
    else:
        print("[i] Code signing skipped (no certificate provided).")


def build_executable(onefile=True):
    mode_str = "PORTABLE ONE-FILE (.EXE)" if onefile else "UNPACKED DIRECTORY (--onedir)"
    print("=" * 65)
    print(f"   BUILDING {APP_NAME} v{VERSION} [{mode_str}]")
    print("=" * 65)

    icon_path = os.path.abspath(os.path.join("assets", "icon.ico"))
    assets_data = f"{os.path.abspath('assets')}{os.path.pathsep}assets"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile" if onefile else "--onedir",
        "--windowed",
        "--name=SmartFileOrganizer",
        f"--icon={icon_path}",
        f"--add-data={assets_data}",
        "--collect-all=customtkinter",
        "--collect-all=gui_modules",
        "--hidden-import=gui_modules",
        "--hidden-import=sorter_core",
        "--hidden-import=version",
        "--hidden-import=PIL",
        "--hidden-import=cv2",
        "--hidden-import=watchdog",
        "--hidden-import=send2trash",
        "gui.py"
    ]

    print("\n[+] Running PyInstaller compilation command:")
    print(" ".join(cmd))
    print("-" * 65)

    subprocess.check_call(cmd)

    if onefile:
        output_exe = os.path.join("dist", "SmartFileOrganizer.exe")
    else:
        output_exe = os.path.join("dist", "SmartFileOrganizer", "SmartFileOrganizer.exe")

    if os.path.exists(output_exe):
        size_mb = os.path.getsize(output_exe) / (1024 * 1024)
        print("\n" + "=" * 65)
        print(" [✓] BUILD SUCCEEDED!")
        print(f" [✓] Executable: {os.path.abspath(output_exe)}")
        print(f" [✓] File Size:  {size_mb:.2f} MB")
        print(" [✓] Ready to run: Double-click to launch the GUI immediately!")
        print("=" * 65)

        # Optional code signing
        cert_pfx = os.environ.get("CODE_SIGNING_CERT_PFX")
        cert_pass = os.environ.get("CODE_SIGNING_CERT_PASS")
        if cert_pfx:
            sign_executable(output_exe, cert_pfx, cert_pass)
        return output_exe
    else:
        print(f"\n[!] Build completed, but could not verify target executable at: {output_exe}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Smart File Organizer Standalone Executable")
    parser.add_argument("--onedir", action="store_true", help="Build as unpacked directory instead of single-file exe")
    args = parser.parse_args()

    build_executable(onefile=not args.onedir)
