# Team A → Team B — QS-Net Data Interface Note (QADCP **v1.0 unified**)

**QS-Net / QuantumSentinel** · Week 1 · Team A (dataset curation) → Team B (QML).
Re: Arjun's request *"please provide the prepared data samples."* **Short answer: yes — a reproducible,
leakage-safe, quantum-ready sample is ready now** at `datasets/<name>/unified/qadcp/` (**v1.0**). The legacy
per-dataset package remains at `datasets/<name>/qadcp/` (**v0.1**) for comparison and richer zero-day splits.

## Status — what this is / is not

- ✅ **Published benchmark (mentor-approved):** **CICIoT2023 + BoT-IoT + UNSW-NB15** on **v1.0 unified** — 17 identical features, full train/val/cal/test/zeroday splits, `quantum/q8_*` angle tensors ∈ **[0, π]**.
- ✅ **Is (v1.0):** all 5 datasets projected to unified schema (reproducibility / audit); **use only the benchmark trio for published QS-Net results**.
- ✅ **Is (v0.1):** per-dataset feature sets (16–38 cols) for all 5 datasets — reference / exploratory work.
- ⚠️ **Is not:** full raw scale (checkpoint ~200k caps). BoT-IoT is not the full 73M stream.
- ❌ **Set aside from benchmark:** **TON_IoT** and **Edge-IIoTset** on v1.0 — unified projection collapses zero-day to 1–2 rows (see [`17_unified_collapse_mentor_note.md`](17_unified_collapse_mentor_note.md)). Do **not** report unified TON/Edge zero-day metrics.

## Benchmark trio — `datasets/<name>/unified/qadcp/`

**Use these three only** for MAQT training, CQ-ZDR calibration, test accuracy, and zero-day rejection:

Produced by [`unified_schema.py`](../scripts/unified_schema.py) + [`qadcp.py --unified`](../scripts/qadcp.py);
checksum-pinned in [`manifest/MANIFEST.md`](../manifest/MANIFEST.md).

| File | Columns | Use it for |
|---|---|---|
| `train / val / calibration / test / zeroday.parquet` | **17 unified features** + `label_multiclass` + `label_binary` + `label_family` | split contract (QS-Net map below) |
| `train_balanced.parquet` | same, majority capped 20k, rare classes 100 % | balanced MAQT training |
| **`quantum/q8_<split>.parquet`** | **top-8 ranked** features angle-encoded ∈ **[0, π]** | **8-qubit VQC** (explicit q8 files) |
| `quantum/q16_<split>.parquet` | top-16 ranked ∈ [0, π] | nested budgets 4/8/12/16 |
| **`quantum/pca8_<split>.parquet`** | `pca_1..8` ∈ **[0, π]** + labels | **8-qubit PCA baseline** ([`10`](10_pca_baseline.md)) |
| `encoders.json` · `scalers.json` · `feature_groups.json` · `qubit_budgets.json` · `validation_report.json` | train-fit params, semantic groups, rankings, gate results | reproduce / audit |

**Unified features (identical order everywhere):** `duration`, `n_pkts_total`, `n_bytes_total`, `src_pkts`,
`dst_pkts`, `src_bytes`, `dst_bytes`, `rate`, `rate_src`, `rate_dst`, `pkt_size_min`, `pkt_size_max`,
`pkt_size_mean`, `pkt_size_std`, `iat`, `protocol`, `conn_state`

Config: `seed=42`, split `70/10/10/10`, `MAX_PER_CLASS=20000`, frequency-encoded categoricals (train-fit),
`qubit_budgets={4,8,12,16}`. Run `python week1/scripts/make_manifest.py --verify` after you receive it
(expect 0 mismatch = identical bytes).

## How the splits map onto QS-Net (from `QS-Net_Explained.pdf`)

| QS-Net algorithm | Uses | Notes |
|---|---|---|
| **Alg 1 — MAQT** (train VQC + prototypes) | **`train`** / `train_balanced` | per-class samples → prototype density matrix ρ_c; fit **on train only**. |
| **Alg 2 — CQ-ZDR** (conformal threshold q) | **`calibration`** | **KNOWN classes only** — zero-day family excluded by construction. |
| **Alg 3 — Inference** (classify or flag) | **`test`** + **`zeroday`** | `test` = known classes; `zeroday` = held-out family (rejection rate vs α). |
| model / HP selection | **`val`** | never touch `test` / `zeroday` during training. |

**Usage rules (respect these, or the conformal guarantee breaks):** fit encoder/VQC on `train` only;
use `calibration` **only** to set threshold q; evaluate `zeroday` **only** at test time.

**Zero-day family held out per dataset** (same as v0.1; tiers in [`09`](09_zero_day_benchmark.md)):

| Dataset | Holdout | Tier | v1.0 zeroday rows | Benchmark? |
|---------|---------|------|------------------:|:----------:|
| CIC-IoT2023 | **Mirai** | Hard | 10,984 | ✅ |
| BoT-IoT | **Theft** | Medium | 683 | ✅ |
| UNSW-NB15 | **Worms + Shellcode** | Easy | 1,216 | ✅ |
| TON_IoT | ransomware | Easy | 1 | ❌ set aside |
| Edge-IIoTset | Ransomware + Fingerprinting | Easy | 2 | ❌ set aside |

## Concerns & Recommendations

**Concerns**

- **C1 — Two candidate encoders, neither final.** ranked-8 (`q8_*`) and PCA-8 (`pca8_*`) are baselines;
  Team C's selection will replace both ([`10`](10_pca_baseline.md)).
- **C2 — Checkpoint sampling.** ~20k-per-class cap; rare-class prototypes ρ_c may be noisy.
- **C3 — Unified projection information loss on TON/Edge.** Mentor decision: **exclude TON and Edge from the published benchmark**; report per tier on **CIC + BoT + UNSW only**, never pooled with TON/Edge unified splits.
- **C4 — Labels:** `label_multiclass` keeps each dataset's vocabulary; `label_family` is the 10-family
  ontology for cross-dataset work.
- **C5 — BoT-IoT split is stratified, not time-aware** (`stime` dropped) → possible temporal leakage.
- **C6 — Benchmark trio confirmed:** **CIC-IoT2023 + BoT-IoT + UNSW-NB15** (mentor-approved Jul 2026).

**Recommendations**

- **R1:** integrate against **v1.0 unified** on the **benchmark trio** — start with **CIC-IoT2023**,
  `quantum/q8_train.parquet`; keep split names hard-wired.
- **R2:** use `calibration` for CQ-ZDR and `zeroday` for rejection from the start.
- **R3:** run **ranked-8 vs PCA-8 A/B** ([`10`](10_pca_baseline.md)) on v1.0 unified splits (benchmark trio).
- **R4:** do **not** use unified TON/Edge for published zero-day results; v0.1 packages remain for reference only.

## Quick start (v1.0)

```python
import pandas as pd
q = "datasets/CICIoT2023/unified/qadcp"
tr  = pd.read_parquet(f"{q}/quantum/q8_train.parquet")       # ranked-8, angle ∈ [0, π]
cal = pd.read_parquet(f"{q}/calibration.parquet")             # KNOWN classes only (CQ-ZDR)
zd  = pd.read_parquet(f"{q}/zeroday.parquet")                 # held-out family (Mirai)
feats = [c for c in tr.columns if not c.startswith("label_")]
X = tr[feats].to_numpy()          # 8 angle features ∈ [0, π]
y = tr["label_multiclass"].to_numpy()
# PCA-8 alternative: quantum/pca8_train.parquet
```

## Legacy v0.1

Per-dataset features at `datasets/<name>/qadcp/` — same split contract, dataset-specific columns.
Use when you need richer TON/Edge zero-day splits or per-dataset feature granularity.

---
*Provenance:* v1.0 from [`unified_schema.py`](../scripts/unified_schema.py) + [`qadcp.py --unified`](../scripts/qadcp.py);
schema [`12_unified_schema.md`](12_unified_schema.md), package [`13_unified_package.md`](13_unified_package.md),
index [`METADATA.md`](../METADATA.md); pinned in [`manifest/MANIFEST.md`](../manifest/MANIFEST.md).

**Week 1 closure:** full handover [`14_handover_report.md`](14_handover_report.md) · Team C feature selection [`15_teamC_interface.md`](15_teamC_interface.md).
