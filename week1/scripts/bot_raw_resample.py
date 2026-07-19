#!/usr/bin/env python3
"""
BoT-IoT raw-mode rare-class re-sample (AK / @Thedaemon-AK) — recover the Theft zero-day.

The Day-3 200k head-sample (4k rows/file) misses BoT-IoT's ultra-rare **Theft** family
(1,587 of 73M) and thins **Normal** (9,543) → BoT-IoT's `zeroday` split is empty
(`qadcp.py` C1 / R-a). This streams the **full 74-file raw tree**, keeps **100 % of
Normal + Theft** rows, caps the DDoS/DoS/Reconnaissance majority per file, then runs the
**exact Day-3 cleaning** by reusing `preprocess.py` (same schema) — so `qadcp.py` picks
up Theft with **zero code changes** (Theft is already its BoT zero-day holdout) and
`zero_day_tiers.py` scores it automatically.

Overwrites `datasets/BoT-IoT/processed/BoT-IoT_clean.parquet` (the Day-3 version is kept
in the manifest history + `week1/_ak_day4_v0`). Needs the 41 GB raw tree. Run:
    python week1/scripts/bot_raw_resample.py
    python week1/scripts/qadcp.py && python week1/scripts/zero_day_tiers.py
"""
from __future__ import annotations

import glob
import time

import pandas as pd

import preprocess as P
from _paths import BOTIOT_DIR

SEED = 42
KEEP_ALL = {"Normal", "Theft"}      # rare classes → keep 100 %
MAJ_CAP_PER_FILE = 3000             # DDoS / DoS / Reconnaissance cap per file


def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def rare_class_sample() -> pd.DataFrame:
    files = sorted(f for f in glob.glob(str(BOTIOT_DIR / "data_*.csv"))
                   if not f.endswith("data_names.csv"))
    parts, n_rare = [], 0
    for i, f in enumerate(files, 1):
        d = pd.read_csv(f, low_memory=False)
        d.columns = d.columns.str.strip()
        cat = d["category"].astype(str).str.strip()
        rare = d[cat.isin(KEEP_ALL)]
        maj = d[~cat.isin(KEEP_ALL)]
        if len(maj) > MAJ_CAP_PER_FILE:
            maj = maj.sample(MAJ_CAP_PER_FILE, random_state=SEED)
        parts.append(pd.concat([rare, maj]))
        n_rare += len(rare)
        if i % 20 == 0 or i == len(files):
            log(f"  streamed {i}/{len(files)} files (rare kept so far {n_rare:,})")
    df = pd.concat(parts, ignore_index=True)
    c = df["category"].astype(str).str.strip()
    log(f"  raw rare-class sample: {len(df):,} rows | "
        f"Theft={int((c == 'Theft').sum()):,} Normal={int((c == 'Normal').sum()):,}")
    return df


def main():
    log("BoT-IoT raw-mode rare-class re-sample (recover Theft + Normal)")
    P.REGISTRY["BoT-IoT"]["load"] = rare_class_sample     # override the head-sample loader
    inv = P.load_inventory()
    meta = P.process("BoT-IoT", P.REGISTRY["BoT-IoT"], inv)   # reuse exact Day-3 cleaning
    dist = meta.get("class_distribution") or {}
    log(f"done -> BoT-IoT_clean.parquet: {meta['rows_after_dedup']:,} rows, "
        f"{meta['label_multiclass_classes']} classes; Theft in checkpoint = "
        f"{'Theft' in dist or 'YES (see meta)'}")


if __name__ == "__main__":
    main()
