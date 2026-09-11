"""
Model poisoning attack simulation.

Threat model: one of the participating entities is compromised (or
run by a malicious insider) and, instead of sending its honest
(clipped, noised) DP-SGD update, sends an update SCALED by a large
factor in an adversarial direction. Under plain FedAvg (arithmetic
mean across a small cross-silo cohort), this single client can drag
the global model far off the honest optimum -- a realistic and
well-documented attack against small-cohort cross-silo FL (unlike
cross-device FL with thousands of clients, a 3-5 entity government
consortium has NO safety in numbers: one bad actor is 20-33% of the
vote).

We simulate two attack strengths:
  - `scale_attack`: the malicious client sends its honest update
    multiplied by a large constant (a "loud", easy-to-reason-about
    attack -- amplifies whatever direction its own data points in).
  - `sign_flip_attack`: the malicious client sends the NEGATIVE of its
    honest update, scaled up -- actively pushes the global model
    away from the honest gradient direction, not just further along
    a random one.

We then compare global-model utility (ROC-AUC) with plain FedAvg vs.
coordinate-wise trimmed-mean / median aggregation, over the SAME
malicious client, to show the robust aggregators actually neutralize
the attack. This is run as its own experiment
(experiments/run_poisoning_experiment.py) alongside, not instead of,
the main privacy/utility/attack sweep.
"""
import numpy as np


def craft_malicious_update(honest_update, mode="scale", scale=25.0):
    if mode == "scale":
        return honest_update * scale
    elif mode == "sign_flip":
        return -honest_update * scale
    raise ValueError(f"unknown poisoning mode: {mode}")
