import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

with open(os.path.join(RESULTS_DIR, "results.json")) as f:
    R = json.load(f)

sweep = R["3_fl_dp_sweep"]
eps_vals = sorted([float(k) for k in sweep.keys()])
key_by_eps = {float(k): k for k in sweep.keys()}
util = [sweep[key_by_eps[e]]["utility"]["roc_auc_mean"] for e in eps_vals]
util_std = [sweep[key_by_eps[e]]["utility"]["roc_auc_std"] for e in eps_vals]
mi = [sweep[key_by_eps[e]]["mi_attack"]["subgroup_auc_mean"] for e in eps_vals]
mi_std = [sweep[key_by_eps[e]]["mi_attack"]["subgroup_auc_std"] for e in eps_vals]

naive_util = R["1_centralized_naive"]["utility"]["roc_auc_mean"]
naive_mi = R["1_centralized_naive"]["mi_attack"]["subgroup_auc_mean"]
fl_util = R["2_fl_no_dp"]["utility"]["roc_auc_mean"]
fl_mi = R["2_fl_no_dp"]["mi_attack"]["subgroup_auc_mean"]

# ---- Chart 1: privacy/utility/attack trade-off vs epsilon ----
fig, ax1 = plt.subplots(figsize=(8, 5))
ax1.errorbar(eps_vals, util, yerr=util_std, marker="o", color="#1f77b4",
             label="Model utility (ROC-AUC)", capsize=3)
ax1.errorbar(eps_vals, mi, yerr=mi_std, marker="s", color="#d62728",
             label="MI attack success (high-risk subgroup AUC)", capsize=3)
ax1.axhline(0.5, color="gray", linestyle="--", linewidth=1, label="Random guessing (AUC=0.5)")
ax1.axhline(naive_util, color="#1f77b4", linestyle=":", linewidth=1.3,
            label=f"Naive centralized utility ({naive_util:.2f})")
ax1.axhline(naive_mi, color="#d62728", linestyle=":", linewidth=1.3,
            label=f"Naive centralized MI attack ({naive_mi:.2f})")
ax1.set_xscale("log")
ax1.set_xlabel("Privacy budget epsilon (log scale) — smaller = more private")
ax1.set_ylabel("AUC")
ax1.set_title("Privacy / Utility / Attack-Success Trade-off\nFederated Learning + DP-SGD, averaged over 3 seeds")
ax1.legend(fontsize=8, loc="lower right")
ax1.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(RESULTS_DIR, "chart_privacy_utility_tradeoff.png"), dpi=150)
plt.close(fig)

# ---- Chart 2: bar comparison across the 4 headline conditions ----
conditions = ["1. Centralized\nnaive", "2. FL\n(no DP)", "3. FL+DP\n(eps=4)", "4. Proposed\n(FL+DP+SecAgg+Firewall)"]
eps4_key = key_by_eps[4.0]
util_bars = [naive_util, fl_util, sweep[eps4_key]["utility"]["roc_auc_mean"],
             R["4_proposed"]["utility"]["roc_auc_mean"]]
mi_bars = [naive_mi, fl_mi, sweep[eps4_key]["mi_attack"]["subgroup_auc_mean"],
           R["4_proposed"]["mi_attack"]["subgroup_auc_mean"]]

x = range(len(conditions))
width = 0.35
fig, ax = plt.subplots(figsize=(9, 5))
ax.bar([i - width / 2 for i in x], util_bars, width, label="Model utility (ROC-AUC)", color="#1f77b4")
ax.bar([i + width / 2 for i in x], mi_bars, width, label="MI attack success (AUC)", color="#d62728")
ax.axhline(0.5, color="gray", linestyle="--", linewidth=1)
ax.set_xticks(list(x))
ax.set_xticklabels(conditions)
ax.set_ylabel("AUC")
ax.set_title("Headline Comparison Across the Four Experimental Conditions")
ax.legend()
ax.grid(alpha=0.3, axis="y")
fig.tight_layout()
fig.savefig(os.path.join(RESULTS_DIR, "chart_condition_comparison.png"), dpi=150)
plt.close(fig)

print("Saved charts to", RESULTS_DIR)
