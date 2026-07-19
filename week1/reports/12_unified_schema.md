# Deliverable (Day 6) — Unified Feature Schema

**QS-Net / QuantumSentinel — Team A** · Week 1 · Day 6.
Machine-readable spec: [`../schema/unified_schema.json`](../schema/unified_schema.json).

## 1. Purpose

Days 1–5 produced **per-dataset** QADCP splits with incompatible column names. Day 6 projects every
dataset onto one **shared network-flow schema** so Team B/C can train on comparable features across
CIC-IoT2023, TON_IoT, BoT-IoT, Edge-IIoTset, and UNSW-NB15.

## 2. Unified columns (17 features + 3 labels)

| Column | Type | Semantics |
|--------|------|-----------|
| `duration` | float | Flow duration |
| `n_pkts_total` | float | Total packets in flow |
| `n_bytes_total` | float | Total bytes in flow |
| `src_pkts` | float | Source packets (NaN where absent → train-median impute) |
| `dst_pkts` | float | Destination packets |
| `src_bytes` | float | Source bytes |
| `dst_bytes` | float | Destination bytes |
| `rate` | float | Overall flow rate |
| `rate_src` | float | Source rate / load |
| `rate_dst` | float | Destination rate / load |
| `pkt_size_min` | float | Minimum packet size statistic |
| `pkt_size_max` | float | Maximum packet size statistic |
| `pkt_size_mean` | float | Mean packet size statistic |
| `pkt_size_std` | float | Std packet size statistic |
| `iat` | float | Inter-arrival time |
| `protocol` | float | Harmonized protocol (frequency-encoded on train) |
| `conn_state` | float | Harmonized connection state (frequency-encoded on train) |
| `label_multiclass` | str | Fine harmonized label |
| `label_binary` | int | 0/1 benign vs attack |
| `label_family` | str | 10-family ontology |

## 3. Harmonized vocabularies

**Protocol:** `tcp`, `udp`, `icmp`, `arp`, `dns`, `http`, `https`, `mqtt`, `other`

**Connection state:** `established`, `closed`, `syn`, `rst`, `rej`, `fin`, `other`

## 4. Per-dataset mapping

| Dataset | Duration | Packets | Bytes | Rate | Protocol source | State source |
|---------|----------|---------|-------|------|-----------------|--------------|
| CIC-IoT2023 | `flow_duration` | flag counts | `Tot sum` | `Rate` | TCP/UDP/ICMP one-hots | TCP flags |
| TON_IoT | `duration` | `src_pkts+dst_pkts` | `src_bytes+dst_bytes` | derived | ordinal `proto` | ordinal `conn_state` |
| BoT-IoT | `dur` | `pkts` | `bytes` | `rate` | ordinal `proto` | ordinal `state` |
| Edge-IIoTset | `udp.time_delta` | `tcp.len+udp.stream` | `http.content_length` | `udp.time_delta` | mqtt/tcp/udp/icmp/arp fields | TCP connection flags |
| UNSW-NB15 | `dur` | `spkts+dpkts` | `sbytes+dbytes` | `rate` | ordinal `proto` | ordinal `state` |

CIC checkpoint has `Drate` but no `Srate` — `rate_dst` ← `Drate`, `rate_src` ← NaN (train-median impute).

Directional packet/byte columns are **NaN** for CIC and Edge where absent; QADCP imputes with train medians.

## 5. Encoding policy

1. **Projection** (`unified_schema.py`): map clean checkpoints → unified columns; categoricals as `protocol_cat` / `conn_state_cat` strings.
2. **Feature-space dedup** on unified columns before QADCP.
3. **QADCP unified mode**: split first → **frequency-encode** `protocol_cat` / `conn_state_cat` on train only → impute NaN on train medians → scale → quantum tensors.

Ordinal encoding from Day 3 is **not** reused for the unified categoricals.

## 6. Output locations

```
datasets/<name>/unified/processed/<name>_unified.parquet
datasets/<name>/unified/qadcp/{train,val,calibration,test,zeroday}.parquet
```

v0.1 per-dataset outputs remain at `datasets/<name>/qadcp/` for comparison.

---

*Reproduce:* `python week1/scripts/unified_schema.py && python week1/scripts/qadcp.py --unified`
