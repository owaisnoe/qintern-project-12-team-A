# Dataset Challenges, Strengths & Novel-Dataset Design Inputs

**QS-Net / QuantumSentinel — Team A** · Week 1 consolidation (mentor-requested).
**Audience:** mentors + team. **Purpose:** per the **mentor request** at the Week-1 review, this pins — in
one place — the dataset **positives, challenges, and issues** we hit while building the QADCP, and turns
them into concrete **design inputs for a future "curate our own dataset"** effort (the Team-A novelty).
It consolidates and extends the flaw registers ([`00`](00_findings_and_flaws.md), [`05`](05_data_quality_report.md))
and the collapse note ([`17`](17_unified_collapse_mentor_note.md)); the enriched-schema exploration
([`18`](18_enriched_schema_exploration.md)) is the executable evidence behind §3.

## 1. Challenges (measured)

### Cross-cutting
| Challenge | Evidence | Consequence |
|---|---|---|
| **Severe class imbalance** | CIC-IoT2023 up to **7,698 : 1** (benign vs rarest attack); BoT-IoT `Theft` = 1,587 of 73 M | rare-class prototypes ρ_c noisy; needs capping + rare-class-preserving sampling |
| **Feature-space duplication** | after dropping identifiers, **40–56 %** of rows are duplicate vectors (TON 55.6 %, BoT 51.4 %, UNSW 40.4 %) | row counts mislead; dedup mandatory before split (else train/test leakage) |
| **Schema heterogeneity** | 5 datasets, 15–42 native features, different vocabularies (Zeek vs Argus vs packet-level) | no shared feature set → the Day-6 unification, and its collapse (below) |
| **Mirror / variant variance** | CIC 7.85 M vs docs' 7.33 M; TON 211 k (a standard 50k-normal variant, not partial) | must pin **source URL + rows + SHA-256** (manifest) so all members train on identical bytes |
| **Categorical encoding** | native ordinal codes imply a false distance metric | switched to **frequency encoding** (train-fit) for the unified schema |

### Per-dataset
| Dataset | Key issue |
|---|---|
| **CIC-IoT2023** | 34-class label only; extreme imbalance; 4 ultra-rare known classes (≤ 9 cal/test rows) → marginal-only conformal |
| **TON_IoT** | Zeek-rich but **unified zero-day collapses 254 → 1** (discriminative `*_ip_bytes`/DNS/HTTP fields dropped) → **set aside** |
| **BoT-IoT** | 73 M rows, 99.99 % attacks, **unshuffled temporal order** (`stime` dropped → stratified, not time-aware → possible temporal leakage); `Theft` ultra-rare (recovered to 683 via raw re-run) |
| **Edge-IIoTset** | packet-level (MQTT/TCP sensor fields); **unified train collapses to 12 %**, zero-day to 2 rows → **set aside** |
| **UNSW-NB15** | **non-IoT** (cross-domain probe); train/test name-swap + 40 % overlap in the ML-ready form |

**Benchmark consequence (mentor decision):** the published benchmark is locked to **CIC-IoT2023 + BoT-IoT +
UNSW-NB15** — the three whose train **and** zero-day splits survive the 17-feature unified schema intact.
TON_IoT and Edge-IIoTset are **set aside** (v0.1 packages preserved for reference). See [`17`](17_unified_collapse_mentor_note.md).

## 2. Strengths (what the QADCP does well)

- **Leakage-safe by construction** — split **first**, then fit scalers / correlation-prune / ranking /
  angle-ranges / balancing **on train only**; a post-prune cross-split dedup (S7b) caught a real 13 k-vector
  leakage channel on Edge that most tutorial pipelines miss.
- **Conformal-ready partitions** — Train / **Calibration (known-only)** / Test / **Zero-Day (held-out class)**;
  Week-2 Day-9 verified exchangeability (cal↔test two-sample AUROC ≈ 0.50, coverage ≈ 0.90).
- **Difficulty-aware zero-day tiers** (Easy/Medium/Hard) from a pre-registered blended score — a novel
  curation contribution beyond a plain family holdout.
- **Reproducible + pinned** — seed 42 throughout; **SHA-256 manifest** over raw + processed + curated;
  `validate_pipeline.py` acceptance gate (incl. the quantum-label gate) passes on all datasets, 0 mismatch.
- **Cross-dataset alignment** — one **17-feature** schema lets CIC/BoT/UNSW train together; **frequency
  encoding** replaces false-ordinal distances.
- **Rare-class recovery** — raw-mode re-run restored BoT `Theft` (39→683) as a genuine Medium/Hard zero-day.

## 3. Design inputs for our own curated dataset (the novelty)

The core lesson: **a shared schema that is a lowest-common-denominator of coarse flow stats destroys the
very rare/zero-day flows the benchmark needs.** [`18`](18_enriched_schema_exploration.md) measured this — a
richer NetFlow-v2-aligned schema recovers TON 1→253 and Edge 2→9,042 zero-day rows leakage-safely, but at
the cost of columns that are dataset-specific under an 8-qubit budget. So a dataset we curate ourselves
should be **designed** to avoid the trade-off:

1. **One rich, common feature set across all attack families** — a NetFlow-v2-style 40+ field standard
   (Sarhan/Layeghy/Portmann) captured natively, so no lossy down-map and no zero-day collapse.
2. **Balanced by design** — sufficient rows per attack family (incl. rare/theft/ransomware) so zero-day and
   class-conditional conformal are both viable (≥ a few hundred per family after dedup).
3. **No temporal leakage** — capture with time-aware split points; keep a timestamp for temporal-shift study.
4. **Adversarial-ready** — a clean known-attack pool + a genuinely held-out family, labelled on the
   `origin × perturb` axes (Week-2 Day-10 RQ3 schema) from the start.
5. **IoT-native flows** — real IoT/IIoT protocols (MQTT/CoAP) as first-class flow features, not packet-level
   fragments that don't aggregate to flows.
6. **Pinned + documented** — source, rows, SHA-256, and a QADCP-style leakage-safe split shipped with it.

## Concerns & Recommendations

- **Concern:** existing IDS datasets force a choice between *cross-dataset comparability* (coarse shared
  schema → zero-day collapse) and *per-dataset richness* (incomparable features). Neither alone supports a
  clean cross-dataset quantum zero-day benchmark.
- **Recommendation:** scope a Team-A **novel dataset** on the §3 principles (rich common NetFlow-v2 schema +
  balanced families + time-aware + adversarial-labelled). Near-term, the mentor-locked **CIC + BoT + UNSW**
  trio is the sound benchmark; the novel dataset is the Week-3+ differentiator.

---
*Sources:* Week-1 reports [`00`](00_findings_and_flaws.md), [`05`](05_data_quality_report.md),
[`09`](09_zero_day_benchmark.md), [`17`](17_unified_collapse_mentor_note.md),
[`18`](18_enriched_schema_exploration.md); Sarhan/Layeghy/Portmann NF-v2 NetFlow standard.
