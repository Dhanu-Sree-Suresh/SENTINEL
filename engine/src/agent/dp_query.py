"""
Privacy-preserving federated analytics: a distributed counting/sum
query using the Laplace mechanism, with noise added LOCALLY by each
entity before any single party (including the aggregator/agent) ever
sees an exact per-entity count.

This is the "population statistic / query interface" deliverable from
the brief's minimum-requirements list, implemented as a real,
executable mechanism rather than only the FL classifier.

Why Laplace, not Gaussian, here: a simple counting query has a clean,
exact L1 sensitivity of `sensitivity` (adding/removing one record
changes the count by at most `sensitivity`, normally 1) under
add/remove-one-record neighboring datasets, which is exactly the
setting the (pure-epsilon, no delta) Laplace mechanism is built for --
no need to bring in the Gaussian mechanism's (epsilon, delta)
approximate-DP machinery for a scalar counting query.

Privacy accounting for this mechanism is DELIBERATELY SEPARATE from
the Gaussian/DP-SGD accountant used for FL training (src/accountant.py):
each entity's counting-query noise only protects that entity's own
individuals, and successive counting queries against the SAME entity
compose via simple (worst-case, non-RDP) summation of their epsilons --
conservative and easy to audit, at the cost of a looser bound than a
full RDP treatment would give. A production build should unify all
mechanisms (Gaussian FL rounds + Laplace queries) under one RDP
accountant; this is disclosed, not hidden, in
src/firewall/budget_ledger.py's query-budget tracking.
"""
import numpy as np


def local_dp_count(true_count, epsilon, sensitivity=1.0, rng=None):
    """One entity's noised contribution to a distributed count query."""
    rng = rng or np.random.default_rng()
    noise = rng.laplace(0, sensitivity / epsilon)
    return true_count + noise


def federated_dp_count_query(entity_dataframes, filter_fn, epsilon, sensitivity=1.0, seed=None):
    """
    entity_dataframes: dict[entity_name -> pandas.DataFrame] (each
        entity's OWN local data; never pooled).
    filter_fn: predicate applied independently inside each entity's
        local process, e.g. `lambda df: df.insider_threat_label == 1`.
    epsilon: privacy budget spent AT EACH entity for this one query
        (each entity's individuals are only protected by that
        entity's own epsilon spend -- an entity that answers many
        queries accumulates budget only against its own ledger row).

    Returns (noisy_total, per_entity_noisy_counts, per_entity_true_counts).
    per_entity_true_counts is returned ONLY for this repo's own
    evaluation/audit purposes (e.g. computing the mechanism's error) --
    a real deployment would never transmit or log the true count
    off the entity's own infrastructure.
    """
    rng = np.random.default_rng(seed)
    true_counts, noisy_counts = {}, {}
    for entity, df in entity_dataframes.items():
        true_count = int(filter_fn(df).sum())
        true_counts[entity] = true_count
        noisy_counts[entity] = local_dp_count(true_count, epsilon, sensitivity, rng)
    noisy_total = sum(noisy_counts.values())
    return noisy_total, noisy_counts, true_counts
