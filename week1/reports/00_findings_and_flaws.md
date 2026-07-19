# Data-Quality Findings & Flaws — CIC-IoT2023 · TON_IoT · BoT-IoT

**QS-Net / QuantumSentinel — Team A (Dataset Analysis & Quantum-Aware Dataset Curation)**
Week 1 · Day 1 · scope = the three datasets named in `first 7 days task.pdf`.

> **Why this document exists.** In the kick-off meeting the mentor (Dr. Sajwan) stated that Week 1 is
> about **finding the flaws** in the existing datasets (duplication, repetition, preprocessing issues)
> and using them to **justify and design a curation pipeline (QADCP)** — *not* about building a new
> dataset yet. This report is the evidence base for that pipeline. Every number is reproduced by
> [`scripts/profile_datasets.py`](../scripts/profile_datasets.py) on the downloaded CSVs.

## 0. Flaw matrix (at a glance)

| Flaw | CIC-IoT2023 | TON_IoT (Network) | BoT-IoT |
|------|:-----------:|:-----------------:|:-------:|
| Rows measured | 7,845,673 | 211,043 | 73,370,443 |
| Exact duplicate rows | 0.535 %¹ | **9.75 % (20,569)** | ~0 %² |
| Missing as literal `-` string | – | **4,384,861 cells** | – |
| Empty / all-null columns | – | – | **6** (`smac,dmac,soui,doui,sco,dco`) |
| Constant / zero-variance columns | **3** (`Telnet,SMTP,IRC`)¹ | 0 | (6 all-null, sample²) |
| Header row repeated in data files | – | – | **Yes — in all 74 files** |
| Trailing whitespace in header | – | – | **Yes — `subcategory `** |
| Unshuffled (temporal-slice) ordering | split-level | – | **Yes — 1 attack per file** |
| Leaky identifier columns | none | IPs/ports (4) | **14** (IDs/IPs/MACs/ports/ts) |
| Severe class imbalance | **Yes** (min 0.003 %) | moderate (mitm 0.49 %) | **Extreme** (Normal 0.013 %) |
| Row count vs docs | 7.33M→7.85M (mirror variance) | 461K→211K (variant: 50k Normal) | ~73.37M ✓ matches paper |

¹ CIC-IoT2023 duplicate/constant figures measured on the validation split (~1.18 M rows) for
memory reasons; representative of a random split. ² BoT-IoT duplicate/empty-column figures from a
210 K stratified sample across 7 files (loading all 14.6 GB is unnecessary for this check).

## 1. TON_IoT (Network) — the "dirty" dataset
- **9.75 % exact duplicate rows (20,569 of 211,043).** Directly matches the mentor's "duplication/
  repetition" concern. Must be de-duplicated before any split, or train/test leakage results.
- **4,384,861 cells hold the literal string `-`** (not `NaN`). Naïve `df.isna()` reports **zero**
  missing and silently treats `-` as a valid category. `-` is the placeholder for
  "protocol not applicable to this flow" across `service`, all `dns_*`, all `ssl_*`, most `http_*`,
  and `weird_*`. Many of these columns are therefore **>90 % `-`** → near-zero information.
- **Variant, not a partial download:** the downloaded file has **211,043 rows** vs the commonly-cited
  **461,043**. This is a **standard TON_IoT variant with 50k Normal instead of 300k** — the 9 attack
  classes are **identical** (9×20,000 + 1,043 MITM) and 461,043 − 250,000 = **211,043** exactly. The
  only open decision is **which Normal-count variant is canonical** for the project.
- **Leaky identifiers:** `src_ip, dst_ip, src_port, dst_port` encode the testbed topology; keeping
  them lets a model memorize "attacker IP" instead of learning traffic behaviour.

## 2. BoT-IoT — the "traps" dataset (74 files, ~73.4 M rows)
- **Header row repeated in every one of the 74 files.** `pd.concat` of naïvely-read files injects
  73 fake rows (`pkSeqID == "pkSeqID"`); confirmed programmatically. Always read with `header=0` per
  file or drop `pkSeqID`-non-numeric rows.
- **Trailing space in the header** → the last column parses as `'subcategory '`, so
  `df['subcategory']` raises `KeyError`. Fix: `df.columns = df.columns.str.strip()`.
- **Files are contiguous time slices, not shuffled** — e.g. `data_1.csv` is 99.8 % Reconnaissance.
  **No single file is representative**; any sampling must stream/stratify across all 74. Critically, a
  **random** train/test split on this time-ordered data **leaks temporally adjacent flows** across the
  split → use **time-aware / group splitting**, not `train_test_split(shuffle=True)`.
- **6 completely empty columns** (`smac, dmac, soui, doui, sco, dco` — 100 % null) → drop entirely.
- **14 leaky identifier columns** (`pkSeqID, stime, ltime, seq, saddr, daddr, sport, dport, smac,
  dmac, soui, doui, sco, dco`). After dropping empties + identifiers, only ~**18 usable flow
  features** remain (`flgs, proto, state, dur, pkts, bytes, spkts, dpkts, sbytes, dbytes, rate,
  srate, drate, mean, stddev, sum, min, max`).
- **`sport`/`dport` are `object`, not int** — they contain hex strings and blanks (ARP flows), so
  numeric parsing must be explicit.
- **Pathological imbalance:** **99.987 % of rows are attacks**; Normal = 9,543 and Theft = 1,587 out
  of 73.4 M. Undersampling the DDoS/DoS majority is mandatory; the full set is overkill for QML.

## 3. CIC-IoT2023 — the "clean but skewed" dataset
- **Cleanest of the three:** 0 missing, 0 placeholders, all 46 features numeric (already flow-
  aggregated), 0.5 % duplicates on the validation split.
- **3 zero-variance columns** (`Telnet, SMTP, IRC` — protocols that never appear) → drop.
- **Only the 34-class fine label is present** in this Kaggle build; the official **7-category** and
  **binary** groupings must be **re-derived** (needed to align with the other datasets and for the
  benchmark's binary/coarse tasks).
- **Severe imbalance:** DDoS/DoS/Mirai floods dominate (top class 15.4 %); Benign is 2.36 %; the
  rarest attacks are `Uploading_Attack` (208), `Recon-PingSweep` (347), `Backdoor_Malware` (574).
- **Kaggle mirror variance (not an error):** Discord note says 7,332,065; we measure **7,845,673**.
  Different Kaggle mirrors ship different subsets → this *motivates* pinning source URL + row count +
  checksum (§5), so all three team members train on identical bytes.
- Minor: header typo `Magnitue` (should be *Magnitude*); `Protocol Type` is a float code, not a name.

## 4. Cross-cutting issues (affect all three)
1. **Schema heterogeneity.** Three different feature worlds — CIC = aggregated flow statistics,
   TON = Zeek/Bro connection logs, BoT = Argus flow records. **Almost no identical column names.**
   A unified schema needs *semantic* mapping (see `02_feature_inventory.md`).
2. **Label-vocabulary mismatch.** `DDoS-ICMP_Flood` (CIC) vs `ddos` (TON) vs `DDoS/UDP` (BoT);
   `Backdoor_Malware` vs `backdoor`; `MITM-ArpSpoofing` vs `mitm`. Needs a harmonized ontology.
3. **Imbalance everywhere**, at very different severities → a single balancing policy won't fit all;
   QADCP must parameterize per-dataset sampling.
4. **Leakage risk** from identifier columns (IPs, ports, MACs, timestamps, sequence IDs) in TON &
   BoT — must be dropped before feature selection (Team C) and modelling (Team B).
5. **Source pinning needed** — row counts vary by Kaggle **mirror** (CIC-IoT2023) and by **variant**
   (TON_IoT Normal-count). These are **not errors**, but they mean the team can silently train on
   different bytes → a pinned, checksummed source manifest is required (§5). The "third dataset" is
   also inconsistent across docs (BoT-IoT vs UNSW-NB15 vs Edge-IIoTset).

## 5. What this means for the QADCP (design implications → Day 4)
The pipeline must include, in order: **schema normalization** (strip headers, unify column names) →
**identifier/empty-column drop** → **`-`/placeholder → missing** conversion → **de-duplication** →
**constant/zero-variance drop** → **label harmonization** to a common ontology → **per-dataset
balancing** (undersample majorities, keep rare classes) → **stratified subsampling** (esp. BoT-IoT)
→ **scaling/encoding** → **quantum-ready reduction** (feature budget for N qubits) → **reproducible
splits** (Train/Val/Calibration/Test/Zero-Day). Each step above is motivated by a specific measured
flaw in §1–§4.

**Reproducibility manifest (QADCP requirement) — ✅ implemented.** Because Kaggle mirrors and variants
differ, every file is **pinned by source URL + row count + SHA-256** so all three of us train on
byte-identical data. Datasets are now laid out as `datasets/<name>/{raw,processed}/`; the manifest is
[`../manifest/MANIFEST.md`](../manifest/MANIFEST.md) (generated by `scripts/make_manifest.py`; run
`--verify` to re-check before any experiment).

## 6. Open questions for the mentor
1. **Third dataset:** proceed with **BoT-IoT** (task PDF) — confirm vs UNSW-NB15 (overview PDF) /
   Edge-IIoTset (Discord note, already downloaded).
2. **Canonical variant/mirror:** which TON_IoT Normal-count variant (50k vs 300k) and which
   CIC-IoT2023 mirror do we pin? (All counts are valid — see §5 manifest; we just need one agreed source.)
3. **Quantum feature budget:** target qubit count → how aggressively QADCP should reduce features
   (coordinate with Team C's selection output).

## 7. Day-2 addendum — Edge-IIoTset & UNSW-NB15 + feature-space duplication
Coverage extended to **5 datasets**; full EDA in [`04_eda_report.md`](04_eda_report.md) and
[`05_data_quality_report.md`](05_data_quality_report.md).
- **UNSW-NB15** (both forms): **40 % train/test feature-space duplication** (leakage); `attack_cat`
  blank for Normal (87 % of raw) and a **"Backdoor" vs "Backdoors"** label split (1,795 + 534);
  `service` 55 % `-`; `is_ftp_login`/`ct_ftp_cmd` ~49 % missing; train/test files **name-swapped**;
  not IoT-specific.
- **Edge-IIoTset**: 8 zero-variance columns; the MQTT feature block is perfectly correlated (r=1.0);
  otherwise the cleanest alongside CIC-IoT2023.
- **Cross-dataset headline:** dropping identifiers exposes **40–56 % feature-space duplicates** in
  TON_IoT, BoT-IoT and UNSW-NB15 — now the single largest quality issue (under-counted on Day 1).

## Concerns & Recommendations
**Concerns:** hidden feature-space redundancy; missingness encoded as `-`/blank/empty (invisible to
`isna()`); heavy-tailed features (20–32 % IQR-outliers); redundant/perfectly-correlated features
wasting qubits; UNSW train/test overlap.
**Recommendations (QADCP):** (R1) de-duplicate on **feature columns** then split leakage-safe —
**time-aware** for BoT-IoT (temporal ordering); (R2) canonical `-`/blank/`0.0.0.0`→`NaN` before any
missing-value decision; (R3) robust (quantile/log1p) scaling, angle-encode only at the end;
(R4) correlation-prune |r|≥0.95 pairs; (R5) for UNSW-NB15 pool→dedup→re-split and normalize labels;
(R6) **pin source URL + row count + SHA-256 per file** — **done**: `datasets/<name>/{raw,processed}/`
+ [`../manifest/MANIFEST.md`](../manifest/MANIFEST.md) (`make_manifest.py --verify`). Full detail in `04`/`05`.

---
*Reproduce:* `source .venv/bin/activate && python week1/scripts/profile_datasets.py`
(Python 3.12; raw numbers in `reports/_generated/*.json` and `*_classdist.csv`).
