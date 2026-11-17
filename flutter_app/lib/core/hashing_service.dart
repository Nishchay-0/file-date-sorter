import 'dart:io';
import 'dart:math';
import 'dart:typed_data';
import 'package:crypto/crypto.dart';

/// Tiered File Hashing & Perceptual Comparison Engine
/// Direct Dart port of hashing.py
class HashingService {
  static const int chunkSize = 65536; // 64 KB
  static const int sampleSize = 16384; // 16 KB for head/tail sampling

  /// Calculates full SHA-256 hash of a file
  static Future<String> getFileHash(File file) async {
    final stream = file.openRead();
    final digest = await sha256.bind(stream).first;
    return digest.toString();
  }

  /// Calculates fast head + tail SHA-256 hash for ultra-fast candidate duplicate filtering
  static Future<String> getFileFastHash(File file) async {
    final length = await file.length();
    if (length <= sampleSize * 2) {
      return getFileHash(file);
    }

    final raf = await file.open(mode: FileMode.read);
    try {
      final head = await raf.read(sampleSize);
      await raf.setPosition(length - sampleSize);
      final tail = await raf.read(sampleSize);

      final combined = Uint8List(head.length + tail.length);
      combined.setRange(0, head.length, head);
      combined.setRange(head.length, combined.length, tail);

      return sha256.convert(combined).toString();
    } finally {
      await raf.close();
    }
  }

  /// Calculates fuzzy Levenshtein name similarity between two file names (0.0 to 1.0)
  static double calculateFuzzyNameSimilarity(String s1, String s2) {
    if (s1 == s2) return 1.0;
    if (s1.isEmpty || s2.isEmpty) return 0.0;

    final distance = _levenshteinDistance(s1.toLowerCase(), s2.toLowerCase());
    final maxLen = max(s1.length, s2.length);
    return 1.0 - (distance / maxLen);
  }

  static int _levenshteinDistance(String s1, String s2) {
    final d = List.generate(s1.length + 1, (_) => List.filled(s2.length + 1, 0));

    for (int i = 0; i <= s1.length; i++) d[i][0] = i;
    for (int j = 0; j <= s2.length; j++) d[0][j] = j;

    for (int i = 1; i <= s1.length; i++) {
      for (int j = 1; j <= s2.length; j++) {
        final cost = s1[i - 1] == s2[j - 1] ? 0 : 1;
        d[i][j] = min(
          d[i - 1][j] + 1,
          min(d[i][j - 1] + 1, d[i - 1][j - 1] + cost),
        );
      }
    }
    return d[s1.length][s2.length];
  }
}
