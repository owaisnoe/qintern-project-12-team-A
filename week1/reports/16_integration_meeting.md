# Week 1 Integration Meeting — Team A Presentation Outline

**QS-Net / QuantumSentinel** · End of Day 7 · ~10 minutes.

Covers the task-PDF bullets for Team A: dataset analysis, QADCP, standardized splits, documentation.

---

## Slide 1 — Title

**Team A: Quantum-Aware Dataset Curation Pipeline (QADCP)**

Members: Amon Koike, Mohammed Owais, Iwo Wojtakajtis

*Speaker note:* We curated 5 IDS datasets into standardized, leakage-safe, quantum-ready packages for Team B and Team C.

---

## Slide 2 — What we studied (Days 1–2)

**5 datasets, 6 views** (UNSW in ML + raw forms):

| Dataset | Rows (raw) | Key finding |
|---------|----------:|-------------|
| CIC-IoT2023 | 7.85M | severe imbalance (7,698:1) |
| TON_IoT | 211k | 55.6% feature-space duplicates |
| BoT-IoT | 73.4M | 51.4% duplicates; Theft ultra-rare |
| Edge-IIoTset | 158k | cleanest; protocol-field rich |
| UNSW-NB15 | 258k | 40% dup + train/test overlap |

*Speaker note:* Headline — row counts are misleading; 40–56% become duplicate feature vectors once identifiers are dropped. This drove our dedup + leakage-safe splitting design.

Reports: `00–06_*.md` · Dashboard: `reports/dashboard.html`

---

## Slide 3 — QADCP workflow (Days 3–4)

![QADCP workflow](figures/qadcp_workflow.png)

**Key design choice:** split **before** fitting scalers/rankings (prevents leakage).

Stages: S0 validate → S1 clean → S2 labels → S3 groups → **S7a split** → S6a prune → S7b dedup → S4 scale → S5 balance → S6b quantum → S8 gates.

*Speaker note:* S7b (post-prune dedup) caught a real leakage channel on Edge-IIoTset — 13k vectors that would have spanned train and test.

Report: `08_qadcp_design.md`

---

## Slide 4 — Zero-day benchmark (Day 5)

**Difficulty-aware holdouts** (Easy / Medium / Hard):

| Dataset | Holdout | Tier |
|---------|---------|------|
| CIC-IoT2023 | Mirai | **Hard** |
| BoT-IoT | Theft | **Medium** |
| TON_IoT | ransomware | Easy |
| Edge-IIoTset | Ransomware + Fingerprinting | Easy |
| UNSW-NB15 | Worms + Shellcode | Easy |

Split contract: Train / Val / **Calibration** / Test / **Zero-Day**

*Speaker note:* Calibration = known classes only (for CQ-ZDR threshold). Zero-day = held-out family (measure rejection, not classification accuracy).

Report: `09_zero_day_benchmark.md`

---

## Slide 5 — Unified package v1.0 (Day 6)

**17 identical features** across all 5 datasets:

`duration`, `n_pkts_total`, …, `protocol`, `conn_state` + 3 labels

Two packages shipped:
- **v0.1** `qadcp/` — per-dataset features (richer zero-day on TON/Edge)
- **v1.0** `unified/qadcp/` — cross-dataset QML (explicit `q8_*` parquets)

*Speaker note:* TON/Edge unified zero-day collapsed to 1–2 rows — use v0.1 for those evaluations.

Reports: `12_unified_schema.md`, `METADATA.md`

---

## Slide 6 — Live demo (2 min)

```python
import pandas as pd

# Load quantum-ready 8-qubit features
tr = pd.read_parquet("datasets/CICIoT2023/unified/qadcp/quantum/q8_train.parquet")
feats = [c for c in tr.columns if not c.startswith("label_")]
print(f"Features: {len(feats)}, angles in [0,π]: {tr[feats].min().min():.2f} – {tr[feats].max().max():.2f}")
print(f"Classes: {tr['label_multiclass'].nunique()}")
print(f"Zero-day held out: Mirai (not in train)")

cal = pd.read_parquet("datasets/CICIoT2023/unified/qadcp/calibration.parquet")
zd  = pd.read_parquet("datasets/CICIoT2023/unified/qadcp/zeroday.parquet")
print(f"Calibration: {len(cal):,} rows | Zero-day: {len(zd):,} rows")
```

Verify reproducibility:
```bash
python week1/scripts/validate_pipeline.py   # ALL PASS
python week1/scripts/make_manifest.py --verify   # 0 mismatch
```

---

## Slide 7 — Handover & documentation index

| Audience | Document | Data path |
|----------|----------|-----------|
| **Team B** | `11_qsnet_interface.md` | `unified/qadcp/quantum/q8_*` |
| **Team C** | `15_teamC_interface.md` | `qadcp/train.parquet` + `feature_groups.json` |
| **Everyone** | `14_handover_report.md` | full Week 1 summary |
| **Reproduce** | `README.md` + `METADATA.md` | `manifest/MANIFEST.md` (SHA-256 pins) |

---

## Slide 8 — Week 2 asks

**Team B:** MAQT on `q8_train` (9 known classes on TON, not 8); CQ-ZDR on `calibration`; zero-day rejection on `zeroday`.

**Team C:** Beat S6b baseline ranking with MI/BPSO/QPSO; deliver top-8 feature list.

**Open for mentor:** canonical dataset trio; target qubit budget (4 vs 8 vs 16).

---

## Anticipated Q&A

**Q: Why 8 qubits but 9 classes on TON?**
A: 8 qubits = input features. 9 classes = known train labels (ransomware held out). Readout produces 9 scores via prototypes or a classical head — not one logit per qubit.

**Q: Binary or multiclass?**
A: Train multiclass on known classes. Zero-day eval = rejection rate (OOD detection), not class prediction.

**Q: Which package should we use?**
A: v1.0 unified for cross-dataset work. v0.1 for TON/Edge zero-day evaluation.

**Q: Is the pipeline reproducible?**
A: Yes — seed 42, `validate_pipeline.py` ALL PASS, manifest 0 mismatch.

**Q: What about BoT-IoT full 73M?**
A: Checkpoint mode (~200k). Full-scale re-run is future work.

---

*Full handover:* [`14_handover_report.md`](14_handover_report.md)
