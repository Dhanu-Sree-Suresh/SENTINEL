import os
import sys
import unittest
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.accountant import compute_epsilon, find_sigma_for_epsilon, rdp_gaussian


class TestAccountant(unittest.TestCase):
    def test_epsilon_decreases_with_more_noise(self):
        """More noise (higher sigma) at fixed steps/delta must give a SMALLER epsilon."""
        eps_low_noise, _, _ = compute_epsilon(sigma=1.0, num_steps=50, delta=1e-5)
        eps_high_noise, _, _ = compute_epsilon(sigma=5.0, num_steps=50, delta=1e-5)
        self.assertGreater(eps_low_noise, eps_high_noise)

    def test_epsilon_increases_with_more_steps(self):
        """More composed releases at fixed sigma must give a LARGER (worse) epsilon
        -- this is the composition property; getting this backwards is exactly the
        'ignoring composition' mistake called out as a common DP bug."""
        eps_few, _, _ = compute_epsilon(sigma=2.0, num_steps=10, delta=1e-5)
        eps_many, _, _ = compute_epsilon(sigma=2.0, num_steps=100, delta=1e-5)
        self.assertLess(eps_few, eps_many)

    def test_epsilon_increases_as_delta_shrinks(self):
        """Tighter (smaller) delta must not make epsilon smaller for the same mechanism."""
        eps_loose_delta, _, _ = compute_epsilon(sigma=2.0, num_steps=50, delta=1e-3)
        eps_tight_delta, _, _ = compute_epsilon(sigma=2.0, num_steps=50, delta=1e-8)
        self.assertLessEqual(eps_loose_delta, eps_tight_delta)

    def test_find_sigma_round_trip(self):
        """find_sigma_for_epsilon should invert compute_epsilon to within tolerance."""
        for target_eps in [0.5, 1.0, 4.0, 8.0]:
            sigma = find_sigma_for_epsilon(target_eps, num_steps=15, delta=1e-5)
            actual_eps, _, _ = compute_epsilon(sigma, num_steps=15, delta=1e-5)
            self.assertAlmostEqual(actual_eps, target_eps, delta=0.05)

    def test_rdp_gaussian_scales_with_alpha(self):
        """RDP of the Gaussian mechanism is alpha / (2 sigma^2) -- linear in alpha."""
        sigma = 2.0
        self.assertAlmostEqual(rdp_gaussian(2.0, sigma), 2 * rdp_gaussian(1.0, sigma), places=6)

    def test_epsilon_always_positive_and_finite(self):
        for sigma in [0.5, 1.0, 5.0, 20.0]:
            for steps in [1, 15, 100]:
                eps, delta, alpha = compute_epsilon(sigma, steps, 1e-5)
                self.assertGreater(eps, 0)
                self.assertLess(eps, 1e6)


if __name__ == "__main__":
    unittest.main()
