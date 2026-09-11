# Limitations

Consolidated from disclosures scattered through the codebase (README,
CHANGELOG, and inline docstrings) into one place, as requested by the
"required final outputs" checklist. Each item links to where it's enforced
or discussed in code.

## Privacy accounting
- RDP accounting is conservative: no subsampling-amplification credit
  claimed. See `docs/privacy_model.md` and `src/accountant.py`.
- Two separate, unfused accounting streams (Gaussian/FL-rounds vs.
  Laplace/queries). See `src/agent/dp_query.py`, `src/firewall/budget_ledger.py`.

## Model choice
- Logistic regression throughout the privacy pipeline (not a deep net) —
  chosen deliberately so DP-SGD, both attacks, and Byzantine-robustness math
  stay exactly comparable across every condition, and gradient inversion is
  exact/closed-form rather than approximate. See `src/model.py`.
- Traditional-ML/deep-learning baselines (`src/baselines.py`) are
  centralized-only reference points, not integrated into the privacy
  pipeline — no clean per-example-gradient/DP-SGD story for a random forest
  without materially more machinery.

## Dataset and attack track
- The privacy-attack track (membership inference) trains on a bounded
  per-entity subsample (~750 records), not the full 20k+ pool — see
  `experiments/run_experiment.py: build_splits()` docstring. Verified
  empirically: the full pool generalizes too well for this linear model to
  stay meaningfully MI-vulnerable, which would hide the attack, not
  demonstrate privacy protection.
- Membership-inference signal is reported primarily on the rare/high-risk
  subgroup, not the whole population — the population-wide metric is
  diluted to ~0.51 (indistinguishable from random) by the ~96% easy
  majority class regardless of condition. Both are reported; the subgroup
  number is the honest primary metric for this application.

## Secure aggregation
- Real pairwise-masking implementation (genuinely hides individual updates
  from the aggregator), but the "shared secret" between client pairs is
  simulated via a common seed rather than actual Diffie-Hellman key
  exchange. See `src/secure_agg.py`.
- Mutually exclusive with Byzantine-robust aggregation in this build (see
  `src/fl_engine.py`) — robust rules need per-client visibility that secure
  aggregation is designed to hide. Requesting both raises `ValueError`
  rather than silently picking one.

## Byzantine robustness
- Coordinate-median / trimmed-mean are only guaranteed below 50% malicious
  participants. The what-if simulator's Threat panel deliberately includes
  the 50% (2-of-4) case, where robust aggregation measurably degrades
  (utility 0.459 vs. 0.634 honest) — this is the platform's stated, honest
  residual risk, not hidden.
- Krum/Multi-Krum were deliberately NOT implemented: they require pairwise
  distance computation over full client updates, which is incompatible with
  secure aggregation for the same reason coordinate-median is (see above),
  and add complexity without a demonstrated benefit over coordinate-median
  at this platform's realistic 3-5-entity cohort size.
- Collusion *detection* is not implemented — only the *effect* of collusion
  (the 2-of-4 scenario) is measured.

## Agent
- The agent's decision path is deliberately rule-based/deterministic, not
  an LLM — see `src/agent/intent.py` docstring for the prompt-injection /
  excessive-agency reasoning. This means it can be evaded by sufficiently
  indirect phrasing that doesn't match its regex patterns; it is a first
  line of defense on top of, not a replacement for, the statistical query
  monitor.
- The agent never receives raw per-record data by construction (only calls
  `federated_dp_count_query`, which returns noised aggregates, or hands off
  training requests) — but this bound is enforced by *what code paths
  exist*, not by a runtime sandbox; a bug that added a new tool with raw
  access would not be caught by the agent's own logic.

## Query monitor
- A real bug was found and fixed during development: `frozenset(dict)`
  captures only dictionary keys, not key-value pairs, causing queries with
  identical filter *keys* but different *values* to be treated as ~100%
  similar. Fixed to `frozenset(dict.items())`; regression-tested. See
  `src/firewall/query_monitor.py` and `tests/test_firewall.py`.
- The default similarity threshold (0.65) was derived from the what-if
  grid's own sensitivity analysis, not picked arbitrarily — but it is still
  a hand-tuned heuristic threshold, not a formally optimal detector; a
  production deployment should tune it against real query-log data.
- Detection is deterministic, rule-based (frequency + Jaccard similarity),
  not a learned/statistical anomaly model — deliberately simple, to show
  that privacy attacks generate detectable SOC-style telemetry at all, not
  to be a research-grade detector.

## Deployment
- `deploy/` (Docker Compose + Dockerfiles) is a **documented, unvalidated**
  production topology — no Docker daemon or network access in this sandbox
  to test it end-to-end. Every function it would call (DP-SGD, DP queries,
  the agent, the ledger) is real and unit-tested; the network-service /
  TLS-mTLS / authentication layer is a stub. See `deploy/*/entrypoint.py`
  docstrings.
- No real identity federation, PKI, HSM, or SIEM integration is implemented
  — these are named in the roadmap, not built.

## What-if simulator
- Every value shown is looked up from a precomputed grid of real executed
  experiments (`experiments/run_whatif_grid.py`) — sliders snap to the
  nearest tested value; nothing is interpolated or invented at slider-move
  time. This means the grid's resolution (e.g. 7 epsilon points, 3×3
  malicious/aggregation combinations, 3×3 detection thresholds) is the
  simulator's actual resolution — moving a slider between tested points
  jumps to the nearest one rather than showing a smooth curve.

## Statistical rigor
- Most experiments average over 3 seeds, not more, for time-budget reasons
  in this sandboxed environment — reported standard deviations are
  therefore themselves noisy estimates, not tight confidence intervals.
  Every script is deterministic and reproducible, but 3 seeds is a modest
  sample for the standard-deviation bars shown.
