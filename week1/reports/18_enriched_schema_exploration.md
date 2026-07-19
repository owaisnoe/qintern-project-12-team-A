# Appendix (Week 1) — Enriched Unified Schema Exploration (superseded; retained for the novel-dataset agenda)

**QS-Net / QuantumSentinel — Team A** · Week 1 · AK (@Thedaemon-AK).

> **Status: superseded — not in the benchmark.** The mentor decision ([`17`](17_unified_collapse_mentor_note.md))
> **set TON_IoT and Edge-IIoTset aside** rather than enrich the schema; the published benchmark is
> **CIC + BoT + UNSW** only. This document is the **executable, measured version of [`17`](17_unified_collapse_mentor_note.md)
> §5 "Option A"** (add discriminative columns to recover the collapsing zero-day splits): it quantifies
> exactly what a richer schema recovers and why one extra column alone was rejected under the 8-qubit cap.
> It is **retained** as (a) reproducible evidence behind that decision and (b) a **design template for the
> future "curate our own dataset" work** (a common *rich* feature set that does not collapse). It does
> **not** modify the frozen v1.0 — separate script [`scripts/unified_enrich.py`](../scripts/unified_enrich.py),
> separate schema [`schema/unified_schema_v2.json`](../schema/unified_schema_v2.json), separate output
> `datasets/<name>/unified_v1_1/qadcp/` (regenerable; not in the shipped benchmark package).

## 1. Problem — the v1.0 zero-day collapse on TON_IoT & Edge-IIoTset

v1.0's 17-feature down-map is a clean common-flow core, but its per-dataset projection sets **5 of 15
numerics to NaN for TON_IoT** (all packet-size stats + IAT) and **10 of 15 for Edge-IIoTset** (plus
`duration`≡`rate`, both `udp.time_delta`). The coarse vectors collapse under feature-space + cross-split
dedup, so the **zero-day holdout is wiped**: TON ransomware **1 row**, Edge Ransomware/Fingerprinting
**2 rows** ([`13`](13_unified_package.md) §4). Two of five datasets cannot be zero-day-evaluated in v1.0.

## 2. Approach — a richer, NetFlow-v2-aligned schema (30 features)

Grounded in the published cross-dataset standard — Sarhan, Layeghy & Portmann standardized UNSW-NB15,
BoT-IoT and ToN-IoT (+ CSE-CIC-IDS2018) to a common **43-feature NetFlow** set (the NF-\*-v2 datasets,
merged as NF-UQ-NIDS-v2)¹. v1.0's 17 is lean by comparison. v1.1 keeps v1.0's 17 as a subset and adds
**13 discriminative fields that already exist in the Day-3 clean checkpoints** but the 17-schema discards:

| Group | Enriched features (added to the v1.0 core) | Recovers |
|---|---|---|
| Directional bytes | `src_ip_bytes`, `dst_ip_bytes`, `missed_bytes` | TON |
| Application layer | `app_req_bytes`, `app_resp_bytes`, `dns_signal` | TON, Edge |
| TCP session | `tcp_seq`, `tcp_ack`, `dstport`, `flag_count` | Edge |
| Host/flow | `ttl_total` | UNSW |
| Categoricals | `service` (Zeek service / inferred), `app_proto` (freq-encoded, train-fit) | TON, Edge, CIC, UNSW |

Total **30 features** (26 numeric + 4 frequency-encoded categoricals). Each dataset fills what it has;
missing → NaN + **train-median impute** (identical policy to v1.0). The pipeline **reuses the verified
`qadcp.process_dataframe`** (leakage-safe split → S7b cross-split dedup → train-fit encode/impute/scale →
angle **[0, π]** → S8 gates) — so v1.1 inherits every guarantee, unchanged.

## 3. Result — measured zero-day recovery (leakage-safe)

| Dataset | Holdout family | v1.0 (17f) zeroday | **v1.1 (30f) zeroday** | Δ |
|---|---|---:|---:|---:|
| CIC-IoT2023 | Mirai | 10,984 | 10,984 | +0 |
| **TON_IoT** | ransomware | **1** | **253** | **+252** |
| BoT-IoT | Theft | 683 | 683 | +0 |
| **Edge-IIoTset** | Ransomware + Fingerprinting | **2** | **9,042** | **+9,040** |
| UNSW-NB15 | Worms + Shellcode | 1,216 | 1,321 | +105 |

Edge v1.1 zero-day = Ransomware 8,910 + Fingerprinting 132; TON = ransomware 253. **TON and Edge are now
zero-day-evaluable in the unified schema.** CIC/BoT are unchanged (already rich enough at 17f).

**Leakage-safety independently re-checked** (not just the built-in S8 asserts): for every dataset the
holdout families are **absent from train** and the **train∩zeroday feature-hash overlap is 0**; the
recovery is genuine separation, not leakage. Angle features verified ∈ **[0, π]**; splits carry all 3
labels; encoders/scalers fit on **train only**.

## 4. Why it works

The collapse was never intrinsic to ransomware/fingerprinting — it was the coarse projection making
distinct flows *look* identical, so cross-split dedup discarded them as train-duplicates. Restoring
`service` (Zeek distinguishes ransomware's HTTP/SSL/DNS mix), directional `*_ip_bytes`/`missed_bytes`,
application-layer byte counts, and TCP `seq`/`ack`/`dstport` (Edge fingerprinting is a port/seq scan)
re-separates those flows from benign/other-attack traffic — so the holdout survives.

## 5. Recommendation for Day 7 (Iwo owns the schema decision)

1. **Adopt the enriched schema for TON_IoT & Edge-IIoTset** (at minimum) so all five datasets have a
   usable unified zero-day split — the Day-6 task asks for *"Train/Val/Calibration/Test/Zero-Day"* on the
   unified schema, which v1.0 cannot satisfy for 2/5.
2. Or ship **both**: v1.0 (leanest 17-feature shared core for the strictest cross-dataset comparison) and
   v1.1 (30-feature, zero-day-complete). Team B picks per experiment; the split names/contract are identical.
3. For the strongest grounding, converge toward the **NetFlow-v2 43-feature standard**¹ at full-raw scale
   (Day-7+); ready-made **NF-BoT-IoT-v2 / NF-ToN-IoT-v2 / NF-UNSW-NB15-v2** already exist for 3 of the 5.

## 6. Limitations (honest)

- Some enriched fields are **dataset-specific** (NaN elsewhere → imputed), so v1.1 is slightly less "pure
  shared core" than v1.0 — a deliberate trade of schema minimalism for zero-day coverage.
- **Edge** recovery leans on `tcp.seq`/`tcp.ack`/`dstport`; Edge is packet-level, so these are
  packet-fields, not true flow aggregates — the *proper* fix is flow re-aggregation from raw PCAP (Day-7+).
- Still **checkpoint scale** (~200k caps), like v1.0.
- Difficulty **tier re-scoring** on the recovered TON/Edge splits (via `zero_day_tiers.py`) is the natural
  next step — now possible because the splits are no longer 1–2 rows.

## Concerns & Recommendations

**Concern:** without this (or an equivalent richer schema), the shipped unified package cannot present a
zero-day benchmark for TON_IoT or Edge-IIoTset — a visible gap at the Day-7 integration meeting.
**Recommendation:** adopt v1.1 (or the NetFlow-v2 standard) for those two datasets; keep v1.0 as the
minimal shared core. Both are checksum-reproducible from the committed scripts.

---
¹ M. Sarhan, S. Layeghy, N. Moustafa, M. Portmann, *"NetFlow Datasets for ML-Based NIDS"* / *"Towards a
Standard Feature Set for NIDS Datasets"* (arXiv:2011.09144, 2101.11315) — 43-feature common NetFlow schema
across UNSW-NB15 / BoT-IoT / ToN-IoT / CSE-CIC-IDS2018.
*Reproduce:* `python week1/scripts/unified_enrich.py` (seed 42; reuses `qadcp.process_dataframe`;
→ `datasets/<name>/unified_v1_1/qadcp/` + `reports/_generated/unified_enriched_recovery.json`).
