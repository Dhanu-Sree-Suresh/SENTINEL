# Privacy Model — SENTINEL · PPA-GOV

## Mechanism

**Gaussian mechanism inside DP-SGD** for federated training rounds
(`/federated`), conceptually paired with a **Laplace-style noised-answer**
mechanism for analyst counting/prevalence queries (`/console`,
`answerQuery()` in `src/lib/engine.ts`). These are presented in the app as
two related but distinct privacy surfaces — training-round privacy and
query privacy — each contributing to the same per-entity ledger
(`/ledger`).

## Parameters used at the demo's operating point

| Parameter | Value | Where |
|---|---|---|
| Clipping norm (C) | 1.5 | `src/lib/results.ts: ARCH_STAGES` ("train" stage) |
| Delta (δ) | 1e-5 | `src/lib/results.ts: ARCH_STAGES` ("noise" stage) |
| Operating epsilon (ε) | ≈ 4 | `src/lib/results.ts: MEASURED.flDp4Auc`, `sweep` |
| Epsilon sweep tested | No DP, 0.5, 1, 2, 4, 8, 16, 32 | `src/lib/results.ts: MEASURED.sweep` |
| Entities | 5 | `src/lib/results.ts: MEASURED.entities` |
| Total records | ~32,000 | `src/lib/results.ts: MEASURED.records` |
| Positive rate | ~4.06% | `src/lib/results.ts: MEASURED.positiveRate` |
| Query epsilon (per analyst query) | scenario-dependent, charged against the entity's remaining budget | `src/lib/engine.ts: answerQuery`, `/ledger` |

## Privacy accountant

**Rényi-DP (RDP) composition** for the Gaussian mechanism used in DP-SGD, as
referenced by the "noise" architecture stage (`src/lib/results.ts:
ARCH_STAGES`): calibrated Gaussian noise is added to clipped gradients, and
an RDP accountant converts the result to an (ε, δ)-DP guarantee with
δ = 1e-5.

The ε-sweep (`MEASURED.sweep`) shows the expected shape of this trade-off:
utility rises quickly from "No DP" (AUC 0.5919) through ε = 1–2, and
essentially flattens by ε ≈ 4 (AUC 0.5944) — additional budget beyond that
buys negligible extra utility in this model, which is why ε ≈ 4 is used as
the platform's standard operating point throughout the dashboard and attack
lab.

## Record-level vs. user-level vs. entity-level — explicitly distinguished

- **DP-SGD as configured gives a record-level guarantee** at each entity's
  local training set: the released, clipped-and-noised gradient at each
  round is protected against the presence or absence of any one training
  record.
- This is **record-level, not automatically user-level**: if one
  individual could contribute multiple records, their overall privacy loss
  would not be bounded by the same ε without additional composition. This
  prototype's synthetic data generation is built so that each synthetic
  individual appears at most once per entity — under that construction,
  record-level DP-SGD coincides with user-level DP-SGD. A dataset with
  repeated individual activity per entity would need explicit group-privacy
  composition or user-level DP-SGD (clipping/noising the per-user gradient
  sum rather than the per-example gradient) — not implemented here.
- **Entity-level DP** (protecting an entire entity's participation as the
  unit, rather than any one individual's record) is a different, stronger
  guarantee that is **not** implemented. The entity-reputation and
  robust-aggregation controls protect the *aggregator's view of an
  entity's update* — a security property — not an entity-level DP
  guarantee.

## What Secure Aggregation is, and is not

- **Is**: in this build, a genuine pairwise-masking protocol simulation
  (`src/lib/store.ts`) in which the aggregator only observes the *sum* of
  clipped/noised entity updates, never any individual entity's update, and
  drop handling is modeled.
- **Is not**: a bound on what the *released aggregate/model* reveals about
  any one training record. That bound comes only from DP-SGD. Secure
  Aggregation and Differential Privacy are **complementary, not
  substitutable** — the dashboard's FL+DP condition runs both together
  specifically to make that complementarity concrete (`/federated`,
  `/pipeline`).

## What Robust (Byzantine-resistant) Aggregation is, and is not

- **Is**: coordinate-median / trimmed-mean aggregation, shown to recover
  near-clean utility against a 10×-scale poisoning attack (`MEASURED.
  poisoning`: mean 0.585 vs. median 0.594 under 10× scale, vs. 0.592/0.595
  clean).
- **Is not**: a privacy mechanism. It says nothing about what a released
  model reveals about training data — it's a security-integrity control,
  measured with a security metric (utility under attack), not a privacy
  metric.
- **Is not freely combinable with Secure Aggregation** in this
  architecture — robust rules need visibility into individual entity
  updates, which is exactly what secure aggregation is designed to hide.
  `architecture.md`'s "robust" stage names this trade-off explicitly rather
  than hiding it.

## Query-privacy path (`/console`, `/decisions`)

- `classifyQuery()` (`src/lib/engine.ts`) blocks individual-level asks
  (named individuals, specific dates of birth, "membership" questions,
  etc.) outright — these never reach the noised-answer path at all and are
  logged as `BLOCKED` with `risk = HIGH`.
- Allowed queries are answered via `answerQuery()`, which returns an
  aggregate figure with a stated noise characterisation (e.g. "Laplace
  noise σ≈…pp") and charges an ε cost against the entity's ledger balance.
- Repeated or rare-subgroup query patterns are themselves treated as a
  privacy-attack signal — see `threat-model.md` and the "Repeated query
  attack" / "Rare subgroup reconstruction" scenarios in `/attacklab`.

## Formal DP summary at the platform's chosen operating point

At the "proposed system" operating point used throughout the demo
(ε ≈ 4, δ = 1e-5, C = 1.5, record-level = user-level under this dataset's
one-record-per-individual construction):

> For any two neighbouring per-entity training sets differing in one
> individual's record, the distribution of that entity's sequence of
> released, clipped-and-noised gradient updates differs by at most
> (ε ≈ 4, δ = 1e-5) in the standard approximate-DP sense, as tracked by the
> RDP accountant referenced in `architecture.md`'s "noise" stage. This is a
> disclosed operating point from one executed experiment (see
> `limitations.md`), not an independently re-verified formal proof.
