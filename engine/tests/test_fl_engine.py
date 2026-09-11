import os
import sys
import unittest
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fl_engine import Client, run_federated_training


def _make_clients(seed=0, n_clients=3, n=200, d=5):
    rng = np.random.default_rng(seed)
    clients = []
    for i in range(n_clients):
        X = rng.normal(0, 1, size=(n, d))
        y = (rng.random(n) < 0.3).astype(int)
        clients.append(Client(f"client_{i}", X, y))
    return clients


class TestFLEngineReproducibility(unittest.TestCase):
    def test_identical_seed_gives_identical_model(self):
        """This is a regression test for a real bug found during
        development: using Python's randomized hash(str) to seed
        per-client local RNGs made every run non-reproducible even
        with a fixed top-level seed. Must never regress."""
        clients = _make_clients()
        m1, _, _ = run_federated_training(
            clients, rounds=5, lr=0.5, clip_norm=1.0, noise_multiplier=1.0,
            enable_dp=True, enable_secure_agg=False, fedprox_mu=0.0, seed=42,
        )
        clients2 = _make_clients()  # rebuild identically
        m2, _, _ = run_federated_training(
            clients2, rounds=5, lr=0.5, clip_norm=1.0, noise_multiplier=1.0,
            enable_dp=True, enable_secure_agg=False, fedprox_mu=0.0, seed=42,
        )
        np.testing.assert_allclose(m1.get_flat_params(), m2.get_flat_params())

    def test_different_seeds_give_different_models(self):
        clients_a = _make_clients()
        clients_b = _make_clients()
        m1, _, _ = run_federated_training(
            clients_a, rounds=5, lr=0.5, clip_norm=1.0, noise_multiplier=1.0,
            enable_dp=True, enable_secure_agg=False, fedprox_mu=0.0, seed=1,
        )
        m2, _, _ = run_federated_training(
            clients_b, rounds=5, lr=0.5, clip_norm=1.0, noise_multiplier=1.0,
            enable_dp=True, enable_secure_agg=False, fedprox_mu=0.0, seed=2,
        )
        self.assertFalse(np.allclose(m1.get_flat_params(), m2.get_flat_params()))

    def test_secure_agg_and_robust_agg_together_raises(self):
        clients = _make_clients()
        with self.assertRaises(ValueError):
            run_federated_training(
                clients, rounds=2, lr=0.5, clip_norm=1.0, noise_multiplier=1.0,
                enable_dp=True, enable_secure_agg=True, fedprox_mu=0.0, seed=1,
                aggregation_strategy="median",
            )

    def test_budget_exhaustion_halts_client_participation(self):
        from src.firewall.budget_ledger import BudgetLedger
        clients = _make_clients(n_clients=3)
        ledger = BudgetLedger([c.name for c in clients], tier="normal")
        run_federated_training(
            clients, rounds=50, lr=0.5, clip_norm=1.0, noise_multiplier=0.3,
            enable_dp=True, enable_secure_agg=False, fedprox_mu=0.0, seed=1,
            firewall=ledger,
        )
        # with only 50 rounds requested but a tight budget, at least one
        # client should have been cut off before round 50
        self.assertTrue(any(r < 50 for r in ledger.rounds_used.values()))


if __name__ == "__main__":
    unittest.main()
