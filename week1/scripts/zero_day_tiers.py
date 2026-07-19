"""Day 5 — Difficulty-aware zero-day benchmark (Easy / Medium / Hard tiers).

Design: reports/09_zero_day_benchmark.md. Assigns a difficulty tier to attack
families by how DISSIMILAR they are from everything a model would train on:

  metric A (primary)  — feature-space similarity: symmetric centroid distance
                        between the held-out family and its nearest attack family
                        in train, on robust-scaled QADCP features (deterministic,
                        model-free); plus k-NN overlap fraction as a local check.
  metric B (validate) — classifier transfer: RandomForest trained WITHOUT the
                        family (binary attack-vs-benign), detection recall on the
                        family. Low recall = genuinely hard zero-day.
  metric C (context)  — task-sheet "clustering": KMeans over all attack rows;
                        family isolation = 1 - max cluster-purity overlap with
                        any trained family.

Tiers (fixed, pre-registered thresholds on the blended difficulty score in [0,1],
score = 0.5*simA_norm + 0.3*(1-recallB) + 0.2*isolationC):
  Easy < 0.35 <= Medium < 0.60 <= Hard

Two granularities per dataset:
  1. holdout  — the actual qadcp/zeroday.parquet families (the shipped benchmark)
  2. loo      — every attack family with >=50 train rows, leave-one-out (design
                table for Day-6 cross-dataset tiers; BoT-IoT Theft joins when the
                raw-mode re-run lands, R-a)

Outputs -> datasets/<name>/qadcp/zero_day_tiers.json
        -> reports/_generated/zero_day_tiers.csv + zero_day_tiers_summary.json
        -> reports/figures/zero_day_tiers.png
Run: python week1/scripts/zero_day_tiers.py   (seed 42, ~1-2 min all datasets)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import NearestNeighbors

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "datasets"
GEN = BASE / "week1" / "reports" / "_generated"

SEED = 42
DATASETS = ["CICIoT2023", "TON_IoT", "BoT-IoT", "Edge-IIoTset", "UNSW-NB15"]
MIN_FAMILY_ROWS = 50          # LOO candidates need enough rows to score reliably
SAMPLE_PER_FAMILY = 5_000     # cap per family for distance/kNN/cluster work
RF_TRAIN_CAP = 60_000
KNN_K = 10
TIER_EDGES = (0.35, 0.60)     # pre-registered: Easy < .35 <= Medium < .60 <= Hard
W_SIM, W_TRANSFER, W_ISO = 0.5, 0.3, 0.2
BENIGN = "benign"


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def tier_of(score: float) -> str:
    return "Easy" if score < TIER_EDGES[0] else ("Medium" if score < TIER_EDGES[1] else "Hard")


def fam_sample(df: pd.DataFrame, fam_col: str, fam: str, feats: list[str],
               rng: np.random.Generator) -> np.ndarray:
    g = df[df[fam_col] == fam]
    if len(g) > SAMPLE_PER_FAMILY:
        g = g.sample(n=SAMPLE_PER_FAMILY, random_state=SEED)
    return g[feats].to_numpy(dtype=np.float64)


def centroid_distance(x_hold: np.ndarray, train_fams: dict[str, np.ndarray]) -> tuple[float, str]:
    """Min over trained attack families of the centroid L2 distance (scaled space)."""
    c_hold = x_hold.mean(axis=0, keepdims=True)
    best, best_fam = np.inf, ""
    for fam, x in train_fams.items():
        d = float(cdist(c_hold, x.mean(axis=0, keepdims=True))[0, 0])
        if d < best:
            best, best_fam = d, fam
    return best, best_fam


def knn_overlap(x_hold: np.ndarray, x_train_attacks: np.ndarray) -> float:
    """Fraction of held-out points whose train-attack NN is 'close' (< median
    train-attack self-NN distance). 1.0 = family sits inside trained attack space."""
    nn = NearestNeighbors(n_neighbors=1).fit(x_train_attacks)
    d_hold = nn.kneighbors(x_hold, return_distance=True)[0][:, 0]
    nn_self = NearestNeighbors(n_neighbors=2).fit(x_train_attacks)
    d_self = nn_self.kneighbors(x_train_attacks, return_distance=True)[0][:, 1]
    return float((d_hold < np.median(d_self)).mean())


def transfer_recall(train_df: pd.DataFrame, hold_x: np.ndarray, feats: list[str],
                    exclude_fam: str | None) -> float:
    """RF attack-vs-benign trained without exclude_fam; recall on the held-out family."""
    tr = train_df if exclude_fam is None else train_df[train_df["label_family"] != exclude_fam]
    if len(tr) > RF_TRAIN_CAP:
        # keep all benign (often scarce), cap attacks
        ben = tr[tr["label_family"] == BENIGN]
        att = tr[tr["label_family"] != BENIGN]
        att = att.sample(n=max(RF_TRAIN_CAP - len(ben), 10_000), random_state=SEED) \
            if len(att) > RF_TRAIN_CAP - len(ben) else att
        tr = pd.concat([ben, att])
    y = (tr["label_family"] != BENIGN).to_numpy()
    if y.all() or not y.any():          # degenerate (e.g. BoT-IoT: 27 benign rows)
        return float("nan")
    rf = RandomForestClassifier(n_estimators=150, max_depth=20, n_jobs=-1,
                                random_state=SEED, class_weight="balanced")
    rf.fit(tr[feats].to_numpy(dtype=np.float64), y)
    return float(rf.predict(hold_x).mean())    # all held-out rows are attacks


def cluster_isolation(fam_arrays: dict[str, np.ndarray], target: str) -> float:
    """KMeans over all attack families; isolation = 1 - (target rows sharing a
    cluster whose majority is another trained family) -> 1.0 = own private cluster."""
    fams = [f for f in fam_arrays if len(fam_arrays[f])]
    X = np.vstack([fam_arrays[f] for f in fams])
    labels = np.repeat(np.arange(len(fams)), [len(fam_arrays[f]) for f in fams])
    k = min(max(len(fams), 4), 12)
    km = KMeans(n_clusters=k, n_init=4, random_state=SEED).fit(X)
    t_idx = fams.index(target)
    t_mask = labels == t_idx
    shared = 0
    for c in range(k):
        in_c = km.labels_ == c
        t_in_c = int((in_c & t_mask).sum())
        if not t_in_c:
            continue
        # does any OTHER family dominate this cluster?
        others = int((in_c & ~t_mask).sum())
        if others > t_in_c:
            shared += t_in_c
    return 1.0 - shared / max(int(t_mask.sum()), 1)


def score_family(name: str, fam: str, hold_x: np.ndarray, train_df: pd.DataFrame,
                 feats: list[str], train_fam_arrays: dict[str, np.ndarray],
                 sim_norm_ref: float, mode: str) -> dict:
    """Blend A/B/C into the difficulty score for one held-out family."""
    train_attacks = {f: a for f, a in train_fam_arrays.items() if f not in (BENIGN, fam)}
    if not train_attacks:
        return {"family": fam, "mode": mode, "error": "no other attack families in train"}
    d_cent, nearest = centroid_distance(hold_x, train_attacks)
    x_all_attacks = np.vstack(list(train_attacks.values()))
    overlap = knn_overlap(hold_x, x_all_attacks)
    sim_a = 1.0 - overlap                                    # local dissimilarity in [0,1]
    sim_a = 0.5 * sim_a + 0.5 * min(d_cent / sim_norm_ref, 1.0)   # blend local + global
    rec_b = transfer_recall(train_df, hold_x, feats, exclude_fam=fam if mode == "loo" else None)
    iso_c = cluster_isolation({**train_attacks, fam: hold_x}, fam)
    if np.isnan(rec_b):                                      # degenerate benign -> reweight A/C
        score = (W_SIM * sim_a + W_ISO * iso_c) / (W_SIM + W_ISO)
        rec_out = None
    else:
        score = W_SIM * sim_a + W_TRANSFER * (1.0 - rec_b) + W_ISO * iso_c
        rec_out = round(rec_b, 4)
    return {"family": fam, "mode": mode, "n_rows": int(len(hold_x)),
            "nearest_train_family": nearest,
            "centroid_distance": round(d_cent, 4), "knn_overlap": round(overlap, 4),
            "simA": round(sim_a, 4), "transfer_recallB": rec_out,
            "cluster_isolationC": round(iso_c, 4),
            "difficulty_score": round(float(score), 4), "tier": tier_of(float(score))}


def process(name: str, unified: bool = False) -> dict:
    rng = np.random.default_rng(SEED)
    q = DATA / name / ("unified/qadcp" if unified else "qadcp")
    train = pd.read_parquet(q / "train.parquet")
    feats = [c for c in train.columns if not c.startswith("label_")]
    # median-IQR-scaled space: use a fixed global reference for centroid-distance
    # normalization = 95th pct of pairwise train-family centroid distances
    fam_arrays = {f: fam_sample(train, "label_family", f, feats, rng)
                  for f in train["label_family"].unique()}
    cents = np.vstack([a.mean(axis=0) for f, a in fam_arrays.items() if f != BENIGN])
    ref = float(np.percentile(cdist(cents, cents)[np.triu_indices(len(cents), 1)], 95)) \
        if len(cents) > 1 else 1.0

    results = []
    # granularity 1: the shipped zeroday split
    zd_path = q / "zeroday.parquet"
    if zd_path.exists():
        zd = pd.read_parquet(zd_path)
        for fam in sorted(zd["label_family"].unique()):
            hx = fam_sample(zd, "label_family", fam, feats, rng)
            results.append(score_family(name, fam, hx, train, feats, fam_arrays, ref, "holdout"))
            log(f"  {name} holdout {fam}: {results[-1].get('tier','?')} "
                f"(score {results[-1].get('difficulty_score')})")
    else:
        log(f"  {name}: no zeroday.parquet (BoT-IoT Theft pending raw re-run, R-a)")

    # granularity 2: leave-one-out over trainable families (Day-6 design table)
    for fam in sorted(train["label_family"].unique()):
        if fam == BENIGN or len(train[train["label_family"] == fam]) < MIN_FAMILY_ROWS:
            continue
        hx = fam_arrays[fam]
        others = {f: a for f, a in fam_arrays.items() if f != fam}
        results.append(score_family(name, fam, hx,
                                    train[train["label_family"] != fam], feats,
                                    others, ref, "loo"))
        log(f"  {name} loo {fam}: {results[-1].get('tier','?')} "
            f"(score {results[-1].get('difficulty_score')})")

    out = {"dataset": name, "seed": SEED, "mode": "unified" if unified else "v0.1",
           "config": {"weights": {"simA": W_SIM, "transferB": W_TRANSFER, "isolationC": W_ISO},
                      "tier_edges": TIER_EDGES, "knn_k": KNN_K,
                      "sample_per_family": SAMPLE_PER_FAMILY,
                      "centroid_norm_ref_p95": round(ref, 4)},
           "families": results}
    (q / "zero_day_tiers.json").write_text(json.dumps(out, indent=1))
    return out


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--unified", action="store_true")
    args = parser.parse_args()
    GEN.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name in DATASETS:
        log(f"zero-day tiers: {name} ({'unified' if args.unified else 'v0.1'})")
        summary[name] = process(name, unified=args.unified)
    fname = "unified_zero_day_tiers_summary.json" if args.unified else "zero_day_tiers_summary.json"
    (GEN / fname).write_text(json.dumps(summary, indent=1))
    # compact cross-dataset tier table for the report
    rows = [{"dataset": d, **{k: r[k] for k in
             ("family", "mode", "tier", "difficulty_score", "transfer_recallB",
              "nearest_train_family")}}
            for d, s in summary.items() for r in s["families"] if "error" not in r]
    df = pd.DataFrame(rows)
    csv_name = "unified_zero_day_tiers.csv" if args.unified else "zero_day_tiers.csv"
    df.to_csv(GEN / csv_name, index=False)
    make_figure(df, unified=args.unified)
    log(f"done -> {GEN / fname} + {GEN / csv_name}")


def make_figure(d: pd.DataFrame, unified: bool = False) -> None:
    """figures/zero_day_tiers.png — every family, sorted by score, tier-colored."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = d.sort_values("difficulty_score")
    colors = {"Easy": "#0b6e4f", "Medium": "#c98a00", "Hard": "#8b1a1a"}
    fig, ax = plt.subplots(figsize=(10, 9))
    labels = d["dataset"] + " · " + d["family"] + np.where(d["mode"] == "holdout", " ★", "")
    y = np.arange(len(d))
    ax.barh(y, d["difficulty_score"], color=[colors[t] for t in d["tier"]], alpha=0.85)
    ax.scatter(1 - d["transfer_recallB"].fillna(-1), y, marker="D", s=28, color="#15304b",
               zorder=3, label="1 − transfer recall (metric B)")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    for edge in TIER_EDGES:
        ax.axvline(edge, color="#999999", lw=1, ls="--")
    for x, t in ((0.175, "Easy"), (0.475, "Medium"), (0.78, "Hard")):
        ax.text(x, len(d) - 0.2, t.upper(), ha="center", color=colors[t], fontweight="bold")
    ax.set_xlabel(f"difficulty score  ({W_SIM}·simA + {W_TRANSFER}·(1−recallB) + {W_ISO}·isolationC)")
    ax.set_title("QS-Net zero-day difficulty tiers — ★ = shipped zeroday split, "
                 "rest = leave-one-out design table", fontsize=10.5)
    ax.set_xlim(0, 1)
    ax.invert_yaxis()
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fname = "zero_day_tiers_unified.png" if unified else "zero_day_tiers.png"
    out = BASE / "week1" / "reports" / "figures" / fname
    fig.savefig(out, dpi=150, facecolor="white")


if __name__ == "__main__":
    sys.exit(main())
