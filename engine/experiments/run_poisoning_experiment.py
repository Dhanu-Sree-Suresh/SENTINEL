"""
Byzantine-robustness experiment.

Runs on the FULL, unsampled per-entity dataset (20,000+ records per
entity) -- this experiment is about scale and resilience, not the
attack-track's overfitting-driven privacy story, so there is no
reason to subsample here.

Compares four conditions, all otherwise identical (FL+DP at a fixed,
moderate epsilon):
  1. Honest cohort, plain FedAvg               (reference)
  2. One malicious entity (scale-up attack), plain FedAvg
  3. One malicious entity (scale-up attack), coordinate-wise MEDIAN
  4. One malicious entity (scale-up attack), coordinate-wise TRIMMED MEAN

If robust aggregation is doing its job, conditions 3 and 4 should
recover utility close to condition 1 despite the same attacker being
present in conditions 2-4; condition 2 should show a clear utility
collapse relative to condition 1.

Run with:  python3 -m experiments.run_poisoning_experiment
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

from src.data_gen import generate_all, FEATURE_COLUMNS
from src.fl_engine import Client, run_federated_training
from src.accountant import find_sigma_for_epsilon
from src.provenance import get_provenance

BASE_SEED = 42
SEEDS = [1, 2, 3]
ROUNDS = 15
CLIP_NORM = 2.0
TARGET_EPS = 8.0  # a looser, "normal-tier" operating point -- this experiment
                   # is about Byzantine robustness, not re-litigating the
                   # privacy/utility sweep already covered in run_experiment.py
DELTA = 1e-5
MALICIOUS_ENTITY = "B"
MALICIOUS_MODE = "sign_flip"  # actively corrupts the gradient direction --
                               # a naive "scale" attack (same direction,
                               # amplified) turned out NOT to move ROC-AUC
                               # much in testing, because AUC is rank-based
                               # and invariant to same-direction rescaling;
                               # sign-flip is the mode that actually
                               # demonstrates why an unprotected aggregator
                               # is a real security exposure, not just a
                               # theoretical one. Both modes are implemented
                               # in src/attacks/poisoning.py.
MALICIOUS_SCALE = 8.0

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def build_full_splits(df, seed, test_size=0.3):
    """
    Full-scale splits (NO subsampling) -- ~14-15k train / ~6-7k holdout
    per entity. test_size=0.3 (rather than the attack-track's 0.75) is
    appropriate here because this experiment is not trying to induce
    overfitting; it is testing robustness under realistic, generous
    per-entity training-set sizes.
    """
    splits = {}
    for entity in df.entity.unique():
        sub = df[df.entity == entity]
        X = sub[FEATURE_COLUMNS].values
        y = sub["insider_threat_label"].values
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size,
                                               random_state=seed, stratify=y)
        splits[entity] = dict(Xtr=Xtr, ytr=ytr, Xte=Xte, yte=yte)
    return splits


def run_once(splits, seed, *, aggregation_strategy, malicious):
    clients = [Client(name, s["Xtr"], s["ytr"]) for name, s in splits.items()]
    mu_g = np.mean([c.mu for c in clients], axis=0)
    sigma_g = np.mean([c.sigma for c in clients], axis=0)
    sigma = find_sigma_for_epsilon(TARGET_EPS, ROUNDS, DELTA)

    model, hist, dp = run_federated_training(
        clients, rounds=ROUNDS, lr=1.0, clip_norm=CLIP_NORM, noise_multiplier=sigma,
        enable_dp=True, enable_secure_agg=False, fedprox_mu=0.01, seed=seed,
        aggregation_strategy=aggregation_strategy,
        malicious_client_name=MALICIOUS_ENTITY if malicious else None,
        malicious_mode=MALICIOUS_MODE, malicious_scale=MALICIOUS_SCALE,
    )
    Xte = np.concatenate([s["Xte"] for s in splits.values()])
    yte = np.concatenate([s["yte"] for s in splits.values()])
    p = model.predict_proba((Xte - mu_g) / sigma_g)
    auc = roc_auc_score(yte, p) if len(np.unique(yte)) > 1 else float("nan")
    return auc


def main():
    print("=" * 70)
    print("Generating FULL-SCALE synthetic dataset (no subsampling) ...")
    df = generate_all(seed=BASE_SEED, out_dir=os.path.join(os.path.dirname(RESULTS_DIR), "data"))
    print(df.groupby("entity")["insider_threat_label"].agg(["count", "mean"]))

    conditions = [
        ("1_honest_fedavg",        dict(aggregation_strategy="mean",         malicious=False)),
        ("2_attacked_fedavg",      dict(aggregation_strategy="mean",         malicious=True)),
        ("3_attacked_median",      dict(aggregation_strategy="median",       malicious=True)),
        ("4_attacked_trimmed_mean", dict(aggregation_strategy="trimmed_mean", malicious=True)),
    ]

    results = {}
    for label, cfg in conditions:
        aucs = []
        for seed in SEEDS:
            splits = build_full_splits(df, seed)
            auc = run_once(splits, seed, **cfg)
            aucs.append(auc)
        results[label] = dict(auc_mean=float(np.mean(aucs)), auc_std=float(np.std(aucs)),
                               auc_runs=[float(a) for a in aucs], **cfg)
        print(f"  {label:30s} -> ROC-AUC = {np.mean(aucs):.3f} +- {np.std(aucs):.3f}  "
              f"(malicious entity: {MALICIOUS_ENTITY}, scale={MALICIOUS_SCALE}x)"
              if cfg["malicious"] else
              f"  {label:30s} -> ROC-AUC = {np.mean(aucs):.3f} +- {np.std(aucs):.3f}  (no attacker)")

    honest = results["1_honest_fedavg"]["auc_mean"]
    attacked = results["2_attacked_fedavg"]["auc_mean"]
    recovered_median = results["3_attacked_median"]["auc_mean"]
    recovered_trimmed = results["4_attacked_trimmed_mean"]["auc_mean"]
    print("\nSummary:")
    print(f"  Utility drop from attack under plain FedAvg: {honest - attacked:+.3f} AUC")
    print(f"  Utility recovered with coordinate median:     {recovered_median - attacked:+.3f} AUC "
          f"({(recovered_median - attacked) / max(1e-6, honest - attacked) * 100:.0f}% of the gap closed)")
    print(f"  Utility recovered with trimmed mean:          {recovered_trimmed - attacked:+.3f} AUC "
          f"({(recovered_trimmed - attacked) / max(1e-6, honest - attacked) * 100:.0f}% of the gap closed)")

    with open(os.path.join(RESULTS_DIR, "poisoning_results.json"), "w") as f:
        json.dump({"results": results,
                    "provenance": get_provenance(
                        experiment="run_poisoning_experiment", seeds=SEEDS, rounds=ROUNDS,
                        clip_norm=CLIP_NORM, target_eps=TARGET_EPS, delta=DELTA,
                        malicious_entity=MALICIOUS_ENTITY, malicious_mode=MALICIOUS_MODE,
                        malicious_scale=MALICIOUS_SCALE, base_seed=BASE_SEED)},
                   f, indent=2)
    print("\nSaved poisoning_results.json to", RESULTS_DIR)
    return results


if __name__ == "__main__":
    main()
