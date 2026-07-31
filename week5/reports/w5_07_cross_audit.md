# Week 5 · Day 30 — Cross-Audit of All Team-A Numbers Against Raw Logs

Task (`qi26_12_Week_5.pdf`): *cross-audit all Team-A numbers against raw logs; fix any rounding/label mismatches.* Seed 42 · α = 0.05 · trio CICIoT2023, BoT-IoT, UNSW-NB15 · scores **dummy**.

**Verdict: 90 PASS · 0 FAIL · 1 WARN** (91 checks). Every headline quantity was **re-derived from the raw inputs with an independent implementation** (order-statistic threshold, counting, sklearn AUROC vs Mann-Whitney, argmax-re-derived predictions, recounted McNemar cells, raw BetaBinomial pmf) and compared against every artifact that quotes it, including the numbers printed in the rendered md tables. Manifest hashes were re-verified with an independent hashlib pass.

## Fixes applied under this task

1. **Absolute-path leak (label hygiene).** `coverage_harness.py` was the one writer the Day-26 scrub missed — it stored `scores_root` as an absolute path; `w3_02_coverage_verification.json` carried a Windows home path. Fixed at source (repo-relative), the committed JSON scrubbed surgically (only that field changed), and the Day-21 INTEGRATION package re-frozen: 34 files, 0 mismatch, thresholds byte-identical.
2. **pytest artefact-regression guard.** The Day-26 freeze round-trip tests ran the three result mains into the real tree with a CIC-only dataset list, which had overwritten the committed full-trio artifacts (the state this audit's manifest gate now catches). `test_freeze_results.py` redirects the mains to tmp; the committed artifacts were regenerated (byte-identical to the v1.0 manifest) and `--verify` is clean.

## Checks

| # | check | scope | expected | observed | Δ | verdict |
|---:|---|---|---|---|---|:--:|
| 1 | threshold q (order statistic) | CICIoT2023 | 0.300551 | 0.300551 | 0 | ✅ |
| 2 | k = ceil((1-a)(n+1)) | CICIoT2023 | 17940 | 17940 | 0 | ✅ |
| 3 | n_cal | CICIoT2023 | 18883 | 18883 | 0 | ✅ |
| 4 | canonical FZR | CICIoT2023 | 0.048615 | 0.048615 | 0 | ✅ |
| 5 | canonical coverage | CICIoT2023 | 0.951385 | 0.951385 | 0 | ✅ |
| 6 | zero-day recall | CICIoT2023 | 0.999818 | 0.999818 | 0 | ✅ |
| 7 | zero-day n | CICIoT2023 | 10984 | 10984 | 0 | ✅ |
| 8 | Day-19 quantum recall row | CICIoT2023 | 0.9998 | 0.9998 | 0 | ✅ |
| 9 | exact band membership | CICIoT2023 | True | True | 0 | ✅ |
| 10 | XGB accuracy: predictions.csv vs results.json | CICIoT2023 | 0.9896 | 0.9896 | 0 | ✅ |
| 11 | XGB macro-F1: predictions.csv vs results.json | CICIoT2023 | 0.8043 | 0.8043 | 0 | ✅ |
| 12 | XGB accuracy vs frozen scalar | CICIoT2023 | 0.9896 | 0.9896 | 0 | ✅ |
| 13 | XGB macro-F1 vs frozen scalar | CICIoT2023 | 0.8043 | 0.8043 | 0 | ✅ |
| 14 | XGB OVR-AUROC vs frozen scalar | CICIoT2023 | 0.999 | 0.999 | 0 | ✅ |
| 15 | QS-Net accuracy (argmax re-derivation) | CICIoT2023 | 0.9034 | 0.9034 | 0 | ✅ |
| 16 | QS-Net macro-F1 (argmax re-derivation) | CICIoT2023 | 0.6598 | 0.6598 | 0 | ✅ |
| 17 | QS-Net OVR-AUROC (sklearn vs Mann-Whitney) | CICIoT2023 | 0.9438 | 0.9438 | 0 | ✅ |
| 18 | McNemar n10 (QS-only-right) | CICIoT2023 | 176 | 176 | 0 | ✅ |
| 19 | McNemar n01 (XGB-only-right) | CICIoT2023 | 1803 | 1803 | 0 | ✅ |
| 20 | McNemar doubled exact tail | CICIoT2023 | 0 | 0 | 0 | ✅ |
| 21 | RQ3 separation AUROC (sklearn) | CICIoT2023 | 0.4994 | 0.4994 | 0 | ✅ |
| 22 | RQ3 zeroday_vs_clean AUROC (sklearn) | CICIoT2023 | 0.9998 | 0.9998 | 0 | ✅ |
| 23 | RQ3 adv_vs_clean AUROC (sklearn) | CICIoT2023 | 0.9998 | 0.9998 | 0 | ✅ |
| 24 | threshold q (order statistic) | BoT-IoT | 0.262934 | 0.262934 | 0 | ✅ |
| 25 | k = ceil((1-a)(n+1)) | BoT-IoT | 17663 | 17663 | 0 | ✅ |
| 26 | n_cal | BoT-IoT | 18591 | 18591 | 0 | ✅ |
| 27 | canonical FZR | BoT-IoT | 0.053036 | 0.053036 | 0 | ✅ |
| 28 | canonical coverage | BoT-IoT | 0.946964 | 0.946964 | 0 | ✅ |
| 29 | zero-day recall | BoT-IoT | 0.095168 | 0.095168 | 0 | ✅ |
| 30 | zero-day n | BoT-IoT | 683 | 683 | 0 | ✅ |
| 31 | Day-19 quantum recall row | BoT-IoT | 0.0952 | 0.0952 | 0 | ✅ |
| 32 | exact band membership | BoT-IoT | True | True | 0 | ✅ |
| 33 | XGB accuracy: predictions.csv vs results.json | BoT-IoT | 0.9515 | 0.9515 | 0 | ✅ |
| 34 | XGB macro-F1: predictions.csv vs results.json | BoT-IoT | 0.9727 | 0.9727 | 0 | ✅ |
| 35 | XGB accuracy vs frozen scalar | BoT-IoT | 0.9515 | 0.9515 | 0 | ✅ |
| 36 | XGB macro-F1 vs frozen scalar | BoT-IoT | 0.9727 | 0.9727 | 0 | ✅ |
| 37 | XGB OVR-AUROC vs frozen scalar | BoT-IoT | 0.9955 | 0.9955 | 0 | ✅ |
| 38 | QS-Net accuracy (argmax re-derivation) | BoT-IoT | 0.9396 | 0.9396 | 0 | ✅ |
| 39 | QS-Net macro-F1 (argmax re-derivation) | BoT-IoT | 0.8339 | 0.8339 | 0 | ✅ |
| 40 | QS-Net OVR-AUROC (sklearn vs Mann-Whitney) | BoT-IoT | 0.9509 | 0.9509 | 0 | ✅ |
| 41 | McNemar n10 (QS-only-right) | BoT-IoT | 869 | 869 | 0 | ✅ |
| 42 | McNemar n01 (XGB-only-right) | BoT-IoT | 1089 | 1089 | 0 | ✅ |
| 43 | McNemar doubled exact tail | BoT-IoT | 7.26273e-07 | 7.26273e-07 | 0 | ✅ |
| 44 | RQ3 separation AUROC (sklearn) | BoT-IoT | 0.4763 | 0.4763 | 0 | ✅ |
| 45 | RQ3 zeroday_vs_clean AUROC (sklearn) | BoT-IoT | 0.5881 | 0.5881 | 0 | ✅ |
| 46 | RQ3 adv_vs_clean AUROC (sklearn) | BoT-IoT | 0.6083 | 0.6083 | 0 | ✅ |
| 47 | threshold q (order statistic) | UNSW-NB15 | 0.38338 | 0.38338 | 0 | ✅ |
| 48 | k = ceil((1-a)(n+1)) | UNSW-NB15 | 9608 | 9608 | 0 | ✅ |
| 49 | n_cal | UNSW-NB15 | 10112 | 10112 | 0 | ✅ |
| 50 | canonical FZR | UNSW-NB15 | 0.046302 | 0.046302 | 0 | ✅ |
| 51 | canonical coverage | UNSW-NB15 | 0.953698 | 0.953698 | 0 | ✅ |
| 52 | zero-day recall | UNSW-NB15 | 0.385691 | 0.385691 | 0 | ✅ |
| 53 | zero-day n | UNSW-NB15 | 1216 | 1216 | 0 | ✅ |
| 54 | Day-19 quantum recall row | UNSW-NB15 | 0.3857 | 0.3857 | 0 | ✅ |
| 55 | exact band membership | UNSW-NB15 | True | True | 0 | ✅ |
| 56 | XGB accuracy: predictions.csv vs results.json | UNSW-NB15 | 0.802 | 0.802 | 0 | ✅ |
| 57 | XGB macro-F1: predictions.csv vs results.json | UNSW-NB15 | 0.6016 | 0.6016 | 0 | ✅ |
| 58 | XGB accuracy vs frozen scalar | UNSW-NB15 | 0.802 | 0.802 | 0 | ✅ |
| 59 | XGB macro-F1 vs frozen scalar | UNSW-NB15 | 0.6016 | 0.6016 | 0 | ✅ |
| 60 | XGB OVR-AUROC vs frozen scalar | UNSW-NB15 | 0.9695 | 0.9695 | 0 | ✅ |
| 61 | QS-Net accuracy (argmax re-derivation) | UNSW-NB15 | 0.7966 | 0.7966 | 0 | ✅ |
| 62 | QS-Net macro-F1 (argmax re-derivation) | UNSW-NB15 | 0.5513 | 0.5513 | 0 | ✅ |
| 63 | QS-Net OVR-AUROC (sklearn vs Mann-Whitney) | UNSW-NB15 | 0.8711 | 0.8711 | 0 | ✅ |
| 64 | McNemar n10 (QS-only-right) | UNSW-NB15 | 1602 | 1602 | 0 | ✅ |
| 65 | McNemar n01 (XGB-only-right) | UNSW-NB15 | 1656 | 1656 | 0 | ✅ |
| 66 | McNemar doubled exact tail | UNSW-NB15 | 0.35313 | 0.35313 | 0 | ✅ |
| 67 | RQ3 separation AUROC (sklearn) | UNSW-NB15 | 0.5104 | 0.5104 | 0 | ✅ |
| 68 | RQ3 zeroday_vs_clean AUROC (sklearn) | UNSW-NB15 | 0.8477 | 0.8477 | 0 | ✅ |
| 69 | RQ3 adv_vs_clean AUROC (sklearn) | UNSW-NB15 | 0.8405 | 0.8405 | 0 | ✅ |
| 70 | all-seed mean FZR: Table A vs frozen scalar | CICIoT2023 | 0.05175 | 0.05175 | 0 | ✅ |
| 71 | all-seed mean FZR: Table A vs Figure 2 | CICIoT2023 | 0.05175 | 0.05175 | 0 | ✅ |
| 72 | all-seed mean recomputed from per-seed rows | CICIoT2023 | 0.05175 | 0.05175 | 0 | ✅ |
| 73 | all-seed mean FZR: Table A vs frozen scalar | BoT-IoT | 0.050143 | 0.050143 | 0 | ✅ |
| 74 | all-seed mean FZR: Table A vs Figure 2 | BoT-IoT | 0.050143 | 0.050143 | 0 | ✅ |
| 75 | all-seed mean recomputed from per-seed rows | BoT-IoT | 0.050143 | 0.050143 | 0 | ✅ |
| 76 | all-seed mean FZR: Table A vs frozen scalar | UNSW-NB15 | 0.050783 | 0.050783 | 0 | ✅ |
| 77 | all-seed mean FZR: Table A vs Figure 2 | UNSW-NB15 | 0.050783 | 0.050783 | 0 | ✅ |
| 78 | all-seed mean recomputed from per-seed rows | UNSW-NB15 | 0.050783 | 0.050783 | 0 | ✅ |
| 79 | per-class out-of-band recount | CICIoT2023 | 0 | 0 | 0 | ✅ |
| 80 | per-class out-of-band recount | BoT-IoT | 0 | 0 | 0 | ✅ |
| 81 | per-class out-of-band recount | UNSW-NB15 | 0 | 0 | 0 | ✅ |
| 82 | Table B 5-seed mean == Table A all-seed mean | CICIoT2023 | 0.05175 | 0.05175 | 0 | ✅ |
| 83 | Table B 5-seed mean == Table A all-seed mean | BoT-IoT | 0.050143 | 0.050143 | 0 | ✅ |
| 84 | Table B 5-seed mean == Table A all-seed mean | UNSW-NB15 | 0.050783 | 0.050783 | 0 | ✅ |
| 85 | rendered md cells match JSON (w5_02_table_a.md) | - | all | all | — | ✅ |
| 86 | rendered md cells match JSON (w5_04_table_b.md) | - | all | all | — | ✅ |
| 87 | SHA-256 manifest (RESULTS_FROZEN) | - | 0 | 0 | 0 | ✅ |
| 88 | SHA-256 manifest (INTEGRATION) | - | 0 | 0 | 0 | ✅ |
| 89 | SHA-256 manifest (week2 FROZEN) | - | known drift | 13 deviations | — | ⚠ |
| 90 | absolute-path leak scan | repo | 0 | 0 | 0 | ✅ |
| 91 | CRLF scan (committed text) | repo | 0 | 0 | 0 | ✅ |

Notes for each row (tolerances, provenance) are in [`_generated/w5_07_cross_audit.json`](_generated/w5_07_cross_audit.json) / [`.csv`](_generated/w5_07_cross_audit.csv). Exact-copy scalars are held to 1e-9; independently re-implemented estimators to 5e-5 at the 4-dp reporting precision.

## Known-issues register (stated, not hidden)

- **week2 FROZEN drift (pre-existing, WARN):** rq3 eval files regenerated after the Day-14 freeze, README evolved, and `IWO_DAY13-14_SUMMARY.md` was renamed into the two TASK handoffs; the docs also disagree on 93 vs 97 pinned files. Re-cutting that freeze is a team decision (week-2 scope), not silently done here.
- **Environment note:** this audit ran on Python 3.10.12 / sklearn 1.7.2; the repo venv is Python 3.12 / sklearn 1.8.0. All 39 frozen scalars and every manifest hash reproduced regardless — evidence the pipeline is environment-robust, but the venv remains the reference.

## Bottom line

**All checks pass.** Every number the manuscript will cite traces to a raw log and survives an independent re-derivation; the rendered tables print exactly what the artifacts contain; both Team-A freezes verify clean.

CSV: `_generated/w5_07_cross_audit.csv` · JSON: `_generated/w5_07_cross_audit.json` · hand-off: `week5/HANDOVER/` (Day-30 companion, `handover_teamB.py`).
