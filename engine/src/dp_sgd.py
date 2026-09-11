"""
DP-SGD local training step (Abadi et al., 2016), implemented directly
in numpy against the LogisticRegressionNP model.

Per step, on a local minibatch of size m:
  1. compute PER-EXAMPLE gradients
  2. clip each example's gradient to L2 norm C
  3. sum the clipped gradients
  4. add Gaussian noise N(0, sigma^2 * C^2 * I) to the summed gradient
  5. divide by m and take a standard SGD step

This gives a formal (record-level) DP guarantee on the resulting
gradient sum released at every step (and, by composition, on every
model update / FL round it feeds into). See src/accountant.py for the
Renyi-DP -> (epsilon, delta) conversion used to report the final budget.

`enable_dp=False` runs the identical loop with clipping/noise disabled,
used for the "FL without DP" baseline, so the only difference between
conditions is the privacy mechanism, not the optimizer.
"""
import numpy as np
from .model import LogisticRegressionNP


def clip_gradients(grads, clip_norm):
    norms = np.linalg.norm(grads, axis=1, keepdims=True)
    factor = np.minimum(1.0, clip_norm / (norms + 1e-12))
    return grads * factor


def dp_sgd_local_train(model: LogisticRegressionNP, X, y, *, epochs, batch_size,
                        lr, clip_norm, noise_multiplier, enable_dp, rng,
                        fedprox_mu=0.0, global_params=None):
    """Runs local epochs of (DP-)SGD in place on `model`. Returns number of steps taken."""
    n = len(X)
    steps = 0
    for _ in range(epochs):
        perm = rng.permutation(n)
        for start in range(0, n, batch_size):
            idx = perm[start:start + batch_size]
            Xb, yb = X[idx], y[idx]
            if len(Xb) == 0:
                continue
            grads = model.per_example_gradients(Xb, yb)  # (m, d+1)

            if enable_dp:
                grads = clip_gradients(grads, clip_norm)
                summed = grads.sum(axis=0)
                noise = rng.normal(0, noise_multiplier * clip_norm, size=summed.shape)
                summed = summed + noise
                mean_grad = summed / len(Xb)
            else:
                mean_grad = grads.mean(axis=0)

            grad_w, grad_b = mean_grad[:-1], mean_grad[-1]

            # FedProx proximal term: pulls local model toward the global model
            # to stabilize training under non-IID client data.
            if fedprox_mu > 0 and global_params is not None:
                gw, gb = global_params[:-1], global_params[-1]
                grad_w = grad_w + fedprox_mu * (model.w - gw)
                grad_b = grad_b + fedprox_mu * (model.b - gb)

            model.apply_update(-lr * grad_w, -lr * grad_b)
            steps += 1
    return steps
