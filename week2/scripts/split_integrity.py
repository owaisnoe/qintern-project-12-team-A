#!/usr/bin/env python3
"""
Week 2 · Day 9 (Team A) — split-integrity & conformal-exchangeability verification.

Task (`qi26_12_Week 2.pdf`): *verify exchangeability prerequisites for conformal — calibration and test
drawn i.i.d. from the same known-class distribution; add stratified sampling + fixed seeds so splits are
reproducible.* Exchangeability can only be **falsified**, not proven (Barber, Candès, Ramdas & Tibshirani,
*Conformal Prediction Beyond Exchangeability*, 2023), so we run four independent checks per dataset:

  1. **Disjointness (hard asserts):** zeroday ∩ calibration = ∅ · train ∩ (cal ∪ test) = ∅ (feature-hash);
     zero-day family absent from every known split; calibration = KNOWN classes only.
  2. **Class-distribution match (cal vs test):** identical class set + TVD, χ², KS on class proportions.
  3. **Classifier two-sample test:** train a classifier to tell calibration from test on the features;
     5-fold CV AUROC ≈ 0.5 ⟺ indistinguishable ⟺ exchangeable (a direct falsification test).
  4. **Conformal coverage smoke test:** split-conformal on the known classes (nonconformity = 1 − p_true
     from an RF fit on train) → empirical marginal coverage on test ≈ 1 − α (α = 0.1). A large miss is the
     operational exchangeability alarm. Also reports mean zero-day nonconformity (should exceed test).

Report: week2/reports/w2_02_split_integrity.md · JSON: week2/reports/_generated/split_integrity.json
Run (venv, after make_partitions.py): python week2/scripts/split_integrity.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score

BASE = Path(__file__).resolve().parents[2]
PART = BASE / "week2" / "partitions"
GEN = BASE / "week2" / "reports" / "_generated"

SEED = 42
TRIO = ["CICIoT2023", "BoT-IoT", "UNSW-NB15"]
LABELS = ["label_multiclass", "label_binary", "label_family"]
ALPHA = 0.10
FIT_CAP = 40_000        # subsample cap for the RF fits (speed; deterministic, seed 42)
rng = np.random.default_rng(SEED)


def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def fhash(df, feats):
    return set(pd.util.hash_pandas_object(df[feats], index=False))


def subsample(df, n):
    return df.sample(n=n, random_state=SEED) if len(df) > n else df


def dist_distances(cal, test):
    """TVD / χ² / KS on the class-proportion vectors of calibration vs test."""
    classes = sorted(set(cal) | set(test))
    pc = cal.value_counts(normalize=True).reindex(classes, fill_value=0.0).to_numpy()
    pt = test.value_counts(normalize=True).reindex(classes, fill_value=0.0).to_numpy()
    tvd = float(0.5 * np.abs(pc - pt).sum())
    # χ² on counts (test counts vs expected from cal proportions)
    ct = test.value_counts().reindex(classes, fill_value=0).to_numpy().astype(float)
    exp = pc * ct.sum()
    keep = exp > 0
    chi2 = float(((ct[keep] - exp[keep]) ** 2 / exp[keep]).sum())
    dof = int(keep.sum() - 1)
    p = float(stats.chi2.sf(chi2, dof)) if dof > 0 else 1.0
    ks = float(np.max(np.abs(np.cumsum(pc) - np.cumsum(pt))))
    return {"class_set_identical": sorted(set(cal)) == sorted(set(test)),
            "tvd": round(tvd, 5), "chi2": round(chi2, 4), "chi2_dof": dof,
            "chi2_p": round(p, 4), "ks": round(ks, 5)}


def classifier_two_sample(cal, test, feats):
    """AUROC of a classifier trained to separate calibration (0) from test (1). ~0.5 = exchangeable."""
    a, b = subsample(cal, FIT_CAP // 2), subsample(test, FIT_CAP // 2)
    X = pd.concat([a[feats], b[feats]], ignore_index=True).to_numpy("float64")
    y = np.r_[np.zeros(len(a)), np.ones(len(b))]
    clf = RandomForestClassifier(n_estimators=200, max_depth=12, n_jobs=-1, random_state=SEED)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    proba = cross_val_predict(clf, X, y, cv=cv, method="predict_proba", n_jobs=-1)[:, 1]
    return round(float(roc_auc_score(y, proba)), 4)


def conformal_coverage(train, cal, test, zeroday, feats):
    """Split-conformal marginal coverage on known classes (nonconformity = 1 - p_true)."""
    tr = subsample(train, FIT_CAP)
    clf = RandomForestClassifier(n_estimators=250, max_depth=None, n_jobs=-1, random_state=SEED,
                                 class_weight="balanced_subsample")
    clf.fit(tr[feats].to_numpy("float64"), tr["label_multiclass"].to_numpy())
    cls = list(clf.classes_); idx = {c: i for i, c in enumerate(cls)}

    def nonconf(df):
        P = clf.predict_proba(df[feats].to_numpy("float64"))
        yi = df["label_multiclass"].map(idx).to_numpy()
        known = yi >= 0  # rows whose class the classifier knows (all cal/test known)
        s = np.full(len(df), np.nan)
        s[known] = 1.0 - P[np.arange(len(df))[known], yi[known].astype(int)]
        return s, P

    s_cal, _ = nonconf(cal)
    s_cal = s_cal[~np.isnan(s_cal)]
    n = len(s_cal)
    q_level = min(1.0, np.ceil((n + 1) * (1 - ALPHA)) / n)
    q = float(np.quantile(s_cal, q_level, method="higher"))
    s_test, _ = nonconf(test)
    s_test = s_test[~np.isnan(s_test)]
    coverage = float(np.mean(s_test <= q))                 # true class in the conformal set
    # zero-day: max prob over KNOWN classes → nonconformity 1 - max_p (should be high = rejected)
    zd_nc = float(np.mean(1.0 - clf.predict_proba(zeroday[feats].to_numpy("float64")).max(1))) if len(zeroday) else None
    return {"alpha": ALPHA, "target_coverage": round(1 - ALPHA, 3), "empirical_coverage": round(coverage, 4),
            "q_threshold": round(q, 4), "cal_n": n,
            "mean_test_nonconformity": round(float(np.mean(s_test)), 4),
            "mean_zeroday_nonconformity": round(zd_nc, 4) if zd_nc is not None else None}


def run(name):
    p = PART / name
    S = {s: pd.read_csv(p / f"{s}.csv") for s in ["train", "calibration", "test", "zeroday"]}
    feats = [c for c in S["train"].columns if c not in LABELS]
    known = set(S["train"]["label_multiclass"].unique())
    zd = set(S["zeroday"]["label_multiclass"].unique())

    # 1) disjointness (hard asserts)
    htr = fhash(S["train"], feats)
    assert htr.isdisjoint(fhash(S["calibration"], feats)), f"{name}: train∩cal overlap"
    assert htr.isdisjoint(fhash(S["test"], feats)), f"{name}: train∩test overlap"
    assert fhash(S["zeroday"], feats).isdisjoint(fhash(S["calibration"], feats)), f"{name}: zeroday∩cal overlap"
    assert zd.isdisjoint(known), f"{name}: zero-day family in known classes"
    cal_known_only = set(S["calibration"]["label_multiclass"].unique()).issubset(known)
    assert cal_known_only, f"{name}: calibration has non-known classes"

    # 2) class-distribution match
    dd = dist_distances(S["calibration"]["label_multiclass"], S["test"]["label_multiclass"])
    # 3) classifier two-sample
    c2st = classifier_two_sample(S["calibration"], S["test"], feats)
    # 4) conformal coverage
    cov = conformal_coverage(S["train"], S["calibration"], S["test"], S["zeroday"], feats)
    # rare classes in cal/test (<10) — flag for Mondrian/class-conditional
    rare = sorted({c for c, n in S["calibration"]["label_multiclass"].value_counts().items() if n < 10}
                  | {c for c, n in S["test"]["label_multiclass"].value_counts().items() if n < 10})

    verdict = (dd["class_set_identical"] and dd["tvd"] < 0.05 and abs(c2st - 0.5) < 0.05
               and abs(cov["empirical_coverage"] - (1 - ALPHA)) < 0.03)
    res = {"dataset": name, "disjoint_asserts": "pass", "calibration_known_only": cal_known_only,
           "n_known_classes": len(known), "zero_day_families": sorted(zd),
           "cal_vs_test": dd, "classifier_two_sample_auroc": c2st, "conformal": cov,
           "rare_known_classes_lt10": rare, "exchangeable_verdict": bool(verdict)}
    log(f"  {name}: TVD={dd['tvd']} chi2_p={dd['chi2_p']} 2sampleAUC={c2st} "
        f"coverage={cov['empirical_coverage']} (target={1-ALPHA}) "
        f"zd_nc={cov['mean_zeroday_nonconformity']} "
        f"exchangeable={verdict}" + (f" | rare<10: {rare}" if rare else ""))
    return res


def main():
    GEN.mkdir(parents=True, exist_ok=True)
    log(f"Week-2 Day-9 split-integrity & exchangeability (alpha={ALPHA}, seed {SEED})")
    out = {name: run(name) for name in TRIO}
    (GEN / "split_integrity.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    ok = all(r["exchangeable_verdict"] for r in out.values())
    log(f"done -> split_integrity.json | all exchangeable: {ok}")


if __name__ == "__main__":
    main()
