"""
Secure aggregation, simulated via pairwise additive masking
(Bonawitz et al., CCS 2017 -- simplified, single-process simulation).

Each pair of clients (i, j) shares a symmetric random mask vector
derived from a shared per-round seed (in a real deployment this would
come from a Diffie-Hellman key agreement; here we simulate the
already-agreed shared secret directly, since the point being
demonstrated is the AGGREGATION PROPERTY, not the key-exchange
protocol -- this simplification is stated explicitly in the README).

Client i adds +mask_ij for j > i and -mask_ij for j < i to its own
update before sending it to the aggregator. When the aggregator sums
all received (masked) updates, every pairwise mask cancels out
exactly, so the aggregator recovers the TRUE SUM of the underlying
updates but never observes any individual client's update.

This is complementary to, not a substitute for, DP-SGD:
  - Secure aggregation hides each client's update from the aggregator.
  - DP-SGD bounds what the *released aggregate/model* reveals about
    any one training record, including to someone who only ever sees
    the final aggregate (i.e. it protects against exactly the honest
    aggregator who correctly only sees the sum).
"""
import numpy as np


def generate_pairwise_masks(num_clients, dim, round_seed):
    """Deterministic per-round pairwise masks, shared secret simulated via a common seed."""
    masks = np.zeros((num_clients, dim))
    for i in range(num_clients):
        for j in range(i + 1, num_clients):
            pair_rng = np.random.default_rng(hash((round_seed, i, j)) % (2 ** 32))
            m = pair_rng.normal(0, 5.0, dim)
            masks[i] += m
            masks[j] -= m
    return masks


def secure_aggregate(client_updates, round_seed):
    """
    client_updates: list of np.array, one flattened update per client.
    Returns the TRUE SUM, computed the way a real aggregator would --
    by summing masked updates -- to demonstrate the cancellation
    property, not by cheating and summing the raw updates directly.
    """
    num_clients = len(client_updates)
    dim = len(client_updates[0])
    masks = generate_pairwise_masks(num_clients, dim, round_seed)

    masked_updates = [client_updates[i] + masks[i] for i in range(num_clients)]
    # The aggregator only ever sees `masked_updates` individually.
    # It computes the sum -- masks cancel exactly.
    aggregator_view_sum = np.sum(masked_updates, axis=0)

    # sanity: aggregator's per-client VIEW must differ substantially from the truth
    per_client_leak = np.linalg.norm(masked_updates[0] - client_updates[0])
    assert per_client_leak > 1.0, "masking not effective"

    return aggregator_view_sum, masked_updates
