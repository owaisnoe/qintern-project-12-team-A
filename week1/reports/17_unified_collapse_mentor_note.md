# Mentor Note — Unified Schema Zero-Day Collapse

**QS-Net / QuantumSentinel — Team A** · Week 1 follow-up.
**Audience:** mentors · **Trigger:** Team B reported that TON_IoT `unified/qadcp/quantum/q8_zeroday.parquet` is effectively unusable for zero-day evaluation.

Related docs: [`12_unified_schema.md`](12_unified_schema.md) · [`13_unified_package.md`](13_unified_package.md) · [`14_handover_report.md`](14_handover_report.md)

---

## ✅ Mentor decision (approved)

> As discussed, we're locking the benchmark to **CIC, BoT, and UNSW only**. These are the three datasets whose zero-day and training splits survive the unified schema intact, so every result we publish will be statistically meaningful. We're **setting TON and Edge aside** because the shared 17-feature schema blurs their attack flows into noise — a benchmark built on 1–2 rows isn't a benchmark. Nothing about our methods changes: QADCP, difficulty-aware splits, MAQT, conformal prediction, MO-AQPSO, and all four evaluation axes stay exactly as planned.

### Approved benchmark policy

| Dataset | Unified v1.0 benchmark role | Notes |
|---------|----------------------------|-------|
| **CICIoT2023** | ✅ **In benchmark** | train + val + cal + test + zeroday (100 % row parity) |
| **BoT-IoT** | ✅ **In benchmark** | train + val + cal + test + zeroday (100 % zeroday parity) |
| **UNSW-NB15** | ✅ **In benchmark** | train + val + cal + test + zeroday (75 % zeroday retained) |
| TON_IoT | ❌ **Set aside** | unified zeroday = 1 row; v0.1 package preserved for reference only |
| Edge-IIoTset | ❌ **Set aside** | unified zeroday = 2 rows; train 12 % retained; v0.1 preserved |

**Team B / published results:** use `datasets/{CICIoT2023,BoT-IoT,UNSW-NB15}/unified/qadcp/` only.

**Methods unchanged:** QADCP · difficulty-aware zero-day tiers · MAQT · CQ-ZDR (conformal) · MO-AQPSO · four evaluation axes.

---

## 1. Summary

Day 6 projected all five datasets onto a **shared 17-feature network-flow schema** so Team B/C could train cross-dataset QML models. The projection is **successful for training on CIC, BoT, and UNSW**, but **collapses zero-day holdout splits on TON_IoT and Edge-IIoTset** to 1–2 rows. This is not a labelling error — the surviving rows are correctly tagged `ransomware` / `Ransomware` — but the benchmark is statistically meaningless.

We need mentor guidance on whether to (a) accept a **train-only role** for the collapsing datasets in the unified package, (b) extend the schema by one column, or (c) keep them on the legacy v0.1 package only.

**Update:** mentors approved **Option C variant** — benchmark locked to **CIC + BoT + UNSW**; TON and Edge set aside (see decision box above). Sections 5–8 below retain the analysis that informed that decision.

---

## 2. What happened

Two pipeline stages combine to produce the collapse:

### Step A — Projection information loss (Day 6)

The unified schema keeps only coarse flow statistics (`duration`, packet/byte counts, rates, protocol/state). Dataset-specific discriminative columns are dropped — e.g. TON's `src_ip_bytes`, `dst_ip_bytes`, DNS/HTTP fields, Edge's MQTT/TCP/UDP sensor features.

Many distinct attack flows (including ransomware) map to **identical 17-dimensional vectors**.

**TON_IoT example (ransomware holdout):**

| Stage | Ransomware rows | Unique 17-feat vectors | Vectors shared with non-ransomware |
|-------|----------------:|-----------------------:|-----------------------------------:|
| v0.1 clean checkpoint | 254 | 254 | — |
| v1.0 unified checkpoint | 8 | 8 | **7 / 8** |

### Step B — Cross-split deduplication (Day 4 S7b, applied in unified mode)

QADCP resolves duplicate feature vectors across splits with priority **`train > val > calibration > test > zeroday`**. When a ransomware flow collides with a train flow on the 17 shared features, the **train copy wins** and the zero-day copy is dropped.

**TON_IoT zero-day funnel (v1.0 unified):**

```
254 ransomware (v0.1)
  →  8 after unified projection
  →  8 assigned to zeroday split (S7a)
  →  7 dropped by S7b (duplicate of train rows)
  →  1 row in zeroday.parquet
```

The single survivor is labelled `ransomware` but is **nearest-neighbour similar to `normal` / `xss` traffic** in q8 feature space — it does not represent a distinct zero-day signal.

---

## 3. Measured impact across datasets

### Zero-day row retention (v0.1 → v1.0 unified)

| Dataset | Holdout family | v0.1 zeroday | v1.0 zeroday | Retained |
|---------|---------------|-------------:|-------------:|---------:|
| CICIoT2023 | Mirai | 10,984 | 10,984 | **100 %** |
| BoT-IoT | Theft | 683 | 683 | **100 %** |
| UNSW-NB15 | Worms + Shellcode | 1,615 | 1,216 | 75 % |
| **TON_IoT** | **ransomware** | **254** | **1** | **0.4 %** |
| **Edge-IIoTset** | **Ransomware + Fingerprinting** | **10,548** | **2** | **0.02 %** |

### Train row retention (v0.1 → v1.0 unified)

| Dataset | v0.1 train | v1.0 train | Retained | Train viable? |
|---------|----------:|-----------:|---------:|:-------------|
| CICIoT2023 | 132,166 | 132,166 | 100 % | ✅ |
| BoT-IoT | 130,205 | 130,138 | 99.9 % | ✅ |
| TON_IoT | 62,215 | 60,308 | **96.9 %** | ✅ |
| UNSW-NB15 | 84,730 | 71,094 | 83.9 % | ✅ |
| Edge-IIoTset | 89,971 | 11,158 | **12.4 %** | ⚠️ |

**Key observation:** TON **mostly survives in train** (97 %); Edge **does not** — unified projection destroys 88 % of Edge train rows as well. The collapse is therefore asymmetric across datasets and across splits.

---

## 4. Why this surfaced now

Team B's notebooks load `unified/qadcp/quantum/q8_zeroday.parquet` as the primary 8-qubit path ([`11_qsnet_interface.md`](11_qsnet_interface.md)). On TON they found:

1. Only **one row** in the unified zero-day file (expected after collapse, but not obvious from the handover).
2. Missing labels in `q8_zeroday.parquet` — a **separate Day 4 export bug** in `qadcp.py` (label/index misalignment in `quantum/q8_*`); parent `zeroday.parquet` labels are correct. We are fixing and re-exporting that independently.

The collapse itself is a **Day 6 schema design consequence**, documented as a caveat but not gated in Day 7 acceptance.

---

## 5. Option A — Add one more unified column

We could extend the schema to **18 features** by adding a column that separates colliding flows on TON, e.g. `src_ip_bytes` (present in TON, absent elsewhere).

**Effect on TON ransomware separation (rough check on v0.1 clean features):**

| Feature set | Unique ransomware vectors | Overlap with non-ransomware |
|-------------|--------------------------:|----------------------------:|
| Current 17-feat unified core | 8 | 7 / 8 |
| Core + `src_ip_bytes` | **232** | 26 / 232 |
| Core + `dst_ip_bytes` | 16 | 6 / 16 |

`src_ip_bytes` is the stronger separator for TON ransomware.

**Problems with this approach:**

| Issue | Detail |
|-------|--------|
| **Cross-dataset sparsity** | `src_ip_bytes` exists in **TON only**; absent in CIC, BoT, Edge. Would be **NaN on ~60 %+ of rows** in a pooled cross-dataset train set. |
| **Qubit budget** | Team B targets **8 qubits**. We are already at 17 features → top-8 ranked subset. Adding an 18th column that is mostly NaN on 3/5 datasets gives Team C a sparse, dataset-imbalanced feature with little cross-dataset signal. |
| **Imputation distorts semantics** | Train-median imputation (our current convention) would fill CIC/BoT/Edge NaNs with a constant, wasting a qubit on a TON-specific proxy. |
| **Edge not fixed** | Edge collapse is driven by MQTT/IIoT sensor features, not IP-byte fields. One extra network-flow column does not recover Edge train (12 % retained) or zero-day (2 rows). |

**Verdict:** a single extra column **may partially rescue TON zero-day** but is a poor fit for cross-dataset QML under an 8-qubit cap and does not solve Edge.

---

## 6. Option B — Train-only role for collapsing datasets (our recommendation)

Accept that the 17-feature unified schema is a **cross-dataset training alignment layer**, not a universal zero-day benchmark layer.

### Proposed policy

| Dataset | Unified v1.0 role | Zero-day evaluation |
|---------|-------------------|---------------------|
| CICIoT2023 | train + val + cal + test + **zeroday** | v1.0 unified |
| BoT-IoT | train + val + cal + test + **zeroday** | v1.0 unified |
| UNSW-NB15 | train + val + cal + test + zeroday (75 % rows) | v1.0 unified (with caveat) |
| **TON_IoT** | **`train` (+ val/cal/test) only** | **v0.1** `qadcp/zeroday.parquet` (254 rows) |
| **Edge-IIoTset** | **exclude from unified pool** or v0.1 only | **v0.1** `qadcp/zeroday.parquet` (10,548 rows) |

**Rationale:**

- **TON** retains **96.9 % of train rows** on the unified schema — it adds diversity to cross-dataset MAQT training (9 known classes; `ransomware` held out) without pretending the unified zero-day split is usable.
- **Edge** loses **88 % of train rows** even before zero-day — it should **not** be pooled into unified training. Keep Edge on v0.1 for any IIoT-specific experiments.
- **CIC + BoT** remain the primary unified zero-day benchmark trio (per PDF scope) with full row parity.

### What Team B should do (interim)

```python
# Cross-dataset training — unified q8 train (after label fix)
ton_tr = pd.read_parquet("datasets/TON_IoT/unified/qadcp/quantum/q8_train.parquet")

# TON zero-day rejection eval — v0.1 only
ton_zd = pd.read_parquet("datasets/TON_IoT/qadcp/zeroday.parquet")          # 254 rows
# or v0.1 q8 with labels joined from parent split
```

---

## 7. Option C — No schema change; document and split packages

Keep the 17-feature schema as-is. Formalise two consumption paths:

| Package | Path | Purpose |
|---------|------|---------|
| **v1.0 unified** | `datasets/<name>/unified/qadcp/` | Cross-dataset QML (CIC + BoT + UNSW + TON train) |
| **v0.1 per-dataset** | `datasets/<name>/qadcp/` | Zero-day benchmarks on TON / Edge; richer per-dataset features |

This is what we documented in Week 1 handover; we now propose elevating it from a footnote to an **explicit mentor-approved policy**.

---

## 8. Decision requested → **Resolved**

| # | Question | Outcome |
|---|----------|---------|
| 1 | Accept train-only unified role for TON? | **No** — TON set aside from published benchmark |
| 2 | Exclude Edge from unified pool? | **Yes** — Edge set aside |
| 3 | Extend schema to 18 features? | **No** |
| 4 | Primary unified zero-day benchmark | **CIC + BoT + UNSW** (mentor-approved trio) |
| 5 | Dual-package policy | **Yes** — v1.0 unified for benchmark trio; v0.1 preserved for TON/Edge reference |

---

## 9. Concerns & Recommendations

- **Concern:** Week 1 handover pointed Team B at all five unified packages without hard-gating zero-day usability per dataset.
- **Recommendation (done):** adopt mentor-approved **CIC + BoT + UNSW** benchmark lock; update [`11_qsnet_interface.md`](11_qsnet_interface.md), [`14_handover_report.md`](14_handover_report.md), [`METADATA.md`](../METADATA.md).
- **Recommendation (done):** re-export `quantum/q8_*` with corrected label write in `qadcp.py` (Day 4 bug fix, independent of collapse decision).

---

*Evidence:* `datasets/*/unified/qadcp/qadcp_report.json` (S7b drop counts) · [`14_handover_report.md`](14_handover_report.md) §3 · Team B notebook feedback (Jul 2026).
