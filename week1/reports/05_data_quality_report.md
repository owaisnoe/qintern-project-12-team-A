# Deliverable ③ (Day 2) — Data Quality Report

**QS-Net / QuantumSentinel — Team A** · Week 1 · Day 2.
Per-dataset quality scorecard + consolidated flaw register across all five datasets (UNSW-NB15 in
both forms). Evidence: [`scripts/profile_datasets.py`](../scripts/profile_datasets.py) +
[`scripts/eda_datasets.py`](../scripts/eda_datasets.py) → `reports/_generated/*.json`.

## 1. Quality scorecard
Grades: A (clean) → F (severe). "Dup" = **feature-space** duplication (identifiers + labels dropped).

| Dataset | Rows | Missing | Dup | Imbalance | Outliers | Redundancy | **Overall** |
|---|---:|:--:|:--:|:--:|:--:|:--:|:--:|
| **CIC-IoT2023** | 7.85 M | A | A (0.09 %) | D (7,698:1) | C | C (19 pairs) | **B** |
| **TON_IoT** | 211 k | D (`-` ≈100 %) | **F (55.6 %)** | A (48:1) | C | A (0) | **C** |
| **BoT-IoT** | 73.4 M | C (6 empty) | **F (51.4 %)** | **F (3,999:1)** | B | B (5) | **D** |
| **Edge-IIoTset** | 157.8 k | A | A (0.5 %) | A (24:1) | C | B (10) | **B+** |
| **UNSW-NB15 (ML)** | 257.7 k | C (`service` 55 %) | **F (40.4 %)** | D (534:1) | C | C (18) | **C** |
| **UNSW-NB15 (raw)** | 2.54 M | D (blank/`-`) | D (20 %) | **F (9,387:1)** | C | C (18) | **D** |

**Cleanest:** Edge-IIoTset & CIC-IoT2023. **Most work needed:** BoT-IoT & UNSW-NB15.

## 2. Consolidated flaw register
| # | Dataset | Flaw | Evidence | QADCP action |
|---|---|---|---|---|
| 1 | TON_IoT | 55.6 % feature-space duplicates | eda_toniot.json | dedup on features, leakage-safe split |
| 2 | TON_IoT | `-` = missing in ssl/http/dns (≈100 %) | 4.38 M cells | `-`→NaN; drop >95 % cols |
| 3 | BoT-IoT | 51.4 % feature-space duplicates | eda_botiot.json | dedup |
| 4 | BoT-IoT | 6 empty columns (`smac…dco`) | 100 % null | drop |
| 5 | BoT-IoT | header repeated in 74 files; `subcategory ` | profiler flaws | `str.strip`, `header=0`/file |
| 6 | BoT-IoT | Normal 0.013 %, Theft 0.002 % | classdist | undersample majority, protect rare |
| 7 | BoT-IoT | 14 leaky identifier columns | feature_inventory | drop before modelling |
| 8 | CIC-IoT2023 | perfect-correlated features (`Rate=Srate`,`IPv=LLC`) | 19 pairs | correlation-prune |
| 9 | CIC-IoT2023 | 3 zero-variance cols (`Telnet,SMTP,IRC`) | profiler | drop |
| 10 | CIC-IoT2023 | only 34-class label (no 7-cat/binary) | schema | derive coarse labels |
| 11 | UNSW-NB15 | 40.4 % dup + train/test overlap | eda_unsw_mlready | pool→dedup→re-split |
| 12 | UNSW-NB15 | `attack_cat` blank for Normal (87 % raw) | 2.22 M | fill "Normal" |
| 13 | UNSW-NB15 | **"Backdoor" vs "Backdoors"** label split | raw: 1,795 + 534 | normalize labels |
| 14 | UNSW-NB15 | `is_ftp_login`/`ct_ftp_cmd` 49 % missing/anomalous | raw | impute/binary-encode |
| 15 | UNSW-NB15 | train/test files **name-swapped** | 82,332 vs 175,341 | verify, re-split |
| 16 | Edge-IIoTset | 8 zero-variance cols; MQTT block r=1.0 | profiler/eda | drop / correlation-prune |
| 17 | ALL | encoded missingness invisible to `isna()` | §above | canonical `to_missing()` |
| 18 | ALL | heavy-tailed byte/rate features (20–32 % IQR) | eda outliers | robust (quantile/log) scaling |

## 3. Provenance concerns
- **Row-count variance (not errors):** CIC-IoT2023 7.33 M → 7.85 M = **Kaggle mirror variance**;
  TON_IoT 461 k → 211 k = **50k-Normal variant** (attack rows identical); UNSW-NB15 train/test files name-swapped.
- **"Third dataset" ambiguity** unresolved across the project docs (BoT-IoT / UNSW-NB15 / Edge-IIoTset)
  — deferred to the mentor (contact currently unknown).
- **Pin sources (mirror/variant safe) — ✅ implemented:** source URL + row count + SHA-256 per file are
  recorded in [`../manifest/MANIFEST.md`](../manifest/MANIFEST.md) (`make_manifest.py --verify`), with a
  `datasets/<name>/{raw,processed}/` layout, so all three of us train on byte-identical data.

## Concerns & Recommendations
**Top concern:** the headline row counts are **misleading** — after removing identifiers and exact
feature-duplicates, TON_IoT/BoT-IoT/UNSW-NB15 retain roughly **half** their rows as unique. A QADCP
that reports "N rows curated" without a **dedup + unique-feature-vector audit** would overstate the
data. **Recommend** a mandatory `dedup_report` (pre/post counts, cross-split leakage check = 0) as a
first-class QADCP output, plus the canonical cleaning order in
[`04_eda_report.md`](04_eda_report.md) §R1–R6. Grades here become the **acceptance gate**: a dataset
is "curated" only once every F/D in its row is remediated and re-graded.

---
*Reproduce:* `python week1/scripts/profile_datasets.py && python week1/scripts/eda_datasets.py`.
