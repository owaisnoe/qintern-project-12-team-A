# Deliverable 2 — Feature Inventory

**QS-Net / QuantumSentinel — Team A** · Week 1 · Day 1.
Per-dataset feature catalogue + a **cross-dataset semantic mapping** (the "identify common features"
task). Exhaustive per-column stats (dtype, #unique, #missing, example) are in the machine-readable
[`feature_inventory.csv`](feature_inventory.csv); this document groups them and adds **keep/drop**
recommendations for the QADCP.

## 1. Feature budget summary

| Dataset | Raw features | Drop (reason) | Usable features |
|---|---:|---|---:|
| CIC-IoT2023 | 46 | 3 zero-variance (`Telnet`, `SMTP`, `IRC`) | **43** |
| TON_IoT | 42 | 4 identifiers (`src_ip`, `dst_ip`, `src_port`, `dst_port`); dash-placeholder cleanup collapses ~13 sparse protocol cols | **~25** |
| BoT-IoT | 32 | 6 empty (`smac`, `dmac`, `soui`, `doui`, `sco`, `dco`); 8 identifiers (`pkSeqID`, `stime`, `ltime`, `seq`, `saddr`, `daddr`, `sport`, `dport`) | **~18** |

## 2. CIC-IoT2023 — 46 features (all `float64`; no missing)

| Semantic group | Columns | Keep? |
|---|---|---|
| Flow timing | `flow_duration`, `Duration`, `IAT`, `Header_Length` | Yes |
| Rates | `Rate`, `Srate`, `Drate` | Yes |
| TCP-flag flags (binary) | `fin_flag_number`, `syn_flag_number`, `rst_flag_number`, `psh_flag_number`, `ack_flag_number`, `ece_flag_number`, `cwr_flag_number` | Yes |
| TCP-flag counts | `ack_count`, `syn_count`, `fin_count`, `urg_count`, `rst_count` | Yes |
| Protocol one-hots | `HTTP`, `HTTPS`, `DNS`, `SSH`, `TCP`, `UDP`, `DHCP`, `ARP`, `ICMP`, `IPv`, `LLC` | Yes |
| Protocol one-hots (dead) | `Telnet`, `SMTP`, `IRC` | No (zero-variance) |
| Packet-size statistics | `Tot sum`, `Min`, `Max`, `AVG`, `Std`, `Tot size`, `Number`, `Magnitue`, `Radius`, `Covariance`, `Variance`, `Weight` | Yes |
| Protocol code | `Protocol Type` | Yes (numeric code) |

Note: `Magnitue` is a typo for *Magnitude* in the source — keep the name for traceability.

## 3. TON_IoT (Network) — 42 features

| Semantic group | Columns | Keep? |
|---|---|---|
| Identifiers (leaky) | `src_ip`, `dst_ip`, `src_port`, `dst_port` | No (topology leakage) |
| Core flow | `proto`, `service`, `duration`, `conn_state`, `missed_bytes` | Yes (encode `proto` / `service` / `conn_state`) |
| Byte/packet counts | `src_bytes`, `dst_bytes`, `src_pkts`, `dst_pkts`, `src_ip_bytes`, `dst_ip_bytes` | Yes |
| DNS context | `dns_query`, `dns_qclass`, `dns_qtype`, `dns_rcode`, `dns_AA`, `dns_RD`, `dns_RA`, `dns_rejected` | Review (mostly dash placeholders) |
| SSL context | `ssl_version`, `ssl_cipher`, `ssl_resumed`, `ssl_established`, `ssl_subject`, `ssl_issuer` | Review (mostly dash placeholders; low value) |
| HTTP context | `http_trans_depth`, `http_method`, `http_uri`, `http_version`, `http_request_body_len`, `http_response_body_len`, `http_status_code`, `http_user_agent`, `http_orig_mime_types`, `http_resp_mime_types` | Review (mixed; keep numeric lengths/status) |
| Zeek "weird" | `weird_name`, `weird_addl`, `weird_notice` | Review (mostly dash placeholders) |

After converting dash placeholders to missing, the DNS/SSL/HTTP/weird object columns are largely empty for non-web flows. QADCP should keep the **numeric** ones (`*_bytes`, `*_body_len`, `http_status_code`, `dns_q*`) and either drop or binary-encode ("present/absent") the sparse categorical ones.

## 4. BoT-IoT — 32 features

| Semantic group | Columns | Keep? |
|---|---|---|
| Identifiers (leaky) | `pkSeqID`, `stime`, `ltime`, `seq`, `saddr`, `daddr`, `sport`, `dport` | No |
| Empty (100% null) | `smac`, `dmac`, `soui`, `doui`, `sco`, `dco` | No |
| Core flow | `proto`, `flgs`, `state`, `dur` | Yes (encode `proto` / `flgs` / `state`) |
| Packet/byte counts | `pkts`, `bytes`, `spkts`, `dpkts`, `sbytes`, `dbytes` | Yes |
| Rates | `rate`, `srate`, `drate` | Yes |
| Inter-packet statistics | `mean`, `stddev`, `sum`, `min`, `max` | Yes |

`sport` / `dport` are `object` (hex strings + blanks) — even if kept for analysis they need explicit numeric parsing; recommended **dropped** as leaky identifiers.

## 5. Cross-dataset semantic mapping (common features)

The unifying abstraction is the **network flow**. Same concept, three vocabularies:

| Unified concept | CIC-IoT2023 | TON_IoT | BoT-IoT | In all 3? |
|---|---|---|---|:---:|
| Flow duration | `flow_duration` / `Duration` | `duration` | `dur` | Yes |
| Protocol | `TCP`/`UDP`/`ICMP` one-hots | `proto` (+ `service`) | `proto` | Yes |
| Total packets | `Number` (a) | `src_pkts` + `dst_pkts` | `pkts` (= `spkts` + `dpkts`) | Yes |
| Total bytes | `Tot sum` / `Tot size` | `src_bytes` + `dst_bytes` | `bytes` (= `sbytes` + `dbytes`) | Yes |
| Flow rate | `Rate` / `Srate` / `Drate` | derive `pkts/duration` | `rate` / `srate` / `drate` | Yes |
| Connection state | flag flags/counts | `conn_state` | `state` / `flgs` | Yes |
| Source packets | — | `src_pkts` | `spkts` | TON+BoT |
| Dest. packets | — | `dst_pkts` | `dpkts` | TON+BoT |
| Source bytes | — | `src_bytes` | `sbytes` | TON+BoT |
| Dest. bytes | — | `dst_bytes` | `dbytes` | TON+BoT |
| Packet-size stats | `Min`/`Max`/`AVG`/`Std` | — | `min`/`max`/`mean`/`stddev` | CIC+BoT |
| Inter-arrival time | `IAT` | — | — | CIC only |

(a) CIC-IoT2023 exposes aggregate/statistical counts rather than a raw packet total; `Number` and the byte-sum features are the closest proxies.

**Literal column-name overlap across the three datasets is approximately 0.** Any unified schema must be built on this **semantic** table, not string matching.

## 6. Proposed seed of the unified schema (Day 6)

A minimal, robust common core present (directly or by trivial derivation) in **all three**:

`duration`, `protocol`, `n_pkts_total`, `n_bytes_total`, `rate`, `conn_state`

Extendable with the directional split (`src`/`dst` pkts/bytes) for TON_IoT + BoT-IoT and the size-statistics block for CIC + BoT. Categorical fields (`proto`, `service`, `conn_state`, `flgs`, `state`) need consistent encoding; the target **quantum feature budget** (qubit count, from Team C / mentor) will drive final dimensionality.

**Note on counts.** `feature_inventory.csv` marks only **structural** drops (identifiers, empty, zero-variance) — so TON_IoT shows 38 "keep". The "~25 usable" above additionally prunes the ~13 DNS/SSL/HTTP/weird columns that collapse to near-constant once dash placeholders become missing; that sparsity pruning is finalized during preprocessing (Day 3), not baked into the structural CSV.

## 7. Day 2 — Edge-IIoTset and UNSW-NB15 feature groups

`feature_inventory.csv` now covers all **6 views**. Highlights:

- **Edge-IIoTset (61 feat):** protocol-field features (`arp.*`, `icmp.*`, `tcp.*`, `http.*`, `mqtt.*`, `mbtcp.*`, `dns.*`). Drop 8 zero-variance (`icmp.unused`, `http.tls_port`, `mbtcp.*`, etc.) and one of each perfectly correlated MQTT pair; keep `ip.src_host` / `ip.dst_host` out of modelling (identifiers).
- **UNSW-NB15 (ML 42 / raw 47 feat):** rich flow+content+time features (`dur`, `sbytes`/`dbytes`, `Sload`/`Dload`, `Sjit`/`Djit`, `ct_*_ltm`, `tcprtt`, `synack`, `ackdat`). Drop `id` (ML) and `srcip`/`sport`/`dstip`/`dsport`/`Stime`/`Ltime` (raw). Redundant pairs: `is_ftp_login` ~ `ct_ftp_cmd` (0.999), `*bytes` ~ `*loss`, `swin` ~ `dwin`.

Extended common core: **duration, bytes (src/dst), packets (src/dst), rate/load, protocol, state** all have direct UNSW-NB15 equivalents — UNSW-NB15 is the **richest** schema and the best template for the unified schema (Day 6).

## Concerns and Recommendations

- **Concern:** usable feature counts differ ~3x (BoT-IoT ~18 vs Edge-IIoTset 53) — a unified schema must **down-map to the common core**, not up-pad missing dimensions.
- **Recommendation:** correlation-prune per dataset first (cheapest qubit saving), build the unified schema on UNSW-NB15's directional flow features, then hand the pruned set to Team C for selection.

---

*Per-column raw stats: [`feature_inventory.csv`](feature_inventory.csv) (regenerate via [`../scripts/build_feature_inventory.py`](../scripts/build_feature_inventory.py)); profiles in `reports/_generated/` (from [`../scripts/profile_datasets.py`](../scripts/profile_datasets.py)).*
