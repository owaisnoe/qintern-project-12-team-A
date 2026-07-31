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
| **28–32** | Results week continues — final figures/tables, hand-off of coverage + stats assets to Team B (Day 30), manuscript prep | pending | pending |

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
python -m pytest week2/tests week3/tests week4/tests week5/tests -q             # full suite: 135 tests
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
