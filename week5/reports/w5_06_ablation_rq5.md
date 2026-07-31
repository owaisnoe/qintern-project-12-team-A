# Week 5 · Day 29 — Conformal Ablation Asset + RQ5 Honesty Summary

Task (`qi26_12_Week_5.pdf`): *produce the conformal-vs-heuristic ablation figure/table (shows the guarantee's value); compile the RQ5 honesty summary (where quantum helps / does not).* Seed 42 · α = 0.05 · trio CICIoT2023, BoT-IoT, UNSW-NB15 · quantum scores: **dummy**.

## The ablation asset

Machinery is Day-20's (`heuristic_ablation.py` — reused, not re-implemented); Day 29 re-runs it at the primary α and renders the paper-ready assets: [`_generated/w5_06_ablation.md`](_generated/w5_06_ablation.md) + [`.tex`](_generated/w5_06_ablation.tex) + `figures/w5_fig3_ablation.png` (written).

| Dataset | conformal FZR (in band) | heuristic FZR (in band) | fixed-τ FZR (in band) |
|---|---:|---:|---:|
| CICIoT2023 | 0.0486 (✅) | 0.0487 (✅) | 0.0013 (⚠) |
| BoT-IoT | 0.0530 (✅) | 0.0531 (✅) | 0.0009 (⚠) |
| UNSW-NB15 | 0.0463 (✅) | 0.0465 (✅) | 0.0075 (⚠) |

**What the asset shows.** On a large i.i.d. calibration split all three rules can land near α — the value of the guarantee is (i) the *certificate* (only the conformal count has an exact finite-sample acceptance band), (ii) **small-n honesty**: over the subsample drill the heuristic's mean FZR exceeds α in 13/15 cells (anti-conservative — the missing +1; ≈ 2× the budget at n = 20) while the conformal mean stays ≤ α in 11/15, and (iii) a fixed τ does not respond to α at all (the sweep panels). Two honest footnotes: the deterministic fact is the ordering — q_conf = s_(k) with the +1 is never below the in-sample percentile of the same subsample, so conformal is never the anti-conservative side — and a conformal *mean* can still sit a hair above α at tiny n (e.g. expected FZR at n = 20 is 1/21 ≈ 0.048 with per-draw sd ≈ 0.044, so a 300-rep Monte-Carlo mean wobbles around the target; the per-draw certificate is the band, not the subsample mean). Per-n detail: [`_generated/w5_06_small_n.csv`](_generated/w5_06_small_n.csv).

## RQ5 honesty summary

Compiled from Day 25 (never recomputed): [`_generated/w5_06_rq5_honesty.md`](_generated/w5_06_rq5_honesty.md). Counts: **ahead 4 / behind 3 / equivalent 1 / unresolved 0** — on the dummy interface this pattern is generator artifact; the compilation repricing on real prototypes is the manuscript's RQ5 section, negative rows included.

## Bottom line

Both Day-29 deliverables are protocol-final: the ablation asset shows the guarantee's value as a structural contrast (certificate + small-n honesty + α-responsiveness), and the RQ5 summary is a faithful compilation of the Day-25 verdicts with effect sizes and provenance. Everything quantum is ‡ provisional and reprices with one flag.

CSV: `_generated/w5_06_ablation.csv` + `_generated/w5_06_small_n.csv` · JSON: `_generated/w5_06_ablation_rq5.json` · table: `_generated/w5_06_ablation.md` + `.tex` · RQ5: `_generated/w5_06_rq5_honesty.md` · figure: `figures/w5_fig3_ablation.png`.
