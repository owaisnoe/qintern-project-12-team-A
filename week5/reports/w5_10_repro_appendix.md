# Week 5 · Day 31 (b) — Reproducibility Appendix: the Statistics Pipeline

Task (`qi26_12_Week_5.pdf`, Team A): *prepare the reproducibility appendix for the statistics pipeline.*
Deliverable: **repro appendix (stats)**.

This appendix is the artifact Day 32 signs off against ("every RQ2 / RQ5 number and Figure 2 reproducible
from one script"). It states what is fixed, what is verified, how to re-run it, and — deliberately — where
byte-level reproducibility stops and numerical reproducibility takes over. A LaTeX rendering ships as
[`_generated/w5_10_repro_appendix.tex`](_generated/w5_10_repro_appendix.tex). The methods text these
procedures implement is [`w5_09_methods_data_stats.md`](w5_09_methods_data_stats.md).

Everything below was **measured**, not inherited from an earlier report: first on 2026-08-01 by re-running
the pipeline from a clean checkout of `main` @ `c5e40e9`, then re-measured on 2026-08-04 after Day 32 added
the `signoff.py` gate and closed the open item in §9.1. The verification log in §6 is the current run.

---

## 1. Scope

The statistics pipeline is Team A's chain from frozen partitions to the manuscript's tables and figures:

```
week2/partitions/              (frozen data partitions, seed 42)
        │
        ├── week2/interface/dummy_scores/         score interface (Team B fills this)
        │
week3/scripts/conformal_calibrate.py    s = 1 - max_c F ; q = s_(k)     [calibration]
week3/scripts/coverage_harness.py       exact Beta-Binomial band         [coverage]
week3/scripts/stats_protocol.py         paired t / McNemar / Holm / d_z  [significance]
week4/scripts/{conformal_integration,live_coverage,zeroday_recall,significance}.py
week5/scripts/{disentanglement,table_a,figure2_coverage,table_b_final,
               table_a_effects,ablation_rq5,cross_audit,handover_teamB}.py
        │
        ├── Table A · Table B · Figure 2 · RQ3 panel · ablation · RQ5 summary
        │
week5/scripts/signoff.py        the single Day-32 entry point that gates all of the above (5 gates)
```

Model training (MAQT prototypes, Team B) and feature selection (Team C) are outside this scope; they enter
through the score interface described in §8.

## 2. Environment

**Reference environment** — the repo virtualenv, which is the environment of record:

| Component | Version |
|---|---|
| Python | 3.12.12 |
| numpy | 2.1.3 |
| pandas | 2.2.3 |
| scipy | 1.14.1 |
| scikit-learn | 1.8.0 |
| matplotlib | 3.9.2 |
| xgboost | 3.2.0 |
| pyarrow | 18.1.0 |
| joblib | 1.5.3 |
| pytest | 9.1.1 |

```bash
source .venv/bin/activate     # Python 3.12
```

**Verified elsewhere.** The Day-30 cross-audit reproduced all 39 frozen scalars and every manifest hash
under Python 3.10.12 / scikit-learn 1.7.2, and the run logged in §6 reproduced them under Python 3.12.12 /
scikit-learn 1.8.0 on macOS (darwin, freetype 2.6.1). The pipeline is environment-robust **numerically**;
see §7 for the precise sense in which it is not environment-robust **byte-wise**.

## 3. Determinism contract

| Quantity | Value | Where fixed |
|---|---|---|
| Partition seed | 42 | `week2/scripts/make_partitions.py` (inherited from the Week-1 QADCP) |
| Primary α | 0.05 | every module's `--alpha` default |
| Seed convention (multi-seed) | 42, 43, 44, 45, 46 | all-seed coverage, 5-seed CIs, paired-*t* |
| α-sweep | 0.01 → 0.20 step 0.01 | `--sweep 0.01 0.20 0.01` |
| Benchmark trio | CICIoT2023, BoT-IoT, UNSW-NB15 | `TRIO` in `conformal_calibrate.py` |
| Qubit budget | 8 | QADCP angle-encoding budget |
| Fidelity convention | non-squared Uhlmann *F* | `week4/INTEGRATION/interface_contract.json` |
| Conformal mode | marginal | `--mode marginal` (default) |

There is no stochastic element in the statistics pipeline itself: given the partitions and a score file, the
threshold, band, coverage and every test statistic are deterministic functions of the inputs. The seeds
above index **re-splits** (a deliberate resampling of the calibration/test boundary to test stability), not
model initialisations.

## 4. One-command rerun

```bash
source .venv/bin/activate

# --- Days 26-27: the frozen result surface -----------------------------------
python week5/scripts/disentanglement.py  --datasets CICIoT2023 BoT-IoT UNSW-NB15 --alpha 0.05
python week5/scripts/table_a.py          --datasets CICIoT2023 BoT-IoT UNSW-NB15 --alpha 0.05
python week5/scripts/figure2_coverage.py --alpha 0.05 --sweep 0.01 0.20 0.01

# --- Days 28-29: final tables + ablation -------------------------------------
python week5/scripts/table_b_final.py    --datasets CICIoT2023 BoT-IoT UNSW-NB15 --alpha 0.05
python week5/scripts/table_a_effects.py  --datasets CICIoT2023 BoT-IoT UNSW-NB15 --alpha 0.05
python week5/scripts/ablation_rq5.py     --alpha 0.05 --sweep 0.01 0.20 0.01

# --- Day 30: audit + handover ------------------------------------------------
python week5/scripts/cross_audit.py
python week5/scripts/handover_teamB.py

# --- verification gates ------------------------------------------------------
python week5/scripts/freeze_results.py    --verify      # 16 files, expect 0 mismatch
python week4/scripts/freeze_integration.py --verify     # 34 files, expect 0 mismatch
python week5/scripts/handover_teamB.py     --verify     # 41 files, expect 0 mismatch
python week5/scripts/freeze_results.py    --reproduce   # 39 scalars, expect 0 mismatch @ 1e-9
python -m pytest week2/tests week3/tests week4/tests week5/tests -q

# --- Day 32: the single sign-off entry point ---------------------------------
python week5/scripts/signoff.py                         # 324 checks: reproduce/freeze/complete/neutral/audit
python week5/scripts/signoff.py --tol 0                 # bit-exact variant; reproduces the §7 ULP finding
```

`signoff.py` is the "one script" the Day-32 task asks for and supersedes the block above for verification
purposes: it re-runs the five result mains itself. The individual commands remain the way to *regenerate*
the committed artifacts; `signoff.py` never writes to them.

**Measured wall-clock** (reference environment, §2). The stages below are the seven result modules; the
freeze verifiers and `handover_teamB.py` are not included in the 57 s total.

| Stage | Time |
|---|---:|
| `disentanglement.py` | 38 s |
| `table_a.py` | 2 s |
| `table_b_final.py` | 1 s |
| `table_a_effects.py` | 2 s |
| `figure2_coverage.py` | 2 s |
| `ablation_rq5.py` | 2 s |
| `cross_audit.py` | 10 s |
| **full result chain** | **57 s** |
| test suite (182 tests) | 73 s |

## 5. Artifact map

| Manuscript object | Producing script | Machine-readable artifacts |
|---|---|---|
| Table A (RQ1) skeleton | `week5/scripts/table_a.py` | `w5_02_table_a.{md,tex,json,csv}`, `w5_02_per_class_fzr.csv` |
| Table A final + effects | `week5/scripts/table_a_effects.py` | `w5_05_table_a.{md,tex}`, `w5_05_table_a_effects.{json,csv}`, `w5_05_known_fa.csv` |
| Table B (RQ2) final + CIs | `week5/scripts/table_b_final.py` | `w5_04_table_b.{md,tex,json,csv}`, `w5_04_allseed_ci.csv` |
| Figure 2 (coverage headline) | `week5/scripts/figure2_coverage.py` | `figures/w5_fig2_coverage.png`, `w5_03_figure2.json`, `w5_03_figure2_data.csv` |
| RQ3 disentanglement panel | `week5/scripts/disentanglement.py` | `w5_01_disentanglement.{json,csv}` |
| Conformal-vs-heuristic ablation | `week5/scripts/ablation_rq5.py` | `w5_06_ablation.{md,tex,csv}`, `w5_06_small_n.csv`, `figures/w5_fig3_ablation.png` |
| RQ5 honesty summary | `week5/scripts/ablation_rq5.py` | `w5_06_rq5_honesty.md` |
| Coverage diagnostics | `week4/scripts/live_coverage.py` | `w4_04_live_coverage.{json,csv}`, `w4_04_exchangeability_audit.csv` |
| Audit of all of the above | `week5/scripts/cross_audit.py` | `w5_07_cross_audit.{json,csv}` (91 checks) |
| Final sign-off (Day 32) | `week5/scripts/signoff.py` | `w5_11_signoff.{json,csv}` (324 checks) |

All paths are relative to `week5/reports/_generated/` unless the table says otherwise.

## 6. Verification gates and measured results

Three independent SHA-256 freezes pin the pipeline's state, each with a `--verify` that re-hashes:

| Freeze | Scope | Files | Result (2026-08-01) |
|---|---|---:|---|
| `week4/INTEGRATION/` | calibration rule, score schema, primary α, per-dataset thresholds | 34 | **VERIFY OK — 0 mismatch** |
| `week5/RESULTS_FROZEN/` | Day-26/27 result surface + the three result modules | 16 | **VERIFY OK — 0 mismatch** |
| `week5/HANDOVER/` | the Team-B manuscript package | 41 | **VERIFY OK — 0 mismatch** |

Beyond hashing, two stronger gates:

- **`signoff.py`** (Day 32) is the single entry point: it re-runs the **five** result mains with their
  outputs sandboxed and diffs **every** extracted scalar against the committed artifact that quotes it,
  spanning RQ1, RQ2, RQ3, RQ5 and Figure 2 — then verifies the three manifests, checks deliverable
  completeness, runs the Day-30 cross-audit, and asserts it changed no pinned artifact while running.
  Measured: **324 checks, 324 PASS / 0 FAIL**. Of the 289 scalar checks, **204 are recomputed** from the
  raw scores on the run and **85 are pass-throughs** the emitting module reads from an upstream frozen
  artifact; the sign-off tags each one and reports the split rather than pooling it, because for a
  pass-through the check proves the assembly path is stable, not that the numeric re-derives. Those are
  covered instead by the cross-audit's independent implementation, which the sign-off runs as its own gate.
- **`freeze_results.py --reproduce`** re-runs the three deterministic result mains and asserts that all
  **39 pinned headline scalars** return to within 1e-9. Measured: **39 scalars, 0 mismatch (tol 1e-9)**.
  Note the scope difference: this check covers RQ1, RQ3 and Figure 2 only — **RQ2 and RQ5 are not in the
  39**, which is why Day 32 added the wider gate above.
- **`cross_audit.py`** re-derives every headline quantity from the raw inputs with an *independent*
  implementation — order-statistic threshold, hand-counted flags, sklearn AUROC cross-checked against
  Mann-Whitney, argmax-re-derived predictions, recounted McNemar cells, raw Beta-Binomial pmf — and compares
  against every artifact that quotes it, including the numbers printed in the rendered tables. Measured:
  **90 PASS · 0 FAIL · 1 WARN** over 91 checks. Exact-copy scalars are held to 1e-9; independently
  re-implemented estimators to 5e-5 at the 4-dp reporting precision.

Two structural gates are also worth recording, because both were failures caught earlier and fixed:

- **LF gate.** The freeze refuses to pin any text file containing a CRLF. Combined with the repo-root
  `.gitattributes` (`* text=auto eol=lf`, binaries pinned), this makes a fresh clone byte-identical on any
  OS, so `--verify` passes off a Windows checkout.
- **Test-isolation gate.** The freeze round-trip tests redirect the result mains to `tmp_path` instead of
  the real tree. Without it, running the suite silently rewrote the committed artifacts with whichever
  `--datasets` list the last test passed. Verified in this run: **`pytest` leaves the working tree clean**
  (182 passed, 8 subtests passed, no modified files afterwards).
- **Sandbox gate (added Day 32).** The same redirection now applies to `--reproduce` and to `signoff.py`'s
  G1, via `freeze_results.sandboxed_outputs()`. Re-running the mains to *check* the numbers no longer
  rewrites the artifacts being checked, which is what makes the sign-off's tree-neutrality gate meaningful
  rather than circular. This closes §9.1 as originally written.

## 7. Reproducibility is numerical, not byte-level — and the distinction is load-bearing

This is the appendix's most important caveat, and it is stated rather than papered over.

**Re-running the pipeline reproduces every number, but not every byte.** Running the full result chain in
the reference environment against the committed artifacts leaves **9 files modified**:

| File | Nature of the difference |
|---|---|
| `w5_02_table_a.json` | McNemar exact-binomial tail, last 1–2 ULP |
| `w5_05_table_a_effects.{json,csv}` | same, last 1–2 ULP |
| `w5_05_known_fa.csv` | same, last 1–2 ULP |
| `w5_07_cross_audit.{json,csv}` + `w5_07_cross_audit.md` | same, plus the embedded environment string |
| `figures/w5_fig2_coverage.png` | PNG rasterization |
| `figures/w5_fig3_ablation.png` | PNG rasterization |

The scalar differences are at the floating-point noise floor. For example, the BoT-IoT McNemar doubled exact
tail is `7.26273412199973e-07` as committed and `7.26273412199952e-07` when recomputed — an absolute
difference of **2.1e-20**, a relative difference of ~3e-14, arising from summation order in
`scipy.stats.binom.cdf` across scipy/Python builds. Every verdict, every significance marker and every
reported digit is unchanged; the cross-audit still passes all 91 checks, because its tolerances are set at
the reporting precision rather than at bit-equality.

Two consequences follow, and both should be understood before Day 32's sign-off:

1. **No rendered table changes.** Every `.md` and `.tex` table under `_generated/` is byte-identical after
   a full re-run, because they are rendered at 2–4 significant figures. The manuscript-facing surface is
   byte-stable; only the full-precision machine-readable mirrors drift.
2. **The PNGs are not byte-reproducible across machines.** Both figures re-render at a different byte length
   (e.g. Figure 2 at 159,629 bytes as committed vs 149,363 bytes here) under the *same* matplotlib 3.9.2,
   because glyph rasterization depends on the platform freetype build. The **plotted data is identical** —
   `w5_03_figure2_data.csv` is byte-for-byte unchanged by the re-run — so this is a rendering difference,
   not a result difference.

The honest formulation for the manuscript is therefore: *the statistics pipeline is deterministic and
reproduces every reported quantity to 1e-9 across Python 3.10–3.12 and scikit-learn 1.7–1.8; the SHA-256
manifests pin the exact artifact bytes produced by the reference environment, and are the correct gate for
detecting unintended change, not a claim that an arbitrary machine will re-emit identical bytes.*

## 8. Repricing on real prototypes

Every module is source-agnostic: it recomputes *s* = 1 − max_c `fid__c` from the fidelity vector, so real
scores drop in at the same schema with no code change.

```bash
python week5/scripts/disentanglement.py  --source real --scores-root <dir>
python week5/scripts/table_a.py          --source real --scores-root <dir>
python week5/scripts/figure2_coverage.py --source real --scores-root <dir>
python week5/scripts/table_b_final.py    --source real --scores-root <dir>
python week5/scripts/table_a_effects.py  --source real --scores-root <dir>
python week5/scripts/ablation_rq5.py     --source real --scores-root <dir>
python week5/scripts/cross_audit.py      --source real --scores-root <dir>
python week5/scripts/handover_teamB.py                  # re-cut the package as v1.1
```

Requirements on `<scores-root>/<dataset>/`: one row per partition row with `fid__<class>` columns carrying
**non-squared** Uhlmann fidelity (take `sqrt()` of PennyLane/Qiskit's *F*²); prototypes ρ*_c* built from the
**train** split only; and for RQ3, `rq3_scores.parquet` with `role ∈ {clean_known, adv_known, true_zeroday}`
plus `sample_id`. Expected behaviour after the swap: **validity should hold** (the band is score-agnostic),
and a coverage FAIL means exchangeability was broken in the plumbing — most likely prototypes fit on
calibration rows — rather than that fidelity is a poor score. **Power will change**, and that is the open
empirical question the swap answers.

## 9. Known-issues register

Stated, not hidden — the same convention the Day-30 audit uses.

1. ~~**`--reproduce` dirties the working tree, so a subsequent `--verify` fails.**~~ **RESOLVED on Day 32.**
   As written on Day 31: `freeze_results.py --reproduce` re-ran the three result mains *into the real tree*
   to compare scalars, rewriting the artifacts it was checking; the scalar check passed (0/39 mismatch) but
   the two ULP- and rasterization-drifting files from §7 were left modified and `--verify` then reported 2
   CHANGED. Day 32 added `freeze_results.sandboxed_outputs()`, a context manager that redirects the mains'
   output dirs to a temp tree for the duration of the re-run — the same pattern `test_freeze_results.py`
   already used. Verified after the fix: `--reproduce` returns 39/39 scalars and leaves the working tree
   clean, and `--verify` immediately afterwards reports 0 mismatch. The finding is kept on the record
   rather than deleted, because it is what motivated the sign-off's tree-neutrality gate.
2. **`cross_audit.md` is self-modifying.** The report embeds the environment it ran under, so re-running the
   audit on a different machine rewrites that line. Expected, but it means the audit report cannot be pinned
   by hash across environments.
3. **`week2/FROZEN` drift (pre-existing, the Day-30 WARN).** 13 deviations: the RQ3 eval files were
   regenerated after the Day-14 freeze, the README evolved, and a summary document was renamed into two
   handoff files; the docs also disagree on 93 vs 97 pinned files. Re-cutting that freeze is a Week-2 scope
   decision for the team, not something to change silently during writing week.
4. **Every quantum-side number is provisional.** All QS-Net cells ride the Day-14 dummy fidelity interface
   and are marked ‡ throughout. They validate the *machinery*, not detection quality.
5. **n = 5 seeds.** Paired *t*-tests are exact only under normally distributed seed differences; this is why
   an effect size accompanies every *p*, why McNemar provides a second row-level axis over thousands of
   pairs, and why the d_z ≈ 1.24 detection floor is stated explicitly.
6. **Ties and discreteness.** The exact Beta-Binomial band assumes continuous scores; heavy ties make the
   `s > q` rule conservative. Measured tie fractions are ≤ 2.7e-4 and do not break the band, and below-band
   excursions are reported rather than failed.

## 10. Checklist for the Day-32 sign-off

- [x] Partitions deterministic under seed 42 and asserted in-script
- [x] Calibration known-class only; zero-day never used for fitting or calibration
- [x] Three SHA-256 freezes verify with 0 mismatch (34 + 16 + 41 files)
- [x] 39 headline scalars reproduce to 1e-9 from a re-run of the result mains
- [x] 91 cross-audit checks re-derived independently: 90 PASS / 0 FAIL / 1 documented WARN
- [x] Full test suite green and artifact-neutral (182 passed, working tree clean afterwards)
- [x] Full result chain runs in 57 s from the reference environment
- [x] Rendered `.md` / `.tex` tables byte-stable across a full re-run
- [x] `--reproduce` made tree-neutral (§9.1) — closed Day 32 via `sandboxed_outputs()`
- [x] **One script** covers every RQ2 / RQ5 number and Figure 2: `signoff.py`, 324/324 checks
      (204 scalars recomputed on the run; the 85 pass-through cells re-derived by the cross-audit gate)
- [x] All Team-A deliverables present and non-empty (30 files across 9 groups, gate G3)
- [ ] Repriced on Team B's real prototypes and freezes re-cut as v1.1 — blocked on real scores
