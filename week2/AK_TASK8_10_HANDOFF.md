# AK - Week 2 Days 8-10 Handoff (Conformal Partitions, Split Integrity, RQ3) + Week-1 verification

This note covers the Task 8-10 contribution (conformal data partitions, split-integrity/exchangeability,
and the RQ3 adversarial-vs-zero-day evaluation set) for the mentor-locked benchmark trio, plus the Week-1
verification work done during this period (most importantly the quantum-label fix). Day 11-12 was Owais's
(see `week2/OWAIS_TASK11_12_HANDOFF.md`); Day 13-14 is Iwo's.

## What was implemented

1. **Day 8 - conformal partitions.** Re-shaped the Week-1 leakage-safe unified v1.0 splits into the Week-2
   Train / Calibration / Test / Zero-Day layout for CIC-IoT2023, BoT-IoT, UNSW-NB15 (`week2/scripts/make_partitions.py`
   -> `week2/partitions/<name>/*.csv` + `partition_meta.json`; report `w2_01_partition_spec.md`). Train =
   Week-1 train + val; calibration/test/zeroday are byte-identical to Week 1 (so exchangeability is
   preserved). Calibration is KNOWN classes only; one full attack class is held out as the zero-day.
2. **Day 9 - split-integrity + conformal exchangeability.** `week2/scripts/split_integrity.py` runs four
   checks per dataset: (a) hard disjointness asserts (`zeroday ∩ calibration = ∅`, `train ∩ (cal ∪ test) = ∅`,
   zero-day family isolated, calibration known-only); (b) class-distribution match (TVD/chi2/KS);
   (c) a classifier two-sample test (AUROC ~0.50 means calibration and test are indistinguishable =
   exchangeable); (d) a split-conformal coverage smoke test at alpha=0.10. Report `w2_02_split_integrity.md`.
3. **Day 10 - RQ3 adversarial-vs-zero-day evaluation set.** `week2/scripts/make_rq3_evalset.py` builds a
   two-axis factorial eval set - origin (known/novel) x perturb (clean/adversarial) - with a clean
   adversarial-source pool of KNOWN attacks (never the zero-day class) for Team B to perturb with FGSM/PGD,
   plus the true held-out zero-day. Labelling schema keeps adversarial-known and true-zero-day separable;
   metrics defined (novelty AUROC, adversarial AUROC, a 3x3 confusion matrix). Report `w2_03_rq3_eval_set.md`.

## Week-1 verification since 2026-07-10 (done during Week 2)

1. **Quantum label fix (Week-1 QADCP).** `week1/scripts/qadcp.py` wrote the `quantum/q{4,8,12,16}_*`
   label columns with an index-aligned assignment on boolean-masked splits, so about 34% of the q8/q16
   labels became NaN or scrambled (parent split parquets were always correct). Adopted the team's fix
   (`for lbl in LABELS: q[lbl] = s[lbl].to_numpy()`, positional) and regenerated the full v0.1 + unified
   pipeline. `validate_pipeline.py` (the Day-7 acceptance gate, including the `quantum_labels` check) now
   passes on all datasets: q8 labels equal the parent split, 0 NaN.
2. **Reconciled the repo to the team Week-1-FINAL** (adopted `14_handover_report`, `15_teamC_interface`,
   `16_integration_meeting`, `17_unified_collapse_mentor_note`, `validate_pipeline.py`; renamed the earlier
   enriched-schema study to `18_enriched_schema_exploration.md`, marked superseded by the mentor decision).
3. **Manifest re-verified end to end.** Regenerated the SHA-256 manifest over the full raw + curated tree
   (now including Week-2 partitions/RQ3 and the CIC baseline artifacts): 632 files, `--verify` 0 mismatch,
   0 missing.

## What went well

- **No re-shuffle:** partitions reuse the verified Week-1 split assignment, so the leakage-safe guarantees
  and exchangeability transfer exactly; calibration/test/zeroday are byte-identical to Week 1.
- **Exchangeability empirically confirmed,** not just asserted: the calibration-vs-test classifier
  two-sample AUROC is ~0.50 on all three datasets and split-conformal coverage is ~0.90, which is the
  decisive falsification test for the conformal prerequisite.
- **RQ3 designed for a genuinely hard question** with a factorial labelling schema so adversarial-known and
  true-zero-day stay separable; adversarial seeds are never drawn from the zero-day class.
- **Caught and helped verify the q8 label bug fix** before it reached Team B's training.

## Challenges and issues

1. **Unified 17-feature schema collapses TON/Edge zero-day** to 1-2 rows; this drove the mentor decision to
   lock the benchmark to CIC + BoT + UNSW and set TON/Edge aside (`week1/reports/17_unified_collapse_mentor_note.md`).
2. **CIC-IoT2023 has 4 ultra-rare known classes** (`Backdoor_Malware`, `Recon-PingSweep`, `Uploading_Attack`,
   `XSS`; <=9 calibration/test rows each). Marginal conformal (calibration n=18,883) is unaffected and
   verified, but class-conditional/Mondrian thresholds at 90-95% are too sparse for those classes.
3. **The q8 label bug** (fixed, above) briefly affected the Week-1 quantum outputs; the parent splits were
   always correct.
4. **BoT-IoT split is stratified, not time-aware** (`stime` dropped as an identifier) -> possible temporal
   leakage; a Day-6+ fix is noted.

## Concerns and recommendations

- **Team B:** use **marginal** conformal for CIC (rare classes block Mondrian); BoT/UNSW support either.
  Apply FGSM/PGD in the classical feature space **before** angle encoding, with the epsilon budget in
  scaled-feature units, and **never seed adversarials from the zero-day class**. Report the RQ3 result as
  the 3x3 confusion matrix (adversarial-known vs true-zero-day), not a pooled number.
- ~~**Day 13 (Iwo) / final table:** the classical baselines are near-ceiling on CIC (a known dataset-triviality
  effect), so frame the bar QS-Net must clear as the **hard slices** (rare-class macro-F1, per-attack
  zero-day AUPRC/FPR@95, calibration coverage, efficiency), not the saturated top-line. XGBoost `hist` is
  not bit-identical across machines - use the 5-seed mean/std/95% CI for the reported number.~~
- **Datasets:** Day-13 in the task sheet lists TON-IoT, but the mentor locked the trio to **UNSW** - use UNSW.
- **Novelty agenda:** the challenges + strengths and the enriched-schema study (`week1/reports/19`, `18`)
  are the design inputs for a future team-curated dataset that avoids the schema collapse.

## Measured results (Days 8-10)

**Day 8 partition spec (per dataset):**

| Dataset     |   Train | Calibration |   Test | Zero-Day | Known classes | Held-out zero-day  |
| ----------- | ------: | ----------: | -----: | -------: | ------------: | ------------------ |
| CIC-IoT2023 | 151,049 |      18,883 | 18,883 |   10,984 |            31 | Mirai (3 variants) |
| BoT-IoT     | 148,729 |      18,591 | 18,591 |      683 |             4 | Theft              |
| UNSW-NB15   |  81,215 |      10,112 | 10,086 |    1,216 |             8 | Worms + Shellcode  |

**Day 9 exchangeability (calibration vs test):**

| Dataset     |    TVD | two-sample AUROC | conformal coverage (alpha=0.10) | zero-day nonconformity | exchangeable |
| ----------- | -----: | ---------------: | ------------------------------: | ---------------------: | :----------: |
| CIC-IoT2023 | 0.0000 |           0.4999 |                          0.9019 |                  0.771 |     yes     |
| BoT-IoT     | 0.0000 |           0.5038 |                          0.9007 |                  0.134 |     yes     |
| UNSW-NB15   | 0.0019 |           0.5035 |                          0.9063 |                  0.352 |     yes     |

**Day 10 RQ3 factorial cells (clean; Team B adds adversarial-known by perturbing the pool):**

| Dataset     | adversarial-source pool | clean-known | true-zero-day | pool classes |
| ----------- | ----------------------: | ----------: | ------------: | -----------: |
| CIC-IoT2023 |                   3,273 |       3,473 |         3,000 |           30 |
| BoT-IoT     |                     600 |         800 |           683 |            3 |
| UNSW-NB15   |                     956 |       1,156 |         1,216 |            7 |

## References

- Barber, Candes, Ramdas, Tibshirani, *Conformal Prediction Beyond Exchangeability* (2023); Angelopoulos &
  Bates, *A Gentle Introduction to Conformal Prediction* (2023) - exchangeability + coverage.
- Novello, Dalmau, Andeol, *OOD Detection Should Use Conformal Prediction (and Vice-versa?)* (2024);
  Xie et al., *Conformal Inference for Open-Set and Imbalanced Classification* (2024) - conformal novelty.
- Karunanayake et al., *Out-of-Distribution Data: An Acquaintance of Adversarial Examples*, ACM CSUR (2024);
  West et al., *Benchmarking Adversarially Robust QML at Scale* (2022) - adversarial vs OOD; attack surface.
- Sarhan, Layeghy, Portmann, *Towards a Standard Feature Set for NIDS* / NetFlow NF-v2 datasets - unified schema.

## Upload / merge these files

### Day 8-10 files (already synced in the shared Week-2 package)

- `week2/AK_TASK8_10_HANDOFF.md` (this note)
- `week2/reports/w2_01_partition_spec.md`, `w2_02_split_integrity.md`, `w2_03_rq3_eval_set.md`
- `week2/scripts/make_partitions.py`, `split_integrity.py`, `make_rq3_evalset.py`
- `week2/partitions/<name>/*` and `week2/rq3/<name>/*` (CIC, BoT, UNSW)
- `week2/README.md` (Week-2 index)

### Week-1 verification files (canonical)

- `week1/scripts/qadcp.py` (q8 label fix), `validate_pipeline.py`
- `week1/manifest/manifest.json`, `week1/manifest/MANIFEST.md` (632 files, 0 mismatch)

## Do not upload

- `../.venv/`, any `__pycache__/`, `week2/reports/_generated/` (regeneratable intermediates).

## Verification performed

- `validate_pipeline.py` (Day-7 acceptance, incl. `quantum_labels`): ALL PASS on all 5 datasets.
- `split_integrity.py`: all disjointness asserts pass; cal-vs-test two-sample AUROC ~0.50; coverage ~0.90;
  reproducible under seed 42.
- `make_rq3_evalset.py`: the adversarial pool excludes benign + zero-day; `should_flag_*` labels correct;
  no zero-day leakage into the pool.
- `make_manifest.py --verify`: 632 files, 0 mismatch, 0 missing.

## WhatsApp message

```text
Team A - my Week 2 Days 8 to 10 (data partitions and RQ3) plus the Week-1 verification.

Done for the benchmark trio CIC, BoT, UNSW:
1. Conformal partitions (Train, Calibration, Test, Zero-Day). Calibration is known classes only; one full
   attack class is held out as the zero-day.
2. Split-integrity report: calibration and test are indistinguishable (two-sample AUROC about 0.50) and
   split-conformal coverage is about 0.90 on all three, so exchangeability holds.
3. RQ3 adversarial vs zero-day eval set with a two-axis label (origin known/novel, perturb clean/adversarial)
   so adversarial-known stays separable from true-zero-day. Never seed adversarials from the zero-day class.

Week-1 verification: adopted and re-verified the quantum label fix in qadcp.py (about a third of the q8/q16
labels were NaN or scrambled; parent splits were fine). Day-7 validation now passes and the full manifest
verifies (632 files, 0 mismatch).

Notes for Team B: use marginal conformal for CIC (four rare classes); apply FGSM/PGD in the classical
feature space before angle encoding. Days 8 to 10 done; Day 13 is with Iwo. Thanks.
```
