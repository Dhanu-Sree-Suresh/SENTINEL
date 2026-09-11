"""
Cross-silo horizontal FL orchestration: FedAvg / FedProx, with
optional per-client DP-SGD and optional secure aggregation.

Design choice: each client does ONE full-batch (DP-)SGD step per
round (local_epochs=1, batch_size=len(local_data)). This is a
deliberate, disclosed choice for a small cross-silo setting: it keeps
the number of composed DP releases (rounds) small, which matters a
lot under our conservative, non-subsampled RDP accountant (see
src/accountant.py) -- a full-batch step per round is common practice
in small cross-silo FL and does not require claiming subsampling
amplification we haven't implemented.
"""
import numpy as np
from .model import LogisticRegressionNP
from .dp_sgd import dp_sgd_local_train
from .secure_agg import secure_aggregate
from .accountant import compute_epsilon
from .robust_agg import aggregate as robust_aggregate
from .attacks.poisoning import craft_malicious_update


class Client:
    def __init__(self, name, X, y, standardize_stats=None):
        self.name = name
        if standardize_stats is None:
            self.mu = X.mean(axis=0)
            self.sigma = X.std(axis=0) + 1e-8
        else:
            self.mu, self.sigma = standardize_stats
        self.X = (X - self.mu) / self.sigma
        self.y = y
        self.n = len(X)


def run_federated_training(clients, *, rounds, lr, clip_norm, noise_multiplier,
                            enable_dp, enable_secure_agg, fedprox_mu, seed,
                            firewall=None, aggregation_strategy="mean",
                            malicious_client_name=None, malicious_mode="scale",
                            malicious_scale=25.0):
    """
    Returns (trained_global_model, history, dp_report).
    If `firewall` (a BudgetLedger) is provided, every DP round call is
    logged against it and training halts early for any client whose
    budget is exhausted.

    aggregation_strategy: "mean" (plain FedAvg, no Byzantine robustness),
    "median" or "trimmed_mean" (coordinate-wise robust aggregation, see
    src/robust_agg.py). NOTE: robust aggregation and enable_secure_agg
    are mutually exclusive in this build -- coordinate-wise robust
    rules need to see each client's individual update, which is exactly
    what secure aggregation is designed to hide from the aggregator.
    Requesting both raises an error rather than silently picking one,
    since silently ignoring a requested security control is worse than
    failing loudly.

    malicious_client_name: if set, that client's update is replaced each
    round with an adversarially-crafted one (see src/attacks/poisoning.py)
    -- used by experiments/run_poisoning_experiment.py to compare plain
    FedAvg vs. robust aggregation under an active poisoning attacker.
    """
    if enable_secure_agg and aggregation_strategy != "mean":
        raise ValueError(
            "enable_secure_agg=True is incompatible with a robust "
            "(non-mean) aggregation_strategy in this build: robust rules "
            "require visibility into individual client updates, which "
            "secure aggregation is designed to hide from the aggregator. "
            "Pick one per deployment; see src/robust_agg.py docstring."
        )

    n_features = clients[0].X.shape[1]
    rng = np.random.default_rng(seed)
    global_model = LogisticRegressionNP(n_features, seed=seed)
    history = []
    exhausted = set()

    for rnd in range(rounds):
        client_updates = []
        global_flat = global_model.get_flat_params()

        for c_idx, c in enumerate(clients):
            if firewall is not None and c.name in exhausted:
                continue
            local_model = global_model.copy()
            # NOTE: uses c_idx (stable enumeration order), not hash(c.name) --
            # Python's string hash() is randomized per-process by default
            # (PYTHONHASHSEED), which silently broke run-to-run
            # reproducibility during development. This is exactly the kind
            # of bug "does it survive a second run" is meant to catch.
            local_rng = np.random.default_rng(seed * 1000 + rnd * 10 + c_idx)
            dp_sgd_local_train(
                local_model, c.X, c.y,
                epochs=1, batch_size=c.n, lr=lr,
                clip_norm=clip_norm, noise_multiplier=noise_multiplier,
                enable_dp=enable_dp, rng=local_rng,
                fedprox_mu=fedprox_mu, global_params=global_flat,
            )
            delta = local_model.get_flat_params() - global_flat

            if malicious_client_name is not None and c.name == malicious_client_name:
                delta = craft_malicious_update(delta, mode=malicious_mode, scale=malicious_scale)

            client_updates.append(delta)

            if firewall is not None and enable_dp:
                allowed = firewall.record_round(c.name, clip_norm, noise_multiplier)
                if not allowed:
                    exhausted.add(c.name)

        if len(client_updates) == 0:
            break

        if enable_secure_agg:
            summed, _ = secure_aggregate(client_updates, round_seed=seed * 7919 + rnd)
            avg_delta = summed / len(client_updates)
        else:
            avg_delta = robust_aggregate(client_updates, strategy=aggregation_strategy)

        global_model.set_flat_params(global_flat + avg_delta)
        history.append({"round": rnd, "n_active_clients": len(client_updates)})

    dp_report = None
    if enable_dp:
        max_rounds_used = rounds if firewall is None else max(
            firewall.rounds_used.get(c.name, 0) for c in clients
        )
        eps, delta, alpha = compute_epsilon(noise_multiplier, max_rounds_used, delta=1e-5)
        dp_report = dict(epsilon=eps, delta=1e-5, alpha=alpha,
                          noise_multiplier=noise_multiplier, clip_norm=clip_norm,
                          rounds=max_rounds_used)

    return global_model, history, dp_report


def run_centralized_naive(X, y, epochs=200, lr=0.5, seed=42):
    """
    Baseline 1: pool everything, plain SGD, no privacy, no FL, NO
    regularization -- deliberately representative of "naive" practice
    (an engineer who centralizes the data and trains to convergence
    without thinking about privacy also typically skips regularization
    tuning). This is what makes it a fair, realistic naive baseline
    rather than a straw man: it is exactly as regularized as a
    default sklearn/quick-prototype model would be.
    """
    mu, sigma = X.mean(axis=0), X.std(axis=0) + 1e-8
    Xs = (X - mu) / sigma
    model = LogisticRegressionNP(X.shape[1], l2=0.0, seed=seed)
    rng = np.random.default_rng(seed)
    dp_sgd_local_train(model, Xs, y, epochs=epochs, batch_size=len(Xs), lr=lr,
                        clip_norm=1e9, noise_multiplier=0.0, enable_dp=False, rng=rng)
    return model, (mu, sigma)
