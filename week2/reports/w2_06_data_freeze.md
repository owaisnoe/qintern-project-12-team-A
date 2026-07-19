# Week 2 · Day 14 — DATA FREEZE, Dummy Score Interface & Handover

**QS-Net / QuantumSentinel — Team A (Iwo)** · Week 2 · Day 14 · benchmark trio **CIC-IoT2023 + BoT-IoT +
UNSW-NB15** · seed **42** · qubit budget **8**.
Task (`Week 2.pdf`): *DATA FREEZE — finalise and version all partitions; publish prototype-shaped dummy
score files so Teams B and C can build against a stable interface; hand over calibration/test/zero-day sets
+ baseline results to the wider project.*
Scripts: [`../scripts/freeze_package.py`](../scripts/freeze_package.py) ·
[`../scripts/make_dummy_scores.py`](../scripts/make_dummy_scores.py).

This is the **Week-2 milestone**: the partitions, RQ3 set and classical baselines from Days 8–13 are frozen
as **v1.0** and the score interface that Team B (real MAQT/CQ-ZDR) and Team C consume is published in
dummy form, so downstream code can be written against a stable contract this week.

## 1. DATA FREEZE — v1.0

[`freeze_package.py`](../scripts/freeze_package.py) pins the **entire Week-2 deliverable surface** by
SHA-256 + byte size + row count into [`../FROZEN/freeze_manifest_v1.0.json`](../FROZEN/freeze_manifest_v1.0.json),
with a one-line [`../FROZEN/VERSION`](../FROZEN/VERSION) marker and a human index
[`../FROZEN/FROZEN_PACKAGE.md`](../FROZEN/FROZEN_PACKAGE.md).

- **93 files · 180.0 MB** pinned: `partitions/`, `rq3/`, `baselines/`, the new `interface/`, all `reports/`
  (+ `_generated/`), `scripts/`, `tests/`, README and handoff notes.
- **Self-contained and Week-2-scoped.** It does **not** regenerate or depend on the Week-1 raw-tree
  manifest: per the [Day-13 handoff](../IWO_TASK13_HANDOFF.md), this checkout carries no raw data (0 of the
  193 raw CSVs), so `week1/make_manifest.py` here would produce a divergent *partial* manifest. The freeze
  pins only what Team A ships, so it verifies on any checkout that carries `week2/`.
- **Content-addressed.** `frozen_utc` is metadata only; `--verify` compares hashes, so a re-freeze on a
  clean tree reproduces byte-identical pins.

```bash
python week2/scripts/freeze_package.py            # write FROZEN/ (v1.0)
python week2/scripts/freeze_package.py --verify   # re-hash -> "FREEZE VERIFY OK — 93 files, 0 mismatch."
```

Once merged into the Drive master with the raw tree, regenerate the shared Week-1 manifest as usual
(Day-13 handoff §Manifest) — the two are complementary: the raw-tree manifest pins provenance, this freeze
pins the Week-2 deliverable at v1.0.

## 2. Dummy score interface — prototype-shaped, stable for Teams B and C

Team B's Day-14 deliverable is the real per-class prototype density matrices `{ρ_c}`; their scores don't
exist yet. To unblock downstream code now, Team A publishes a **synthetic score interface** with the exact
schema, dtypes, ranges and row-alignment the real scores will carry.
[`make_dummy_scores.py`](../scripts/make_dummy_scores.py) writes, per dataset:

```
week2/interface/dummy_scores/<name>/{calibration,test,zeroday}_scores.parquet
week2/interface/dummy_scores/<name>/{...}.head.csv     # 10-row human preview
week2/interface/dummy_scores/<name>/prototypes_meta.json
week2/interface/dummy_scores_schema.json               # the interface contract
```

**Schema — one row per partition row, aligned by `sample_id` (0-based index into
`partitions/<name>/<split>.csv`):**

| Column | Type | Meaning |
|---|---|---|
| `sample_id` | int64 | row index into the matching partition CSV |
| `dataset`, `split` | str | provenance |
| `true_label_multiclass`, `true_label_family` | str | copied from the partition (audit) |
| `y_known` | int8 | 1 for calibration/test, 0 for zeroday |
| `pred_class` | str | argmax-fidelity prototype (predicted known class) |
| `pred_correct` | int8 | `pred_class == true` on known rows |
| `max_fidelity` | float64 | `max_c F(ρ_x, ρ_c)` ∈ [0,1] |
| `runner_up_fidelity`, `margin` | float64 | top-2 fidelity and its gap |
| `fid_true_class`, `nonconformity_true` | float64 | true-class fidelity / `1−fid_true` (NaN on zeroday) |
| **`nonconformity`** | float64 | **`1 − max_fidelity`** — the CQ-ZDR conformal score (higher ⇒ more novel) |
| `trace_distance_nearest` | float64 | trace distance to the nearest prototype ∈ [0,1] |
| **`fid__<class>`** | float64 | **one column per known prototype** — Uhlmann `F(ρ_x, ρ_c)` ∈ [0,1] |

The `fid__<class>` block is the prototype-shaped core (31 columns for CIC, 4 for BoT, 8 for UNSW);
`max_fidelity`, `pred_class`, `nonconformity` are all derived from it, so **Team B swaps synthetic
fidelities for real MAQT fidelities and every derived column follows**. `prototypes_meta.json` self-
describes the block (8 qubits, 256-dim Hilbert space, `ρ_c` = per-class mean density matrix).

**Dummy values are placeholders, not results.** They are deterministic (seed 42) and *shape-plausible*: the
per-dataset zero-day `nonconformity` mean is seeded to the **Day-9 diagnostic** (CIC 0.771 · BoT 0.134 ·
UNSW 0.352 — [`w2_02`](w2_02_split_integrity.md)), and known-row scores are kept high enough that split-
conformal at α=0.10 behaves. They are superseded the instant Team B publishes real prototypes.

### End-to-end self-check ([`_generated/dummy_score_selfcheck.json`](_generated/dummy_score_selfcheck.json))

Fitting the split-conformal threshold `q` on dummy **calibration** at α=0.10, then scoring test/zeroday,
proves the interface drives the full CQ-ZDR loop without degenerating:

| Dataset | `q` | known-test flag rate (→ α) | known-test coverage (→ 1−α) | zero-day rejection | known-test acc |
|---|---:|---:|---:|---:|---:|
| CIC-IoT2023 | 0.245 | 0.099 | 0.901 | 1.000 | 0.903 |
| BoT-IoT | 0.213 | 0.103 | 0.897 | 0.179 | 0.940 |
| UNSW-NB15 | 0.329 | 0.097 | 0.903 | 0.524 | 0.797 |

The known-test flag rate lands on α=0.10 on all three (conformal coverage holds), and the dummy zero-day
rejection tracks the existing diagnostics — **CIC easily rejectable, BoT hard, UNSW medium** — matching
Day-9 and the Day-13 novelty heads. These are interface-sanity numbers, **not** QS-Net results.

## 3. Handover — what the wider project receives

- **Partitions (Days 8–9):** `week2/partitions/<name>/{train,calibration,test,zeroday}.csv` +
  `partition_meta.json`. `train` = known classes (MAQT), `calibration` = **known-only** (CQ-ZDR threshold),
  `test` = known-class accuracy, `zeroday` = full held-out family (rejection). Exchangeable (2-sample
  AUROC ≈ 0.50, coverage ≈ 0.90). **Use marginal conformal for CIC** (4 sub-10 rare classes block Mondrian).
- **RQ3 set (Day 10):** `week2/rq3/<name>/{adversarial_source_pool,eval_clean}.csv` + `rq3_schema.json`.
  Perturb `adversarial_source_pool.csv` (clean known attacks) with FGSM/PGD in the classical feature space
  before angle encoding; keep the `origin × perturb` labels; **never seed adversarials from the zero-day class.**
- **Classical baselines (Days 11–13):** `week2/baselines/<name>/` + five-seed statistics
  ([`stats_harness.json`](_generated/stats_harness.json)) + leakage confirmation. The bar for QS-Net is the
  **hard slice**: UNSW-NB15 macro-F1 0.60 and UNSW Shellcode/Worms zero-day below chance for every
  unsupervised head ([`w2_05`](w2_05_day13_all_datasets.md)).
- **Score interface (Day 14):** `week2/interface/` — the contract above. Team B fills it with real MAQT
  fidelities; Team C's consumers and Team A's Week-3 CQ-ZDR calibration build against it now.

## 4. Reproduce & verify

```bash
source ../.venv/bin/activate                          # Python 3.12
python week2/scripts/make_dummy_scores.py             # interface/ + self-check (seed 42)
python week2/scripts/freeze_package.py                # FROZEN/ v1.0
python week2/scripts/freeze_package.py --verify       # expect 0 mismatch
python -m unittest discover -s week2/tests            # 24 tests
```

## 5. Files produced (Day 14)

- `week2/scripts/make_dummy_scores.py`, `week2/scripts/freeze_package.py` (new).
- `week2/interface/dummy_scores_schema.json` + `dummy_scores/<name>/{calibration,test,zeroday}_scores.parquet`
  (+ `.head.csv`) + `prototypes_meta.json` (new).
- `week2/FROZEN/{freeze_manifest_v1.0.json, VERSION, FROZEN_PACKAGE.md}` (new).
- `week2/reports/_generated/dummy_score_selfcheck.json` (new).
- `week2/tests/test_dummy_scores.py` (new, 5 tests).
- `week2/reports/w2_06_data_freeze.md` (this report), `week2/IWO_TASK14_HANDOFF.md`, `week2/README.md`
  (Day-14 row) — updated.

**Unchanged:** every Day 8–13 partition, RQ3 file, baseline model and canonical number is byte-identical;
Day 14 only adds the freeze manifest and the score interface.

---
*Reproduce:* `python week2/scripts/make_dummy_scores.py && python week2/scripts/freeze_package.py --verify`.
