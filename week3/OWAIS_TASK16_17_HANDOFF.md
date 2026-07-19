# Owais — Week 3 Days 16–17 Handoff (Coverage-Verification Harness + Statistical Protocol)

Covers Day 16 (coverage-verification harness + α-sweep 0.01–0.20) and Day 17 (5-seed statistical protocol +
significance dry-run), built on AK's Day-15 CQ-ZDR module and Iwo's Day-13/14 package. Also records the
independent verification of AK's Day-15 numbers he requested.

## Verification of Day 15 (requested by AK — all confirmed)

- Full suite re-run on this machine: **35/35 pass** (24 Iwo + 11 AK).
- `conformal_calibrate.py` re-run, trio @ α = 0.05: **q(CIC) = 0.300551, coverage 0.9514, FZR 0.0486** —
  exact match, BoT/UNSW previews match to the 6th decimal.
- **Iwo freeze inconsistency confirmed as reported:** `freeze_manifest_v1.0.json` pins **97** files
  (handoff says 93) and pins `week2/IWO_DAY13-14_SUMMARY.md`, which is **absent** from the package —
  1 pinned-but-missing file. Iwo: re-run `freeze_package.py` for a self-consistent v1.0.

## What was implemented

1. **Day 16 — `week3/scripts/coverage_harness.py`** (+ report `w3_02_coverage_harness.md`, figure,
   9 tests). Imports AK's conformal math (single source of truth) and adds the verification layer: the
   task's "FZR ≤ α on held-out KNOWN data" is checked against the **exact finite-sample law**
   E ~ BetaBinomial(m, n+1−k, k) (coverage | cal ~ Beta(k, n+1−k); Vovk 2012, A&B 2023 §3.2) — observed
   rate, exact central 99% band, one-sided tail p, verdicts (`expectation_ok` continuity bound vs
   **`finite_sample_ok`** harness gate), `conservative_note` for below-band. α-sweep grid 0.01–0.20
   (task range) × trio → tidy CSV + the headline coverage-curve figure (validity and power panels kept
   separate, per AK's Day-15 note). Real prototypes swap in via `--scores-root/--source`, no code change.
2. **Day 17 — `week3/scripts/stats_protocol.py`** (+ report `w3_03_significance_dryrun.md`, 8 tests).
   The comparison layer on top of Iwo's Day-13 harness: `summarize` (mean/std/t-CI), seed-paired t-test,
   paired **Cohen's d_z**, **exact** two-sided McNemar (row-paired, seed-42 predictions), **Holm–Bonferroni**
   step-down over the declared family. Zero-variance guards make A-vs-A provably null. Standalone
   (scipy-only; no xgboost import), so Team C can reuse it for the selector benchmark as posted.

## Measured results

- **Day 16 headline (α = 0.05, dummy):** CIC FZR 0.0486 (p = 0.73) PASS · **BoT 0.0530 — violates the naive
  bound but p = 0.090 inside the exact band → PASS** (formally resolves AK's Day-15 open item: sampling
  noise, not a coverage miss) · UNSW 0.0463 (p = 0.89) PASS. **Sweep: 60/60 PASS.**
- **Day 17 dry-run:** re-derived **all 78** (dataset, head, metric) cells of `stats_harness.json` —
  0 mismatches; 9 A-vs-A self-tests all t = 0, p = 1, d = 0. Holm over the 9 head-pair tests on zero-day
  AUROC: 3 survive, all |d_z| ≥ 5 (CIC IF > OC-SVM; BoT & UNSW OC-SVM > IF; BoT AE > IF), and CIC AE-vs-IF's
  raw p = 0.011 is correctly killed (p_holm = 0.056). McNemar (IF vs AE, row-paired): CIC p < 1e−300,
  UNSW p = 1.1e−7, **BoT p = 0.36** — a nice case where a seed-level AUROC gap has no per-sample
  thresholded-decision counterpart; the report explains why both views are kept.

## Challenges and issues

1. **The naive Day-16 reading ("assert FZR ≤ α") is statistically wrong** — it fails sound systems ~half
   the time at the boundary. Solved with the exact Beta-Binomial band; documented in w3_02 §1 so the paper
   gates on `finite_sample_ok`, never the raw comparison.
2. **Windows console encoding** — `α` in log lines crashes under cp1252; logs are ASCII, files stay UTF-8.
3. **CIC has no OC-SVM head** (Day-13 scope decision), so its family has 3 pairs like the others minus one;
   the pair list is discovered from the JSON, not hard-coded.
4. **n = 5 seeds is small** — d_z reported beside every p; McNemar provides the row-level second axis.

## Concerns and recommendations

- **Gate the paper's coverage claims on `finite_sample_ok`** (exact, auditable from the sweep CSV);
  keep the expectation bound only as a printed diagnostic.
- **Declare test families before running them** — the dry-run's own family (9 tests) is declared in the
  JSON; QS-NET-vs-baseline tables should do the same in captions.
- **When Team B's real CIC prototypes land:** `coverage_harness.py --scores-root <real> --source real`
  re-verifies validity and re-draws the curve; validity should hold — if it FAILS, the plumbing broke
  exchangeability (prototypes touching calibration rows), which is precisely what the gate is for.
- **Day 18 (next member):** the sweep CSV already carries per-dataset achieved-FZR-vs-α — "coverage table
  v1" is a formatting pass; extension to real prototypes is the `--datasets` flag as they arrive.

## Files added (this handoff)

- `week3/scripts/coverage_harness.py` · `week3/tests/test_coverage_harness.py`
- `week3/scripts/stats_protocol.py` · `week3/tests/test_stats_protocol.py`
- `week3/reports/w3_02_coverage_harness.md` · `week3/reports/w3_03_significance_dryrun.md`
- `week3/reports/figures/w3_02_coverage_curve.png`
- `week3/reports/_generated/w3_02_coverage_verification.json` · `w3_02_alpha_sweep.csv` ·
  `w3_03_significance_dryrun.json` · `w3_03_significance_dryrun.csv`
- `week3/README.md` (Days 16–17 rows + results), this handoff.

## Verification performed

- `python -m pytest week2/tests week3/tests` → **52 passed** (24 + 11 + 9 + 8) on Python 3.14/scipy 1.17;
  suite also green pre-change (35) — no regressions.
- `coverage_harness.py` canonical run → 60/60 PASS, figure rendered and visually checked.
- `stats_protocol.py` canonical run → 78-cell cross-check 0 mismatches, sanity + Holm + McNemar as above.
- **Manifest left untouched (AK's canonical 665-pin version).** Trial regeneration on this git checkout
  showed it would silently drop the **198 raw-data pins** (`datasets/*/raw/*`, source zips — 41 GB that
  correctly lives outside git) while adding nothing (week3 code/reports are outside the manifest's data
  scope). Those pins are source provenance — dropping them loses information. **Team decision needed for
  the git era:** either document that `--verify` on a fresh clone reports those 198 as *expected-missing*
  (raw data is re-downloaded per week-1 README), or add a `--scope git` flag to `make_manifest.py`.
  Flagged rather than unilaterally resolved.
