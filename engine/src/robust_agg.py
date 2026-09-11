"""
Byzantine-robust aggregation.

A malicious or compromised entity can send an arbitrarily scaled or
adversarially-crafted update to drag the global model in a direction
that benefits the attacker (model poisoning) or degrades everyone's
utility (untargeted/Byzantine sabotage). Plain FedAvg (arithmetic
mean) has NO resistance to this: a single client scaling its update
by 100x moves the average by roughly 100x/num_clients, which for a
small cross-silo cohort (3-5 entities, exactly our setting) is
catastrophic.

We implement two standard coordinate-wise robust rules that are
DP-compatible (they operate on the already-clipped-and-noised
per-client updates, so they don't require an additional privacy
accounting step of their own):

  - coordinate-wise MEDIAN (Yin et al., "Byzantine-Robust Distributed
    Learning", ICML 2018): for each parameter coordinate independently,
    take the median across clients. Provably robust to < 50% malicious
    clients for the coordinate-wise statistic, at some statistical
    efficiency cost vs. the mean under fully honest participants.

  - coordinate-wise TRIMMED MEAN: for each coordinate, drop the
    top/bottom `trim_frac` fraction of values across clients, then
    average what remains. Slightly better statistical efficiency than
    the median under partial honesty, standard baseline alongside
    Krum/Multi-Krum.

We deliberately do NOT implement Krum/Multi-Krum: those require
pairwise distance computation between full client updates and, more
importantly, are NOT compatible with secure aggregation (the
aggregator needs to see individual updates to compute pairwise
distances, defeating the point of masking them). Coordinate-wise
median/trimmed-mean can be computed the same way -- this is a real,
disclosed limitation: for this build, Byzantine robustness and secure
aggregation are alternatives selected per-deployment, not simultaneous
guarantees, unless a more advanced protocol (e.g. robust aggregation
inside MPC) is adopted in production.
"""
import numpy as np


def fedavg(client_updates):
    return np.mean(client_updates, axis=0)


def coordinate_median(client_updates):
    return np.median(np.stack(client_updates, axis=0), axis=0)


def coordinate_trimmed_mean(client_updates, trim_frac=0.25):
    """
    Default trim_frac=0.25 (not the more common 0.1-0.2): with only
    3-5 cross-silo clients (this platform's realistic cohort size,
    not cross-device FL's thousands), a small trim_frac rounds DOWN
    to k=0 trimmed clients and silently degenerates to plain FedAvg --
    verified empirically during development (0.2 trims nothing at
    n=4; 0.25 correctly trims 1 from each end). Robustness to a
    single malicious entity out of 3-5 requires trim_frac >= 1/n;
    callers with a different cohort size should set trim_frac
    explicitly rather than rely on this default.
    """
    stacked = np.sort(np.stack(client_updates, axis=0), axis=0)
    n = stacked.shape[0]
    k = int(np.floor(n * trim_frac))
    if 2 * k >= n:
        k = max(0, (n - 1) // 2)
    trimmed = stacked[k: n - k] if k > 0 else stacked
    return np.mean(trimmed, axis=0)


AGGREGATORS = {
    "mean": fedavg,
    "median": coordinate_median,
    "trimmed_mean": coordinate_trimmed_mean,
}


def aggregate(client_updates, strategy="mean", trim_frac=0.25):
    if strategy == "mean":
        return fedavg(client_updates)
    elif strategy == "median":
        return coordinate_median(client_updates)
    elif strategy == "trimmed_mean":
        return coordinate_trimmed_mean(client_updates, trim_frac=trim_frac)
    raise ValueError(f"unknown aggregation strategy: {strategy}")
