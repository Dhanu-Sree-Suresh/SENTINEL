import os
import sys
import unittest
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.secure_agg import secure_aggregate, generate_pairwise_masks


class TestSecureAggregation(unittest.TestCase):
    def test_masked_sum_equals_true_sum(self):
        rng = np.random.default_rng(0)
        updates = [rng.normal(0, 1, size=8) for _ in range(4)]
        true_sum = np.sum(updates, axis=0)
        recovered_sum, masked_views = secure_aggregate(updates, round_seed=123)
        np.testing.assert_allclose(recovered_sum, true_sum, atol=1e-8)

    def test_aggregator_view_hides_individual_update(self):
        rng = np.random.default_rng(1)
        updates = [rng.normal(0, 1, size=8) for _ in range(4)]
        _, masked_views = secure_aggregate(updates, round_seed=999)
        for true_u, masked_u in zip(updates, masked_views):
            self.assertGreater(np.linalg.norm(true_u - masked_u), 0.5,
                                "masked view too close to the true individual update")

    def test_masks_are_deterministic_given_same_round_seed(self):
        m1 = generate_pairwise_masks(4, 6, round_seed=42)
        m2 = generate_pairwise_masks(4, 6, round_seed=42)
        np.testing.assert_allclose(m1, m2)

    def test_masks_differ_across_rounds(self):
        m1 = generate_pairwise_masks(4, 6, round_seed=1)
        m2 = generate_pairwise_masks(4, 6, round_seed=2)
        self.assertFalse(np.allclose(m1, m2))

    def test_pairwise_masks_sum_to_zero_across_clients(self):
        """This is the entire correctness property secure aggregation relies
        on: every pairwise mask must cancel when summed across all clients."""
        masks = generate_pairwise_masks(5, 10, round_seed=7)
        np.testing.assert_allclose(masks.sum(axis=0), np.zeros(10), atol=1e-8)


if __name__ == "__main__":
    unittest.main()
