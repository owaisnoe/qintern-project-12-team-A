# Iwo — Week 2 Day 14 Handoff (DATA FREEZE v1.0 + Dummy Score Interface)

This is the **Week-2 milestone / DATA FREEZE** note. It versions the whole Week-2 deliverable surface as
**v1.0**, publishes the prototype-shaped **dummy score interface** so Teams B and C can build against a
stable contract before real MAQT scores exist, and hands over the calibration/test/zero-day sets +
baselines to the wider project. It does **not** change any Day 8–13 partition, RQ3 file, baseline model or
canonical number — those are byte-identical and simply pinned. Full write-up:
[`reports/w2_06_data_freeze.md`](reports/w2_06_data_freeze.md).

## What was implemented

1. **DATA FREEZE v1.0** — [`scripts/freeze_package.py`](scripts/freeze_package.py) pins the entire `week2/`
   deliverable surface (partitions, RQ3, baselines, interface, reports, scripts, tests) by SHA-256 + bytes
   + row count into `week2/FROZEN/freeze_manifest_v1.0.json`, with `VERSION` and `FROZEN_PACKAGE.md`.
   **93 files, 180.0 MB.** `--verify` re-hashes → **0 mismatch**. Week-2-scoped and independent of the
   Week-1 raw-tree manifest (this checkout has no raw data).
2. **Dummy score interface** — [`scripts/make_dummy_scores.py`](scripts/make_dummy_scores.py) writes
   `week2/interface/dummy_scores/<name>/{calibration,test,zeroday}_scores.parquet` aligned by `sample_id`
   to the partitions, carrying the full prototype-fidelity vector `fid__<class>` plus the derived CQ-ZDR
   columns (`max_fidelity`, `pred_class`, **`nonconformity = 1 − max_fidelity`**, `trace_distance_nearest`).
   `dummy_scores_schema.json` is the machine-readable contract; `prototypes_meta.json` self-describes the
   fidelity block (8 qubits, 256-dim Hilbert space, `ρ_c` = per-class mean density matrix).
3. **End-to-end self-check** — fitting split-conformal on the dummy calibration at α=0.10 controls the
   known-test false-flag rate to ~0.10 on all three datasets and rejects zero-day at rates that track the
   Day-9 diagnostic (CIC 1.00, BoT 0.18, UNSW 0.52). Recorded in `_generated/dummy_score_selfcheck.json`.

## Dummy values are a placeholder, not a result

Scores are deterministic (seed 42) and *shape-plausible*: the per-dataset zero-day nonconformity mean is
seeded to the **Day-9 diagnostic** (CIC 0.771 · BoT 0.134 · UNSW 0.352) so the interface is internally
consistent with existing artifacts and exercises the conformal loop without degenerating. **They are
superseded the moment Team B publishes real prototypes** — the schema is the deliverable, the numbers are not.

## Interface contract (for Team B and Team C)

- **One row per partition row**, `sample_id == 0-based index into `partitions/<name>/<split>.csv``.
- `fid__<class>` ∈ [0,1] is the prototype-shaped core (31 cols CIC / 4 BoT / 8 UNSW). Everything else is
  derived from it, so **Team B swaps synthetic fidelities for real MAQT fidelities and all derived columns
  follow automatically** — no schema change needed.
- Conformal score is `nonconformity = 1 − max_c F(ρ_x, ρ_c)`; threshold `q` is the split-conformal
  quantile of calibration nonconformity at α; flag `zeroday` when `nonconformity > q`.

## Upload / merge these files

### New Day-14 files
- `week2/scripts/make_dummy_scores.py`, `week2/scripts/freeze_package.py`
- `week2/interface/dummy_scores_schema.json`
- `week2/interface/dummy_scores/{CICIoT2023,BoT-IoT,UNSW-NB15}/{calibration,test,zeroday}_scores.parquet`
  (+ `.head.csv`) and `prototypes_meta.json`
- `week2/FROZEN/{freeze_manifest_v1.0.json, VERSION, FROZEN_PACKAGE.md}`
- `week2/reports/_generated/dummy_score_selfcheck.json`
- `week2/reports/w2_06_data_freeze.md`
- `week2/tests/test_dummy_scores.py`

### Existing files updated
- `week2/README.md` — Day-14 index row + reproduce command.

Everything from Days 8–13 is unchanged and byte-identical (the freeze pins it, it does not rewrite it).

## Manifest

As on Day 13, I did **not** regenerate `week1/manifest/` — this is a partial checkout with no raw tree.
The **Week-2 freeze** (`FROZEN/freeze_manifest_v1.0.json`) is the self-contained v1.0 pin. Regenerate the
shared Week-1 raw-tree manifest after merging into the Drive master, as the existing process states; the
two are complementary.

## Verification performed

- **24 tests pass** (`python -m unittest discover -s week2/tests` — 19 prior + 5 new interface tests).
- Freeze `--verify` → **0 mismatch** across 93 files.
- Dummy-score self-check: known-test flag rate 0.099 / 0.103 / 0.097 (target α=0.10) on CIC / BoT / UNSW.
- Interface tests confirm row-alignment to the partitions, `nonconformity == 1 − max(fid__*)`, value ranges
  ∈ [0,1], and byte-for-byte determinism at seed 42.

## WhatsApp message

```text
Team A Week 2 — Day 14 done: DATA FREEZE v1.0 + dummy score interface (milestone)

Froze the whole Week-2 package as v1.0: freeze_package.py pins all 93 deliverable files
(partitions + RQ3 + baselines + interface + reports) by SHA-256 — `--verify` = 0 mismatch.
It's Week-2-scoped and doesn't touch the Week-1 raw-tree manifest (my checkout has no raw data),
so please still regenerate the shared manifest once after merging into the Drive master.

Published the prototype-shaped DUMMY score interface so B and C can build now, before real MAQT
scores exist: week2/interface/dummy_scores/<name>/{calibration,test,zeroday}_scores.parquet, one row
per partition row (sample_id = row index), with the full fid__<class> prototype-fidelity vector plus
nonconformity = 1 - max_c F(rho_x, rho_c) and pred_class/trace_distance. dummy_scores_schema.json is
the contract; prototypes_meta.json self-describes it (8 qubits, 256-dim, rho_c = class-mean density matrix).

Arjun/La Wun: swap your real MAQT fidelities into the fid__<class> columns and every derived column
(max_fidelity, pred_class, nonconformity) follows — no schema change. Values are synthetic (seed 42),
seeded to the Day-9 zero-day diagnostic (CIC 0.77 / BoT 0.13 / UNSW 0.35) so they're shape-plausible,
NOT results — they're superseded once your prototypes land.

Self-check: split-conformal on the dummy calibration at alpha=0.10 controls the known-test false-flag
rate to ~0.10 on all three, dummy zero-day rejection CIC 1.00 / BoT 0.18 / UNSW 0.52 (tracks Day-9).
24 tests pass.
```
