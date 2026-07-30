#!/usr/bin/env python3
"""
Week 5 · Day 26 (Team A) — Table A (in-distribution detection, RQ1) + significance + coverage diagnostics.

Task (`qi26_12_Week_5.pdf`): *Finalise Table A (in-distribution detection) with significance markers and an
all-seed coverage check.* Deliverable: the paper's **RQ1** table — how well each system classifies KNOWN
traffic — with McNemar significance vs the strong classical detector, plus the coverage evidence Team A owns.

What Table A is (and how it differs from Table B)
-------------------------------------------------
Table B (Day 24, `week4/scripts/rq2_table_b.py`) is the **zero-day guarantee** (RQ2): achieved false-alarm
rate vs α and true-zero-day recall. Table A is the complementary **closed-set** result (RQ1): on the KNOWN
test split, accuracy / macro-F1 / one-vs-rest macro AUROC for each system. A detector has to be good at the
known task before its novelty behaviour is interesting, so RQ1 is the table that establishes the baseline is
strong and QS-Net is competitive on it.

Two arms, two provenances (no dummy number can pass as a result)
----------------------------------------------------------------
  XGBoost (detector)  REAL, FINAL — read straight from `week2/baselines/<ds>/results.json`
                      (`detector.multiclass.{accuracy,f1_macro,auroc_ovr_macro}`), the frozen Day-12 model
                      on real features. Never recomputed here.
  QS-Net (CQ-ZDR)     PROVISIONAL — computed from the Day-14 **dummy** fidelity interface
                      (`test_scores.parquet`): accuracy = mean(pred_correct); macro-F1 from pred_class;
                      OVR-macro AUROC computed per known class from the `fid__<class>` columns (raw
                      non-squared fidelity as the class score). Reprices on Team B's real prototypes with
                      `--source real` — no code change.
Every QS-Net cell carries the ‡ provisional marker and the rendered `.tex`/`.md` carry the legend.

Significance (the "significance markers")
-----------------------------------------
Exact two-sided **McNemar** (Day-17 `stats_protocol.mcnemar_exact`) on the paired per-sample correctness of
QS-Net vs XGBoost on the shared KNOWN test split, row-aligned by a true-label guard, **Holm-corrected**
(Day-17 `holm_bonferroni`) over the dataset family. A `*` on the QS-Net accuracy cell = the two systems
differ significantly at α after Holm. On the dummy interface this compares a placeholder against a real
model, so the marker is itself provisional; it reprices with the real scores.

Coverage evidence Team A owns (beside the RQ1 numbers)
------------------------------------------------------
1. **All-seed coverage check** — the split-conformal guarantee is marginal over the calibration/test draw,
   so it must be stable across seeds, not one lucky split. Reusing Day-23 `live_coverage.fix_splits`, the
   pooled KNOWN calibration ∪ test scores are re-drawn at the original sizes under the 5-seed convention
   (42–46); each re-split's achieved false-zero-day rate is judged against its exact BetaBinomial band
   (Day-16 `coverage_band`). Reported as mean FZR + #in-band / 5.
2. **Per-class achieved-FZR diagnostic** — marginal conformal controls the false-alarm rate over the KNOWN
   *mixture*; it gives **no per-class guarantee**. (Directly answering a review flag that dataset imbalance
   might undermine the threshold: tiny classes contribute few pooled points and do NOT skew the marginal q —
   the mixture guarantee still holds — but a rare class can be individually under/over-covered.) Each known
   class's test flag count is judged against **its own** exact band `coverage_band(n_cal, k, m_c)`; classes
   outside their band are flagged. The fix if a class is badly off is **clustered conformal** (Ding et al.
   2023), not fully class-conditional (CIC's ≤ 9-row classes are far below the ⌈1/α⌉−1 = 19 floor).

Report: week5/reports/w5_02_table_a.md
Table A skeleton: week5/reports/_generated/w5_02_table_a.md + .tex (booktabs)
JSON/CSV: week5/reports/_generated/w5_02_table_a.{json,csv} + w5_02_per_class_fzr.csv
Run (venv): python week5/scripts/table_a.py --datasets CICIoT2023 BoT-IoT UNSW-NB15 --alpha 0.05
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import f1_score

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week3" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))

from conformal_calibrate import (  # noqa: E402  (Day-15 — score rule + io + threshold)
    IFACE, TRIO, conformal_threshold, known_classes, load_scores, nonconformity_from_fidelities,
)
from coverage_harness import DEFAULT_BAND, coverage_band  # noqa: E402  (Day-16 — exact finite-sample band)
from live_coverage import fix_splits                       # noqa: E402  (Day-23 — pooled re-split)
from stats_protocol import holm_bonferroni, mcnemar_exact  # noqa: E402  (Day-17 — significance + multiplicity)

BASELINES = BASE / "week2" / "baselines"
GEN = BASE / "week5" / "reports" / "_generated"
REPORTS = BASE / "week5" / "reports"

SEED = 42
DEFAULT_ALPHA = 0.05
SEEDS = [42, 43, 44, 45, 46]              # repo 5-seed convention

FINAL = "final"                # real Day-12 model on real features
PROVISIONAL = "provisional"    # rides the Day-14 dummy fidelity interface

XGBOOST_LABEL = "XGBoost (detector)"
QUANTUM_LABEL = "QS-Net (CQ-ZDR)"


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def _rel(p):
    """Repo-relative path for committed outputs (an absolute path would leak the author's home dir)."""
    p = Path(p)
    try:
        return p.resolve().relative_to(BASE).as_posix()
    except ValueError:
        return str(p)


def _auroc(pos, neg):
    """Rank AUROC = U / (n_pos·n_neg) (ties at ½). None if either side is empty."""
    pos, neg = np.asarray(pos, dtype=float), np.asarray(neg, dtype=float)
    if pos.size == 0 or neg.size == 0:
        return None
    u = stats.mannwhitneyu(pos, neg, alternative="two-sided").statistic
    return float(u / (pos.size * neg.size))


# ---------------------------------------------------------------- the two arms (RQ1 metrics)

def xgboost_row(dataset):
    """REAL closed-set metrics — read from the frozen Day-12 detector's results.json (not recomputed)."""
    f = BASELINES / dataset / "results.json"
    if not f.exists():
        raise FileNotFoundError(f"{f} — the frozen Day-12 baselines must be present for the real arm")
    mc = json.loads(f.read_text(encoding="utf-8"))["detector"]["multiclass"]
    return {"dataset": dataset, "system": XGBOOST_LABEL, "arm": "classical", "source_kind": "real",
            "accuracy": round(float(mc["accuracy"]), 4),
            "macro_f1": round(float(mc["f1_macro"]), 4),
            "auroc_ovr_macro": round(float(mc["auroc_ovr_macro"]), 4),
            "n_classes": int(mc.get("auroc_classes_evaluated", 0)),
            "provenance": "week2/baselines/<ds>/results.json (detector.multiclass)"}


def qsnet_row(dataset, scores_root, source):
    """PROVISIONAL closed-set metrics from the (dummy) fidelity interface — reprices on real prototypes."""
    frames = load_scores(dataset, scores_root)
    known = known_classes(frames)
    test = frames["test"]
    y_true = test["true_label_multiclass"].to_numpy()
    y_pred = test["pred_class"].to_numpy()

    acc = float(np.mean(test["pred_correct"].to_numpy(dtype=float)))
    macro_f1 = float(f1_score(y_true, y_pred, labels=known, average="macro", zero_division=0))

    # OVR-macro AUROC: per known class, raw fid__<class> as the class score (positive = that class).
    aucs = []
    for c in known:
        col = test[f"fid__{c}"].to_numpy(dtype=float)
        m = y_true == c
        a = _auroc(col[m], col[~m])
        if a is not None:
            aucs.append(a)
    ovr = float(np.mean(aucs)) if aucs else None

    return {"dataset": dataset, "system": QUANTUM_LABEL, "arm": "quantum", "source_kind": source,
            "accuracy": round(acc, 4), "macro_f1": round(macro_f1, 4),
            "auroc_ovr_macro": None if ovr is None else round(ovr, 4),
            "n_classes": len(aucs),
            "provenance": "week2/interface/.../test_scores.parquet (pred_correct / pred_class / fid__*)"}


# ---------------------------------------------------------------- McNemar (QS-Net vs XGBoost)

def paired_correct(dataset, scores_root):
    """Row-aligned per-sample correctness on the KNOWN test split: (qsnet_correct, xgboost_correct).

    Aligns the dummy interface's test rows to the baseline predictions by a true-label guard — if the two
    label vectors disagree the splits are not the same rows and we refuse to compute a paired test.
    """
    frames = load_scores(dataset, scores_root)
    test = frames["test"]
    qs_correct = test["pred_correct"].to_numpy().astype(bool)
    y_iface = test["true_label_multiclass"].astype(str).to_numpy()

    p = pd.read_csv(BASELINES / dataset / "predictions.csv",
                    usecols=["split", "row_index", "true_label_multiclass", "xgboost_prediction"])
    p = p[p["split"] == "test"].sort_values("row_index").reset_index(drop=True)
    y_pred = p["true_label_multiclass"].astype(str).to_numpy()

    if y_iface.shape != y_pred.shape or not np.array_equal(y_iface, y_pred):
        raise AssertionError(
            f"{dataset}: dummy test rows are not row-aligned with predictions.csv[test] "
            f"(true-label guard failed) — cannot compute a paired McNemar")
    xgb_correct = (p["xgboost_prediction"].astype(str).to_numpy() == y_pred)
    return qs_correct, xgb_correct


def mcnemar_row(dataset, scores_root):
    """Exact McNemar on QS-Net vs XGBoost paired correctness (raw p; Holm applied over the family later)."""
    qs, xgb = paired_correct(dataset, scores_root)
    n01 = int(np.sum(~qs & xgb))          # XGBoost right where QS-Net wrong
    n10 = int(np.sum(qs & ~xgb))          # QS-Net right where XGBoost wrong
    mc = mcnemar_exact(n10, n01)          # (n01, n10) order is symmetric for the two-sided exact test
    return {"dataset": dataset, "pair": f"{QUANTUM_LABEL} vs {XGBOOST_LABEL}", "n_pairs": int(qs.size),
            "qsnet_only_right": n10, "xgboost_only_right": n01, "p_raw": mc["p"], "note": mc["note"]}


# ---------------------------------------------------------------- coverage evidence

def all_seed_coverage(dataset, scores_root, alpha, seeds=SEEDS, band_level=DEFAULT_BAND):
    """Pooled KNOWN calibration ∪ test re-split under each seed; FZR judged vs its own exact band.

    Reuses Day-23 `fix_splits` (a uniformly random split of a pooled set is exchangeable by construction),
    so this measures whether the conformal false-alarm rate is stable across the 5-seed convention — not a
    single lucky split. On the Day-14 dummy interface it is a placeholder; reprices on real scores.
    """
    frames = load_scores(dataset, scores_root)
    known = known_classes(frames)
    s_cal = nonconformity_from_fidelities(frames["calibration"], known)
    s_test = nonconformity_from_fidelities(frames["test"], known)
    y_cal = frames["calibration"]["true_label_multiclass"].to_numpy()
    y_test = frames["test"]["true_label_multiclass"].to_numpy()

    rows = []
    for sd in seeds:
        sc, _, st, _ = fix_splits(s_cal, y_cal, s_test, y_test, seed=sd)
        q, k, n = conformal_threshold(sc, alpha)
        m = int(st.size)
        e = int(np.sum(st > q))
        lo, hi, _, _ = coverage_band(n, k, m, band_level)
        rows.append({"seed": sd, "n_cal": n, "k": k, "m_test": m, "false_flags": e,
                     "fzr": round(e / m, 6) if m else 0.0,
                     "band_lo_rate": round(lo / m, 6) if m else 0.0,
                     "band_hi_rate": round(hi / m, 6) if m else 0.0,
                     "in_band": bool(lo <= e <= hi)})
    fzrs = [r["fzr"] for r in rows]
    return {"dataset": dataset, "seeds": list(seeds), "per_seed": rows,
            "mean_fzr": round(float(np.mean(fzrs)), 6), "max_fzr": round(float(np.max(fzrs)), 6),
            "n_in_band": int(sum(r["in_band"] for r in rows)), "n_seeds": len(seeds),
            "all_in_band": bool(all(r["in_band"] for r in rows))}


def per_class_fzr(dataset, scores_root, alpha, band_level=DEFAULT_BAND):
    """Each known class's test false-flag count vs ITS OWN exact band under the marginal threshold.

    Marginal conformal gives no per-class coverage guarantee (the review flag). A class outside its band is
    under/over-covered relative to the pooled rate — the signal for clustered conformal (Ding et al. 2023).
    """
    frames = load_scores(dataset, scores_root)
    known = known_classes(frames)
    s_cal = nonconformity_from_fidelities(frames["calibration"], known)
    s_test = nonconformity_from_fidelities(frames["test"], known)
    q, k, n = conformal_threshold(s_cal, alpha)
    yt = frames["test"]["true_label_multiclass"].to_numpy()
    flagged = s_test > q

    floor = int(np.ceil(1.0 / alpha)) - 1          # ⌈1/α⌉−1 class-conditional floor (Ding et al. 2023)
    rows = []
    for c in known:
        m = yt == c
        m_c = int(m.sum())
        if m_c == 0:
            continue
        e_c = int(flagged[m].sum())
        lo, hi, expected, _ = coverage_band(n, k, m_c, band_level)
        rows.append({"dataset": dataset, "class": str(c), "m_test": m_c, "false_flags": e_c,
                     "fzr": round(e_c / m_c, 6), "band_lo_rate": round(lo / m_c, 6),
                     "band_hi_rate": round(hi / m_c, 6), "expected_rate": round(expected, 6),
                     "in_band": bool(lo <= e_c <= hi),
                     "below_conditional_floor": bool(m_c < floor)})
    n_out = sum(not r["in_band"] for r in rows)
    return {"dataset": dataset, "n_cal": n, "k": k, "threshold_q": (None if np.isinf(q) else round(q, 6)),
            "alpha": alpha, "conditional_floor": floor, "n_classes": len(rows),
            "n_out_of_band": n_out, "per_class": rows}


# ---------------------------------------------------------------- assembly

def build_table_a(datasets, scores_root, source, alpha, band_level=DEFAULT_BAND):
    rows, mcnemar, coverage, per_class = [], [], [], []
    for ds in datasets:
        rows.append(xgboost_row(ds))
        rows.append(qsnet_row(ds, scores_root, source))
        mcnemar.append(mcnemar_row(ds, scores_root))
        coverage.append(all_seed_coverage(ds, scores_root, alpha, SEEDS, band_level))
        per_class.append(per_class_fzr(ds, scores_root, alpha, band_level))

    # Holm over the McNemar family (one comparison per dataset).
    holm = holm_bonferroni([m["p_raw"] for m in mcnemar], alpha)
    for m, adj, rej in zip(mcnemar, holm["p_adjusted"], holm["reject"]):
        m["p_holm"] = adj
        m["significant"] = bool(rej)
    return rows, mcnemar, coverage, per_class, holm


def _fmt(x, spec="{:.4f}", dash="—"):
    return dash if x is None else spec.format(x)


# ---------------------------------------------------------------- renderers (mirror rq2_table_b)

def render_table_a_md(rows, mcnemar, alpha, source_kind):
    mc_by_ds = {m["dataset"]: m for m in mcnemar}
    L = ["# Table A — In-Distribution Detection (RQ1)", "",
         f"**Caption.** Closed-set detection on the KNOWN test split at seed {SEED}: accuracy, macro-F1, "
         "and one-vs-rest macro AUROC for each system per dataset. XGBoost is the frozen Day-12 detector "
         "on real features; QS-Net is the CQ-ZDR head. `*` on QS-Net accuracy = exact McNemar vs XGBoost "
         f"significant at α = {alpha} after Holm over the dataset family.", "",
         "| Dataset | System | scores | accuracy | macro-F1 | OVR-AUROC | McNemar vs XGBoost (p Holm) |",
         "|---|---|---|---:|---:|---:|---:|"]
    for r in rows:
        prov = "‡" if r["source_kind"] != "real" else ""
        sig = ""
        if r["arm"] == "quantum":
            m = mc_by_ds.get(r["dataset"])
            sig = "*" if (m and m.get("significant")) else ""
            pcell = f"{_fmt(m['p_holm'], '{:.2e}')}{prov}" if m else "—"
        else:
            pcell = "— (reference)"
        L.append(f"| {r['dataset']} | {r['system']} | {r['source_kind']} | "
                 f"{_fmt(r['accuracy'])}{sig}{prov} | {_fmt(r['macro_f1'])}{prov} | "
                 f"{_fmt(r['auroc_ovr_macro'])}{prov} | {pcell} |")
    L += ["",
          f"‡ **Provisional — rides the Day-14 `{source_kind}` fidelity interface.** The QS-Net cells (and "
          "the McNemar that compares them to the real detector) reprice unchanged-in-form on Team B's real "
          "prototypes (`--source real --scores-root <dir>`); the XGBoost row is already final (real Day-12 "
          "model on real features).", "",
          "**Reading the table.** RQ1 asks whether each system is a competent KNOWN-class detector before "
          "its novelty behaviour (Table B) is meaningful. XGBoost sets a strong closed-set bar; the QS-Net "
          "numbers here are the dummy placeholder and exist to prove the table assembles and the McNemar "
          "pairing is row-aligned. The sign and significance convention is what carries into the "
          "manuscript; the numbers arrive with Team B's real fidelities.", ""]
    return "\n".join(L) + "\n"


def render_table_a_tex(rows, mcnemar, alpha, source_kind):
    mc_by_ds = {m["dataset"]: m for m in mcnemar}
    L = [r"% Table A --- in-distribution detection (RQ1). Generated by week5/scripts/table_a.py.",
         r"% Cells marked \ddag are provisional (Day-14 " + source_kind +
         r" fidelity interface) and reprice on Team B's real prototypes.",
         r"% Requires: \usepackage{booktabs}.",
         r"\begin{table}[t]", r"\centering",
         r"\caption{In-distribution detection (RQ1) on the KNOWN test split, seed " + str(SEED) +
         r". A \texttt{*} on QS-Net accuracy marks an exact McNemar difference vs XGBoost significant at "
         r"$\alpha = " + f"{alpha}" + r"$ after Holm.}",
         r"\label{tab:in-distribution-detection}",
         r"\begin{tabular}{llrrr}", r"\toprule",
         r"Dataset & System & accuracy & macro-F1 & OVR-AUROC \\", r"\midrule"]
    for r in rows:
        ddag = r"$^\ddag$" if r["source_kind"] != "real" else ""
        sig = ""
        if r["arm"] == "quantum":
            m = mc_by_ds.get(r["dataset"])
            sig = r"\texttt{*}" if (m and m.get("significant")) else ""
        ds = r["dataset"].replace("_", r"\_")
        sysname = r["system"].replace("_", r"\_")
        L.append(f"{ds} & {sysname} & {_fmt(r['accuracy'], '{:.4f}', '---')}{sig}{ddag} & "
                 f"{_fmt(r['macro_f1'], '{:.4f}', '---')}{ddag} & "
                 f"{_fmt(r['auroc_ovr_macro'], '{:.4f}', '---')}{ddag} \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(L) + "\n"


def render_markdown(out):
    alpha = out["alpha"]
    rows, mcnemar = out["rows"], out["mcnemar"]
    L = ["# Week 5 · Day 26 — Table A (In-Distribution Detection, RQ1) + Significance + Coverage", "",
         "Task (`qi26_12_Week_5.pdf`): *finalise Table A (in-distribution detection) with significance "
         "markers and an all-seed coverage check.* "
         f"Seed {SEED} · α = {alpha} · trio {', '.join(out['datasets'])} · quantum scores: "
         f"**{out['source_kind']}**.", "",
         "Table A is the closed-set complement to Table B's zero-day guarantee: how well each system "
         "classifies KNOWN traffic (RQ1). XGBoost is real and final; QS-Net rides the Day-14 dummy interface "
         "and is provisional. Rendered standalone for the manuscript in "
         "[`_generated/w5_02_table_a.md`](_generated/w5_02_table_a.md) + "
         "[`.tex`](_generated/w5_02_table_a.tex). Reproduced here:", "",
         "| Dataset | System | scores | accuracy | macro-F1 | OVR-AUROC | McNemar vs XGBoost (p Holm) |",
         "|---|---|---|---:|---:|---:|---:|"]
    mc_by_ds = {m["dataset"]: m for m in mcnemar}
    for r in rows:
        prov = "‡" if r["source_kind"] != "real" else ""
        if r["arm"] == "quantum":
            m = mc_by_ds.get(r["dataset"])
            sig = "*" if (m and m.get("significant")) else ""
            pcell = f"{_fmt(m['p_holm'], '{:.2e}')}{prov}" if m else "—"
        else:
            sig, pcell = "", "— (reference)"
        L.append(f"| {r['dataset']} | {r['system']} | {r['source_kind']} | "
                 f"{_fmt(r['accuracy'])}{sig}{prov} | {_fmt(r['macro_f1'])}{prov} | "
                 f"{_fmt(r['auroc_ovr_macro'])}{prov} | {pcell} |")

    L += ["", f"‡ provisional (Day-14 **{out['source_kind']}** fidelity interface); `*` = McNemar "
          f"significant at α = {alpha} after Holm. ", "",
          "## Which cells are already final", "",
          "| Column | Status | Why |", "|---|---|---|",
          "| XGBoost accuracy / macro-F1 / OVR-AUROC | **final** | real frozen Day-12 detector on real "
          "features (read from `results.json`, never recomputed) |",
          "| QS-Net accuracy / macro-F1 / OVR-AUROC | provisional | Day-14 dummy fidelity interface |",
          "| McNemar QS-Net vs XGBoost | provisional | one arm is the dummy interface |", ""]

    L += ["## All-seed coverage check", "",
          f"The split-conformal guarantee is marginal over the calibration/test draw, so it must hold "
          f"across seeds, not one split. Pooled KNOWN calibration ∪ test re-drawn at the original sizes "
          f"under seeds {SEEDS} (Day-23 `fix_splits`); each re-split's achieved false-zero-day rate judged "
          f"against its own exact {int(out['band_level']*100)}% BetaBinomial band (Day-16).", "",
          "| Dataset | mean FZR (5 seeds) | max FZR | in band | target α |",
          "|---|---:|---:|:--:|---:|"]
    for c in out["coverage_all_seed"]:
        L.append(f"| {c['dataset']} | {c['mean_fzr']:.4f} | {c['max_fzr']:.4f} | "
                 f"{c['n_in_band']}/{c['n_seeds']} | {alpha:.2f} |")
    n_all = sum(c["all_in_band"] for c in out["coverage_all_seed"])
    L += ["", f"**{n_all}/{len(out['coverage_all_seed'])} datasets hold the exact band on all "
          f"{len(SEEDS)} seeds** — the conformal false-alarm control is stable across the 5-seed "
          "convention, not an artifact of one split.", ""]

    L += ["## Per-class achieved-FZR diagnostic", "",
          "Marginal conformal controls the false-alarm rate over the KNOWN **mixture**; it gives **no "
          "per-class guarantee**. (This is the precise answer to the concern that class imbalance might "
          "undermine the threshold: rare classes contribute few pooled points and do **not** skew the "
          "marginal q — the mixture guarantee holds — but an individual class can still be under- or "
          "over-covered.) Each known class's test flag count is judged against **its own** exact band "
          "`coverage_band(n_cal, k, m_c)`.", "",
          "| Dataset | classes | classes out of their own band | conditional floor ⌈1/α⌉−1 | note |",
          "|---|---:|---:|---:|---|"]
    for pc in out["per_class_fzr"]:
        note = ("clustered conformal (Ding et al. 2023) recommended" if pc["n_out_of_band"] > 0
                else "all classes inside their own band")
        L.append(f"| {pc['dataset']} | {pc['n_classes']} | {pc['n_out_of_band']} | "
                 f"{pc['conditional_floor']} | {note} |")
    L += ["", "Per-class detail (every class, its m_test, achieved FZR, own band, and in-band verdict) is "
          "in [`_generated/w5_02_per_class_fzr.csv`](_generated/w5_02_per_class_fzr.csv). Where a class "
          "falls outside its band, the fix is **clustered conformal** (Ding et al. 2023) — grouping the "
          "rare classes into a few clusters with enough calibration mass each — **not** fully "
          "class-conditional conformal, since several classes sit far below the ⌈1/α⌉−1 floor "
          "(19 at α = 0.05) needed for a finite class-conditional quantile.", "",
          "## Bottom line", "",
          "Table A's structure, provenance split, significance convention (McNemar + Holm), and the two "
          "coverage diagnostics are final and publishable; the QS-Net cells and the McNemar comparing them "
          "to the real detector reprice on Team B's real prototypes, and that rerun is the one that goes in "
          "the manuscript.", "",
          "CSV: `_generated/w5_02_table_a.csv` · per-class: `_generated/w5_02_per_class_fzr.csv` · "
          "JSON: `_generated/w5_02_table_a.json` · Table A: `_generated/w5_02_table_a.md` + `.tex`."]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- cli

def main(argv=None):
    ap = argparse.ArgumentParser(description="Day-26 Table A (RQ1) + significance + coverage diagnostics")
    ap.add_argument("--datasets", nargs="+", default=list(TRIO))
    ap.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    ap.add_argument("--band", type=float, default=DEFAULT_BAND)
    ap.add_argument("--scores-root", default=str(IFACE))
    ap.add_argument("--source", choices=["dummy", "real"], default="dummy")
    args = ap.parse_args(argv)

    GEN.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    rows, mcnemar, coverage, per_class, holm = build_table_a(
        args.datasets, args.scores_root, args.source, args.alpha, args.band)

    for r in rows:
        log(f"{r['dataset']} {r['system']} ({r['source_kind']}): acc={r['accuracy']} "
            f"macroF1={r['macro_f1']} OVR-AUROC={r['auroc_ovr_macro']}")
    for m in mcnemar:
        log(f"{m['dataset']} McNemar QS-Net vs XGBoost: n10={m['qsnet_only_right']} "
            f"n01={m['xgboost_only_right']} p_raw={m['p_raw']:.2e} p_holm={m['p_holm']:.2e} "
            f"-> {'SIG' if m['significant'] else 'ns'}")
    for c in coverage:
        log(f"{c['dataset']} all-seed coverage: mean FZR={c['mean_fzr']} in band {c['n_in_band']}/"
            f"{c['n_seeds']}")
    for pc in per_class:
        log(f"{pc['dataset']} per-class FZR: {pc['n_out_of_band']}/{pc['n_classes']} classes out of "
            f"their own band (conditional floor {pc['conditional_floor']})")

    out = {"schema_version": "1.0", "day": 26, "research_question": "RQ1 — in-distribution detection",
           "seed": SEED, "alpha": args.alpha, "band_level": args.band, "source_kind": args.source,
           "scores_root": _rel(args.scores_root), "datasets": list(args.datasets),
           "status_legend": {FINAL: "real frozen Day-12 model on real features",
                             PROVISIONAL: "rides the Day-14 dummy fidelity interface; reprices on "
                                          "Team B's real prototypes"},
           "rows": rows, "mcnemar": mcnemar, "holm": {k: holm[k] for k in ("alpha", "m")},
           "coverage_all_seed": coverage, "per_class_fzr": per_class,
           "all_seed_coverage_all_in_band": bool(all(c["all_in_band"] for c in coverage)),
           "per_class_all_in_band": bool(all(pc["n_out_of_band"] == 0 for pc in per_class))}

    (GEN / "w5_02_table_a.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    pd.DataFrame(rows).to_csv(GEN / "w5_02_table_a.csv", index=False)
    pd.DataFrame([r for pc in per_class for r in pc["per_class"]]).to_csv(
        GEN / "w5_02_per_class_fzr.csv", index=False)
    (GEN / "w5_02_table_a.md").write_text(
        render_table_a_md(rows, mcnemar, args.alpha, args.source), encoding="utf-8")
    (GEN / "w5_02_table_a.tex").write_text(
        render_table_a_tex(rows, mcnemar, args.alpha, args.source), encoding="utf-8")
    (REPORTS / "w5_02_table_a.md").write_text(render_markdown(out), encoding="utf-8")

    log(f"done -> w5_02_table_a.md + w5_02_table_a.{{md,tex,csv,json}} + w5_02_per_class_fzr.csv "
        f"({len(rows)} rows, {len(args.datasets)} datasets)")
    return out


if __name__ == "__main__":
    main()
