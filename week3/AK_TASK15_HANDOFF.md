# AK — Week 3 Day 15 Handoff (CQ-ZDR Conformal Calibration) + Iwo Day-13/14 merge

Covers AK's Week-3 Day-15 contribution (the conformal calibration module, Algorithm 2 / CQ-ZDR, and the
first threshold q for dataset 1) plus the integration of Iwo's Day-13/14 deliverables into the shared
Team-A package. Day 15 is the week's ★milestone. Days 16–18 are the same posted task and continue from here.

## What was implemented

1. **Day-15 CQ-ZDR conformal calibration module** (`week3/scripts/conformal_calibrate.py`, report
   `week3/reports/w3_01_conformal_calibration.md`). Nonconformity `s = 1 − max_c F(ρ_x, ρ_c)` computed
   directly from the prototype-fidelity vector; split-conformal threshold `q = s_(k)`,
   `k = ⌈(1−α)(n+1)⌉` on the **known-only** calibration set; flags test/zero-day points with `s > q`.
   Default **marginal** mode (Mondrian behind a flag), α-sweep hook for Day 16, source-agnostic so Team B's
   real prototypes swap in at the same schema (`--source real`). 11 pytest cases.
2. **Ran it on dataset 1 (CIC-IoT2023) at α = 0.05** against Iwo's Day-14 dummy-score interface →
   **first threshold q (CIC, dummy) = 0.300551**, known-test coverage 0.9514, false-zero-day 0.0486 (≤ α).
3. **Merged Iwo's Day-13/14 package** into the repo (additive): all-dataset baselines + One-Class SVM,
   `stats_harness.py` (5-seed CIs), `leakage_check.py`, the Day-14 `FROZEN/` data freeze, and the
   `interface/dummy_scores/` score contract; the three handoffs (Owais 11-12, Iwo 13-14). The manifest was
   **regenerated** (not overwritten with Iwo's partial one). Full suite: 35 tests pass (24 his + 11 mine).

## What went well

- **The Day-14 interface unblocked Day-15 immediately** — the dummy scores already emit the exact
  `1 − max_c F` contract, so the module was built and run end-to-end without waiting on Team B.
- **The design is literature-clean:** `q = s_(k)`, `k = ⌈(1−α)(n+1)⌉`, flag `s > q` is the textbook
  one-sided split-conformal / conformal-outlier test (Bates et al. 2023); coverage held on CIC
  (false-zero-day 0.0486 ≤ 0.05).
- **Real-prototype swap needs no code change** — recomputing `s` from `fid__*` makes the dummy→real switch a
  `--scores-root/--source` flag.
- **Merge was clean and verified** — the interface `nonconformity` recompute matched to 0.0; all prior tests
  still pass.

## Challenges and issues

1. **Dummy vs real prototypes.** The milestone wants "real prototypes"; Team B's real fidelities for CIC are
   not in the package yet, so q = 0.300551 is a **placeholder**. The module is wired to reprice on arrival.
2. **Order-statistic reconciliation.** The task's `q = s_(k)` is one index below `split_integrity.py`'s
   `np.quantile(…, method="higher")` = `s_(k+1)`; both satisfy coverage ≥ 1 − α. Documented; did **not** edit
   another member's file.
3. **UNSW is the hard bar** (from Iwo's Day-13: macro-F1 ≈ 0.60, zero-day OC-SVM AUROC ≈ 0.48) — frame the
   bar QS-Net must clear as the hard slices, not the saturated CIC top-line.
4. **Iwo's freeze is internally inconsistent** (count 93 vs 97; pins a `IWO_DAY13-14_SUMMARY.md` absent from
   the package) — flagged to Iwo; re-run `freeze_package.py` for a self-consistent v1.0.

## Concerns and recommendations

- **Team B:** use **marginal** conformal for CIC (four ≤ 9-row known classes make class-conditional
  degenerate at α = 0.05 — Ding et al. 2023). Build each prototype `ρ_c` from **train only**; calibration
  must stay out-of-sample or the threshold is optimistic. Flag with strict `s > q`.
- **Report coverage and power separately** — the α-sweep validates false-zero-day ≤ α on known data; zero-day
  detection is a separate ROC on the held-out class. Do not conflate them.
- **Novelty note:** fidelity-to-prototype as a conformal nonconformity score appears novel (good for the
  paper) — validity is score-agnostic, but detection **power** must be shown on real prototypes empirically.

## Measured results (Day 15, dummy interface, α = 0.05)

| Dataset                             |  n_cal |      k |        threshold q | known coverage | false-zero-day (≤ α) | zero-day rejection |
| ----------------------------------- | -----: | -----: | -----------------: | -------------: | ---------------------: | -----------------: |
| **CIC-IoT2023** (deliverable) | 18,883 | 17,940 | **0.300551** |         0.9514 |                 0.0486 |             0.9998 |
| BoT-IoT (dummy preview)             | 18,591 | 17,663 |           0.262934 |         0.9470 |               0.0530¹ |           0.0952² |
| UNSW-NB15 (dummy preview)           | 10,112 |  9,608 |           0.383380 |         0.9537 |                 0.0463 |           0.3857² |

¹ dummy synthetic artifact (placeholder scores, not a real coverage miss). ² low by construction — the dummy
zero-day means track the Day-9 diagnostic (CIC 0.771, BoT 0.134, UNSW 0.352); real prototypes will differ.

## References

- Angelopoulos & Bates 2023 (the quantile + coverage bound); Bates, Candès, Lei, Romano & Sesia 2023
  (conformal outlier p-values — CQ-ZDR); Ding et al. 2023 (class-conditional CP — the ≥ 19/class floor);
  Vovk/Gammerman/Shafer 2005 + Lei et al. 2018 (split-conformal foundations); Barber et al. 2023
  (beyond exchangeability).

## Upload / merge these files

**AK uploads (new or changed vs Drive):**
- `week1/manifest/{manifest.json, MANIFEST.md}` — regenerated canonical (665 files; supersedes Iwo's partial 434).
- `week3/` — `scripts/conformal_calibrate.py`, `reports/w3_01_conformal_calibration.md`, `tests/`, `README.md`, this handoff.
- `week2/reports/w2_07_leakage_controls.md` — new consolidated leakage-control page.
- Updated index docs: `week1/README.md`, `week1/UPLOAD.md`, `week2/README.md` (Days 8–14 + Week-3 + counts).
- 14 line-ending-aligned data files (LF): `week2/rq3/<name>/{adversarial_source_pool,eval_clean}.csv` + `rq3_schema.json`
  and `datasets/<name>/unified/qadcp/validation_report.json` — content-identical to Drive but CRLF there (Iwo's Windows
  checkout), so upload the LF versions to keep `make_manifest.py --verify` byte-clean (or leave them and note the diff is cosmetic).

**Already on Drive via Iwo's zip — do NOT re-upload (verified byte-identical to Drive):**
- `week2/scripts/{leakage_check,stats_harness,make_dummy_scores,freeze_package}.py`, `week2/reports/{w2_05,w2_06}*.md`,
  `week2/{FROZEN,interface}/`, `week2/baselines/{BoT-IoT,UNSW-NB15}/`, `week2/{IWO_TASK13,IWO_TASK14,OWAIS_TASK11_12}_HANDOFF.md`.

## Do not upload

- `../.venv/`, any `__pycache__/`, `week2|week3/reports/_generated/` (confidential
  local mirror), the raw archives.

## Verification performed

- `python -m pytest week2/tests week3/tests` → 35 passed.
- `conformal_calibrate.py` on CIC α=0.05 → q 0.300551, coverage 0.9514, false-zero-day 0.0486, crosscheck 0.0.
- `make_manifest.py --verify` → 0 mismatch, 0 missing on the regenerated full manifest.

## WhatsApp message (Week-3 kickoff update)

```text
Team A - Week 3 Day 15 done (conformal calibration module, CQ-ZDR / Algorithm 2).

What landed:
1. Merged Iwo's Day 13 and Day 14 into the shared package: all-dataset baselines plus One-Class SVM, the
   5-seed statistics harness, the leakage check, the Day-14 data freeze, and the dummy score interface. All
   24 of his tests pass here.
2. Built and ran the Day-15 CQ-ZDR conformal calibration module on dataset 1 (CIC) at alpha 0.05, against
   the dummy score interface. First threshold q (CIC, dummy) = 0.3006, known-test coverage 0.9514,
   false-zero-day rate 0.0486 (at or below alpha). Module plus 11 tests. The identical command reprices q
   when Team B's real prototypes arrive at the same schema.

Using marginal conformal for CIC (its four rare known classes make class-conditional degenerate at 0.05).

To confirm:
- Team B: are the real prototype fidelities for dataset 1 (CIC) ready? Until then I run on the dummy interface.
- Iwo: the Day-14 freeze count reads 93 in the handoff but 97 in FROZEN, and it pins IWO_DAY13-14_SUMMARY.md
  which is not in the package - can you re-run the freeze so it is self-consistent?

Days 16 to 18 (coverage harness, alpha-sweep, 5-seed stats, all datasets) are the same posted task, ready to
continue. Thanks.
```
