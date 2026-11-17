# 📱 Smart File Organizer Pro — Flutter Cross-Platform

Cross-platform mobile and desktop port of **Smart File Organizer Suite Pro** built with Flutter & Dart.

Supports:
- **Android** (API 26+, Scoped Storage + SAF support)
- **Windows** (Native C++ desktop embedder)
- **macOS** (Cocoa desktop embedder)
- **Linux** (GTK desktop embedder)

---

## 🚀 Running on Android

### 1. Prerequisites
- [Flutter SDK](https://docs.flutter.dev/get-started/install) (>= 3.0.0)
- Android Studio or Android SDK with platform-tools (`adb`)
- Android device with USB Debugging enabled OR Android Emulator

### 2. Launch
```bash
cd flutter_app

# Fetch dependencies
flutter pub get

# Check connected Android devices
flutter devices

# Run on Android
flutter run
```

### 3. Build Release APK (Google Play / Sideload)
```bash
flutter build apk --release
# Output APK: build/app/outputs/flutter-apk/app-release.apk
```

---

## 💻 Running on Windows Desktop

```bash
cd flutter_app
flutter run -d windows
```

### Build Windows Standalone Executable
```bash
flutter build windows --release
# Output: build/windows/x64/runner/Release/
```

---

## 🍏 Running on macOS Desktop

```bash
cd flutter_app
flutter run -d macos
```

### Build macOS App Bundle (.app)
```bash
flutter build macos --release
```

---

## 🛡️ Architecture & Engine Modules

- **`lib/constants/file_categories.dart`**: Complete categories & stopword dictionary ported from `config.py`.
- **`lib/core/smart_name_sorter.dart`**: Natural sort & deterministic token extractor ported from `sorter_core.py`.
- **`lib/core/hashing_service.dart`**: SHA-256 tiered hashing, fast head/tail sampling, Levenshtein fuzzy similarity.
- **`lib/core/system_vault.dart`**: Pre-move atomic ZIP archive generator and `.undo_manifest.json` 1-click restore.
- **`lib/core/sorter_engine.dart`**: Date (`YYYY/MM`), Category, Smart Name, Size, and Extension organization engine.
- **`lib/ui/theme.dart`**: Apple-inspired Glassmorphism design system tokens with real blur `BackdropFilter`.
- **`lib/main.dart`**: Responsive adaptive interface with collapsible sidebar navigation and real-time dry-run preview.
