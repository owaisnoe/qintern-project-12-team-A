"""Week 5 · Day 26 — tests for the disentanglement (RQ3) separation AUROC."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week5" / "scripts"))
sys.path.insert(0, str(BASE / "week3" / "scripts"))

import disentanglement as di                       # noqa: E402

IFACE = BASE / "week2" / "interface" / "dummy_scores"
IFACE_OK = (IFACE / "CICIoT2023" / "zeroday_scores.parquet").exists()
needs_iface = pytest.mark.skipif(not IFACE_OK, reason="Day-14 dummy interface not present")


def test_auroc_perfect_and_inverted():
    assert di.auroc([1.0, 1.0, 0.9], [0.0, 0.1, 0.2]) == 1.0     # positives strictly above
    assert di.auroc([0.0, 0.1], [1.0, 1.0]) == 0.0               # positives strictly below


def test_auroc_identical_populations_is_half():
    x = [0.2, 0.4, 0.6, 0.8]
    assert di.auroc(x, x) == 0.5                                 # ties counted at ½


def test_auroc_empty_is_none():
    assert di.auroc([], [1.0]) is None
    assert di.auroc([1.0], []) is None


def test_bootstrap_ci_brackets_and_is_seed_deterministic():
    rng = np.random.default_rng(0)
    pos = rng.normal(1.0, 1.0, 400)
    neg = rng.normal(0.0, 1.0, 400)
    point = di.auroc(pos, neg)
    lo1, hi1 = di.auroc_bootstrap_ci(pos, neg, n_boot=300, seed=42)
    lo2, hi2 = di.auroc_bootstrap_ci(pos, neg, n_boot=300, seed=42)
    assert (lo1, hi1) == (lo2, hi2)                              # seed 42 -> reproducible band
    assert lo1 <= point <= hi1


@needs_iface
def test_dummy_adv_and_zeroday_are_disjoint_halves():
    scores = di._role_scores_dummy("CICIoT2023", IFACE, seed=42)
    assert set(scores) == set(di.ROLES)
    # true_zeroday and adv_known are two seeded halves of the zero-day pool (no reuse)
    assert scores["true_zeroday"].size == scores["adv_known"].size


@needs_iface
def test_separation_auroc_is_near_half_on_dummy():
    r = di.disentangle_dataset("CICIoT2023", IFACE, "dummy", n_boot=500)
    panels = {p["panel"]: p for p in r["panels"]}
    assert set(panels) == {"separation", "zeroday_vs_clean", "adv_vs_clean"}
    sep = panels["separation"]
    # honest null: adv_known is an independent draw from the zero-day distribution -> AUROC ~ 0.5
    assert sep["ci95_low"] <= 0.5 <= sep["ci95_high"]
    assert abs(sep["auroc"] - 0.5) < 0.05
    # ...yet novelty is detectable against clean traffic (both halves sit far from the prototypes)
    assert panels["zeroday_vs_clean"]["auroc"] > 0.5
    assert panels["adv_vs_clean"]["auroc"] > 0.5


@needs_iface
def test_positive_class_is_true_zeroday_for_separation():
    # separation must be P(s(true_zeroday) > s(adv_known)); positive/negative wired correctly
    sep = next(p for p in di.PANELS if p[0] == "separation")
    assert sep[1] == "true_zeroday" and sep[2] == "adv_known"
