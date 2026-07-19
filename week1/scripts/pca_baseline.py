#!/usr/bin/env python3
"""PCA-8 baseline on QADCP splits (v0.1 or --unified Day 6).

Run:
  python week1/scripts/pca_baseline.py
  python week1/scripts/pca_baseline.py --unified
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from _paths import DATASETS, PROJ

SEED = 42
N_COMPONENTS = 8
LABELS = ["label_multiclass", "label_binary", "label_family"]
SPLITS = ["train", "val", "calibration", "test", "zeroday"]
DATASET_DIRS = ["CICIoT2023", "TON_IoT", "BoT-IoT", "Edge-IIoTset", "UNSW-NB15"]


def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def qadcp_dir(name: str, unified: bool) -> Path:
    if unified:
        return DATASETS / name / "unified" / "qadcp"
    return DATASETS / name / "qadcp"


def run(name: str, unified: bool = False):
    qdir = qadcp_dir(name, unified)
    if not (qdir / "train.parquet").exists():
        log(f"  {name}: no train.parquet — skip")
        return None
    splits = {s: pd.read_parquet(qdir / f"{s}.parquet")
              for s in SPLITS if (qdir / f"{s}.parquet").exists()}
    train = splits["train"]
    feats = [c for c in train.columns if c not in LABELS]
    ncomp = min(N_COMPONENTS, len(feats))

    Xtr = train[feats].to_numpy("float64")
    pca = PCA(n_components=ncomp, random_state=SEED).fit(Xtr)
    Ptr = pca.transform(Xtr)
    lo, hi = Ptr.min(0), Ptr.max(0)
    rng = np.where(hi > lo, hi - lo, 1.0)

    (qdir / "quantum").mkdir(parents=True, exist_ok=True)
    rows = {}
    for s, df in splits.items():
        P = pca.transform(df[feats].to_numpy("float64")) if len(df) else np.zeros((0, ncomp))
        ang = np.clip((P - lo) / rng, 0.0, 1.0) * np.pi
        out = pd.DataFrame({f"pca_{i+1}": ang[:, i] for i in range(ncomp)})
        for lbl in LABELS:
            if lbl in df.columns:
                out[lbl] = df[lbl].to_numpy()
        out.to_parquet(qdir / "quantum" / f"pca8_{s}.parquet", index=False)
        rows[s] = int(len(out))

    meta = {
        "author": "AK (@Thedaemon-AK)", "seed": SEED, "n_components": ncomp,
        "mode": "unified" if unified else "v0.1",
        "fit_on": "train.parquet only (leakage-safe)",
        "explained_variance_train": round(float(pca.explained_variance_ratio_.sum()), 4),
        "outputs": [f"quantum/pca8_{s}.parquet" for s in splits], "rows": rows,
    }
    (qdir / "pca_baseline.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    log(f"  {name}: PCA{ncomp} evr={meta['explained_variance_train']:.3f}")
    return {"dataset": name, **meta}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unified", action="store_true")
    args = parser.parse_args()
    res = [r for r in (run(n, args.unified) for n in DATASET_DIRS) if r]
    fname = "_unified_pca_baseline_summary.json" if args.unified else "_pca_baseline_summary.json"
    (DATASETS / fname).write_text(json.dumps({r["dataset"]: r for r in res}, indent=1), encoding="utf-8")
    log(f"done -> quantum/pca8_* ({len(res)} datasets)")


if __name__ == "__main__":
    main()
