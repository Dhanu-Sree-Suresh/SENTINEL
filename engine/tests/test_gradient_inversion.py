import os
import sys
import unittest
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model import LogisticRegressionNP
from src.attacks.gradient_inversion import (single_example_gradient, invert_from_gradient,
                                             clip_and_noise_single, run_inversion_demo)


class TestGradientInversion(unittest.TestCase):
    def test_raw_gradient_inverts_exactly(self):
        """For logistic regression, x = grad_w / grad_b must recover x exactly
        (up to floating point) when the gradient is NOT clipped or noised --
        this is the core claim of the attack and must hold deterministically."""
        rng = np.random.default_rng(0)
        model = LogisticRegressionNP(6, seed=1)
        x = rng.normal(0, 1, size=6)
        y = 1
        gw, gb, err = single_example_gradient(model, x, y)
        if abs(err) < 1e-6:
            self.skipTest("degenerate near-zero-error draw; not informative")
        x_rec = invert_from_gradient(gw, gb)
        np.testing.assert_allclose(x_rec, x, rtol=1e-6, atol=1e-6)

    def test_dp_protected_gradient_does_not_invert(self):
        """With clipping + noise applied, reconstruction must NOT recover the
        true input to any meaningful precision."""
        rng = np.random.default_rng(0)
        model = LogisticRegressionNP(6, seed=1)
        x = rng.normal(0, 1, size=6)
        y = 1
        gw, gb, err = single_example_gradient(model, x, y)
        gw_dp, gb_dp = clip_and_noise_single(gw, gb, clip_norm=1.0, noise_multiplier=5.0,
                                              rng=np.random.default_rng(42))
        x_rec_dp = invert_from_gradient(gw_dp, gb_dp)
        if x_rec_dp is None:
            return  # gb_dp ~ 0 -> correctly refuses to invert, also a pass
        cos_sim = np.dot(x_rec_dp, x) / (np.linalg.norm(x_rec_dp) * np.linalg.norm(x) + 1e-9)
        self.assertLess(abs(cos_sim), 0.9)  # should NOT be close to a real reconstruction

    def test_inversion_demo_summary_shape(self):
        rng = np.random.default_rng(0)
        X = rng.normal(0, 1, size=(40, 5))
        y = (rng.random(40) < 0.4).astype(int)
        model = LogisticRegressionNP(5, seed=2)
        summary = run_inversion_demo(model, X, y, clip_norm=1.0, noise_multiplier=3.0,
                                      seed=1, n_trials=20)
        self.assertIn("raw", summary)
        self.assertIn("dp_protected", summary)
        # the headline claim: raw reconstruction fidelity >> DP-protected fidelity
        self.assertGreater(summary["raw"]["mean_cosine_similarity"],
                            summary["dp_protected"]["mean_cosine_similarity"])


if __name__ == "__main__":
    unittest.main()
