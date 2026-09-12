# System Architecture — SENTINEL · PPA-GOV

## 1. Candidate Architectures

### Architecture A — Basic FL + Differential Privacy

```
Local Data
   ↓
Local Training
   ↓
Differential Privacy
   ↓
Federated Aggregation
   ↓
Global Model
```

**Advantages**
- Simple to implement and explain to a non-technical audience.
- Low engineering complexity for a prototype timeline.

**Limitations**
- No defence against a malicious or compromised entity's update.
- No operational visibility — nothing to show a SOC analyst.
- Widely demonstrated already; low differentiation.

**Assessment:** 6/10

---

### Architecture B — Federated Analytics + Secure Aggregation + DP

```
Local Data
   ↓
Local Query
   ↓
DP
   ↓
Secure Aggregation
   ↓
Global Statistic
```

**Advantages**
- Strong fit for the population-prevalence side of the product (`/prevalence`).
- Keeps individual entity contributions out of the aggregator's view.

**Limitations**
- Doesn't cover the ML/insider-threat classification side of the product.
- No query-abuse monitoring on its own.

**Assessment:** 8/10

---

### Architecture C — FL + DP + Secure Aggregation + Robust Aggregation

```
Local Training
   ↓
User-Level DP
   ↓
Secure Aggregation
   ↓
Robust Aggregation
   ↓
Global Model
```

**Advantages**
- Covers both privacy (DP, SecAgg) and integrity (robust aggregation).
- Matches the poisoning-defence numbers we can actually measure (see below).

**Limitation**
- Secure aggregation hides the per-client updates that coordinate-median /
  trimmed-mean need to inspect. This is a real, disclosed trade-off in this
  build, not a modeling error — see `limitations.md`.

**Assessment:** 8.5/10

---

### Architecture D — Confidential / TEE-Based FL

```
Clients
   ↓
Protected Updates
   ↓
Trusted Execution Environment
   ↓
Robust Aggregation
   ↓
Global Model
```

**Advantages**
- Strongest production-security ceiling of the candidates.
- Hardware-backed trust in addition to cryptographic/statistical controls.

**Limitations**
- Attestation, enclave provisioning and deployment complexity are out of
  reach for a browser-based prototype and a short build window.

**Assessment:** 8/10

---

## 2. Selected Architecture — Privacy Security Control Plane

**Architecture E** is selected as the final design. SENTINEL · PPA-GOV
implements it as a single-page control plane (React + TanStack Start) with
seven functional zones — Command, Analytics & ML, Access, Security, and
Ops — sitting around a shared privacy/query engine (`src/lib/engine.ts`)
and app store (`src/lib/store.ts`).

The **Privacy Security Control Plane** is the differentiator: policy
enforcement, privacy-budget tracking, query-risk scoring, attack detection
and audit trail are first-class UI surfaces (`/policy`, `/ledger`,
`/decisions`, `/monitor`, `/audit`), not just backend plumbing.

## 3. Architecture Decision Matrix

| Criterion              | A: FL+DP | B: FL Analytics | C: FL+DP+SecAgg | D: TEE-FL | E: Control Plane |
|------------------------|----------|-----------------|-----------------|-----------|------------------|
| Privacy                | 4        | 5               | 5               | 5         | 5                |
| Cybersecurity          | 3        | 4               | 5               | 5         | 5                |
| Innovation             | 3        | 4               | 4               | 4         | 5                |
| Feasibility (browser prototype) | 5 | 5             | 4               | 2         | 5                |
| Demonstrability        | 4        | 4               | 4               | 2         | 5                |
| Operational value      | 3        | 4               | 4               | 4         | 5                |
| **Overall**            | Medium   | High            | High            | High      | **Highest**      |

## 4. Final Decision

**Architecture E — Privacy Security Control Plane** is selected because it
provides the strongest balance of privacy, cybersecurity relevance,
feasibility inside a client-side prototype, operational visibility,
demonstrability and government applicability.

The underlying cryptographic and statistical primitives (FL, DP-SGD, secure
aggregation, robust aggregation) are established techniques. The
differentiation is their **operational composition** — surfaced as SOC-style
telemetry — around a government collaborative-analytics problem.

## 5. Trust-Boundary Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│ TRUSTED (Entity Boundary — Dept. A..E)                            │
│  • Synthetic per-entity records (~5.5k–7.2k rows each)            │
│  • Local training (logistic classifier)                           │
│  • Local DP-SGD (clip C=1.5, Gaussian noise)                      │
└────────────────────────────┬─────────────────────────────────────┘
                             │ Clipped, noised gradients only
┌────────────────────────────▼─────────────────────────────────────┐
│ PARTIALLY TRUSTED (SENTINEL Control Plane)                        │
│  • Policy / query-risk engine (src/lib/engine.ts)                 │
│  • Privacy Budget Ledger (per-entity ε spend)                     │
│  • Attack / kill-chain monitor                                    │
│  • Audit trail                                                    │
└────────────────────────────┬─────────────────────────────────────┘
                             │ Aggregated / protected results
┌────────────────────────────▼─────────────────────────────────────┐
│ NOT TRUSTED WITH INDIVIDUAL UPDATES (Secure Aggregator)            │
│  • Pairwise-mask secure aggregation (protocol simulation)         │
│  • Global model distribution                                      │
└──────────────────────────────────────────────────────────────────┘
```

## 6. Data-Flow Diagram

```
Entity A–E Local Environment
  │
  │ 1. Local training on synthetic records (never leaves)
  │ 2. Clip per-example gradients (C=1.5), add Gaussian noise
  │ 3. Produce protected model update
  ▼
Privacy Security Control Plane
  │
  │ 4. classifyQuery() enforces policy (blocks individual-level asks)
  │ 5. Query monitor scores risk LOW/MEDIUM/HIGH/CRITICAL
  │ 6. RDP accountant records ε expenditure to the ledger
  ▼
Secure Aggregation
  │
  │ 7. Aggregate without exposing any single entity's update
  ▼
Global Insider-Threat Model
  │
  │ 8. Distribute model / prevalence results to /overview, /prevalence
  ▼
Analyst Console / SOC Views
  │
  │ 9. Analysts query aggregates via /console
  │ 10. /monitor, /threat, /audit surface kill-chain alerts
```

## 7. Key Design Principles

1. **Raw records never leave their entity.** The UI, console and attack lab
   operate only on aggregates, model updates and synthetic telemetry.
2. **Individual updates are protected** en route to the aggregator via
   secure aggregation and DP-SGD.
3. **Privacy expenditure is tracked per entity** in a visible ledger
   (`/ledger`), not treated as an informal noise knob.
4. **Suspicious query behaviour is a security event**, not just a privacy
   statistic — it flows into the same kill-chain monitor as other SOC
   telemetry (`/monitor`, `/threat`).
5. **The Control Plane provides operational visibility without needing
   access to raw data.**

## 8. What Is Simulated vs. Executed

To be precise about what this prototype actually does at runtime (see
`limitations.md` for the full disclosure):

- The **headline numbers** (AUC, membership-inference advantage, gradient
  inversion cosine similarity, poisoning-defence AUC) come from one
  executed experiment, shipped as `public/results.json` /
  `src/lib/results.ts` — they are not placeholders.
- The **in-browser attack lab** (`/attacklab`) replays and interpolates
  that executed experiment against user-adjustable parameters; it does not
  retrain a model on 32k rows in the browser on every click.
- **Secure aggregation** (`src/lib/store.ts`) is a real mask-exchange /
  drop-handling protocol simulation, not a production MPC deployment.
