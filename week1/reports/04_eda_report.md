# Deliverable ① (Day 2) — Exploratory Data Analysis (EDA) Report

**QS-Net / QuantumSentinel — Team A** · Week 1 · Day 2.
Six EDA analyses across **all five datasets** (UNSW-NB15 in both forms → 6 views).
Reproduced by [`scripts/eda_datasets.py`](../scripts/eda_datasets.py); raw stats in
`reports/_generated/eda_*.json`; figures in [`figures/`](figures/); interactive
[`dashboard.html`](dashboard.html). Companion: [`05_data_quality_report.md`](05_data_quality_report.md),
[`06_visualization_dashboard.md`](06_visualization_dashboard.md).

**Analysis scope (memory strategy).** Class distributions use **full** counts (from the profiler).
Numeric analyses use a working frame — full for small sets, a **seeded sample** for huge ones:

| View | Working frame | Numeric features analyzed |
|---|---|---|
| CIC-IoT2023 | validation split, sampled 200 k | 40 |
| TON_IoT (Network) | full 211,043 | 17 |
| BoT-IoT | 4 k×74-file head-sample = 296 k | 15 |
| Edge-IIoTset (ML) | full 157,800 | 39 |
| UNSW-NB15 (ML-ready) | full 257,673 | 39 |
| UNSW-NB15 (raw) | 60 k×4-file head-sample = 240 k | 38 |

## 1. Missing values
| Dataset | Headline | Worst columns |
|---|---|---|
| CIC-IoT2023 | **none** | — |
| TON_IoT | `-` placeholders everywhere | `ssl_subject/ssl_issuer` 99.99 %, `http_orig_mime_types` 99.99 % |
| BoT-IoT | 6 empty columns | `smac,dmac,soui,doui,sco,dco` **100 %** |
| Edge-IIoTset | negligible | `ip.src_host` 0.13 % |
| UNSW-NB15 (ML) | `-` in `service` | `service` **54.8 %** |
| UNSW-NB15 (raw) | blanks + `-` | `is_ftp_login` 49.3 %, `ct_ftp_cmd` 49.3 %, `service` 46.9 %, `attack_cat` **87.4 % (blank=Normal)** |

**Finding:** missingness is almost always **encoded, not `NaN`** — `-` (TON_IoT, UNSW `service`),
blank (UNSW `attack_cat`/`ftp`), or empty columns (BoT-IoT). Standard `isna()` misses all of it.
Figures: `figures/<dataset>/missing.png`.

## 2. Duplicate records — the biggest cross-dataset issue
Exact **full-row** duplicates (profiler) vs **feature-space** duplicates (EDA, after dropping
identifiers + labels):

| Dataset | Full-row dup | **Feature-space dup** |
|---|---:|---:|
| CIC-IoT2023 | 0.5 % | 0.09 % |
| **TON_IoT** | 9.7 % | **55.6 %** |
| **BoT-IoT** | ~0 % | **51.4 %** |
| Edge-IIoTset | 0.5 % | 0.5 % |
| **UNSW-NB15 (ML)** | 36.8 %¹ | **40.4 %** |
| UNSW-NB15 (raw) | 17.7 % | 20.3 % |

¹ over the whole row minus the unique `id`. **Finding:** once IP/port/timestamp **identifiers** are
removed (as they must be, to avoid leakage), **40–56 % of rows become duplicates** in TON_IoT,
BoT-IoT and UNSW-NB15 — feature vectors repeat, sometimes with *different* labels (class overlap).
This is the single strongest argument for the QADCP's **de-duplication + leakage-safe splitting**
step, and it means the datasets carry far less independent information than their row counts suggest.
UNSW-NB15's 36–40 % also implies **overlap between the official train and test partitions** →
concatenating them (as many papers do) leaks.

## 3. Class imbalance
`cross_dataset_imbalance.png` — majority : minority ratio (log) and normalized entropy (1 = uniform):

| Dataset | Classes | Imbalance ratio | Norm. entropy |
|---|---:|---:|---:|
| CIC-IoT2023 | 34 | 7,698 : 1 | 0.747 |
| BoT-IoT | 4* | 3,999 : 1 | **0.574** |
| UNSW-NB15 (raw) | 10 | 9,387 : 1 | **0.241** |
| UNSW-NB15 (ML) | 10 | 534 : 1 | 0.734 |
| TON_IoT | 10 | 48 : 1 | 0.935 |
| Edge-IIoTset | 15 | 24 : 1 | **0.949** |

*BoT-IoT sample saw 4 of 5 categories (Theft is too rare to appear in a head-sample; the full set has
5 — Theft = 1,587). **Finding:** TON_IoT and Edge-IIoTset are near-balanced (entropy ≈ 0.94);
CIC-IoT2023, BoT-IoT and UNSW-NB15 are severely skewed. The UNSW-NB15 **raw** entropy (0.24) reflects
87 % Normal; the **ML-ready** partition was deliberately re-balanced (entropy 0.73). Figures:
`figures/<dataset>/class_distribution.png`.

## 4. Outliers (share of values outside 1.5·IQR)
| Dataset | Most outlier-heavy features |
|---|---|
| CIC-IoT2023 | `Max` 31.9 %, `AVG` 30.8 %, `Tot size` 30.7 % |
| Edge-IIoTset | `tcp.len` 22.8 %, `tcp.seq` 22.6 %, `tcp.ack` 21.3 % |
| TON_IoT | `duration` 22.6 %, `dst_ip_bytes` 20.6 %, `dst_bytes` 20.5 % |
| UNSW-NB15 (ML) | `dload` 22.3 %, `ct_src_dport_ltm` 19.0 % |
| UNSW-NB15 (raw) | `Sload` 22.4 %, `ct_src_dport_ltm` 21.2 %, `Sjit` 18.6 % |
| BoT-IoT | `rate` 11.3 %, `srate` 8.7 % |

**Finding:** byte/packet/rate/load features are extremely **heavy-tailed** (20–32 % IQR-outliers) — an
artefact of flood attacks, not errors. Implication: **robust scaling** (quantile / log1p), not
z-score standardization, and **do not clip** as if they were noise. Figures:
`figures/<dataset>/outliers.png`, `distributions.png`.

## 5. Feature distributions
Top-variance features are near-log-normal with huge dynamic range (bytes/rates span many orders of
magnitude); binary flags and protocol one-hots are bimodal. Several Edge-IIoTset counters overflow
float32 range (`tcp.seq`, `tcp.ack`), confirming they must be **log/quantile-transformed** before any
quantum encoding (which needs bounded, normalized inputs). See `figures/<dataset>/distributions.png`.

## 6. Feature correlations (redundancy)
Highly-correlated pairs |r| ≥ 0.9 (candidates to drop before feature selection / quantum encoding):

| Dataset | # pairs | Examples (perfect r=1.0 in **bold**) |
|---|---:|---|
| CIC-IoT2023 | **19** | **`Rate`=`Srate`**, **`IPv`=`LLC`**, **`Std`=`Radius`** |
| UNSW-NB15 (ML) | 18 | `is_ftp_login`~`ct_ftp_cmd` 0.999, `dbytes`~`dloss` 0.997 |
| UNSW-NB15 (raw) | 18 | `swin`~`dwin` 0.9997, `dbytes`~`dloss` 0.993 |
| Edge-IIoTset | 10 | **`mqtt.*` cluster all r=1.0** |
| BoT-IoT | 5 | `dpkts`~`dbytes` 0.996, `pkts`~`bytes` 0.95 |
| TON_IoT | 0 | (numeric features largely independent) |

**Finding:** every dataset except TON_IoT carries **redundant / perfectly-correlated** features
(`Rate`≡`Srate`, `IPv`≡`LLC` in CIC-IoT2023; whole MQTT block in Edge-IIoTset). For a **qubit-budget**
pipeline this is critical — dropping one of each redundant pair frees qubits at zero information cost.
Figures: `figures/<dataset>/correlation_heatmap.png`.

## Concerns & Recommendations
**Concerns**
- **C1 — Hidden redundancy.** 40–56 % feature-space duplication (TON_IoT/BoT-IoT/UNSW-NB15) means
  effective sample sizes are far below row counts; naïve splitting leaks duplicates across train/test.
- **C2 — Encoded missingness.** `-`/blank/empty-column missingness is invisible to `isna()`; any
  pipeline that trusts `isna()` (common in tutorials) will silently mis-handle 4.4 M (TON_IoT) cells.
- **C3 — Heavy tails.** 20–32 % IQR-outliers make standardization + naïve clipping destructive.
- **C4 — Redundant features waste qubits.** Perfect correlations inflate dimensionality for QML.
- **C5 — UNSW train/test overlap** (36–40 %) risks leakage if the two files are concatenated.

**Recommendations for the QADCP**
- **R1** De-duplicate **on feature columns only** (drop identifiers first), then split — guarantee no
  feature vector spans train/test (leakage-safe). Use **time-aware/group splitting for BoT-IoT**
  (unshuffled temporal order → a random split leaks adjacent flows). Log pre/post row counts per dataset.
- **R2** Convert `-`/blank/empty/`0.0.0.0` → `NaN` first (a canonical `to_missing()` step), then decide
  drop-vs-impute per column; drop columns > ~95 % missing (TON_IoT ssl/http, UNSW `service` review).
- **R3** Use **quantile / log1p (robust) scaling**; reserve min-max→[0,π] only for the final quantum
  angle-encoding layer.
- **R4** Add a **correlation-pruning** step (drop one of each |r|≥0.95 pair) before Team C's feature
  selection — this is the cheapest qubit saving.
- **R5** For UNSW-NB15, treat the two files as one pool, de-duplicate, then re-split (don't trust the
  shipped partition); confirm the swapped file-naming with the team.
- **R6** **Pin every source** (URL + row count + SHA-256) in a `raw/`+`processed/` layout with a
  `MANIFEST` README — Kaggle mirrors/variants differ, so this guarantees all three of us train on
  identical bytes.

---
*Reproduce:* `source .venv/bin/activate && python week1/scripts/eda_datasets.py` (Python 3.12).
