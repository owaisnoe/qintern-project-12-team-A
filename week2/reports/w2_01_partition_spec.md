# Week 2 · Day 8 — Partition Specification (conformal Train / Calibration / Test / Zero-Day)

**QS-Net / QuantumSentinel — Team A** · Week 2 · Day 8.
Task (`qi26_12_Week 2.pdf`): *re-partition each curated dataset into Train / Calibration / Test / Zero-Day,
holding out ≥1 entire attack class as unseen zero-day; document the exact class membership of every split;
the calibration set must contain KNOWN classes only.*
Script: [`../scripts/make_partitions.py`](../scripts/make_partitions.py) (seed 42) ·
Data: `week2/partitions/<name>/{train,calibration,test,zeroday}.csv` + `partition_meta.json` (full per-class counts).

## 1. Scope — mentor-locked benchmark trio

Per the **mentor decision**, the published benchmark is **CIC-IoT2023 + BoT-IoT + UNSW-NB15** only
(see [`../../week1/reports/17_unified_collapse_mentor_note.md`](../../week1/reports/17_unified_collapse_mentor_note.md)).
TON_IoT and Edge-IIoTset are **set aside** (their unified zero-day collapses to 1–2 rows). All three trio
datasets share the **17-feature unified schema** and retain full known-class + zero-day splits.

## 2. Construction — reuse the leakage-safe Week-1 assignment (no re-shuffle)

Partitions are the Week-1 **unified v1.0** splits (leakage-safe: split-first, train-fit scalers/encoders,
seed 42) re-shaped to the Week-2 4-way conformal layout:

| Week-2 split | Source (Week-1 unified) | Role |
|---|---|---|
| **Train** | `train` + `val` (val folded in) | MAQT training — known classes only |
| **Calibration** | `calibration` (unchanged) | CQ-ZDR threshold — **KNOWN classes only** |
| **Test** | `test` (unchanged) | known-class accuracy + certified radius |
| **Zero-Day** | `zeroday` (unchanged) | held-out attack class — rejection rate |

Folding `val` into `train` gives the conformal 4-way layout while leaving `calibration`/`test`/`zeroday`
**byte-identical to Week 1**, so the exchangeability verified on Day 9 is preserved exactly. Output is
CSV v1 = the 17 unified features + `label_multiclass` / `label_binary` / `label_family`.

## 3. Partition-specification table (measured)

| Dataset | Train | Calibration | Test | Zero-Day | # known classes | Held-out zero-day class(es) |
|---|---:|---:|---:|---:|---:|---|
| **CIC-IoT2023** | 151,049 | 18,883 | 18,883 | 10,984 | **31** | `Mirai-greeth_flood`, `Mirai-greip_flood`, `Mirai-udpplain` |
| **BoT-IoT** | 148,729 | 18,591 | 18,591 | 683 | **4** | `Theft` |
| **UNSW-NB15** | 81,215 | 10,112 | 10,086 | 1,216 | **8** | `Shellcode`, `Worms` |

**Known-class membership** (identical set across train / calibration / test per dataset — full per-class
counts in each `partition_meta.json`):
- **CIC-IoT2023 (31):** `BenignTraffic` + 7 DDoS-* + 3 DoS-* floods + Recon-* + web-injection
  (`SqlInjection`/`XSS`/`CommandInjection`/…) + `DictionaryBruteForce` + `Backdoor_Malware` + `DNS_Spoofing`/`MITM-*`.
- **BoT-IoT (4):** `DDoS`, `DoS`, `Normal`, `Reconnaissance`.
- **UNSW-NB15 (8):** `Normal`, `Exploits`, `Fuzzers`, `Reconnaissance`, `DoS`, `Generic`, `Analysis`, `Backdoor`.

## 4. Invariants (asserted in the script)

- ✅ **Zero-day = a full held-out attack class**, present **only** in `zeroday`, **0 rows** in train /
  calibration / test (checked per dataset).
- ✅ **Calibration = KNOWN classes only** — the zero-day family is absent by construction (required for the
  CQ-ZDR conformal threshold; see Day 9).
- ✅ **Deterministic** — seed 42; re-running reproduces identical partitions.

Exchangeability (calibration vs test drawn from the same known-class distribution) and the disjointness /
coverage checks are verified in **Day 9** ([`w2_02_split_integrity.md`](w2_02_split_integrity.md)); the
adversarial-vs-zero-day evaluation set is built in **Day 10** ([`w2_03_rq3_eval_set.md`](w2_03_rq3_eval_set.md)).

---
*Reproduce:* `python week2/scripts/make_partitions.py` → `week2/partitions/<name>/*.csv` +
`partition_meta.json` + `reports/_generated/partition_summary.json`.
