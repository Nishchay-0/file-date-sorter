"""
Windows Explorer Right-Click Context Menu Integration Module
Manages Registry keys under HKCU for "Organize with Smart File Organizer".
"""

import sys
import os

HAS_WINREG = False
if sys.platform == "win32":
    try:
        import winreg
        HAS_WINREG = True
    except ImportError:
        HAS_WINREG = False


REG_KEY_NAME = "SmartFileOrganizer"
MENU_LABEL = "📁 Organize with Smart File Organizer"


def get_python_exe_command():
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
        return f'"{exe_path}" "%1"'
    else:
        python_exe = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        return f'"{python_exe}" "{script_path}" "%1"'


def install_context_menu():
    if not HAS_WINREG:
        return False, "Registry manipulation is only supported on Windows."

    try:
        cmd_str = get_python_exe_command()

        # 1. Directory Context Menu (Right-click on a folder background or item)
        dir_key_path = fr"Software\Classes\Directory\shell\{REG_KEY_NAME}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, dir_key_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, MENU_LABEL)
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, sys.executable)
            with winreg.CreateKey(key, "command") as cmd_key:
                winreg.SetValue(cmd_key, "", winreg.REG_SZ, cmd_str)

        # 2. Directory Background Context Menu (Right-click inside empty folder space)
        bg_key_path = fr"Software\Classes\Directory\Background\shell\{REG_KEY_NAME}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, bg_key_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, MENU_LABEL)
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, sys.executable)
            with winreg.CreateKey(key, "command") as cmd_key:
                winreg.SetValue(cmd_key, "", winreg.REG_SZ, f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}" "%V"' if not getattr(sys, 'frozen', False) else f'"{sys.executable}" "%V"')

        return True, "Successfully added 'Organize with Smart File Organizer' to Windows Explorer Right-Click Menu!"

    except Exception as e:
        return False, f"Failed to modify Windows Registry: {str(e)}"


def uninstall_context_menu():
    if not HAS_WINREG:
        return False, "Registry manipulation is only supported on Windows."

    removed = 0
    errors = []

    for base_path in [
        fr"Software\Classes\Directory\shell\{REG_KEY_NAME}",
        fr"Software\Classes\Directory\Background\shell\{REG_KEY_NAME}"
    ]:
        try:
            # Delete command subkey first, then main key
            cmd_path = fr"{base_path}\command"
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, cmd_path)
            except OSError:
                pass
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, base_path)
            removed += 1
        except OSError:
            pass
        except Exception as e:
            errors.append(str(e))

    if removed > 0:
        return True, "Successfully removed right-click context menu shortcuts from Windows Explorer."
    else:
        return False, "Context menu entries were not found in Windows Registry."


def check_context_menu_status():
    if not HAS_WINREG:
        return False

    try:
        dir_key_path = fr"Software\Classes\Directory\shell\{REG_KEY_NAME}"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, dir_key_path) as key:
            return True
    except OSError:
        return False
