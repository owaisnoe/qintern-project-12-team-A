# Deliverable (Day 6) — Unified Dataset Package & Metadata

**QS-Net / QuantumSentinel — Team A** · Week 1 · Day 6.
Task: unified feature schema, Train/Val/Calibration/Test/Zero-Day datasets, validate consistency & reproducibility.

## 1. What was delivered

| Item | Location |
|------|----------|
| Schema specification | [`12_unified_schema.md`](12_unified_schema.md) + [`../schema/unified_schema.json`](../schema/unified_schema.json) |
| Projection pipeline | [`../scripts/unified_schema.py`](../scripts/unified_schema.py) + [`../scripts/_unified.py`](../scripts/_unified.py) |
| Unified QADCP splits | `datasets/<name>/unified/qadcp/` (all 5 datasets) |
| Package metadata | [`../METADATA.md`](../METADATA.md) |
| Validation report | [`../scripts/validate_unified.py`](../scripts/validate_unified.py) → `reports/_generated/unified_validation_summary.json` |
| Manifest pins | [`../manifest/MANIFEST.md`](../manifest/MANIFEST.md) (includes `unified/` paths) |

v0.1 per-dataset outputs at `datasets/<name>/qadcp/` are **preserved** for comparison.

## 2. Unified schema summary

17 shared features + 3 labels. See [`12_unified_schema.md`](12_unified_schema.md) for per-dataset mapping.

**Key design choices:**
- Down-map to common network-flow core (no Edge-IIoTset mqtt.* up-padding)
- Frequency encoding for `protocol` / `conn_state` (train-fit; replaces Day-3 ordinal)
- Correlation prune **disabled** in unified mode (keeps identical 17 columns)
- Fixed column order from `schema/unified_schema.json`

## 3. Validation results

All five datasets pass automated gates (`validate_unified.py`):

- Identical feature column names **and order** across datasets
- 0 NaN in split files
- 0 cross-split feature-hash overlap
- Zero-day families isolated from train/val/cal/test
- Label sanity (`label_family` ≠ `other`, binary ∈ {0,1})
- Row conservation (split sum = checkpoint − S7b cross-split dedup)
- Encoders/scalers marked train-fit only

Full Week 1 acceptance (Days 3–7): [`validate_pipeline.py`](../scripts/validate_pipeline.py) → `reports/_generated/final_validation.json`.

## 4. Zero-day benchmark (unified)

Re-scored on unified features ([`unified_zero_day_tiers_summary.json`](_generated/unified_zero_day_tiers_summary.json)):

| Dataset | Holdout | Unified tier |
|---------|---------|--------------|
| CICIoT2023 | Mirai | Hard |
| BoT-IoT | Theft | Hard |
| UNSW-NB15 | Shellcode | Medium |
| UNSW-NB15 | Worms | Easy |

**Caveat:** TON_IoT and Edge-IIoTset unified zero-day splits retain only 1–2 rows after projection dedup — the coarse schema cannot distinguish most ransomware/fingerprinting flows from other attacks.

## 5. Team B handover (v1.0)

Use `datasets/<name>/unified/qadcp/` — same split names as v0.1:

```python
import pandas as pd
q = "datasets/CICIoT2023/unified/qadcp"
tr = pd.read_parquet(f"{q}/quantum/q8_train.parquet")   # 8-qubit ranked
cal = pd.read_parquet(f"{q}/calibration.parquet")        # CQ-ZDR calibration
zd = pd.read_parquet(f"{q}/zeroday.parquet")             # Mirai holdout
```

See [`11_qsnet_interface.md`](11_qsnet_interface.md).

## 6. Day 7 handover (Week 1 closure)

| # | Deliverable | File |
| -- | -- | -- |
| ① | Final pipeline validation | [`validate_pipeline.py`](../scripts/validate_pipeline.py) |
| ② | Handover report | [`14_handover_report.md`](14_handover_report.md) |
| ③ | Team C interface | [`15_teamC_interface.md`](15_teamC_interface.md) |
| ④ | Integration meeting | [`16_integration_meeting.md`](16_integration_meeting.md) |

## Concerns & Recommendations

- **Concern:** unified projection loses discriminative power for some zero-day families (TON, Edge).
- **Recommendation:** use v1.0 for cross-dataset QML comparison; use **v0.1** `qadcp/zeroday.parquet` for TON/Edge zero-day evaluation.

---

*Reproduce:* commands in [`../METADATA.md`](../METADATA.md). Full handover: [`14_handover_report.md`](14_handover_report.md).
