import 'package:flutter_test/flutter_test.dart';
import '../lib/core/smart_name_sorter.dart';
import '../lib/constants/file_categories.dart';

void main() {
  group('SmartNameSorter Tests', () {
    test('naturalCompare sorts numerically', () {
      final list = ['file_10.txt', 'file_2.txt', 'file_1.txt', 'file_20.txt'];
      list.sort(SmartNameSorter.naturalCompare);
      expect(list, ['file_1.txt', 'file_2.txt', 'file_10.txt', 'file_20.txt']);
    });

    test('extractMeaningfulGroup strips leading numbers and stopwords', () {
      expect(SmartNameSorter.extractMeaningfulGroup('01 - The Invoice Report.pdf'), 'Invoice Report');
      expect(SmartNameSorter.extractMeaningfulGroup('a new document.docx'), 'New Document');
      expect(SmartNameSorter.extractMeaningfulGroup('IMG_20240101_123456.jpg'), 'Img');
    });

    test('extractMeaningfulGroup routes random hashes to _Random', () {
      expect(SmartNameSorter.extractMeaningfulGroup('a1b2c3d4e5f60718.dat'), '_Random');
      expect(SmartNameSorter.extractMeaningfulGroup('4f3d2c1b.tmp'), '_Random');
    });

    test('extractMeaningfulGroup stops at date patterns', () {
      expect(SmartNameSorter.extractMeaningfulGroup('Bank Statement 2024-05-12.pdf'), 'Bank Statement');
    });
  });

  group('FileCategories Tests', () {
    test('detects correct category from extension', () {
      expect(FileCategories.getCategoryForExtension('.jpg'), 'Images');
      expect(FileCategories.getCategoryForExtension('.pdf'), 'Documents');
      expect(FileCategories.getCategoryForExtension('.mp4'), 'Videos');
      expect(FileCategories.getCategoryForExtension('.mp3'), 'Audio');
      expect(FileCategories.getCategoryForExtension('.zip'), 'Archives');
      expect(FileCategories.getCategoryForExtension('.py'), 'Code');
      expect(FileCategories.getCategoryForExtension('.xyz123'), 'Other');
    });
  });
}
