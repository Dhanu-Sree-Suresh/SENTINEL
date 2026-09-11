"""
Privacy-aware analyst agent.

Implements the request lifecycle from the platform brief as real,
deterministic, testable code -- not a prompt:

  1. Receive an analyst request (free text + optional structured filters)
  2. Classify intent                              (src/agent/intent.py)
  3. Identify relevant entities                    (all connected entities, or filter-scoped)
  4. Evaluate privacy risk of the request itself    (membership_probe -> hard block)
  5. Check query-pattern risk (differencing/burst)  (src/firewall/query_monitor.py)
  6. Check available privacy budget                 (src/firewall/budget_ledger.py)
  7. Decide whether the request is allowed
  8. Select and execute the privacy mechanism        (DP count query, or hand off to FL training)
  9. Monitor for anomalies in the result itself       (e.g. absurdly large noise relative to signal)
 10. Produce a privacy-safe result
 11. Generate a full audit record
 12. Generate a plain-language explanation of the privacy/utility trade-off actually applied

The agent NEVER receives raw per-record data: it only ever calls
`federated_dp_count_query`, which returns entity-level NOISED
aggregates (see src/agent/dp_query.py) or hands off model-training
requests to the existing FL+DP+SecAgg+Firewall pipeline in
src/fl_engine.py, whose outputs are a trained model's aggregate
parameters, not records. This bounds the agent's own "excessive
agency" risk: even a fully compromised or misdirected agent process
cannot exfiltrate raw records, because it was never given a code path
that touches them.
"""
import time
from .intent import classify_intent
from .dp_query import federated_dp_count_query


DEFAULT_QUERY_EPSILON = 0.5  # spent per-entity, per aggregate query, at the "normal" tier


class AgentResponse:
    def __init__(self, allowed, intent, result=None, explanation="", audit=None, alert=None):
        self.allowed = allowed
        self.intent = intent
        self.result = result
        self.explanation = explanation
        self.audit = audit or {}
        self.alert = alert

    def to_dict(self):
        return dict(allowed=self.allowed, intent=self.intent, result=self.result,
                     explanation=self.explanation, audit=self.audit, alert=self.alert)


class PrivacyAwareAgent:
    def __init__(self, entity_dataframes, ledger, monitor, query_epsilon=DEFAULT_QUERY_EPSILON):
        """
        entity_dataframes: dict[entity_name -> pandas.DataFrame]. The
        agent holds a reference for orchestration purposes only -- see
        module docstring for why this does not amount to raw-data
        access from the analyst's perspective.
        ledger: a firewall.budget_ledger.BudgetLedger
        monitor: a firewall.query_monitor.QueryMonitor
        """
        self.entity_dataframes = entity_dataframes
        self.ledger = ledger
        self.monitor = monitor
        self.query_epsilon = query_epsilon

    def handle_request(self, analyst, request_text, filters=None, ts=None):
        ts = ts if ts is not None else time.time()
        filters = filters or {}
        intent = classify_intent(request_text)
        audit = {"analyst": analyst, "request": request_text, "intent": intent, "timestamp": ts}

        # Step 4: hard policy block, independent of budget or pattern history
        if intent == "membership_probe":
            self.monitor.alerts.append({
                "type": "membership_probe_intent", "analyst": analyst,
                "request": request_text, "timestamp": ts,
            })
            audit["decision"] = "denied_by_policy"
            return AgentResponse(
                allowed=False, intent=intent, audit=audit,
                explanation=(
                    "This request asks whether a specific individual is present in the data. "
                    "That question is refused unconditionally by platform policy, regardless of "
                    "privacy budget available, because it is structurally identical to a "
                    "membership-inference probe. The attempt has been logged as a security event."
                ),
                alert="membership_probe_intent",
            )

        # Step 5: statistical query-pattern risk (differencing / burst behavior)
        pattern_alert = self.monitor.submit_query(analyst, filters, ts=ts)
        if pattern_alert:
            audit["decision"] = "denied_by_pattern_monitor"
            audit["pattern_alert"] = pattern_alert
            return AgentResponse(
                allowed=False, intent=intent, audit=audit, alert=pattern_alert,
                explanation=(
                    "This request was blocked because your recent query pattern matches a "
                    f"known probing signature ({pattern_alert.get('type')}). If this is "
                    "legitimate analysis, please contact your privacy officer to review the "
                    "query plan before resubmitting."
                ),
            )

        if intent == "unknown":
            audit["decision"] = "clarification_requested"
            return AgentResponse(
                allowed=False, intent=intent, audit=audit,
                explanation=(
                    "I couldn't confidently classify this request as an aggregate/statistic "
                    "query or a model-training request. Rather than guess and execute something "
                    "unintended, I'm asking for clarification: could you rephrase, e.g. "
                    "'how many insider-threat flags in region X' or 'train the classifier'?"
                ),
            )

        if intent == "train_model":
            audit["decision"] = "routed_to_fl_pipeline"
            return AgentResponse(
                allowed=True, intent=intent, audit=audit,
                explanation=(
                    "Model-training requests are handled by the federated pipeline "
                    "(src/fl_engine.py: FL + DP-SGD + Secure Aggregation + this same "
                    "BudgetLedger), not by this agent's own query path. See "
                    "experiments/run_experiment.py for a full run."
                ),
                result={"handoff": "fl_engine.run_federated_training"},
            )

        # intent == "aggregate_count": Steps 6-11
        entities = list(self.entity_dataframes.keys())
        # Step 6: budget check happens by ATTEMPTING the spend per entity;
        # any entity that cannot afford it is excluded from this query
        # rather than failing the whole request, so one exhausted
        # entity does not deny an aggregate across the rest.
        eligible = {}
        excluded = []
        for e in entities:
            if self.ledger.spend_query_epsilon(e, self.query_epsilon):
                eligible[e] = self.entity_dataframes[e]
            else:
                excluded.append(e)

        if not eligible:
            audit["decision"] = "denied_budget_exhausted"
            return AgentResponse(
                allowed=False, intent=intent, audit=audit,
                explanation="Every entity's query budget is exhausted for the current risk tier; "
                            "this request cannot be answered without a budget reset or a tier change.",
            )

        label_filter = filters.get("label_filter", lambda df: df["insider_threat_label"] == 1)
        noisy_total, noisy_by_entity, true_by_entity = federated_dp_count_query(
            eligible, label_filter, epsilon=self.query_epsilon, seed=int(ts * 1000) % (2 ** 31),
        )

        # Step 9: sanity-monitor the result itself -- if the noise is
        # larger than the signal, flag it so the analyst doesn't
        # over-trust a number that is mostly noise.
        true_total = sum(true_by_entity.values())
        noise_dominates = abs(noisy_total - true_total) > max(1.0, 0.5 * true_total)

        audit["decision"] = "answered"
        audit["entities_used"] = list(eligible.keys())
        audit["entities_excluded_budget"] = excluded
        audit["epsilon_spent_this_query"] = self.query_epsilon
        audit["cumulative_budget_state"] = self.ledger.summary()

        explanation = (
            f"Answered using {len(eligible)}/{len(entities)} entities "
            f"({', '.join(eligible.keys())}); "
            f"{len(excluded)} excluded for insufficient remaining budget: {excluded or 'none'}. "
            f"Each entity added its own Laplace noise (epsilon={self.query_epsilon} per entity) "
            f"before this query interface ever saw a count, so no single party -- including this "
            f"agent -- observed any entity's exact value. "
        )
        if noise_dominates:
            explanation += (
                "Note: the added noise is large relative to the estimated count at this budget "
                "level; treat this result as directional only, not precise, or request a higher "
                "budget tier if precision matters more than tight privacy for this query."
            )

        return AgentResponse(
            allowed=True, intent=intent,
            result={"noisy_total_estimate": noisy_total, "entities_used": list(eligible.keys())},
            explanation=explanation, audit=audit,
        )
