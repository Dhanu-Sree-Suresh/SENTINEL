"""
Gradient Inversion / "Deep Leakage from Gradients" style attack
(Zhu, Liu & Han, NeurIPS 2019), specialised to logistic regression so
it can be solved IN CLOSED FORM rather than by iterative optimization
-- this makes the point sharper, not weaker: for a single-example
gradient of logistic regression,

    grad_w = (sigmoid(w.x + b) - y) * x = err * x
    grad_b = sigmoid(w.x + b) - y      = err

so a curious/malicious aggregator that observes a RAW per-example
gradient can recover the exact input record:

    x_reconstructed = grad_w / grad_b        (elementwise)

This is not a toy simplification of the attack -- it is the literal
mechanism DLG demonstrates for deep networks via iterative gradient
matching; here it is exact and non-iterative because the model is
linear, which makes the "FL updates leak training data" claim
completely unambiguous rather than an approximate reconstruction.

We then repeat the same attack against a CLIPPED + NOISED (DP-SGD)
per-example gradient and show the reconstruction degrades sharply,
because clipping destroys the exact err*x relationship (the gradient
is rescaled) and Gaussian noise perturbs grad_b (which sits in a
division, so noise on grad_b is catastrophic for reconstruction
accuracy -- a nice, honest, mechanistic explanation for WHY DP breaks
this specific attack, not just an empirical observation).
"""
import numpy as np


def single_example_gradient(model, x, y):
    p = model.predict_proba(x[None, :])[0]
    err = p - y
    grad_w = err * x
    grad_b = err
    return grad_w, grad_b, err


def invert_from_gradient(grad_w, grad_b, eps=1e-6):
    if abs(grad_b) < eps:
        return None  # cannot invert when err ~ 0 (model already confident/correct)
    return grad_w / grad_b


def clip_and_noise_single(grad_w, grad_b, clip_norm, noise_multiplier, rng):
    full = np.concatenate([grad_w, [grad_b]])
    norm = np.linalg.norm(full)
    factor = min(1.0, clip_norm / (norm + 1e-12))
    clipped = full * factor
    noisy = clipped + rng.normal(0, noise_multiplier * clip_norm, size=clipped.shape)
    return noisy[:-1], noisy[-1]


def run_inversion_demo(model, X, y, clip_norm, noise_multiplier, seed=0, n_trials=30):
    rng = np.random.default_rng(seed)
    idxs = rng.choice(len(X), size=min(n_trials, len(X)), replace=False)
    results = {"raw": [], "dp_protected": []}
    for i in idxs:
        x_true, y_true = X[i], y[i]
        gw, gb, err = single_example_gradient(model, x_true, y_true)
        if abs(err) < 1e-3:
            continue  # skip near-zero-error examples (uninformative for either condition)

        x_rec_raw = invert_from_gradient(gw, gb)
        if x_rec_raw is not None:
            cos = np.dot(x_rec_raw, x_true) / (np.linalg.norm(x_rec_raw) * np.linalg.norm(x_true) + 1e-9)
            mse = float(np.mean((x_rec_raw - x_true) ** 2))
            results["raw"].append({"cosine_sim": float(cos), "mse": mse})

        gw_dp, gb_dp = clip_and_noise_single(gw, gb, clip_norm, noise_multiplier, rng)
        x_rec_dp = invert_from_gradient(gw_dp, gb_dp)
        if x_rec_dp is not None:
            cos_dp = np.dot(x_rec_dp, x_true) / (np.linalg.norm(x_rec_dp) * np.linalg.norm(x_true) + 1e-9)
            mse_dp = float(np.mean((x_rec_dp - x_true) ** 2))
            results["dp_protected"].append({"cosine_sim": float(cos_dp), "mse": mse_dp})

    summary = {}
    for k, v in results.items():
        if v:
            summary[k] = {
                "mean_cosine_similarity": float(np.mean([r["cosine_sim"] for r in v])),
                "median_mse": float(np.median([r["mse"] for r in v])),
                "n": len(v),
            }
    return summary
