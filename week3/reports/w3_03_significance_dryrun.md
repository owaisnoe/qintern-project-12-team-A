# Deliverable (Week 3 · Day 17) — 5-Seed Statistical Protocol + Significance Dry-Run

**QS-Net / QuantumSentinel — Team A** · Week 3 · Day 17.
Task (`qi26_12_week3.pdf`): *integrate the 5-seed statistical protocol: mean±std, 95% CI, paired t-test,
McNemar, Holm–Bonferroni, Cohen's d; dry-run significance tests on baseline-vs-baseline as a sanity check.*
Implementation: [`scripts/stats_protocol.py`](../scripts/stats_protocol.py) ·
Machine-readable: `reports/_generated/w3_03_significance_dryrun.{json,csv}` ·
Tests: [`tests/test_stats_protocol.py`](../tests/test_stats_protocol.py) (8 cases, incl. hand-computed
McNemar and the classic Holm worked example).

## 1. The protocol (and the conventions that make it auditable)

| Piece | Convention |
|---|---|
| mean ± std, 95% CI | sample std (ddof = 1), t-based CI — same convention as Iwo's Day-13 harness |
| paired t-test | two-sided, pairs matched **by seed** (same seed list 42–46 drives every head) |
| Cohen's d | paired **d_z = mean(diff)/std(diff)** — effect size reported beside every p |
| McNemar | **exact** two-sided binomial on discordant pairs, matched **by test row** (seed-42 artifacts) |
| Holm–Bonferroni | step-down over the **declared family** = all dataset × head-pair tests on the headline metric |
| guards | zero-variance ⇒ t=0, p=1, d=0 (A-vs-A cannot fake significance); n=5 caveat stated on every table |

**Integration is verified, not asserted:** the module re-derives Iwo's stored mean/std/CI from the raw
per-seed values for **all 78 (dataset, head, metric) cells — 0 mismatches** — and runs 9 A-vs-A
self-comparisons, all returning t = 0, p = 1, d = 0.

## 2. Dry-run: novelty heads pairwise on zero-day AUROC (5 seeds, Holm over 9 tests)

| Dataset | Comparison | Δ mean | t | p raw | **p Holm** | d_z | verdict |
|---|---|---:|---:|---:|---:|---:|---|
| CIC-IoT2023 | AE vs IF | −0.061 | −4.45 | 0.011 | **0.056** | −1.99 | ns¹ |
| CIC-IoT2023 | AE vs OC-SVM | −0.006 | −0.60 | 0.578 | 0.607 | −0.27 | ns |
| CIC-IoT2023 | IF vs OC-SVM | +0.055 | +13.26 | 1.9e−4 | **1.3e−3** | +5.93 | **SIG** |
| BoT-IoT | AE vs IF | +0.162 | +11.53 | 3.2e−4 | **1.9e−3** | +5.16 | **SIG** |
| BoT-IoT | AE vs OC-SVM | −0.015 | −1.59 | 0.188 | 0.563 | −0.71 | ns |
| BoT-IoT | IF vs OC-SVM | −0.177 | −36.74 | 3.3e−6 | **3.0e−5** | −16.43 | **SIG** |
| UNSW-NB15 | AE vs IF | −0.046 | −1.18 | 0.303 | 0.607 | −0.53 | ns |
| UNSW-NB15 | AE vs OC-SVM | −0.142 | −3.52 | 0.025 | 0.098 | −1.57 | ns |
| UNSW-NB15 | IF vs OC-SVM | −0.096 | −31.33 | 6.2e−6 | **5.0e−5** | −14.01 | **SIG** |

¹ **The correction earned its keep on the first run:** CIC AE-vs-IF is "significant" raw (p = 0.011) and
correctly loses it under Holm (p = 0.056) — with 9 tests, one raw p ≈ 0.01 is unremarkable. This is exactly
the mistake the protocol exists to prevent, caught on baselines before any QS-Net claim depends on it.

Surviving effects are the *huge* ones (|d_z| ≥ 5): IF beats OC-SVM on CIC; OC-SVM beats IF on BoT and UNSW;
AE beats IF on BoT. Consistent with the Day-13 picture — **no head dominates across datasets**, so QS-Net's
bar is per-dataset, not a single number.

## 3. McNemar on per-sample novelty decisions (IF vs AE, test+zeroday, seed 42)

| Dataset | n pairs | acc IF | acc AE | n01 (AE only right) | n10 (IF only right) | p exact |
|---|---:|---:|---:|---:|---:|---:|
| CIC-IoT2023 | 29,867 | 0.799 | 0.674 | 1,038 | 4,762 | < 1e−300 |
| BoT-IoT | 19,274 | 0.328 | 0.331 | 1,243 | 1,290 | **0.36** |
| UNSW-NB15 | 11,701 | 0.734 | 0.716 | 922 | 707 | 1.1e−7 |

Row-paired and seed-paired tests answer different questions: BoT shows a **seed-level** AE > IF gap
(Δ AUROC +0.162, SIG) yet **no per-sample thresholded-decision difference** (p = 0.36) — AUROC is
threshold-free, McNemar tests the deployed flags. The protocol reports both so the paper never conflates them.

## 4. Limitations

1. **n = 5 seeds** — t-tests are exact only under normal seed-differences; that is why d_z accompanies every
   p and why McNemar (row-level, thousands of pairs) is the second axis. 2. **Family choice** — Holm is
   applied over the 9 declared head-pair tests; a different declared family changes adjusted p's (declare
   before testing, as done here). 3. **Dry-run scope** — baselines only by design; QS-NET-vs-baseline
   comparisons reuse this module unchanged (`head_pair_tests` on any per-seed metric vector, McNemar on any
   paired per-row decisions).

## Concerns & Recommendations

**Concern:** with 5 seeds, a raw p < 0.05 will appear ~once per 9-test family by chance; unadjusted tables
in the paper would not survive review. **Recommendations:** (1) every comparison table in Articles 1–2 goes
through `holm_bonferroni` with the family declared in the caption; (2) report d_z beside p everywhere
(reviewers at Q1 venues expect effect sizes); (3) when Team B's MAQT metrics arrive per-seed, the QS-NET-vs-
baseline table is `head_pair_tests` + Holm, zero new code; (4) keep McNemar for deployed-threshold claims
(false-flag budgets), seed-paired t for ranking claims.

---
*Reproduce:* `python week3/scripts/stats_protocol.py` (~3 s) → `_generated/w3_03_significance_dryrun.{json,csv}`.
Tests: `python -m pytest week3/tests/test_stats_protocol.py` (8). Inputs: Iwo's Day-13
`stats_harness.json` (78 cells cross-checked) + the Day-11/12 `baselines/<ds>/predictions.csv`.*
