#!/usr/bin/env python3
"""Day 6 — project Day-3 clean checkpoints onto the unified feature schema.

Reads datasets/<name>/processed/*_clean.parquet, maps to shared columns,
deduplicates on unified feature space, writes unified/processed/*_unified.parquet.

Frequency encoding of categoricals happens in qadcp.py --unified (train-fit only).
Run: python week1/scripts/unified_schema.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from _paths import DATASETS, PROJ
from _unified import CAT_COLS, LABELS, NUM_COLS, dedup_features, load_schema, project_dataset

SEED = 42
DATASET_DIRS = ["CICIoT2023", "TON_IoT", "BoT-IoT", "Edge-IIoTset", "UNSW-NB15"]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def process(name: str, schema: dict) -> dict:
    src = DATASETS / name / "processed" / f"{name}_clean.parquet"
    if not src.exists():
        log(f"  {name}: missing {src.name} — skip")
        return {}
    out_dir = DATASETS / name / "unified" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(src)
    rows_in = len(df)
    unified = project_dataset(name, df)
    unified, dup_removed = dedup_features(unified)

    meta = {
        "dataset": name,
        "seed": SEED,
        "schema_version": schema["version"],
        "source_checkpoint": str(src.relative_to(PROJ)),
        "rows_in": rows_in,
        "rows_after_dedup": len(unified),
        "feature_dupes_removed": dup_removed,
        "n_features_unified": len(NUM_COLS) + 2,
        "columns": NUM_COLS + CAT_COLS + LABELS,
        "categorical_raw": CAT_COLS,
        "note": "protocol/conn_state frequency-encoded in qadcp.py --unified (train-fit)",
    }
    out_path = out_dir / f"{name}_unified.parquet"
    unified.to_parquet(out_path, index=False)
    (out_dir / f"{name}_unified_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    log(f"  {name}: {rows_in:,} -> dedup -{dup_removed:,} -> {len(unified):,} rows x {len(NUM_COLS)+2} feats+cats")
    return meta


def main() -> None:
    schema = load_schema()
    summary = {}
    for name in DATASET_DIRS:
        log(f"unified {name}")
        summary[name] = process(name, schema)
    gen = PROJ / "week1" / "reports" / "_generated"
    gen.mkdir(parents=True, exist_ok=True)
    (gen / "unified_projection_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    log("done -> datasets/<name>/unified/processed/*_unified.parquet")


if __name__ == "__main__":
    sys.exit(main())
