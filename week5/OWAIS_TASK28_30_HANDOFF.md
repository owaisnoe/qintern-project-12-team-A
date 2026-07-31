# Owais — Week 5 Days 28–30 Handoff (Table B Final, Table A Effects, Ablation + RQ5, Audit, Team-B Handover)

Covers the review-and-merge of AK's Days 26–27 (as requested in AK's chat update) and the Week-5
Days 28–30 deliverables: Table B final with the all-seed coverage CIs (Day 28), Table A final with
significance vs every baseline + Cohen's d effects, the conformal-vs-heuristic ablation asset and the
RQ5 honesty summary (Day 29), and the cross-audit + Team-B manuscript hand-off (Day 30). All reuse the
consolidated Week-3/4 machinery and AK's Day-26/27 modules — no math re-implemented. Days 31–32
(methods subsections + final sign-off) continue from here.

## Review of Days 26–27 (AK's branch) — verdict

**Every number verifies.** Full suite 135 passed + 8 subtests; the three mains reproduce AK's handoff
numbers exactly (separation AUROC 0.4994/0.4763/0.5104 with CIs bracketing 0.5; every Table-A cell;
McNemar sig/sig/ns with UNSW p = 0.353; all-seed coverage 5/5 in band, mean FZR 0.0518/0.0501/0.0508;
per-class 0/31, 0/4, 0/8; Figure 2 in-band); `freeze_results.py --reproduce` returns all 39 scalars to
1e-9; `freeze_integration.py --verify` 34/34. Reproduced on a *different* environment (Python 3.10,
scikit-learn 1.7.2) with identical bytes — the pipeline is environment-robust.

Two hygiene findings, both fixed on this branch:

1. **The committed result artefacts were CIC-only test residue** — `freeze_results.py --verify`
   failed out-of-the-box with 13/16 CHANGED. Cause: the Day-26 freeze round-trip tests call
   `fr.freeze(["CICIoT2023"], ...)`, which runs the three mains **into the real tree**, so a pytest
   run after the freeze overwrote the committed full-trio artefacts with single-dataset outputs
   (not a CRLF issue — the files were LF; the sizes were simply smaller). Fixed:
   `test_freeze_results.py` now redirects the mains' output dirs to tmp (the pattern the Day-26
   table-A/figure-2 tests already used), and the full-trio artefacts were regenerated —
   byte-identical to AK's v1.0 manifest, `--verify` now 0 mismatch, and stays clean after pytest.
2. **One absolute-path leak survived the Day-26 scrub** — `coverage_harness.py` wrote `scores_root`
   as an absolute path, and the committed `w3_02_coverage_verification.json` carried a Windows home
   path. Fixed at source (repo-relative, same convention as the other writers), the committed JSON
   scrubbed surgically (only that field changed), and the Day-21 INTEGRATION package re-frozen:
   34 files, 0 mismatch, thresholds byte-identical.

## What was implemented

1. **Day 28 — Table B (RQ2) FINAL + all-seed coverage CIs** (`week5/scripts/table_b_final.py`,
   `w5_04_table_b.md`). Keeps the Day-24 assembly discipline (canonical cells still trace to the
   Day-19/21/22/23 artefacts, never recomputed) and adds the 5-seed re-split block: pooled KNOWN
   calibration ∪ test re-drawn under seeds 42–46 (Day-23 `fix_splits`), each re-split re-calibrated
   (q = s_(k)) and judged against its own exact band, with the **fixed** zero-day pool scored at each
   re-split's q. Per dataset: achieved-α mean + t-based 95% CI and recall mean + 95% CI (Day-17
   `summarize`). The JSON carries a cross-check that the 5-seed FZR means equal Day-26 Table A's
   all-seed means to 1e-9 (same seeds, same machinery) — it does, on all three datasets.
2. **Day 29 — Table A (RQ1) FINAL: significance vs every baseline + effects**
   (`week5/scripts/table_a_effects.py`, `w5_05_table_a_effects.md`). Each baseline is paired on the
   face it actually shares: XGBoost on closed-set correctness (exact McNemar, Holm m = 3 — identical
   p to Day 26, now with Cohen's h on the accuracy gap and paired d_z on per-sample correctness), and
   every Day-12 novelty head on the KNOWN-split flag-vs-keep decision (Day-25 pairing, Holm m = 8;
   CIC has no OC-SVM). Budgets are NOT matched in the FA family and the report says so: QS-Net sits
   at its conformal α = 0.05, the heads at their shipped Day-12 operating points (2α = 0.10 known-FPR
   budget) — a deployed-behaviour statement, with the like-for-like recall comparison staying in
   Table B. The Day-25 seed-level classical paired-t (with its d_z) and the quantum-arm blocker are
   surfaced, not recomputed.
3. **Day 29 — ablation asset + RQ5 honesty summary** (`week5/scripts/ablation_rq5.py`,
   `w5_06_ablation_rq5.md`). The paper-ready conformal-vs-heuristic asset (Day-20 machinery reused):
   booktabs table + 4-panel figure (`w5_fig3_ablation.png`) — three α-sweep panels plus the small-n
   drill. The honest reading is printed on the asset: at n ≈ 19k all rules land near α and the
   guarantee's value is the *certificate*, the small-n anti-conservatism of the no-+1 heuristic
   (≈ 2× the budget at n = 20), and α-responsiveness (a fixed τ has none). The RQ5 summary
   (`w5_06_rq5_honesty.md`) compiles the Day-25 verdicts (ahead 4 / behind 3 / equivalent 1 /
   unresolved 0 on the dummy) with Δrecall CIs, h, and the seed-level d_z floor — negative rows kept.
4. **Day 30 — cross-audit** (`week5/scripts/cross_audit.py`, `w5_07_cross_audit.md`). Independent
   re-derivation of every headline number from the raw logs — order-statistic threshold, counted
   FZR/coverage/recall, sklearn AUROC vs the repo's Mann-Whitney (two estimators of the same
   quantity), argmax-re-derived predictions (validates the stored `pred_class`/`pred_correct`),
   recounted McNemar cells + the doubled exact tail from `binom.cdf`, the band from the raw
   BetaBinomial pmf — compared against every artefact that quotes each number, including the cells
   PRINTED in the rendered md tables. Plus independent SHA-256 manifest passes, an absolute-path
   leak scan and a CRLF scan. **90 PASS / 0 FAIL / 1 WARN** (the WARN is the pre-existing week-2
   FROZEN drift, documented in a known-issues register rather than hidden).
5. **Day 30 — Team-B hand-off** (`week5/scripts/handover_teamB.py`, `week5/HANDOVER/`). One
   SHA-256-pinned surface (41 files) with per-deliverable status: Tables A/B (skeleton + final),
   Figure 2 + data, the RQ3 panel, the ablation asset, RQ5 + the full Day-25 suite, the coverage
   diagnostics, the audit, and the two upstream freeze manifests pinned by reference. The cut is
   **audit-gated** — `freeze()` refuses to run if `w5_07_cross_audit.json` is not green. `--verify`
   re-hashes (0 mismatch). Repricing on real prototypes re-cuts it as v1.1 with the same asset list.

## What went well

- **Pure reuse again.** Day 28 imports the Day-24 assembly; Day 29 imports the Day-26 rows, the
  Day-25 pairing/effects and the Day-20 ablation; Day 30 reuses the Day-21 hash helpers. The suite
  grew 135 → 162 tests, all green, and the new tests follow the redirect-to-tmp convention.
- **Cross-artifact consistency is now asserted, not assumed** — Table B's 5-seed means vs Table A's,
  Figure 2's points vs both, the frozen scalars vs everything, and the printed md cells vs their
  JSONs are all machine-checked in the audit.
- **The independent re-derivations agreed to float precision everywhere** — including sklearn AUROC
  vs Mann-Whitney U and argmax-re-derived predictions vs the stored interface columns.

## Challenges and issues

1. **The two Day-26/27 findings above** — both fixed, neither affected any number.
2. **A statistics footnote the ablation must carry:** a conformal *Monte-Carlo mean* can sit a hair
   above α at tiny n (expected FZR at n = 20 is 1/21 ≈ 0.048, per-draw sd ≈ 0.044, so a 300-rep mean
   wobbles) — the deterministic fact is the ordering (q_conf ≥ the in-sample percentile, always);
   the per-draw certificate is the band, not the subsample mean. The asset and its tests encode
   exactly that, no stronger claim.
3. **Known-FA budgets differ by design** (α = 0.05 conformal vs the heads' shipped 0.10) — reported
   as a deployed-operating-point comparison; the matched-budget comparison lives in Table B.

## Concerns and recommendations

- **Team B (standing asks, unchanged):** real per-seed QS-Net scores (reprices Tables A/B + Figure 2,
  unlocks the 5-seed paired-t; the d_z floor at n = 5 is ≈ 1.24), and the Day-26 RQ3 hand-off
  (`rq3_scores.parquet` with `role`, `sample_id`, `fid__<class>`, non-squared F).
- **week2 FROZEN drift** (12 changed / 1 missing vs its manifest + the 93-vs-97 docs discrepancy) is
  pre-existing and out of Day-30 scope — recommend the team decides on a week-2 re-freeze or a
  documented supersession note.
- **Days 23–25 still need a task-handoff doc** (AK flagged this too).

## Measured results (Days 28–30, dummy interface, α = 0.05)

**Day 28 — Table B final (canonical | 5-seed mean [95% CI], all 5/5 in band):** achieved α —
CIC 0.0486 | 0.0517 [0.0498, 0.0537]; BoT 0.0530 | 0.0501 [0.0476, 0.0527]; UNSW 0.0463 | 0.0508
[0.0473, 0.0542]. Recall — CIC 0.9998 | 0.9998 [0.9998, 0.9998]; BoT 0.0952 | 0.0928
[0.0912, 0.0945]; UNSW 0.3857 | 0.3929 [0.3884, 0.3975]. Every CI covers the target α.

**Day 29 — Table A effects (QS-Net vs XGBoost):** Δacc/h/d_z — CIC −0.0862 / −0.427 / −0.276 (sig);
BoT −0.0118 / −0.052 / −0.036 (sig); UNSW −0.0054 / −0.013 / −0.009 (ns, p = 0.353). Known-split FA
family (8 pairs, all sig on the dummy): QS-Net ≈ 0.05 vs heads ≈ 0.10 (their 2α design point),
h ≈ −0.17…−0.22. RQ5 counts: ahead 4 / behind 3 / equivalent 1 / unresolved 0.

**Day 30 — audit:** 91 checks, **90 PASS / 0 FAIL / 1 WARN** (week-2 register). Handover: 41 files,
0.59 MB, `--verify` 0 mismatch; RESULTS_FROZEN 16/16 and INTEGRATION 34/34 both verify clean.

## Do not commit
- `../.venv/`, any `__pycache__/` (gitignored); raw dataset archives. *(The `_generated/` results,
  figures, `HANDOVER/`, and the re-frozen `INTEGRATION/` manifest ARE committed, repo convention.)*

## Verification performed
- `python -m pytest week2/tests week3/tests week4/tests week5/tests -q` → **162 passed, 8 subtests**.
- `freeze_results.py --verify` → 16 files, 0 mismatch (and stays clean after a full pytest run).
- `freeze_results.py --reproduce` → 39/39 scalars to 1e-9.
- `freeze_integration.py --verify` → 34 files, 0 mismatch (post re-freeze; thresholds identical).
- `cross_audit.py` → 90 PASS / 0 FAIL / 1 WARN.
- `handover_teamB.py --verify` → 41 files, 0 mismatch.

## Chat update

```text
Team A - Week 5 Days 28 to 30 done, plus the review AK asked for.

Review of Days 26-27: every number reproduces - full suite green, all three mains match the handoff
figures exactly, --reproduce returns all 39 frozen scalars to 1e-9, and INTEGRATION verifies 34/34.
Two hygiene catches, both fixed on this branch: (1) the committed week5 result artefacts were
CIC-only leftovers of the freeze round-trip tests (they run the three mains into the real tree), so
freeze --verify failed on a fresh checkout - the tests now redirect to tmp, the full-trio artefacts
are restored byte-identical to AK's manifest, and verify is clean before AND after pytest; (2) one
absolute-path leak survived the Day-26 scrub (coverage_harness wrote scores_root absolute;
w3_02_coverage_verification.json carried a local Windows path) - fixed at source, scrubbed, and
INTEGRATION re-frozen with identical thresholds.

Day 28 (Table B final): the Day-24 table plus the all-seed coverage CIs - pooled cal/test re-split
under seeds 42-46, each re-split against its own exact band, and the fixed zero-day pool scored at
each re-split's q. Achieved-alpha 5-seed means sit on 0.05 with every CI covering the target and
5/5 in band on all three datasets; the 5-seed means agree with Table A's all-seed check to 1e-9.

Day 29 (Table A final + effects): significance vs every baseline on the face each one shares -
McNemar vs XGBoost on closed-set correctness (same p as Day 26, now with Cohen's h and paired d_z),
and vs every novelty head on known-split flag-vs-keep (Holm m=8; budgets deliberately unmatched:
conformal 0.05 vs the heads' shipped 0.10 - stated on the table). Also the paper-ready
conformal-vs-heuristic ablation (figure + booktabs; the no-+1 heuristic runs ~2x the budget at n=20
while conformal holds) and the compiled RQ5 honesty summary (ahead 4 / behind 3 / equivalent 1 on
the dummy - negative rows kept).

Day 30 (audit + handover): cross-audit re-derives every headline number from the raw logs with
independent implementations (sklearn AUROC vs Mann-Whitney, argmax-re-derived predictions,
recounted McNemar cells, raw BetaBinomial band) and checks every artefact that quotes it, including
the printed md cells - 90 PASS / 0 FAIL / 1 WARN (the WARN is the pre-existing week2 FROZEN drift,
now documented). The Team-B package is cut under week5/HANDOVER: 41 files, SHA-256-pinned,
audit-gated, --verify 0 mismatch; reprices to v1.1 on real prototypes with the same asset list.

Everything quantum is still the dummy interface and tagged provisional; structures, conventions and
the hand-off surface are final. Standing asks to Team B unchanged: per-seed real scores and
rq3_scores.parquet. Full suite 162 tests green. Thanks.
```
