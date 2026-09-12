# Threat Model — SENTINEL · PPA-GOV

## 1. Government Collaborative Analytics Use Case

SENTINEL models five synthetic government entities — HR/identity,
licensing, critical infrastructure, health services, and digital services
(`src/lib/results.ts: DEFAULT_ENTITIES`) — each holding its own
insider-threat-relevant records. Individually, these datasets could reveal
sensitive information about government personnel, infrastructure and
operational activity if pooled or leaked.

Insider-threat patterns, however, are rare within any single entity
(~4% positive rate) and benefit from cross-entity signal. SENTINEL enables
these entities to collaboratively train an insider-threat classifier and
compute population statistics without centralising their raw records.

**Core principle:**
Entities jointly learn insider-threat patterns while raw records remain
inside their own security boundaries.

## 2. Why Ordinary Centralised Analytics Is Not Sufficient

A traditional architecture would require participating entities to send
their records to a central repository. This creates several problems,
directly motivating SENTINEL's design:

- A central repository becomes a high-value target for attackers.
- A single breach could expose information belonging to multiple entities.
- Entities lose direct control over their raw data.
- Centralisation increases the consequences of insider misuse or
  compromised credentials — ironic, given the use case is detecting
  insider threats.
- Data-sharing arrangements introduce additional governance and privacy
  considerations, and cross-border/cross-entity transfers may trigger
  additional compliance requirements (see `compliance.md`, `uae-context.md`).

SENTINEL instead keeps raw records within each entity and shares only
protected computational outputs — clipped/noised gradients, secure
aggregates, and policy-governed query answers.

## 3. Assets to Protect

| Asset | Description | Protection Objectives |
|-------|-------------|-------------------------|
| **Entity records** | Synthetic per-entity insider-threat-relevant records (~5.5k–7.2k rows per entity) | Confidentiality, locality — never centralised |
| **Individual-level information** | Attributes that could identify a specific synthetic individual (age, region, risk flag, etc.) | Minimise individual-level inference from any query or model output |
| **ML models and model updates** | Local and global insider-threat classifiers; per-round gradient updates crossing the entity boundary | Protection against leakage (DP-SGD) or manipulation (robust aggregation) |
| **Privacy budget and ledger** | Each entity's remaining ε (`DEFAULT_ENTITIES: budget`) and its expenditure history | Protection from unauthorised or excessive draw-down |
| **Audit trail** | Queries, decisions, training rounds, attack events (`/audit`) | Integrity and traceability for investigation |
| **Control-plane infrastructure** | The React/TanStack Start app itself, its (currently disabled) auth layer | Availability, integrity of the policy/monitoring layer itself |

**Overall protection objective:** Preserve the confidentiality, integrity,
privacy, availability and accountability of the collaborative analytics
process — in this prototype, over synthetic data, as a demonstration of
the control-plane pattern.

## 4. Stakeholders

| Stakeholder | Role / Interest |
|-------------|-------------------|
| Government entities (A–E) | Retain control of sensitive data while gaining collaborative intelligence |
| SOC analysts | Monitor `/monitor`, `/threat`; investigate alerts |
| Security analysts | Run `/attacklab` scenarios; assess residual risk |
| Privacy officers | Track `/ledger` budget spend; review `/policy` |
| ML / security engineers | Maintain `/federated`, `/pipeline`, `/ml` |
| Federation administrator | Connect/disconnect entities via `/infrastructure` |
| Auditors | Review `/audit` and `/decisions` trails |

## 5. Trust Model

### Trusted
- Each entity's local execution environment: its own synthetic records,
  local training, and local DP-SGD noising happen before anything leaves
  the entity.

### Partially Trusted
- The SENTINEL control plane (policy engine, ledger, query monitor, kill-
  chain monitor, audit log). It coordinates the collaborative process but
  is not assumed trustworthy enough to see individual model updates.

### Not Trusted With Individual Updates
- The secure aggregator. The architecture assumes it may be curious or
  compromised, and relies on secure aggregation (pairwise masking) so it
  only ever observes summed updates.

### Potentially Malicious (modeled in `/attacklab` and entity reputation)
- A compromised or malicious entity sending poisoned updates (label flip,
  10× scale, collusion)
- A malicious or careless analyst issuing individual-level, repeated, or
  rare-subgroup-targeting queries
- An attacker attempting gradient inversion on an intercepted (non-DP)
  update
- An attacker attempting a differencing attack across two similar queries

### Out of Scope for This Prototype
- Real identity compromise or credential theft (auth is off by default —
  there is no real credential to steal in this build).
- A fully compromised entity endpoint that already has legitimate
  plaintext access to its own raw data — no privacy technology protects
  against an administrator who already has legitimate local access.

## 6. Threat Actors and Threats (as Modeled in `/attacklab`)

| Threat Actor | Threat | Scenario in `/attacklab` | Potential Impact |
|---------------|---------|-----------------------------|---------------------|
| Privacy attacker (analyst-side) | Membership inference | "Membership inference" | Individual-level disclosure (modest advantage even unprotected — see `limitations.md`) |
| Attacker intercepting an update | Gradient inversion | "Gradient inversion" | Near-exact batch reconstruction if DP is off (cosine ≈ 1.0); collapses under DP (≈ 0.0003) |
| Analyst issuing crafted query pairs | Differencing attack | "Differencing attack" | Isolates one individual via two near-identical aggregate queries |
| Analyst targeting a small group | Rare subgroup reconstruction | "Rare subgroup reconstruction" | Near-identification via a tiny-n aggregate release |
| Analyst automating queries | Repeated query attack | "Repeated query attack" | Averages out noise across many releases of the same query |
| Compromised/malicious entity | Model poisoning | "Model poisoning" | Degrades global model utility (mitigated by robust aggregation, not by secure aggregation — see trade-off in `limitations.md`) |
| Sybil / colluding entities | Coordinated poisoning (2-of-5) | Poisoning condition `2/5 collude` | Larger, harder-to-detect degradation than a single attacker |
| Privileged attacker | Audit-log manipulation | *(not separately modeled — flagged as a production gap)* | Loss of accountability |

## 7. Attack Assumptions

The system assumes that:

1. Raw entity records must not be centrally collected.
2. The control plane may itself be curious or, in a real deployment, be
   the target of compromise.
3. Individual model updates can contain information about local training
   data (demonstrated directly via gradient inversion).
4. The final trained model can also leak information (demonstrated via
   membership inference).
5. Some federation participants may be compromised or malicious
   (demonstrated via the poisoning and collusion scenarios).
6. Analysts may intentionally or unintentionally issue privacy-sensitive,
   repeated, or rare-subgroup-targeting queries.
7. Privacy expenditure must be tracked across repeated analytical
   operations, per entity, not just globally.
8. Attackers may attempt membership inference, gradient inversion,
   differencing, rare-subgroup reconstruction, repeated-query averaging,
   or poisoning — SENTINEL models all six as first-class scenarios.
9. Audit records may themselves become a target and would require
   integrity protection in a production successor (not implemented here).
10. No single privacy mechanism is sufficient — the architecture combines
    data locality, DP-SGD, secure aggregation, robust aggregation, query
    governance and kill-chain monitoring, with each mechanism's actual
    coverage (and gaps) disclosed in `limitations.md` and `privacy_model.md`.
