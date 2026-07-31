# Week 5 · Day 30 — Handover to Manuscript (Team A → Team B)

Task (`qi26_12_Week_5.pdf`): *hand final statistics + coverage assets to Team B for manuscript assembly.* Seed 42 · α = 0.05 · trio CICIoT2023, BoT-IoT, UNSW-NB15.

The hand-off surface is **[`week5/HANDOVER/`](../HANDOVER/HANDOVER.md)** — 41 files (0.59 MB), SHA-256-pinned in [`HANDOVER/handover_manifest_v1.0.json`](../HANDOVER/handover_manifest_v1.0.json), cut only after the Day-30 cross-audit came back **90 PASS / 0 FAIL / 1 WARN** (the freeze refuses to cut on a non-green audit).

| Deliverable | files | status |
|---|---:|---|
| Table A (RQ1) — skeleton + final with effects | 9 | ‡ quantum cells provisional |
| Table B (RQ2) — skeleton + final with 5-seed CIs | 9 | ‡ quantum cells provisional |
| Figure 2 — coverage headline | 3 | ‡ provisional (dummy scores) |
| RQ3 — disentanglement AUROC panel | 2 | ‡ honest null on dummy; reprices on rq3_scores.parquet |
| Conformal-vs-heuristic ablation asset | 5 | rule contrast structural/final; rates ‡ |
| RQ5 honesty summary + Day-25 significance suite | 4 | ‡ verdicts reprice on real scores |
| Coverage diagnostics (per-class, exchangeability) | 2 | bands final; rates ‡ |
| Audited statistics (Day-30 cross-audit, all green) | 2 | audit of the above |
| Upstream freeze manifests (state pinned by reference) | 5 | final |

Verification: `python week5/scripts/handover_teamB.py --verify` (0 mismatch). The two upstream freezes are pinned by their manifests inside this package, so the hand-off state and the freeze state cannot silently diverge. Repricing on real prototypes re-runs the week-5 mains with `--source real` and re-cuts this package as v1.1 — the asset list and schema are frozen.

With this hand-off, every Team-A Week-5 deliverable (Days 26–30) is complete: the remaining Team-A days are the methods subsections + repro appendix (Day 31) and the final sign-off (Day 32).
