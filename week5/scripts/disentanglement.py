#!/usr/bin/env python3
"""
Week 5 · Day 26 (Team A) — disentanglement experiment support (RQ3): separation AUROC.

Task (`qi26_12_Week_5.pdf`): *Support the disentanglement experiment — supply adversarial-known vs
true-zero-day labels + scoring, and compute the separation AUROC.* Team A owns the labels + the scoring
rule; Team B runs the full integration on its Day 26 and hands over the real separation scores, which drop
into this module unchanged via `--source real`.

RQ3 — what "disentanglement" asks
---------------------------------
The Day-15 novelty score  s(x) = 1 − max_c F(ρ_x, ρ_c)  (higher ⇒ farther from every KNOWN prototype ⇒
more novel) is the object the whole detector is built on. RQ3 asks whether that *one* score can tell apart
two things that both look "far from the known prototypes":

  * a **true zero-day** — traffic from a genuinely held-out attack family (should score high, correctly), and
  * an **adversarially-perturbed KNOWN** attack — a known class pushed by an FGSM/PGD budget ε until it too
    lands far from its own prototype (scores high, but is NOT novel — it is a known class in disguise).

A detector that flags novelty well can still be *fooled* by adversarial-known traffic. So the headline is the
**separation AUROC**: with **true-zero-day as the POSITIVE class and adversarial-known as the NEGATIVE class**,
AUROC = P(s(zero-day) > s(adv-known)). 1.0 ⇒ the score cleanly separates real novelty from disguised-known;
0.5 ⇒ the score cannot disentangle them at all. Proposition 2 gives a separable budget ε*: below ε* the two
stay separable (AUROC ≈ 1), and past it AUROC decays toward 0.5.

Reported as a 3-way panel so the story is legible (Hendrycks & Gimpel 2017; Lee et al. 2018):
  separation        true-zero-day (+) vs adversarial-known (−)   — the RQ3 headline
  zeroday_vs_clean  true-zero-day (+) vs clean-known (−)         — is novelty detectable at all?
  adv_vs_clean      adversarial-known (+) vs clean-known (−)     — does adv-known ALSO look novel?
If both zeroday_vs_clean and adv_vs_clean are high but separation is ≈ 0.5, the score detects novelty yet is
fully fooled by adversarial-known — the precise failure RQ3 exists to measure.

AUROC = Mann–Whitney U / (n_pos · n_neg) (ties counted at ½, so it is the exact rank-AUC); 95% CI by a
seed-42 stratified bootstrap over the two populations.

Dummy stand-in (PROVISIONAL — Team B's real adversarial scores are not in yet)
-----------------------------------------------------------------------------
Team B's real FGSM/PGD separation scores are not delivered, so on the Day-14 interface:
  clean_known  ← the KNOWN test nonconformity  (low s)
  true_zeroday ← one seeded half of the held-out zero-day nonconformity  (high s)
  adv_known    ← the OTHER seeded half of the zero-day pool  (an independent draw from the SAME
                 distribution ⇒ separation AUROC ≈ 0.5 BY CONSTRUCTION)
This is a deliberate honest null, NOT a synthesised easy separation: with no real adversarial scores the
placeholder makes adv-known and true-novel indistinguishable, so the headline reads ≈ 0.5 and cannot be
mistaken for a result. It also exercises the exact code path the real scores will run — `zeroday_vs_clean`
and `adv_vs_clean` both come out high, which is the shape the real experiment should refine. Every AUROC is
tagged `provisional` and reprices on real scores with no code change.

Real interface (Team B swaps in at the SAME schema — no code change)
--------------------------------------------------------------------
`<scores-root>/<name>/rq3_scores.parquet`: one row per RQ3 sample, columns
  role ∈ {clean_known, adv_known, true_zeroday},  sample_id,  fid__<class>  (non-squared Uhlmann F).
Run with `--source real --scores-root <team-B dir>`; s is recomputed as 1 − max_c F from the fid__ columns
(identical rule to Day 15), so the fidelity convention is enforced here too.

Report: week5/reports/w5_01_disentanglement.md
JSON/CSV: week5/reports/_generated/w5_01_disentanglement.{json,csv}
Run (venv): python week5/scripts/disentanglement.py --datasets CICIoT2023 BoT-IoT UNSW-NB15 --alpha 0.05
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

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week3" / "scripts"))

from conformal_calibrate import (  # noqa: E402  (Day-15 module — single source of the score rule + io)
    IFACE, TRIO, known_classes, load_scores, nonconformity_from_fidelities,
)

GEN = BASE / "week5" / "reports" / "_generated"
REPORTS = BASE / "week5" / "reports"

SEED = 42
DEFAULT_ALPHA = 0.05
N_BOOT = 2000
CI_LEVEL = 0.95
ROLES = ("clean_known", "adv_known", "true_zeroday")

# The 3-way panel: (name, positive role, negative role). Positive = the class that SHOULD score higher.
PANELS = (
    ("separation", "true_zeroday", "adv_known"),        # RQ3 headline
    ("zeroday_vs_clean", "true_zeroday", "clean_known"),
    ("adv_vs_clean", "adv_known", "clean_known"),
)


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def _rel(p):
    """Repo-relative path for committed outputs (an absolute path would leak the author's home dir)."""
    p = Path(p)
    try:
        return p.resolve().relative_to(BASE).as_posix()
    except ValueError:
        return str(p)


# ---------------------------------------------------------------- AUROC (rank / Mann-Whitney)

def auroc(pos, neg):
    """AUROC = P(s_pos > s_neg) + ½P(=) = U / (n_pos·n_neg), via Mann–Whitney U (exact tie handling)."""
    pos = np.asarray(pos, dtype=float)
    neg = np.asarray(neg, dtype=float)
    if pos.size == 0 or neg.size == 0:
        return None
    u = stats.mannwhitneyu(pos, neg, alternative="two-sided").statistic
    return float(u / (pos.size * neg.size))


def auroc_bootstrap_ci(pos, neg, n_boot=N_BOOT, level=CI_LEVEL, seed=SEED):
    """Stratified (per-population) bootstrap CI for the AUROC. Seed 42 → reproducible band."""
    pos = np.asarray(pos, dtype=float)
    neg = np.asarray(neg, dtype=float)
    if pos.size == 0 or neg.size == 0:
        return None, None
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        p = pos[rng.integers(0, pos.size, pos.size)]
        q = neg[rng.integers(0, neg.size, neg.size)]
        boot[i] = auroc(p, q)
    tail = (1.0 - level) / 2.0
    lo, hi = np.quantile(boot, [tail, 1.0 - tail])
    return float(lo), float(hi)


# ---------------------------------------------------------------- role scores (dummy + real)

def _role_scores_dummy(dataset, scores_root, seed=SEED):
    """Build the three role populations from the Day-14 interface (PROVISIONAL placeholder).

    clean_known  = KNOWN test s;  the zero-day pool is split into two independent halves (seed 42) to
    stand in for true_zeroday and adv_known — same distribution ⇒ separation AUROC ≈ 0.5 (honest null).
    """
    frames = load_scores(dataset, scores_root)
    known = known_classes(frames)
    s_test = nonconformity_from_fidelities(frames["test"], known)
    s_zd = nonconformity_from_fidelities(frames["zeroday"], known)

    rng = np.random.default_rng(seed)
    perm = rng.permutation(s_zd.size)
    half = s_zd.size // 2
    return {
        "clean_known": s_test,
        "true_zeroday": s_zd[perm[:half]],
        "adv_known": s_zd[perm[half:2 * half]],
    }


def _role_scores_real(dataset, scores_root):
    """Team B's real RQ3 scores: one parquet with a `role` column + fid__<class> (non-squared F)."""
    f = Path(scores_root) / dataset / "rq3_scores.parquet"
    if not f.exists():
        raise FileNotFoundError(
            f"real RQ3 scores not found: {f}\n"
            f"  -> Team B emits <scores-root>/{dataset}/rq3_scores.parquet with columns "
            f"role in {ROLES}, sample_id, fid__<class> (non-squared Uhlmann F)."
        )
    df = pd.read_parquet(f)
    if "role" not in df.columns:
        raise ValueError(f"{f}: missing required `role` column (values in {ROLES})")
    known = [c[len("fid__"):] for c in df.columns if c.startswith("fid__")]
    out = {}
    for role in ROLES:
        sub = df[df["role"] == role]
        if sub.empty:
            raise ValueError(f"{f}: role '{role}' has no rows")
        out[role] = nonconformity_from_fidelities(sub, known)
    return out


def role_scores(dataset, scores_root, source):
    return _role_scores_real(dataset, scores_root) if source == "real" \
        else _role_scores_dummy(dataset, scores_root)


# ---------------------------------------------------------------- per-dataset disentanglement

def disentangle_dataset(dataset, scores_root, source, n_boot=N_BOOT, level=CI_LEVEL):
    scores = role_scores(dataset, scores_root, source)
    n_by_role = {r: int(np.asarray(scores[r]).size) for r in ROLES}
    mean_by_role = {r: round(float(np.mean(scores[r])), 6) for r in ROLES}

    panels = []
    for name, pos_role, neg_role in PANELS:
        a = auroc(scores[pos_role], scores[neg_role])
        lo, hi = auroc_bootstrap_ci(scores[pos_role], scores[neg_role], n_boot, level)
        panels.append({
            "panel": name, "positive": pos_role, "negative": neg_role,
            "n_pos": n_by_role[pos_role], "n_neg": n_by_role[neg_role],
            "auroc": None if a is None else round(a, 4),
            "ci95_low": None if lo is None else round(lo, 4),
            "ci95_high": None if hi is None else round(hi, 4),
        })
    return {"dataset": dataset, "source_kind": source, "n_by_role": n_by_role,
            "mean_score_by_role": mean_by_role, "panels": panels}


# ---------------------------------------------------------------- report

def render_markdown(out):
    src = out["source_kind"]
    prov = "‡" if src == "dummy" else ""
    L = ["# Week 5 · Day 26 — Disentanglement (RQ3): Separation AUROC", "",
         "Task (`qi26_12_Week_5.pdf`): *support the disentanglement experiment — supply adversarial-known "
         "vs true-zero-day labels + scoring, compute the **separation AUROC**.* Team A owns the labels and "
         "the scoring rule; Team B runs the full integration and hands over the real separation scores.", "",
         f"Score: the Day-15 novelty score **s = 1 − max_c F(ρ_x, ρ_c)** (higher ⇒ more novel). Seed "
         f"{SEED} · scores: **{src}** · AUROC = Mann–Whitney U / (n₊·n₋) · {int(CI_LEVEL*100)}% CI = "
         f"seed-{SEED} stratified bootstrap ({out['n_boot']} resamples).", "",
         "**Separation AUROC** = P(s(true-zero-day) > s(adversarial-known)) — true-zero-day is the "
         "POSITIVE class. 1.0 ⇒ the novelty score cleanly separates genuine novelty from adversarially-"
         "disguised known attacks; 0.5 ⇒ it cannot disentangle them (Proposition 2's separable budget ε\\*: "
         "below ε\\* the two stay separable, past it AUROC decays to 0.5).", ""]

    for ds in out["datasets"]:
        d = out["results"][ds]
        L += [f"## {ds}", "",
              "| Panel | positive | negative | n₊ | n₋ | **AUROC** | "
              f"{int(CI_LEVEL*100)}% CI |", "|---|---|---|---:|---:|---:|---|"]
        for p in d["panels"]:
            ci = "—" if p["ci95_low"] is None else f"[{p['ci95_low']:.4f}, {p['ci95_high']:.4f}]"
            head = "**separation**" if p["panel"] == "separation" else p["panel"]
            au = "—" if p["auroc"] is None else f"{p['auroc']:.4f}"
            L.append(f"| {head} | {p['positive']} | {p['negative']} | {p['n_pos']:,} | {p['n_neg']:,} | "
                     f"**{au}**{prov if p['panel']=='separation' else ''} | {ci} |")
        mb = d["mean_score_by_role"]
        L += ["", f"mean s — clean_known {mb['clean_known']:.4f} · true_zeroday {mb['true_zeroday']:.4f} · "
              f"adv_known {mb['adv_known']:.4f}.", ""]

    if src == "dummy":
        L += ["## Reading the table (dummy interface)", "",
              "‡ **Provisional — the separation column rides the Day-14 dummy interface.** Team B's real "
              "FGSM/PGD adversarial-known scores are not in yet, so `adv_known` is a seeded second half of "
              "the zero-day pool: an independent draw from the **same** distribution as `true_zeroday`. That "
              "makes the separation AUROC ≈ 0.5 **by construction** — a deliberate honest null, not a "
              "result, and not a synthesised easy separation. It cannot be read as evidence that the score "
              "can (or cannot) truly disentangle the two.",
              "- `zeroday_vs_clean` and `adv_vs_clean` both come out high because both halves sit far from "
              "the KNOWN prototypes — which is exactly *why* separation is the hard question: two "
              "populations that each look novel against clean traffic need not be separable from each "
              "other.",
              "- The identical command reprices every cell the moment Team B ships "
              "`rq3_scores.parquet` (`--source real --scores-root <dir>`); only the separation row is then a "
              "genuine RQ3 result.", ""]
    else:
        L += ["## Reading the table (real scores)", "",
              "Separation AUROC is now a genuine RQ3 result: it measures how well the novelty score alone "
              "tells true zero-day from adversarially-disguised known traffic. Compare against ε\\* "
              "(Proposition 2) — a separation AUROC that collapses toward 0.5 as the adversarial budget "
              "grows is the empirical signature of the separable-budget threshold.", ""]

    L += ["## What Team A supplies vs what Team B supplies", "",
          "- **Team A (this module):** the labels (role ∈ {clean_known, adv_known, true_zeroday}), the "
          "scoring rule (s = 1 − max_c F), the AUROC + bootstrap-CI machinery, and the 3-way panel.",
          "- **Team B (Day 26):** the real per-sample fidelities behind each role — in particular the "
          "adversarially-perturbed known attacks (FGSM/PGD at budget ε) that populate `adv_known`.", "",
          f"CSV: `_generated/w5_01_disentanglement.csv` · JSON: `_generated/w5_01_disentanglement.json`."]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- cli

def main(argv=None):
    ap = argparse.ArgumentParser(description="Day-26 disentanglement (RQ3) — separation AUROC")
    ap.add_argument("--datasets", nargs="+", default=list(TRIO))
    ap.add_argument("--alpha", type=float, default=DEFAULT_ALPHA,
                    help="carried for provenance; AUROC is threshold-free")
    ap.add_argument("--scores-root", default=str(IFACE))
    ap.add_argument("--source", choices=["dummy", "real"], default="dummy")
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--ci-level", type=float, default=CI_LEVEL)
    args = ap.parse_args(argv)

    GEN.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    results, flat = {}, []
    for ds in args.datasets:
        r = disentangle_dataset(ds, args.scores_root, args.source, args.n_boot, args.ci_level)
        results[ds] = r
        sep = next(p for p in r["panels"] if p["panel"] == "separation")
        log(f"{ds}  separation AUROC={sep['auroc']} CI=[{sep['ci95_low']}, {sep['ci95_high']}]  "
            f"(zeroday_vs_clean={next(p['auroc'] for p in r['panels'] if p['panel']=='zeroday_vs_clean')}, "
            f"adv_vs_clean={next(p['auroc'] for p in r['panels'] if p['panel']=='adv_vs_clean')})")
        for p in r["panels"]:
            flat.append({"dataset": ds, "source_kind": args.source, **p})

    out = {"schema_version": "1.0", "day": 26, "research_question": "RQ3 — disentanglement",
           "seed": SEED, "alpha": args.alpha, "source_kind": args.source,
           "scores_root": _rel(args.scores_root), "n_boot": args.n_boot,
           "ci_level": args.ci_level, "score_def": "s = 1 - max_c F(rho_x, rho_c)",
           "separation_def": "AUROC(true_zeroday POSITIVE vs adv_known NEGATIVE)",
           "datasets": list(args.datasets), "results": results}

    (GEN / "w5_01_disentanglement.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    pd.DataFrame(flat).to_csv(GEN / "w5_01_disentanglement.csv", index=False)
    (REPORTS / "w5_01_disentanglement.md").write_text(render_markdown(out), encoding="utf-8")
    log(f"done -> w5_01_disentanglement.md/.csv/.json ({len(flat)} panels across "
        f"{len(args.datasets)} datasets)")
    return out


if __name__ == "__main__":
    main()
