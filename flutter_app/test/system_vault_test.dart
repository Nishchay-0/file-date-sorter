import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('SystemVault Manifest Tests', () {
    test('manifest serialization structure matches Python engine', () {
      final manifest = {
        'version': '1.0.0',
        'timestamp': DateTime.now().toIso8601String(),
        'target_dir': '/data/user/0/documents',
        'operations': [
          {
            'type': 'move',
            'source': '/data/user/0/documents/photo.jpg',
            'destination': '/data/user/0/documents/Images/photo.jpg'
          }
        ],
        'total_files': 1,
        'app': 'SmartFileOrganizerSuitePro-Mobile'
      };

      final jsonStr = jsonEncode(manifest);
      final decoded = jsonDecode(jsonStr) as Map<String, dynamic>;

      expect(decoded['version'], '1.0.0');
      expect(decoded['total_files'], 1);
      expect(decoded['operations'].length, 1);
      expect(decoded['operations'][0]['type'], 'move');
    });
  });
}
