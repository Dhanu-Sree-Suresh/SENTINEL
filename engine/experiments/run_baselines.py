"""
Traditional-ML (Random Forest, Gradient Boosting) and small-neural-net
utility baselines, run CENTRALIZED (pooled data), on the FULL,
unsampled dataset (20,000+ records per entity) -- i.e. with the
privacy constraint completely ignored. These are reference ceilings:
"how good could a model realistically get on this task if you could
pool everything," so the deck can honestly say what utility cost the
federated + DP-protected system pays relative to the best a naive,
unconstrained approach could do -- not just relative to a matched
naive linear model.

None of these baselines feed into the FL / DP / attack pipeline (see
src/baselines.py docstring for why: no per-example gradient / clean
DP-SGD story for a random forest or an ad hoc autodiff-free deep net).

Run with:  python3 -m experiments.run_baselines
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from sklearn.model_selection import train_test_split

from src.data_gen import generate_all, FEATURE_COLUMNS
from src.baselines import random_forest_baseline, gradient_boosting_baseline, mlp_baseline
from src.fl_engine import run_centralized_naive
from src.model import LogisticRegressionNP
from src.provenance import get_provenance

BASE_SEED = 42
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def utility_metrics_lr(model, mu, sigma, X, y):
    from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve
    Xs = (X - mu) / sigma
    p = model.predict_proba(Xs)
    roc = roc_auc_score(y, p)
    pr_auc = average_precision_score(y, p)
    prec, rec, thresh = precision_recall_curve(y, p)
    f1s = 2 * prec * rec / (prec + rec + 1e-12)
    return dict(roc_auc=float(roc), pr_auc=float(pr_auc), f1_best=float(np.max(f1s)))


def main():
    print("=" * 70)
    print("Generating FULL-SCALE dataset for centralized utility baselines ...")
    df = generate_all(seed=BASE_SEED, out_dir=os.path.join(os.path.dirname(RESULTS_DIR), "data"))
    X = df[FEATURE_COLUMNS].values
    y = df["insider_threat_label"].values
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=BASE_SEED, stratify=y)
    print(f"  pooled train={len(Xtr)} test={len(Xte)} pos_rate={ytr.mean():.4f}")

    results = {}

    print("\n[1/4] Logistic regression (same model used throughout the privacy pipeline) ...")
    lr_model, (mu, sigma) = run_centralized_naive(Xtr, ytr, epochs=800, lr=1.0, seed=BASE_SEED)
    results["logistic_regression"] = utility_metrics_lr(lr_model, mu, sigma, Xte, yte)
    print(f"  {results['logistic_regression']}")

    print("\n[2/4] Random Forest (traditional ML, no privacy, no FL) ...")
    rf_metrics, _ = random_forest_baseline(Xtr, ytr, Xte, yte, seed=BASE_SEED)
    results["random_forest"] = rf_metrics
    print(f"  {rf_metrics}")

    print("\n[3/4] Gradient Boosting (traditional ML, no privacy, no FL) ...")
    gb_metrics, _ = gradient_boosting_baseline(Xtr, ytr, Xte, yte, seed=BASE_SEED)
    results["gradient_boosting"] = gb_metrics
    print(f"  {gb_metrics}")

    print("\n[4/4] Small MLP (deep-learning reference point, no privacy, no FL) ...")
    mu_mlp, sigma_mlp = Xtr.mean(axis=0), Xtr.std(axis=0) + 1e-8
    Xtrs, Xtes = (Xtr - mu_mlp) / sigma_mlp, (Xte - mu_mlp) / sigma_mlp
    mlp_metrics, _ = mlp_baseline(Xtrs, ytr, Xtes, yte, seed=BASE_SEED)
    results["mlp"] = mlp_metrics
    print(f"  {mlp_metrics}")

    print("\nSummary (ROC-AUC, centralized/no-privacy ceiling, for reference only):")
    for k, v in results.items():
        print(f"  {k:20s} roc_auc={v['roc_auc']:.3f}  pr_auc={v['pr_auc']:.3f}  f1_best={v['f1_best']:.3f}")

    with open(os.path.join(RESULTS_DIR, "baseline_results.json"), "w") as f:
        json.dump({"results": results,
                    "provenance": get_provenance(experiment="run_baselines", base_seed=BASE_SEED)},
                   f, indent=2)
    print("\nSaved baseline_results.json to", RESULTS_DIR)
    return results


if __name__ == "__main__":
    main()
