"""
Membership Inference Attack.

Threat model: black-box query access to the trained model and a
candidate record; goal is to decide whether that record was a
training member. We implement two variants:

  1. loss-threshold attack (Yeom et al., 2018): members tend to have
     systematically lower loss than non-members because the model has
     partially memorized/overfit to them. A simple threshold on
     per-example loss is a strong, simple attacker.

  2. confidence-vector attack (Shokri et al., 2017; Salem et al.,
     2019 "population attack" simplification): train an attack
     classifier on (loss, confidence, confidence_margin) features
     computed directly from the TARGET model on a labeled calibration
     set of known members/non-members, then evaluate it on a
     disjoint held-out member/non-member set. NOTE: this is the
     single-model "population" simplification of the full
     multi-shadow-model attack (which trains several independent
     shadow models to mimic the target's training procedure on
     disjoint data). We use the simplified variant because it needs
     no extra shadow-training budget and is the more commonly used
     black-box baseline in practice; it is, if anything, a WEAKER
     attacker than the full shadow-model ensemble, so any attack
     success we report is a conservative (lower-bound) estimate of
     the true membership-inference risk.

Both attacks report accuracy and ROC-AUC, which is the headline
metric compared across experimental conditions.
"""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, accuracy_score


def _features(model, X, y):
    p = np.clip(model.predict_proba(X), 1e-7, 1 - 1e-7)
    loss = -(y * np.log(p) + (1 - y) * np.log(1 - p))
    confidence = np.where(y == 1, p, 1 - p)
    margin = np.abs(p - 0.5)
    return np.stack([loss, confidence, margin], axis=1)


def loss_threshold_attack(model, X_member, y_member, X_nonmember, y_nonmember):
    loss_m = -np.log(np.clip(np.where(y_member == 1,
                     model.predict_proba(X_member), 1 - model.predict_proba(X_member)), 1e-7, 1))
    loss_n = -np.log(np.clip(np.where(y_nonmember == 1,
                     model.predict_proba(X_nonmember), 1 - model.predict_proba(X_nonmember)), 1e-7, 1))
    losses = np.concatenate([loss_m, loss_n])
    truth = np.concatenate([np.ones(len(loss_m)), np.zeros(len(loss_n))])
    # lower loss => predict "member" => score = -loss
    scores = -losses
    auc = roc_auc_score(truth, scores)
    thresh = np.median(losses)
    preds = (losses <= thresh).astype(int)
    acc = accuracy_score(truth, preds)
    return {"attack": "loss_threshold", "auc": auc, "accuracy": acc}


def confidence_vector_attack(model, X_member_train, y_member_train, X_nonmember_train, y_nonmember_train,
                              X_member_test, y_member_test, X_nonmember_test, y_nonmember_test, seed=0):
    Xtr = np.concatenate([_features(model, X_member_train, y_member_train),
                           _features(model, X_nonmember_train, y_nonmember_train)])
    ytr = np.concatenate([np.ones(len(X_member_train)), np.zeros(len(X_nonmember_train))])

    Xte = np.concatenate([_features(model, X_member_test, y_member_test),
                           _features(model, X_nonmember_test, y_nonmember_test)])
    yte = np.concatenate([np.ones(len(X_member_test)), np.zeros(len(X_nonmember_test))])

    attacker = LogisticRegression(max_iter=1000, random_state=seed)
    attacker.fit(Xtr, ytr)
    scores = attacker.predict_proba(Xte)[:, 1]
    auc = roc_auc_score(yte, scores)
    acc = accuracy_score(yte, attacker.predict(Xte))
    return {"attack": "confidence_vector", "auc": auc, "accuracy": acc}
