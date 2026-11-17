import os
import sys
import tempfile
import pytest

# Ensure safe isolated Vault directory for all test runs
_test_vault_dir = os.path.join(tempfile.gettempdir(), "test_sfo_vault")
os.makedirs(_test_vault_dir, exist_ok=True)
os.environ["SMART_FILE_ORGANIZER_VAULT_DIR"] = _test_vault_dir

# Defend against Windows DwmSetWindowAttribute handle issues on Tkinter headless test runs
try:
    import customtkinter.windows.ctk_tk as ctk_tk_mod
    def _safe_windows_set_titlebar_color(self, color_mode):
        # No-op titlebar chrome in test environment to prevent 0xc0000008 Windows handle fault
        pass
    ctk_tk_mod.CTk._windows_set_titlebar_color = _safe_windows_set_titlebar_color
except Exception:
    pass
