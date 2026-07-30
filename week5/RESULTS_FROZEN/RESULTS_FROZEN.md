# RESULTS_FROZEN — QS-Net Team A · Week-5 results · **v1.0**

**RESULTS FREEZE (Day 26).** Seed 42 · primary α = 0.05 · source `dummy` · **PROVISIONAL** (Day-14 dummy interface) · trio CICIoT2023, BoT-IoT, UNSW-NB15 · 16 files · 272.7 kB · 39 scalars · frozen 2026-07-30T01:46:51Z.

The Day-26/27 result surface the manuscript cites — RQ1 Table A, RQ3 disentanglement AUROC, and the Figure-2 coverage headline — SHA-256-pinned so the numbers stop moving during writing week. Every file is listed in [`results_manifest_v1.0.json`](results_manifest_v1.0.json).

```bash
python week5/scripts/freeze_results.py --verify      # re-hash, expect 0 mismatch
python week5/scripts/freeze_results.py --reproduce   # re-run the mains, expect 0 mismatch
```

## Contents
- **disentanglement (RQ3):** `w5_01_disentanglement.{md,json,csv}` — separation AUROC panel.
- **Table A (RQ1):** `w5_02_table_a.{md,json,csv}` + skeleton `.md`/`.tex` + `w5_02_per_class_fzr.csv`.
- **Figure 2 (coverage headline):** `w5_03_figure2.{md,json}` + `w5_03_figure2_data.csv` + `figures/w5_fig2_coverage.png`.
- **result modules:** `week5/scripts/{disentanglement,table_a,figure2_coverage}.py`.
- **`results_frozen_scalars.json`** — the pinned headline scalars for `--reproduce`.

## Gates
- **LF gate.** The freeze refuses any pinned text file containing a CRLF; the repo-root `.gitattributes` (`* text=auto eol=lf`) keeps a fresh clone byte-identical so `--verify` passes off a clean checkout on any OS. Run the freeze on Linux.
- **Reproducibility.** `--reproduce` re-runs the three deterministic mains and asserts all 39 pinned scalars return to 1e-9.

> **Provisional.** Every quantum number rides the Day-14 dummy fidelity interface. Re-cut as v1.1 on Team B's real prototypes: `--source real --scores-root <dir>`.
