import os
import sys
import unittest
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model import LogisticRegressionNP
from src.dp_sgd import clip_gradients, dp_sgd_local_train


class TestDPSGD(unittest.TestCase):
    def test_clip_gradients_enforces_norm_bound(self):
        rng = np.random.default_rng(0)
        grads = rng.normal(0, 10, size=(200, 6))  # deliberately large, unclipped norms
        clipped = clip_gradients(grads, clip_norm=1.0)
        norms = np.linalg.norm(clipped, axis=1)
        self.assertTrue(np.all(norms <= 1.0 + 1e-9))

    def test_clip_gradients_leaves_small_gradients_untouched(self):
        rng = np.random.default_rng(0)
        grads = rng.normal(0, 0.01, size=(50, 4))  # already well within the bound
        clipped = clip_gradients(grads, clip_norm=5.0)
        np.testing.assert_allclose(clipped, grads)

    def test_dp_training_runs_and_changes_model(self):
        rng = np.random.default_rng(1)
        X = rng.normal(0, 1, size=(300, 5))
        y = (rng.random(300) < 0.3).astype(int)
        model = LogisticRegressionNP(5, seed=1)
        w0 = model.w.copy()
        dp_sgd_local_train(model, X, y, epochs=3, batch_size=len(X), lr=0.5,
                            clip_norm=1.0, noise_multiplier=1.0, enable_dp=True,
                            rng=np.random.default_rng(2))
        self.assertFalse(np.allclose(w0, model.w))  # model actually moved

    def test_disabling_dp_matches_plain_sgd_with_zero_noise_and_huge_clip(self):
        """enable_dp=False should be numerically equivalent to enable_dp=True with
        an effectively-infinite clip norm and zero noise (same optimizer, different
        privacy mechanism -- this is the property that makes conditions 1-4
        comparable at all)."""
        rng = np.random.default_rng(3)
        X = rng.normal(0, 1, size=(150, 4))
        y = (rng.random(150) < 0.4).astype(int)

        m1 = LogisticRegressionNP(4, seed=5)
        dp_sgd_local_train(m1, X, y, epochs=5, batch_size=len(X), lr=0.3,
                            clip_norm=1e9, noise_multiplier=0.0, enable_dp=False,
                            rng=np.random.default_rng(9))

        m2 = LogisticRegressionNP(4, seed=5)
        dp_sgd_local_train(m2, X, y, epochs=5, batch_size=len(X), lr=0.3,
                            clip_norm=1e9, noise_multiplier=0.0, enable_dp=True,
                            rng=np.random.default_rng(9))

        np.testing.assert_allclose(m1.w, m2.w, rtol=1e-6)


if __name__ == "__main__":
    unittest.main()
