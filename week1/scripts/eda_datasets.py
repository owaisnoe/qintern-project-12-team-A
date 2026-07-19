#!/usr/bin/env python3
"""
QADCP Day-2 EDA engine — QuantumSentinel / QS-Net, Team A.

Exploratory Data Analysis across all five datasets (CIC-IoT2023, TON_IoT,
BoT-IoT, Edge-IIoTset, UNSW-NB15 ML-ready + raw). For each dataset it computes
the six Day-2 analyses — missing values, duplicate records, class imbalance,
outliers, feature distributions, feature correlations — and renders a
visualization dashboard in BOTH formats:

  * static PNG figures  -> week1/reports/figures/<slug>/*.png
  * interactive HTML    -> week1/reports/dashboard.html   (self-contained, offline)

Per-dataset stats are written to week1/reports/_generated/eda_<slug>.json.

Class-distribution / imbalance use the FULL counts from the profiler's
*_classdist.csv; the numeric analyses (missing/dup/outlier/distribution/
correlation) run on a working frame (full for small sets, a seeded stratified
sample for the huge ones) — the scope is logged in every JSON and caption.

Run inside the Python 3.12 venv, AFTER profile_datasets.py:
    python week1/scripts/eda_datasets.py
"""
from __future__ import annotations

import glob
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
sns.set_theme(style="whitegrid")

from _paths import (PROJ, GEN, FIG, CICIOT_SPLITS, TONIOT_NETWORK, BOTIOT_DIR, EDGE_ML,
                    UNSW_FEATURES, UNSW_RAW, UNSW_TRAIN, UNSW_TEST)

GEN.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

PLACEHOLDERS = {"-", "", " ", "nan", "NaN", "None", "?", "0.0.0.0"}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ------------------------------- loaders -------------------------------
def load_ciciot():
    df = pd.read_csv(CICIOT_SPLITS["validation"], low_memory=False)
    if len(df) > 200_000:
        df = df.sample(n=200_000, random_state=RANDOM_SEED).reset_index(drop=True)
    return df, "validation split, sampled to 200k"


def load_toniot():
    df = pd.read_csv(TONIOT_NETWORK, low_memory=False)
    df.columns = df.columns.str.replace("﻿", "", regex=False).str.strip()
    return df, "full file (211,043 rows)"


def load_botiot():
    files = sorted(f for f in glob.glob(str(BOTIOT_DIR / "data_*.csv"))
                   if not f.endswith("data_names.csv"))
    parts = []
    for f in files:
        d = pd.read_csv(f, nrows=4000, low_memory=False)
        d.columns = d.columns.str.strip()
        parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    return df, f"head-sample 4,000 rows x {len(files)} files ({len(df):,} rows)"


def load_edge():
    return pd.read_csv(EDGE_ML, low_memory=False), "full file (157,800 rows)"


def load_unsw_ml():
    parts = []
    for fp in (UNSW_TRAIN, UNSW_TEST):
        d = pd.read_csv(fp, low_memory=False)
        d.columns = d.columns.str.replace("﻿", "", regex=False).str.strip()
        parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    return df, "full ML-ready (257,673 rows)"


def load_unsw_raw():
    feats = pd.read_csv(UNSW_FEATURES, encoding="latin-1")
    feats.columns = feats.columns.str.strip()
    names = feats["Name"].astype(str).str.strip().tolist()
    parts = [pd.read_csv(f, header=None, names=names, nrows=60000, low_memory=False) for f in UNSW_RAW]
    df = pd.concat(parts, ignore_index=True)
    df["attack_cat"] = (df["attack_cat"].astype(str).str.strip()
                        .replace({"nan": "Normal", "": "Normal"}))
    return df, f"head-sample 60,000 x 4 files ({len(df):,} rows)"


TARGETS = [
    dict(slug="ciciot2023", name="CIC-IoT2023", load=load_ciciot, label="label",
         classdist="ciciot2023_classdist.csv", exclude=set()),
    dict(slug="toniot", name="TON_IoT (Network)", load=load_toniot, label="type",
         classdist="toniot_network_classdist.csv",
         exclude={"src_ip", "dst_ip", "src_port", "dst_port", "label", "type"}),
    dict(slug="botiot", name="BoT-IoT", load=load_botiot, label="category",
         classdist="botiot_category_classdist.csv",
         exclude={"pkSeqID", "stime", "ltime", "seq", "saddr", "daddr", "sport", "dport",
                  "smac", "dmac", "soui", "doui", "sco", "dco", "attack", "category", "subcategory"}),
    dict(slug="edge_iiotset", name="Edge-IIoTset (ML)", load=load_edge, label="Attack_type",
         classdist="edge_iiotset_classdist.csv", exclude={"Attack_label", "Attack_type"}),
    dict(slug="unsw_mlready", name="UNSW-NB15 (ML-ready)", load=load_unsw_ml, label="attack_cat",
         classdist="unsw_nb15_mlready_classdist.csv", exclude={"id", "attack_cat", "label"}),
    dict(slug="unsw_raw", name="UNSW-NB15 (raw)", load=load_unsw_raw, label="attack_cat",
         classdist="unsw_nb15_raw_classdist.csv",
         exclude={"srcip", "sport", "dstip", "dsport", "Stime", "Ltime", "attack_cat", "Label"}),
]


# ------------------------------- analyses -------------------------------
def missing_report(df: pd.DataFrame) -> dict:
    n = len(df)
    out = {}
    for c in df.columns:
        s = df[c]
        na = int(s.isna().sum())
        ph = int(s.astype(str).str.strip().isin(PLACEHOLDERS).sum()) if s.dtype == object else 0
        if na + ph > 0:
            out[c] = {"pct": round(100 * (na + ph) / n, 3), "nan": na, "placeholder": ph}
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["pct"]))


def numeric_frame(df: pd.DataFrame, exclude: set) -> pd.DataFrame:
    cols = [c for c in df.columns if c not in exclude]
    num = df[cols].apply(pd.to_numeric, errors="coerce")
    num = num.dropna(axis=1, how="all")
    num = num.loc[:, num.std(numeric_only=True) > 0]   # drop constant columns
    return num


def outlier_report(num: pd.DataFrame) -> dict:
    n = len(num)
    out = {}
    for c in num.columns:
        s = num[c].dropna()
        if s.empty:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        iqr_out = int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()) if iqr > 0 else 0
        std = s.std()
        z_out = int((((s - s.mean()).abs() / std) > 3).sum()) if std > 0 else 0
        out[c] = {"iqr_outlier_pct": round(100 * iqr_out / n, 3),
                  "z3_outlier_pct": round(100 * z_out / n, 3)}
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["iqr_outlier_pct"]))


def corr_report(num: pd.DataFrame):
    pear = num.corr(method="pearson")
    pairs = []
    cols = list(pear.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r = pear.iloc[i, j]
            if pd.notna(r) and abs(r) >= 0.9:
                pairs.append({"a": cols[i], "b": cols[j], "r": round(float(r), 4)})
    pairs.sort(key=lambda d: -abs(d["r"]))
    return pear, pairs


# ------------------------------- figures -------------------------------
def fig_classdist(slug, name, classdist_csv):
    p = GEN / classdist_csv
    if not p.exists():
        return None, None, None
    d = pd.read_csv(p)
    d = d.sort_values("count", ascending=False)
    fig, ax = plt.subplots(figsize=(10, max(3, 0.35 * len(d))))
    sns.barplot(data=d, y="class", x="count", ax=ax, color="#4C72B0")
    ax.set_xscale("log")
    ax.set_title(f"{name} — class distribution (full, log scale)")
    ax.set_xlabel("count (log)")
    fig.tight_layout()
    out = FIG / slug / "class_distribution.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    return d["class"].tolist(), d["count"].tolist(), out


def fig_missing(slug, name, miss):
    if not miss:
        return None
    items = list(miss.items())[:20]
    cols = [k for k, _ in items]
    pcts = [v["pct"] for _, v in items]
    fig, ax = plt.subplots(figsize=(10, max(3, 0.35 * len(cols))))
    sns.barplot(x=pcts, y=cols, ax=ax, color="#C44E52")
    ax.set_title(f"{name} — missing/placeholder % by column (top {len(cols)})")
    ax.set_xlabel("% missing (NaN + placeholder)")
    fig.tight_layout()
    out = FIG / slug / "missing.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    return out


def fig_corr(slug, name, pear):
    if pear.shape[0] < 2:
        return None
    fig, ax = plt.subplots(figsize=(min(16, 0.5 * len(pear) + 3), min(14, 0.5 * len(pear) + 2)))
    sns.heatmap(pear, cmap="coolwarm", center=0, vmin=-1, vmax=1, square=False,
                cbar_kws={"shrink": 0.6}, ax=ax)
    ax.set_title(f"{name} — Pearson correlation ({len(pear)} numeric features)")
    fig.tight_layout()
    out = FIG / slug / "correlation_heatmap.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    return out


def fig_distributions(slug, name, num):
    top = num.var(numeric_only=True).sort_values(ascending=False).head(9).index.tolist()
    if not top:
        return None
    ncol = 3
    nrow = int(np.ceil(len(top) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(13, 3.2 * nrow))
    axes = np.array(axes).reshape(-1)
    for ax, c in zip(axes, top):
        s = num[c].dropna()
        # clip to 1-99 pct for readability of heavy-tailed features
        lo, hi = s.quantile(0.01), s.quantile(0.99)
        sns.histplot(s.clip(lo, hi), bins=40, ax=ax, color="#55A868")
        ax.set_title(c, fontsize=9)
        ax.set_xlabel("")
    for ax in axes[len(top):]:
        ax.axis("off")
    fig.suptitle(f"{name} — distributions of top-variance features (1–99% clipped)")
    fig.tight_layout()
    out = FIG / slug / "distributions.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    return out


def fig_outliers(slug, name, num, outliers):
    top = [c for c in outliers][:8]
    if not top:
        return None
    fig, ax = plt.subplots(figsize=(12, 5))
    data = [num[c].dropna() for c in top]
    ax.boxplot(data, labels=top, showfliers=True, sym=".")
    ax.set_yscale("symlog")
    ax.set_title(f"{name} — boxplots of most-outlier-heavy features (symlog)")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=8)
    fig.tight_layout()
    out = FIG / slug / "outliers.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    return out


# ------------------------------- driver -------------------------------
def analyze(t) -> dict:
    slug, name = t["slug"], t["name"]
    (FIG / slug).mkdir(parents=True, exist_ok=True)
    log(f"{name}: loading")
    df, scope = t["load"]()
    log(f"{name}: {df.shape[0]:,} x {df.shape[1]} ({scope})")

    miss = missing_report(df)
    dup = int(df.drop(columns=[c for c in t["exclude"] if c in df.columns],
                      errors="ignore").duplicated().sum())
    lab = df[t["label"]].astype(str).str.strip() if t["label"] in df.columns else pd.Series(dtype=str)
    vc = lab.value_counts()
    imbalance = {
        "n_classes": int(vc.shape[0]),
        "ratio_max_min": round(float(vc.max() / vc.min()), 1) if vc.min() else None,
        "normalized_entropy": round(float(-(vc / vc.sum() * np.log(vc / vc.sum())).sum()
                                          / np.log(len(vc))), 4) if len(vc) > 1 else 0.0,
    }
    num = numeric_frame(df, t["exclude"])
    outliers = outlier_report(num)
    skew = {c: round(float(num[c].skew()), 3) for c in num.columns}
    kurt = {c: round(float(num[c].kurt()), 3) for c in num.columns}
    pear, hi_pairs = corr_report(num)

    labels, counts, _ = fig_classdist(slug, name, t["classdist"])
    fig_missing(slug, name, miss)
    fig_corr(slug, name, pear)
    fig_distributions(slug, name, num)
    fig_outliers(slug, name, num, outliers)

    stats = {
        "name": name, "scope": scope,
        "working_rows": int(len(df)), "working_cols": int(df.shape[1]),
        "n_numeric_features_analyzed": int(num.shape[1]),
        "duplicates_working": dup,
        "duplicates_working_pct": round(100 * dup / len(df), 3),
        "missing_top": dict(list(miss.items())[:25]),
        "class_imbalance": imbalance,
        "outliers_top": dict(list(outliers.items())[:15]),
        "skewness": skew, "kurtosis": kurt,
        "highly_correlated_pairs_abs_ge_0.9": hi_pairs,
    }
    (GEN / f"eda_{slug}.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    log(f"{name}: done (dup {dup:,}; {num.shape[1]} numeric feats; "
        f"{len(hi_pairs)} corr>=.9 pairs; {len(outliers)} feats profiled)")
    return {"slug": slug, "name": name, "labels": labels, "counts": counts,
            "miss": miss, "pear": pear, "imbalance": imbalance, "stats": stats}


def build_html_dashboard(results):
    """Self-contained offline Plotly dashboard."""
    blocks = []
    # cross-dataset imbalance panel
    names = [r["name"] for r in results]
    ratios = [r["imbalance"]["ratio_max_min"] or 0 for r in results]
    f0 = go.Figure(go.Bar(x=names, y=ratios, marker_color="#8172B3"))
    f0.update_layout(title="Cross-dataset class imbalance (majority : minority ratio, log)",
                     yaxis_type="log", height=380, template="plotly_white")
    blocks.append(f0.to_html(full_html=False, include_plotlyjs="inline"))

    for r in results:
        if r["labels"]:
            fb = go.Figure(go.Bar(x=r["counts"], y=r["labels"], orientation="h",
                                  marker_color="#4C72B0"))
            fb.update_layout(title=f"{r['name']} — class distribution (log)",
                             xaxis_type="log", height=max(300, 22 * len(r["labels"])),
                             template="plotly_white", margin=dict(l=180))
            blocks.append(fb.to_html(full_html=False, include_plotlyjs=False))
        if r["miss"]:
            items = list(r["miss"].items())[:20]
            fh = go.Figure(go.Bar(x=[v["pct"] for _, v in items],
                                  y=[k for k, _ in items], orientation="h",
                                  marker_color="#C44E52"))
            fh.update_layout(title=f"{r['name']} — missing/placeholder % (top {len(items)})",
                             height=max(300, 22 * len(items)), template="plotly_white",
                             margin=dict(l=180))
            blocks.append(fh.to_html(full_html=False, include_plotlyjs=False))
        if r["pear"].shape[0] >= 2:
            fc = go.Figure(go.Heatmap(z=r["pear"].values,
                                      x=list(r["pear"].columns), y=list(r["pear"].index),
                                      zmin=-1, zmax=1, colorscale="RdBu_r"))
            fc.update_layout(title=f"{r['name']} — Pearson correlation",
                             height=650, template="plotly_white")
            blocks.append(fc.to_html(full_html=False, include_plotlyjs=False))

    html = ("<!doctype html><html><head><meta charset='utf-8'>"
            "<title>QS-Net Week1 — EDA Dashboard</title>"
            "<style>body{font-family:system-ui,Arial,sans-serif;margin:24px;background:#fafafa;}"
            "h1{color:#333}section{background:#fff;padding:12px;margin:16px 0;border-radius:8px;"
            "box-shadow:0 1px 4px rgba(0,0,0,.08)}</style></head><body>"
            "<h1>QS-Net · Week 1 · Day 2 — Interactive EDA Dashboard</h1>"
            "<p>Team A · QuantumSentinel. Class distributions are full-set; numeric panels use the "
            "working sample logged in each report. Hover for values.</p>")
    html += "".join(f"<section>{b}</section>" for b in blocks)
    html += "</body></html>"
    out = WEEK1 / "reports" / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    log(f"Wrote {out.relative_to(PROJ)} ({out.stat().st_size/1e6:.1f} MB)")


def fig_cross_imbalance(results):
    names = [r["name"] for r in results]
    ratios = [r["imbalance"]["ratio_max_min"] or 1 for r in results]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    sns.barplot(x=names, y=ratios, ax=ax, color="#8172B3")
    ax.set_yscale("log")
    ax.set_title("Cross-dataset class imbalance (majority : minority, log)")
    ax.set_ylabel("imbalance ratio (log)")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "cross_dataset_imbalance.png", dpi=120)
    plt.close(fig)


def main():
    results = [analyze(t) for t in TARGETS]
    fig_cross_imbalance(results)
    build_html_dashboard(results)
    log(f"EDA complete: {len(results)} datasets, figures in {FIG.relative_to(PROJ)}")


if __name__ == "__main__":
    main()
