#!/usr/bin/env python3
"""
Week 2 · Day 14 (Team A) — prototype-shaped DUMMY score interface for the frozen partitions.

DATA FREEZE deliverable: publish a *stable score interface* so Teams B and C can build against it
**before** Team B's real MAQT prototypes / CQ-ZDR scores exist. The files here are SYNTHETIC
placeholders with the exact schema, dtypes, ranges and row-alignment the real scores will have.

The QS-Net scoring stage (what Team B will emit):
  * MAQT (Alg 1) learns a per-known-class prototype density matrix rho_c on `train`.
  * For a sample x with encoded state rho_x, fidelity to each prototype is  F(rho_x, rho_c) in [0, 1].
  * CQ-ZDR (Alg 2) nonconformity score is  s(x) = 1 - max_c F(rho_x, rho_c)  (higher => more novel).
  * The conformal threshold q is the split-conformal quantile of s on `calibration` at level alpha,
    then `test`/`zeroday` points with s > q are flagged zero-day (Alg 3).

So the interface = one row per partition row, carrying the full prototype-fidelity vector
`fid__<class>` plus the derived conformal columns. Team B swaps synthetic fidelities for real ones
by matching this schema; Team A's Week-3 CQ-ZDR code and Team C's consumers build now.

Dummy values are deterministic (seed 42) and *shape-plausible*, NOT results: the per-dataset zero-day
`nonconformity` mean is seeded to the Day-9 diagnostic (CIC 0.771, BoT 0.134, UNSW 0.352 — see
w2_02_split_integrity.md) so the placeholder is internally consistent with existing artifacts. They are
superseded the moment Team B publishes real prototypes.

Outputs (under week2/interface/):
  dummy_scores/<name>/{calibration,test,zeroday}_scores.parquet   aligned to partitions/<name>/<split>.csv
  dummy_scores/<name>/{calibration,test,zeroday}_scores.head.csv  10-row human preview
  dummy_scores/<name>/prototypes_meta.json                        prototype registry (self-describes fid__*)
  dummy_scores_schema.json                                        the machine-readable interface contract
  ../reports/_generated/dummy_score_selfcheck.json               end-to-end conformal self-check

Run (venv):  python week2/scripts/make_dummy_scores.py
Verify only: python week2/scripts/make_dummy_scores.py --check
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PART = BASE / "week2" / "partitions"
IFACE = BASE / "week2" / "interface"
GEN = BASE / "week2" / "reports" / "_generated"

SEED = 42
TRIO = ["CICIoT2023", "BoT-IoT", "UNSW-NB15"]
SPLITS = ["calibration", "test", "zeroday"]
ALPHA = 0.10  # CQ-ZDR target miscoverage — matches Day-9 split_integrity

# Per-dataset synthetic knobs. zeroday_nonconf = Day-9 diagnostic mean nonconformity (w2_02).
# known_nonconf keeps calibration/test max-fidelity high so conformal coverage ~ 1-alpha is sensible.
# pred_acc controls how often the argmax prototype is the true class on known rows (shape only).
KNOBS = {
    "CICIoT2023": {"zeroday_nonconf": 0.771, "known_nonconf": 0.12, "pred_acc": 0.90},
    "BoT-IoT":    {"zeroday_nonconf": 0.134, "known_nonconf": 0.10, "pred_acc": 0.94},
    "UNSW-NB15":  {"zeroday_nonconf": 0.352, "known_nonconf": 0.18, "pred_acc": 0.80},
}
SCHEMA_VERSION = "1.0"

# Column contract (order matters for the head previews / consumers)
BASE_COLS = [
    "sample_id", "dataset", "split", "true_label_multiclass", "true_label_family", "y_known",
    "pred_class", "pred_correct", "max_fidelity", "runner_up_fidelity", "margin",
    "fid_true_class", "nonconformity", "nonconformity_true", "trace_distance_nearest",
]


def _beta_meank(rng: np.random.Generator, mean: float, k: float, n: int) -> np.ndarray:
    """Beta samples with target `mean` and concentration `k` (a=mean*k, b=(1-mean)*k), clipped to (0,1)."""
    mean = float(min(max(mean, 1e-3), 1 - 1e-3))
    a, b = mean * k, (1.0 - mean) * k
    return np.clip(rng.beta(a, b, size=n), 1e-4, 1 - 1e-4)


def _dataset_rng(dataset: str, split: str) -> np.random.Generator:
    """Deterministic per-(dataset, split) stream so files are independent yet reproducible."""
    off = TRIO.index(dataset) * 100 + SPLITS.index(split)
    return np.random.default_rng(SEED + off)


def build_split(dataset: str, split: str, known: list[str]) -> pd.DataFrame:
    """Prototype-shaped dummy scores for one partition split, aligned by row to <split>.csv."""
    part = pd.read_csv(PART / dataset / f"{split}.csv", usecols=["label_multiclass", "label_family"])
    n = len(part)
    rng = _dataset_rng(dataset, split)
    k = KNOBS[dataset]
    n_cls = len(known)
    cls_index = {c: j for j, c in enumerate(known)}
    is_zeroday = split == "zeroday"

    # 1) target max-fidelity distribution (1 - nonconformity mean), concentration 12
    target_nonconf = k["zeroday_nonconf"] if is_zeroday else k["known_nonconf"]
    max_fid = _beta_meank(rng, 1.0 - target_nonconf, 12.0, n)

    # 2) full prototype-fidelity matrix: all classes below max_fid, then the argmax class set to max_fid
    fid = max_fid[:, None] * _beta_meank(rng, 0.45, 6.0, n * n_cls).reshape(n, n_cls)

    true_mc = part["label_multiclass"].to_numpy()
    if is_zeroday:
        # novel rows: argmax is whichever prototype it most resembles (a known class), true class is unknown
        arg = rng.integers(0, n_cls, size=n)
    else:
        # known rows: argmax == true class with prob pred_acc, else a random other prototype (a "miss")
        true_idx = np.array([cls_index[c] for c in true_mc])
        hit = rng.random(n) < k["pred_acc"]
        arg = true_idx.copy()
        if (~hit).any():
            rand = rng.integers(0, n_cls, size=n)
            # ensure the miss lands on a different class
            same = rand == true_idx
            rand[same] = (rand[same] + 1) % n_cls
            arg[~hit] = rand[~hit]

    rows = np.arange(n)
    fid[rows, arg] = max_fid  # the winning prototype carries exactly max_fidelity

    order = np.argsort(-fid, axis=1)
    runner_up = fid[rows, order[:, 1]] if n_cls > 1 else np.zeros(n)
    pred_class = np.array(known)[arg]

    if is_zeroday:
        fid_true = np.full(n, np.nan)
        y_known = np.zeros(n, dtype=np.int8)
        pred_correct = np.zeros(n, dtype=np.int8)
    else:
        fid_true = fid[rows, np.array([cls_index[c] for c in true_mc])]
        y_known = np.ones(n, dtype=np.int8)
        pred_correct = (pred_class == true_mc).astype(np.int8)

    nonconf = 1.0 - max_fid
    # trace distance to nearest prototype: correlated with novelty, in [0,1]
    trace_d = np.clip(nonconf * rng.uniform(0.6, 1.0, size=n), 0.0, 1.0)

    out = pd.DataFrame({
        "sample_id": rows.astype(np.int64),
        "dataset": dataset,
        "split": split,
        "true_label_multiclass": true_mc,
        "true_label_family": part["label_family"].to_numpy(),
        "y_known": y_known,
        "pred_class": pred_class,
        "pred_correct": pred_correct,
        "max_fidelity": max_fid,
        "runner_up_fidelity": runner_up,
        "margin": max_fid - runner_up,
        "fid_true_class": fid_true,
        "nonconformity": nonconf,
        "nonconformity_true": np.where(y_known == 1, 1.0 - fid_true, np.nan),
        "trace_distance_nearest": trace_d,
    })
    for j, c in enumerate(known):
        out[f"fid__{c}"] = fid[:, j]
    return out


def conformal_selfcheck(dataset: str, frames: dict[str, pd.DataFrame]) -> dict:
    """Fit the split-conformal threshold on dummy calibration, then score test/zeroday — proves usability."""
    cal = frames["calibration"]["nonconformity"].to_numpy()
    n = len(cal)
    # split-conformal quantile: q = the ceil((n+1)(1-alpha))/n empirical quantile of calibration scores
    q_level = min(1.0, np.ceil((n + 1) * (1 - ALPHA)) / n)
    q = float(np.quantile(cal, q_level, method="higher"))
    test_nc = frames["test"]["nonconformity"].to_numpy()
    zd_nc = frames["zeroday"]["nonconformity"].to_numpy()
    return {
        "alpha": ALPHA,
        "calibration_n": int(n),
        "threshold_q": q,
        "known_test_flag_rate": float((test_nc > q).mean()),   # target ~ alpha (false zero-day rate)
        "known_test_coverage": float((test_nc <= q).mean()),   # target ~ 1 - alpha
        "zeroday_rejection_rate": float((zd_nc > q).mean()),   # TPR at this threshold (dummy separation)
        "known_test_accuracy": float(frames["test"]["pred_correct"].mean()),
    }


def build(check: bool) -> dict:
    IFACE_SCORES = IFACE / "dummy_scores"
    schema_cols = list(BASE_COLS)  # fid__* appended per dataset (variable width)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "seed": SEED,
        "status": "DUMMY — synthetic placeholder, superseded by Team B real MAQT/CQ-ZDR scores",
        "alpha": ALPHA,
        "row_alignment": "sample_id == 0-based row index into week2/partitions/<dataset>/<split>.csv",
        "nonconformity": "1 - max_fidelity  (= 1 - max_c F(rho_x, rho_c)); higher => more novel",
        "base_columns": schema_cols,
        "prototype_columns": "fid__<known_class> in [0,1] — Uhlmann fidelity to prototype rho_class",
        "column_dtypes": {
            "sample_id": "int64", "y_known": "int8", "pred_correct": "int8",
            "max_fidelity": "float64", "nonconformity": "float64", "fid__<class>": "float64",
        },
        "datasets": {},
    }
    selfcheck = {"alpha": ALPHA, "seed": SEED, "datasets": {}}

    for dataset in TRIO:
        meta = json.loads((PART / dataset / "partition_meta.json").read_text())
        known = list(meta["known_classes"])
        frames = {sp: build_split(dataset, sp, known) for sp in SPLITS}
        outdir = IFACE_SCORES / dataset

        if not check:
            outdir.mkdir(parents=True, exist_ok=True)
            for sp, df in frames.items():
                df.to_parquet(outdir / f"{sp}_scores.parquet", index=False)
                df.head(10).to_csv(outdir / f"{sp}_scores.head.csv", index=False)
            proto = {
                "dataset": dataset,
                "seed": SEED,
                "status": "DUMMY prototype registry — real rho_c come from Team B MAQT (Alg 1) Day-14 checkpoint",
                "n_qubits": 8,
                "hilbert_dim": 256,
                "encoding": "angle-encoded top-8 ranked features in [0, pi] (quantum/q8_*)",
                "prototype_representation": "per-class mean density matrix rho_c (Hermitian, PSD, trace 1)",
                "fidelity": "Uhlmann F(rho_x, rho_c) in [0,1] -> column fid__<class>",
                "nonconformity": "1 - max_c F(rho_x, rho_c)",
                "n_known_classes": len(known),
                "known_classes": known,
                "zero_day_families": meta["zero_day_families"],
                "fidelity_columns": [f"fid__{c}" for c in known],
            }
            (outdir / "prototypes_meta.json").write_text(json.dumps(proto, indent=1))

        sc = conformal_selfcheck(dataset, frames)
        selfcheck["datasets"][dataset] = sc
        manifest["datasets"][dataset] = {
            "n_known_classes": len(known),
            "rows": {sp: int(len(frames[sp])) for sp in SPLITS},
            "n_columns": len(BASE_COLS) + len(known),
            "fidelity_columns": len(known),
        }
        print(f"[{dataset:12s}] cal/test/zeroday rows="
              f"{[len(frames[sp]) for sp in SPLITS]}  q={sc['threshold_q']:.3f}  "
              f"test_flag={sc['known_test_flag_rate']:.3f}  zd_reject={sc['zeroday_rejection_rate']:.3f}")

    if not check:
        IFACE.mkdir(parents=True, exist_ok=True)
        (IFACE / "dummy_scores_schema.json").write_text(json.dumps(manifest, indent=1))
        GEN.mkdir(parents=True, exist_ok=True)
        (GEN / "dummy_score_selfcheck.json").write_text(json.dumps(selfcheck, indent=1))
        print(f"\nWrote interface -> {IFACE.relative_to(BASE)}/  (schema + dummy_scores/<name>/)")
        print(f"Wrote self-check -> {(GEN / 'dummy_score_selfcheck.json').relative_to(BASE)}")
    return selfcheck


def main() -> None:
    ap = argparse.ArgumentParser(description="Day-14 prototype-shaped dummy score interface")
    ap.add_argument("--check", action="store_true", help="build in memory + self-check, write nothing")
    build(check=ap.parse_args().check)


if __name__ == "__main__":
    main()
