#!/usr/bin/env python3
"""
Week 2 · Day 10 (Team A) — RQ3 adversarial-vs-zero-day evaluation set.

Task (`qi26_12_Week 2.pdf`): *construct the adversarial-vs-zero-day evaluation set for RQ3 — known-attack
samples to be perturbed later (FGSM/PGD by Team B) plus the genuine held-out zero-day class; define a
labelling schema that keeps 'adversarial-known' and 'true-zero-day' distinguishable in evaluation.*

RQ3 is hard because an adversarial example is **semantically in-distribution** (a perturbed KNOWN attack)
yet sits in **OOD regions** of the representation — so a single novelty score flags *both* and cannot, by
itself, separate them (Karunanayake et al., *OOD Data: An Acquaintance of Adversarial Examples*, ACM CSUR
2024). The fix is a **two-axis factorial** eval set — never a flat label:
  * **Axis A — origin ∈ {known, novel}**  (novel = the held-out zero-day class; never in train/calibration)
  * **Axis B — perturb ∈ {clean, adversarial}**  (Team B fills `adversarial` after FGSM/PGD)
Cells: **clean-known · adversarial-known · clean-novel**.  We ship the two *clean* cells + a clean
**adversarial-source pool** (known attacks earmarked for perturbation). **Adversarial seeds are drawn only
from KNOWN attacks — never from the zero-day class** — so the two axes stay independent.

FGSM/PGD are applied in the **classical 17-feature space *before* angle encoding** (the real attack
surface; quantum-state perturbations barely move VQC accuracy — West et al. 2022). Features are already
robust-scaled (Week-1 `scalers.json`), so Team B's ε-budget is in **scaled-feature units** (recorded in the
schema).

Outputs (per trio dataset, under week2/rq3/<name>/):
  adversarial_source_pool.csv   clean KNOWN-attack rows to perturb (origin=known, perturb→adversarial)
  eval_clean.csv                clean-known + clean-novel cells (the shipped clean eval set)
  rq3_schema.json               column contract + factorial cells + metric definitions
Run (venv, after make_partitions.py): python week2/scripts/make_rq3_evalset.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PART = BASE / "week2" / "partitions"
OUT = BASE / "week2" / "rq3"
GEN = BASE / "week2" / "reports" / "_generated"

SEED = 42
TRIO = ["CICIoT2023", "BoT-IoT", "UNSW-NB15"]
LABELS = ["label_multiclass", "label_binary", "label_family"]
ADV_PER_CLASS = 200        # known-attack rows per class earmarked for FGSM/PGD
CLEAN_PER_CLASS = 200      # clean-known reference rows per known class (incl. benign)
ZD_CAP = 3000              # clean-novel cap (balanced across zero-day families)
SCHEMA_COLS = ["sample_id", "dataset", "attack_class", "origin", "perturb", "role",
               "should_flag_novel", "should_flag_adversarial"]


def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def balanced_sample(df, by, cap):
    groups = []
    for _, group in df.groupby(by, sort=True, observed=True):
        groups.append(group.sample(n=min(len(group), cap), random_state=SEED))
    return pd.concat(groups, ignore_index=True)


def tag(df, ds, feats, *, origin, perturb, role):
    out = df.reset_index(drop=True).copy()
    out.insert(0, "sample_id", [f"{ds[:3]}_{role}_{i}" for i in range(len(out))])
    out["dataset"] = ds
    out["attack_class"] = out["label_multiclass"]
    out["origin"] = origin                       # known | novel
    out["perturb"] = perturb                     # clean | adversarial (Team B sets adversarial)
    out["role"] = role                           # clean_known | adv_source | true_zeroday
    out["should_flag_novel"] = origin == "novel"
    out["should_flag_adversarial"] = perturb == "adversarial"
    return out[SCHEMA_COLS + feats + ["label_binary", "label_family"]]


def run(name):
    p = PART / name
    test = pd.read_csv(p / "test.csv")
    zeroday = pd.read_csv(p / "zeroday.csv")
    feats = [c for c in test.columns if c not in LABELS]
    outdir = OUT / name
    outdir.mkdir(parents=True, exist_ok=True)

    attacks = test[test["label_binary"] == 1]           # known attacks (exclude benign)
    benign = test[test["label_binary"] == 0]

    # adversarial-source pool: known attacks only, balanced (NEVER from zero-day)
    adv_pool = tag(balanced_sample(attacks, "label_multiclass", ADV_PER_CLASS), name, feats,
                   origin="known", perturb="clean", role="adv_source")
    adv_pool.to_csv(outdir / "adversarial_source_pool.csv", index=False)

    # clean-known reference (benign + known attacks, balanced)
    clean_known = tag(balanced_sample(test, "label_multiclass", CLEAN_PER_CLASS), name, feats,
                      origin="known", perturb="clean", role="clean_known")
    # clean-novel = the held-out zero-day class (balanced across its families)
    zd = balanced_sample(zeroday, "label_multiclass", max(1, ZD_CAP // max(1, zeroday["label_multiclass"].nunique())))
    clean_novel = tag(zd, name, feats, origin="novel", perturb="clean", role="true_zeroday")
    eval_clean = pd.concat([clean_known, clean_novel], ignore_index=True)
    eval_clean.to_csv(outdir / "eval_clean.csv", index=False)

    schema = {
        "dataset": name, "seed": SEED,
        "axes": {"A_origin": ["known", "novel"], "B_perturb": ["clean", "adversarial"]},
        "cells_shipped": {"clean_known": int((clean_known["role"] == "clean_known").sum()),
                          "true_zeroday": int(len(clean_novel)),
                          "adv_source_pool_to_perturb": int(len(adv_pool))},
        "adversarial_generation": {
            "who": "Team B", "attacks": ["FGSM", "PGD"],
            "space": "classical 17-feature space BEFORE angle encoding",
            "eps_units": "robust-scaled feature units (Week-1 unified scalers.json; angle-encode after)",
            "rule": "seed ONLY from adv_source_pool (known attacks); NEVER from the zero-day class",
            "adds_cell": {"origin": "known", "perturb": "adversarial", "role": "adv_known"}},
        "columns": SCHEMA_COLS + feats + ["label_binary", "label_family"],
        "ground_truth": {"should_flag_novel": "TRUE iff origin==novel",
                         "should_flag_adversarial": "TRUE iff perturb==adversarial"},
        "metrics": {
            "novelty_auroc": "clean_known vs clean_novel (perturbation excluded so it can't contaminate)",
            "adversarial_auroc": "clean_known vs adv_known (after Team B perturbs the pool)",
            "rq3_confusion": "3x3 over {clean_known, adv_known, true_zeroday} — off-diagonal adv_known↔true_zeroday IS the RQ3 result",
            "report_alongside": "closed-set known-class accuracy"},
        "zero_day_families": sorted(zeroday["label_multiclass"].unique().tolist()) if len(zeroday) else [],
    }
    (outdir / "rq3_schema.json").write_text(json.dumps(schema, indent=1), encoding="utf-8")
    # invariant: no zero-day class in the adversarial pool
    assert set(adv_pool["attack_class"]).isdisjoint(set(schema["zero_day_families"])), f"{name}: zero-day leaked into adv pool"
    log(f"  {name}: adv_source={len(adv_pool):,} clean_known={len(clean_known):,} "
        f"true_zeroday={len(clean_novel):,} | pool classes={adv_pool['attack_class'].nunique()}")
    return schema


def main():
    GEN.mkdir(parents=True, exist_ok=True)
    log("Week-2 Day-10 RQ3 adversarial-vs-zero-day evaluation set (factorial origin × perturb)")
    out = {name: run(name) for name in TRIO}
    (GEN / "rq3_summary.json").write_text(json.dumps(
        {n: s["cells_shipped"] for n, s in out.items()}, indent=1), encoding="utf-8")
    log("done -> week2/rq3/<name>/{adversarial_source_pool,eval_clean}.csv + rq3_schema.json")


if __name__ == "__main__":
    main()
