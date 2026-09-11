"""
Privacy Firewall - query pattern monitor.

Detects the operational SIGNATURE of a membership-inference /
differencing-attack campaign against the analytics query interface:
a burst of near-identical queries that each narrow the target
population by one record (the classic "query the group, then query
the group minus one person" differencing pattern), or an unusually
high query rate from a single analyst identity in a short window.

This is deliberately simple (rolling-window frequency + Jaccard
similarity of query filter-sets) -- the point is to show that privacy
attacks generate detectable SOC-style telemetry, not to build a
research-grade anomaly detector.
"""
import time
from collections import deque, defaultdict


class QueryMonitor:
    def __init__(self, window_seconds=60, freq_threshold=5, jaccard_threshold=0.65):
        """
        jaccard_threshold default derived empirically (see
        experiments/run_whatif_grid.py's query-detection grid), not
        picked arbitrarily: for a classic differencing attack where an
        analyst holds `k` filter dimensions constant and adds one
        `exclude_id` field, similarity between consecutive probes is
        `k / (k+1)` under the (now bug-fixed, see the query_monitor
        docstring below) key-value-pair Jaccard metric. With as few as
        2 constant base dimensions that's only 0.667 -- a default of
        0.8 (a common textbook default) is too strict and MISSES this
        exact attack shape via the similarity detector alone (though
        the frequency detector still catches it as a backstop, which
        is why the platform runs both). 0.65 catches the 2-constant-
        dimension case while still requiring genuine, repeated overlap
        rather than flagging on any coincidental partial match.
        """
        self.window_seconds = window_seconds
        self.freq_threshold = freq_threshold
        self.jaccard_threshold = jaccard_threshold
        self.history = defaultdict(deque)  # analyst -> deque[(ts, filter_frozenset)]
        self.alerts = []

    @staticmethod
    def _jaccard(a, b):
        if not a and not b:
            return 1.0
        return len(a & b) / max(1, len(a | b))

    def submit_query(self, analyst, filter_set, ts=None):
        ts = ts if ts is not None else time.time()
        # BUG FIX (found via the what-if grid's burst-query scenario):
        # frozenset(dict) iterates only the dict's KEYS, not its
        # key-value pairs -- so two queries with identical filter
        # *keys* but completely different *values* were being treated
        # as 100% similar, firing the differencing-pattern detector on
        # completely unrelated queries. frozenset(dict.items()) is the
        # correct way to capture the actual filter content.
        q = frozenset(filter_set.items())
        hist = self.history[analyst]
        hist.append((ts, q))
        while hist and ts - hist[0][0] > self.window_seconds:
            hist.popleft()

        alert = None
        if len(hist) >= self.freq_threshold:
            alert = {"type": "high_frequency", "analyst": analyst,
                      "count": len(hist), "window_s": self.window_seconds}

        if len(hist) >= 2:
            sims = [self._jaccard(hist[-1][1], h[1]) for h in list(hist)[:-1]]
            if max(sims) >= self.jaccard_threshold and len(hist) >= 3:
                alert = alert or {}
                prior_type = alert.get("type")
                alert["type"] = f"{prior_type}+differencing_pattern" if prior_type else "differencing_pattern"
                alert["analyst"] = analyst
                alert["max_similarity"] = round(max(sims), 3)

        if alert:
            alert["timestamp"] = ts
            self.alerts.append(alert)
        return alert
