import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
with open(os.path.join(RESULTS_DIR, "results.json")) as f:
    R = json.load(f)

inv = R["gradient_inversion_demo"]
raw_cos = inv["raw"]["mean_cosine_similarity"]
dp_cos = inv["dp_protected"]["mean_cosine_similarity"]
raw_mse = inv["raw"]["median_mse"]
dp_mse = inv["dp_protected"]["median_mse"]

fig, axes = plt.subplots(1, 2, figsize=(9, 4.5))

axes[0].bar(["Raw FL gradient\n(no DP)", "DP-protected\ngradient (clip+noise)"],
            [raw_cos, dp_cos], color=["#d62728", "#2ca02c"])
axes[0].axhline(0, color="gray", linewidth=0.8)
axes[0].set_ylabel("Mean cosine similarity\n(reconstructed vs. true input record)")
axes[0].set_title("Gradient Inversion: Reconstruction Fidelity")
axes[0].set_ylim(-0.2, 1.1)
for i, v in enumerate([raw_cos, dp_cos]):
    axes[0].text(i, v + (0.03 if v >= 0 else -0.06), f"{v:.3f}", ha="center", fontweight="bold")

axes[1].bar(["Raw FL gradient\n(no DP)", "DP-protected\ngradient (clip+noise)"],
            [raw_mse, dp_mse], color=["#d62728", "#2ca02c"])
axes[1].set_ylabel("Median reconstruction MSE\n(lower = closer to exact recovery)")
axes[1].set_title("Gradient Inversion: Reconstruction Error")
for i, v in enumerate([raw_mse, dp_mse]):
    axes[1].text(i, v, f"{v:.2g}", ha="center", va="bottom", fontweight="bold")

fig.suptitle("A raw FL update lets an aggregator recover the exact input record;\n"
             "DP-SGD's clipping + noise breaks this completely", fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(RESULTS_DIR, "chart_gradient_inversion.png"), dpi=150)
print("Saved chart_gradient_inversion.png")
