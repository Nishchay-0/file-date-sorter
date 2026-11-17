"""
Build Script for Smart File Organizer Suite
Converts the CustomTkinter GUI into a standalone Windows .exe using PyInstaller.
"""

import subprocess
import sys
import os

try:
    from version import APP_NAME, VERSION
except ImportError:
    APP_NAME = "Smart File Organizer Suite"
    VERSION = "1.0.0"

def sign_executable(exe_path, cert_pfx_path=None, cert_password=None):
    """
    Code-signing placeholder hook.
    
    To eliminate Windows SmartScreen "unrecognized publisher" warnings on user machines,
    acquire an EV/OV Code Signing Certificate (.pfx) and invoke signtool:
    
      signtool sign /f <cert.pfx> /p <password> /tr http://timestamp.digicert.com /td sha256 <exe_path>
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
        print("[i] Code signing skipped (no certificate provided). To enable, pass cert_pfx_path to sign_executable().")

def build_executable():
    print("==========================================================")
    print(f"   BUILDING STANDALONE WINDOWS EXECUTABLE: {APP_NAME} v{VERSION}")
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
    add_data_ctk = f"{ctk_path}{os.path.pathsep}customtkinter"
    
    icon_path = os.path.abspath(os.path.join("assets", "icon.ico"))
    assets_data = f"{os.path.abspath('assets')}{os.path.pathsep}assets"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=SmartFileOrganizer",
        f"--icon={icon_path}",
        f"--add-data={add_data_ctk}",
        f"--add-data={assets_data}",
        "--collect-all=gui_modules",
        "--hidden-import=gui_modules",
        "--hidden-import=sorter_core",
        "--hidden-import=version",
        "--hidden-import=PIL",
        "--hidden-import=cv2",
        "gui.py"
    ]

    print(f"[+] Executing command: {' '.join(cmd)}")
    ret = subprocess.call(cmd)
    
    if ret == 0:
        exe_output = os.path.abspath("dist/SmartFileOrganizer/SmartFileOrganizer.exe")
        print("\n==========================================================")
        print("[SUCCESS] BUILD SUCCESSFUL!")
        print(f"Standalone application folder created in: {os.path.abspath('dist/SmartFileOrganizer')}")
        print(f"Executable: {exe_output}")
        print("==========================================================")

        # Trigger code-signing hook (no-op unless certificate path is supplied)
        cert_path = os.environ.get("CODE_SIGNING_CERT_PATH")
        cert_pass = os.environ.get("CODE_SIGNING_CERT_PASS")
        sign_executable(exe_output, cert_pfx_path=cert_path, cert_password=cert_pass)
    else:
        print("\n[!] Build failed with return code:", ret)

if __name__ == "__main__":
    build_executable()
