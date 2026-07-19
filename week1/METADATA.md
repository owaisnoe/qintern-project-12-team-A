# QS-Net Unified Dataset Package — METADATA (v1.0)

**Team A · Day 6 · QS-Net / QuantumSentinel**

## Package identity

| Field | Value |
|-------|-------|
| Version | **1.0** (unified schema) |
| Prior version | v0.1 per-dataset QADCP at `datasets/<name>/qadcp/` |
| Seed | 42 |
| Schema spec | [`schema/unified_schema.json`](schema/unified_schema.json) |
| Sampling | Checkpoint mode (~200k caps); not full 73M BoT-IoT |

## Unified feature schema (17 columns)

Identical column names and order in every split file:

`duration`, `n_pkts_total`, `n_bytes_total`, `src_pkts`, `dst_pkts`, `src_bytes`, `dst_bytes`, `rate`, `rate_src`, `rate_dst`, `pkt_size_min`, `pkt_size_max`, `pkt_size_mean`, `pkt_size_std`, `iat`, `protocol`, `conn_state`

Plus labels: `label_multiclass`, `label_binary`, `label_family`

## Per-dataset split counts (unified/qadcp)

| Dataset | Train | Val | Cal | Test | Zero-Day | Features | Benchmark |
|---------|------:|----:|----:|-----:|---------:|---------:|:---------:|
| CICIoT2023 | 132,166 | 18,883 | 18,883 | 18,883 | 10,984 | 17 | ✅ |
| BoT-IoT | 130,138 | 18,591 | 18,591 | 18,591 | 683 | 17 | ✅ |
| UNSW-NB15 | 71,094 | 10,121 | 10,112 | 10,086 | 1,216 | 17 | ✅ |
| TON_IoT | 60,308 | 8,505 | 8,492 | 8,481 | 1 | 17 | ❌ set aside |
| Edge-IIoTset | 11,158 | 1,575 | 1,572 | 1,570 | 2 | 17 | ❌ set aside |

**Mentor-approved published benchmark:** CICIoT2023 + BoT-IoT + UNSW-NB15 on v1.0 unified only.
See [`reports/17_unified_collapse_mentor_note.md`](reports/17_unified_collapse_mentor_note.md).

## Zero-day holdouts (benchmark trio)

| Dataset | Held-out families | Tier |
|---------|-------------------|------|
| CICIoT2023 | Mirai (3 variants) | Hard |
| BoT-IoT | Theft | Medium |
| UNSW-NB15 | Worms, Shellcode | Easy |

TON_IoT and Edge-IIoTset unified packages are retained for audit but **excluded from the published benchmark**.

## Directory layout

```
datasets/<name>/unified/
  processed/<name>_unified.parquet
  processed/<name>_unified_meta.json
  qadcp/{train,val,calibration,test,zeroday,train_balanced}.parquet
  qadcp/quantum/{q4,q8,q12,q16,pca8}_<split>.parquet
  qadcp/{encoders,scalers,feature_groups,qubit_budgets,qadcp_report,validation_report,pca_baseline}.json
  qadcp/zero_day_tiers.json
```

## Encoding & scaling

- **Categoricals:** `protocol_cat` / `conn_state_cat` → **frequency encoding** (fit on train only) → `protocol`, `conn_state`
- **Missing directional fields:** train-median impute (CIC, Edge)
- **Robust scaling:** median/IQR fit on train → `scalers.json`
- **Quantum tensors:** angle-encoded ∈ [0, π]; explicit `q8_*` files for 8-qubit budget

## Reproduce

```bash
cd "Team A"
source ../.venv/bin/activate   # repo-root venv (Python 3.12 + pyarrow)
python week1/scripts/unified_schema.py
python week1/scripts/qadcp.py --unified
python week1/scripts/pca_baseline.py --unified
python week1/scripts/zero_day_tiers.py --unified
python week1/scripts/validate_unified.py
python week1/scripts/validate_pipeline.py         # Day 7 final acceptance
python week1/scripts/make_manifest.py --verify
```

## Known limitations

1. **Benchmark scope:** published results on **CIC + BoT + UNSW** unified v1.0 only; TON/Edge set aside.
2. **Projection information loss:** TON zeroday ≈ 1 row, Edge zeroday ≈ 2 rows on unified schema — not statistically meaningful.
3. **Checkpoint sampling:** row counts reflect ~200k caps, not full raw scale.
4. **No correlation prune in unified mode:** disabled to preserve identical 17-column schema across datasets.
5. **CIC lacks Srate:** `rate_src` is train-median imputed; `rate_dst` from `Drate`.
6. **UNSW-NB15** cross-domain (non-IoT) — included in mentor-approved trio.

## Validation

Automated gates:
- **Unified package:** [`scripts/validate_unified.py`](scripts/validate_unified.py) — schema, leakage, row conservation
- **Full Week 1 (Day 7):** [`scripts/validate_pipeline.py`](scripts/validate_pipeline.py) — clean + v0.1 + v1.0 + manifest verify

Summaries: `reports/_generated/unified_validation_summary.json`, `reports/_generated/final_validation.json`

## Week 1 handover

Final handover report: [`reports/14_handover_report.md`](reports/14_handover_report.md) · Team B: [`reports/11_qsnet_interface.md`](reports/11_qsnet_interface.md) · Team C: [`reports/15_teamC_interface.md`](reports/15_teamC_interface.md)
