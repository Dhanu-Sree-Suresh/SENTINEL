# System Architecture — Privacy-Preserving Collaborative Cyber-Defence

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
- Simple to implement.
- Low engineering complexity.

**Limitations**
- Provides limited defence against malicious participants.
- Does not provide an operational privacy-monitoring layer.
- Similar architectures are already common.

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
- Strong for distributed analytical queries.
- Reduces exposure of individual contributions.

**Limitations**
- Less comprehensive for full ML-based cyber-defence.
- Limited security-operations functionality.

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
- Strong technical security.
- Addresses privacy and malicious-client concerns.

**Limitation**
- Secure aggregation hides the individual updates that robust aggregation methods may need to inspect.
- This creates a significant privacy-versus-robustness trade-off.

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
- Strong production-security potential.
- Provides an additional hardware-backed trust mechanism.

**Limitations**
- Hardware attestation and deployment complexity are significant for a competition prototype.

**Assessment:** 8/10

---

## 2. Selected Architecture — Privacy Security Control Plane

**Architecture E** is selected as the final design.

```
            ┌─────────────────────────────┐
            │      GOVERNMENT SOC         │
            │  Dashboard • Investigation  │
            └──────────────┬──────────────┘
                           │
            ┌──────────────▼──────────────┐
            │  PRIVACY SECURITY CONTROL   │
            │           PLANE             │
            │                             │
            │  • Policy Engine            │
            │  • Privacy Budget Manager   │
            │  • Privacy Ledger           │
            │  • Query Risk Engine        │
            │  • Privacy Attack Detection │
            │  • Audit / SIEM Integration │
            └──────────────┬──────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
 ┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
 │ Government A  │ │ Government B  │ │ Government C  │
 │               │ │               │ │               │
 │ Raw Data      │ │ Raw Data      │ │ Raw Data      │
 │ Local ML      │ │ Local ML      │ │ Local ML      │
 │ User-Level DP │ │ User-Level DP │ │ User-Level DP │
 └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                ┌──────────▼──────────┐
                │  SECURE AGGREGATION │
                └──────────┬──────────┘
                           │
                ┌──────────▼──────────┐
                │ GLOBAL CYBER MODEL /│
                │ COLLABORATIVE       │
                │ ANALYTICS           │
                └─────────────────────┘

 ATTACKS
   │
   ▼
 MIA • Query Abuse • Poisoning
   │
   ▼
 Detection → Policy → Containment → SOC Alert
```

The **Privacy Security Control Plane** is the key differentiator. It combines policy enforcement, privacy-budget management, query monitoring, attack detection and audit functionality around the collaborative analytics process.

## 3. Architecture Decision Matrix

| Criterion              | A: FL+DP | B: FL Analytics | C: FL+DP+SecAgg | D: TEE-FL | E: Control Plane |
|------------------------|----------|-----------------|-----------------|-----------|------------------|
| Privacy                | 4        | 5               | 5               | 5         | 5                |
| Cybersecurity          | 3        | 4               | 5               | 5         | 5                |
| Innovation             | 3        | 4               | 4               | 4         | 5                |
| Feasibility            | 5        | 5               | 3               | 2         | 5                |
| Demonstrability        | 4        | 4               | 4               | 2         | 5                |
| Operational value      | 3        | 4               | 4               | 4         | 5                |
| **Overall**            | Medium   | High            | High            | High      | **Highest**      |

## 4. Final Decision

**Architecture E — Privacy Security Control Plane** is selected because it provides the strongest balance between:

- Privacy
- Cybersecurity relevance
- Feasibility
- Operational visibility
- Demonstrability
- Government applicability
- Product potential

The objective is not to claim that the underlying cryptographic primitives are new. The differentiation is their **operational composition** around a government cybersecurity problem.

## 5. Trust-Boundary Diagram (Text Representation)

```
┌──────────────────────────────────────────────────────────────────┐
│ TRUSTED (Organisation Boundary)                                  │
│  • Raw cybersecurity data                                        │
│  • Local training                                                │
│  • Local user-level DP                                           │
│  • Local identity & credentials                                  │
└────────────────────────────┬─────────────────────────────────────┘
                             │ Protected updates only
┌────────────────────────────▼─────────────────────────────────────┐
│ PARTIALLY TRUSTED (Federation Coordinator / Control Plane)       │
│  • Policy Engine                                                 │
│  • Privacy Budget Manager & Ledger                               │
│  • Query Risk Engine                                             │
│  • Privacy Attack Detection                                      │
│  • Audit / SIEM Integration                                      │
└────────────────────────────┬─────────────────────────────────────┘
                             │ Aggregated / protected results
┌────────────────────────────▼─────────────────────────────────────┐
│ NOT TRUSTED WITH INDIVIDUAL UPDATES (Aggregator)                 │
│  • Secure Aggregation                                            │
│  • Global model distribution                                     │
└──────────────────────────────────────────────────────────────────┘
```

## 6. Data-Flow Diagram (Text Representation)

```
Entity A/B/C Local Environment
  │
  │ 1. Local training on raw data (never leaves)
  │ 2. Apply user-level Differential Privacy
  │ 3. Produce protected model update
  ▼
Privacy Security Control Plane
  │
  │ 4. Enforce policy & privacy budget
  │ 5. Monitor for query abuse / membership probing
  │ 6. Record privacy expenditure in ledger
  ▼
Secure Aggregation
  │
  │ 7. Aggregate without revealing individual updates
  ▼
Global Cyber Model
  │
  │ 8. Distribute global model / analytic results
  ▼
Government SOC / Analysts
  │
  │ 9. Consume collaborative intelligence
  │ 10. Alerts from Privacy Attack Detection
```

## 7. Key Design Principles

1. **Raw data never leaves organisational security boundaries.**
2. **Individual model updates are protected** from the aggregator via Secure Aggregation and Differential Privacy.
3. **Privacy expenditure is formally accounted** and governed by a Privacy Budget Manager + Ledger.
4. **Suspicious analytic behaviour is treated as a cybersecurity event** (Privacy Attack Detection → SOC alert → containment).
5. **The Control Plane provides operational visibility** without requiring access to raw data.
