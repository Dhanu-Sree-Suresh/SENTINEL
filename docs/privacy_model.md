# Privacy Model

## Mechanism

**Gaussian mechanism inside DP-SGD** (Abadi et al., 2016) for FL training
rounds, **Laplace mechanism** for federated counting queries. These are
two separate, disclosed accounting streams — see
`src/firewall/budget_ledger.py` and `src/agent/dp_query.py`.

## Parameters actually used (defaults; every experiment states its own)

| Parameter | Value | Where |
|---|---|---|
| Clipping norm (C) | 2.0 | `experiments/run_experiment.py: CLIP_NORM` |
| Noise multiplier (sigma) | derived per target epsilon via `find_sigma_for_epsilon` | `src/accountant.py` |
| Sampling / batch | full-batch per local round (no subsampling) | `src/fl_engine.py` — deliberate, see below |
| Rounds (T) | 15 | `experiments/run_experiment.py: ROUNDS` |
| Delta | 1e-5 | `experiments/run_experiment.py: DELTA` |
| Query epsilon (Laplace, per entity per query) | 0.5 (agent default) | `src/agent/agent.py: DEFAULT_QUERY_EPSILON` |

## Privacy accountant

**Renyi-DP (RDP)** composition for the plain (non-subsampled) Gaussian
mechanism (`src/accountant.py`):

```
eps_RDP(alpha)     = alpha / (2 * sigma^2)               [single release]
eps_RDP_T(alpha)   = T * alpha / (2 * sigma^2)            [T-fold composition]
eps                = min_alpha [ eps_RDP_T(alpha) + ln(1/delta) / (alpha-1) ]
```

**Explicitly conservative, explicitly disclosed**: we do NOT claim privacy
amplification by subsampling (Wang et al., 2019 / the moments-accountant
subsampling bound), even though DP-SGD in general supports it. Implementing
that correctly without a reference library to validate against in this
offline sandbox was judged too risky to certify. Every epsilon this repo
reports is therefore a **valid upper bound**, not the tightest bound
achievable — a production build should swap in Opacus's or TF-Privacy's
accountant, which would report a *smaller* (better) epsilon for the same
noise multiplier and round count.

**Why full-batch, not minibatch, per round**: composing over `T=15` rounds
(one release per round) is deliberately cheap for the accountant compared to
composing over `T = rounds x batches-per-round`. This is a legitimate design
choice for small cross-silo cohorts (a handful of entities, each with a
modest local dataset) — see `src/fl_engine.py`'s module docstring — not an
accounting trick.

## Record-level vs. user-level vs. client-level — explicitly distinguished

- **DP-SGD as configured gives a record-level (per-training-example)
  guarantee** at each client's local dataset: the released gradient sum at
  each step is protected against the presence/absence of any *one training
  example*.
- This is **record-level, not automatically user-level**: if one individual
  can contribute multiple records (e.g. multiple login events), their
  overall privacy loss is *not* bounded by the same epsilon unless one of:
  1. each individual contributes at most one record per client (enforced by
     construction in `src/data_gen.py` — one `synthetic_id` per record, no
     repeated individuals across records in this prototype), **or**
  2. records are aggregated to one-per-user before training, **or**
  3. group-privacy composition is applied (accepting a `k times epsilon`
     degradation for a user with `k` records), **or**
  4. explicit user-level DP-SGD is used (clip/noise the per-user gradient
     *sum*, not the per-example gradient).
- **This prototype uses option (1)** — synthetic individuals appear at most
  once per entity — so record-level DP-SGD coincides with user-level DP-SGD
  here. This is stated explicitly, not silently assumed; a production
  dataset with repeated individual activity would need option (2), (3), or
  (4), and mixing this up (claiming user-level protection from record-level
  accounting when individuals have multiple records) is exactly the kind of
  mistake this document exists to prevent.
- **Client-level DP** (protecting an entire entity's participation/dataset
  as the unit, rather than any one individual's record) is a **different,
  stronger, and NOT implemented** guarantee in this build — worth naming
  because it's sometimes conflated with record/user-level DP. The
  Byzantine-robustness and secure-aggregation controls protect the
  *aggregator's view of a client's update*, which is a security property,
  not a client-level DP guarantee.

## Composition across the whole system

Two independently-tracked streams, both disclosed as such:

1. **FL training rounds** — Gaussian mechanism, RDP-accounted, composed
   across all `T` rounds of a training run (`BudgetLedger.record_round`).
2. **Analyst counting queries** — Laplace mechanism, composed via simple
   (worst-case, non-RDP) summation of per-query epsilons
   (`BudgetLedger.spend_query_epsilon`).

**A production system should unify these under one accountant** (e.g.
converting the Laplace releases into an equivalent RDP cost and composing
everything together). Keeping them separate here is disclosed as a
simplification, not presented as the final design.

## What Secure Aggregation is, and is not

- **Is**: a guarantee that the aggregator only observes the *sum* of
  clipped/noised client updates, never any individual client's update
  (`src/secure_agg.py`, real pairwise-masking implementation, unit-tested
  for the cancellation property).
- **Is not**: a bound on what the *released aggregate/model* reveals about
  any one training record. That bound comes only from DP-SGD. Secure
  Aggregation and Differential Privacy are **complementary, not
  substitutable** — this repo never claims one implies the other, and the
  4th "proposed" experimental condition runs both together specifically to
  make that complementarity concrete.

## What Byzantine-robust aggregation is, and is not

- **Is**: a guarantee (for coordinate-median / trimmed-mean, below 50%
  malicious participants) that a compromised entity's adversarial update
  cannot arbitrarily corrupt the global model.
- **Is not**: a privacy mechanism. It says nothing about what any released
  model reveals about training data; it is purely a security-integrity
  control, and is measured with a security metric (global-model utility
  under attack), not a privacy metric.
- **Is not compatible with Secure Aggregation in this build** — see
  `src/fl_engine.py` docstring: robust rules need to see individual client
  updates, exactly what secure aggregation is designed to hide.

## Formal DP summary at the platform's chosen operating point

At the "proposed system" operating point used throughout the demo
(epsilon≈4, delta=1e-5, C=2.0, T=15 rounds, full-batch, record-level = user-level
under this dataset's one-record-per-individual construction):

> For any two neighboring datasets differing in one individual's record at
> one entity, the distribution of that entity's sequence of 15 released
> gradient sums differs by at most (epsilon≈4, delta=1e-5) in the standard
> approximate-DP sense — a valid but not tight bound (see accountant
> disclosure above).
