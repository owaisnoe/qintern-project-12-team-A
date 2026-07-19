#!/usr/bin/env python3
"""Day 7 — final Week 1 pipeline validation (Days 3–6 acceptance gates).

Checks clean checkpoints, v0.1 QADCP, v1.0 unified package, quantum sanity,
and manifest reproducibility. Delegates unified schema gates to validate_unified.

Run: python week1/scripts/validate_pipeline.py
     python week1/scripts/validate_pipeline.py --skip-manifest
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from _paths import DATASETS, PROJ, WEEK1
from validate_unified import DATASET_DIRS, LABELS, SPLITS, ZERO_DAY, validate_dataset
from _unified import load_schema

SEED = 42
GEN = WEEK1 / "reports" / "_generated"
V01_SPLITS = SPLITS + ["train_balanced"]
V01_JSONS = [
    "scalers.json", "qubit_budgets.json", "feature_groups.json", "qadcp_report.json",
    "zero_day_tiers.json", "pca_baseline.json",
]
QUANTUM_SPLITS = ["train", "val", "calibration", "test", "zeroday"]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _zd_isolated(frames: dict[str, pd.DataFrame], name: str) -> bool:
    for pat in ZERO_DAY[name]:
        for s in ("train", "val", "calibration", "test"):
            if s in frames and len(frames[s]):
                if frames[s]["label_multiclass"].astype(str).str.startswith(pat).any():
                    return False
    return True


def _check_q8_angles(qdir: Path) -> bool:
    q8 = qdir / "quantum" / "q8_train.parquet"
    if not q8.exists():
        return False
    q8df = pd.read_parquet(q8)
    qfeats = [c for c in q8df.columns if c not in LABELS]
    if not qfeats:
        return False
    arr = q8df[qfeats].to_numpy()
    return bool(np.all(arr >= 0) and np.all(arr <= np.pi))


def _check_quantum_labels(qdir: Path) -> bool:
    for s in QUANTUM_SPLITS:
        base = qdir / f"{s}.parquet"
        q8 = qdir / "quantum" / f"q8_{s}.parquet"
        if not base.exists() or not q8.exists():
            continue
        bdf = pd.read_parquet(base)
        qdf = pd.read_parquet(q8)
        if len(bdf) != len(qdf):
            return False
        if not len(bdf):
            continue
        if int(qdf[LABELS].isna().sum().sum()) != 0:
            return False
        if not (qdf["label_multiclass"].astype(str).values == bdf["label_multiclass"].astype(str).values).all():
            return False
    return True


def validate_clean(name: str) -> dict:
    path = DATASETS / name / "processed" / f"{name}_clean.parquet"
    ok = path.exists()
    rows = len(pd.read_parquet(path)) if ok else 0
    rel = str(path.relative_to(PROJ)) if ok else str(path)
    return {"gate": "clean_checkpoint", "status": "pass" if ok else "fail", "path": rel, "rows": rows}


def validate_v01(name: str) -> dict:
    qdir = DATASETS / name / "qadcp"
    gates: dict[str, str] = {}
    missing: list[str] = []

    for s in V01_SPLITS:
        p = qdir / f"{s}.parquet"
        if not p.exists():
            missing.append(f"{s}.parquet")

    for j in V01_JSONS:
        if not (qdir / j).exists():
            missing.append(j)

    for s in QUANTUM_SPLITS:
        for kind in ("q8", "pca8"):
            p = qdir / "quantum" / f"{kind}_{s}.parquet"
            if not p.exists():
                missing.append(f"quantum/{kind}_{s}.parquet")

    gates["files_present"] = "pass" if not missing else "fail"
    if missing:
        return {"gate": "v01_qadcp", "status": "fail", "missing": missing, "gates": gates}

    frames = {s: pd.read_parquet(qdir / f"{s}.parquet") for s in SPLITS}
    feat_cols = [c for c in frames["train"].columns if c not in LABELS]
    nan_ok = all(int(df[feat_cols].isna().sum().sum()) == 0 for df in frames.values() if len(df))
    gates["no_nan"] = "pass" if nan_ok else "fail"
    gates["zero_day_isolation"] = "pass" if _zd_isolated(frames, name) else "fail"
    gates["q8_angles"] = "pass" if _check_q8_angles(qdir) else "fail"
    gates["quantum_labels"] = "pass" if _check_quantum_labels(qdir) else "fail"

    passed = all(v == "pass" for v in gates.values())
    return {
        "gate": "v01_qadcp",
        "status": "pass" if passed else "fail",
        "n_features": len(feat_cols),
        "split_rows": {s: len(frames[s]) for s in SPLITS},
        "gates": gates,
    }


def validate_unified_pkg(name: str, schema: dict) -> dict:
    proc = DATASETS / name / "unified" / "processed" / f"{name}_unified.parquet"
    udir = DATASETS / name / "unified" / "qadcp"
    if not proc.exists():
        return {"gate": "unified_package", "status": "fail", "error": "missing unified processed parquet"}
    detail = validate_dataset(name, schema)
    q8_ok = _check_q8_angles(udir)
    labels_ok = _check_quantum_labels(udir)
    gates = dict(detail.get("gates", {}))
    gates["q8_angles"] = "pass" if q8_ok else "fail"
    gates["quantum_labels"] = "pass" if labels_ok else "fail"
    passed = detail.get("passed", False) and q8_ok and labels_ok
    return {
        "gate": "unified_package",
        "status": "pass" if passed else "fail",
        "gates": gates,
        "split_rows": detail.get("split_rows", {}),
    }


def verify_manifest() -> dict:
    script = PROJ / "week1" / "scripts" / "make_manifest.py"
    result = subprocess.run(
        [sys.executable, str(script), "--verify"],
        capture_output=True, text=True, cwd=str(PROJ),
    )
    ok = result.returncode == 0 and "0 mismatch" in result.stdout
    return {
        "gate": "manifest_verify",
        "status": "pass" if ok else "fail",
        "exit_code": result.returncode,
        "tail": result.stdout.strip().splitlines()[-1] if result.stdout else result.stderr.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-manifest", action="store_true", help="skip slow manifest re-hash")
    args = parser.parse_args()

    GEN.mkdir(parents=True, exist_ok=True)
    schema = load_schema()
    report: dict = {"seed": SEED, "datasets": {}, "week1_success_criteria": {}, "passed": True}

    for name in DATASET_DIRS:
        log(f"pipeline {name}")
        ds = {
            "clean": validate_clean(name),
            "v01": validate_v01(name),
            "unified": validate_unified_pkg(name, schema),
        }
        ds["passed"] = all(ds[k]["status"] == "pass" for k in ("clean", "v01", "unified"))
        report["datasets"][name] = ds
        if not ds["passed"]:
            report["passed"] = False
        status = "PASS" if ds["passed"] else "FAIL"
        log(f"  {name}: {status}")

    if not args.skip_manifest:
        log("manifest --verify")
        report["manifest"] = verify_manifest()
        if report["manifest"]["status"] != "pass":
            report["passed"] = False
    else:
        report["manifest"] = {"gate": "manifest_verify", "status": "skipped"}

    criteria = {
        "reproducible_qadcp": all(report["datasets"][n]["v01"]["status"] == "pass" for n in DATASET_DIRS),
        "standardized_datasets": all(report["datasets"][n]["unified"]["status"] == "pass" for n in DATASET_DIRS),
        "clean_checkpoints": all(report["datasets"][n]["clean"]["status"] == "pass" for n in DATASET_DIRS),
        "manifest_pinned": report["manifest"].get("status") == "pass",
    }
    report["week1_success_criteria"] = criteria
    crit_ok = all(criteria.values())
    if report["manifest"].get("status") == "skipped":
        crit_ok = all(v for k, v in criteria.items() if k != "manifest_pinned")
    if not crit_ok:
        report["passed"] = False

    out = GEN / "final_validation.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log(f"pipeline: {'ALL PASS' if report['passed'] else 'FAILURES'} -> {out}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
