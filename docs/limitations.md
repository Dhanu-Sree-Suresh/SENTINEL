# Limitations — SENTINEL · PPA-GOV

Consolidated from disclosures scattered through the codebase (`README.md`,
inline comments in `src/lib/`) into one place. Each item names where it's
stated or enforced in code so it can be checked, not just taken on faith.

## Data
- **Synthetic data only.** No real personal records are processed anywhere
  in this application — dashboard, console, attack lab, or the optional
  `research/` Python engine. ~32,000 synthetic records across 5 entities,
  ~4.06% positive rate (`src/lib/results.ts: MEASURED.records / positiveRate`).
- Entities are illustrative government functions (HR/identity, licensing,
  critical infrastructure, health services, digital services) with
  synthetic record counts and starting privacy budgets
  (`src/lib/results.ts: DEFAULT_ENTITIES`) — not modeled on any real agency.

## Model choice
- The headline classifier is logistic regression, not a deep net —
  `src/lib/results.ts: MEASURED.models` also reports Random Forest,
  Histogram Gradient Boosting, an MLP, and Isolation Forest for comparison,
  but the FL/DP-SGD/attack pipeline is built and measured around the
  logistic model specifically, because it keeps DP-SGD accounting and
  gradient-inversion math exact rather than approximate.
- ROC-AUC across all model families is modest (0.492–0.597) — this is a
  genuinely weak-signal synthetic task, reported as such rather than
  tuned to look stronger than it is.

## What's measured vs. what's simulated in the running app
- **The headline numbers are from one executed experiment**, shipped as
  `public/results.json` / `src/lib/results.ts`, not placeholders:
  naïve-pooled AUC 0.5965, FL-no-DP AUC 0.5919, FL+DP (ε≈4) AUC 0.5944;
  membership-inference AUC 0.5098 (naïve) vs. 0.4913–0.4935 (DP/proposed);
  gradient-inversion cosine similarity 0.999999999933 (raw) vs. 0.000325196
  (DP-protected).
- **The in-browser `/attacklab` replays and interpolates** that executed
  experiment against the parameters you choose (`src/lib/engine.ts:
  attackConfidence`, `measuredAnchor`) — it is not retraining a model on
  32k rows in the browser on every click. The confidence numbers it shows
  are a parameterised interpolation anchored to the measured results, not
  a fresh statistical computation each time.
- **Secure aggregation** (`src/lib/store.ts`) is a real pairwise-masking
  *protocol simulation* — it genuinely models mask exchange and drop
  handling — but it is not a production MPC deployment; there's no real
  cryptographic key exchange between simulated entities in the browser.
- **Robust (coordinate-median / trimmed-mean) aggregation and secure
  aggregation are conceptually presented together** in the architecture
  stages (`src/lib/results.ts: ARCH_STAGES`), but the underlying disclosed
  trade-off — robust rules need per-client visibility that secure
  aggregation is designed to hide — is real and unresolved in this build,
  same as in the underlying research engine. The UI presents this as a
  named trade-off, not a solved problem.

## Privacy accounting
- RDP (Rényi differential privacy) accounting for the Gaussian mechanism in
  DP-SGD, δ = 1e-5, clip norm C = 1.5. The ε-sweep shown in the dashboard
  (`src/lib/results.ts: MEASURED.sweep`) runs from "No DP" through ε = 32,
  with AUC gains flattening out by ε ≈ 4 — the operating point used
  throughout the demo.
- Analyst-console query privacy (`/console`) and FL-round privacy
  (`/federated`) are presented together in the per-entity ledger
  (`/ledger`), but — consistent with the underlying research engine this
  prototype is modeled on — they are conceptually two different
  accounting streams (Gaussian/FL-rounds vs. Laplace/queries) rather than
  one unified accountant. A production system should unify these.

## Membership inference specifically
- The reported membership-inference advantage is modest even in the
  naïve setting (AUC ≈ 0.51) because the underlying classification signal
  is weak — this is disclosed as the honest result of a hard, realistic
  synthetic task, not softened to look more dramatic.
- `src/lib/results.ts: MEASURED.miByN` shows MI AUC creeping above chance
  only as the training-set size shrinks toward n≈150–500 — i.e. the attack
  is realistically hardest against the largest, most representative
  training sets and easiest against small/rare subgroups, which is exactly
  why `/attacklab`'s "rare subgroup reconstruction" scenario exists as a
  separate, harder case.

## Byzantine robustness / poisoning
- `src/lib/results.ts: MEASURED.poisoning` reports four conditions (clean,
  label flip, 10× scale, 2/5 collude) across four aggregation rules (mean,
  median, trimmed mean, clip). Coordinate-median recovers clean-level
  utility against a 10×-scale attack (0.594 vs. 0.592 clean) — but, as
  above, this protection is presented as incompatible with secure
  aggregation in the same round, not as a free combination.
- Only the **effect** of a colluding-minority attack (2 of 5 entities) is
  measured; **detecting** collusion itself is not implemented.

## Query / attack-lab engine
- Individual-query blocking (`src/lib/engine.ts: classifyQuery`) is a
  regex-pattern match against terms like "named patient," "specific
  person," "date of birth," "membership," etc. — deliberately simple, to
  demonstrate that privacy-sensitive requests generate detectable,
  blockable telemetry at all, not to be a production-grade intent
  classifier. It can be evaded by sufficiently indirect phrasing that
  doesn't match its patterns.
- Attack-confidence scores in `/attacklab` (`attackConfidence()`) are a
  hand-tuned formula (exposure × signal, size factor, per-scenario boost)
  calibrated to land near the measured anchors, not an independently
  re-derived statistical result per interaction.

## Deployment / auth
- **Auth is off by default.** This is a stated design choice ("Auth is
  off. This is a demonstration control plane, not a multi-tenant
  production service" — `README.md`), not an oversight. No real identity
  federation, PKI, HSM or SIEM integration is implemented.
- State (entities, queries, events, ledger, audit) lives in a client-side
  Zustand store (`src/lib/store.ts`). Without `DATABASE_URL` set, app data
  also falls back to an embedded in-memory Postgres (PGLite) that resets
  on every process restart — appropriate for a demo, not for persisted
  production audit evidence.
- This repository ships as a Vite/TanStack Start web app; there is no
  validated Docker/Kubernetes production topology included.

## Statistical rigor
- The measured results shown throughout the UI come from one executed
  experiment run, not an average over many seeds. Numbers should be read
  as a single, real, reproducible data point — not as a tight confidence
  interval.
