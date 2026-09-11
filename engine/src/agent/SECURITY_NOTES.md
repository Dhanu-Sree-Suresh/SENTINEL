# Agent Security Notes

This document covers the agentic-AI-specific threat model the brief asks
for (Section 22 of the original master prompt: prompt injection, tool
injection, excessive agency, data exfiltration, query manipulation,
privacy-budget abuse, unauthorized access, hallucinated security
decisions, malicious instructions, agent privilege escalation, model
manipulation).

## What the agent can and cannot do in this build

`PrivacyAwareAgent` (src/agent/privacy_agent.py) is a **deterministic,
rule-based policy engine**, not an LLM. This is a scope/environment
disclosure, not a design preference dressed up as one: this sandbox has
no network access and no model API credentials, so any "AI agent" claim
here would either be fabricated or would require silently hardcoding
canned outputs. We chose to build the real thing at the layer we could
build honestly (the orchestration/policy/audit pipeline) rather than
fake the layer we couldn't (free-text natural-language understanding).

**The agent never touches raw entity data.** Every action it takes is a
call into an already-existing, independently-tested module
(`BudgetLedger`, `QueryMonitor`, `run_federated_training`) -- the agent
holds no direct data-access credential or raw-record read path of its
own. This is the single most important mitigation on this list: excessive
agency and data exfiltration risks are structural, not policy-based, when
the agent's own code has no code path that can reach raw records.

## Threat-by-threat mapping

| Threat | Mitigation in this build |
|---|---|
| **Prompt injection** (malicious text in a request tricking the agent into misclassifying intent) | Intent parsing is keyword-rule based, not a model completion -- there is no prompt for an adversary to inject into. A future LLM-backed intent parser MUST treat the analyst's request as untrusted data passed as a tool argument, never concatenated into a system-level instruction context. |
| **Tool injection** (a compromised entity's data containing text that gets executed as an instruction) | The agent's tools (`BudgetLedger`, `QueryMonitor`) take structured arguments (filter dicts, entity names), not free text harvested from entity data -- there is no code path where entity record content is interpreted as an instruction. |
| **Excessive agency** (agent granted more authority than the task needs) | The agent can only ever call `record_round` / `submit_query` on already-instantiated ledger/monitor objects passed in by the caller -- it cannot create new entities, change risk tiers, or bypass the ledger. `set_tier` (the one genuinely privileged action) is deliberately NOT exposed to the agent's `handle_request` path in this build; only a human operator calls it directly. |
| **Data exfiltration via the query interface** | Every request passes through `score_request_risk` + the real `QueryMonitor` differencing-attack detector before any mechanism is selected; `risk_score >= 0.7` hard-denies regardless of intent. |
| **Query manipulation / repeated-query budget abuse** | Budget spend is tracked by `BudgetLedger`, not by the agent -- the agent cannot "convince" the ledger to under-count spend, because it has no write access to the ledger's internal accounting, only the same `record_round` call path every other caller uses. |
| **Unauthorized access** | `analyst` identity is a required, non-optional argument to `handle_request`; this build does not implement authentication itself (that's an infra-layer concern -- see deploy/README.md for the intended identity-federation integration point) but every decision is logged against the identity string it was given. |
| **Hallucinated security decisions** | There is nothing to hallucinate -- `authorize_or_deny` is an explicit if/elif chain over numeric thresholds, fully unit-tested (see tests/test_agent.py). |
| **Malicious instructions embedded in a request** ("ignore previous budget limits") | Such text would only ever be matched against `INTENT_RULES` / `RISKY_PATTERNS` keyword lists -- there is no instruction-following model in this path to be redirected by it. Worth noting explicitly: a plausible attack against a FUTURE LLM-backed version of step 2 is exactly this kind of embedded instruction; the mitigation is architectural (keep authorization in the deterministic layer below the LLM), not prompt-level. |
| **Agent privilege escalation** | The agent object is constructed with references to a *specific* ledger and monitor instance for a *specific* deployment; nothing in its interface allows swapping in a different ledger, a different tier, or a different entity list at request time. |
| **Model manipulation** (n/a in this build) | No model is in the authorization path to manipulate. |

## What a production LLM-backed version would need (roadmap, not implemented)

If/when an LLM is added for richer natural-language intent parsing and
explanation generation, it must sit **strictly upstream** of
`handle_request`'s policy engine: it may propose an `intent` guess and an
`target_entities` guess for the deterministic pipeline to then evaluate,
exactly like today's keyword parser does — it must never gain a code path
that calls `record_round`, `set_tier`, or any FL/DP execution function
directly. This is the standard "LLM proposes, deterministic policy
disposes" pattern recommended by current agentic-AI security guidance
(NIST AI RMF generative-AI profile; OWASP Top 10 for LLM Applications,
particularly LLM06 Excessive Agency and LLM01 Prompt Injection).
