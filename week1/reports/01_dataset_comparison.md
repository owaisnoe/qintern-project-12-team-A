# Deliverable ① — Dataset Comparison Report

**QS-Net / QuantumSentinel — Team A** · Week 1 · Day 1
Datasets (per `first 7 days task.pdf`): **CIC-IoT2023, TON_IoT (Network), BoT-IoT.**
All figures **measured** on the downloaded CSVs unless marked *claimed*; all URLs verified live.

## 1. Side-by-side comparison

| Property | **CIC-IoT2023** | **TON_IoT (Network)** | **BoT-IoT** |
|---|---|---|---|
| Producer | CIC, Univ. of New Brunswick | UNSW Canberra (N. Moustafa) | UNSW Canberra (Koroniotis et al.) |
| Year | 2023 | 2020–21 | 2018–19 |
| Environment | 105 real IoT devices | IoT/IIoT + network testbed | IoT (Ostinato/Node-RED) testbed |
| Feature type | Aggregated **flow statistics** | **Zeek/Bro** connection logs | **Argus** flow records |
| Files used | `train/test/validation.csv` | `train_test_network.csv` | 74 × `data_*.csv` |
| **Rows (measured)** | **7,845,673** | **211,043** | **73,370,443** |
| Rows (*docs*) | 7,332,065 *(Discord note; mirror variance)* | 461,043 *(300k-Normal variant)* | ~72–73 M ✓ |
| Columns | 47 | 44 | 35 |
| **Features** | **46** (all numeric) | **42** | **32** |
| Label column(s) | `label` (34-class) | `label` (binary) + `type` (10-class) | `attack` (bin) + `category` (5) + `subcategory` (8) |
| Class granularity | 34 fine / 7 cat* / 2 bin* | 10 (9 attacks + normal) | 5 category / 8 subcategory |
| Benign / Normal share | 2.36 % | 23.69 % | **0.013 %** |
| Missing values | none | **4.38 M cells as `-`** | 6 all-null columns |
| Duplicate rows | 0.5 %¹ | **9.75 %** | ~0 %² |
| Leaky identifiers | none | IPs, ports | IDs, IPs, MACs, ports, timestamps |
| Data-quality grade | **A− (clean, skewed)** | **C (dirty, dedup+`-` needed)** | **C+ (traps + extreme skew)** |
| License | research use (CIC) | research use (UNSW) | research use (UNSW) |

*\* 7-category and binary labels are **not present** in this Kaggle build of CIC-IoT2023 and must be
derived. ¹ validation split. ² 210 K stratified sample.*

## 2. Per-dataset capsule

**CIC-IoT2023** — the largest and cleanest. 46 pre-computed flow features (rates, packet/byte
statistics, TCP-flag counts, protocol one-hots, IAT, statistical moments). Best "reference" dataset,
but ships only the 34-class label and is heavily DDoS/DoS-dominated. 3 protocol columns
(`Telnet, SMTP, IRC`) are all-zero.

**TON_IoT (Network)** — richest protocol context (DNS/SSL/HTTP fields) but the messiest: ~10 %
duplicate rows, 4.38 M `-` placeholders, and IP/port identifiers. Reasonably balanced across the 9
attack types (~20 k each) except MITM (1,043). The downloaded copy is a **standard variant** (50k
Normal instead of 300k; attack rows identical) — **not a partial download** (461,043 − 250,000 = 211,043).

**BoT-IoT** — botnet-focused and enormous (~73.4 M rows across 74 files). Excellent DDoS/DoS volume
but pathological imbalance (Normal 9,543; Theft 1,587) and several structural traps: repeated
headers, a trailing-space column name, unshuffled per-file temporal ordering, 6 empty columns, and
14 leaky identifier columns. Usable feature count after cleaning ≈ 18.

## 3. Common ground (basis for the future unified schema)
Despite three different schemas, all datasets expose the same **network-flow semantics**: a flow
**duration**, **packet** and **byte** counts (often split source/destination), derived **rates**, a
**protocol**, and a **connection state / TCP-flag** summary. These ~8–12 shared concepts are the
seed of the Day-6 unified feature schema (full mapping in `02_feature_inventory.md`). Literal column-
name overlap is essentially nil — harmonization must be **semantic**, not string-based.

## 4. Discrepancies flagged
- **"Third dataset" inconsistency:** task PDF → **BoT-IoT** (used here); overview PDF → UNSW-NB15;
  Discord note + downloaded data → Edge-IIoTset. *Mentor confirmation requested.*
- **Row-count variance (not errors):** CIC-IoT2023 7.33 M → 7.85 M is **Kaggle mirror variance**;
  TON_IoT 461 k → 211 k is a **50k-Normal variant** (attack rows identical) → pin source + checksum.
- **Missing coarse labels** in the CIC-IoT2023 Kaggle build (7-category / binary).

## 5. Verified sources
- CIC-IoT2023 — official: <https://www.unb.ca/cic/datasets/iotdataset-2023.html> ·
  Kaggle: <https://www.kaggle.com/datasets/himadri07/ciciot2023> ·
  paper: Neto et al., *CICIoT2023*, Sensors 2023.
- TON_IoT — official: <https://research.unsw.edu.au/projects/toniot-datasets> ·
  Kaggle: <https://www.kaggle.com/datasets/arnobbhowmik/ton-iot-network-dataset> ·
  paper: Moustafa, *TON_IoT*, 2021.
- BoT-IoT — official: <https://research.unsw.edu.au/projects/bot-iot-dataset> ·
  paper: Koroniotis et al., *Towards the development of realistic botnet dataset…*, FGCS 2019.
- *(Also downloaded, not in Day-1 scope)* Edge-IIoTset — Ferrag et al., 2022:
  <https://www.kaggle.com/datasets/mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot>

## 6. Supplementary — datasets added on Day 2 (Edge-IIoTset, UNSW-NB15)
| Property | **Edge-IIoTset (ML)** | **UNSW-NB15 (ML-ready)** | **UNSW-NB15 (raw)** |
|---|---|---|---|
| Producer / year | Ferrag et al. 2022 | Moustafa & Slay 2015 | (same) |
| Rows (measured) | 157,800 | 257,673 | 2,540,047 |
| Columns / features | 63 / 61 | 45 / 42 | 49 / 47 |
| Label(s) | Attack_label + Attack_type (15) | attack_cat (10) + label | attack_cat (11¹) + Label |
| Benign / Normal | 15.4 % | 36.1 % | 87.4 % (blank) |
| Feature-space dup | 0.5 % | **40.4 %** | 20.3 % |
| Quality grade | B+ | C | D |
| IoT-specific? | yes (IoT/IIoT) | **no** (enterprise) | no |

¹ 11 because the raw splits **"Backdoor" (1,795)** and **"Backdoors" (534)** — a label-consistency flaw.
Edge-IIoTset: <https://www.kaggle.com/datasets/mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot> ·
UNSW-NB15: <https://research.unsw.edu.au/projects/unsw-nb15-dataset>. Full EDA: `04`/`05`.

## Concerns & Recommendations
- **Concern:** the five datasets are schema- and label-incompatible, and three (TON_IoT, BoT-IoT,
  UNSW-NB15) lose 40–56 % of rows to feature-space duplication — a "unified, large" corpus is smaller
  and messier than the row counts suggest.
- **Recommendation:** agree a **canonical trio** with the mentor (IoT-focused → CIC-IoT2023 + TON_IoT +
  BoT-IoT and/or Edge-IIoTset; UNSW-NB15 is **non-IoT**, best used as a cross-domain zero-day test),
  then run QADCP dedup/harmonization before any cross-dataset claim.

---
*Numbers reproduced by [`scripts/profile_datasets.py`](../scripts/profile_datasets.py); raw output in
`reports/_generated/summary.csv` and `*_profile.json`.*
