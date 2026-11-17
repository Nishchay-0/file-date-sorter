import '../constants/file_categories.dart';

/// Smart Name Sorting & Deterministic Token Extraction
/// Direct high-performance Dart port of sorter_core.py:extract_meaningful_group
class SmartNameSorter {
  static final RegExp _uuidRegex = RegExp(r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$');
  static final RegExp _hexHashRegex = RegExp(r'^[a-fA-F0-9]{12,}$');

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
  /// Ported directly from sorter_core.py:extract_meaningful_group
  static String extractMeaningfulGroup(String filename, {String randomFolder = '_Random'}) {
    if (filename.isEmpty) return randomFolder;

    // Stem without extension
    final dotIdx = filename.lastIndexOf('.');
    final stem = dotIdx > 0 ? filename.substring(0, dotIdx).trim() : filename.trim();
    if (stem.isEmpty) return randomFolder;

    // Check UUID or pure numeric without separator
    final cleanNoSep = stem.replaceAll(RegExp(r'[\s_\-\.]'), '');
    if (RegExp(r'^\d+$').hasMatch(cleanNoSep) || _uuidRegex.hasMatch(stem)) {
      return randomFolder;
    }

    // Hex hash >= 12 chars without clear alphabetic token >= 3 chars
    if (_hexHashRegex.hasMatch(cleanNoSep) && cleanNoSep.contains(RegExp(r'\d')) && cleanNoSep.contains(RegExp(r'[a-zA-Z]'))) {
      final tokensAll = RegExp(r'[a-zA-Z]+').allMatches(stem).map((m) => m.group(0)!).toList();
      if (!tokensAll.any((t) => t.length >= 3)) {
        return randomFolder;
      }
    }

    // Interleaved hash/random alphanumeric strings (e.g. 323f9w8ehf8awjefi, 4f8a2c9e1b)
    if (RegExp(r'\d+[a-zA-Z]+\d+[a-zA-Z]+|\d+[a-zA-Z]\d+').hasMatch(stem)) {
      return randomFolder;
    }

    // Random consonant gibberish
    final alphaOnly = stem.replaceAll(RegExp(r'[^a-zA-Z]'), '').toLowerCase();
    if (alphaOnly.length >= 8 && !alphaOnly.contains(RegExp(r'[aeiou]'))) {
      return randomFolder;
    }

    // Normalize separators into single _
    final norm = stem.replaceAll(RegExp(r'[\s_\-\.]+'), '_').replaceAll(RegExp(r'^_+|_+$'), '');
    if (norm.isEmpty) return randomFolder;

    final tokens = norm.split('_');
    final prefixParts = <String>[];
    bool started = false;

    for (final tok in tokens) {
      if (tok.isEmpty) continue;

      if (RegExp(r'^\d+$').hasMatch(tok)) {
        if (started) {
          break; // Stop scanning on date/number after title
        } else {
          continue; // Skip leading counter
        }
      }

      final alphaParts = RegExp(r'[a-zA-Z]+').allMatches(tok).map((m) => m.group(0)!).toList();
      if (alphaParts.isEmpty) {
        if (started) break; else continue;
      }

      for (final ap in alphaParts) {
        prefixParts.add(ap);
        started = true;
      }
    }

    if (prefixParts.isEmpty) return randomFolder;

    // Strip leading stopwords
    while (prefixParts.isNotEmpty && FileCategories.commonStopwords.contains(prefixParts.first.toLowerCase())) {
      prefixParts.removeAt(0);
    }

    if (prefixParts.isEmpty) return randomFolder;

    // Minimum length rule: joined length >= 3 and at least one token >= 2
    final joined = prefixParts.join(' ');
    if (joined.length < 3 || !prefixParts.any((p) => p.length >= 2)) {
      return randomFolder;
    }

    // Title case formatting
    return prefixParts
        .map((w) => w.length > 1 ? '${w[0].toUpperCase()}${w.substring(1)}' : w.toUpperCase())
        .join(' ');
  }
}
