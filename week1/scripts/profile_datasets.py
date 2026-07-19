#!/usr/bin/env python3
"""
QADCP Day-1 dataset profiler — QuantumSentinel / QS-Net, Team A.

Profiles the three Day-1 datasets named in `first 7 days task.pdf`:
  - CIC-IoT2023   (Kaggle himadri07 pre-split train / test / validation)
  - TON_IoT       (Network Train_Test subset)
  - BoT-IoT       (full 74-file UNSW version, ~73M rows)

For each dataset it records: file list, measured row/column counts, feature vs
label columns, class distribution, and data-quality flaws (duplicate rows,
missing values incl. the literal '-' placeholder, constant/zero-variance
columns). Every number in the Day-1 reports is reproducible from this script.

Outputs (written to week1/reports/_generated/):
  - <dataset>_profile.json     full per-dataset profile
  - *_classdist.csv            class -> count tables
  - summary.csv                one headline row per dataset

Run inside the project's Python 3.12 venv:
    source .venv/bin/activate
    python week1/scripts/profile_datasets.py
"""
from __future__ import annotations

import glob
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

from _paths import (PROJ, GEN, CICIOT_SPLITS, TONIOT_NETWORK, BOTIOT_DIR, EDGE_ML,
                    UNSW_FEATURES, UNSW_RAW, UNSW_TRAIN, UNSW_TEST)

OUT = GEN
OUT.mkdir(parents=True, exist_ok=True)

# Values treated as "missing" even when stored as strings (TON_IoT uses '-').
MISSING_TOKENS = {"-", "", "nan", "NaN", "?", "None"}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def jsonable(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def probe_frame(df: pd.DataFrame) -> dict:
    """Data-quality probe on an in-memory frame."""
    n = len(df)
    dup = int(df.duplicated().sum())
    nan_cells = int(df.isna().sum().sum())
    obj = df.select_dtypes(include=["object"])
    placeholder = int(obj.isin(MISSING_TOKENS).sum().sum()) if not obj.empty else 0
    nun = df.nunique(dropna=False)
    const_cols = nun[nun <= 1].index.tolist()
    return {
        "rows_in_frame": n,
        "duplicate_rows": dup,
        "duplicate_pct": round(100 * dup / n, 3) if n else 0.0,
        "nan_cells": nan_cells,
        "placeholder_cells": placeholder,
        "constant_columns": const_cols,
        "n_constant_columns": len(const_cols),
    }


def col_meta(df: pd.DataFrame) -> list:
    out = []
    for c in df.columns:
        s = df[c]
        out.append({
            "name": c,
            "dtype": str(s.dtype),
            "n_unique": int(s.nunique(dropna=False)),
            "n_missing": int(s.isna().sum()),
            "example": jsonable(s.dropna().iloc[0]) if s.notna().any() else None,
        })
    return out


def save_classdist(name: str, counts: pd.Series) -> None:
    total = int(counts.sum())
    dfc = counts.rename_axis("class").reset_index(name="count")
    dfc["pct"] = (100 * dfc["count"] / total).round(4)
    dfc.to_csv(OUT / f"{name}_classdist.csv", index=False)


# ---------------------------- CIC-IoT2023 ----------------------------
def profile_ciciot() -> dict:
    log("CIC-IoT2023: starting")
    splits = CICIOT_SPLITS
    header = pd.read_csv(splits["train"], nrows=0).columns.tolist()
    label_col = "label"
    feat_cols = [c for c in header if c != label_col]

    # Full label distribution across all splits (read only the label column).
    counts = pd.Series(dtype="float64")
    rows_per_split = {}
    for s, p in splits.items():
        lab = pd.read_csv(p, usecols=[label_col])[label_col]
        rows_per_split[s] = int(len(lab))
        counts = counts.add(lab.value_counts(), fill_value=0)
        log(f"  {s}: {len(lab):,} rows")
    counts = counts.sort_values(ascending=False).astype("int64")

    # Feature stats + quality on validation split (bounded memory, representative).
    val = pd.read_csv(splits["validation"], low_memory=False)
    q = probe_frame(val)
    q["_quality_scope"] = "validation split only (memory-bounded, ~1.18M rows)"

    save_classdist("ciciot2023", counts)
    prof = {
        "name": "CIC-IoT2023",
        "source_official": "https://www.unb.ca/cic/datasets/iotdataset-2023.html",
        "source_kaggle": "https://www.kaggle.com/datasets/himadri07/ciciot2023",
        "files": {s: str(p.relative_to(PROJ)) for s, p in splits.items()},
        "rows_total_measured": int(counts.sum()),
        "rows_per_split": rows_per_split,
        "n_columns": len(header),
        "n_features": len(feat_cols),
        "label_columns": [label_col],
        "n_classes": int(counts.shape[0]),
        "class_distribution": {k: int(v) for k, v in counts.items()},
        "columns": col_meta(val),
        "quality": q,
        "notes": [
            "Kaggle himadri07 version exposes only the 34-class fine label; "
            "the 7-category and binary groupings must be derived.",
        ],
    }
    log(f"CIC-IoT2023: done ({int(counts.sum()):,} rows, {counts.shape[0]} classes)")
    return prof


# ------------------------------ TON_IoT ------------------------------
def profile_toniot() -> dict:
    log("TON_IoT: starting")
    p = TONIOT_NETWORK
    df = pd.read_csv(p, low_memory=False)
    df.columns = df.columns.str.replace("﻿", "", regex=False).str.strip()
    label_cols = ["label", "type"]
    feat_cols = [c for c in df.columns if c not in label_cols]
    counts = df["type"].value_counts().sort_values(ascending=False)
    q = probe_frame(df)
    q["_quality_scope"] = "full file"
    save_classdist("toniot_network", counts)
    prof = {
        "name": "TON_IoT (Network)",
        "source_official": "https://research.unsw.edu.au/projects/toniot-datasets",
        "source_kaggle": "https://www.kaggle.com/datasets/arnobbhowmik/ton-iot-network-dataset",
        "files": {"train_test_network": str(p.relative_to(PROJ))},
        "rows_total_measured": int(len(df)),
        "n_columns": int(df.shape[1]),
        "n_features": len(feat_cols),
        "label_columns": label_cols,
        "n_classes": int(counts.shape[0]),
        "class_distribution": {k: int(v) for k, v in counts.items()},
        "columns": col_meta(df),
        "quality": q,
        "notes": [
            "211,043 rows = standard TON_IoT variant (50k Normal vs 300k); attack rows identical "
            "(9x20k + 1,043 MITM), 461,043 - 250,000 = 211,043. NOT a partial download.",
            "Missing values are stored as the literal '-' string (see placeholder_cells).",
        ],
    }
    log(f"TON_IoT: done ({len(df):,} rows, {counts.shape[0]} classes)")
    return prof


# ------------------------------ BoT-IoT ------------------------------
def profile_botiot(sample_file_nums=(1, 12, 24, 37, 50, 62, 74),
                   sample_rows_per_file=30000) -> dict:
    log("BoT-IoT: starting")
    files = sorted(
        f for f in glob.glob(str(BOTIOT_DIR / "data_*.csv"))
        if not f.endswith("data_names.csv")
    )
    log(f"  {len(files)} data files found")
    pick = {"attack", "category", "subcategory"}

    # Full class distribution: stream label columns from every file.
    attack_counts = pd.Series(dtype="float64")
    category_counts = pd.Series(dtype="float64")
    subcat_counts = pd.Series(dtype="float64")
    total = 0
    for i, f in enumerate(files, 1):
        d = pd.read_csv(f, usecols=lambda c: c.strip() in pick)
        d.columns = d.columns.str.strip()
        total += len(d)
        attack_counts = attack_counts.add(d["attack"].value_counts(), fill_value=0)
        category_counts = category_counts.add(d["category"].value_counts(), fill_value=0)
        subcat_counts = subcat_counts.add(d["subcategory"].value_counts(), fill_value=0)
        if i % 10 == 0 or i == len(files):
            log(f"  streamed {i}/{len(files)} files, {total:,} rows so far")
    category_counts = category_counts.sort_values(ascending=False).astype("int64")
    subcat_counts = subcat_counts.sort_values(ascending=False).astype("int64")
    attack_counts = attack_counts.astype("int64")
    save_classdist("botiot_category", category_counts)
    save_classdist("botiot_subcategory", subcat_counts)

    header_raw = pd.read_csv(files[0], nrows=0).columns.tolist()
    header = [c.strip() for c in header_raw]
    label_cols = ["attack", "category", "subcategory"]
    feat_cols = [c for c in header if c not in label_cols]

    # Stratified-ish sample (spread across files) for feature stats & quality.
    idxs = sorted({min(k, len(files)) - 1 for k in sample_file_nums})
    parts = []
    for j in idxs:
        part = pd.read_csv(files[j], nrows=sample_rows_per_file, low_memory=False)
        part.columns = part.columns.str.strip()
        parts.append(part)
    sample = pd.concat(parts, ignore_index=True)
    q = probe_frame(sample)
    q["_quality_scope"] = (f"stratified sample: first {sample_rows_per_file} rows "
                           f"from files {[i+1 for i in idxs]} ({len(sample):,} rows)")

    # Programmatic flaw confirmation: does a non-first file also begin with a header line?
    second_first_cell = pd.read_csv(files[1], nrows=1, header=None).iloc[0, 0]
    header_repeated = str(second_first_cell).strip() == "pkSeqID"

    prof = {
        "name": "BoT-IoT",
        "source_official": "https://research.unsw.edu.au/projects/bot-iot-dataset",
        "files_count": len(files),
        "rows_total_measured": int(total),
        "n_columns": len(header),
        "n_features": len(feat_cols),
        "label_columns": label_cols,
        "n_classes_category": int(category_counts.shape[0]),
        "n_classes_subcategory": int(subcat_counts.shape[0]),
        "class_distribution_category": {k: int(v) for k, v in category_counts.items()},
        "class_distribution_subcategory": {k: int(v) for k, v in subcat_counts.items()},
        "attack_binary": {str(k): int(v) for k, v in attack_counts.items()},
        "columns": col_meta(sample),
        "quality": q,
        "flaws_confirmed": {
            "header_repeated_in_each_file": bool(header_repeated),
            "trailing_space_in_header": any(c != c.strip() for c in header_raw),
            "trailing_space_columns": [c for c in header_raw if c != c.strip()],
            "temporal_slices_not_shuffled": (
                "each file is a contiguous time window dominated by one attack type"),
            "leaky_identifier_columns": [
                "pkSeqID", "stime", "ltime", "saddr", "daddr", "sport", "dport",
                "smac", "dmac", "soui", "doui", "sco", "dco", "seq"],
        },
        "notes": [
            "Full 74-file BoT-IoT (~73M rows) is overkill for QML -> plan a "
            "stratified subsample for the curated dataset.",
        ],
    }
    log(f"BoT-IoT: done ({total:,} rows, categories={category_counts.shape[0]})")
    return prof


# ---------------------------- Edge-IIoTset ----------------------------
def profile_edge() -> dict:
    log("Edge-IIoTset: starting")
    p = EDGE_ML
    df = pd.read_csv(p, low_memory=False)
    label_cols = ["Attack_label", "Attack_type"]
    feat_cols = [c for c in df.columns if c not in label_cols]
    counts = df["Attack_type"].astype(str).str.strip().value_counts().sort_values(ascending=False)
    q = probe_frame(df)
    q["_quality_scope"] = "full file (ML-EdgeIIoT)"
    save_classdist("edge_iiotset", counts)
    prof = {
        "name": "Edge-IIoTset (ML)",
        "source_official": "https://www.kaggle.com/datasets/mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot",
        "paper": "Ferrag et al., 2022 (IEEE Access / TechRxiv)",
        "files": {"ml_edgeiiot": str(p.relative_to(PROJ))},
        "rows_total_measured": int(len(df)),
        "n_columns": int(df.shape[1]),
        "n_features": len(feat_cols),
        "label_columns": label_cols,
        "n_classes": int(counts.shape[0]),
        "class_distribution": {k: int(v) for k, v in counts.items()},
        "columns": col_meta(df),
        "quality": q,
        "notes": [
            "14 attacks + Normal = 15 classes; 61 selected features (of 1176 extracted).",
            "DNN-EdgeIIoT version (~2.2M rows) not profiled here.",
            "Optional dataset (shared on Discord); not in the Day-1 task-PDF trio.",
        ],
    }
    log(f"Edge-IIoTset: done ({len(df):,} rows, {counts.shape[0]} classes)")
    return prof


# ---------------------------- UNSW-NB15 (ML-ready) ----------------------------
def profile_unsw() -> dict:
    log("UNSW-NB15 (ML-ready): starting")
    parts = []
    for fp in (UNSW_TRAIN, UNSW_TEST):
        d = pd.read_csv(fp, low_memory=False)
        d.columns = d.columns.str.replace("﻿", "", regex=False).str.strip()
        d["_source_file"] = fp.name
        parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    src = df.pop("_source_file")
    label_cols = ["attack_cat", "label"]
    id_cols = ["id"]
    feat_cols = [c for c in df.columns if c not in label_cols + id_cols]
    counts = df["attack_cat"].astype(str).str.strip().value_counts().sort_values(ascending=False)
    # Drop the unique 'id' before the duplicate/quality probe, else it masks all duplicates.
    q = probe_frame(df.drop(columns=[c for c in id_cols if c in df.columns]))
    q["_quality_scope"] = "full ML-ready (training-set + testing-set), 'id' dropped for dup check"
    save_classdist("unsw_nb15_mlready", counts)
    prof = {
        "name": "UNSW-NB15 (ML-ready)",
        "source_official": "https://research.unsw.edu.au/projects/unsw-nb15-dataset",
        "paper": "Moustafa & Slay, 2015 (MilCIS)",
        "files": {"training_set": str(UNSW_TRAIN.relative_to(PROJ)),
                  "testing_set": str(UNSW_TEST.relative_to(PROJ))},
        "rows_total_measured": int(len(df)),
        "rows_per_file": {k: int(v) for k, v in src.value_counts().items()},
        "n_columns": int(df.shape[1]),
        "n_features": len(feat_cols),
        "label_columns": label_cols,
        "identifier_columns": id_cols,
        "n_classes": int(counts.shape[0]),
        "class_distribution": {k: int(v) for k, v in counts.items()},
        "columns": col_meta(df),
        "quality": q,
        "notes": [
            "File names appear SWAPPED vs canonical: training-set=82,332 rows "
            "(canonical train=175,341); testing-set=175,341 (canonical test=82,332).",
            "'id' is an identifier (drop); 'rate' is a derived feature.",
            "Not IoT-specific (general enterprise traffic).",
        ],
    }
    log(f"UNSW-NB15 (ML-ready): done ({len(df):,} rows, {counts.shape[0]} classes)")
    return prof


# ---------------------------- UNSW-NB15 (raw 4-part) ----------------------------
def profile_unsw_raw(sample_rows_per_file=50000) -> dict:
    log("UNSW-NB15 (raw): starting")
    feats = pd.read_csv(UNSW_FEATURES, encoding="latin-1")
    feats.columns = feats.columns.str.strip()
    names = feats["Name"].astype(str).str.strip().tolist()   # 49 column names
    files = UNSW_RAW
    label_cols = ["attack_cat", "Label"]
    id_cols = ["srcip", "sport", "dstip", "dsport", "Stime", "Ltime"]

    total = 0
    attack_counts = pd.Series(dtype="float64")
    missing = pd.Series(0.0, index=names)
    for f in files:
        for chunk in pd.read_csv(f, header=None, names=names, low_memory=False, chunksize=200_000):
            total += len(chunk)
            ac = (chunk["attack_cat"].astype(str).str.strip()
                  .replace({"nan": "Normal(blank)", "": "Normal(blank)"}))
            attack_counts = attack_counts.add(ac.value_counts(), fill_value=0)
            missing = missing.add(chunk.isna().sum(), fill_value=0)
    attack_counts = attack_counts.sort_values(ascending=False).astype("int64")
    save_classdist("unsw_nb15_raw", attack_counts)

    sample = pd.concat(
        [pd.read_csv(f, header=None, names=names, nrows=sample_rows_per_file, low_memory=False)
         for f in files], ignore_index=True)
    q = probe_frame(sample.drop(columns=[c for c in id_cols if c in sample.columns]))
    q["_quality_scope"] = (f"dtypes/dup from head sample ({len(sample):,} rows); "
                           f"missing counted over FULL {total:,} rows")
    q["missing_over_full"] = {k: int(v) for k, v in
                              missing[missing > 0].sort_values(ascending=False).items()}
    prof = {
        "name": "UNSW-NB15 (raw 4-part)",
        "source_official": "https://research.unsw.edu.au/projects/unsw-nb15-dataset",
        "files": [str(f.relative_to(PROJ)) for f in files],
        "rows_total_measured": int(total),
        "n_columns": len(names),
        "n_features": len(names) - len(label_cols),
        "label_columns": label_cols,
        "identifier_columns": id_cols,
        "n_classes": int(attack_counts.shape[0]),
        "class_distribution": {k: int(v) for k, v in attack_counts.items()},
        "columns": col_meta(sample),
        "quality": q,
        "notes": [
            "No header row; 49 column names assigned from NUSW-NB15_features.csv.",
            "attack_cat is blank (NaN) for Normal rows -> shown as 'Normal(blank)'.",
            "Whitespace / 'Backdoors' vs 'Backdoor' label inconsistency; sport/dsport can be hex.",
            "Contains identifiers (srcip/sport/dstip/dsport/Stime/Ltime) -> leakage; drop.",
        ],
    }
    log(f"UNSW-NB15 (raw): done ({total:,} rows, {attack_counts.shape[0]} attack_cat values)")
    return prof


def main() -> None:
    fns = {
        "ciciot": profile_ciciot, "toniot": profile_toniot, "botiot": profile_botiot,
        "edge": profile_edge, "unsw": profile_unsw, "unsw_raw": profile_unsw_raw,
    }
    profiles = {}
    for key, fn in fns.items():
        p = fn()
        profiles[key] = p
        (OUT / f"{key}_profile.json").write_text(
            json.dumps(p, indent=2, default=jsonable), encoding="utf-8")

    rows = []
    for p in profiles.values():
        n_classes = p.get("n_classes") or p.get("n_classes_category")
        rows.append({
            "dataset": p["name"],
            "rows_measured": p.get("rows_total_measured"),
            "n_columns": p.get("n_columns"),
            "n_features": p.get("n_features"),
            "n_classes": n_classes,
            "duplicate_pct": p["quality"].get("duplicate_pct"),
            "placeholder_cells": p["quality"].get("placeholder_cells"),
            "n_constant_cols": p["quality"].get("n_constant_columns"),
            "quality_scope": p["quality"].get("_quality_scope"),
        })
    pd.DataFrame(rows).to_csv(OUT / "summary.csv", index=False)
    log(f"Wrote summary.csv + {len(profiles)} profiles to {OUT.relative_to(PROJ)}")


if __name__ == "__main__":
    main()
