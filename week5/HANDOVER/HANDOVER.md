# HANDOVER — Team A → Team B · final statistics + coverage assets · **v1.0**

**Day-30 manuscript hand-off.** Seed 42 · primary α = 0.05 · trio CICIoT2023, BoT-IoT, UNSW-NB15 · 41 files · 0.59 MB · audit **90 PASS / 0 FAIL / 1 WARN** · frozen 2026-07-31T15:50:43Z.

Everything the manuscript cites from Team A, in one SHA-256-pinned surface. Each asset carries its status: **final** cells never move again; **‡ provisional** cells ride the Day-14 dummy fidelity interface and reprice with one flag on your real prototypes — the schema, table structures, significance conventions and figures do not change.

```bash
python week5/scripts/handover_teamB.py --verify   # re-hash, expect 0 mismatch
```

## Contents

### Table A (RQ1) — skeleton + final with effects
*status: ‡ quantum cells provisional*

- [`week5/reports/_generated/w5_02_table_a.md`](../../week5/reports/_generated/w5_02_table_a.md) — 1,792 B
- [`week5/reports/_generated/w5_02_table_a.tex`](../../week5/reports/_generated/w5_02_table_a.tex) — 1,075 B
- [`week5/reports/_generated/w5_02_table_a.json`](../../week5/reports/_generated/w5_02_table_a.json) — 20,274 B
- [`week5/reports/_generated/w5_02_table_a.csv`](../../week5/reports/_generated/w5_02_table_a.csv) — 873 B, 6 rows
- [`week5/reports/_generated/w5_05_table_a.md`](../../week5/reports/_generated/w5_05_table_a.md) — 1,630 B
- [`week5/reports/_generated/w5_05_table_a.tex`](../../week5/reports/_generated/w5_05_table_a.tex) — 1,412 B
- [`week5/reports/_generated/w5_05_table_a_effects.json`](../../week5/reports/_generated/w5_05_table_a_effects.json) — 13,267 B
- [`week5/reports/_generated/w5_05_table_a_effects.csv`](../../week5/reports/_generated/w5_05_table_a_effects.csv) — 728 B, 3 rows
- [`week5/reports/_generated/w5_05_known_fa.csv`](../../week5/reports/_generated/w5_05_known_fa.csv) — 1,873 B, 8 rows

### Table B (RQ2) — skeleton + final with 5-seed CIs
*status: ‡ quantum cells provisional*

- [`week4/reports/_generated/w4_05_table_b.md`](../../week4/reports/_generated/w4_05_table_b.md) — 2,098 B
- [`week4/reports/_generated/w4_05_table_b.tex`](../../week4/reports/_generated/w4_05_table_b.tex) — 1,236 B
- [`week4/reports/_generated/w4_05_rq2_results.json`](../../week4/reports/_generated/w4_05_rq2_results.json) — 10,513 B
- [`week4/reports/_generated/w4_05_rq2_results.csv`](../../week4/reports/_generated/w4_05_rq2_results.csv) — 2,793 B, 11 rows
- [`week5/reports/_generated/w5_04_table_b.md`](../../week5/reports/_generated/w5_04_table_b.md) — 2,274 B
- [`week5/reports/_generated/w5_04_table_b.tex`](../../week5/reports/_generated/w5_04_table_b.tex) — 1,543 B
- [`week5/reports/_generated/w5_04_table_b.json`](../../week5/reports/_generated/w5_04_table_b.json) — 12,584 B
- [`week5/reports/_generated/w5_04_table_b.csv`](../../week5/reports/_generated/w5_04_table_b.csv) — 992 B, 3 rows
- [`week5/reports/_generated/w5_04_allseed_ci.csv`](../../week5/reports/_generated/w5_04_allseed_ci.csv) — 1,661 B, 15 rows

### Figure 2 — coverage headline
*status: ‡ provisional (dummy scores)*

- [`week5/reports/figures/w5_fig2_coverage.png`](../../week5/reports/figures/w5_fig2_coverage.png) — 159,629 B
- [`week5/reports/_generated/w5_03_figure2.json`](../../week5/reports/_generated/w5_03_figure2.json) — 3,094 B
- [`week5/reports/_generated/w5_03_figure2_data.csv`](../../week5/reports/_generated/w5_03_figure2_data.csv) — 8,930 B, 60 rows

### RQ3 — disentanglement AUROC panel
*status: ‡ honest null on dummy; reprices on rq3_scores.parquet*

- [`week5/reports/_generated/w5_01_disentanglement.json`](../../week5/reports/_generated/w5_01_disentanglement.json) — 3,324 B
- [`week5/reports/_generated/w5_01_disentanglement.csv`](../../week5/reports/_generated/w5_01_disentanglement.csv) — 831 B, 9 rows

### Conformal-vs-heuristic ablation asset
*status: rule contrast structural/final; rates ‡*

- [`week5/reports/_generated/w5_06_ablation.md`](../../week5/reports/_generated/w5_06_ablation.md) — 1,644 B
- [`week5/reports/_generated/w5_06_ablation.tex`](../../week5/reports/_generated/w5_06_ablation.tex) — 1,626 B
- [`week5/reports/_generated/w5_06_ablation.csv`](../../week5/reports/_generated/w5_06_ablation.csv) — 1,025 B, 9 rows
- [`week5/reports/_generated/w5_06_small_n.csv`](../../week5/reports/_generated/w5_06_small_n.csv) — 871 B, 15 rows
- [`week5/reports/figures/w5_fig3_ablation.png`](../../week5/reports/figures/w5_fig3_ablation.png) — 217,045 B

### RQ5 honesty summary + Day-25 significance suite
*status: ‡ verdicts reprice on real scores*

- [`week5/reports/_generated/w5_06_rq5_honesty.md`](../../week5/reports/_generated/w5_06_rq5_honesty.md) — 2,512 B
- [`week4/reports/_generated/w4_06_significance.json`](../../week4/reports/_generated/w4_06_significance.json) — 22,022 B
- [`week4/reports/_generated/w4_06_significance.csv`](../../week4/reports/_generated/w4_06_significance.csv) — 2,920 B, 16 rows
- [`week4/reports/_generated/w4_06_rq5_honesty.md`](../../week4/reports/_generated/w4_06_rq5_honesty.md) — 4,533 B

### Coverage diagnostics (per-class, exchangeability)
*status: bands final; rates ‡*

- [`week5/reports/_generated/w5_02_per_class_fzr.csv`](../../week5/reports/_generated/w5_02_per_class_fzr.csv) — 3,314 B, 43 rows
- [`week4/reports/_generated/w4_04_live_coverage.json`](../../week4/reports/_generated/w4_04_live_coverage.json) — 29,725 B

### Audited statistics (Day-30 cross-audit, all green)
*status: audit of the above*

- [`week5/reports/_generated/w5_07_cross_audit.json`](../../week5/reports/_generated/w5_07_cross_audit.json) — 20,191 B
- [`week5/reports/_generated/w5_07_cross_audit.csv`](../../week5/reports/_generated/w5_07_cross_audit.csv) — 8,365 B, 91 rows

### Upstream freeze manifests (state pinned by reference)
*status: final*

- [`week5/RESULTS_FROZEN/results_manifest_v1.0.json`](../../week5/RESULTS_FROZEN/results_manifest_v1.0.json) — 3,644 B
- [`week5/RESULTS_FROZEN/results_frozen_scalars.json`](../../week5/RESULTS_FROZEN/results_frozen_scalars.json) — 1,895 B
- [`week4/INTEGRATION/integration_manifest_v1.0.json`](../../week4/INTEGRATION/integration_manifest_v1.0.json) — 7,259 B
- [`week4/INTEGRATION/frozen_thresholds.json`](../../week4/INTEGRATION/frozen_thresholds.json) — 2,467 B
- [`week4/INTEGRATION/interface_contract.json`](../../week4/INTEGRATION/interface_contract.json) — 1,785 B

## What unblocks the final numbers (the standing asks)

1. **Real per-seed QS-Net scores** — reprices Table A, Table B, Figure 2, and finally lets QS-Net enter the Day-25 5-seed paired-t (the seed-level d_z floor is documented in the Table-A-final report).
2. **RQ3 separation scores** — `<scores-root>/<dataset>/rq3_scores.parquet` with columns `role ∈ {clean_known, adv_known, true_zeroday}`, `sample_id`, `fid__<class>` (**non-squared** Uhlmann F). The AUROC machinery and labels are Team A's; your FGSM/PGD fidelities fill `adv_known`.
3. **Conventions:** non-squared fidelity (`sqrt()` PennyLane/Qiskit's F²), ONE primary α for quantum and classical, marginal conformal on CIC.

## Repricing procedure (identical schema, no code change)

```bash
python week5/scripts/disentanglement.py  --source real --scores-root <dir>
python week5/scripts/table_a.py          --source real --scores-root <dir>
python week5/scripts/figure2_coverage.py --source real --scores-root <dir>
python week5/scripts/table_b_final.py    --source real --scores-root <dir>
python week5/scripts/table_a_effects.py  --source real --scores-root <dir>
python week5/scripts/ablation_rq5.py     --source real --scores-root <dir>
python week5/scripts/cross_audit.py      --source real --scores-root <dir>
python week5/scripts/handover_teamB.py                    # re-cut as v1.1
```
