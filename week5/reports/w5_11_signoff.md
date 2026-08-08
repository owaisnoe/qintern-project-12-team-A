# Week 5 · Day 32 — Final Sign-Off: One-Script Reproducibility + Frozen Deliverables

Task (`qi26_12_Week_5.pdf`): *final sign-off — every RQ2 / RQ5 number and Figure 2 reproducible from one script; confirm all Team-A deliverables are frozen for writing.* Seed 42 · α = 0.05 · trio CICIoT2023, BoT-IoT, UNSW-NB15 · scores **dummy** (PROVISIONAL).

Produced by [`../scripts/signoff.py`](../scripts/signoff.py) — the single entry point the task asks for. It re-runs the five result mains from the raw inputs with their outputs sandboxed, then diffs **every** extracted scalar against the committed artifact that quotes it.

## Verdict: **SIGNED OFF** — 324 PASS · 0 FAIL (324 checks, tol 1e-09)

## Gates

| Gate | What it proves | Checks | PASS | FAIL |
|---|---|---:|---:|---:|
| **G1 REPRODUCE** | every RQ1/RQ2/RQ3/RQ5/Figure-2 scalar matches the artifact that quotes it | 289 | 289 | 0 |
| **G2 FREEZE** | the three SHA-256 manifests re-hash clean | 3 | 3 | 0 |
| **G3 COMPLETE** | every declared Team-A deliverable is present and non-empty | 30 | 30 | 0 |
| **G4 NEUTRAL** | this sign-off run did not itself modify any pinned artifact | 1 | 1 | 0 |
| **G5 AUDIT** | the pass-through cells re-derive under an independent implementation | 1 | 1 | 0 |

## G1 — by research question, split by provenance

Of 289 scalars, **204 are recomputed** from the raw scores on this run and **85 are pass-throughs** the emitting module reads from an upstream frozen artifact (Table B's canonical cells from the Day-21/22/19 arms, the RQ5 verdicts from the Day-25 significance JSON, Table A's classical arm from the Day-12 `results.json`). For the pass-throughs G1 proves the **assembly path is stable**, not that the numeric re-derives — that is G5's job, and the two are reported separately rather than pooled.

| Scope | Scalars | recomputed | pass-through | PASS | FAIL | max \|Δ\| |
|---|---:|---:|---:|---:|---:|---:|
| **RQ1** | 39 | 30 | 9 | 39 | 0 | 1.11e-16 |
| **RQ2** | 84 | 48 | 36 | 84 | 0 | 0.00e+00 |
| **RQ3** | 27 | 27 | 0 | 27 | 0 | 0.00e+00 |
| **RQ5** | 105 | 65 | 40 | 105 | 0 | 0.00e+00 |
| **FIG2** | 34 | 34 | 0 | 34 | 0 | 0.00e+00 |

## G3 — deliverables frozen for writing

| Deliverable group | Files | All present |
|---|---:|:--:|
| Table A (RQ1) | 6 | ✅ |
| Table B (RQ2) | 4 | ✅ |
| Figure 2 (coverage) | 2 | ✅ |
| Figure 3 (ablation) | 3 | ✅ |
| RQ3 disentanglement | 1 | ✅ |
| RQ5 honesty | 2 | ✅ |
| Coverage diagnostics | 2 | ✅ |
| Cross-audit (Day 30) | 2 | ✅ |
| Methods + repro appendix (Day 31) | 4 | ✅ |
| Freeze packages | 4 | ✅ |

## Notes

- **Tolerance.** Floats compare to 1e-09; ints, bools and verdict strings compare exactly. The Day-31 appendix (§7) records why bit-equality is the wrong gate: re-runs differ by 1-2 ULP in the scipy exact-binomial tail across library builds, far below any reported digit. `--tol 0` reproduces that finding on demand.
- **Sandboxing.** G1 redirects the mains' output dirs to a temp tree, so G4 is a real check rather than a tautology. The same fix landed in `freeze_results.py --reproduce` on Day 32, closing the open item the Day-31 appendix logged.
- **Scope widened.** `freeze_results.py --reproduce` pins 39 scalars covering RQ1, RQ3 and Figure 2 only. This module additionally covers **RQ2 (Table B, including every per-seed coverage point and both 5-seed CIs) and RQ5 (the ablation rules and every honesty verdict)** — the two the task names explicitly, and the two that had never been inside a reproducibility gate.
- **Provenance is not decoration.** A sign-off that counted pass-throughs as re-derivations would be measuring its own plumbing. The split above, plus G5, is what makes the claim checkable: *recomputed* cells re-derive here, *pass-through* cells re-derive under `cross_audit.py`'s separate implementation.
- **Provenance.** Quantum-side cells ride the Day-14 dummy fidelity interface and remain PROVISIONAL. Re-run with `--source real --scores-root <dir>` to sign off the repriced surface.

CSV: [`_generated/w5_11_signoff.csv`](_generated/w5_11_signoff.csv) · JSON: [`_generated/w5_11_signoff.json`](_generated/w5_11_signoff.json).
