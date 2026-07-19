#!/usr/bin/env python3
"""Week 2 Day 13: split-leakage confirmation for the classical-baseline benchmark trio.

Day-13 review ask: *confirm there is no resample-before-split or duplicate-flow leakage* before the
all-dataset baselines are read as a bar. The Day-9 ``split_integrity.py`` already hard-asserts
feature-hash disjointness with random-forest two-sample and conformal-coverage checks; this script is
the focused, standalone confirmation that ships with the Day-13 numbers. For every mentor-locked
dataset (CIC-IoT2023, BoT-IoT, UNSW-NB15) it checks four things and writes a machine-readable verdict:

1. **Cross-split duplicate flows.** Hash each row's feature vector and count identical feature rows shared
   between ``train`` and every evaluation split (``calibration``/``test``/``zeroday``) and between the
   evaluation splits themselves. A shared row is the fingerprint of a flow that survived a
   resample-before-split or a copy across splits. Expected: 0.
2. **Class-membership contract.** ``calibration`` and ``test`` carry known classes only; ``zeroday`` is
   exactly the held-out families and never appears in a known split.
3. **No resample-before-split inflation.** Within-split feature-row duplication rates are reported so a
   split that was up-sampled (duplicated rows) before partitioning is visible. QADCP dedups/balances
   inside ``train`` only, so evaluation splits should not be inflated.
4. **Binary/multiclass label consistency.** Each multiclass label maps to a single binary label.

Run from ``Team A``::

    ../.venv/bin/python week2/scripts/leakage_check.py

Output: ``week2/reports/_generated/day13_leakage_check.json`` (and a PASS/FAIL console summary).
"""
from __future__ import annotations

import json
import sys
import time
from itertools import combinations
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PARTITIONS = BASE / "week2" / "partitions"
GENERATED = BASE / "week2" / "reports" / "_generated"

TRIO = ["CICIoT2023", "BoT-IoT", "UNSW-NB15"]
SPLITS = ["train", "calibration", "test", "zeroday"]
EVAL_SPLITS = ["calibration", "test", "zeroday"]
LABEL_COLUMNS = ["label_multiclass", "label_binary", "label_family"]


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def feature_hashes(frame: pd.DataFrame, features: list[str]) -> pd.Series:
    """Stable per-row hash of the feature vector (order-fixed, index-independent)."""
    return pd.util.hash_pandas_object(frame[features], index=False)


def check_dataset(name: str) -> dict:
    directory = PARTITIONS / name
    metadata = json.loads((directory / "partition_meta.json").read_text(encoding="utf-8"))
    features = list(metadata["features"])
    frames = {split: pd.read_csv(directory / f"{split}.csv") for split in SPLITS}
    hashes = {split: feature_hashes(frame, features) for split, frame in frames.items()}
    hash_sets = {split: set(series) for split, series in hashes.items()}

    # 1. Cross-split duplicate flows (feature-vector collisions between any two splits).
    cross_split = {}
    for left, right in combinations(SPLITS, 2):
        shared = len(hash_sets[left] & hash_sets[right])
        cross_split[f"{left}|{right}"] = int(shared)
    train_eval_leak = sum(cross_split[f"train|{split}"] for split in EVAL_SPLITS)

    # 2. Class-membership contract.
    known = set(frames["train"]["label_multiclass"].unique())
    zero_day = set(frames["zeroday"]["label_multiclass"].unique())
    membership = {
        "calibration_known_only": set(frames["calibration"]["label_multiclass"].unique()).issubset(known),
        "test_known_only": set(frames["test"]["label_multiclass"].unique()).issubset(known),
        "zeroday_disjoint_from_known": known.isdisjoint(zero_day),
        "zeroday_nonempty": bool(zero_day),
        "known_classes": len(known),
        "zero_day_classes": sorted(zero_day),
    }

    # 3. Within-split duplication rate (resample-before-split would inflate this on eval splits).
    within_split = {
        split: {
            "rows": int(len(frames[split])),
            "unique_feature_rows": int(hashes[split].nunique()),
            "duplicate_rate": float(1.0 - hashes[split].nunique() / len(frames[split])),
        }
        for split in SPLITS
    }

    # 4. Binary/multiclass label consistency.
    mapping_counts = frames["train"].groupby("label_multiclass")["label_binary"].nunique()
    label_consistent = bool((mapping_counts == 1).all())

    passed = (
        train_eval_leak == 0
        and all(v == 0 for k, v in cross_split.items() if k.startswith("train|"))
        and membership["calibration_known_only"]
        and membership["test_known_only"]
        and membership["zeroday_disjoint_from_known"]
        and membership["zeroday_nonempty"]
        and label_consistent
    )
    return {
        "dataset": name,
        "passed": passed,
        "train_to_eval_duplicate_flows": int(train_eval_leak),
        "cross_split_feature_collisions": cross_split,
        "class_membership": membership,
        "within_split_duplication": within_split,
        "label_multiclass_to_binary_consistent": label_consistent,
    }


def main() -> None:
    log("Day-13 leakage confirmation | benchmark trio CIC-IoT2023 + BoT-IoT + UNSW-NB15")
    results = {name: check_dataset(name) for name in TRIO}
    for name, result in results.items():
        status = "PASS" if result["passed"] else "FAIL"
        log(f"  {name}: {status} | train->eval duplicate flows = {result['train_to_eval_duplicate_flows']}")

    overall = all(result["passed"] for result in results.values())
    payload = {
        "schema_version": "1.0",
        "description": "Day-13 confirmation: no resample-before-split or duplicate-flow leakage.",
        "overall_passed": overall,
        "datasets": results,
    }
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "day13_leakage_check.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log(f"overall: {'PASS' if overall else 'FAIL'} -> week2/reports/_generated/day13_leakage_check.json")
    sys.exit(0 if overall else 1)


if __name__ == "__main__":
    main()
