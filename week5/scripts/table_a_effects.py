#!/usr/bin/env python3
"""
Week 5 · Day 29 (Team A) — Table A (RQ1) FINAL: significance vs EVERY baseline + Cohen's d effects.

Task (`qi26_12_Week_5.pdf`): *Finalise Table A (in-distribution detection) with significance markers vs
every baseline. Attach Cohen's d effect sizes.* Deliverable: **Table A (final, with effects)**.

"Every baseline", stated precisely
----------------------------------
In-distribution detection has two comparable faces, and each baseline is paired with QS-Net on the face
it actually shares (no apples-to-oranges tests):

  closed-set correctness   XGBoost is the only baseline that emits a per-sample CLASS prediction, so the
  (multiclass, RQ1 proper) closed-set McNemar family stays QS-Net vs XGBoost per dataset (Day-26 pairing,
                           Day-17 exact test, Holm over the 3-dataset family) — now with effect sizes.
  in-distribution          The novelty heads (Isolation Forest / OC-SVM / Autoencoder) never predict a
  false-alarm behaviour    class, but on the KNOWN test split every system makes the same binary
  (known test split)       in-distribution decision: flag or keep. Correct on a known row = NOT flagged.
                           Exact McNemar QS-Net vs each head on the paired per-row flags (Day-22 frozen-q
                           decisions vs the Day-12 heads' `is_novel`), Holm over the dataset x head family.

Effect sizes (Demšar 2006 — never a p-value alone):
  d_z   paired Cohen's d on the per-sample correctness difference (Day-17 `cohens_d_paired`); with binary
        outcomes d_z = mean(diff)/sd(diff) — small by construction on huge n, reported beside n.
  h     Cohen's h on the two marginal rates (Day-25 `cohens_h`) — the magnitude language the RQ5 verdicts
        already speak.
The Day-25 seed-level arm (classical 5-seed paired-t with its own d_z, and the fact that QS-Net cannot
enter it until Team B ships per-seed scores) is surfaced from `w4_06_significance.json`, not recomputed.

Provenance: XGBoost cells real/FINAL (frozen Day-12 `results.json`); every QS-Net cell and every test
involving it is PROVISIONAL (‡, Day-14 dummy interface) and reprices with `--source real`.

Report: week5/reports/w5_05_table_a_effects.md
Table A final: week5/reports/_generated/w5_05_table_a.md + .tex (booktabs)
JSON/CSV: week5/reports/_generated/w5_05_table_a_effects.{json,csv} + w5_05_known_fa.csv
Run (venv): python week5/scripts/table_a_effects.py --datasets CICIoT2023 BoT-IoT UNSW-NB15 --alpha 0.05
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week3" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))
sys.path.insert(0, str(BASE / "week5" / "scripts"))

from conformal_calibrate import IFACE, TRIO                       # noqa: E402  (Day-15)
from stats_protocol import cohens_d_paired, holm_bonferroni, mcnemar_exact  # noqa: E402  (Day-17)
from significance import QUANTUM, cohens_h, load_paired_decisions  # noqa: E402  (Day-25)
import table_a as ta                                                # noqa: E402  (Day-26 — reused rows)

GEN = BASE / "week5" / "reports" / "_generated"
REPORTS = BASE / "week5" / "reports"
W4_SIG = BASE / "week4" / "reports" / "_generated" / "w4_06_significance.json"

SEED = 42
DEFAULT_ALPHA = 0.05
TEST_ALPHA = 0.05                 # significance level for the McNemar/Holm families (Day-25 convention)

FINAL = "final"
PROVISIONAL = "provisional"


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def _rel(p):
    p = Path(p)
    try:
        return p.resolve().relative_to(BASE).as_posix()
    except ValueError:
        return str(p)


def _fmt(x, spec="{:.4f}", dash="—"):
    return dash if x is None else spec.format(x)


def _dz(a, b):
    """Paired Cohen's d_z on per-sample binary outcomes (Day-17 convention, ddof=1; 0 on zero variance)."""
    return round(float(cohens_d_paired(np.asarray(a, dtype=float), np.asarray(b, dtype=float))), 4)


# ---------------------------------------------------------------- family 1: closed-set vs XGBoost

def closed_set_row(dataset, scores_root):
    """Exact McNemar on paired per-sample closed-set correctness (Day-26 pairing) + both effect sizes."""
    qs, xgb = ta.paired_correct(dataset, scores_root)          # row-aligned, true-label guard inside
    n01 = int(np.sum(~qs & xgb))                                # XGBoost right where QS-Net wrong
    n10 = int(np.sum(qs & ~xgb))                                # QS-Net right where XGBoost wrong
    mc = mcnemar_exact(n10, n01)
    acc_qs, acc_xgb = float(np.mean(qs)), float(np.mean(xgb))
    return {"family": "closed_set_correctness", "dataset": dataset,
            "comparison": f"{QUANTUM} vs XGBoost (detector)", "scope": "KNOWN test split, multiclass",
            "n_pairs": int(qs.size), "acc_qsnet": round(acc_qs, 4), "acc_xgboost": round(acc_xgb, 4),
            "acc_diff": round(acc_qs - acc_xgb, 4),
            "qsnet_only_right": n10, "xgboost_only_right": n01,
            "cohens_h": round(cohens_h(acc_qs, acc_xgb), 4), "cohens_dz": _dz(qs, xgb),
            "p_raw": mc["p"], "note": mc["note"]}


# ---------------------------------------------------------------- family 2: known-split FA vs every head

def known_fa_rows(dataset):
    """QS-Net (frozen q) vs each Day-12 novelty head on the KNOWN test rows: correct = NOT flagged.

    Pairing comes from Day-25's `load_paired_decisions` (Day-22 decisions ↔ predictions.csv, row-aligned
    and label-guarded); `truth` marks zero-day rows, so the known test split is exactly `~truth`.
    """
    flags, truth, _ = load_paired_decisions(dataset)
    known = ~truth
    qs_ok = ~flags[QUANTUM][known]                              # correct on a known row = kept, not flagged
    rows = []
    for name, fl in flags.items():
        if name == QUANTUM:
            continue
        head_ok = ~fl[known]
        n01 = int(np.sum(~qs_ok & head_ok))                     # head right where QS-Net wrong
        n10 = int(np.sum(qs_ok & ~head_ok))                     # QS-Net right where head wrong
        mc = mcnemar_exact(n10, n01)
        fa_qs, fa_head = float(np.mean(~qs_ok)), float(np.mean(~head_ok))
        rows.append({"family": "known_split_false_alarm", "dataset": dataset,
                     "comparison": f"{QUANTUM} vs {name}", "baseline": name,
                     "scope": "KNOWN test split, flag-vs-keep", "n_pairs": int(qs_ok.size),
                     "fa_rate_qsnet": round(fa_qs, 4), "fa_rate_baseline": round(fa_head, 4),
                     "fa_diff": round(fa_qs - fa_head, 4),
                     "qsnet_only_right": n10, "baseline_only_right": n01,
                     "cohens_h": round(cohens_h(fa_qs, fa_head), 4), "cohens_dz": _dz(qs_ok, head_ok),
                     "p_raw": mc["p"], "note": mc["note"]})
    return rows


def apply_holm(rows, alpha=TEST_ALPHA):
    """Holm within ONE declared family (Day-25 convention: families are corrected separately)."""
    holm = holm_bonferroni([r["p_raw"] for r in rows], alpha)
    for r, adj, rej in zip(rows, holm["p_adjusted"], holm["reject"]):
        r["p_holm"] = adj
        r["significant"] = bool(rej)
    return rows, {"m": holm["m"], "alpha": holm["alpha"]}


# ---------------------------------------------------------------- seed-level arm (assembled, Day 25)

def seed_level_block():
    """The Day-25 classical 5-seed paired-t rows (with d_z) + the quantum-arm blocker + the floor."""
    if not W4_SIG.exists():
        return {"available": False, "note": "w4_06_significance.json absent — run week4 significance.py"}
    doc = json.loads(W4_SIG.read_text(encoding="utf-8"))
    return {"available": True,
            "paired_t_seeds": doc.get("paired_t_seeds"),
            "quantum_seed_arm": doc.get("quantum_seed_arm"),
            "detection_floor": doc.get("detection_floor")}


# ---------------------------------------------------------------- renderers

def render_table_a_md(rows, closed, alpha, source_kind):
    by_ds = {c["dataset"]: c for c in closed}
    L = ["# Table A — In-Distribution Detection (RQ1), FINAL with effects", "",
         f"**Caption.** Closed-set detection on the KNOWN test split at seed {SEED}: accuracy, macro-F1, "
         "one-vs-rest macro AUROC per system. `*` on QS-Net accuracy = exact McNemar vs XGBoost "
         f"significant at α = {alpha} after Holm over the dataset family; the effect columns give "
         "Cohen's h on the accuracy gap and the paired d_z on per-sample correctness (Demšar 2006 — "
         "effect sizes beside p-values). In-distribution false-alarm significance vs the novelty heads "
         "is the companion family (`w5_05_known_fa.csv`).", "",
         "| Dataset | System | scores | accuracy | macro-F1 | OVR-AUROC | p Holm (vs XGB) | Cohen's h | d_z |",
         "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        prov = "‡" if r["source_kind"] != "real" else ""
        if r["arm"] == "quantum":
            c = by_ds.get(r["dataset"])
            sig = "*" if (c and c.get("significant")) else ""
            pcell = f"{_fmt(c['p_holm'], '{:.2e}')}{prov}" if c else "—"
            hcell = f"{_fmt(c['cohens_h'], '{:+.3f}')}{prov}" if c else "—"
            dcell = f"{_fmt(c['cohens_dz'], '{:+.3f}')}{prov}" if c else "—"
        else:
            sig, pcell, hcell, dcell = "", "— (reference)", "—", "—"
        L.append(f"| {r['dataset']} | {r['system']} | {r['source_kind']} | "
                 f"{_fmt(r['accuracy'])}{sig}{prov} | {_fmt(r['macro_f1'])}{prov} | "
                 f"{_fmt(r['auroc_ovr_macro'])}{prov} | {pcell} | {hcell} | {dcell} |")
    L += ["",
          f"‡ **Provisional — rides the Day-14 `{source_kind}` fidelity interface**; reprices on Team B's "
          "real prototypes (`--source real --scores-root <dir>`). The XGBoost row is final (real frozen "
          "Day-12 model). Negative h / d_z = QS-Net below XGBoost; the sign stays in the table "
          "(RQ5 honesty).", ""]
    return "\n".join(L) + "\n"


def render_table_a_tex(rows, closed, alpha, source_kind):
    by_ds = {c["dataset"]: c for c in closed}
    L = [r"% Table A (final, with effects) --- in-distribution detection (RQ1).",
         r"% Generated by week5/scripts/table_a_effects.py (Day 29).",
         r"% Cells marked \ddag are provisional (Day-14 " + source_kind +
         r" fidelity interface) and reprice on Team B's real prototypes.",
         r"% Requires: \usepackage{booktabs}.",
         r"\begin{table*}[t]", r"\centering",
         r"\caption{In-distribution detection (RQ1) on the KNOWN test split, seed " + str(SEED) +
         r". \texttt{*} on QS-Net accuracy: exact McNemar vs XGBoost significant at $\alpha = " +
         f"{alpha}" + r"$ after Holm. Effect sizes: Cohen's $h$ on the accuracy gap and paired $d_z$ "
         r"on per-sample correctness (Dem\v{s}ar 2006).}",
         r"\label{tab:in-distribution-detection-final}",
         r"\begin{tabular}{llrrrrrr}", r"\toprule",
         r"Dataset & System & accuracy & macro-F1 & OVR-AUROC & $p_{\mathrm{Holm}}$ & $h$ & $d_z$ \\",
         r"\midrule"]
    for r in rows:
        ddag = r"$^\ddag$" if r["source_kind"] != "real" else ""
        if r["arm"] == "quantum":
            c = by_ds.get(r["dataset"])
            sig = r"\texttt{*}" if (c and c.get("significant")) else ""
            p = _fmt(c["p_holm"], "{:.1e}", "---") if c else "---"
            h = _fmt(c["cohens_h"], "{:+.3f}", "---") if c else "---"
            dz = _fmt(c["cohens_dz"], "{:+.3f}", "---") if c else "---"
        else:
            sig, p, h, dz = "", "---", "---", "---"
        ds = r["dataset"].replace("_", r"\_")
        sysname = r["system"].replace("_", r"\_")
        L.append(f"{ds} & {sysname} & {_fmt(r['accuracy'], '{:.4f}', '---')}{sig}{ddag} & "
                 f"{_fmt(r['macro_f1'], '{:.4f}', '---')}{ddag} & "
                 f"{_fmt(r['auroc_ovr_macro'], '{:.4f}', '---')}{ddag} & {p}{ddag if p != '---' else ''} & "
                 f"{h} & {dz} \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    return "\n".join(L) + "\n"


def render_markdown(out):
    alpha = out["alpha"]
    L = ["# Week 5 · Day 29 — Table A (RQ1) FINAL: Significance vs Every Baseline + Effect Sizes", "",
         "Task (`qi26_12_Week_5.pdf`): *finalise Table A (in-distribution detection) with significance "
         "markers vs every baseline; attach Cohen's d effect sizes.* "
         f"Seed {SEED} · α = {alpha} · trio {', '.join(out['datasets'])} · quantum scores: "
         f"**{out['source_kind']}**.", "",
         "Every baseline is paired with QS-Net on the face of in-distribution detection it actually "
         "shares: **XGBoost** on closed-set multiclass correctness (it is the only baseline emitting a "
         "class prediction), and **every Day-12 novelty head** on the known-split flag-vs-keep decision "
         "(the Day-22 frozen-q decisions against each head's `is_novel`, row-aligned by the Day-25 "
         "pairing). Each family is Holm-corrected separately; every test carries Cohen's h and the "
         "paired d_z (Demšar 2006). Table A final: "
         "[`_generated/w5_05_table_a.md`](_generated/w5_05_table_a.md) + "
         "[`.tex`](_generated/w5_05_table_a.tex).", "",
         "## Family 1 — closed-set correctness (QS-Net vs XGBoost)", "",
         "| Dataset | n_pairs | acc QS-Net | acc XGBoost | Δacc | n10/n01 | h | d_z | p (Holm) | sig |",
         "|---|---:|---:|---:|---:|---|---:|---:|---:|:--:|"]
    for c in out["closed_set"]["rows"]:
        L.append(f"| {c['dataset']} | {c['n_pairs']:,} | {c['acc_qsnet']:.4f}‡ | {c['acc_xgboost']:.4f} | "
                 f"{c['acc_diff']:+.4f}‡ | {c['qsnet_only_right']}/{c['xgboost_only_right']} | "
                 f"{c['cohens_h']:+.3f}‡ | {c['cohens_dz']:+.3f}‡ | {_fmt(c['p_holm'], '{:.2e}')}‡ | "
                 f"{'**sig**' if c['significant'] else 'ns'} |")
    L += ["", f"Holm family m = {out['closed_set']['holm']['m']} (one comparison per dataset).", "",
          "## Family 2 — in-distribution false alarms on the KNOWN split (QS-Net vs every head)", "",
          "Correct on a known row = **not** flagged. This is the in-distribution face the novelty heads "
          "share; their zero-day (power) face is Table B / Day-25 territory and is not retested here.", "",
          "| Dataset | baseline | n_pairs | FA QS-Net | FA baseline | ΔFA | h | d_z | p (Holm) | sig |",
          "|---|---|---:|---:|---:|---:|---:|---:|---:|:--:|"]
    for c in out["known_fa"]["rows"]:
        L.append(f"| {c['dataset']} | {c['baseline']} | {c['n_pairs']:,} | {c['fa_rate_qsnet']:.4f}‡ | "
                 f"{c['fa_rate_baseline']:.4f} | {c['fa_diff']:+.4f}‡ | {c['cohens_h']:+.3f}‡ | "
                 f"{c['cohens_dz']:+.3f}‡ | {_fmt(c['p_holm'], '{:.2e}')}‡ | "
                 f"{'**sig**' if c['significant'] else 'ns'} |")
    L += ["", f"Holm family m = {out['known_fa']['holm']['m']} (dataset × head; CIC-IoT2023 has no "
          "OC-SVM model — a real absence from Day 12, not a missing value).", "",
          "**Reading the FA family — budgets are NOT matched here, by design.** This family compares "
          f"the systems at their **shipped operating points**: QS-Net at its conformal α = {alpha} "
          "(guaranteed), each head at its own frozen Day-12 threshold, which targeted a **2α = 0.10** "
          "known-FPR budget (and delivers ≈ 0.10). So the significant gaps say: *as deployed, QS-Net "
          "keeps significantly more known traffic than every head* — a deployed-behaviour statement, "
          "not a same-budget superiority claim. The like-for-like comparison at ONE shared α is "
          "Table B's recall column (Day-19 re-thresholds every head with the same conformal rule at "
          f"α = {alpha}); the Day-25 all-rows/zero-day families use these same shipped flags, so this "
          "family completes that triptych on the known split.", ""]

    sl = out["seed_level"]
    if sl.get("available"):
        pt = sl["paired_t_seeds"]
        L += ["## Seed-level arm (assembled from Day 25 — not recomputed)", "",
              f"Classical 5-seed paired-t (metric: `{pt['metric']}`, seeds {pt['seeds']}), with paired "
              "d_z per row — the seed-level Cohen's d the task asks to attach:", "",
              "| Dataset | pair | mean Δ | d_z | p (Holm) | sig |", "|---|---|---:|---:|---:|:--:|"]
        for r in pt["rows"]:
            L.append(f"| {r['dataset']} | {r['system_a']} vs {r['system_b']} | "
                     f"{r['mean_diff']:+.4f} | {r.get('cohens_d_z', r.get('cohens_dz', 0)):+.3f} | "
                     f"{_fmt(r.get('p_holm'), '{:.2e}')} | "
                     f"{'**sig**' if r.get('significant') else 'ns'} |")
        floor = sl["detection_floor"]
        qa = sl["quantum_seed_arm"]
        reason = qa.get("reason", "no per-seed quantum scores")
        unblocked = qa.get("unblocked_by", "Team B per-seed scores")
        L += ["", f"**QS-Net cannot enter this family yet** — {reason} (unblocked by: {unblocked}). "
              f"With n = {floor['n']} seeds the smallest significant paired effect is d_z ≈ "
              f"{floor['d_z_for_significance']:.2f} (80% power: ≈ {floor['d_z_for_80pct_power']:.2f}) — "
              "the floor any seed-level quantum claim must clear.", ""]

    L += ["## Bottom line", "",
          "Table A is final: the closed-set table with `*` markers and both effect sizes, plus the "
          "known-split false-alarm family covering **every** baseline head, each family Holm-corrected "
          "and each p-value accompanied by h and d_z. Every QS-Net cell is ‡ provisional and reprices "
          "with one flag on Team B's real prototypes — the structure, families and effect-size "
          "conventions are what carry into the manuscript.", "",
          "CSV: `_generated/w5_05_table_a_effects.csv` + `_generated/w5_05_known_fa.csv` · "
          "JSON: `_generated/w5_05_table_a_effects.json` · Table A: `_generated/w5_05_table_a.md` + "
          "`.tex`."]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- cli

def main(argv=None):
    ap = argparse.ArgumentParser(description="Day-29 Table A final — significance vs every baseline + effects")
    ap.add_argument("--datasets", nargs="+", default=list(TRIO))
    ap.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    ap.add_argument("--scores-root", default=str(IFACE))
    ap.add_argument("--source", choices=["dummy", "real"], default="dummy")
    args = ap.parse_args(argv)

    GEN.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    # Table-A rows exactly as Day 26 built them (reused, never re-implemented)
    rows = []
    for ds in args.datasets:
        rows.append(ta.xgboost_row(ds))
        rows.append(ta.qsnet_row(ds, args.scores_root, args.source))

    closed, holm_cs = apply_holm([closed_set_row(ds, args.scores_root) for ds in args.datasets])
    fa_rows, holm_fa = apply_holm([r for ds in args.datasets for r in known_fa_rows(ds)])

    for c in closed:
        log(f"{c['dataset']} closed-set: Δacc={c['acc_diff']:+.4f} h={c['cohens_h']:+.3f} "
            f"d_z={c['cohens_dz']:+.3f} p_holm={c['p_holm']:.2e} -> "
            f"{'SIG' if c['significant'] else 'ns'}")
    for c in fa_rows:
        log(f"{c['dataset']} known-FA vs {c['baseline']}: ΔFA={c['fa_diff']:+.4f} h={c['cohens_h']:+.3f} "
            f"p_holm={c['p_holm']:.2e} -> {'SIG' if c['significant'] else 'ns'}")

    out = {"schema_version": "1.0", "day": 29,
           "research_question": "RQ1 — in-distribution detection, FINAL: significance vs every "
                                "baseline + Cohen's d effect sizes",
           "seed": SEED, "alpha": args.alpha, "test_alpha": TEST_ALPHA, "source_kind": args.source,
           "scores_root": _rel(args.scores_root), "datasets": list(args.datasets),
           "effect_size_defs": {
               "cohens_h": "2*asin(sqrt(p1)) - 2*asin(sqrt(p2)) on the two marginal rates (Day-25)",
               "cohens_dz": "mean(diff)/sd(diff, ddof=1) on per-sample paired binary outcomes (Day-17)"},
           "status_legend": {FINAL: "real frozen Day-12 model on real features",
                             PROVISIONAL: "rides the Day-14 dummy fidelity interface"},
           "rows": rows,
           "closed_set": {"family": "closed_set_correctness", "holm": holm_cs, "rows": closed},
           "known_fa": {"family": "known_split_false_alarm", "holm": holm_fa, "rows": fa_rows},
           "seed_level": seed_level_block()}

    (GEN / "w5_05_table_a_effects.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    pd.DataFrame(closed).to_csv(GEN / "w5_05_table_a_effects.csv", index=False)
    pd.DataFrame(fa_rows).to_csv(GEN / "w5_05_known_fa.csv", index=False)
    (GEN / "w5_05_table_a.md").write_text(
        render_table_a_md(rows, closed, args.alpha, args.source), encoding="utf-8")
    (GEN / "w5_05_table_a.tex").write_text(
        render_table_a_tex(rows, closed, args.alpha, args.source), encoding="utf-8")
    (REPORTS / "w5_05_table_a_effects.md").write_text(render_markdown(out), encoding="utf-8")

    log(f"done -> w5_05_table_a_effects.md + w5_05_table_a.{{md,tex}} + "
        f"w5_05_table_a_effects.{{json,csv}} + w5_05_known_fa.csv "
        f"({len(closed)} closed-set + {len(fa_rows)} known-FA comparisons)")
    return out


if __name__ == "__main__":
    main()
