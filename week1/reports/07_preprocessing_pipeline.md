# Deliverable (Day 3) — Automated Preprocessing Pipeline & Cleaned Datasets

**QS-Net / QuantumSentinel — Team A** · Week 1 · Day 3.
Task (`first 7 days task.pdf`): *missing-value handling, duplicate removal, categorical encoding,
normalization, feature scaling, validation → automated preprocessing pipeline and cleaned datasets.*
Implementation: [`scripts/preprocess.py`](../scripts/preprocess.py) (deterministic, seed 42). Cleaned
data → each `datasets/<name>/processed/` (Parquet + sample CSV + meta JSON), pinned in
[`../manifest/MANIFEST.md`](../manifest/MANIFEST.md).

## 1. Pipeline (implements R1–R5 from `00`/`04`)
Each dataset is **stratified-capped to ~200k rows** (keep all rare-class rows, proportionally sample
the majority; seed 42) before the in-memory steps, then:

1. **Schema-normalize** — strip headers / BOM; fix BoT-IoT trailing-space `subcategory `.
2. **Label harmonize (R5)** — `label_multiclass` (strip, UNSW `"Backdoors"→"Backdoor"`, blank→`"Normal"`)
   + derived `label_binary` (0 = benign/normal). *(Done before capping so rare-class detection is clean.)*
3. **Drop structural columns** — identifiers / empty / zero-variance from [`feature_inventory.csv`](feature_inventory.csv).
4. **`-`/blank/`0.0.0.0`/`nan` → `NaN` (R2)**.
5. **Drop >95 %-missing columns**, then **impute** (numeric = median, categorical = `"missing"`).
6. **Encode categoricals** — high-cardinality object (> 1,000 uniques) ⇒ **drop** (identifier/free-text);
   low-cardinality ⇒ **ordinal**.
7. **Robust scale (R3)** — `log1p` for heavy-tailed non-negative features, then median/IQR scaling.
8. **Perfect-duplicate correlation prune (R4)** — drop one of each **|r| ≥ 0.99** pair.
9. **Feature-space de-duplication (R1)** — on the final cleaned schema (column drops can create new
   dupes), guaranteeing unique feature vectors.
10. **Validate + write** — assert 0 residual NaN and 0 duplicate feature rows; write Parquet + 1k CSV
    sample + `_clean_meta.json`.

## 2. Per-dataset before → after
| Dataset | Raw | Capped | **Cleaned (rows × feat)** | Feat-dupes removed | Classes | Attack % |
|---|---|---:|---|---:|---:|---:|
| CIC-IoT2023 | 1,176,851 × 47 ¹ | 200,000 | **199,799 × 37** | 201 (0.1 %) | 34 | 97.7 % |
| TON_IoT | 211,043 × 44 | 199,998 | **89,136 × 22** | 110,862 (**55.4 %**) | 10 | 74.5 % |
| BoT-IoT | 296,000 × 35 ² | 200,000 | **111,085 × 18** | 88,915 (**44.5 %**) | 4 ² | 99.96 % |
| Edge-IIoTset | 157,800 × 63 | 157,800 | **152,210 × 42** | 5,590 (3.5 %) | 15 | 84.1 % |
| UNSW-NB15 | 257,673 × 45 | 200,000 | **122,657 × 41** | 77,343 (**38.7 %**) | 10 | 45.4 % |

¹ CIC source = the validation split (a representative random split), then capped. ² BoT-IoT source =
a 4k-rows-per-file head-sample (296k) across the 74 files; the **Theft** class (1,587 of 73 M) does not
appear in that sample → 4 categories here (see Concerns).

**The dedup rates confirm the Day-2 EDA:** removing identifiers exposes ~40–56 % feature-space
duplicates in TON_IoT / BoT-IoT / UNSW-NB15 — those rows are now removed, so the cleaned tables hold
**only unique feature vectors** (leakage-safe basis for splitting on Day 6).

## 3. What each dataset needed (highlights)
- **CIC-IoT2023** — cleanest: dropped 3 zero-variance (`Telnet/SMTP/IRC`) + 5 perfect-corr pairs
  (**`Rate`=`Srate`, `IPv`=`LLC`**, `Std`≈`Radius`, `Tot sum`≈`AVG`, `IAT`≈`Number`).
- **TON_IoT** — `-`→NaN then **dropped 8 columns >95 % missing** (`http_*`, `ssl_cipher`); encoded
  `proto/service/conn_state/dns_*`.
- **BoT-IoT** — dropped all **14 identifier/empty** columns (`pkSeqID, stime, ltime, seq, s/daddr,
  s/dport, smac…dco`); encoded `flgs/proto/state`; 10 features log1p-scaled.
- **Edge-IIoTset** — dropped 8 zero-variance + **8 high-cardinality identifiers/free-text**
  (`ip.src_host, ip.dst_host, frame.time, tcp.payload, http.request.full_uri, …`) + the perfect-corr
  **MQTT block** (`mqtt.conflags`=`mqtt.proto_len`=`mqtt.ver`, r=1.0).
- **UNSW-NB15** — label harmonized to **10 classes** (`"Backdoors"→"Backdoor"`); dropped `id` and the
  `is_ftp_login`=`ct_ftp_cmd` (r=0.999) pair; encoded `proto/service/state`.

## 4. Output schema
Every `processed/<name>_clean.parquet` = **numeric feature columns** (encoded + scaled) +
**`label_multiclass`** (harmonized fine label) + **`label_binary`** (0/1). Uniform label schema across
datasets seeds the Day-6 unified schema. Companions: `_sample.csv` (1k preview), `_clean_meta.json`
(every drop/encode/scale decision, before/after counts). All git-ignored under `datasets/` but
**checksum-pinned** in the manifest.

## Concerns & Recommendations
**Concerns**
- **C1 — BoT-IoT Theft missing in the sample.** The head-sample (4k/file) omits the ultra-rare Theft
  class (Keylogging 1,469 / Data_Exfiltration 118 in 73 M). The cleaned BoT set has 4 categories, not 5.
- **C2 — Capped dedup ≠ full-scale dedup.** Dedup runs on the ~200k cap, not the full set; true unique
  counts at full scale differ (esp. BoT-IoT 73 M).
- **C3 — Mid-cardinality ordinals.** `dns_query` (718) and `proto` (133, UNSW) were ordinal-encoded
  (< 1,000 threshold); ordinal codes impose a false order and may mislead distance-based / quantum kernels.
- **C4 — Scaling is dataset-local.** Median/IQR params are fit per dataset on the cap; a train-only fit
  is required once splits exist (avoid test leakage).

**Recommendations**
- **R-a (Day 5/6 scale-up):** re-run with **targeted rare-class sampling** (guarantee Theft + all
  minorities) and **stream-dedup** BoT-IoT/CIC at full scale before the final Train/Val/Cal/Test/Zero-Day splits.
- **R-b:** for mid-cardinality categoricals, prefer **frequency/target encoding or hashing** over ordinal
  before quantum encoding; leave final selection to **Team C**.
- **R-c:** fit scalers/encoders on **train only** (persist them) once Day-6 splitting exists — the current
  `_clean_meta.json` already records the parameters to move to a fit/transform split.
- **R-d:** keep `label_multiclass` + `label_binary`; add the cross-dataset **unified family** label on Day 6.

---
*Reproduce:* `python week1/scripts/preprocess.py` → `datasets/<name>/processed/`; then
`python week1/scripts/make_manifest.py` pins the outputs (`--verify` = 0 mismatch). Python 3.12 venv.
