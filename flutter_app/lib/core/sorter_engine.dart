import 'dart:io';
import 'package:intl/intl.dart';
import 'package:path/path.dart' as p;
import '../constants/file_categories.dart';
import 'smart_name_sorter.dart';
import 'system_vault.dart';

enum SortMode { date, category, name, extension, size }

class MoveOperation {
  final String sourcePath;
  final String destinationPath;
  final String category;
  final int fileSizeBytes;

  MoveOperation({
    required this.sourcePath,
    required this.destinationPath,
    required this.category,
    required this.fileSizeBytes,
  });

  Map<String, String> toMap() => {
    'src': sourcePath,
    'dest': destinationPath,
  };
}

class SorterResult {
  final List<MoveOperation> operations;
  final int totalFiles;
  final int totalBytes;
  final bool isDryRun;
  final String? backupZipPath;

  SorterResult({
    required this.operations,
    required this.totalFiles,
    required this.totalBytes,
    required this.isDryRun,
    this.backupZipPath,
  });
}

/// Main Cross-Platform Organizing Engine
/// Direct Dart port of sorter_core.py
class SorterEngine {
  /// Scans directory and computes the exact destination paths
  static Future<List<MoveOperation>> planOrganization({
    required Directory directory,
    required SortMode sortMode,
    bool recursive = false,
    Set<String> excludeFolders = const {'.git', 'node_modules', 'Android', 'Vault'},
  }) async {
    final operations = <MoveOperation>[];
    final entities = directory.listSync(recursive: recursive, followLinks: false);

    for (final entity in entities) {
      if (entity is! File) continue;

      final filename = p.basename(entity.path);
      // Skip system files and manifests
      if (filename == SystemVault.manifestFile || filename.startsWith('.')) continue;

      // Check folder exclusion
      final parentDir = p.basename(p.dirname(entity.path));
      if (excludeFolders.contains(parentDir)) continue;

      final stat = await entity.stat();
      final ext = p.extension(entity.path);
      final category = FileCategories.getCategoryForExtension(ext);

      String subfolder;
      switch (sortMode) {
        case SortMode.date:
          final dt = stat.modified;
          subfolder = DateFormat('yyyy/MM').format(dt);
          break;
        case SortMode.category:
          subfolder = category;
          break;
        case SortMode.name:
          subfolder = SmartNameSorter.extractMeaningfulGroup(filename);
          break;
        case SortMode.extension:
          subfolder = ext.isNotEmpty ? ext.substring(1).toUpperCase() : 'NO_EXT';
          break;
        case SortMode.size:
          final sizeKb = stat.size / 1024;
          if (sizeKb < 1024) {
            subfolder = '< 1 MB';
          } else if (sizeKb < 50 * 1024) {
            subfolder = '1 MB - 50 MB';
          } else {
            subfolder = '> 50 MB';
          }
          break;
      }

      final destDir = p.join(directory.path, subfolder);
      final destPath = p.join(destDir, filename);

      // Only move if target destination is different from current location
      if (p.normalize(entity.path) != p.normalize(destPath)) {
        operations.add(MoveOperation(
          sourcePath: entity.path,
          destinationPath: destPath,
          category: category,
          fileSizeBytes: stat.size,
        ));
      }
    }

    return operations;
  }

  /// Executes file moves with mandatory System Vault backup
  static Future<SorterResult> executeOrganization({
    required Directory directory,
    required List<MoveOperation> operations,
    required bool dryRun,
  }) async {
    int totalBytes = 0;
    for (final op in operations) {
      totalBytes += op.fileSizeBytes;
    }

    if (dryRun) {
      return SorterResult(
        operations: operations,
        totalFiles: operations.length,
        totalBytes: totalBytes,
        isDryRun: true,
      );
    }

    // 1. Create atomic backup zip before any move
    final filesToBackup = operations.map((op) => File(op.sourcePath)).toList();
    final zipPath = await SystemVault.createBackupArchive(filesToBackup, directory.path);

    // 2. Perform moves
    final executed = <Map<String, String>>[];
    for (final op in operations) {
      final destDir = Directory(p.dirname(op.destinationPath));
      if (!await destDir.exists()) {
        await destDir.create(recursive: true);
      }

      final srcFile = File(op.sourcePath);
      await srcFile.rename(op.destinationPath);
      executed.add(op.toMap());
    }

    // 3. Save undo manifest
    await SystemVault.saveUndoManifest(
      directoryPath: directory.path,
      operations: executed,
      backupZipPath: zipPath,
    );

    return SorterResult(
      operations: operations,
      totalFiles: operations.length,
      totalBytes: totalBytes,
      isDryRun: false,
      backupZipPath: zipPath,
    );
  }

  /// Standalone recursive empty directory cleaner
  static Future<int> cleanEmptyDirectories(Directory dir) async {
    int removed = 0;
    final entities = dir.listSync(recursive: true, followLinks: false).reversed;

    for (final entity in entities) {
      if (entity is Directory) {
        final children = entity.listSync();
        if (children.isEmpty) {
          await entity.delete();
          removed++;
        }
      }
    }
    return removed;
  }
}
