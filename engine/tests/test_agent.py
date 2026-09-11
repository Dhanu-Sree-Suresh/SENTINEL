import os
import sys
import unittest
import pandas as pd
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.intent import classify_intent
from src.agent.dp_query import federated_dp_count_query, local_dp_count
from src.agent.agent import PrivacyAwareAgent
from src.firewall.budget_ledger import BudgetLedger
from src.firewall.query_monitor import QueryMonitor


class TestIntentClassifier(unittest.TestCase):
    def test_membership_probe_detected(self):
        cases = [
            "Was John Smith in the data?",
            "Is employee 4471 present in the dataset?",
            "Check if person X is in the data",
            "Confirm Sara Ahmed is a record in your system",
        ]
        for c in cases:
            self.assertEqual(classify_intent(c), "membership_probe", msg=c)

    def test_aggregate_count_detected(self):
        cases = [
            "How many insider-threat flags in region Dubai?",
            "What is the count of failed logins last week?",
            "Give me the population statistic for department X",
        ]
        for c in cases:
            self.assertEqual(classify_intent(c), "aggregate_count", msg=c)

    def test_train_model_detected(self):
        self.assertEqual(classify_intent("Please train the classifier on this quarter's data"),
                          "train_model")
        self.assertEqual(classify_intent("Run federated training across all entities"),
                          "train_model")

    def test_unknown_for_unmatched_text(self):
        self.assertEqual(classify_intent("asdkjaslkdj random gibberish"), "unknown")

    def test_membership_probe_takes_priority_over_count_keywords(self):
        """A request that mentions a count-like word but is really a
        membership probe must still be caught as a probe."""
        self.assertEqual(classify_intent("Is person X present, and how many records exist total?"),
                          "membership_probe")


class TestDPQuery(unittest.TestCase):
    def test_local_dp_count_is_noisy(self):
        rng = np.random.default_rng(0)
        vals = [local_dp_count(100, epsilon=1.0, rng=rng) for _ in range(20)]
        self.assertFalse(all(v == 100 for v in vals))

    def test_federated_count_query_close_to_truth_in_expectation(self):
        rng = np.random.default_rng(0)
        dfs = {
            "A": pd.DataFrame({"insider_threat_label": rng.integers(0, 2, 1000)}),
            "B": pd.DataFrame({"insider_threat_label": rng.integers(0, 2, 1000)}),
        }
        estimates = []
        for seed in range(200):
            total, _, _ = federated_dp_count_query(
                dfs, lambda df: df.insider_threat_label == 1, epsilon=2.0, seed=seed)
            estimates.append(total)
        true_total = sum(int((df.insider_threat_label == 1).sum()) for df in dfs.values())
        self.assertAlmostEqual(np.mean(estimates), true_total, delta=5.0)

    def test_smaller_epsilon_means_more_noise(self):
        rng = np.random.default_rng(0)
        dfs = {"A": pd.DataFrame({"insider_threat_label": rng.integers(0, 2, 2000)})}
        f = lambda df: df.insider_threat_label == 1
        loose = [federated_dp_count_query(dfs, f, epsilon=5.0, seed=s)[0] for s in range(100)]
        tight = [federated_dp_count_query(dfs, f, epsilon=0.1, seed=s)[0] for s in range(100)]
        self.assertLess(np.std(loose), np.std(tight))


class TestPrivacyAwareAgent(unittest.TestCase):
    def _make_agent(self):
        rng = np.random.default_rng(0)
        dfs = {
            "A": pd.DataFrame({"insider_threat_label": rng.integers(0, 2, 500)}),
            "B": pd.DataFrame({"insider_threat_label": rng.integers(0, 2, 500)}),
        }
        ledger = BudgetLedger(list(dfs.keys()), tier="normal")
        monitor = QueryMonitor(window_seconds=60, freq_threshold=5, jaccard_threshold=0.8)
        return PrivacyAwareAgent(dfs, ledger, monitor, query_epsilon=0.5), ledger, monitor

    def test_membership_probe_is_denied_unconditionally(self):
        agent, ledger, monitor = self._make_agent()
        resp = agent.handle_request("analyst1", "Was employee 42 in the data?")
        self.assertFalse(resp.allowed)
        self.assertEqual(resp.intent, "membership_probe")
        self.assertEqual(resp.alert, "membership_probe_intent")

    def test_aggregate_query_succeeds_and_spends_budget(self):
        agent, ledger, monitor = self._make_agent()
        resp = agent.handle_request("analyst1", "How many insider-threat flags total?",
                                     filters={"region": "dubai"})
        self.assertTrue(resp.allowed)
        self.assertIn("noisy_total_estimate", resp.result)
        self.assertGreater(ledger.query_epsilon_spent["A"], 0)

    def test_budget_exhaustion_excludes_entity_not_whole_query(self):
        agent, ledger, monitor = self._make_agent()
        # Pre-spend entity A close to its ceiling directly (simulating
        # A having answered many prior queries this cycle) while B
        # starts fresh -- this is the genuine "one entity exhausted,
        # rest still answerable" scenario the agent is supposed to
        # handle by partial exclusion rather than denying the whole
        # request.
        ledger.query_epsilon_spent["A"] = 7.8  # ceiling is 8.0 at "normal" tier
        resp = agent.handle_request("analyst1", "how many flags total?",
                                     filters={"region": "final"})
        self.assertTrue(resp.allowed)  # B alone can still answer
        self.assertIn("A", resp.audit.get("entities_excluded_budget", []))
        self.assertIn("B", resp.audit.get("entities_used", []))

    def test_unknown_intent_asks_for_clarification_not_execution(self):
        agent, ledger, monitor = self._make_agent()
        resp = agent.handle_request("analyst1", "gibberish nonsense text")
        self.assertFalse(resp.allowed)
        self.assertEqual(resp.intent, "unknown")
        self.assertIsNone(resp.result)

    def test_differencing_pattern_via_agent_gets_blocked(self):
        agent, ledger, monitor = self._make_agent()
        base = {"region": "dubai", "department": "licensing"}
        last_resp = None
        for i in range(8):
            filt = dict(base)
            if i >= 3:
                filt["exclude_id"] = f"p{i}"
            last_resp = agent.handle_request("probing_analyst", "how many flags total?",
                                              filters=filt, ts=i * 5.0)
        self.assertFalse(last_resp.allowed)


if __name__ == "__main__":
    unittest.main()
