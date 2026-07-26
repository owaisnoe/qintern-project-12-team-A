# Week 4 · Day 23 — Live Coverage on the Integrated Pipeline + Exchangeability Audit

Task (`WEEK 4.pdf`): *Run coverage verification live on the integrated pipeline; confirm achieved false-zero-day rate ≤ α. Log any exchangeability violations and fix splits if needed.* Deliverables: **live coverage result** + **exchangeability audit**. Seed 42 · primary α = 0.05 · scores: **dummy** (`week2/interface/dummy_scores`).

This is not a Day-16 rerun, and it does not re-implement Day 22. Day 16 *derives* a threshold and checks it. Day 22 ([`w4_03_conformal_integration.md`](w4_03_conformal_integration.md)) is the adapter that applies the **frozen** q and emits per-row decisions. Day 23 **calls that adapter** (`conformal_integration.integrate_dataset`) so the rate verified here comes off the same code path as the deployed decisions — then adds the statistical verdict Day 22 does not give, and audits the assumption the guarantee rests on.

## 0. Contract provenance (what these numbers are attributable to)

- Frozen surface: `INTEGRATION/integration_manifest_v1.0.json` v1.0 · **34 pinned files** · frozen `2026-07-26T10:55:48Z`.
- Re-hashed live: missing **0**, changed **0** → contract **INTACT**.
- Frozen thresholds: `week4/INTEGRATION/frozen_thresholds.json` covering **CICIoT2023, BoT-IoT, UNSW-NB15**.

The Day-21 manifest pins an explicit whitelist — the Day-15/16/17/19 code modules, the score interface Team B fills, the packaged coverage/recall/significance outputs, and the two frozen JSONs. Because it is a whitelist rather than a directory sweep, later work (this module, the Day-24 reports) never registers as drift: a `MISSING`/`CHANGED` line is a real break, with no `ADDED` noise to filter. Re-cut as v1.1 when Team B's real numbers land.

## 1. Live coverage result — achieved FZR at the frozen q

Produced by the Day-22 adapter, whose own three gates (score contract `s = 1 − max_c F`, frozen-threshold provenance, coverage reproduces the freeze) pass as a precondition of these rows existing at all — the adapter raises on failure.

| Dataset | frozen q | n_cal | m_test | false flags | **achieved FZR** | ≤ α? | exact 99% band | p(E ≥ e) | verdict |
|---|---:|---:|---:|---:|---:|:--:|---|---:|---|
| CICIoT2023 | 0.300551 | 18,883 | 18,883 | 918 | **0.0486** | ✅ | [0.0443, 0.0559] | 0.732 | **PASS** |
| BoT-IoT | 0.262934 | 18,591 | 18,591 | 986 | **0.0530** | ⚠ | [0.0443, 0.0559] | 0.090 | **PASS** |
| UNSW-NB15 | 0.383380 | 10,112 | 10,086 | 467 | **0.0463** | ✅ | [0.0423, 0.0581] | 0.887 | **PASS** |

**Achieved false-zero-day rate ≤ α on 2/3 datasets; inside the exact finite-sample band on 3/3.** The band is the verdict, `≤ α` is the headline: the empirical rate fluctuates around (n+1−k)/(n+1), so a bare `≤ α` assertion fails on sound systems roughly half the time (Day 16 §law). A dataset that is ≤ α but outside the band would be over-conservative — also worth eyes.

### Frozen q vs repriced q (threshold drift)

| Dataset | frozen q | repriced q (live cal) | \|Δq\| | rounding only? | n_cal matches | FZR frozen | FZR repriced | zero-day recall |
|---|---:|---:|---:|:--:|:--:|---:|---:|---:|
| CICIoT2023 | 0.300551 | 0.300551 | 7.00e-08 | yes | yes | 0.0486 | 0.0486 | 0.9998 |
| BoT-IoT | 0.262934 | 0.262934 | 1.20e-07 | yes | yes | 0.0530 | 0.0530 | 0.0952 |
| UNSW-NB15 | 0.383380 | 0.383380 | 4.10e-07 | yes | yes | 0.0463 | 0.0463 | 0.3857 |

`frozen_thresholds.json` publishes q rounded to 6 dp. That rounding is a real (small) difference between the calibration-time flag count and the deployed one — it is reported rather than hidden, and it is the only source of drift on a dummy-vs-dummy run. A |Δq| above 0.0001 on real prototypes means the interface was repriced and the frozen package must be re-cut, not patched.

### Do the decisions on disk agree?

The adapter recomputes decisions in-process; Day 24 and Team B read the per-row CSVs it wrote earlier. Those two must not diverge:

| Dataset | decisions CSV | rows | flags on disk | flags in-process | agrees |
|---|---|---:|---:|---:|:--:|
| CICIoT2023 | `week4/reports/_generated/w4_03_decisions_CICIoT2023.csv` | 29,867 | 918 | 918 | ✅ |
| BoT-IoT | `week4/reports/_generated/w4_03_decisions_BoT-IoT.csv` | 19,274 | 986 | 986 | ✅ |
| UNSW-NB15 | `week4/reports/_generated/w4_03_decisions_UNSW-NB15.csv` | 11,302 | 467 | 467 | ✅ |

## 2. Exchangeability audit

Six inferential tests per dataset, Holm step-down over the declared family (18 cells, α = 0.05). A rejection is a **violation**: the conformal guarantee is void for that split, and the achieved FZR above stops meaning anything.

The first row per dataset — conformal p-value uniformity — is **descriptive, not in the family**, and that is a deliberate correction. `p_i = (1 + #{j: s_j ≥ s_i})/(n+1)` is the textbook exchangeability audit, but every p_i is computed against the *same* calibration set, so the p-values are exchangeable rather than independent and the one-sample KS-against-U(0,1) null is far too tight: measured on this interface it rejects on **~37% of genuinely exchangeable re-splits** (60 pooled re-splits of BoT-IoT, raw p ≤ 0.05). It is also redundant — sup_t |F_p(t) − t| equals the two-sample KS statistic up to 1/(n+1). So the statistic and the shape are reported (row below, and the figure's ECDF panel) while `cal_vs_test_ks2` carries the inference under the correct two-sample null.

| Dataset | Test | statistic | effect | p (raw) | p (Holm) | violation |
|---|---|---:|---:|---:|---:|:--:|
| CICIoT2023 | `conformal_pvalue_uniformity (descriptive)` | 0.006525 | 0.007 (KS D) | — | — | ok |
| CICIoT2023 | `cal_vs_test_ks2` | 0.006567 | 0.007 (KS D) | 0.808 | 1 | ok |
| CICIoT2023 | `cal_vs_test_mannwhitney` | 1.784e+08 | 0.001 (rank-biserial r) | 0.924 | 1 | ok |
| CICIoT2023 | `class_mix_chi2` | 0 | 0.000 (Cramer's V) | 1 | 1 | ok |
| CICIoT2023 | `flag_rate_by_class_chi2` | 12.08 | — | 0.673 | 1 | ok |
| CICIoT2023 | `index_drift_cal_spearman` | -0.001592 | -0.002 (Spearman rho) | 0.827 | 1 | ok |
| CICIoT2023 | `index_drift_test_spearman` | -0.002794 | -0.003 (Spearman rho) | 0.701 | 1 | ok |
| BoT-IoT | `conformal_pvalue_uniformity (descriptive)` | 0.011 | 0.011 (KS D) | — | — | ok |
| BoT-IoT | `cal_vs_test_ks2` | 0.01103 | 0.011 (KS D) | 0.207 | 1 | ok |
| BoT-IoT | `cal_vs_test_mannwhitney` | 1.715e+08 | -0.008 (rank-biserial r) | 0.197 | 1 | ok |
| BoT-IoT | `class_mix_chi2` | 0 | 0.000 (Cramer's V) | 1 | 1 | ok |
| BoT-IoT | `flag_rate_by_class_chi2` | 5.693 | — | 0.128 | 1 | ok |
| BoT-IoT | `index_drift_cal_spearman` | -0.003108 | -0.003 (Spearman rho) | 0.672 | 1 | ok |
| BoT-IoT | `index_drift_test_spearman` | -0.01368 | -0.014 (Spearman rho) | 0.0622 | 1 | ok |
| UNSW-NB15 | `conformal_pvalue_uniformity (descriptive)` | 0.01244 | 0.012 (KS D) | — | — | ok |
| UNSW-NB15 | `cal_vs_test_ks2` | 0.01239 | 0.012 (KS D) | 0.418 | 1 | ok |
| UNSW-NB15 | `cal_vs_test_mannwhitney` | 5.146e+07 | 0.009 (rank-biserial r) | 0.261 | 1 | ok |
| UNSW-NB15 | `class_mix_chi2` | 0.3348 | 0.004 (Cramer's V) | 1 | 1 | ok |
| UNSW-NB15 | `flag_rate_by_class_chi2` | 6.557 | — | 0.161 | 1 | ok |
| UNSW-NB15 | `index_drift_cal_spearman` | 0.0129 | 0.013 (Spearman rho) | 0.195 | 1 | ok |
| UNSW-NB15 | `index_drift_test_spearman` | 0.01182 | 0.012 (Spearman rho) | 0.235 | 1 | ok |

**No exchangeability violations.** Every cell survives Holm; the split-conformal guarantee holds as stated, so the Section-1 coverage numbers are valid, not merely arithmetic.

The p-value ECDF panel of `figures/w4_04_exchangeability.png` is the picture of this table: on the diagonal ⇔ p ~ U(0,1) ⇔ exchangeable. Note the identity the audit asserts at runtime — `p_i ≤ α ⟺ s_i > q` — so the audit tests exactly the object the pipeline flags on, not a parallel re-derivation.

One row deserves a caveat rather than credit: `class_mix_chi2` is exactly 0 on CICIoT2023 and BoT-IoT because the Day-14 dummy generator mirrors the calibration class counts into test row-for-row — a perfect class match is an artifact of the placeholder interface, not evidence about Team B's splits. UNSW-NB15's small non-zero χ² is the real Day-9 partition and is the one to watch when real scores land.

### Diagnostics (no p-value — these bound the *exact band*, not the guarantee)

| Dataset | tie frac (cal / test) | ties break exact band | fidelity min/max | in [0,1] | mean conformal p |
|---|---|:--:|---|:--:|---:|
| CICIoT2023 | 0.00e+00 / 0.00e+00 | no | 0.0034 / 0.9999 | ✅ | 0.5003 |
| BoT-IoT | 2.69e-04 / 1.61e-04 | no | 0.0064 / 0.9999 | ✅ | 0.4962 |
| UNSW-NB15 | 0.00e+00 / 0.00e+00 | no | 0.0071 / 0.9987 | ✅ | 0.5046 |

Ties make the exact BetaBinomial band conservative (it assumes continuous scores); a fidelity range outside [0,1] — or a suspiciously compressed one — is the F²-vs-F trap from Day 20. Mean conformal p should sit at 0.5.

## 3. Does the audit have power? (injected-violation drills)

The Day-14 dummy interface is i.i.d. by construction, so a clean audit proves nothing about the audit. Each drill injects a known break, re-runs the p-bearing subset of the battery, then applies the pooled re-split remediation over 5 seeds (42–46):

| Dataset | violation | FZR clean → violated | audit caught it | coverage broke | mean FZR after `fix_splits` | audits clean | coverage restored |
|---|---|---:|:--:|:--:|---:|:--:|:--:|
| CICIoT2023 | `cal_trim` | 0.0486 → **0.0971** | ✅ | ✅ | 0.0509 | 5/5 | 5/5 |
| CICIoT2023 | `test_shift` | 0.0486 → **0.0931** | ✅ | ✅ | 0.0514 | 5/5 | 5/5 |
| CICIoT2023 | `class_mix` | 0.0486 → **0.0467** | ✅ | — (in band) | 0.0503 | 4/5 | 5/5 |
| BoT-IoT | `cal_trim` | 0.0530 → **0.1003** | ✅ | ✅ | 0.0506 | 4/5 | 5/5 |
| BoT-IoT | `test_shift` | 0.0530 → **0.1036** | ✅ | ✅ | 0.0509 | 5/5 | 5/5 |
| BoT-IoT | `class_mix` | 0.0530 → **0.0504** | ✅ | — (in band) | 0.0496 | 3/5 | 5/5 |
| UNSW-NB15 | `cal_trim` | 0.0463 → **0.0947** | ✅ | ✅ | 0.0482 | 5/5 | 5/5 |
| UNSW-NB15 | `test_shift` | 0.0463 → **0.0928** | ✅ | ✅ | 0.0507 | 5/5 | 5/5 |
| UNSW-NB15 | `class_mix` | 0.0463 → **0.0483** | ✅ | — (in band) | 0.0495 | 5/5 | 5/5 |

Injections (the exact per-dataset parameters are in the JSON's `description`): `cal_trim` — the top of the calibration score distribution is trimmed away ('outlier cleaning'), so q lands below where the guarantee needs it · `test_shift` — every known test score is nudged up by delta — deployment drift, inputs harder than calibration ever saw · `class_mix` — the test window over-represents one known class (every other class thinned), the classic split bug

**All injected violations are caught.** Two of the three also break coverage outright: trimming the calibration tail or shifting the test scores roughly *doubles* the achieved false-alarm rate and pushes it clean out of the exact band. `class_mix` is the instructive one — the audit flags it decisively (class-mix χ² p ≈ 1e-209) while the **marginal** FZR stays inside the band. That is not a miss: marginal conformal is class-agnostic, so a class-mix skew invalidates the *assumption* without necessarily moving the *pooled* rate. It is exactly the failure a coverage-only check cannot see, and the reason this audit exists alongside Section 1.

Remediation is judged over 5 re-split seeds rather than one: the drill's own 3-test family controls FWER at 0.05, so ~1 in 20 genuinely exchangeable re-splits shows a surviving flag by chance, and a single unlucky draw must not read as a failed fix.

**Caveat that must travel with the remediation.** A pooled re-split repairs *split-induced* non-exchangeability (a filtered calibration set, a skewed class mix) — there the pool is homogeneous and re-drawing the boundary is the right fix, upstream in `week2/scripts/make_partitions.py`. It also makes `test_shift` *look* fixed, because calibration and test become exchangeable draws from the shifted mixture — but that mixture is not the deployment distribution. **A real deployment shift is answered by recalibrating on fresh data, never by re-splitting.** `fix_splits` is opt-in (`--fix-splits`) for exactly this reason; it is never applied silently.

## Bottom line

Run live through the Day-22 adapter, the frozen threshold holds achieved false-zero-day rate inside the exact finite-sample band on 3/3 integrated dataset(s) (CICIoT2023, BoT-IoT, UNSW-NB15), and the exchangeability assumption behind that number survives a Holm-corrected audit over 18 cells spanning 3 dataset(s) with zero violations. All quantum-side numbers ride the Day-14 **dummy** interface and are placeholders — the same command reprices them against Team B's prototypes (`--source real --scores-root <dir>`) with no code change, and that rerun is the one that goes in the paper.

Figure: `figures/w4_04_exchangeability.png` (written) · CSV: `_generated/w4_04_live_coverage.csv`, `_generated/w4_04_exchangeability_audit.csv` · JSON: `_generated/w4_04_live_coverage.json`.
