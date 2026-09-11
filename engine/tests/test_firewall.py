import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.firewall.budget_ledger import BudgetLedger, RISK_TIERS
from src.firewall.query_monitor import QueryMonitor


class TestBudgetLedger(unittest.TestCase):
    def test_locked_tier_denies_everything(self):
        ledger = BudgetLedger(["A", "B"], tier="locked")
        allowed = ledger.record_round("A", clip_norm=1.0, noise_multiplier=2.0)
        self.assertFalse(allowed)

    def test_budget_exhausts_eventually_under_normal_tier(self):
        """With enough rounds at a low enough noise multiplier, the ceiling
        MUST eventually trigger -- a ledger that never denies anything isn't
        enforcing a budget, it's just logging."""
        ledger = BudgetLedger(["A"], tier="normal")
        results = [ledger.record_round("A", clip_norm=1.0, noise_multiplier=0.5)
                   for _ in range(50)]
        self.assertIn(False, results, "ledger never denied a round -- budget not enforced")

    def test_tighter_tier_exhausts_sooner(self):
        ledger_normal = BudgetLedger(["A"], tier="normal")
        ledger_elevated = BudgetLedger(["A"], tier="elevated")

        def rounds_until_denied(ledger, sigma):
            for i in range(200):
                if not ledger.record_round("A", clip_norm=1.0, noise_multiplier=sigma):
                    return i
            return 200

        n_normal = rounds_until_denied(ledger_normal, sigma=1.0)
        n_elevated = rounds_until_denied(ledger_elevated, sigma=1.0)
        self.assertLessEqual(n_elevated, n_normal)

    def test_audit_log_records_every_event(self):
        ledger = BudgetLedger(["A"], tier="normal")
        ledger.record_round("A", clip_norm=1.0, noise_multiplier=5.0)
        ledger.record_round("A", clip_norm=1.0, noise_multiplier=5.0)
        self.assertEqual(len([e for e in ledger.audit_log if e["event"] == "round"]), 2)

    def test_tier_change_is_logged(self):
        ledger = BudgetLedger(["A"], tier="normal")
        ledger.set_tier("elevated", reason="threat level raised")
        self.assertEqual(ledger.tier, "elevated")
        self.assertTrue(any(e["event"] == "tier_change" for e in ledger.audit_log))


class TestQueryMonitor(unittest.TestCase):
    def test_differencing_pattern_detected(self):
        qm = QueryMonitor(window_seconds=60, freq_threshold=5, jaccard_threshold=0.8)
        alerts = []
        base = {"region": "dubai", "department": "licensing"}
        for i in range(8):
            filt = dict(base)
            if i >= 3:
                filt["exclude_id"] = f"person_{i}"
            a = qm.submit_query("analyst_x", filt, ts=i * 5.0)
            if a:
                alerts.append(a)
        self.assertGreater(len(alerts), 0)

    def test_no_false_alarm_on_sparse_unrelated_queries(self):
        qm = QueryMonitor(window_seconds=60, freq_threshold=5, jaccard_threshold=0.8)
        alerts = []
        for i in range(3):
            a = qm.submit_query("analyst_y", {"region": f"region_{i}", "dept": f"dept_{i}"},
                                 ts=i * 40.0)  # spaced well outside the window, distinct filters
            if a:
                alerts.append(a)
        self.assertEqual(len(alerts), 0)

    def test_same_filter_keys_different_values_not_flagged_as_differencing(self):
        """Regression test for a real bug found via the what-if grid:
        frozenset(dict) captures only KEYS, so queries with identical
        filter keys but completely different values (e.g. different
        regions each time -- ordinary, non-suspicious analyst behavior)
        were incorrectly treated as ~100% similar and flagged as a
        differencing attack. Same keys, genuinely different content,
        must NOT trigger the differencing-pattern detector."""
        qm = QueryMonitor(window_seconds=60, freq_threshold=10, jaccard_threshold=0.8)
        differencing_alerts = []
        for i in range(6):
            filt = {"region": f"region_{i}", "department": f"dept_{i}", "metric": f"m{i}"}
            alert = qm.submit_query("normal_analyst", filt, ts=i * 5.0)
            if alert and "differencing_pattern" in alert.get("type", ""):
                differencing_alerts.append(alert)
        self.assertEqual(len(differencing_alerts), 0)

    def test_identical_filter_content_repeated_is_flagged(self):
        """Sanity check in the other direction: truly repeated identical
        queries (same keys AND same values) should still be flagged as
        high similarity -- the fix must not become too lenient."""
        qm = QueryMonitor(window_seconds=60, freq_threshold=10, jaccard_threshold=0.8)
        last_alert = None
        for i in range(5):
            alert = qm.submit_query("repeat_analyst", {"region": "dubai", "dept": "licensing"},
                                     ts=i * 5.0)
            if alert:
                last_alert = alert
        self.assertIsNotNone(last_alert)
        self.assertIn("differencing_pattern", last_alert.get("type", ""))
        self.assertAlmostEqual(last_alert["max_similarity"], 1.0)


if __name__ == "__main__":
    unittest.main()
