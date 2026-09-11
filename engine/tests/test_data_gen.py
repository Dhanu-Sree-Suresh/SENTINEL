import os
import sys
import unittest
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_gen import generate_all, FEATURE_COLUMNS, ENTITY_CONFIG


class TestDataGen(unittest.TestCase):
    def test_generates_all_configured_entities(self):
        df = generate_all(seed=1, scale=0.02)
        self.assertEqual(set(df.entity.unique()), set(ENTITY_CONFIG.keys()))

    def test_no_missing_values_after_imputation(self):
        df = generate_all(seed=1, scale=0.02)
        self.assertEqual(df[FEATURE_COLUMNS].isna().sum().sum(), 0)

    def test_label_is_binary(self):
        df = generate_all(seed=1, scale=0.02)
        self.assertEqual(set(df.insider_threat_label.unique()) - {0, 1}, set())

    def test_positive_rate_is_rare_per_entity(self):
        """Sanity check on the intended class-imbalance design -- if this
        drifts to e.g. 50% positive, the whole 'rare-event classifier'
        framing (and the high-risk-subgroup MI attack) silently breaks."""
        df = generate_all(seed=1, scale=1.0)
        for entity in ENTITY_CONFIG:
            rate = df[df.entity == entity].insider_threat_label.mean()
            self.assertLess(rate, 0.15, f"entity {entity} positive rate too high: {rate}")
            self.assertGreater(rate, 0.005, f"entity {entity} positive rate too low: {rate}")

    def test_synthetic_ids_are_unique(self):
        df = generate_all(seed=1, scale=0.02)
        self.assertEqual(df.synthetic_id.nunique(), len(df))

    def test_reproducible_with_same_seed(self):
        df1 = generate_all(seed=7, scale=0.02)
        df2 = generate_all(seed=7, scale=0.02)
        np.testing.assert_allclose(df1[FEATURE_COLUMNS].values, df2[FEATURE_COLUMNS].values)

    def test_different_seeds_differ(self):
        df1 = generate_all(seed=7, scale=0.02)
        df2 = generate_all(seed=8, scale=0.02)
        self.assertFalse(np.allclose(df1[FEATURE_COLUMNS].values, df2[FEATURE_COLUMNS].values))

    def test_scale_parameter_changes_row_count(self):
        df_small = generate_all(seed=1, scale=0.01)
        df_big = generate_all(seed=1, scale=0.1)
        self.assertLess(len(df_small), len(df_big))


if __name__ == "__main__":
    unittest.main()
