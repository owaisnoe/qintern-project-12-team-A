#!/usr/bin/env python3
"""Day 6 — validate unified dataset package (schema contract + QADCP gates).

Run: python week1/scripts/validate_unified.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

from _paths import DATASETS, WEEK1
from _unified import load_schema

SEED = 42
DATASET_DIRS = ["CICIoT2023", "TON_IoT", "BoT-IoT", "Edge-IIoTset", "UNSW-NB15"]
SPLITS = ["train", "val", "calibration", "test", "zeroday"]
LABELS = ["label_multiclass", "label_binary", "label_family"]
ZERO_DAY = {
    "CICIoT2023": ["Mirai-"],
    "TON_IoT": ["ransomware"],
    "BoT-IoT": ["Theft"],
    "Edge-IIoTset": ["Ransomware", "Fingerprinting"],
    "UNSW-NB15": ["Worms", "Shellcode"],
}
GEN = WEEK1 / "reports" / "_generated"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def validate_dataset(name: str, schema: dict) -> dict:
    qdir = DATASETS / name / "unified" / "qadcp"
    report: dict = {"dataset": name, "gates": {}, "passed": True}

    if not (qdir / "train.parquet").exists():
        report["passed"] = False
        report["error"] = "missing unified/qadcp/train.parquet"
        return report

    frames = {s: pd.read_parquet(qdir / f"{s}.parquet") for s in SPLITS
              if (qdir / f"{s}.parquet").exists()}
    feat_cols = [c for c in frames["train"].columns if c not in LABELS]
    expected_order = [c for c in schema["feature_order"] if c not in LABELS]

    # schema contract: identical names + order across splits and vs schema
    schema_ok = feat_cols == expected_order
    for s, df in frames.items():
        if list(df.columns) != schema["feature_order"]:
            schema_ok = False
    report["gates"]["schema_contract"] = "pass" if schema_ok else "fail"
    report["feature_columns"] = feat_cols

    # no NaN in features
    nan_ok = all(int(df[feat_cols].isna().sum().sum()) == 0 for df in frames.values() if len(df))
    report["gates"]["no_nan"] = "pass" if nan_ok else "fail"

    # split disjointness (feature-hash overlap)
    hashes = {s: set(pd.util.hash_pandas_object(df[feat_cols], index=False))
              for s, df in frames.items() if len(df)}
    disjoint = True
    names = list(hashes)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if hashes[names[i]] & hashes[names[j]]:
                disjoint = False
    report["gates"]["split_disjoint"] = "pass" if disjoint else "fail"

    # zero-day isolation: holdout prefixes absent from train/val/cal/test
    zd_ok = True
    for pat in ZERO_DAY[name]:
        for s in ("train", "val", "calibration", "test"):
            if s in frames and len(frames[s]):
                if frames[s]["label_multiclass"].astype(str).str.startswith(pat).any():
                    zd_ok = False
    report["gates"]["zero_day_isolation"] = "pass" if zd_ok else "fail"

    # label sanity
    label_ok = True
    for s, df in frames.items():
        if not len(df):
            continue
        if (df["label_family"] == "other").any():
            label_ok = False
        if not set(df["label_binary"].unique()).issubset({0, 1}):
            label_ok = False
    report["gates"]["label_sanity"] = "pass" if label_ok else "fail"

    # encoder + scaler leakage
    enc_path = qdir / "encoders.json"
    enc_ok = enc_path.exists() and json.loads(enc_path.read_text()).get("fit_on") == "train split only"
    report["gates"]["encoder_leakage_safe"] = "pass" if enc_ok else "fail"

    scl_path = qdir / "scalers.json"
    scl_ok = scl_path.exists() and "train" in json.loads(scl_path.read_text()).get("fit_on", "")
    report["gates"]["scaler_leakage_safe"] = "pass" if scl_ok else "fail"

    # row conservation: split sum = unified checkpoint rows (± S7b cross-split dedup)
    report["split_rows"] = {s: len(df) for s, df in frames.items()}
    split_sum = sum(report["split_rows"].values())
    proc_meta = DATASETS / name / "unified" / "processed" / f"{name}_unified_meta.json"
    s7b_dropped = 0
    qadcp_report = qdir / "qadcp_report.json"
    if qadcp_report.exists():
        s7b = json.loads(qadcp_report.read_text()).get("s7b_postprune_dupes_dropped", {})
        s7b_dropped = sum(s7b.values()) if s7b else 0
    if proc_meta.exists():
        meta = json.loads(proc_meta.read_text())
        checkpoint_rows = meta.get("rows_after_dedup", 0)
        report["dedup_audit"] = {
            "rows_in": meta.get("rows_in"),
            "rows_after_projection_dedup": checkpoint_rows,
            "feature_dupes_removed": meta.get("feature_dupes_removed"),
            "s7b_cross_split_dropped": s7b_dropped,
            "split_row_sum": split_sum,
        }
        row_ok = split_sum == checkpoint_rows - s7b_dropped
        report["gates"]["row_conservation"] = "pass" if row_ok else "fail"
        if not row_ok:
            report["row_conservation_delta"] = split_sum - (checkpoint_rows - s7b_dropped)
    else:
        report["gates"]["row_conservation"] = "fail"

    for g in report["gates"].values():
        if g == "fail":
            report["passed"] = False

    (qdir / "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    status = "PASS" if report["passed"] else "FAIL"
    log(f"  {name}: {status} train={report['split_rows'].get('train', 0):,}")
    return report


def main() -> int:
    schema = load_schema()
    GEN.mkdir(parents=True, exist_ok=True)
    summary = {}
    all_pass = True
    ref_cols = schema["feature_order"]
    for name in DATASET_DIRS:
        log(f"validate {name}")
        r = validate_dataset(name, schema)
        summary[name] = r
        if not r.get("passed", False):
            all_pass = False
        cols = r.get("feature_columns", [])
        if cols and cols != ref_cols[: len(cols)]:
            log(f"  CROSS-DATASET SCHEMA MISMATCH: {name}")
            all_pass = False

    cross = {"identical_columns": True, "columns": ref_cols[:17], "seed": SEED}
    for name in DATASET_DIRS:
        if name in summary and summary[name].get("feature_columns") != ref_cols[:17]:
            cross["identical_columns"] = False
            all_pass = False
    summary["_cross_dataset"] = cross
    (GEN / "unified_validation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log(f"validate: {'ALL PASS' if all_pass else 'FAILURES'} -> {GEN / 'unified_validation_summary.json'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
