import 'dart:convert';
import 'dart:io';
import 'package:archive/archive_io.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

/// Atomic Safety Vault & 1-Click Restore
/// Direct Dart port of sorter_core.py System Vault & Undo Engine
class SystemVault {
  static const String manifestFile = '.undo_manifest.json';

  /// Returns the persistent System Vault directory (platform-aware)
  static Future<Directory> getVaultDir([String subfolder = '']) async {
    Directory base;
    if (Platform.isAndroid) {
      base = (await getExternalStorageDirectory()) ?? (await getApplicationDocumentsDirectory());
    } else {
      base = await getApplicationSupportDirectory();
    }
    final target = Directory(p.join(base.path, 'SmartFileOrganizer', 'Vault', subfolder));
    if (!await target.exists()) {
      await target.create(recursive: true);
    }
    return target;
  }

  /// Creates an atomic Zip archive of all files scheduled for mutation
  static Future<String?> createBackupArchive(List<File> files, String sourceDirPath) async {
    if (files.isEmpty) return null;

    final backupsDir = await getVaultDir('Backups');
    final timestamp = DateTime.now().toIso8601String().replaceAll(':', '-').replaceAll('.', '-');
    final zipPath = p.join(backupsDir.path, 'vault_backup_$timestamp.zip');

    final encoder = ZipFileEncoder();
    encoder.create(zipPath);

    for (final file in files) {
      if (await file.exists()) {
        final relPath = p.relative(file.path, from: sourceDirPath);
        encoder.addFile(file, relPath);
      }
    }
    encoder.close();
    return zipPath;
  }

  /// Saves the execution manifest for 1-click undo
  static Future<File> saveUndoManifest({
    required String directoryPath,
    required List<Map<String, String>> operations,
    String? backupZipPath,
  }) async {
    final manifestData = {
      'timestamp': DateTime.now().toIso8601String(),
      'directory': directoryPath,
      'backup_zip': backupZipPath,
      'operations': operations, // list of {'src': ..., 'dest': ...}
    };

    final manifestJson = const JsonEncoder.withIndent('  ').convert(manifestData);

    // Save locally in directory root
    final localManifest = File(p.join(directoryPath, manifestFile));
    await localManifest.writeAsString(manifestJson);

    // Save copy in global Vault manifests
    final manifestsDir = await getVaultDir('Manifests');
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final globalManifest = File(p.join(manifestsDir.path, 'manifest_$timestamp.json'));
    await globalManifest.writeAsString(manifestJson);

    return localManifest;
  }

  /// Reverts the last operation using the local manifest file
  static Future<int> undoLastOperation(String directoryPath) async {
    final manifest = File(p.join(directoryPath, manifestFile));
    if (!await manifest.exists()) {
      throw Exception('No undo manifest found in: $directoryPath');
    }

    final content = await manifest.readAsString();
    final data = jsonDecode(content) as Map<String, dynamic>;
    final ops = (data['operations'] as List).cast<Map<String, dynamic>>();

    int restoredCount = 0;
    // Reverse operations
    for (final op in ops.reversed) {
      final currentPath = op['dest'] as String;
      final originalPath = op['src'] as String;

      final currentFile = File(currentPath);
      if (await currentFile.exists()) {
        final origDir = Directory(p.dirname(originalPath));
        if (!await origDir.exists()) {
          await origDir.create(recursive: true);
        }
        await currentFile.rename(originalPath);
        restoredCount++;
      }
    }

    // Delete manifest after complete restoration
    await manifest.delete();
    return restoredCount;
  }
}
