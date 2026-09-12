# Compliance & Governance Positioning — SENTINEL · PPA-GOV

## 1. Core Legal Statement

No technical architecture can by itself create legal compliance.
Compliance depends on the full set of organisational, contractual,
procedural and technical measures applied by the controller and processor.
SENTINEL is a **prototype control plane over synthetic data**; it
demonstrates technical controls, it does not certify anything.

## 2. What the Architecture Actually Provides

| Technical Capability | Compliance-Relevant Benefit |
|-----------------------|-------------------------------|
| Data locality (raw records never leave the entity) | Supports data minimisation and reduces cross-boundary transfer risk |
| DP-SGD (clip C=1.5, Gaussian noise, RDP accounting) | Provides a stated, upper-bound mathematical limit on per-record inference risk at each release |
| Secure aggregation (pairwise masking) | Prevents the aggregator from inspecting any single entity's model update |
| Privacy Ledger (per-entity ε spend, `/ledger`) | Makes cumulative privacy loss visible and reviewable |
| Query-risk engine + `/decisions` log | Treats individual-level and repeated/rare-subgroup queries as detectable, blockable events |
| Entity reputation + robust aggregation | Supports accountability for and containment of a misbehaving participant |
| Audit trail (`/audit`) | Supports investigation, governance and evidence review |

These are **technical and organisational controls** that could form part of
a broader compliance programme in a production deployment. They do not
replace legal analysis, DPIAs, lawful-basis assessments, retention
policies or sector-specific rules — and in this prototype specifically,
they run over **synthetic data only** with **auth disabled by default**
(see `limitations.md`), so no compliance claim attaches to this build as
shipped.

## 3. UAE-Specific Considerations

### PDPL (Federal Decree-Law No. 45 of 2021)
- Applies to personal-data processing, with important exclusions for
  government data, government entities, security/judicial authorities,
  health data and banking/credit data.
- Cross-border transfers are regulated; adequacy or alternative safeguards
  are required where the law applies.
- Health data is subject to separate, stricter localisation rules under
  Federal Law No. 2 of 2019 — directly relevant to SENTINEL's synthetic
  "Dept. D · Health services" entity, which would carry the strictest
  handling requirements of the five modeled entities in any real
  deployment.

### Data Classification & Sovereign Controls
- Higher-classification data is expected to remain under sovereign or
  government-controlled environments.
- A production version of this architecture would place the control plane
  (aggregator, ledger, audit) in a government/sovereign cloud while each
  entity keeps raw data and local training inside its own environment —
  matching the trust-boundary diagram in `architecture.md`.

### Sector & Critical-Infrastructure Rules
- Critical infrastructure and certain government functions (SENTINEL's
  "Dept. C · Critical infra" entity) may be subject to additional
  cybersecurity and data-handling requirements beyond the PDPL.
- The collaborative design supports secure cooperation without forcing
  centralisation of sensitive telemetry.

## 4. Engineering Assumptions vs Legal Requirements

| Category | Statement |
|----------|-----------|
| **Legal requirement** | What the applicable law or regulation actually states (PDPL, health-data rules, cloud security policy, sector rules). |
| **Engineering assumption** | What this prototype assumes: synthetic data, record-level = user-level DP under a one-record-per-individual construction, per-entity ε ledger, disabled auth by default. |
| **Product recommendation** | What a production build would need: real entity identity, complete governance framework, DPIA, data classification, retention policy, SIEM integration, legal review. |

The prototype demonstrates the technical controls end-to-end on synthetic
data. A production deployment still requires each participating
organisation's full legal and governance framework — none of that is
built here.

## 5. Audit & Accountability Requirements

Every significant operation is recorded in `/audit` and the app's event
feed (`/monitor`):

- Federation join / connect / disconnect (`/infrastructure`)
- Training rounds and model updates (`/federated`)
- Privacy-budget allocation and consumption (`/ledger`)
- Analytical queries and their risk scores (`/console`, `/decisions`)
- Detected privacy attacks or anomalous behaviour (`/attacklab`, `/monitor`)
- Policy decisions — ALLOWED / BLOCKED (`/decisions`)
- Kill-chain stage escalations (`/threat`)

In this prototype the audit trail lives in client-side app state
(`src/lib/store.ts`), which is appropriate for a demo but is **not**
tamper-resistant, persistent, or integrated with a real SIEM — a
production system would need:

- Tamper-resistant, append-only storage
- Retention per organisational policy
- Access restricted to authorised investigators and auditors
- Real SIEM/SOC integration

## 6. Zero-Trust Governance Principle

Access decisions should evaluate:

1. Verified identity of the entity / service / analyst — **not implemented
   in this prototype** (auth is off by default; see `limitations.md`)
2. Organisational membership and role
3. Device or workload trust posture (where applicable)
4. Requested operation and purpose (query text, classified by
   `classifyQuery()`)
5. Remaining privacy budget (per-entity ε, `/ledger`)
6. Current risk level of the participant (entity reputation tier:
   normal / elevated / suspected_attack)
7. Applicable security and privacy policy (`/policy`)

Items 4–7 are implemented and visible in the UI today. Items 1–3 are named
as production requirements, deliberately out of scope for this prototype —
the README states plainly that "auth is off" and this "is a demonstration
control plane, not a multi-tenant production service."

A participant that was previously trusted may become compromised;
continuous verification — not a one-time join check — is therefore a
stated requirement for any production successor to this prototype.
