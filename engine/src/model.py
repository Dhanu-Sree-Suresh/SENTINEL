"""
Minimal logistic regression implemented in raw numpy so the whole
pipeline runs with no deep-learning framework (no GPU / heavy deps
required to reproduce the demo -- a deliberate feasibility choice).

Exposes per-example gradients, which is what both DP-SGD (clipping)
and the gradient-inversion attack need.
"""
import numpy as np


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


class LogisticRegressionNP:
    def __init__(self, n_features, l2=1e-4, seed=0):
        rng = np.random.default_rng(seed)
        self.w = rng.normal(0, 0.01, n_features)
        self.b = 0.0
        self.l2 = l2

    def predict_proba(self, X):
        return sigmoid(X @ self.w + self.b)

    def loss_per_example(self, X, y):
        p = np.clip(self.predict_proba(X), 1e-7, 1 - 1e-7)
        return -(y * np.log(p) + (1 - y) * np.log(1 - p))

    def per_example_gradients(self, X, y):
        """Returns (n_samples, n_features+1) gradient matrix, last column = bias grad."""
        p = self.predict_proba(X)
        err = (p - y)  # (n,)
        grad_w = X * err[:, None]  # (n, d)
        grad_b = err  # (n,)
        grad_w += self.l2 * self.w[None, :]  # l2 reg (applied per-example, small)
        return np.concatenate([grad_w, grad_b[:, None]], axis=1)

    def apply_update(self, delta_w, delta_b, lr=1.0):
        self.w = self.w + lr * delta_w
        self.b = self.b + lr * delta_b

    def get_flat_params(self):
        return np.concatenate([self.w, [self.b]])

    def set_flat_params(self, flat):
        self.w = flat[:-1].copy()
        self.b = float(flat[-1])

    def copy(self):
        m = LogisticRegressionNP(len(self.w), l2=self.l2)
        m.w = self.w.copy()
        m.b = self.b
        return m
