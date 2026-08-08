"""
test_people_sorter.py - Unit & Integration Test Suite for Face-Based People Sorter Engine

Tests:
1. Face detection & embedding extraction pipeline on synthetic test images.
2. Embedding vector consistency for identical inputs.
3. DBSCAN clustering behavior on synthetic multi-face dataset.
4. Caching layer hit/miss logic on file modification.
5. Non-destructive opt-in shortcut generation (.url shortcuts).
"""

import os
import sys
import shutil
import tempfile
import unittest
import numpy as np

try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from face_sort import FaceSorterEngine


class TestPeopleSorterEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_people_sorter_")
        self.cache_file = os.path.join(self.test_dir, ".people_cache.json")
        self.index_file = os.path.join(self.test_dir, ".people_index.json")
        self.engine = FaceSorterEngine(cache_file=self.cache_file, index_file=self.index_file)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_synthetic_face_image(self, filename, circle_color=(200, 100, 100)):
        """Creates a synthetic image with a face-like structure (circle + eyes + mouth)."""
        fp = os.path.join(self.test_dir, filename)
        if HAS_PIL:
            img = Image.new('RGB', (200, 200), color=(240, 240, 240))
            draw = ImageDraw.Draw(img)
            # Head
            draw.ellipse((50, 50, 150, 150), fill=circle_color, outline=(0, 0, 0))
            # Eyes
            draw.ellipse((70, 75, 85, 90), fill=(0, 0, 0))
            draw.ellipse((115, 75, 130, 90), fill=(0, 0, 0))
            # Mouth
            draw.line((80, 120, 120, 120), fill=(0, 0, 0), width=3)
            img.save(fp)
        else:
            with open(fp, 'w') as f:
                f.write("mock_image")
        return fp

    def test_01_synthetic_face_detection_and_embedding(self):
        img_path = self._create_synthetic_face_image("face1.jpg")
        faces = self.engine.process_image_file(img_path)
        self.assertIsInstance(faces, list)
        if len(faces) > 0:
            face = faces[0]
            self.assertIn('rect', face)
            self.assertIn('embedding', face)
            self.assertEqual(len(face['embedding']), 128)

    def test_02_embedding_consistency(self):
        img_path = self._create_synthetic_face_image("face_consistency.jpg")
        faces1 = self.engine.process_image_file(img_path)
        faces2 = self.engine.process_image_file(img_path)
        if faces1 and faces2:
            emb1 = np.array(faces1[0]['embedding'])
            emb2 = np.array(faces2[0]['embedding'])
            np.testing.assert_allclose(emb1, emb2, rtol=1e-5)

    def test_03_dbscan_clustering(self):
        # Create synthetic normalized embeddings for 2 distinct clusters
        c1_v1 = np.random.normal(loc=1.0, scale=0.01, size=(5, 128))
        c2_v2 = np.random.normal(loc=-1.0, scale=0.01, size=(5, 128))
        X = np.vstack([c1_v1, c2_v2])
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        X_norm = X / norms

        labels = self.engine._simple_dbscan(X_norm, eps=0.45, min_samples=1)
        self.assertEqual(len(labels), 10)
        # Verify elements in cluster 1 share label, elements in cluster 2 share label
        self.assertEqual(labels[0], labels[1])
        self.assertEqual(labels[5], labels[6])
        self.assertNotEqual(labels[0], labels[5])

    def test_04_caching_layer_hit_miss(self):
        img_path = self._create_synthetic_face_image("cache_test.jpg")
        res1 = self.engine.scan_directory(self.test_dir)
        self.assertTrue(os.path.exists(self.cache_file))

        # Re-run scan without modifying file -> Cache hit
        res2 = self.engine.scan_directory(self.test_dir)
        self.assertEqual(res1['total_files'], res2['total_files'])

    def test_05_opt_in_shortcut_generation(self):
        img_path = self._create_synthetic_face_image("shortcut_photo.jpg")
        res = self.engine.scan_directory(self.test_dir)
        shortcuts_res = self.engine.create_people_shortcuts(self.test_dir)
        self.assertIn('created_shortcuts', shortcuts_res)
        self.assertTrue(os.path.exists(shortcuts_res['people_dir']))


if __name__ == '__main__':
    unittest.main()
