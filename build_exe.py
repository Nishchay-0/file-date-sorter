"""
Build Script for Smart File Organizer Suite Pro
Converts the CustomTkinter GUI into a standalone Windows .exe using PyInstaller.
"""

import subprocess
import sys
import os

try:
    from version import APP_NAME, VERSION
except ImportError:
    APP_NAME = "Smart File Organizer Suite"
    VERSION = "1.0.1"

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

    print("\n[+] Running PyInstaller compilation command:")
    print(" ".join(cmd))
    print("-" * 58)

    subprocess.check_call(cmd)

    output_exe = os.path.join("dist", "SmartFileOrganizer", "SmartFileOrganizer.exe")
    if os.path.exists(output_exe):
        print("\n" + "=" * 58)
        print(" [✓] BUILD SUCCEEDED!")
        print(f" [✓] Executable: {os.path.abspath(output_exe)}")
        print("=" * 58)
        
        # Optional code signing
        cert_pfx = os.environ.get("CODE_SIGNING_CERT_PFX")
        cert_pass = os.environ.get("CODE_SIGNING_CERT_PASS")
        if cert_pfx:
            sign_executable(output_exe, cert_pfx, cert_pass)
    else:
        print("\n[!] Build completed, but could not verify target executable at expected path.")

if __name__ == "__main__":
    build_executable()
