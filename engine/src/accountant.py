"""
Renyi Differential Privacy (RDP) accountant.

We account CONSERVATIVELY for the plain (non-subsampled) Gaussian
mechanism, composed over T released gradient sums:

    RDP of a single Gaussian-mechanism release with noise multiplier
    sigma, at RDP order alpha:               eps_RDP(alpha) = alpha / (2 * sigma^2)

    RDP composes additively over T independent releases:
                                              eps_RDP_T(alpha) = T * alpha / (2 * sigma^2)

    Converting RDP to standard (epsilon, delta)-DP (Mironov 2017,
    Prop. 3 / Canonne et al. 2020 tight conversion, simple form):
                                              eps = eps_RDP(alpha) + ln(1/delta) / (alpha - 1)

    We minimize over a grid of alpha to get the tightest reportable
    epsilon for a chosen delta.

We deliberately DO NOT claim privacy amplification by subsampling
(Wang et al. 2019 / the moments-accountant subsampling bound), even
though our minibatches ARE subsampled -- implementing that correctly
requires care we are not confident enough in to certify without
external tooling (Opacus/TF-Privacy) unavailable in this sandbox.
This makes the reported epsilon a conservative (worse than the
true/tight value achievable with subsampling credit) but CORRECT
upper bound under the composition it actually accounts for. This
trade-off is stated explicitly in the results report and the deck --
we would swap in Opacus's accountant for a production build.
"""
import numpy as np

ALPHA_GRID = np.concatenate([
    np.arange(1.5, 10, 0.5),
    np.arange(10, 64, 2),
    np.arange(64, 512, 8),
])


def rdp_gaussian(alpha, sigma):
    return alpha / (2 * sigma ** 2)


def compose_rdp(sigma, num_steps):
    """RDP of the composition of `num_steps` independent Gaussian-mechanism releases."""
    return num_steps * rdp_gaussian(ALPHA_GRID, sigma)


def rdp_to_eps(rdp_values, delta):
    eps_candidates = rdp_values + np.log(1.0 / delta) / (ALPHA_GRID - 1.0)
    best_idx = np.argmin(eps_candidates)
    return float(eps_candidates[best_idx]), float(ALPHA_GRID[best_idx])


def compute_epsilon(sigma, num_steps, delta):
    """
    Returns (epsilon, delta, optimal_alpha) for `num_steps` compositions
    of the Gaussian mechanism with noise multiplier `sigma`.
    """
    rdp_vals = compose_rdp(sigma, num_steps)
    eps, alpha = rdp_to_eps(rdp_vals, delta)
    return eps, delta, alpha


def find_sigma_for_epsilon(target_eps, num_steps, delta, lo=0.3, hi=50.0, tol=1e-3, max_iter=60):
    """Binary search for the noise multiplier sigma achieving `target_eps` at `num_steps`."""
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        eps, _, _ = compute_epsilon(mid, num_steps, delta)
        if eps > target_eps:
            lo = mid  # need MORE noise (higher sigma) to lower eps
        else:
            hi = mid
        if hi - lo < tol:
            break
    return hi


if __name__ == "__main__":
    for sigma in [0.6, 1.0, 1.5, 2.5, 4.0]:
        eps, delta, alpha = compute_epsilon(sigma, num_steps=200, delta=1e-5)
        print(f"sigma={sigma:>4} steps=200 delta=1e-5 -> epsilon={eps:.3f} (alpha*={alpha})")
