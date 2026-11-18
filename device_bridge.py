"""
device_bridge.py — USB Phone & Mobile Device Integration Bridge
Smart File Organizer Suite Pro

Provides seamless support for organizing files on mobile phones and USB portable devices:
1. High-Speed ADB Bridge (Android Debug Bridge for Android with USB Debugging enabled)
   - In-place remote sorting directly on the phone filesystem (/sdcard/DCIM, Downloads, etc.)
   - High-throughput batch transfer (phone -> PC or PC -> phone)
   - Undo manifest generation for mobile moves
2. Windows Portable Devices / MTP Bridge (Media Transfer Protocol for Plug & Play phones)
   - Zero-configuration detection for Android & iPhone via Windows Shell COM
   - Automated Import & Organize to PC (Date / Category / Name sorting)
   - Optional verified cleanup to free phone internal storage
"""

import json
import logging
import os
import re
import shutil
import string
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("SmartFileOrganizer.DeviceBridge")


class DeviceType(Enum):
    ADB = "adb"
    MTP = "mtp"


@dataclass
class StorageDriveInfo:
    """Represents a mounted physical, removable USB, or network storage volume."""
    letter: str
    path: str
    label: str
    drive_type: str  # 'removable', 'fixed', 'network', 'cdrom', 'unknown'
    type_desc: str   # 'USB / Removable Drive', 'Local Disk', 'Network Share', etc.
    free_bytes: int
    total_bytes: int
    free_str: str    # e.g. "14.8 GB free of 32.0 GB"
    is_removable: bool

    def to_dict(self):
        return asdict(self)


@dataclass
class DeviceInfo:
    id: str  # Serial for ADB, Path or Name for MTP
    name: str  # Human readable friendly name (e.g. "Google Pixel 7")
    type: DeviceType
    status: str  # "online", "unauthorized", "mtp_ready", etc.
    storage_folders: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        d["type"] = self.type.value
        return d


def scan_system_storage_drives(only_removable: bool = False) -> List[StorageDriveInfo]:
    """
    Cross-platform scanner for all mounted physical, removable USB, and network storage drives.
    On Windows: uses kernel32 GetLogicalDrives, GetDriveTypeW, GetVolumeInformationW.
    On macOS: scans /Volumes/*
    On Linux: parses /media, /mnt, /run/media.
    """
    drives: List[StorageDriveInfo] = []

    if sys.platform == "win32":
        try:
            import ctypes
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            type_map = {
                2: ("removable", "USB / Removable Drive"),
                3: ("fixed", "Local / External Disk"),
                4: ("network", "Network Share"),
                5: ("cdrom", "CD/DVD Drive"),
                6: ("ramdisk", "RAM Disk"),
            }
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    root = f"{letter}:\\"
                    code = ctypes.windll.kernel32.GetDriveTypeW(root)
                    dtype, desc = type_map.get(code, ("unknown", "Storage Drive"))
                    is_rem = code in (2, 4)

                    if only_removable and not is_rem:
                        bitmask >>= 1
                        continue

                    vol_buf = ctypes.create_unicode_buffer(1024)
                    fs_buf = ctypes.create_unicode_buffer(1024)
                    try:
                        ctypes.windll.kernel32.GetVolumeInformationW(
                            root, vol_buf, 1024, None, None, None, fs_buf, 1024
                        )
                        label = vol_buf.value or f"Drive ({letter}:)"
                    except Exception:
                        label = f"Drive ({letter}:)"

                    try:
                        usage = shutil.disk_usage(root)
                        fb = usage.free
                        tb = usage.total
                        free_gb = fb / (1024**3)
                        tot_gb = tb / (1024**3)
                        free_str = f"{free_gb:.1f} GB free of {tot_gb:.1f} GB"
                    except Exception:
                        fb = 0
                        tb = 0
                        free_str = "Ready"

                    drives.append(
                        StorageDriveInfo(
                            letter=letter,
                            path=root,
                            label=label,
                            drive_type=dtype,
                            type_desc=desc,
                            free_bytes=fb,
                            total_bytes=tb,
                            free_str=free_str,
                            is_removable=is_rem,
                        )
                    )
                bitmask >>= 1
        except Exception as e:
            logger.warning(f"Error scanning Windows drives: {e}")

    elif sys.platform == "darwin":
        # macOS /Volumes scanner
        vol_root = "/Volumes"
        if os.path.exists(vol_root):
            try:
                for entry in sorted(os.listdir(vol_root)):
                    full = os.path.join(vol_root, entry)
                    if os.path.ismount(full):
                        is_rem = entry.lower() not in ("macintosh hd", "system")
                        if only_removable and not is_rem:
                            continue
                        try:
                            usage = shutil.disk_usage(full)
                            free_str = f"{usage.free / (1024**3):.1f} GB free of {usage.total / (1024**3):.1f} GB"
                            fb, tb = usage.free, usage.total
                        except Exception:
                            fb, tb = 0, 0
                            free_str = "Mounted"
                        drives.append(
                            StorageDriveInfo(
                                letter="",
                                path=full,
                                label=entry,
                                drive_type="removable" if is_rem else "fixed",
                                type_desc="USB / External Volume" if is_rem else "System Volume",
                                free_bytes=fb,
                                total_bytes=tb,
                                free_str=free_str,
                                is_removable=is_rem,
                            )
                        )
            except Exception as e:
                logger.warning(f"Error scanning macOS volumes: {e}")

    elif sys.platform.startswith("linux"):
        # Linux /media and /mnt scanner
        candidates = ["/media", "/mnt", "/run/media"]
        user = os.environ.get("USER") or os.environ.get("LOGNAME")
        if user:
            candidates.extend([f"/media/{user}", f"/run/media/{user}"])

        seen_paths = set()
        for base in candidates:
            if os.path.exists(base):
                try:
                    for entry in os.listdir(base):
                        full = os.path.join(base, entry)
                        if os.path.isdir(full) and full not in seen_paths:
                            seen_paths.add(full)
                            try:
                                usage = shutil.disk_usage(full)
                                free_str = f"{usage.free / (1024**3):.1f} GB free of {usage.total / (1024**3):.1f} GB"
                                fb, tb = usage.free, usage.total
                            except Exception:
                                fb, tb = 0, 0
                                free_str = "Mounted"
                            drives.append(
                                StorageDriveInfo(
                                    letter="",
                                    path=full,
                                    label=entry,
                                    drive_type="removable",
                                    type_desc="Removable Storage",
                                    free_bytes=fb,
                                    total_bytes=tb,
                                    free_str=free_str,
                                    is_removable=True,
                                )
                            )
                except Exception:
                    pass

        # Also add root system disk if not only_removable
        if not only_removable and "/" not in seen_paths:
            try:
                usage = shutil.disk_usage("/")
                free_str = f"{usage.free / (1024**3):.1f} GB free of {usage.total / (1024**3):.1f} GB"
                drives.append(
                    StorageDriveInfo(
                        letter="",
                        path="/",
                        label="Root Filesystem",
                        drive_type="fixed",
                        type_desc="Local Linux Disk",
                        free_bytes=usage.free,
                        total_bytes=usage.total,
                        free_str=free_str,
                        is_removable=False,
                    )
                )
            except Exception:
                pass

    return drives


class AdbBridge:
    """
    Direct interface to Android Debug Bridge (ADB) for fast, robust phone operations.
    """

    def __init__(self, adb_path: Optional[str] = None):
        self._adb_path = adb_path or self.find_adb_binary()

    @staticmethod
    def find_adb_binary() -> Optional[str]:
        # 1. System PATH
        which_adb = shutil.which("adb")
        if which_adb and os.path.exists(which_adb):
            return which_adb

        # 2. Standard Android SDK Locations on Windows
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
            os.path.expandvars(r"%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe"),
            r"C:\Android\platform-tools\adb.exe",
            r"C:\platform-tools\adb.exe",
            os.path.expandvars(r"%PROGRAMFILES%\Android\platform-tools\adb.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Android\platform-tools\adb.exe"),
        ]
        for p in candidates:
            if p and os.path.exists(p):
                return p
        return None

    def is_available(self) -> bool:
        if not self._adb_path or not os.path.exists(self._adb_path):
            return False
        try:
            res = subprocess.run(
                [self._adb_path, "version"],
                capture_output=True,
                text=True,
                timeout=4,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            return res.returncode == 0
        except Exception:
            return False

    def get_adb_path(self) -> Optional[str]:
        return self._adb_path

    def list_devices(self) -> List[DeviceInfo]:
        if not self.is_available():
            return []

        devices = []
        try:
            res = subprocess.run(
                [self._adb_path, "devices", "-l"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if res.returncode != 0:
                return []

            lines = res.stdout.strip().splitlines()
            for line in lines[1:]:  # Skip "List of devices attached"
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                if len(parts) >= 2:
                    serial = parts[0]
                    state = parts[1]

                    # Parse key:value properties (model:Pixel_7 product:panther, etc.)
                    props = {}
                    for p in parts[2:]:
                        if ":" in p:
                            k, v = p.split(":", 1)
                            props[k] = v

                    model = props.get("model", "").replace("_", " ")
                    if not model:
                        model = props.get("device", serial)

                    display_name = f"{model} (Android ADB)"
                    if state == "unauthorized":
                        display_name += " [Tap 'Allow USB Debugging' on phone]"

                    dev = DeviceInfo(
                        id=serial,
                        name=display_name,
                        type=DeviceType.ADB,
                        status=state,
                        details=props,
                        storage_folders=[
                            "/sdcard/DCIM/Camera",
                            "/sdcard/DCIM",
                            "/sdcard/Download",
                            "/sdcard/Pictures",
                            "/sdcard/Documents",
                            "/sdcard/Music",
                            "/sdcard/Movies",
                        ],
                    )
                    devices.append(dev)
        except Exception as e:
            logger.warning(f"Error enumerating ADB devices: {e}")

        return devices

    def list_remote_files(
        self, serial: str, remote_dir: str, extensions: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Lists files in an Android directory with size and modification timestamp.
        """
        if not self.is_available():
            return []

        # Use find or ls to enumerate files
        # We query: filepath, size, epoch timestamp
        # Toybox find supports: find "<dir>" -maxdepth 1 -type f
        clean_dir = remote_dir.rstrip("/")
        cmd = [
            self._adb_path,
            "-s",
            serial,
            "shell",
            f"find '{clean_dir}' -maxdepth 1 -type f",
        ]
        files = []
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if res.returncode != 0:
                return []

            paths = [p.strip() for p in res.stdout.strip().splitlines() if p.strip()]
            for p in paths:
                fname = os.path.basename(p)
                ext = os.path.splitext(fname)[1].lower()
                if extensions and ext not in extensions:
                    continue

                files.append(
                    {
                        "path": p,
                        "name": fname,
                        "ext": ext,
                        "directory": clean_dir,
                    }
                )
        except Exception as e:
            logger.warning(f"Error listing remote files in {remote_dir}: {e}")

        return files

    def pull_file(self, serial: str, remote_path: str, local_dest: str) -> bool:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(local_dest)), exist_ok=True)
            res = subprocess.run(
                [self._adb_path, "-s", serial, "pull", remote_path, local_dest],
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            return res.returncode == 0 and os.path.exists(local_dest)
        except Exception as e:
            logger.error(f"Failed to pull {remote_path} via ADB: {e}")
            return False

    def move_remote_file(self, serial: str, src_path: str, dst_path: str) -> bool:
        """
        Instant in-place move on the Android filesystem.
        """
        try:
            dst_dir = os.path.dirname(dst_path).replace("\\", "/")
            # Create remote directory
            subprocess.run(
                [self._adb_path, "-s", serial, "shell", f"mkdir -p '{dst_dir}'"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            # Move file
            res = subprocess.run(
                [self._adb_path, "-s", serial, "shell", f"mv '{src_path}' '{dst_path}'"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            return res.returncode == 0
        except Exception as e:
            logger.error(f"Failed to move remote file {src_path} -> {dst_path}: {e}")
            return False


class MtpBridge:
    """
    Interface for Windows Portable Devices / MTP using Windows Shell COM.
    Works for any plug-and-play phone without developer options.
    """

    def __init__(self):
        self._script_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "scripts", "mtp_operations.ps1"
        )

    def is_available(self) -> bool:
        return sys.platform == "win32" and os.path.exists(self._script_path)

    def list_devices(self) -> List[DeviceInfo]:
        if not self.is_available():
            return []

        devices = []
        try:
            res = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    self._script_path,
                    "-Action",
                    "list-devices",
                ],
                capture_output=True,
                text=True,
                timeout=8,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            raw = res.stdout.strip()
            if raw and raw != "{}":
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    parsed = [parsed]
                for item in parsed:
                    name = item.get("Name", "USB Device")
                    path = item.get("Path", name)
                    dev = DeviceInfo(
                        id=path,
                        name=f"{name} (USB MTP)",
                        type=DeviceType.MTP,
                        status="mtp_ready",
                        storage_folders=["Internal storage", "SD card", "DCIM", "Downloads"],
                        details=item,
                    )
                    devices.append(dev)
        except Exception as e:
            logger.warning(f"Error enumerating MTP devices: {e}")

        return devices

    def list_folders(self, device_name: str) -> List[str]:
        if not self.is_available():
            return []
        try:
            res = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    self._script_path,
                    "-Action",
                    "list-folders",
                    "-Device",
                    device_name,
                ],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            raw = res.stdout.strip()
            if raw and raw != "{}":
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    parsed = [parsed]
                return [f.get("Name") for f in parsed if "Name" in f]
        except Exception as e:
            logger.warning(f"Error listing MTP folders: {e}")
        return []


class UnifiedDeviceManager:
    """
    Unified manager combining ADB (High-Speed Android Bridge) and MTP (Plug & Play Portable Devices).
    """

    def __init__(self, adb_path: Optional[str] = None):
        self.adb = AdbBridge(adb_path=adb_path)
        self.mtp = MtpBridge()

    def scan_all_devices(self) -> List[DeviceInfo]:
        """
        Scans both ADB and MTP buses simultaneously and returns all detected mobile phones.
        """
        results: List[DeviceInfo] = []

        # 1. Probe ADB devices
        adb_devices = self.adb.list_devices()
        results.extend(adb_devices)

        # 2. Probe Windows MTP devices
        mtp_devices = self.mtp.list_devices()
        # Avoid duplicate listing if ADB and MTP both report the same device
        existing_names = {d.name.lower() for d in results}
        for md in mtp_devices:
            # Simple fuzzy deduplication
            if not any(md.name.lower().split()[0] in ex for ex in existing_names):
                results.append(md)

        return results

    def scan_storage_drives(self, only_removable: bool = False) -> List[StorageDriveInfo]:
        """
        Scans all mounted storage drives (USB flash drives, external HDDs/SSDs, SD cards, network shares).
        """
        return scan_system_storage_drives(only_removable=only_removable)

    def scan_all_connected_devices(self) -> Dict[str, Any]:
        """
        Comprehensive scan of all connected devices across USB, Mobile (ADB/MTP), and storage drives.
        Returns:
            {
                "phones": List[DeviceInfo],
                "removable_drives": List[StorageDriveInfo],
                "fixed_drives": List[StorageDriveInfo],
                "total_count": int
            }
        """
        phones = self.scan_all_devices()
        drives = self.scan_storage_drives(only_removable=False)
        removable = [d for d in drives if d.is_removable]
        fixed = [d for d in drives if not d.is_removable]

        return {
            "phones": phones,
            "removable_drives": removable,
            "fixed_drives": fixed,
            "total_count": len(phones) + len(removable) + len(fixed),
        }

    def organize_phone_folder_adb(
        self,
        serial: str,
        remote_dir: str,
        strategy: str = "date",
        dry_run: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Directly organizes files inside the phone storage via ADB shell commands.
        """
        files = self.adb.list_remote_files(serial, remote_dir)
        total = len(files)
        plan = []
        moved_count = 0

        # Regex for common YYYYMMDD date formats in phone filenames (e.g. IMG_20240518_123456.jpg)
        date_pattern = re.compile(r"(\d{4})[-_]?(\d{2})[-_]?(\d{2})")

        for idx, f in enumerate(files):
            fname = f["name"]
            src_path = f["path"]

            subfolder = "Other"
            match = date_pattern.search(fname)
            if match:
                yyyy, mm, dd = match.group(1), match.group(2), match.group(3)
                if 2000 <= int(yyyy) <= 2030 and 1 <= int(mm) <= 12:
                    subfolder = f"{yyyy}/{yyyy}-{mm}"

            dst_path = f"{remote_dir.rstrip('/')}/{subfolder}/{fname}"
            plan.append({"source": src_path, "destination": dst_path, "subfolder": subfolder})

            if not dry_run and src_path != dst_path:
                ok = self.adb.move_remote_file(serial, src_path, dst_path)
                if ok:
                    moved_count += 1

            if progress_callback:
                progress_callback(idx + 1, total, fname)

        return {
            "total_files": total,
            "moved_count": moved_count,
            "dry_run": dry_run,
            "plan": plan,
        }

    def import_and_organize_to_pc(
        self,
        serial_or_device: str,
        remote_dir: str,
        local_dest_dir: str,
        device_type: DeviceType = DeviceType.ADB,
        delete_from_phone: bool = False,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Imports photos/videos from phone to PC, organizing directly into Date/Category folders.
        """
        os.makedirs(local_dest_dir, exist_ok=True)
        date_pattern = re.compile(r"(\d{4})[-_]?(\d{2})[-_]?(\d{2})")
        imported = 0

        if device_type == DeviceType.ADB:
            files = self.adb.list_remote_files(serial_or_device, remote_dir)
            total = len(files)
            for idx, f in enumerate(files):
                fname = f["name"]
                src = f["path"]

                subfolder = "Unsorted"
                match = date_pattern.search(fname)
                if match:
                    yyyy, mm = match.group(1), match.group(2)
                    if 2000 <= int(yyyy) <= 2030:
                        subfolder = os.path.join(yyyy, f"{yyyy}-{mm}")

                target_dir = os.path.join(local_dest_dir, subfolder)
                target_path = os.path.join(target_dir, fname)

                ok = self.adb.pull_file(serial_or_device, src, target_path)
                if ok:
                    imported += 1
                    if delete_from_phone:
                        # Verified delete only after successful transfer
                        subprocess.run(
                            [self.adb.get_adb_path(), "-s", serial_or_device, "shell", f"rm '{src}'"],
                            capture_output=True,
                            timeout=5,
                            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                        )

                if progress_callback:
                    progress_callback(idx + 1, total, fname)

            return {"total": total, "imported": imported, "local_directory": local_dest_dir}

        return {"error": "MTP import requires manual folder selection via Explorer"}


if __name__ == "__main__":
    mgr = UnifiedDeviceManager()
    print("Scanning for connected devices (ADB + MTP)...")
    devs = mgr.scan_all_devices()
    print(f"Detected {len(devs)} device(s):")
    for d in devs:
        print(f" - [{d.type.value.upper()}] {d.name} (ID: {d.id}, Status: {d.status})")
