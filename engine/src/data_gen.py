"""
Synthetic multi-entity dataset generator.

Simulates three non-colluding "entities":
  A - Government Department (HR/identity heavy)
  B - Government Department (licensing/records, different population)
  C - Critical Infrastructure Operator (OT/IT boundary flavor)

Each entity has its own feature distribution (non-IID), its own class
imbalance for the insider-threat label, missing values, outliers,
correlated/decoy features, and mild temporal (campaign) structure that
is only visible when entities' data is considered together -- this is
the "collective intelligence" signal the FL model is meant to learn.

Every record carries a `synthetic_id` used ONLY as ground truth for the
membership-inference attack evaluation. It is never used as a model
feature and is stripped before training.
"""
import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "auth_events_7d", "login_frequency", "off_hours_access_pct",
    "resource_diversity", "failed_auth_rate", "network_bytes_z",
    "security_event_count_30d", "access_diversity_outlier", "decoy_feature",
]

ENTITY_CONFIG = {
    "A": dict(n=22000, pos_rate=0.035, seed_offset=0,
              mean_shift=0.0, spread=1.0, campaign_weeks=(6, 7)),
    "B": dict(n=20000, pos_rate=0.045, seed_offset=100000,
              mean_shift=0.4, spread=1.2, campaign_weeks=(6,)),
    "C": dict(n=21000, pos_rate=0.02,  seed_offset=200000,
              mean_shift=-0.3, spread=1.6, campaign_weeks=(7, 8)),
    "D": dict(n=20000, pos_rate=0.028, seed_offset=300000,
              mean_shift=0.15, spread=1.35, campaign_weeks=(4, 7)),
}
# Entity D = a 4th, distinct government-style entity ("Customs / Border
# Authority" flavor): more automated/service-account traffic, a different
# base rate and a partially-overlapping but not identical campaign window
# to A/C -- this is what lets a 4-entity FL run show a genuinely federated
# ("nobody alone sees the whole campaign") detection story rather than a
# 3-entity toy example.


def _gen_entity(entity_name, cfg, rng):
    n = cfg["n"]
    shift, spread = cfg["mean_shift"], cfg["spread"]

    week = rng.integers(1, 9, size=n)  # 8-week observation window
    weekly_season = 1.0 + 0.15 * np.sin(2 * np.pi * week / 4.0)

    auth_events_7d = np.clip(
        rng.normal(20 + shift * 5, 6 * spread, n) * weekly_season, 0, None
    )
    login_frequency = np.clip(rng.normal(5 + shift, 2 * spread, n) * weekly_season, 0, None)
    off_hours_access_pct = np.clip(rng.beta(2, 8, n) * 100 + shift * 3, 0, 100)
    resource_diversity = np.clip(rng.normal(4 + shift * 0.5, 1.5 * spread, n), 0, None)
    failed_auth_rate = np.clip(
        rng.gamma(1.5, 1.0 + 0.3 * spread, n) + 0.1 * off_hours_access_pct / 10, 0, None
    )
    network_bytes_z = rng.normal(0 + shift, 1.0 * spread, n)
    security_event_count_30d = rng.poisson(1.2 * spread, n)

    # decoy feature: correlated with failed_auth_rate but NOT causal for label
    decoy_feature = failed_auth_rate * 0.6 + rng.normal(0, 1, n)

    # outliers (rare, label-independent) to stress-test DP-SGD clipping norm C
    outlier_mask = rng.random(n) < 0.007
    access_diversity_outlier = resource_diversity.copy()
    access_diversity_outlier[outlier_mask] *= rng.uniform(4, 8, outlier_mask.sum())
    network_bytes_z[outlier_mask] *= rng.uniform(5, 10, outlier_mask.sum())

    # campaign windows: correlated cross-entity anomaly spike (the collective signal)
    campaign_mask = np.isin(week, cfg["campaign_weeks"])
    campaign_boost = campaign_mask * rng.uniform(0.5, 1.5, n)
    failed_auth_rate = failed_auth_rate + campaign_boost
    off_hours_access_pct = np.clip(off_hours_access_pct + campaign_boost * 8, 0, 100)

    # label as logistic function of true signal features (NOT the decoy)
    logit = (
        -4.2
        + 0.09 * failed_auth_rate
        + 0.02 * off_hours_access_pct
        + 0.10 * security_event_count_30d
        + 0.6 * campaign_boost
        + 0.15 * network_bytes_z
        - 0.03 * resource_diversity
    )
    prob = 1 / (1 + np.exp(-logit))
    # rescale to hit target positive rate approximately
    target = cfg["pos_rate"]
    current = prob.mean()
    scale = np.log(target / (1 - target)) - np.log(current / (1 - current + 1e-9))
    prob = 1 / (1 + np.exp(-(logit + scale)))
    label = (rng.random(n) < prob).astype(int)

    df = pd.DataFrame({
        "auth_events_7d": auth_events_7d,
        "login_frequency": login_frequency,
        "off_hours_access_pct": off_hours_access_pct,
        "resource_diversity": resource_diversity,
        "failed_auth_rate": failed_auth_rate,
        "network_bytes_z": network_bytes_z,
        "security_event_count_30d": security_event_count_30d,
        "access_diversity_outlier": access_diversity_outlier,
        "decoy_feature": decoy_feature,
        "week": week,
        "insider_threat_label": label,
        "entity": entity_name,
    })
    df["synthetic_id"] = [f"{entity_name}-{cfg['seed_offset']+i:06d}" for i in range(n)]

    # missing values: 3-8% MCAR on a couple of non-critical columns
    for col in ["login_frequency", "resource_diversity"]:
        miss_mask = rng.random(n) < rng.uniform(0.03, 0.08)
        df.loc[miss_mask, col] = np.nan

    return df


def generate_all(seed=42, out_dir=None, entity_config=None, scale=1.0):
    """
    scale: multiplies every entity's `n` (rounded). Used by the test suite
    to generate a small, fast dataset (e.g. scale=0.01 -> ~200-ish records
    per entity) without duplicating the generation logic.
    """
    rng = np.random.default_rng(seed)
    cfg = entity_config or ENTITY_CONFIG
    frames = []
    for name, c in cfg.items():
        c2 = dict(c)
        if scale != 1.0:
            c2["n"] = max(20, int(c["n"] * scale))
        frames.append(_gen_entity(name, c2, rng))
    full = pd.concat(frames, ignore_index=True)

    # simple imputation (median, computed globally is fine for a synthetic demo;
    # in production this would be computed locally per entity, never pooled)
    for col in ["login_frequency", "resource_diversity"]:
        full[col] = full[col].fillna(full[col].median())

    if out_dir:
        import os
        os.makedirs(out_dir, exist_ok=True)
        for name in cfg:
            full[full.entity == name].to_csv(f"{out_dir}/entity_{name}.csv", index=False)
        full.to_csv(f"{out_dir}/all_entities_POOLED_FOR_NAIVE_BASELINE_ONLY.csv", index=False)
    return full


if __name__ == "__main__":
    df = generate_all(out_dir="/home/claude/ppa-gov/data")
    print(df.groupby("entity")["insider_threat_label"].agg(["count", "mean"]))
    print("total:", len(df), "positive rate:", df.insider_threat_label.mean())
