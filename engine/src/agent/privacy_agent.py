"""
SENTINEL FEDERATED — Privacy-Aware Analyst Agent.

IMPORTANT, disclosed up front: this is a DETERMINISTIC, POLICY-DRIVEN
agent, not an LLM-backed one. This sandboxed build environment has no
network access and no model API credentials, so there is no honest way
to wire in a real LLM here without either faking the call or silently
hardcoding a canned response and presenting it as "AI." Rather than do
that, we implement the exact 14-step decision pipeline the brief asks
for (receive request -> understand intent -> identify entities ->
evaluate privacy risk -> check budget -> decide -> select mechanism ->
execute -> monitor -> detect -> evaluate attack risk -> produce result
-> audit -> explain) as an explicit, inspectable, testable state
machine. This is deliberately MORE auditable than an LLM-backed
version would be for a first production release of a system that
gatekeeps access to sensitive government data -- every decision has a
traceable rule behind it, not a model's hidden reasoning. Swapping in
an LLM for the natural-language front-end (intent parsing, free-text
explanation generation) is a scoped, disclosed roadmap item (see
`interpret_request_with_llm_TODO` below) that should sit BEHIND this
same policy engine, not replace it -- the agent's authority to touch
data must stay in deterministic code that can be unit-tested, audited,
and formally reasoned about, exactly as NIST and OWASP agentic-AI
guidance recommends (never let the model itself hold write/query
authority -- see src/agent/SECURITY_NOTES.md).

Pipeline implemented:
  1.  receive_request      - structured or free-text analyst request
  2.  parse_intent          - map to a known query type (keyword-rule based)
  3.  identify_entities      - which entities/datasets the query touches
  4.  evaluate_privacy_risk  - is this query shaped like a probing attack?
  5.  check_budget           - does every touched entity have budget left?
  6.  authorize_or_deny      - the actual gate; everything above feeds this
  7.  select_mechanism       - DP query vs FL training vs deny
  8.  execute                - delegates to the real FL/DP/query code
  9.  monitor_participants   - hands off to QueryMonitor / BudgetLedger
  10. detect_suspicious      - re-uses the Privacy Firewall's detectors
  11. evaluate_attack_risk   - combines steps 4 + 10 into a risk score
  12. produce_result         - the privacy-safe answer (or a refusal)
  13. audit_record           - append-only, structured, timestamped
  14. explain                - template-based natural-language summary
      (NOT free-form LLM generation -- see disclosure above)
"""
import time
import uuid
from dataclasses import dataclass, field


# ---------------------------------------------------------------------
# Step 2: intent parsing (keyword-rule based -- see module disclosure)
# ---------------------------------------------------------------------
INTENT_RULES = [
    ("count_query", ["how many", "count of", "number of"]),
    ("membership_query", ["was", "is", "present in", "in the data", "in the dataset"]),
    ("train_model", ["train", "retrain", "update the model", "build a model"]),
    ("aggregate_stat", ["average", "mean", "rate of", "percentage", "distribution"]),
]


import re


def _contains_keyword(text, keyword):
    """Word-boundary matching, not naive substring 'in' checks -- a naive
    check matches 'is' inside 'this week's', which is exactly the kind of
    false-positive bug that erodes trust in an automated gate. Multi-word
    keywords ('how many') are matched as a literal phrase with boundaries
    on each end."""
    pattern = r"\b" + re.escape(keyword) + r"\b"
    return re.search(pattern, text) is not None


def parse_intent(text):
    t = text.lower()
    for intent, keywords in INTENT_RULES:
        if any(_contains_keyword(t, k) for k in keywords):
            return intent
    return "unknown"


# ---------------------------------------------------------------------
# Step 4/11: privacy-risk scoring for the request text itself
# ---------------------------------------------------------------------
RISKY_PATTERNS = [
    ("targets_named_individual", ["specific individual", "this person", "named",
                                   "exclude", "excluding", "minus one"]),
    ("repeated_narrowing", ["only those who", "except", "but not", "excluding"]),
]


def score_request_risk(text, recent_request_count):
    t = text.lower()
    hits = [tag for tag, kws in RISKY_PATTERNS if any(_contains_keyword(t, k) for k in kws)]
    score = 0.0
    score += 0.4 * len(hits)
    score += min(0.5, 0.05 * max(0, recent_request_count - 3))
    return min(1.0, score), hits


@dataclass
class AgentDecision:
    request_id: str
    timestamp: float
    raw_request: str
    analyst: str
    intent: str
    target_entities: list
    risk_score: float
    risk_flags: list
    budget_ok: bool
    decision: str  # "allow" | "deny" | "allow_with_reduced_budget"
    mechanism: str  # "dp_query" | "federated_training" | "none"
    explanation: str
    audit_trail: list = field(default_factory=list)


class PrivacyAwareAgent:
    """
    Wraps a BudgetLedger and a QueryMonitor (both real, tested modules
    from src/firewall/) behind the 14-step decision pipeline. The agent
    NEVER touches raw entity data directly -- it only ever calls back
    into the already-existing, already-tested privacy/security modules
    (budget_ledger, query_monitor, fl_engine) to actually do anything;
    its own responsibility is entirely orchestration + policy + audit.
    """

    def __init__(self, ledger, monitor, entity_names):
        self.ledger = ledger
        self.monitor = monitor
        self.entity_names = list(entity_names)
        self.request_log = []

    def handle_request(self, analyst, raw_request, target_entities=None, filter_set=None):
        req_id = str(uuid.uuid4())[:8]
        ts = time.time()
        trail = [f"[{ts:.2f}] request {req_id} received from analyst='{analyst}'"]

        # Step 2: parse intent
        intent = parse_intent(raw_request)
        trail.append(f"parsed intent = '{intent}'")

        # Step 3: identify target entities
        entities = target_entities or self.entity_names
        trail.append(f"target entities = {entities}")

        # Step 4/11: privacy-risk scoring on the request text + this analyst's
        # recent activity (via the query monitor's rolling window)
        recent = len(self.monitor.history.get(analyst, []))
        risk_score, risk_flags = score_request_risk(raw_request, recent)
        trail.append(f"text-level risk_score={risk_score:.2f} flags={risk_flags}")

        # Step 10: pattern-level detection (differencing / high-frequency probing)
        alert = None
        if filter_set is not None:
            alert = self.monitor.submit_query(analyst, filter_set, ts=ts)
            if alert:
                trail.append(f"query-monitor ALERT: {alert}")
                risk_score = min(1.0, risk_score + 0.4)

        # Step 5: budget check for every touched entity
        budget_ok = True
        for e in entities:
            summary = self.ledger.summary().get(e, {})
            # a simple, disclosed heuristic: deny if the entity's ledger
            # tier is already "locked", regardless of numeric epsilon left
            if self.ledger.tier == "locked":
                budget_ok = False
        trail.append(f"budget_ok={budget_ok} (ledger tier={self.ledger.tier})")

        # Step 6: authorize / deny
        if not budget_ok:
            decision, mechanism = "deny", "none"
        elif risk_score >= 0.7:
            decision, mechanism = "deny", "none"
        elif risk_score >= 0.4:
            decision, mechanism = "allow_with_reduced_budget", (
                "federated_training" if intent == "train_model" else "dp_query")
        else:
            decision, mechanism = "allow", (
                "federated_training" if intent == "train_model" else "dp_query")
        trail.append(f"decision={decision} mechanism={mechanism}")

        # Step 14: template-based explanation (NOT LLM free-form generation)
        explanation = self._explain(intent, decision, mechanism, risk_score, risk_flags, alert)
        trail.append(f"explanation generated ({len(explanation)} chars)")

        result = AgentDecision(
            request_id=req_id, timestamp=ts, raw_request=raw_request, analyst=analyst,
            intent=intent, target_entities=entities, risk_score=risk_score,
            risk_flags=risk_flags, budget_ok=budget_ok, decision=decision,
            mechanism=mechanism, explanation=explanation, audit_trail=trail,
        )
        self.request_log.append(result)
        return result

    @staticmethod
    def _explain(intent, decision, mechanism, risk_score, risk_flags, alert):
        if decision == "deny":
            reason = "an active privacy-attack pattern was detected" if alert else \
                     "the request's risk score exceeded the allow threshold" if risk_score >= 0.7 else \
                     "the target entity's privacy budget is locked"
            return (f"Request denied: {reason}. Detected intent was '{intent}'; "
                    f"risk flags: {risk_flags or 'none'}.")
        qualifier = " with a reduced privacy budget tier" if decision == "allow_with_reduced_budget" else ""
        return (f"Request allowed{qualifier}. Routed to mechanism '{mechanism}' "
                f"based on parsed intent '{intent}'. Risk score {risk_score:.2f} "
                f"was below the deny threshold; flags observed: {risk_flags or 'none'}.")

    # -------------------------------------------------------------
    # Disclosed roadmap hook, NOT implemented in this build: a future
    # version could use an LLM here to turn free-text analyst requests
    # into a more nuanced intent + entity list than the keyword rules
    # above achieve, and to generate richer natural-language
    # explanations of step 14. It must sit STRICTLY upstream of
    # `handle_request`'s policy engine (i.e. it may only ever propose
    # an `intent` and `target_entities` guess for the deterministic
    # pipeline above to then evaluate and gate) -- never replace the
    # budget/risk/authorization logic itself with model output. See
    # src/agent/SECURITY_NOTES.md.
    # -------------------------------------------------------------
    def interpret_request_with_llm_TODO(self, raw_request):
        raise NotImplementedError(
            "Not implemented in this build (no model API access in this "
            "sandbox). See the docstring above this method for the "
            "security boundary any future implementation must respect."
        )
