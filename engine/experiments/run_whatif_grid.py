"""
What-if scenario grid.

Precomputes REAL experimental results across a grid of parameters so
the dashboard's what-if simulator can be fully interactive (instant
slider response) while never fabricating a number: every point the
dashboard can show was actually computed here, not interpolated from
a model of the system or invented for the demo. The dashboard looks
up the nearest precomputed grid point live in JavaScript.

Three axes, each answering a different judge question:

  1. PRIVACY axis: epsilon -> (utility AUC, MI attack AUC)
     Reuses experiments/run_experiment.py's results.json sweep
     directly rather than recomputing it -- one source of truth.
     Answers: "what happens if I loosen/tighten the privacy budget?"

  2. SECURITY axis: (malicious_fraction, aggregation_strategy) -> utility AUC
     Extends run_poisoning_experiment.py into a full grid, INCLUDING
     the 2-of-4 (50%) malicious case deliberately included to show
     robust aggregation's real breaking point -- coordinate median and
     trimmed-mean are only guaranteed below 50% malicious, and we show
     what actually happens AT that boundary rather than only showing
     the case where our defense wins. A red-team-honest what-if
     simulator has to include the case that breaks it.
     Answers: "what happens as more entities are compromised, and does
     my choice of aggregation rule actually matter?"

  3. QUERY-DETECTION axis: (freq_threshold, jaccard_threshold) -> the
     query index at which a fixed 10-query differencing-attack
     sequence first triggers an alert (or "not detected").
     Deterministic, no ML training -- exercises
     src/firewall/query_monitor.py directly.
     Answers: "how sensitive/lenient should the Privacy SOC's
     detection thresholds be, and what's the tradeoff?"

Run with:  python3 -m experiments.run_whatif_grid
(after experiments/run_experiment.py, so results.json exists)
"""
import json
import os
import sys
import subprocess
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from src.data_gen import generate_all, FEATURE_COLUMNS
from src.fl_engine import Client, run_federated_training
from src.accountant import find_sigma_for_epsilon
from src.firewall.query_monitor import QueryMonitor

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
BASE_SEED = 42
SEEDS = [1, 2, 3]
ROUNDS = 15
CLIP_NORM = 2.0
DELTA = 1e-5
SECURITY_EPS = 8.0


def _provenance():
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                              cwd=os.path.dirname(RESULTS_DIR),
                                              stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        git_commit = "not_a_git_repo"
    return {
        "timestamp": time.time(),
        "git_commit": git_commit,
        "python_version": sys.version,
        "numpy_version": np.__version__,
        "base_seed": BASE_SEED,
        "seeds": SEEDS,
        "rounds": ROUNDS,
        "clip_norm": CLIP_NORM,
        "delta": DELTA,
    }


def build_full_splits(df, seed, test_size=0.3):
    splits = {}
    for entity in df.entity.unique():
        sub = df[df.entity == entity]
        X = sub[FEATURE_COLUMNS].values
        y = sub["insider_threat_label"].values
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size,
                                               random_state=seed, stratify=y)
        splits[entity] = dict(Xtr=Xtr, ytr=ytr, Xte=Xte, yte=yte)
    return splits


def run_security_grid(df):
    """malicious_fraction in {0, 1, 2} entities out of 4 (0%, 25%, 50%)
    x aggregation_strategy in {mean, median, trimmed_mean}, at a fixed
    moderate epsilon (this axis is about robustness, not privacy)."""
    entities = sorted(df.entity.unique())  # ['A','B','C','D']
    malicious_sets = {
        0: [],
        1: [entities[1]],           # B
        2: [entities[1], entities[2]],  # B, C -- exactly 50%, the theoretical breaking point
    }
    strategies = ["mean", "median", "trimmed_mean"]
    sigma = find_sigma_for_epsilon(SECURITY_EPS, ROUNDS, DELTA)

    grid = []
    for n_malicious, malicious_entities in malicious_sets.items():
        for strategy in strategies:
            aucs = []
            for seed in SEEDS:
                splits = build_full_splits(df, seed)
                clients = [Client(name, s["Xtr"], s["ytr"]) for name, s in splits.items()]
                mu_g = np.mean([c.mu for c in clients], axis=0)
                sigma_g = np.mean([c.sigma for c in clients], axis=0)

                model = None
                if n_malicious == 0:
                    model, _, _ = run_federated_training(
                        clients, rounds=ROUNDS, lr=1.0, clip_norm=CLIP_NORM, noise_multiplier=sigma,
                        enable_dp=True, enable_secure_agg=False, fedprox_mu=0.01, seed=seed,
                        aggregation_strategy=strategy,
                    )
                elif n_malicious == 1:
                    model, _, _ = run_federated_training(
                        clients, rounds=ROUNDS, lr=1.0, clip_norm=CLIP_NORM, noise_multiplier=sigma,
                        enable_dp=True, enable_secure_agg=False, fedprox_mu=0.01, seed=seed,
                        aggregation_strategy=strategy,
                        malicious_client_name=malicious_entities[0], malicious_mode="sign_flip",
                        malicious_scale=8.0,
                    )
                else:
                    # 2 malicious entities: run_federated_training only supports
                    # ONE named malicious client, so we simulate a second by
                    # monkey-patching a second craft step via two sequential
                    # single-malicious passes is NOT equivalent; instead we
                    # directly reimplement the round loop's aggregation call
                    # for this one case using the same primitives, so the
                    # 50%-malicious point is a real computation, not a proxy.
                    from src.model import LogisticRegressionNP
                    from src.dp_sgd import dp_sgd_local_train
                    from src.robust_agg import aggregate as robust_aggregate
                    from src.attacks.poisoning import craft_malicious_update

                    n_features = clients[0].X.shape[1]
                    global_model = LogisticRegressionNP(n_features, seed=seed)
                    for rnd in range(ROUNDS):
                        updates = []
                        global_flat = global_model.get_flat_params()
                        for c_idx, c in enumerate(clients):
                            local_model = global_model.copy()
                            local_rng = np.random.default_rng(seed * 1000 + rnd * 10 + c_idx)
                            dp_sgd_local_train(local_model, c.X, c.y, epochs=1, batch_size=c.n,
                                                lr=1.0, clip_norm=CLIP_NORM, noise_multiplier=sigma,
                                                enable_dp=True, rng=local_rng, fedprox_mu=0.01,
                                                global_params=global_flat)
                            delta = local_model.get_flat_params() - global_flat
                            if c.name in malicious_entities:
                                delta = craft_malicious_update(delta, mode="sign_flip", scale=8.0)
                            updates.append(delta)
                        avg_delta = robust_aggregate(updates, strategy=strategy)
                        global_model.set_flat_params(global_flat + avg_delta)
                    model = global_model

                Xte = np.concatenate([s["Xte"] for s in splits.values()])
                yte = np.concatenate([s["yte"] for s in splits.values()])
                p = model.predict_proba((Xte - mu_g) / sigma_g)
                aucs.append(roc_auc_score(yte, p) if len(np.unique(yte)) > 1 else float("nan"))

            grid.append({
                "malicious_fraction": n_malicious / len(entities),
                "n_malicious": n_malicious,
                "malicious_entities": malicious_entities,
                "aggregation_strategy": strategy,
                "utility_auc_mean": float(np.mean(aucs)),
                "utility_auc_std": float(np.std(aucs)),
            })
            print(f"  malicious={n_malicious}/{len(entities)} strategy={strategy:14s} "
                  f"-> AUC={np.mean(aucs):.3f}+-{np.std(aucs):.3f}")
    return grid


def run_query_detection_grid():
    """
    freq_threshold x jaccard_threshold -> query index of first alert,
    against TWO distinct fixed attack sequences (both deterministic):

      - "differencing": the classic MI-probing pattern (same filter,
        excluding one more individual each query) -- exercises the
        jaccard/similarity detector primarily.
      - "burst_distinct": many queries in a short window with
        UNRELATED filters (no similarity signature at all) -- this is
        what actually exercises freq_threshold in isolation. Without
        this second scenario the grid would (correctly, but
        uninformatively) show jaccard_threshold dominating every
        result, since the differencing pattern alone triggers before
        a typical freq_threshold would -- verified empirically while
        building this grid, and worth keeping both scenarios so the
        dashboard's threshold sliders are both actually informative.
    """
    freq_thresholds = [3, 5, 8]
    jaccard_thresholds = [0.6, 0.8, 0.95]
    base = {"region": "dubai", "department": "licensing"}

    grid = []
    for ft in freq_thresholds:
        for jt in jaccard_thresholds:
            # scenario 1: differencing attack
            qm1 = QueryMonitor(window_seconds=60, freq_threshold=ft, jaccard_threshold=jt)
            first_diff = None
            for i in range(10):
                filt = dict(base)
                if i >= 2:
                    filt["exclude_id"] = f"person_{i}"
                alert = qm1.submit_query("analyst_x", filt, ts=i * 5.0)
                if alert and first_diff is None:
                    first_diff = i

            # scenario 2: burst of distinct, unrelated queries (no similarity signature)
            qm2 = QueryMonitor(window_seconds=60, freq_threshold=ft, jaccard_threshold=jt)
            first_burst = None
            for i in range(10):
                filt = {"region": f"region_{i}", "department": f"dept_{i}", "metric": f"m{i}"}
                alert = qm2.submit_query("analyst_y", filt, ts=i * 5.0)
                if alert and first_burst is None:
                    first_burst = i

            grid.append({
                "freq_threshold": ft, "jaccard_threshold": jt,
                "differencing_first_alert_index": first_diff,
                "differencing_detected": first_diff is not None,
                "burst_first_alert_index": first_burst,
                "burst_detected": first_burst is not None,
            })
    return grid


def main():
    print("=" * 70)
    print("Loading existing privacy sweep from results.json ...")
    with open(os.path.join(RESULTS_DIR, "results.json")) as f:
        main_results = json.load(f)
    privacy_axis = []
    for eps_key, r in main_results["3_fl_dp_sweep"].items():
        privacy_axis.append({
            "epsilon_target": float(eps_key),
            "epsilon_actual": r["actual_epsilon"],
            "utility_auc_mean": r["utility"]["roc_auc_mean"],
            "utility_auc_std": r["utility"]["roc_auc_std"],
            "mi_attack_auc_mean": r["mi_attack"]["subgroup_auc_mean"],
            "mi_attack_auc_std": r["mi_attack"]["subgroup_auc_std"],
        })
    privacy_axis.sort(key=lambda r: r["epsilon_actual"])
    # anchor points: naive / FL-no-DP, for the dashboard's reference lines
    anchors = {
        "naive_centralized": {
            "utility_auc": main_results["1_centralized_naive"]["utility"]["roc_auc_mean"],
            "mi_attack_auc": main_results["1_centralized_naive"]["mi_attack"]["subgroup_auc_mean"],
        },
        "fl_no_dp": {
            "utility_auc": main_results["2_fl_no_dp"]["utility"]["roc_auc_mean"],
            "mi_attack_auc": main_results["2_fl_no_dp"]["mi_attack"]["subgroup_auc_mean"],
        },
    }

    print("\nGenerating full-scale dataset for the security grid ...")
    df = generate_all(seed=BASE_SEED, out_dir=os.path.join(os.path.dirname(RESULTS_DIR), "data"))

    print("\nComputing SECURITY what-if grid (malicious_fraction x aggregation_strategy) ...")
    security_grid = run_security_grid(df)

    print("\nComputing QUERY-DETECTION what-if grid (freq_threshold x jaccard_threshold) ...")
    query_grid = run_query_detection_grid()

    output = {
        "provenance": _provenance(),
        "privacy_axis": privacy_axis,
        "anchors": anchors,
        "security_grid": security_grid,
        "query_detection_grid": query_grid,
    }

    out_path = os.path.join(RESULTS_DIR, "whatif_grid.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print("\nSaved what-if grid to", out_path)
    return output


if __name__ == "__main__":
    main()
