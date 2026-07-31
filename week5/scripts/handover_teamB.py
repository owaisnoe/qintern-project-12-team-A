#!/usr/bin/env python3
"""
Week 5 · Day 30 (Team A) — Hand final statistics + coverage assets to Team B for manuscript assembly.

Task (`qi26_12_Week_5.pdf`): *Hand final statistics + coverage assets to Team B for manuscript
assembly.* Deliverable: **Handover to manuscript** (the audited-statistics companion is
`cross_audit.py`, which must be green before this package is cut).

What Team B receives
--------------------
One versioned, SHA-256-pinned surface — `week5/HANDOVER/` — collecting every statistic and coverage
asset the manuscript cites, each with its provenance and its FINAL/PROVISIONAL status:

  Table A (RQ1)    Day-26 skeleton + Day-29 final-with-effects (closed-set McNemar + Holm + h + d_z,
                   and the known-split false-alarm family vs every head)
  Table B (RQ2)    Day-24 skeleton + Day-28 final (achieved α vs target at the frozen q, exact bands,
                   5-seed re-split CIs for achieved α AND recall)
  Figure 2         the coverage headline (reliability diagram + its data), Day 27
  RQ3              the disentanglement AUROC panel (honest null on the dummy), Day 26
  Ablation         conformal-vs-heuristic asset (figure + booktabs table + small-n drill), Day 29
  RQ5              the honesty summary + the full Day-25 significance suite it compiles
  Coverage diag.   per-class achieved-FZR diagnostic, all-seed CIs, exchangeability audit
  Audit            the Day-30 cross-audit (every number re-derived from raw logs, all green)

The two upstream freezes (`RESULTS_FROZEN` v1.0, `INTEGRATION` v1.0) are pinned BY their manifests:
this package records their manifest hashes, so hand-off state and freeze state cannot silently diverge.

`--verify` re-hashes every pinned file (expect 0 mismatch). Repricing on real prototypes re-runs the
week-5 mains with `--source real --scores-root <dir>` and re-cuts this package as v1.1 — the schema
and the asset list do not change.

Run:     python week5/scripts/handover_teamB.py
Verify:  python week5/scripts/handover_teamB.py --verify
Report:  week5/reports/w5_08_handover.md · package: week5/HANDOVER/
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week3" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))

from conformal_calibrate import TRIO                     # noqa: E402
from freeze_integration import _rows, _sha256            # noqa: E402  (Day-21 hash/row helpers, reused)

HAND = BASE / "week5" / "HANDOVER"
REPORTS = BASE / "week5" / "reports"
VERSION = "1.0"
SEED = 42
PRIMARY_ALPHA = 0.05
MANIFEST_NAME = f"handover_manifest_v{VERSION}.json"

# deliverable -> (status, [repo-relative files])
ASSETS = {
    "Table A (RQ1) — skeleton + final with effects": ("‡ quantum cells provisional", [
        "week5/reports/_generated/w5_02_table_a.md",
        "week5/reports/_generated/w5_02_table_a.tex",
        "week5/reports/_generated/w5_02_table_a.json",
        "week5/reports/_generated/w5_02_table_a.csv",
        "week5/reports/_generated/w5_05_table_a.md",
        "week5/reports/_generated/w5_05_table_a.tex",
        "week5/reports/_generated/w5_05_table_a_effects.json",
        "week5/reports/_generated/w5_05_table_a_effects.csv",
        "week5/reports/_generated/w5_05_known_fa.csv",
    ]),
    "Table B (RQ2) — skeleton + final with 5-seed CIs": ("‡ quantum cells provisional", [
        "week4/reports/_generated/w4_05_table_b.md",
        "week4/reports/_generated/w4_05_table_b.tex",
        "week4/reports/_generated/w4_05_rq2_results.json",
        "week4/reports/_generated/w4_05_rq2_results.csv",
        "week5/reports/_generated/w5_04_table_b.md",
        "week5/reports/_generated/w5_04_table_b.tex",
        "week5/reports/_generated/w5_04_table_b.json",
        "week5/reports/_generated/w5_04_table_b.csv",
        "week5/reports/_generated/w5_04_allseed_ci.csv",
    ]),
    "Figure 2 — coverage headline": ("‡ provisional (dummy scores)", [
        "week5/reports/figures/w5_fig2_coverage.png",
        "week5/reports/_generated/w5_03_figure2.json",
        "week5/reports/_generated/w5_03_figure2_data.csv",
    ]),
    "RQ3 — disentanglement AUROC panel": ("‡ honest null on dummy; reprices on rq3_scores.parquet", [
        "week5/reports/_generated/w5_01_disentanglement.json",
        "week5/reports/_generated/w5_01_disentanglement.csv",
    ]),
    "Conformal-vs-heuristic ablation asset": ("rule contrast structural/final; rates ‡", [
        "week5/reports/_generated/w5_06_ablation.md",
        "week5/reports/_generated/w5_06_ablation.tex",
        "week5/reports/_generated/w5_06_ablation.csv",
        "week5/reports/_generated/w5_06_small_n.csv",
        "week5/reports/figures/w5_fig3_ablation.png",
    ]),
    "RQ5 honesty summary + Day-25 significance suite": ("‡ verdicts reprice on real scores", [
        "week5/reports/_generated/w5_06_rq5_honesty.md",
        "week4/reports/_generated/w4_06_significance.json",
        "week4/reports/_generated/w4_06_significance.csv",
        "week4/reports/_generated/w4_06_rq5_honesty.md",
    ]),
    "Coverage diagnostics (per-class, exchangeability)": ("bands final; rates ‡", [
        "week5/reports/_generated/w5_02_per_class_fzr.csv",
        "week4/reports/_generated/w4_04_live_coverage.json",
    ]),
    "Audited statistics (Day-30 cross-audit, all green)": ("audit of the above", [
        "week5/reports/_generated/w5_07_cross_audit.json",
        "week5/reports/_generated/w5_07_cross_audit.csv",
    ]),
    "Upstream freeze manifests (state pinned by reference)": ("final", [
        "week5/RESULTS_FROZEN/results_manifest_v1.0.json",
        "week5/RESULTS_FROZEN/results_frozen_scalars.json",
        "week4/INTEGRATION/integration_manifest_v1.0.json",
        "week4/INTEGRATION/frozen_thresholds.json",
        "week4/INTEGRATION/interface_contract.json",
    ]),
}


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def audit_is_green():
    p = BASE / "week5" / "reports" / "_generated" / "w5_07_cross_audit.json"
    if not p.exists():
        return False, "w5_07_cross_audit.json absent — run: python week5/scripts/cross_audit.py"
    doc = json.loads(p.read_text(encoding="utf-8"))
    return bool(doc.get("all_pass")), (f"{doc['n_pass']} PASS / {doc['n_fail']} FAIL / "
                                       f"{doc['n_warn']} WARN")


def freeze(source):
    ok, summary = audit_is_green()
    if not ok:
        raise SystemExit(f"HANDOVER refused — the Day-30 cross-audit is not green ({summary}). "
                         "Fix and re-run cross_audit.py first.")
    HAND.mkdir(parents=True, exist_ok=True)
    recs, missing = [], []
    for deliverable, (status, rels) in ASSETS.items():
        for rel in rels:
            p = BASE / rel
            if not p.exists():
                missing.append(rel)
                continue
            recs.append({"deliverable": deliverable, "status": status, "path": rel,
                         "sha256": _sha256(p), "bytes": p.stat().st_size, "rows": _rows(p)})
    if missing:
        for m in missing:
            log(f"  ERROR missing asset: {m}")
        raise SystemExit(f"handover aborted — {len(missing)} asset(s) absent")

    total = sum(r["bytes"] for r in recs)
    manifest = {
        "package": "QS-Net / QuantumSentinel — Team A → Team B manuscript hand-off",
        "version": VERSION, "day": 30, "seed": SEED,
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "primary_alpha": PRIMARY_ALPHA, "source_kind": source, "benchmark_trio": list(TRIO),
        "audit": summary,
        "scope": "Every statistic and coverage asset the manuscript cites (Tables A/B + effects + "
                 "5-seed CIs, Figure 2, RQ3 panel, ablation asset, RQ5 honesty, coverage "
                 "diagnostics, the Day-30 audit) with per-deliverable status. frozen_utc is "
                 "metadata, NOT part of --verify.",
        "reprice": "re-run the week-5 mains with --source real --scores-root <dir>, re-run "
                   "cross_audit.py, then re-cut this package as v1.1",
        "n_files": len(recs), "total_bytes": total, "files": recs,
    }
    (HAND / MANIFEST_NAME).write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    (HAND / "VERSION").write_text(
        f"QS-Net Team A — Team-B manuscript hand-off\nversion: {VERSION}\nseed: {SEED}\n"
        f"primary_alpha: {PRIMARY_ALPHA}\nsource: {source}\ntrio: {', '.join(TRIO)}\n"
        f"files: {len(recs)}  bytes: {total}\naudit: {summary}\n"
        f"manifest: HANDOVER/{MANIFEST_NAME}\n", encoding="utf-8")
    _write_index(manifest)
    log(f"HANDOVER v{VERSION}: pinned {len(recs)} files ({total/1e6:.2f} MB), audit {summary}")
    return manifest


def verify():
    mp = HAND / MANIFEST_NAME
    if not mp.exists():
        print(f"NO HANDOVER MANIFEST at {mp.relative_to(BASE)} — run without --verify first.")
        return 2
    pinned = {r["path"]: r for r in json.loads(mp.read_text(encoding="utf-8"))["files"]}
    missing, changed = [], []
    for rel, rec in pinned.items():
        p = BASE / rel
        if not p.exists():
            missing.append(rel)
        elif _sha256(p) != rec["sha256"]:
            changed.append(rel)
    for x in missing:
        print(f"  MISSING  {x}")
    for x in changed:
        print(f"  CHANGED  {x}")
    if not missing and not changed:
        print(f"HANDOVER VERIFY OK — {len(pinned)} files, 0 mismatch.")
        return 0
    print(f"HANDOVER VERIFY FAILED — {len(missing)} missing, {len(changed)} changed.")
    return 1


def _write_index(manifest):
    by_deliv = {}
    for r in manifest["files"]:
        by_deliv.setdefault((r["deliverable"], r["status"]), []).append(r)
    L = [f"# HANDOVER — Team A → Team B · final statistics + coverage assets · **v{VERSION}**", "",
         f"**Day-30 manuscript hand-off.** Seed {manifest['seed']} · primary α = "
         f"{manifest['primary_alpha']} · trio {', '.join(manifest['benchmark_trio'])} · "
         f"{manifest['n_files']} files · {manifest['total_bytes']/1e6:.2f} MB · audit "
         f"**{manifest['audit']}** · frozen {manifest['frozen_utc']}.", "",
         "Everything the manuscript cites from Team A, in one SHA-256-pinned surface. Each asset "
         "carries its status: **final** cells never move again; **‡ provisional** cells ride the "
         "Day-14 dummy fidelity interface and reprice with one flag on your real prototypes — the "
         "schema, table structures, significance conventions and figures do not change.", "",
         "```bash",
         "python week5/scripts/handover_teamB.py --verify   # re-hash, expect 0 mismatch",
         "```", "",
         "## Contents", ""]
    for (deliv, status), rows in by_deliv.items():
        L.append(f"### {deliv}")
        L.append(f"*status: {status}*")
        L.append("")
        for r in rows:
            L.append(f"- [`{r['path']}`](../../{r['path']}) — {r['bytes']:,} B"
                     + (f", {r['rows']} rows" if r["rows"] else ""))
        L.append("")
    L += ["## What unblocks the final numbers (the standing asks)", "",
          "1. **Real per-seed QS-Net scores** — reprices Table A, Table B, Figure 2, and finally lets "
          "QS-Net enter the Day-25 5-seed paired-t (the seed-level d_z floor is documented in the "
          "Table-A-final report).",
          "2. **RQ3 separation scores** — `<scores-root>/<dataset>/rq3_scores.parquet` with columns "
          "`role ∈ {clean_known, adv_known, true_zeroday}`, `sample_id`, `fid__<class>` "
          "(**non-squared** Uhlmann F). The AUROC machinery and labels are Team A's; your FGSM/PGD "
          "fidelities fill `adv_known`.",
          "3. **Conventions:** non-squared fidelity (`sqrt()` PennyLane/Qiskit's F²), ONE primary α "
          "for quantum and classical, marginal conformal on CIC.", "",
          "## Repricing procedure (identical schema, no code change)", "",
          "```bash",
          "python week5/scripts/disentanglement.py  --source real --scores-root <dir>",
          "python week5/scripts/table_a.py          --source real --scores-root <dir>",
          "python week5/scripts/figure2_coverage.py --source real --scores-root <dir>",
          "python week5/scripts/table_b_final.py    --source real --scores-root <dir>",
          "python week5/scripts/table_a_effects.py  --source real --scores-root <dir>",
          "python week5/scripts/ablation_rq5.py     --source real --scores-root <dir>",
          "python week5/scripts/cross_audit.py      --source real --scores-root <dir>",
          "python week5/scripts/handover_teamB.py                    # re-cut as v1.1",
          "```"]
    (HAND / "HANDOVER.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def render_report(manifest):
    L = ["# Week 5 · Day 30 — Handover to Manuscript (Team A → Team B)", "",
         "Task (`qi26_12_Week_5.pdf`): *hand final statistics + coverage assets to Team B for "
         "manuscript assembly.* "
         f"Seed {SEED} · α = {PRIMARY_ALPHA} · trio {', '.join(TRIO)}.", "",
         f"The hand-off surface is **[`week5/HANDOVER/`](../HANDOVER/HANDOVER.md)** — "
         f"{manifest['n_files']} files ({manifest['total_bytes']/1e6:.2f} MB), SHA-256-pinned in "
         f"[`HANDOVER/{MANIFEST_NAME}`](../HANDOVER/{MANIFEST_NAME}), cut only after the Day-30 "
         f"cross-audit came back **{manifest['audit']}** (the freeze refuses to cut on a non-green "
         "audit).", "",
         "| Deliverable | files | status |", "|---|---:|---|"]
    seen = {}
    for r in manifest["files"]:
        seen.setdefault((r["deliverable"], r["status"]), 0)
        seen[(r["deliverable"], r["status"])] += 1
    for (deliv, status), n in seen.items():
        L.append(f"| {deliv} | {n} | {status} |")
    L += ["",
          "Verification: `python week5/scripts/handover_teamB.py --verify` (0 mismatch). The two "
          "upstream freezes are pinned by their manifests inside this package, so the hand-off state "
          "and the freeze state cannot silently diverge. Repricing on real prototypes re-runs the "
          "week-5 mains with `--source real` and re-cuts this package as v1.1 — the asset list and "
          "schema are frozen.", "",
          "With this hand-off, every Team-A Week-5 deliverable (Days 26–30) is complete: the "
          "remaining Team-A days are the methods subsections + repro appendix (Day 31) and the final "
          "sign-off (Day 32)."]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Day-30 Team-B manuscript hand-off package")
    ap.add_argument("--source", choices=["dummy", "real"], default="dummy")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args(argv)
    if args.verify:
        sys.exit(verify())
    manifest = freeze(args.source)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "w5_08_handover.md").write_text(render_report(manifest), encoding="utf-8")
    log(f"done -> week5/HANDOVER/ (HANDOVER.md + {MANIFEST_NAME} + VERSION) + "
        f"reports/w5_08_handover.md")
    return manifest


if __name__ == "__main__":
    main()
