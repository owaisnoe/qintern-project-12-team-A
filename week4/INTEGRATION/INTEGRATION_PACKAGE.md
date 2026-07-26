# INTEGRATION — QS-Net Team A · calibration/stats package · **v1.0**

**INTEGRATION FREEZE (Day 21).** Seed 42 · primary α = 0.05 · source `dummy` · trio CICIoT2023, BoT-IoT, UNSW-NB15 · 34 files · 26.3 MB · frozen 2026-07-26T10:55:48Z.

Frozen hand-off surface for integration week (Days 22–25): the calibration rule, the score schema, the primary α, and the per-dataset thresholds are pinned so a decision on Day 25 uses the same `q` as Day 22. Every file is SHA-256-pinned in [`integration_manifest_v1.0.json`](integration_manifest_v1.0.json). Verify:

```bash
python week4/scripts/freeze_integration.py --verify   # expect 0 mismatch
```

## Frozen thresholds (α = 0.05, source: dummy)

| Dataset | n_cal | k | threshold q | achieved coverage | false-zero-day | exact band | verdict |
|---|---:|---:|---:|---:|---:|---|---|
| CICIoT2023 | 18,883 | 17,940 | 0.300551 | 0.9514 | 0.0486 | [0.0443, 0.0559] | PASS |
| BoT-IoT | 18,591 | 17,663 | 0.262934 | 0.9470 | 0.0530 | [0.0443, 0.0559] | PASS |
| UNSW-NB15 | 10,112 | 9,608 | 0.383380 | 0.9537 | 0.0463 | [0.0423, 0.0581] | PASS |

## What Team B does with this (Day 22)
1. Emit real inference scores into the **frozen schema** (`interface_contract.json`): one row per partition row, the `fid__<class>` Uhlmann-fidelity columns (**non-squared** F).
2. Point the Day-22 adapter at your score dir; it loads `frozen_thresholds.json[<dataset>].threshold_q` and flags a point as zero-day iff `s = 1 − max_c F > q`. **No recalibration** — the threshold is frozen.
3. Reprice the whole package on real prototypes with `--source real --scores-root <your dir>` (identical schema → no code change).

## Contents
- `frozen_thresholds.json` — authoritative per-dataset `q` + coverage verdict (the integration core).
- `interface_contract.json` — the frozen score schema + fidelity convention Team B must emit.
- pinned code: Day-15 `conformal_calibrate.py`, Day-16 `coverage_harness.py`, Day-17 `stats_protocol.py`, Day-19 `zeroday_recall.py`.
- packaged outputs: coverage (`w3_02_*`, `w3_04_*`), zero-day recall (`w4_01_*`), significance (`w3_03_*`).
- the score interface Team B fills (`week2/interface/dummy_scores/`).
