import '../constants/file_categories.dart';

/// Smart Name Sorting & Deterministic Token Extraction
/// Direct high-performance Dart port of sorter_core.py:extract_meaningful_group
class SmartNameSorter {
  static final RegExp _hexOrUuidRegex = RegExp(r'^[a-fA-F0-9\-_]{8,}$');
  static final RegExp _digitOnlyRegex = RegExp(r'^\d+$');
  static final RegExp _datePattern = RegExp(r'^\d{4}[-_]?\d{2}[-_]?\d{2}$');

  /// Natural Sort Key: sorts alphanumeric strings numerically (e.g. file_2 before file_10)
  static int naturalCompare(String a, String b) {
    final aTokens = _tokenize(a);
    final bTokens = _tokenize(b);
    final len = aTokens.length < bTokens.length ? aTokens.length : bTokens.length;

    for (int i = 0; i < len; i++) {
      final aPart = aTokens[i];
      final bPart = bTokens[i];

      final aNum = int.tryParse(aPart);
      final bNum = int.tryParse(bPart);

      if (aNum != null && bNum != null) {
        final cmp = aNum.compareTo(bNum);
        if (cmp != 0) return cmp;
      } else {
        final cmp = aPart.toLowerCase().compareTo(bPart.toLowerCase());
        if (cmp != 0) return cmp;
      }
    }
    return aTokens.length.compareTo(bTokens.length);
  }

  static List<String> _tokenize(String str) {
    final tokens = <String>[];
    final buffer = StringBuffer();
    bool? wasDigit;

    for (int i = 0; i < str.length; i++) {
      final char = str[i];
      final isDigit = char.codeUnitAt(0) >= 48 && char.codeUnitAt(0) <= 57;

      if (wasDigit != null && isDigit != wasDigit) {
        tokens.add(buffer.toString());
        buffer.clear();
      }
      buffer.write(char);
      wasDigit = isDigit;
    }
    if (buffer.isNotEmpty) {
      tokens.add(buffer.toString());
    }
    return tokens;
  }

  /// Extracts the meaningful group/topic folder from a filename
  /// Strips leading numbers, stopwords, dates, and routes pure hashes to _Random/
  static String extractMeaningfulGroup(String filename, {String randomFolder = '_Random'}) {
    // Strip extension
    final dotIdx = filename.lastIndexOf('.');
    final nameWithoutExt = dotIdx > 0 ? filename.substring(0, dotIdx) : filename;

    // Normalize separators
    final normalized = nameWithoutExt
        .replaceAll(RegExp(r'[\._\-\+]'), ' ')
        .replaceAll(RegExp(r'\s+'), ' ')
        .trim();

    if (normalized.isEmpty) return randomFolder;

    // Check if filename is purely hex / UUID / MD5 / SHA hash
    if (_hexOrUuidRegex.hasMatch(nameWithoutExt.replaceAll(RegExp(r'[\-_]'), ''))) {
      return randomFolder;
    }

    final words = normalized.split(' ');
    final candidateWords = <String>[];

    for (int i = 0; i < words.length; i++) {
      final word = words[i].trim();
      if (word.isEmpty) continue;

      // Skip leading numeric index (e.g. "01 - MyFile" -> skips "01")
      if (candidateWords.isEmpty && _digitOnlyRegex.hasMatch(word)) {
        continue;
      }

      // Stop on date stamps (e.g. "Invoice 2024-05-12" -> "Invoice")
      if (_datePattern.hasMatch(word)) {
        break;
      }

      final lowerWord = word.toLowerCase();
      // Skip leading stopwords
      if (candidateWords.isEmpty && FileCategories.commonStopwords.contains(lowerWord)) {
        continue;
      }

      candidateWords.add(word);
      // Group by the first 1-2 meaningful topical words
      if (candidateWords.length >= 2) break;
    }

    if (candidateWords.isEmpty) {
      return randomFolder;
    }

    // Capitalize Title Case
    return candidateWords
        .map((w) => w.length > 1 ? '${w[0].toUpperCase()}${w.substring(1)}' : w.toUpperCase())
        .join(' ');
  }
}
