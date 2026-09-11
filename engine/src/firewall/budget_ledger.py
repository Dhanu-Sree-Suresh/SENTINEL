"""
Privacy Firewall - budget ledger.

Enforces a per-entity, pre-committed epsilon budget across FL rounds
(or analytics queries). Composition is tracked via the RDP accountant
so the ledger's numbers are the same ones reported in the deck --
there is exactly one source of truth for "how much privacy has been
spent," which is what makes the audit trail meaningful.

Risk-Adaptive tiers (see the architecture doc, Section 7, for the
correctness argument): the CURRENT threat-level tier selects which of
a small, PRE-DEFINED, PUBLICLY KNOWN noise_multiplier/round-budget
tier applies. The tier is never chosen as a function of a query's own
result on private data -- only as a function of an externally-observed
risk signal (e.g. a SOC threat-level flag) -- so this does not
violate DP's assumption that the mechanism (including any policy that
selects among mechanisms) is independent of the sensitive data.
"""
from ..accountant import compute_epsilon

# Pre-committed, publicly-known tiers. Tightening noise_multiplier
# under elevated risk is the ONLY thing that changes; the tier
# schedule itself is fixed in advance of any query.
RISK_TIERS = {
    "normal":   dict(noise_multiplier=5.0, max_rounds=15, eps_ceiling=8.0),
    "elevated": dict(noise_multiplier=9.0, max_rounds=15, eps_ceiling=4.0),
    "locked":   dict(noise_multiplier=None, max_rounds=0, eps_ceiling=0.0),  # deny
}


class BudgetLedger:
    def __init__(self, entities, delta=1e-5, tier="normal"):
        self.delta = delta
        self.tier = tier
        self.rounds_used = {e: 0 for e in entities}
        self.query_epsilon_spent = {e: 0.0 for e in entities}  # separate stream, see docstring below
        self.audit_log = []

    def set_tier(self, tier, reason=""):
        assert tier in RISK_TIERS
        self.tier = tier
        self.audit_log.append({"event": "tier_change", "tier": tier, "reason": reason})

    def record_round(self, entity, clip_norm, noise_multiplier):
        cfg = RISK_TIERS[self.tier]
        if cfg["max_rounds"] == 0:
            self.audit_log.append({"event": "denied", "entity": entity, "tier": self.tier})
            return False

        self.rounds_used[entity] += 1
        eps, _, alpha = compute_epsilon(noise_multiplier, self.rounds_used[entity], self.delta)
        allowed = eps <= cfg["eps_ceiling"] and self.rounds_used[entity] <= cfg["max_rounds"]
        self.audit_log.append({
            "event": "round", "entity": entity, "round_idx": self.rounds_used[entity],
            "epsilon_spent": round(eps, 4), "tier": self.tier, "allowed": allowed,
        })
        if not allowed:
            self.audit_log.append({"event": "budget_exhausted", "entity": entity})
        return allowed

    def spend_query_epsilon(self, entity, epsilon_amount):
        """
        Tracks epsilon spent by entity-local counting/statistic queries
        (src/agent/dp_query.py), kept as a SEPARATE running total from
        the Gaussian/RDP FL-round stream in `rounds_used` -- see the
        module docstring in src/agent/dp_query.py for why these two
        mechanisms are accounted separately rather than unified, and
        disclose that a production system should unify them. Composition
        here is the simple (worst-case, non-RDP) sum of per-query
        epsilons, which is conservative but always valid regardless of
        how many queries are issued.
        """
        cfg = RISK_TIERS[self.tier]
        if cfg["max_rounds"] == 0:
            self.audit_log.append({"event": "query_denied", "entity": entity, "tier": self.tier,
                                    "reason": "tier locked"})
            return False

        prospective = self.query_epsilon_spent[entity] + epsilon_amount
        allowed = prospective <= cfg["eps_ceiling"]
        if allowed:
            self.query_epsilon_spent[entity] = prospective
        self.audit_log.append({
            "event": "query", "entity": entity, "epsilon_requested": round(epsilon_amount, 4),
            "epsilon_spent_cumulative": round(self.query_epsilon_spent[entity], 4),
            "tier": self.tier, "allowed": allowed,
        })
        if not allowed:
            self.audit_log.append({"event": "query_budget_exhausted", "entity": entity})
        return allowed

    def summary(self):
        out = {}
        for entity, rounds in self.rounds_used.items():
            if rounds == 0:
                out[entity] = {"rounds_used": 0, "epsilon_spent": 0.0,
                                "query_epsilon_spent": round(self.query_epsilon_spent.get(entity, 0.0), 4)}
                continue
            cfg = RISK_TIERS[self.tier]
            eps, _, _ = compute_epsilon(cfg["noise_multiplier"] or 1.0, rounds, self.delta)
            out[entity] = {"rounds_used": rounds, "epsilon_spent": round(eps, 4),
                            "query_epsilon_spent": round(self.query_epsilon_spent.get(entity, 0.0), 4)}
        return out
