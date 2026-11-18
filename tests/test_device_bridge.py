"""
tests/test_device_bridge.py — Unit Tests for Phone & USB Device Bridge
Smart File Organizer Suite Pro
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from device_bridge import AdbBridge, DeviceInfo, DeviceType, MtpBridge, UnifiedDeviceManager


class TestDeviceBridge(unittest.TestCase):
    def test_01_device_info_dataclass(self):
        dev = DeviceInfo(
            id="emulator-5554",
            name="Android SDK Emulator",
            type=DeviceType.ADB,
            status="device",
            storage_folders=["/sdcard/DCIM"],
            details={"model": "sdk_gphone64_x86_64"},
        )
        d = dev.to_dict()
        self.assertEqual(d["id"], "emulator-5554")
        self.assertEqual(d["type"], "adb")
        self.assertEqual(d["name"], "Android SDK Emulator")
        self.assertIn("/sdcard/DCIM", d["storage_folders"])

    def test_02_find_adb_binary(self):
        bridge = AdbBridge()
        adb_path = bridge.get_adb_path()
        if adb_path:
            self.assertTrue(os.path.exists(adb_path))
            self.assertTrue(bridge.is_available())

    @patch("subprocess.run")
    def test_03_adb_device_parsing(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                "List of devices attached\n"
                "192.168.1.100:5555     device product:panther model:Pixel_7 device:panther transport_id:1\n"
                "1234567890             unauthorized\n"
            ),
        )

        bridge = AdbBridge(adb_path="mock_adb")
        bridge.is_available = MagicMock(return_value=True)

        devices = bridge.list_devices()
        self.assertEqual(len(devices), 2)

        # Device 1: Online Pixel 7
        self.assertEqual(devices[0].id, "192.168.1.100:5555")
        self.assertIn("Pixel 7", devices[0].name)
        self.assertEqual(devices[0].status, "device")
        self.assertEqual(devices[0].type, DeviceType.ADB)

        # Device 2: Unauthorized
        self.assertEqual(devices[1].id, "1234567890")
        self.assertIn("Allow USB Debugging", devices[1].name)
        self.assertEqual(devices[1].status, "unauthorized")

    @patch("subprocess.run")
    def test_04_adb_list_remote_files(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                "/sdcard/DCIM/Camera/IMG_20240518_120000.jpg\n"
                "/sdcard/DCIM/Camera/VID_20240518_120100.mp4\n"
                "/sdcard/DCIM/Camera/notes.txt\n"
            ),
        )

        bridge = AdbBridge(adb_path="mock_adb")
        bridge.is_available = MagicMock(return_value=True)

        # Filter image/video extensions only
        files = bridge.list_remote_files(
            "mock_serial", "/sdcard/DCIM/Camera", extensions=[".jpg", ".mp4"]
        )
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0]["name"], "IMG_20240518_120000.jpg")
        self.assertEqual(files[1]["name"], "VID_20240518_120100.mp4")

    @patch("subprocess.run")
    def test_05_adb_organize_dry_run(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                "/sdcard/DCIM/Camera/IMG_20240518_120000.jpg\n"
                "/sdcard/DCIM/Camera/IMG_20231125_091530.jpg\n"
                "/sdcard/DCIM/Camera/random_meme.png\n"
            ),
        )

        mgr = UnifiedDeviceManager(adb_path="mock_adb")
        mgr.adb.is_available = MagicMock(return_value=True)

        res = mgr.organize_phone_folder_adb("mock_serial", "/sdcard/DCIM/Camera", dry_run=True)
        self.assertEqual(res["total_files"], 3)
        self.assertTrue(res["dry_run"])
        self.assertEqual(res["moved_count"], 0)  # dry run does not move

        plan = res["plan"]
        self.assertEqual(plan[0]["subfolder"], "2024/2024-05")
        self.assertEqual(plan[1]["subfolder"], "2023/2023-11")
        self.assertEqual(plan[2]["subfolder"], "Other")

    def test_06_mtp_bridge_availability(self):
        mtp = MtpBridge()
        self.assertTrue(mtp.is_available())

    def test_07_unified_manager_empty_scan(self):
        mgr = UnifiedDeviceManager()
        # Scan should execute without crashing and return a list
        devs = mgr.scan_all_devices()
        self.assertIsInstance(devs, list)


if __name__ == "__main__":
    unittest.main()
