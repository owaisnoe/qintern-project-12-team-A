#!/usr/bin/env python3
"""Shared metrics for the Week-2 classical intrusion-detection baselines.

The module keeps closed-set classification and open-set novelty evaluation separate:

* Closed-set metrics use only known-class ``test.csv`` rows.
* Zero-day metrics label known test rows as 0 and held-out ``zeroday.csv`` rows as 1.
* Novelty scores must be oriented so larger values mean "more novel".
* A novelty threshold is selected from known-only calibration scores, never zero-day data.
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    roc_auc_score,
    roc_curve,
)


def _finite_1d(values, *, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or array.size == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional array")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} contains NaN or infinite values")
    return array


def conformal_novelty_threshold(calibration_scores, alpha: float = 0.10) -> float:
    """Return the finite-sample split-conformal upper threshold.

    Scores at or below the threshold are accepted as known. Scores strictly above it
    are rejected as novel. The order-statistic correction uses
    ``ceil((n + 1) * (1 - alpha))`` and is capped at the largest calibration score.
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be strictly between 0 and 1")
    scores = np.sort(_finite_1d(calibration_scores, name="calibration_scores"))
    rank = int(np.ceil((scores.size + 1) * (1.0 - alpha)))
    return float(scores[min(rank, scores.size) - 1])


def multiclass_metrics(
    y_true,
    y_pred,
    probabilities,
    classes: Sequence[str],
) -> dict[str, float | int]:
    """Compute closed-set multiclass Accuracy, F1-macro, and macro OVR AUROC."""
    truth = np.asarray(y_true)
    prediction = np.asarray(y_pred)
    proba = np.asarray(probabilities, dtype=np.float64)
    class_array = np.asarray(list(classes))

    if truth.ndim != 1 or prediction.shape != truth.shape:
        raise ValueError("y_true and y_pred must be equally sized one-dimensional arrays")
    if proba.shape != (truth.size, class_array.size):
        raise ValueError("probabilities must have shape (n_samples, n_classes)")
    if not np.isfinite(proba).all():
        raise ValueError("probabilities contains NaN or infinite values")

    per_class_auc = []
    per_class_ap = []
    for index, class_name in enumerate(class_array):
        binary_truth = truth == class_name
        if binary_truth.any() and (~binary_truth).any():
            per_class_auc.append(roc_auc_score(binary_truth, proba[:, index]))
            per_class_ap.append(average_precision_score(binary_truth, proba[:, index]))
    if not per_class_auc:
        raise ValueError("AUROC requires at least one evaluable one-vs-rest class")

    return {
        "accuracy": float(accuracy_score(truth, prediction)),
        "balanced_accuracy": float(balanced_accuracy_score(truth, prediction)),
        "f1_macro": float(f1_score(truth, prediction, average="macro", zero_division=0)),
        "auroc_ovr_macro": float(np.mean(per_class_auc)),
        "auprc_ovr_macro": float(np.mean(per_class_ap)),
        "auroc_classes_evaluated": int(len(per_class_auc)),
    }


def binary_metrics(y_true, attack_scores, threshold: float = 0.5) -> dict[str, float]:
    """Compute binary attack-detection metrics from attack probabilities or scores."""
    truth = np.asarray(y_true, dtype=np.int64)
    scores = _finite_1d(attack_scores, name="attack_scores")
    if truth.shape != scores.shape:
        raise ValueError("y_true and attack_scores must have the same shape")
    if not set(np.unique(truth)).issubset({0, 1}) or np.unique(truth).size != 2:
        raise ValueError("binary AUROC requires both target values 0 and 1")
    prediction = (scores >= threshold).astype(np.int64)
    return {
        "accuracy": float(accuracy_score(truth, prediction)),
        "f1_macro": float(f1_score(truth, prediction, average="macro", zero_division=0)),
        "auroc": float(roc_auc_score(truth, scores)),
    }


def novelty_metrics(known_scores, zero_day_scores, threshold: float) -> dict[str, float | int]:
    """Evaluate a novelty head on known test rows versus held-out zero-day rows."""
    known = _finite_1d(known_scores, name="known_scores")
    zero_day = _finite_1d(zero_day_scores, name="zero_day_scores")
    scores = np.concatenate([known, zero_day])
    truth = np.concatenate([
        np.zeros(known.size, dtype=np.int64),
        np.ones(zero_day.size, dtype=np.int64),
    ])
    prediction = (scores > threshold).astype(np.int64)
    fpr, tpr, _ = roc_curve(truth, scores)
    at_95 = fpr[tpr >= 0.95]

    return {
        "accuracy": float(accuracy_score(truth, prediction)),
        "balanced_accuracy": float(balanced_accuracy_score(truth, prediction)),
        "f1_macro": float(f1_score(truth, prediction, average="macro", zero_division=0)),
        "zero_day_auroc": float(roc_auc_score(truth, scores)),
        "zero_day_auprc": float(average_precision_score(truth, scores)),
        "known_false_positive_rate": float(np.mean(known > threshold)),
        "zero_day_true_positive_rate": float(np.mean(zero_day > threshold)),
        "fpr_at_95_tpr": float(np.min(at_95)) if at_95.size else 1.0,
        "threshold": float(threshold),
        "known_score_mean": float(np.mean(known)),
        "zero_day_score_mean": float(np.mean(zero_day)),
        "known_test_rows": int(known.size),
        "zero_day_rows": int(zero_day.size),
    }


def per_attack_zero_day_metrics(
    known_scores,
    zero_day_scores,
    zero_day_families,
    threshold: float,
) -> dict[str, dict[str, float | int]]:
    """Per-held-out-attack zero-day scores.

    A single mean zero-day AUROC hides which held-out families are easy or hard, so this
    scores each held-out attack family separately: known test rows are the shared negatives
    (label 0) and one family's rows are the positives (label 1). Returns AUROC, AUPRC, the
    thresholded detection rate, and the support of every held-out family, keyed by family name.
    """
    known = _finite_1d(known_scores, name="known_scores")
    zero_day = _finite_1d(zero_day_scores, name="zero_day_scores")
    families = np.asarray(zero_day_families)
    if families.shape[0] != zero_day.shape[0]:
        raise ValueError("zero_day_families must align one-to-one with zero_day_scores")

    per_family: dict[str, dict[str, float | int]] = {}
    for family in sorted({str(value) for value in families.tolist()}):
        family_scores = zero_day[families.astype(str) == family]
        combined = np.concatenate([known, family_scores])
        truth = np.concatenate([
            np.zeros(known.size, dtype=np.int64),
            np.ones(family_scores.size, dtype=np.int64),
        ])
        per_family[family] = {
            "zero_day_auroc": float(roc_auc_score(truth, combined)),
            "zero_day_auprc": float(average_precision_score(truth, combined)),
            "detection_rate_at_threshold": float(np.mean(family_scores > threshold)),
            "zero_day_rows": int(family_scores.size),
        }
    return per_family
