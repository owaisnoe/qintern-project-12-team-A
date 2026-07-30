#!/usr/bin/env python3
"""
Week 4 · Day 19 (Team A) — zero-day detection recall + quantum-vs-classical novelty comparison.

Task (`qi26_12_Week_4.pdf`): *Compute zero-day detection recall at the calibrated α (true-zero-day recall on
the held-out class). Compare against the classical Isolation-Forest / OC-SVM novelty heads.* Deliverables:
"Zero-day recall results" / "Quantum-vs-classical novelty comparison".

This is the **detection-power** side of Team A's Proposition 3 (coverage). Prop 3 §5.2: coverage controls the
false-alarm rate only — a detector that flags nothing has perfect coverage — so **coverage and recall are
reported together** here. Every system is calibrated to the SAME primary α (theory Open-item 4: one α for the
quantum detector AND the classical baselines, else the comparison is not like-for-like); the threshold rule is
the single Day-15 `conformal_threshold` (q = s_(k), k = ⌈(1−α)(n+1)⌉) for BOTH arms.

- Quantum (CQ-ZDR): recall = zero-day rejection rate at q on the Day-14 fidelity interface (DUMMY placeholder;
  reprices at Team B's real prototypes with `--source real --scores-root <dir>`).
- Classical: reload the FROZEN Day-12 IsolationForest / OC-SVM / Autoencoder models (no refit — α only sets
  the threshold) and re-threshold their novelty scores at the same α on the real partition features.
  NOTE CIC-IoT2023 has no OC-SVM head (Day-12 shipped IF+AE) — its OC-SVM row is skipped and annotated.

Report: week4/reports/w4_01_zeroday_recall.md · JSON/CSV: week4/reports/_generated/w4_01_zeroday_recall.{json,csv}
Run (venv): python week4/scripts/zeroday_recall.py --datasets CICIoT2023 BoT-IoT UNSW-NB15 --alpha 0.05 --heads isolation_forest ocsvm autoencoder
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import joblib

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week3" / "scripts"))
sys.path.insert(0, str(BASE / "week2" / "scripts"))

from conformal_calibrate import conformal_threshold, calibrate_dataset, IFACE, TRIO  # noqa: E402
from classical_baselines import (  # noqa: E402  (reuse frozen-model scorers — no refit)
    load_bundle, score_isolation_forest, ocsvm_scores, autoencoder_scores,
)

BASELINES = BASE / "week2" / "baselines"
GEN = BASE / "week4" / "reports" / "_generated"
REPORTS = BASE / "week4" / "reports"
SEED = 42
DEFAULT_ALPHA = 0.05

# head -> (frozen artifact filename, scorer(artifact, frame, features) -> novelty scores, larger = more novel)
_HEADS = {
    "isolation_forest": ("isolation_forest.joblib", score_isolation_forest),
    "ocsvm": ("ocsvm.joblib", ocsvm_scores),
    "autoencoder": ("autoencoder.joblib", autoencoder_scores),
}


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def quantum_recall(dataset, alpha, scores_root):
    """CQ-ZDR: reuse the Day-15 module — zero-day rejection rate IS the recall at the calibrated α."""
    r = calibrate_dataset(dataset, alpha, scores_root)
    return {"system": "quantum_cqzdr", "source_kind": "dummy", "n_cal": r["calibration_n"],
            "q": r["threshold_q"], "coverage": r["known_test"]["coverage"],
            "false_zeroday_rate": r["known_test"]["false_zeroday_rate"],
            "zeroday_recall": r["zeroday"]["rejection_rate"], "n_zeroday": r["zeroday"]["n"]}


def classical_head_recall(dataset, head, alpha):
    """Reload the frozen head, re-threshold at the SAME α with the SAME rule. None if the head is absent."""
    path = BASELINES / dataset / _HEADS[head][0]
    if not path.exists():
        return None
    artifact = joblib.load(path)
    scorer = _HEADS[head][1]
    b = load_bundle(dataset)
    s = {sp: np.asarray(scorer(artifact, getattr(b, sp), b.features), dtype=float)
         for sp in ("calibration", "test", "zeroday")}
    q, k, n = conformal_threshold(s["calibration"], alpha)          # identical rule to the quantum arm
    test, zd = s["test"], s["zeroday"]
    return {"system": f"classical_{head}", "source_kind": "real", "n_cal": int(n),
            "q": (None if np.isinf(q) else round(float(q), 6)),
            "coverage": round(float(np.mean(test <= q)), 4),
            "false_zeroday_rate": round(float(np.mean(test > q)), 4),
            "zeroday_recall": round(float(np.mean(zd > q)), 4), "n_zeroday": int(zd.size)}


def compare_dataset(dataset, alpha, scores_root, heads):
    rows = [quantum_recall(dataset, alpha, scores_root)]
    notes = []
    for h in heads:
        r = classical_head_recall(dataset, h, alpha)
        if r is None:
            notes.append(f"{dataset}: classical head '{h}' unavailable (Day-12 skipped) — omitted.")
        else:
            rows.append(r)
    return rows, notes


def render_markdown(results, alpha, source, all_notes):
    L = ["# Week 4 · Day 19 — Zero-Day Recall + Quantum-vs-Classical Novelty", "",
         "Task (`qi26_12_Week_4.pdf`): *zero-day detection recall at the calibrated α; compare against the "
         "classical Isolation-Forest / OC-SVM novelty heads.* All systems calibrated to the **same α = "
         f"{alpha}** with the single Day-15 rule q = s_(k), k = ⌈(1−α)(n+1)⌉ "
         "([`../../week3/scripts/conformal_calibrate.py`](../../week3/scripts/conformal_calibrate.py)); "
         "flag a point as zero-day iff its novelty score > q.", "",
         "**Coverage and recall reported together** (Proposition 3 §5.2: the conformal guarantee bounds "
         "*false alarms* only — a detector flagging nothing has perfect coverage — so detection **power** "
         "(zero-day recall) is a separate axis). Quantum = CQ-ZDR on the Day-14 fidelity interface "
         f"(**{source}** placeholder, reprices at real prototypes); classical = the **real** frozen Day-12 "
         "models re-thresholded at α. Seed 42."]
    for dataset, (rows, _) in results.items():
        L += ["", f"## {dataset}", "",
              "| System | scores | n_cal | q | known coverage | false-zero-day (≤ α) | **zero-day recall** |",
              "|---|---|---:|---:|---:|---:|---:|"]
        for r in rows:
            q = "—" if r["q"] is None else f"{r['q']:.6f}"
            L.append(f"| {r['system']} | {r['source_kind']} | {int(r['n_cal']):,} | {q} | "
                     f"{r['coverage']:.4f} | {r['false_zeroday_rate']:.4f} | **{r['zeroday_recall']:.4f}** |")
    L += ["", "## Reading the table",
          "- All systems hold coverage ≈ 1−α at the same α (that is the guarantee); what differs is **recall** "
          "— the paper's separation. Report both, never recall alone.",
          "- The **quantum** column is the Day-14 **dummy** placeholder (CIC's near-1.0 recall is a synthetic "
          "artifact seeded to the Day-9 diagnostic, not a result); the **classical** column is real. The "
          "identical command reprices the quantum arm the moment Team B lands real fidelities "
          "(`--source real --scores-root <team-B dir>`).",
          "- **CIC-IoT2023 has no OC-SVM** (Day-12 shipped Isolation-Forest + Autoencoder); its OC-SVM row is "
          "omitted, not synthesized."]
    if all_notes:
        L += ["", "### Notes"] + [f"- {n}" for n in all_notes]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Day-19 zero-day recall + quantum-vs-classical")
    ap.add_argument("--datasets", nargs="+", default=TRIO)
    ap.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    ap.add_argument("--heads", nargs="+", default=["isolation_forest", "ocsvm", "autoencoder"],
                    choices=list(_HEADS))
    ap.add_argument("--scores-root", default=str(IFACE))
    ap.add_argument("--source", choices=["dummy", "real"], default="dummy")
    args = ap.parse_args(argv)

    GEN.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    results, flat, all_notes = {}, [], []
    for ds in args.datasets:
        rows, notes = compare_dataset(ds, args.alpha, args.scores_root, args.heads)
        # tag the quantum source with the CLI --source (real path also flows here)
        rows[0]["source_kind"] = args.source
        results[ds] = (rows, notes)
        all_notes += notes
        for r in rows:
            flat.append({"dataset": ds, **r})
            log(f"{ds} {r['system']}: q={r['q']} coverage={r['coverage']} "
                f"false_zeroday={r['false_zeroday_rate']} zeroday_recall={r['zeroday_recall']}")

    import pandas as pd
    pd.DataFrame(flat).to_csv(GEN / "w4_01_zeroday_recall.csv", index=False)
    (GEN / "w4_01_zeroday_recall.json").write_text(
        json.dumps({"schema_version": "1.0", "day": 19, "alpha": args.alpha, "seed": SEED,
                    "primary_alpha_note": "same α applied to quantum + classical (theory open-item 4)",
                    "rows": flat, "notes": all_notes}, indent=1), encoding="utf-8")
    (REPORTS / "w4_01_zeroday_recall.md").write_text(
        render_markdown(results, args.alpha, args.source, all_notes), encoding="utf-8")
    log(f"done -> w4_01_zeroday_recall.md/.csv/.json ({len(flat)} rows across {len(args.datasets)} datasets)")


if __name__ == "__main__":
    main()
