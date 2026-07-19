#!/usr/bin/env python3
"""
QADCP Day-3 preprocessing pipeline — QuantumSentinel / QS-Net, Team A.

Turns each raw dataset into a cleaned, standardized, quantum-ready table under
`datasets/<name>/processed/`. Implements the R1–R5 cleaning already specified in
`reports/00_findings_and_flaws.md` §5 and `reports/04_eda_report.md`:

  schema-normalize -> drop identifiers/empty/zero-variance (from feature_inventory.csv)
  -> `-`/blank/`0.0.0.0` -> NaN -> feature-space de-duplication -> drop >95%-missing
  -> impute -> label harmonize (incl. UNSW "Backdoors"->"Backdoor", blank->"Normal")
  -> encode categoricals (high-card => drop, low-card => ordinal) -> robust scale
  (log1p + median/IQR) -> perfect-duplicate correlation prune (|r|>=0.99) -> validate.

Each dataset is stratified-capped to ~200k rows first (keep all rare-class rows,
proportionally sample the majority) — full-set dedup on BoT-IoT (73M) is infeasible;
that scales up on Day 6.

Outputs per dataset (into datasets/<name>/processed/):
  <name>_clean.parquet     cleaned table (features + label_multiclass + label_binary)
  <name>_sample.csv        1,000-row preview
  <name>_clean_meta.json   before/after stats, dropped cols, encoders, scalers

Run inside the Python 3.12 venv, after profile_datasets.py + build_feature_inventory.py:
    python week1/scripts/preprocess.py
"""
from __future__ import annotations

import csv
import glob
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from _paths import (PROJ, DATASETS, REPORTS, CICIOT_SPLITS, TONIOT_NETWORK,
                    BOTIOT_DIR, EDGE_ML, UNSW_TRAIN, UNSW_TEST)

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
CAP = 200_000              # stratified row cap per dataset
RARE_KEEP = 2_000          # keep ALL rows of any class with <= this many rows
HIGH_CARD = 1_000          # object col with more uniques than this => identifier/free-text => drop
MISSING_MAX = 0.95         # drop columns with > this fraction missing
CORR_DUP = 0.99            # drop one of each |r| >= this pair (perfect duplicates only)
MISSING_TOKENS = {"-", "", " ", "nan", "NaN", "None", "?", "0.0.0.0"}
FEAT_INV = REPORTS / "feature_inventory.csv"


def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


# ------------------------- per-dataset registry -------------------------
def _norm_cols(df):
    df.columns = df.columns.str.replace("﻿", "", regex=False).str.strip()
    return df


def load_ciciot():
    # validation split is a representative random split; capped below.
    return _norm_cols(pd.read_csv(CICIOT_SPLITS["validation"], low_memory=False))


def load_toniot():
    return _norm_cols(pd.read_csv(TONIOT_NETWORK, low_memory=False))


def load_botiot():
    files = sorted(f for f in glob.glob(str(BOTIOT_DIR / "data_*.csv"))
                   if not f.endswith("data_names.csv"))
    parts = [pd.read_csv(f, nrows=4000, low_memory=False) for f in files]  # head-sample per file
    return _norm_cols(pd.concat(parts, ignore_index=True))


def load_edge():
    return _norm_cols(pd.read_csv(EDGE_ML, low_memory=False))


def load_unsw():
    parts = [_norm_cols(pd.read_csv(fp, low_memory=False)) for fp in (UNSW_TRAIN, UNSW_TEST)]
    return pd.concat(parts, ignore_index=True)


# key -> config. inv_name matches the "dataset" column in feature_inventory.csv.
REGISTRY = {
    "CICIoT2023":   dict(inv="CIC-IoT2023",          load=load_ciciot, primary="label",       normal="BenignTraffic"),
    "TON_IoT":      dict(inv="TON_IoT (Network)",    load=load_toniot, primary="type",        normal="normal"),
    "BoT-IoT":      dict(inv="BoT-IoT",              load=load_botiot, primary="category",     normal="Normal"),
    "Edge-IIoTset": dict(inv="Edge-IIoTset (ML)",    load=load_edge,   primary="Attack_type",  normal="Normal"),
    "UNSW-NB15":    dict(inv="UNSW-NB15 (ML-ready)", load=load_unsw,   primary="attack_cat",   normal="Normal"),
}


def load_inventory():
    """dataset_inv_name -> {'drop': set, 'label': set}."""
    out = {}
    with FEAT_INV.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d = out.setdefault(r["dataset"], {"drop": set(), "label": set()})
            if r["role"] == "drop":
                d["drop"].add(r["column"])
            elif r["role"] == "label":
                d["label"].add(r["column"])
    return out


# ------------------------------ helpers ------------------------------
def stratified_cap(df, label):
    if len(df) <= CAP:
        return df.reset_index(drop=True)
    counts = df[label].value_counts()
    rare = counts[counts <= RARE_KEEP].index
    keep = df[df[label].isin(rare)]
    rest = df[~df[label].isin(rare)]
    n = max(CAP - len(keep), 0)
    if len(rest) and n:
        frac = min(1.0, n / len(rest))
        samp = rest.groupby(label, group_keys=False, sort=False).sample(frac=frac, random_state=RANDOM_SEED)
    else:
        samp = rest.iloc[:0]
    return pd.concat([keep, samp]).sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)


def harmonize_label(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip()
    s = s.replace({"Backdoors": "Backdoor", "nan": "Normal", "": "Normal", "None": "Normal"})
    return s


def to_missing(df):
    obj = df.select_dtypes(include=["object"]).columns
    for c in obj:
        df[c] = df[c].where(~df[c].astype(str).str.strip().isin(MISSING_TOKENS), other=np.nan)
    return df


def robust_scale(s: pd.Series):
    s = s.astype("float64")
    if s.min() >= 0 and s.skew() > 2:      # heavy right tail -> log1p first
        s = np.log1p(s)
        logged = True
    else:
        logged = False
    med = s.median()
    iqr = s.quantile(0.75) - s.quantile(0.25)
    scaled = (s - med) / (iqr if iqr else 1.0)
    return scaled, logged


def perfect_dup_columns(df_num: pd.DataFrame):
    """Return columns to drop so no |r| >= CORR_DUP pair remains (keep the first)."""
    if df_num.shape[1] < 2:
        return [], []
    corr = df_num.corr().abs()
    drop, pairs = set(), []
    cols = list(corr.columns)
    for i in range(len(cols)):
        if cols[i] in drop:
            continue
        for j in range(i + 1, len(cols)):
            if cols[j] in drop:
                continue
            r = corr.iloc[i, j]
            if pd.notna(r) and r >= CORR_DUP:
                drop.add(cols[j])
                pairs.append((cols[i], cols[j], round(float(r), 4)))
    return list(drop), pairs


# ------------------------------ pipeline ------------------------------
def process(name, cfg, inv):
    t0 = time.time()
    log(f"{name}: loading")
    df = cfg["load"]()
    raw_rows, raw_cols = df.shape
    primary = cfg["primary"]

    # 3. harmonize primary label + derive binary (before capping so rare detection is clean)
    df[primary] = harmonize_label(df[primary])
    label_mc = df[primary]
    label_bin = (label_mc != cfg["normal"]).astype("int8")

    # 4. stratified cap
    df = df.assign(_lab=label_mc, _bin=label_bin)
    df = stratified_cap(df, "_lab")
    label_mc = df.pop("_lab"); label_bin = df.pop("_bin")
    capped_rows = len(df)

    # 5. separate features from ALL label columns
    label_cols = inv.get(cfg["inv"], {}).get("label", set()) | {primary}
    feats = df.drop(columns=[c for c in label_cols if c in df.columns], errors="ignore")

    # 6. drop identifiers / empty / zero-variance (from feature_inventory.csv)
    drop_struct = [c for c in inv.get(cfg["inv"], {}).get("drop", set()) if c in feats.columns]
    feats = feats.drop(columns=drop_struct)

    # 7. encoded-missing -> NaN
    feats = to_missing(feats)

    # 8. feature-space duplication METRIC on raw features (matches EDA finding); removal is at the end
    raw_feat_dup = int(feats.duplicated().sum())

    # 9. drop >95%-missing columns
    miss_frac = feats.isna().mean()
    drop_missing = miss_frac[miss_frac > MISSING_MAX].index.tolist()
    feats = feats.drop(columns=drop_missing)

    # 10. impute (numeric=median, object="missing")
    for c in feats.columns:
        if feats[c].dtype == object:
            feats[c] = feats[c].fillna("missing")
        else:
            feats[c] = feats[c].fillna(feats[c].median())

    # 11. encode categoricals: high-card object => drop (identifier/free-text); low-card => ordinal
    drop_highcard, encoders = [], {}
    for c in feats.select_dtypes(include=["object"]).columns:
        nun = feats[c].nunique()
        if nun > HIGH_CARD:
            drop_highcard.append(c)
        else:
            codes, uniques = pd.factorize(feats[c], sort=True)
            feats[c] = codes.astype("int32")
            encoders[c] = int(nun)
    feats = feats.drop(columns=drop_highcard)

    # 12. robust scale numeric features (log1p heavy tails, then median/IQR)
    logged = []
    for c in feats.columns:
        if encoders.get(c) is not None:      # keep ordinal codes as-is (categorical)
            continue
        feats[c], did_log = robust_scale(feats[c])
        if did_log:
            logged.append(c)

    # 13. perfect-duplicate correlation prune (|r| >= 0.99), numeric only
    num_cols = [c for c in feats.columns if c not in encoders]
    drop_corr, corr_pairs = perfect_dup_columns(feats[num_cols])
    feats = feats.drop(columns=drop_corr)

    # final de-duplication on the cleaned schema (earlier column drops can create new dupes)
    keepmask = ~feats.duplicated(keep="first")
    feats = feats[keepmask]
    label_mc, label_bin = label_mc[keepmask], label_bin[keepmask]
    dup_removed = int((~keepmask).sum())

    # 14. assemble, validate, write
    out = feats.reset_index(drop=True)
    out["label_multiclass"] = label_mc.reset_index(drop=True)
    out["label_binary"] = label_bin.reset_index(drop=True)
    assert out.drop(columns=["label_multiclass", "label_binary"]).isna().sum().sum() == 0, "residual NaN"
    assert not out.drop(columns=["label_multiclass", "label_binary"]).duplicated().any(), "residual feature dupes"

    outdir = DATASETS / name / "processed"
    outdir.mkdir(parents=True, exist_ok=True)
    pq = outdir / f"{name}_clean.parquet"
    out.to_parquet(pq, index=False)
    out.head(1000).to_csv(outdir / f"{name}_sample.csv", index=False)

    meta = {
        "dataset": name, "seed": RANDOM_SEED,
        "raw_rows": int(raw_rows), "raw_cols": int(raw_cols),
        "capped_rows": int(capped_rows), "cap": CAP,
        "rows_after_dedup": int(len(feats)),
        "feature_dupes_removed": int(dup_removed), "feature_space_dup_raw": raw_feat_dup,
        "n_features_final": int(feats.shape[1]),
        "label_multiclass_classes": int(out["label_multiclass"].nunique()),
        "label_binary_pos_frac": round(float(out["label_binary"].mean()), 4),
        "dropped_structural": sorted(drop_struct),
        "dropped_high_missing": sorted(drop_missing),
        "dropped_high_cardinality": sorted(drop_highcard),
        "dropped_perfect_corr": [{"kept": a, "dropped": b, "r": r} for a, b, r in corr_pairs],
        "encoded_categoricals": encoders,
        "log1p_scaled": sorted(logged),
        "outputs": {"parquet": str(pq.relative_to(PROJ)),
                    "sample_csv": str((outdir / f'{name}_sample.csv').relative_to(PROJ))},
    }
    (outdir / f"{name}_clean_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    log(f"{name}: {raw_rows:,}x{raw_cols} -> cap {capped_rows:,} -> dedup -{dup_removed:,} "
        f"-> {out.shape[0]:,}x{out.shape[1]} (feats {feats.shape[1]}) in {time.time()-t0:.1f}s")
    return meta


def main():
    inv = load_inventory()
    metas = [process(name, cfg, inv) for name, cfg in REGISTRY.items()]
    (DATASETS / "_processed_summary.json").write_text(
        json.dumps({m["dataset"]: m for m in metas}, indent=2), encoding="utf-8")
    log(f"Preprocessing complete: {len(metas)} datasets -> datasets/<name>/processed/")


if __name__ == "__main__":
    main()
