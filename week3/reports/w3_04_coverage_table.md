# Week 3 · Day 18 — Coverage Table v1 (all datasets)

Task (`qi26_12_week3.pdf`): *extend conformal calibration + coverage to all three datasets; log achieved false-zero-day rate vs target alpha per dataset.* Assembled from [`../scripts/coverage_table.py`](../scripts/coverage_table.py) over [`coverage_harness.verify_dataset`](../scripts/coverage_harness.py) (exact BetaBinomial band, Day 16). The seam into Week-4 Day 24 (RQ2, all datasets).

Threshold q = s_(k), k = ⌈(1−α)(n+1)⌉ on the KNOWN-only calibration split; a test point is a false-zero-day iff s > q. Target **α = 0.05**; exact central **99% band**. Scores: **dummy** interface (real prototypes reprice at the same schema). Seed 42.

| Dataset | n_cal | k | threshold q | target α | achieved FZR | known coverage | 99% band | tail p | conformal holds |
|---|---:|---:|---:|---:|---:|---:|:--:|---:|:--:|
| CICIoT2023 | 18,883 | 17,940 | 0.300551 | 0.05 | 0.0486 | 0.9514 | [0.0443, 0.0559] | 0.732 | ✅ |
| BoT-IoT | 18,591 | 17,663 | 0.262934 | 0.05 | 0.0530 | 0.9470 | [0.0443, 0.0559] | 0.090 | ✅ |
| UNSW-NB15 | 10,112 | 9,608 | 0.383380 | 0.05 | 0.0463 | 0.9537 | [0.0423, 0.0581] | 0.887 | ✅ |

**All 3/3 datasets: conformal false-zero-day rate holds inside the exact 99% band at α = 0.05.** An achieved FZR slightly above α (e.g. BoT-IoT 0.0530) is ordinary finite-sample noise, not a coverage miss — it sits inside the band with a large tail p; that is exactly why the verdict is the exact-law `finite_sample_ok`, not the naive `fzr ≤ α` assert. Coverage controls *false alarms only*; zero-day **recall** (detection power) is reported separately (Week-4 Day 19).

## Appendix — α-sweep 0.01–0.20 (from Day-16 `w3_02_alpha_sweep.csv`)

Across the full sweep, **60/60** (dataset × α) verifications pass the exact band — the achieved coverage tracks the target across 0.01–0.20 on all datasets (curve in `w3_02_coverage_curve.png`).
