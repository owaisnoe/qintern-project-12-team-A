# Week 4 · Day 22 — Conformal↔Inference Integration + First End-to-End Decisions

Task (`qi26_12_Week_4.pdf`): *connect the frozen conformal module to Team B's inference pipeline; verify score = 1 − max-fidelity flows correctly; run first end-to-end known-vs-zero-day decisions on dataset 1.* The adapter loads the **Day-21 frozen threshold** ([`../INTEGRATION/frozen_thresholds.json`](../INTEGRATION/frozen_thresholds.json)) — it does **not** recalibrate — and flags a point as zero-day iff `s = 1 − max_c F(ρ_x, ρ_c) > q`. Primary α = 0.05, seed 42, source **dummy**.

## Verification gates (all asserted)
1. **Score contract** — recomputed `s = 1 − max_c F` from the `fid__*` columns matches the interface's precomputed `nonconformity` to ≤ 1e-6 (the task's *score = 1 − max-fidelity flows correctly*).
2. **Frozen-threshold provenance** — the applied `q` is loaded from the Day-21 freeze; an audit recompute from calibration equals it (no silent drift freeze→integration).
3. **Coverage consistency** — the achieved false-zero-day rate on KNOWN test reproduces the frozen Day-21 value (same `q`, same rows).

## CICIoT2023

- applied q = **0.300551** (frozen 0.300551, audit 0.300551) · score-contract max|Δ| = 0.00e+00

| | truly KNOWN (test) | truly ZERO-DAY |
|---|---:|---:|
| decided KNOWN | 17,965 (TN) | 2 (FN) |
| decided ZERO-DAY | 918 (FP) | 10,982 (TP) |

- known-test coverage **0.9514** · false-zero-day **0.0486** (reproduces frozen 0.048615: True)
- zero-day recall **0.9998** (10,982/10,984 caught)

## BoT-IoT

- applied q = **0.262934** (frozen 0.262934, audit 0.262934) · score-contract max|Δ| = 0.00e+00

| | truly KNOWN (test) | truly ZERO-DAY |
|---|---:|---:|
| decided KNOWN | 17,605 (TN) | 618 (FN) |
| decided ZERO-DAY | 986 (FP) | 65 (TP) |

- known-test coverage **0.9470** · false-zero-day **0.0530** (reproduces frozen 0.053036: True)
- zero-day recall **0.0952** (65/683 caught)

## UNSW-NB15

- applied q = **0.383380** (frozen 0.383380, audit 0.383380) · score-contract max|Δ| = 0.00e+00

| | truly KNOWN (test) | truly ZERO-DAY |
|---|---:|---:|
| decided KNOWN | 9,619 (TN) | 747 (FN) |
| decided ZERO-DAY | 467 (FP) | 469 (TP) |

- known-test coverage **0.9537** · false-zero-day **0.0463** (reproduces frozen 0.046302: True)
- zero-day recall **0.3857** (469/1,216 caught)

## Reading this
- This is the **plumbing** end-to-end, not a detection result: on the **dummy** interface the recall column is the Day-14 synthetic placeholder. What Day 22 proves is that Team B's scores flow through the frozen contract and reproduce the frozen coverage exactly.
- The identical command reprices on real prototypes (`--source real --scores-root <team-B dir>`); coverage should hold (the guarantee is score-agnostic), recall is the number that changes.
- Coverage bounds **false alarms only** (Prop 3 §5.2) — recall is the separate power axis (Day 19); Day 23 runs this live and audits exchangeability, Day 24 extends to all datasets.
