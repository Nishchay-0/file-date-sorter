/// Central File Categories & Extension Constants for Smart File Organizer
/// Ported from config.py to native Dart for Android, Windows, and macOS.

class FileCategories {
  static const Map<String, List<String>> categories = {
    'Images': [
      '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif',
      '.raw', '.cr2', '.nef', '.arw', '.dng', '.heic', '.svg', '.ico',
      '.psd', '.ai', '.eps', '.jfif'
    ],
    'Videos': [
      '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v',
      '.mpg', '.mpeg', '.3gp', '.3g2', '.ts', '.vob', '.ogv', '.f4v'
    ],
    'Audio': [
      '.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma', '.opus',
      '.aiff', '.alac', '.mid', '.midi', '.amr', '.3ga'
    ],
    'Documents': [
      '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx',
      '.ods', '.ppt', '.pptx', '.odp', '.csv', '.tsv', '.epub', '.mobi',
      '.md', '.tex', '.pages', '.numbers', '.key'
    ],
    'Archives': [
      '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso',
      '.dmg', '.tgz', '.tbz2', '.zst', '.cab', '.wim'
    ],
    'Code': [
      '.py', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.js', '.ts',
      '.html', '.css', '.scss', '.sass', '.json', '.xml', '.yaml', '.yml',
      '.sql', '.sh', '.bat', '.ps1', '.go', '.rs', '.rb', '.php', '.dart',
      '.kt', '.swift', '.r', '.m'
    ],
    'Executables': [
      '.exe', '.msi', '.apk', '.app', '.bat', '.cmd', '.ps1', '.vbs',
      '.jar', '.deb', '.rpm', '.run', '.bin', '.aab'
    ],
    'Fonts': [
      '.ttf', '.otf', '.woff', '.woff2', '.eot', '.fon'
    ],
    'Database': [
      '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb', '.sqlitedb', '.db3'
    ],
    'System': [
      '.dll', '.sys', '.ini', '.cfg', '.conf', '.log', '.tmp', '.bak',
      '.reg', '.dat'
    ]
  };

  /// Common stopwords stripped during Smart Name Grouping (Ported exactly from config.py)
  static const Set<String> commonStopwords = {
    'a', 'an', 'her', 'his', 'its', 'my', 'our', 'that', 'the', 'their', 'these', 'this', 'those', 'your'
  };

  /// Map an extension to its Category Name
  static String getCategoryForExtension(String ext) {
    final lowerExt = ext.toLowerCase();
    for (final entry in categories.entries) {
      if (entry.value.contains(lowerExt)) {
        return entry.key;
      }
    }
    return 'Other';
  }
}
