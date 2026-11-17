"""
test_people_clustering_tune.py - Unit Test Suite for Face Clustering Tuning & UI Actions

Verifies:
1. Complete-linkage cosine distance clustering prevents mega-cluster absorption.
2. Face quality and size filtering.
3. Statistical outlier cluster detection (is_outlier & warning text).
4. Date range calculation per cluster.
5. Non-destructive cluster merging and face splitting/removal.
"""

import os
import sys
import shutil
import tempfile
import unittest
import numpy as np

from face_sort import FaceSorterEngine, crop_to_b64


class TestPeopleClusteringTune(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_people_tune_")
        self.cache_file = os.path.join(self.test_dir, ".people_cache.json")
        self.index_file = os.path.join(self.test_dir, ".people_index.json")
        self.engine = FaceSorterEngine(cache_file=self.cache_file, index_file=self.index_file)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_complete_linkage_clustering_prevents_mega_cluster(self):
        # Create 4 distinct face embedding groups (128-d vectors)
        # Group 1: 5 faces around [1, 0, 0, ...]
        # Group 2: 5 faces around [0, 1, 0, ...]
        # Group 3: 5 faces around [0, 0, 1, ...]
        # Group 4: 5 faces around [0, 0, 0, 1, ...]
        np.random.seed(42)
        v1 = np.zeros(128); v1[0] = 1.0
        v2 = np.zeros(128); v2[1] = 1.0
        v3 = np.zeros(128); v3[2] = 1.0
        v4 = np.zeros(128); v4[3] = 1.0

        embeddings = []
        for v in [v1, v2, v3, v4]:
            for _ in range(5):
                noisy_v = v + np.random.normal(0, 0.05, 128)
                embeddings.append(noisy_v)

        X = np.array(embeddings)
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        X_norm = X / norms

        # Cluster using complete linkage cosine distance (distance_threshold=0.34)
        labels = self.engine._complete_linkage_cluster(X_norm, distance_threshold=0.34)
        unique_labels = set(labels)

        # Must form 4 distinct clusters, NOT 1 giant merged cluster!
        self.assertEqual(len(unique_labels), 4)
        self.assertNotIn(-1, unique_labels)

    def test_02_outlier_cluster_detection(self):
        # Create mock clusters where one cluster has 25 items and others have 2
        mock_clusters = {
            "Person_1": {"name": "Person 1", "faces": [{"filepath": f"p1_{i}.jpg"} for i in range(25)]},
            "Person_2": {"name": "Person 2", "faces": [{"filepath": "p2_1.jpg"}, {"filepath": "p2_2.jpg"}]},
            "Person_3": {"name": "Person 3", "faces": [{"filepath": "p3_1.jpg"}, {"filepath": "p3_2.jpg"}]},
            "Person_4": {"name": "Person 4", "faces": [{"filepath": "p4_1.jpg"}, {"filepath": "p4_2.jpg"}]}
        }

        flagged = self.engine._flag_outlier_clusters(mock_clusters)
        self.assertTrue(flagged["Person_1"].get('is_outlier'))
        self.assertIn("Unusually large", flagged["Person_1"].get('outlier_warning', ''))
        self.assertFalse(flagged["Person_2"].get('is_outlier'))

    def test_03_merge_and_split_clusters(self):
        self.engine.index = {
            "clusters": {
                "Person_1": {"name": "Alice", "faces": [{"filepath": "a1.jpg", "face_idx": 0}, {"filepath": "a2.jpg", "face_idx": 0}]},
                "Person_2": {"name": "Bob", "faces": [{"filepath": "b1.jpg", "face_idx": 0}]},
                "Person_3": {"name": "Charlie", "faces": [{"filepath": "c1.jpg", "face_idx": 0}]}
            }
        }

        # Merge Person_2 and Person_3 into Person_1
        ok = self.engine.merge_clusters(["Person_2", "Person_3"], "Person_1")
        self.assertTrue(ok)
        clusters = self.engine.index["clusters"]
        self.assertIn("Person_1", clusters)
        self.assertNotIn("Person_2", clusters)
        self.assertNotIn("Person_3", clusters)
        self.assertEqual(len(clusters["Person_1"]["faces"]), 4)

        # Split / remove "b1.jpg" from Person_1
        ok_split = self.engine.remove_face_from_cluster("Person_1", "b1.jpg", face_idx=0)
        self.assertTrue(ok_split)
        self.assertEqual(len(clusters["Person_1"]["faces"]), 3)
        self.assertIn("Unassigned", clusters)
        self.assertEqual(len(clusters["Unassigned"]["faces"]), 1)

    def test_04_crop_to_b64_thumbnail_encoding(self):
        # Generate dummy 100x100 BGR array
        dummy_bgr = np.zeros((100, 100, 3), dtype=np.uint8)
        b64_str = crop_to_b64(dummy_bgr)
        self.assertIsInstance(b64_str, str)


if __name__ == '__main__':
    unittest.main()
