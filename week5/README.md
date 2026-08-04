# QS-Net · Team A — Week 5 (Days 26–32): Coverage Figure, Zero-Day Tables & Final Statistics

Project 12 of QIntern 2026 — **QuantumSentinel / QS-Net**. This is the **Week-5 package index** — the
results week (after it, only manuscript writing). Team A owns the paper's **Proposition 3 (conformal
coverage)**; Week 5 delivers the headline guarantee evidence: the coverage figure and the
significance-tested result tables. Trio **CIC-IoT2023 + BoT-IoT + UNSW-NB15**; qubit budget 8; seed 42.

> These modules consume the **Day-14 score interface** ([`../week2/interface/`](../week2/interface)) and the
> consolidated Week-4 code (conformal / coverage / stats / freeze). Everything quantum is still on the
> **dummy** interface, so every QS-Net number this week is **PROVISIONAL** — Table A, the disentanglement
> AUROC and Figure 2 are **protocol-final, numbers-provisional** and reprice on Team B's real prototypes with
> `--source real --scores-root <dir>` (no code change). Docs are unified in `week1/`.

## Contents

| Day | Deliverable | Report | Code |
|---|---|---|---|
| **26** (a) | **Disentanglement (RQ3) — separation AUROC** — DONE | [`reports/w5_01_disentanglement.md`](reports/w5_01_disentanglement.md) | [`scripts/disentanglement.py`](scripts/disentanglement.py) → `reports/_generated/w5_01_*` |
| **26** (b) | **Table A (RQ1 in-distribution detection) + significance + coverage diagnostics** — DONE | [`reports/w5_02_table_a.md`](reports/w5_02_table_a.md) · Table A: [`_generated/w5_02_table_a.md`](reports/_generated/w5_02_table_a.md) + [`.tex`](reports/_generated/w5_02_table_a.tex) | [`scripts/table_a.py`](scripts/table_a.py) → `reports/_generated/w5_02_*` + `w5_02_per_class_fzr.csv` |
| **26** (c) | **Freeze Team-A result artefacts + confirm reproducibility** — DONE | [`RESULTS_FROZEN/RESULTS_FROZEN.md`](RESULTS_FROZEN/RESULTS_FROZEN.md) | [`scripts/freeze_results.py`](scripts/freeze_results.py) → `RESULTS_FROZEN/` (SHA-256 manifest + scalar snapshot) |
| **27** | **Figure 2 (headline) — empirical false-zero-day rate vs target α** — DONE | [`reports/w5_03_figure2.md`](reports/w5_03_figure2.md) · figure: [`reports/figures/w5_fig2_coverage.png`](reports/figures/w5_fig2_coverage.png) | [`scripts/figure2_coverage.py`](scripts/figure2_coverage.py) → `reports/_generated/w5_03_*` |
| **28** | **Table B (RQ2) FINAL + all-seed coverage CIs** (5-seed re-split CIs for achieved α AND recall) — DONE | [`reports/w5_04_table_b.md`](reports/w5_04_table_b.md) · Table B: [`_generated/w5_04_table_b.md`](reports/_generated/w5_04_table_b.md) + [`.tex`](reports/_generated/w5_04_table_b.tex) | [`scripts/table_b_final.py`](scripts/table_b_final.py) → `reports/_generated/w5_04_*` |
| **29** (a) | **Table A (RQ1) FINAL — significance vs every baseline + Cohen's d/h effects** — DONE | [`reports/w5_05_table_a_effects.md`](reports/w5_05_table_a_effects.md) · Table A: [`_generated/w5_05_table_a.md`](reports/_generated/w5_05_table_a.md) + [`.tex`](reports/_generated/w5_05_table_a.tex) | [`scripts/table_a_effects.py`](scripts/table_a_effects.py) → `reports/_generated/w5_05_*` |
| **29** (b) | **Conformal-vs-heuristic ablation asset + RQ5 honesty summary** — DONE | [`reports/w5_06_ablation_rq5.md`](reports/w5_06_ablation_rq5.md) · figure: [`reports/figures/w5_fig3_ablation.png`](reports/figures/w5_fig3_ablation.png) · RQ5: [`_generated/w5_06_rq5_honesty.md`](reports/_generated/w5_06_rq5_honesty.md) | [`scripts/ablation_rq5.py`](scripts/ablation_rq5.py) → `reports/_generated/w5_06_*` |
| **30** (a) | **Cross-audit: every Team-A number vs the raw logs (independent re-derivations)** — DONE, 90/91 PASS + 1 documented WARN | [`reports/w5_07_cross_audit.md`](reports/w5_07_cross_audit.md) | [`scripts/cross_audit.py`](scripts/cross_audit.py) → `reports/_generated/w5_07_*` |
| **30** (b) | **Handover to manuscript — Team B package (audit-gated, SHA-256-pinned)** — DONE | [`reports/w5_08_handover.md`](reports/w5_08_handover.md) · package: [`HANDOVER/HANDOVER.md`](HANDOVER/HANDOVER.md) | [`scripts/handover_teamB.py`](scripts/handover_teamB.py) → `HANDOVER/` |
| **31** (a) | **Methods subsections — Data + Conformal Statistics** (partition protocol, calibration, coverage) — DONE | [`reports/w5_09_methods_data_stats.md`](reports/w5_09_methods_data_stats.md) · LaTeX: [`_generated/w5_09_methods.tex`](reports/_generated/w5_09_methods.tex) | *(prose — no new code; consolidates Days 8–9, 15–17, 23, 26–30)* |
| **31** (b) | **Reproducibility appendix — the statistics pipeline** — DONE | [`reports/w5_10_repro_appendix.md`](reports/w5_10_repro_appendix.md) · LaTeX: [`_generated/w5_10_repro_appendix.tex`](reports/_generated/w5_10_repro_appendix.tex) | *(verification log measured against the existing freeze/audit gates)* |
| **32** | **Final sign-off — one script re-derives every RQ2/RQ5 number + Figure 2; all deliverables frozen** — DONE, 324/324 checks | [`reports/w5_11_signoff.md`](reports/w5_11_signoff.md) | [`scripts/signoff.py`](scripts/signoff.py) → `reports/_generated/w5_11_signoff.{json,csv}` |

**Day-26 disentanglement (RQ3, dummy):** the separation AUROC — true-zero-day (+) vs adversarial-known (−) —
is **0.4994 / 0.4763 / 0.5104** (CIC / BoT / UNSW), every CI bracketing 0.5. That is the **honest null**: with
no real FGSM/PGD scores yet, `adv_known` is a seeded independent half of the zero-day pool, so the two are
indistinguishable by construction — not a synthesised separation. Both `zeroday_vs_clean` and `adv_vs_clean`
come out high (novelty *is* detectable against clean traffic), which is exactly why separation is the hard
question. The real separation AUROC lands when Team B ships `rq3_scores.parquet`.

**Day-26 Table A (RQ1, α = 0.05):** XGBoost (real, final) accuracy 0.9896 / 0.9515 / 0.8020; QS-Net (dummy,
provisional) 0.9034 / 0.9396 / 0.7966. Exact McNemar QS-Net vs XGBoost, Holm over the 3-dataset family:
significant on CIC and BoT, **not** on UNSW (p = 0.35). The **all-seed coverage check** (pooled re-split over
seeds 42–46) holds the exact 99 % band on **5/5 seeds for all three** datasets (mean FZR ≈ 0.050). The
**per-class achieved-FZR diagnostic** — the correct answer to the class-imbalance flag — gives every known
class its *own* exact band: marginal conformal controls the false-alarm rate over the KNOWN *mixture* but
carries **no per-class guarantee**; 0 classes fall outside their band on the dummy, and a class that does on
real scores points to **clustered conformal** (Ding et al. 2023), not full class-conditioning.

**Day-26 freeze:** 16 result artefacts + 39 headline scalars pinned under `RESULTS_FROZEN/`; `--verify`
re-hashes to **0 mismatch** and `--reproduce` re-runs the three deterministic mains and confirms all 39
scalars return to **1e-9**. An `_assert_lf` gate refuses to freeze any CRLF text blob.

**Day-27 Figure 2 (headline coverage plot):** the empirical false-zero-day rate tracks the diagonal `y = α`
inside the exact **Beta-Binomial** validity band (not Clopper–Pearson) across the 0.01–0.20 sweep on all
three datasets, with the 5-seed points at α = 0.05 (mean ≈ 0.050) sitting inside the band — the picture of a
calibrated detector.

**Day-31 methods + repro appendix:** the two manuscript subsections (Data — partition protocol, leakage
controls, exchangeability verification; Conformal Statistics — nonconformity score, `q = s_(k)`, the
marginal-vs-Mondrian choice, the exact Beta-Binomial acceptance gate, 5-seed stability, the exchangeability
audit, and the significance protocol) ship as prose plus a LaTeX drop-in for Team B's Article-1 assembly.
The repro appendix is backed by a **measured** verification run rather than inherited claims: all three
freezes `--verify` at **0 mismatch** (34 + 16 + 41 files), `--reproduce` returns **39/39 scalars to 1e-9**,
the cross-audit holds at **90 PASS / 0 FAIL / 1 WARN**, and the full suite passes **182 tests in 73 s**
leaving the tree clean. It also records the one honest limit: the pipeline reproduces every *number* to
1e-9 across Python 3.10–3.12, but not every *byte* — a full re-run drifts 9 files by 1–2 ULP in the
scipy exact-binomial McNemar tail (2.1e-20 absolute) plus PNG rasterization, while **every rendered
`.md`/`.tex` table stays byte-identical**. One open item for Day 32 is logged there: `--reproduce` writes
into the real tree, so it dirties the surface a subsequent `--verify` checks (one-line fix, same pattern
the Day-30 pytest guard already uses).

**Day-32 final sign-off:** [`scripts/signoff.py`](scripts/signoff.py) is the *one script* the task asks
for — **324 checks, 324 PASS / 0 FAIL**. It re-runs the five result mains with outputs sandboxed and diffs
**289 scalars** against the committed artefacts that quote them, spanning RQ1, **RQ2**, RQ3, **RQ5** and
Figure 2 — **204 recomputed** from the raw scores on the run, **85 pass-through** cells the emitting module
reads from an upstream frozen artefact (Table B's canonical cells from the Day-21/22/19 arms, the RQ5
verdicts from Day-25, Table A's classical arm from Day-12). That split is reported, not pooled: for a
pass-through, G1 proves the assembly path is stable, and the numeric is re-derived instead by **G5**, which
runs the Day-30 cross-audit's separate implementation (90 PASS / 0 FAIL / 1 WARN). That scope matters: `freeze_results.py --reproduce` pins 39 scalars covering RQ1/RQ3/Figure 2
only, so **RQ2 and RQ5 — the two the task names — were never in a reproducibility gate until now**. The other gates: the three SHA-256 manifests re-hash clean (34 + 16 + 41), all 30 declared deliverables are
present across 9 groups, and **no pinned artefact changed while the sign-off ran** (hashes taken before and
after), which is what makes the check non-circular. `--tol 0` reproduces the Day-31 ULP finding from a
second code path: exactly 2 of 289 scalars fail bit-exact, both McNemar Holm p-values, at 4.2e-20 and
1.1e-16 — every RQ2 and RQ5 scalar is bit-identical. Day 32 also **closed the Day-31 open item**:
`freeze_results.sandboxed_outputs()` makes `--reproduce` tree-neutral, so it no longer rewrites the
artefacts `--verify` pins.

**Repo hygiene this week:** a repo-root [`../.gitattributes`](../.gitattributes) (`* text=auto eol=lf`,
binaries pinned) makes a fresh clone byte-identical on any OS, so the SHA-256 freeze manifests
(`week4/INTEGRATION`, `week5/RESULTS_FROZEN`) `--verify` clean off a Windows checkout too. Absolute
`scores_root` paths that had leaked into committed JSON were made repo-relative at the source.

## Reproduce

```bash
source ../.venv/bin/activate                                                    # Python 3.12
python week5/scripts/disentanglement.py  --datasets CICIoT2023 BoT-IoT UNSW-NB15 --alpha 0.05
python week5/scripts/table_a.py          --datasets CICIoT2023 BoT-IoT UNSW-NB15 --alpha 0.05
python week5/scripts/figure2_coverage.py --alpha 0.05 --sweep 0.01 0.20 0.01
python week5/scripts/freeze_results.py                                          # Day 26 -> RESULTS_FROZEN/
python week5/scripts/freeze_results.py --verify                                 # re-hash, expect 0 mismatch
python week5/scripts/freeze_results.py --reproduce                              # re-run mains, 39 scalars, 0 mismatch
# --- Days 28-30 ---
python week5/scripts/table_b_final.py    --datasets CICIoT2023 BoT-IoT UNSW-NB15 --alpha 0.05   # Day 28
python week5/scripts/table_a_effects.py  --datasets CICIoT2023 BoT-IoT UNSW-NB15 --alpha 0.05   # Day 29
python week5/scripts/ablation_rq5.py     --alpha 0.05 --sweep 0.01 0.20 0.01                    # Day 29
python week5/scripts/cross_audit.py                                             # Day 30: audit vs raw logs
python week5/scripts/handover_teamB.py                                          # Day 30: Team-B package
python week5/scripts/handover_teamB.py --verify                                 # re-hash, expect 0 mismatch
python week5/scripts/signoff.py                                                 # Day 32: 324/324, exit 0
python week5/scripts/signoff.py --tol 0                                         # bit-exact variant (2 ULP fails)
python -m pytest week2/tests week3/tests week4/tests week5/tests -q             # full suite: 182 tests
```

## For Team B (QML) — what unblocks the "final" numbers

- **Real per-seed QS-Net scores** reprice Table A (RQ1), Table B (RQ2), and Figure 2 in one flag
  (`--source real --scores-root <dir>`) — and let QS-Net finally enter the Day-25 5-seed paired-t (currently
  classical-only).
- **RQ3 separation scores (Day 26 hand-off):** emit `<scores-root>/<name>/rq3_scores.parquet` with columns
  `role ∈ {clean_known, adv_known, true_zeroday}`, `sample_id`, `fid__<class>` (non-squared Uhlmann F). Team A
  supplies the labels + the scoring rule + the AUROC machinery; Team B supplies the adversarial (FGSM/PGD)
  fidelities behind `adv_known`.
- **Same conventions as Week 4:** non-squared Uhlmann fidelity (`sqrt()` PennyLane/Qiskit's F²), one primary
  α for quantum and classical, marginal conformal for CIC.

*Notes: every QS-Net cell this week is a dummy placeholder tagged PROVISIONAL / ‡ — the protocol, table
structure, significance convention and figure are final; the numbers arrive with Team B's real prototypes.*
