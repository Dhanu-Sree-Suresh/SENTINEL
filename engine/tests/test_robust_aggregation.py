import os
import sys
import unittest
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.robust_agg import fedavg, coordinate_median, coordinate_trimmed_mean, aggregate
from src.attacks.poisoning import craft_malicious_update


class TestRobustAggregation(unittest.TestCase):
    def test_fedavg_is_sensitive_to_one_outlier(self):
        honest = [np.array([1.0, 1.0]) for _ in range(3)]
        malicious = np.array([1.0, 1.0]) * (-8.0)
        updates = honest + [malicious]
        result = fedavg(updates)
        # a single 8x sign-flipped client out of 4 should visibly drag the mean
        self.assertLess(result[0], 0.0)

    def test_median_resists_one_outlier(self):
        honest = [np.array([1.0, 1.0]) for _ in range(3)]
        malicious = np.array([1.0, 1.0]) * (-8.0)
        updates = honest + [malicious]
        result = coordinate_median(updates)
        np.testing.assert_allclose(result, [1.0, 1.0])

    def test_trimmed_mean_resists_one_outlier_at_n4_trim025(self):
        honest = [np.array([1.0]), np.array([1.0]), np.array([1.0])]
        malicious = [np.array([-8.0])]
        updates = honest + malicious
        result = coordinate_trimmed_mean(updates, trim_frac=0.25)
        np.testing.assert_allclose(result, [1.0])

    def test_trimmed_mean_default_trim_frac_actually_trims_at_n4(self):
        """Regression test for a real bug found during development:
        trim_frac=0.2 rounds down to k=0 trimmed clients at n=4 and
        silently degenerates to plain FedAvg. The default must not do
        this for the platform's realistic 3-5 client cohort size."""
        honest = [np.array([1.0]), np.array([1.0]), np.array([1.0])]
        malicious = [np.array([-100.0])]
        updates = honest + malicious
        result = aggregate(updates, strategy="trimmed_mean")  # uses the module default
        self.assertGreater(result[0], 0.5, "default trim_frac failed to exclude the outlier")

    def test_craft_malicious_update_scale_preserves_direction(self):
        honest = np.array([1.0, -2.0, 0.5])
        mal = craft_malicious_update(honest, mode="scale", scale=10.0)
        np.testing.assert_allclose(mal, honest * 10.0)

    def test_craft_malicious_update_sign_flip_reverses_direction(self):
        honest = np.array([1.0, -2.0, 0.5])
        mal = craft_malicious_update(honest, mode="sign_flip", scale=3.0)
        np.testing.assert_allclose(mal, -honest * 3.0)
        self.assertLess(np.dot(mal, honest), 0)  # genuinely adversarial direction

    def test_unknown_strategy_raises(self):
        with self.assertRaises(ValueError):
            aggregate([np.array([1.0])], strategy="not_a_real_strategy")


if __name__ == "__main__":
    unittest.main()
