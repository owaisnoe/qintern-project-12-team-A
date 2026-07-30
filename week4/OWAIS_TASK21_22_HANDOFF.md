# Owais — Week 4 Days 21–22 Handoff (Integration Freeze + Conformal↔Inference Integration)

Covers Day 21 (freeze the calibration + statistics interface for integration week) and Day 22 (connect the
frozen conformal module to Team B's inference pipeline; first end-to-end known-vs-zero-day decisions on
dataset 1). Built on AK's Week-4 Days 18–20 (`week4-ak`) and the Week-3 conformal/coverage/stats code.
Branch `week4-owais` off `week4-ak`; PR into `week4-ak`.

## What was implemented

1. **Day 21 — `week4/scripts/freeze_integration.py`** (+ package `week4/INTEGRATION/`, 5 tests). A real
   *freeze* of the integration hand-off surface, not a copy: the calibration rule, the score schema, the
   primary α, and the per-dataset thresholds are pinned so a decision on Day 25 uses the same `q` as Day 22.
   Emits:
   - `frozen_thresholds.json` — the authoritative per-dataset conformal `q` at α = 0.05, recomputed from the
     single Day-15 rule (`q = s_(k)`) on the known-only calibration split, with achieved coverage / FZR and
     the Day-16 exact-band verdict. **This is the number Team B loads on Day 22 — they never recalibrate.**
   - `interface_contract.json` — the frozen score schema Team B must emit (the `fid__<class>` columns,
     `s = 1 − max_c F`, the **non-squared** fidelity convention, α, seed).
   - `integration_manifest_v1.0.json` (+ `VERSION`, `INTEGRATION_PACKAGE.md`) — SHA-256 pins for the four core
     modules (Day-15 calibrate, Day-16 coverage harness, Day-17 stats protocol, Day-19 recall), the score
     interface, the packaged coverage/zero-day/significance outputs, and the two files above. `--verify` → 0
     mismatch. Same freeze conventions as Iwo's Week-2 `freeze_package.py` (content-only hashes; `frozen_utc`
     excluded from `--verify`).
2. **Day 22 — `week4/scripts/conformal_integration.py`** (+ report `w4_03_conformal_integration.md`,
   per-row `w4_03_decisions_<ds>.csv`, 7 tests). The adapter: Team B `fid__*` → `s = 1 − max_c F` → load the
   **frozen** `q` → decide KNOWN if `s ≤ q` else ZERO-DAY. Three asserted gates:
   - **Score contract** — recomputed `s` matches the interface's precomputed `nonconformity` to ≤ 1e-6 (the
     task's *verify score = 1 − max-fidelity flows correctly*).
   - **Frozen-threshold provenance** — the applied `q` is the Day-21 frozen value; an audit recompute equals
     it (a silent freeze→integration drift raises AssertionError — tested).
   - **Coverage consistency** — achieved FZR on KNOWN test reproduces the frozen Day-21 value (same `q`, same
     rows), so integration is faithful, not a re-run with new numbers.
   Handles the F² trap (`--assume-fidelity-squared` → `sqrt()` first). Real prototypes: `--source real
   --scores-root <dir>`, identical schema, no code change.

## Measured results (first end-to-end, dataset 1 = CIC-IoT2023, dummy interface, α = 0.05)

- applied **q = 0.300551** (frozen = audit, exact) · score-contract max|Δ| = **0.00e+00**
- known-test **coverage 0.9514**, false-zero-day **0.0486** — **reproduces the frozen value exactly**
- confusion: TN 17,965 / FP 918 (known) · TP 10,982 / FN 2 (zero-day) → recall 0.9998
- frozen package: **34 files, 26.3 MB, `--verify` 0 mismatch**; all three datasets PASS the exact band.

## What went well

- **Pure reuse, single source of truth.** The freeze recomputes `q` via the Day-15 `calibrate_dataset` and the
  verdict via the Day-16 `verify_dataset` — no conformal math re-implemented. The adapter imports the same
  score functions. Suite grew 67 → 78, all green.
- **The freeze is genuinely load-bearing, not ceremony:** Day 22 loads `q` from it and the provenance gate
  makes a freeze↔integration mismatch impossible.
- **The score contract is exact** (max|Δ| = 0.0 on the real interface) — the `s = 1 − max_c F` plumbing Team B
  will use is verified before their real scores land.

## Challenges and issues

1. **Dummy interface.** Every recall number is the Day-14 placeholder; Day 22 proves the *plumbing* and
   reproduces frozen *coverage* exactly (coverage is score-agnostic). Recall reprices on real prototypes with
   no code change.
2. **Fidelity convention (F² trap, AK's Day-20 spec).** `s` needs non-squared F; the adapter carries
   `--assume-fidelity-squared` and the frozen `interface_contract.json` states the convention explicitly.
3. **Rounding across module boundaries.** `calibrate_dataset` rounds FZR to 4 dp, the adapter to 6 dp — the
   coverage-consistency gate compares the underlying rate (≤ 1e-6), the cross-check test uses 1e-4.

## Concerns and recommendations

- **Team B:** emit real `fid__<class>` (non-squared F) into the frozen schema, then run
  `conformal_integration.py --source real --scores-root <your dir>` — the frozen `q` applies unchanged.
  Coverage should hold; if a gate fails after the swap, exchangeability broke in the plumbing (prototypes
  touching calibration), which is exactly what Day 23's live audit is for.
- **Day 23 (next):** run `conformal_integration.py` live on the integrated pipeline across all three datasets
  and audit exchangeability (cal↔test two-sample AUROC ≈ 0.5 from Week-2 `split_integrity.py`); log/fix any
  violation. **Day 24:** the per-row decisions + confusion already emit RQ2 recall + achieved α — assemble
  Table B. **Day 25:** significance via the Day-17 `stats_protocol.py` (Holm + d_z).
- **Manifest note (unchanged from AK):** a fresh git clone verifies 467/665 pins; 198 raw-data files live
  outside git. Still a team decision (document as expected-missing, or add `--scope git`).

## Files added (this branch)

- `week4/scripts/freeze_integration.py` · `week4/tests/test_freeze_integration.py`
- `week4/scripts/conformal_integration.py` · `week4/tests/test_conformal_integration.py`
- `week4/reports/w4_03_conformal_integration.md`
- `week4/INTEGRATION/` (frozen_thresholds.json, interface_contract.json, integration_manifest_v1.0.json,
  VERSION, INTEGRATION_PACKAGE.md)
- `week4/reports/_generated/w4_03_conformal_integration.{json,csv}` + `w4_03_decisions_CICIoT2023.csv`
- `week4/README.md` (Days 21–22 rows + reproduce), this handoff.

## Verification performed

- `python -m pytest week2/tests week3/tests week4/tests` → **78 passed** (67 prior + 11 new) on Python 3.14 /
  scipy 1.17; no regressions in AK's or Iwo's tests.
- `freeze_integration.py` → 34 files pinned, `--verify` 0 mismatch, all three datasets PASS.
- `conformal_integration.py --datasets CICIoT2023` → score contract 0.0, applied q = frozen q, coverage
  reproduces frozen (True), first end-to-end decisions written.
