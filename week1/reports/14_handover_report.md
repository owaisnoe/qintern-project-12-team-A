# Deliverable (Day 7) — Week 1 Handover Report

**QS-Net / QuantumSentinel — Team A** · Week 1 · Day 7.
Task (`first 7 days task.pdf`): *final validation of the complete pipeline; package datasets,
preprocessing scripts, documentation; hand over standardized datasets to Team B and Team C.*

## 1. Executive summary

Team A delivered a **fully reproducible Quantum-Aware Dataset Curation Pipeline (QADCP)** across
**five intrusion-detection datasets**, producing leakage-safe Train / Val / Calibration / Test /
Zero-Day splits in two package versions:

| Package | Path | Use case |
|---------|------|----------|
| **v0.1** | `datasets/<name>/qadcp/` | Per-dataset features (16–38 cols); richest zero-day splits |
| **v1.0 unified** | `datasets/<name>/unified/qadcp/` | **17 identical features** across all datasets; cross-dataset QML |

Final acceptance: [`scripts/validate_pipeline.py`](../scripts/validate_pipeline.py) →
`reports/_generated/final_validation.json` — **ALL PASS** (5 datasets + manifest verify).

**Mentor-approved benchmark (Jul 2026):** published QS-Net results use **CICIoT2023 + BoT-IoT + UNSW-NB15**
on **v1.0 unified** only. TON_IoT and Edge-IIoTset are **set aside** (unified zero-day collapse). See
[`17_unified_collapse_mentor_note.md`](17_unified_collapse_mentor_note.md).

## 2. Final QADCP

Specification: [`08_qadcp_design.md`](08_qadcp_design.md) · Diagram: [`figures/qadcp_workflow.png`](figures/qadcp_workflow.png)
· Implementation: [`scripts/qadcp.py`](../scripts/qadcp.py) (seed 42).

Stages S0–S8: validate → clean → engineer labels → group features → **split first** → corr prune →
S7b dedup → scale (train-fit) → balance (train only) → quantum angle encoding → acceptance gates.

Two modes:
- `python week1/scripts/qadcp.py` → v0.1 per-dataset outputs
- `python week1/scripts/qadcp.py --unified` → v1.0 unified outputs (after `unified_schema.py`)

## 3. Standardized datasets

### v0.1 (`datasets/<name>/qadcp/`)

| Dataset | Feats | Train | Zero-Day | Holdout | Tier |
|---------|------:|------:|---------:|---------|------|
| CICIoT2023 | 30 | 132,166 | 10,984 | Mirai | Hard |
| TON_IoT | 22 | 62,215 | 254 | ransomware | Easy |
| BoT-IoT | 16 | 130,205 | 683 | Theft | Medium |
| Edge-IIoTset | 38 | 89,971 | 10,548 | Ransomware + Fingerprinting | Easy |
| UNSW-NB15 | 38 | 84,730 | 1,615 | Worms + Shellcode | Easy |

Each package includes: 6 split parquets + `train_balanced` + `quantum/{q4,q8,q12,q16,pca8}_*` +
`scalers.json` + `qubit_budgets.json` + `feature_groups.json` + `zero_day_tiers.json`.

### v1.0 unified (`datasets/<name>/unified/qadcp/`)

| Dataset | Feats | Train | Zero-Day | Benchmark role |
|---------|------:|------:|---------:|----------------|
| CICIoT2023 | 17 | 132,166 | 10,984 | ✅ **in benchmark** |
| BoT-IoT | 17 | 130,138 | 683 | ✅ **in benchmark** |
| UNSW-NB15 | 17 | 71,094 | 1,216 | ✅ **in benchmark** |
| TON_IoT | 17 | 60,308 | 1 | ❌ set aside |
| Edge-IIoTset | 17 | 11,158 | 2 | ❌ set aside |

17 shared features — see [`12_unified_schema.md`](12_unified_schema.md) and [`METADATA.md`](../METADATA.md).

## 4. Validation results

Automated by [`validate_pipeline.py`](../scripts/validate_pipeline.py):

| Gate | Status |
|------|--------|
| Clean checkpoints (Day 3) | pass (all 5) |
| v0.1 QADCP contract | pass (splits, q8, pca8, JSONs, zero-day isolation, angles ∈ [0,π]) |
| v1.0 unified package | pass (8 schema/leakage gates per dataset) |
| Manifest SHA-256 verify | pass (0 mismatch) |

Week 1 success criteria: reproducible QADCP ✅ · standardized datasets ✅ · clean checkpoints ✅ · manifest pinned ✅

Full report: `reports/_generated/final_validation.json`

## 5. Handover to Team B (QML)

Interface note: [`11_qsnet_interface.md`](11_qsnet_interface.md)

**Primary path (benchmark trio):** `datasets/{CICIoT2023,BoT-IoT,UNSW-NB15}/unified/qadcp/quantum/q8_<split>.parquet`

**Split contract:**
- **MAQT (train):** `train` or `train_balanced` — multiclass on **known classes only** (`label_multiclass`)
- **CQ-ZDR (calibration):** `calibration` — known classes only, set rejection threshold
- **Inference:** `test` (multiclass accuracy) + `zeroday` (rejection rate, not classification)
- **HP tuning:** `val` only

**Key clarifications:**
- **8 qubits ≠ output classes** — q8 is input encoding; readout produces C logits (prototype fidelities or classical head)
- **Benchmark trio only for published results:** CIC + BoT + UNSW on v1.0 unified
- **TON/Edge set aside** — unified zero-day collapsed to 1–2 rows; do not report unified metrics on these datasets
- **Quantum label export bug fixed** (Jul 2026): `quantum/q8_*` labels now match parent splits; re-pull from Drive patch if you have an older copy

## 6. Handover to Team C (feature selection)

Interface note: [`15_teamC_interface.md`](15_teamC_interface.md)

Baseline S6b ranking in `qubit_budgets.json` (univariate |r| vs binary) — Team C replaces with
MI / RF / BPSO / QPSO. Input features: `qadcp/train.parquet` (v0.1) or `unified/qadcp/train.parquet` (v1.0).

## 7. Known limitations

1. **Checkpoint sampling** (~200k caps) — not full raw scale (esp. BoT-IoT 73M)
2. **Benchmark locked to CIC + BoT + UNSW** — TON/Edge unified packages exist but are **not** for published zero-day metrics ([`17_unified_collapse_mentor_note.md`](17_unified_collapse_mentor_note.md))
3. **BoT-IoT stratified split** — not time-aware (`stime` dropped); temporal leakage possible
4. **S6b ranking is baseline** — Team C owns final feature selection

## 8. Reproduce (full Week 1)

```bash
cd "Team A"
source ../.venv/bin/activate
python week1/scripts/preprocess.py
python week1/scripts/bot_raw_resample.py          # BoT-IoT Theft recovery
python week1/scripts/qadcp.py
python week1/scripts/pca_baseline.py
python week1/scripts/zero_day_tiers.py
python week1/scripts/unified_schema.py
python week1/scripts/qadcp.py --unified
python week1/scripts/pca_baseline.py --unified
python week1/scripts/zero_day_tiers.py --unified
python week1/scripts/validate_unified.py
python week1/scripts/validate_pipeline.py         # Day 7 final acceptance
python week1/scripts/make_manifest.py --verify
```

## 9. Week 2 readiness

| Team | Next step |
|------|-----------|
| **Team B** | Wire QS-Net MAQT on `q8_train`; CQ-ZDR on `calibration`; evaluate `test` + `zeroday` |
| **Team C** | Run MI/RF/BPSO/QPSO on `qadcp/train.parquet`; beat S6b ranking in `qubit_budgets.json` |
| **Team A** | Support integration; optional schema extension for TON/Edge zero-day |

Integration meeting outline: [`16_integration_meeting.md`](16_integration_meeting.md)

---
*Package index:* [`METADATA.md`](../METADATA.md) · *Checksums:* [`manifest/MANIFEST.md`](../manifest/MANIFEST.md)
