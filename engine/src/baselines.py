"""
Traditional-ML and small-deep-learning baselines.

These exist ONLY as centralized, no-privacy utility reference points
-- "how good could a model get if you ignored the privacy constraint
entirely" -- requested by the brief's experiment matrix ("traditional
ML", "deep learning" rows). They are NOT wired into DP-SGD, FL,
secure aggregation, or either attack: doing so for a full
scikit-learn RandomForest (non-differentiable, no clean per-example
gradient) or an arbitrary-depth MLP would require materially more
machinery (tree-specific DP mechanisms / DP-SGD over a real autodiff
stack) than this sandboxed, dependency-free environment can
responsibly implement and verify. That boundary is intentional and
disclosed, not an oversight: every OTHER condition in this repo
(centralized-naive, FL, FL+DP, FL+DP+SecAgg+Firewall) uses the same
LogisticRegressionNP model specifically so clipping, the RDP
accountant, and the closed-form gradient-inversion attack all remain
correct and comparable across conditions.
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve


def _threshold_metrics(y, p):
    if len(np.unique(y)) < 2:
        return dict(roc_auc=float("nan"), pr_auc=float("nan"), f1_best=float("nan"))
    roc = roc_auc_score(y, p)
    pr_auc = average_precision_score(y, p)
    prec, rec, thresh = precision_recall_curve(y, p)
    f1s = 2 * prec * rec / (prec + rec + 1e-12)
    return dict(roc_auc=float(roc), pr_auc=float(pr_auc), f1_best=float(np.max(f1s)))


def random_forest_baseline(Xtr, ytr, Xte, yte, seed=42, n_estimators=200, max_depth=8):
    clf = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth,
                                  class_weight="balanced", random_state=seed, n_jobs=1)
    clf.fit(Xtr, ytr)
    p = clf.predict_proba(Xte)[:, 1]
    return _threshold_metrics(yte, p), clf


def gradient_boosting_baseline(Xtr, ytr, Xte, yte, seed=42, n_estimators=200, max_depth=3):
    clf = GradientBoostingClassifier(n_estimators=n_estimators, max_depth=max_depth,
                                      random_state=seed)
    clf.fit(Xtr, ytr)
    p = clf.predict_proba(Xte)[:, 1]
    return _threshold_metrics(yte, p), clf


# ---------------------------------------------------------------------
# Minimal 1-hidden-layer MLP in raw numpy ("deep learning" reference
# point). Trained centrally, full-batch gradient descent, no privacy.
# ---------------------------------------------------------------------
class MLPNumpy:
    def __init__(self, n_in, n_hidden=16, seed=42, l2=1e-3):
        rng = np.random.default_rng(seed)
        self.W1 = rng.normal(0, np.sqrt(2.0 / n_in), size=(n_in, n_hidden))
        self.b1 = np.zeros(n_hidden)
        self.W2 = rng.normal(0, np.sqrt(2.0 / n_hidden), size=(n_hidden,))
        self.b2 = 0.0
        self.l2 = l2

    def _forward(self, X):
        z1 = X @ self.W1 + self.b1
        a1 = np.maximum(0, z1)  # ReLU
        z2 = a1 @ self.W2 + self.b2
        p = 1.0 / (1.0 + np.exp(-np.clip(z2, -30, 30)))
        return z1, a1, p

    def predict_proba(self, X):
        return self._forward(X)[2]

    def fit(self, X, y, epochs=300, lr=0.1):
        n = len(X)
        for _ in range(epochs):
            z1, a1, p = self._forward(X)
            err = (p - y) / n  # dL/dz2

            grad_W2 = a1.T @ err + self.l2 * self.W2
            grad_b2 = err.sum()

            da1 = np.outer(err, self.W2)
            dz1 = da1 * (z1 > 0)
            grad_W1 = X.T @ dz1 + self.l2 * self.W1
            grad_b1 = dz1.sum(axis=0)

            self.W2 -= lr * grad_W2
            self.b2 -= lr * grad_b2
            self.W1 -= lr * grad_W1
            self.b1 -= lr * grad_b1
        return self


def mlp_baseline(Xtr, ytr, Xte, yte, seed=42, n_hidden=16, epochs=400, lr=0.3):
    model = MLPNumpy(Xtr.shape[1], n_hidden=n_hidden, seed=seed)
    model.fit(Xtr, ytr, epochs=epochs, lr=lr)
    p = model.predict_proba(Xte)
    return _threshold_metrics(yte, p), model
