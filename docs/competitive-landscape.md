# Competitive Landscape & Product Strategy — SENTINEL · PPA-GOV

## 1. Existing Landscape

Existing privacy-preserving platforms must be acknowledged honestly.

**Examples:**

- **Duality** — markets privacy-preserving collaboration using FHE, Federated
  Learning, TEEs, Differential Privacy, MPC, secure querying and governance
  capabilities.
- **NVIDIA FLARE** — open-source (and enterprise) federated-learning
  platform supporting multi-party collaboration, secure aggregation, and
  confidential-computing options.
- Other FL frameworks (Flower, OpenFL, TensorFlow Federated, FedML, PySyft)
  and privacy libraries (Opacus, TensorFlow Privacy, IBM diffprivlib).
- Government and industry CTI platforms that share indicators of
  compromise, but typically still require carefully controlled data
  exchange.

**Correct competitive positioning:**

> Existing platforms primarily provide privacy-preserving computation and
> collaboration.
> SENTINEL's differentiation is the **security-operations layer** — a
> control plane that continuously treats privacy leakage and malicious
> participation as operational cyber threats, and shows that as SOC-style
> UI (kill-chain stages, entity reputation, audit trail), not just an API.

We do **not** claim to have invented privacy-preserving collaboration, and
we do not claim the FL / DP-SGD / secure-aggregation primitives themselves
are novel.

## 2. Competitor Comparison Matrix

| Capability                        | Traditional Centralised Analytics | Standard FL Platform | Privacy-Preserving Platform | **SENTINEL · PPA-GOV** |
|-----------------------------------|-----------------------------------|-----------------------|------------------------------|-------------------------|
| Raw data centralisation           | Yes                                | No                     | Usually No                   | **No**                  |
| Federated learning                | No                                 | Yes                    | Possible                     | **Yes**                 |
| Secure aggregation                | No                                 | Optional               | Possible                     | **Yes (protocol simulation)** |
| Differential privacy              | Optional                          | Optional               | Yes                          | **DP-SGD, RDP-accounted** |
| Robust / Byzantine aggregation    | No                                 | Limited                | Varies                       | **Coordinate-median / trimmed-mean** |
| Privacy accounting                | Limited                            | Limited / varies       | Varies                       | **Per-entity ledger (ε spend)** |
| Privacy-query monitoring          | No                                 | Limited                 | Varies                       | **Core feature (`/console`, `/decisions`)** |
| Privacy attack detection          | No                                 | Limited                 | Varies                       | **Core feature (`/attacklab`, `/monitor`)** |
| Malicious participant controls    | Limited                            | Varies                  | Varies                       | **Entity reputation + kill-chain** |
| SOC-style dashboard                | Possible                          | Limited                 | Limited                       | **Core design (dual dark/light theme)** |
| Government / SOC use case         | General                            | General                 | General                       | **Primary use case**    |

## 3. Customer, Buyer and User Definition

### Primary Customers
- Government departments and agencies
- Government cybersecurity authorities
- Critical infrastructure operators
- Public-sector organisations
- Government-linked security organisations

### Primary Buyers
- Chief Information Security Officers (CISOs)
- Government technology leadership
- Cybersecurity programme directors
- Data-governance leadership
- Digital-transformation leadership

### Primary Users
- SOC analysts (`/monitor`, `/threat`, `/audit`)
- Cybersecurity analysts (`/attacklab`)
- Privacy officers (`/ledger`, `/policy`)
- Data-governance teams
- ML / security engineers (`/ml`, `/federated`, `/pipeline`)
- Federation administrators (`/infrastructure`)

## 4. Product Value Proposition

**Problem**
Government organisations possess valuable cybersecurity intelligence
(insider-threat signals, in this prototype) but cannot or will not
centralise sensitive telemetry to learn from it collectively.

**Solution**
A Privacy Security Control Plane lets five entities collaborate on an
insider-threat classifier and population statistics while raw records stay
inside each entity's own boundary.

**Value delivered**
- Collaborative threat intelligence (shared insider-threat classifier)
- Reduced raw-data sharing (0 raw records ever leave an entity)
- Formal, visible privacy accounting (per-entity ε ledger)
- Protection of individual updates (secure aggregation)
- Monitoring of privacy-sensitive activity (query risk engine)
- Malicious-participant controls (entity reputation, poisoning defence)
- Security alerts (kill-chain monitor)
- Auditability (`/audit`)
- A dashboard SOC analysts can actually read

**Core Value Proposition**

> Collaborate on insider-threat detection without surrendering control of
> sensitive government data.

## 5. Business Case

The system creates value by reducing the need for organisations to choose
between data privacy and collaborative cyber defence.

### For Government Organisations
- Sensitive records remain locally controlled.
- Organisations benefit from cross-organisational intelligence — the
  federated model is measurably close to the naïve-pooled ceiling
  (ROC-AUC 0.594 federated+DP vs. 0.597 naïve pooled at ε≈4).
- Privacy risk becomes measurable (ledger) rather than assumed.
- Security teams get operational visibility into privacy attacks via the
  same kill-chain UI as other SOC telemetry.
- Audit evidence supports governance and accountability.

### For SOC Teams
The control plane converts privacy-related behaviour into security
telemetry:

```
Repeated / rare-subgroup queries
        ↓
High query specificity (risk = MEDIUM/HIGH)
        ↓
Increasing privacy expenditure (ledger)
        ↓
Query-risk engine
        ↓
PRIVACY ATTACK SUSPECTED (kill-chain stage: PROBING → EXTRACTION_ATTEMPT)
        ↓
Block / require approval
        ↓
SOC alert (/monitor, /audit)
```

This makes privacy protection part of the organisation's existing
security-operations model rather than a separate compliance checkbox.

## 6. Core Innovation Statement

The underlying technologies — Federated Learning, Differential Privacy,
Secure Aggregation and robust (coordinate-median / trimmed-mean)
aggregation — are established techniques.

**Our innovation is not another FL algorithm or DP mechanism.**

SENTINEL introduces a **Privacy Security Control Plane** that treats privacy
leakage as an operational cybersecurity threat:

- Every collaborative computation is governed by a formal, per-entity
  privacy budget
- Query patterns are monitored for inference-style behaviour
- Suspicious behaviour is correlated with an entity reputation score
- Detected probing escalates through kill-chain stages toward containment
- Legitimate collaborative analytics keeps working throughout

**Key idea:**

> Privacy is not only something you protect.
> It is something you monitor.

## 7. Final System Security Story

| Problem                              | Control                                                |
|---------------------------------------|---------------------------------------------------------|
| Central exposure of government data   | Federated architecture (no pooled raw records)          |
| Individual update exposure            | Secure aggregation (pairwise masking)                   |
| Individual information leakage        | DP-SGD (clip C=1.5, Gaussian noise, RDP accounting)      |
| Malicious / compromised participants  | Entity reputation tiers + robust aggregation             |
| Privacy-budget exhaustion             | Per-entity privacy ledger                                 |
| Privacy-query attacks                 | Query-risk engine (`classifyQuery`, decision log)         |
| Security investigation                | Kill-chain monitor + audit trail                          |
| Accountability                        | `/audit` operator trail of queries, attacks, rounds        |

This separation is deliberate: FL, secure aggregation, DP-SGD and robust
aggregation do **not** solve the same problem. SENTINEL addresses each
distinctly and brings them together under one operational model — while
disclosing where they trade off against each other (secure aggregation vs.
robust aggregation, in particular — see `limitations.md`).

## 8. Validation Strategy (Demo Narrative)

The `/attacklab` and dashboard together demonstrate three things:

1. **Attack** — Gradient inversion against a raw (non-DP) update
   reconstructs the batch almost exactly (cosine ≈ 1.0). Membership
   inference against the naïve model reaches AUC ≈ 0.510 on the
   rare/high-risk subgroup.
2. **Protection** — The same attacks collapse under FL+DP: gradient
   inversion cosine drops to ≈ 0.0003; membership-inference advantage
   shrinks toward chance (AUC ≈ 0.491–0.494).
3. **Defence** — Repeated/rare-subgroup probing is visible as a kill-chain
   sequence (`/monitor`, `/threat`) and can be blocked at the policy layer
   (`/decisions`), with the event trail preserved in `/audit`.

This is an **attack → protection → detection** narrative, not just "a
federated model can train."

## 9. Strongest Answers for Judges

**"Why can't you just centralise the data?"**
"Because centralisation creates a new high-value trust boundary, increases
breach impact, and requires every participating entity to surrender
control of sensitive records. SENTINEL keeps raw data within each entity
and shares only privacy-protected computation."

**"Is Federated Learning private?"**
"No. Federated Learning is a data-locality architecture, not a complete
privacy guarantee — our own numbers show it: FL-without-DP still reaches
membership-inference AUC 0.486, barely different from the naïve baseline's
0.510. Secure aggregation and DP-SGD address the parts FL alone doesn't."

**"What is actually innovative?"**
"The primitives are established. Our innovation is their operational
composition around a government insider-threat use case, where privacy
attacks, malicious participants and privacy-budget exhaustion are treated
as security incidents inside a single SOC-style control plane."

**"Is your system PDPL compliant?"**
"No technology automatically makes an organisation PDPL compliant.
SENTINEL is designed to reduce raw-data sharing and support technical and
organisational privacy controls, while legal compliance remains dependent
on each organisation's complete legal and governance framework — see
`compliance.md`."

**"What makes this different from existing FL platforms?"**
"Existing platforms primarily provide privacy-preserving computation and
collaboration. SENTINEL's differentiation is the security-operations
layer that continuously treats privacy leakage and malicious participation
as operational cyber threats, and shows that operationally — not just in a
whitepaper."

**"Is the attack lab really attacking a live model?"**
"Honestly: the headline numbers come from one executed experiment. The
in-browser attack lab replays and interpolates that experiment against
your chosen parameters rather than retraining on 32k rows per click — we
say so directly in the app's own 'Honest limitations' section, because we'd
rather be precise than impressive."

## 10. Final Concept Statement

**SENTINEL · PPA-GOV — Privacy Security Control Plane for Collaborative
Government Analytics**

> We don't just make collaborative analytics private.
> We continuously monitor, enforce, and respond to attempts to extract
> information from it — and we show that as one operator's dashboard.
