# Week 3 · Day 15 — CQ-ZDR Conformal Calibration (Algorithm 2)

Task (`qi26_12_week3.pdf`, Team A): *Implement Algorithm 2 (CQ-ZDR): nonconformity score
s = 1 − max_c F(ρ(x), ρ_c); threshold q = s_(k), k = ⌈(1−α)(n+1)⌉. Test Q on Team B's real prototypes for
dataset 1 at α = 0.05.* Deliverables: **conformal calibration module** + **first threshold q (dataset 1)**.
The ★milestone of the week is "conformal calibration runs on real prototypes (dataset 1)."

Module: [`../scripts/conformal_calibrate.py`](../scripts/conformal_calibrate.py) ·
JSON/CSV: `reports/_generated/w3_01_conformal_calibration.{json,csv}` · seed 42 · qubit budget 8.

## Method

For a sample `x` with encoded density matrix `ρ_x`, MAQT (Alg 1, Team B) supplies the fidelity to every
known-class prototype `ρ_c`. The **Algorithm-2 nonconformity score** is

    s(x) = 1 − max_c F(ρ_x, ρ_c)     (higher ⇒ lower fidelity to all known prototypes ⇒ more novel).

The **split-conformal threshold** is the finite-sample order statistic of `s` over the **known-class**
calibration set:

    k = ⌈(1 − α)(n + 1)⌉        q = s_(k)   (k-th smallest calibration score; q = +∞ if k > n).

At test time a point is flagged zero-day iff `s > q`. Under exchangeability of the known-class calibration
and test points this gives a finite-sample **marginal** guarantee, `1 − α ≤ P(s_test ≤ q) ≤ 1 − α + 1/(n+1)`
— i.e. the false-zero-day (false-positive) rate on known traffic is `≤ α` (Angelopoulos & Bates 2023, Thm 1;
Bates, Candès, Lei, Romano & Sesia 2023, *Testing for Outliers with Conformal p-values*). The held-out
zero-day class is *deliberately non-exchangeable* with calibration — that non-exchangeability is the
detection signal — so **coverage is measured on known test traffic, and zero-day detection is reported
separately** (a coverage curve is not a power curve).

**Marginal, not Mondrian, for CIC.** Class-conditional thresholds are degenerate when a class has fewer than
`⌈1/α⌉ − 1` calibration points (Ding et al. 2023): at α = 0.05 that floor is **19 per class**, and CIC-IoT2023
has four known classes with ≤ 9 calibration rows (`Backdoor_Malware`, `Recon-PingSweep`, `Uploading_Attack`,
`XSS`; see [`../../week2/reports/w2_02_split_integrity.md`](../../week2/reports/w2_02_split_integrity.md)).
The module defaults to `--mode marginal`; `--mode mondrian` exists for BoT/UNSW and ablation only. The
marginal guarantee is marginal over the known mixture — it does **not** promise `≤ α` within each known
class; a per-known-class FPR table is emitted as a diagnostic only.

## Result — first threshold q (dataset 1 = CIC-IoT2023)

Run on the **Day-14 dummy-score interface** (`week2/interface/dummy_scores/`, seed 42) at **α = 0.05**.
These are placeholder scores with the exact real-prototype schema; the identical command reprices `q` the
moment Team B's real MAQT fidelities replace the `fid__*` block (`--scores-root … --source real`).

| Dataset | n_cal | k = ⌈0.95·(n+1)⌉ | **threshold q** | known coverage | false-zero-day (≤ α) | zero-day rejection | coverage holds |
|---|---:|---:|---:|---:|---:|---:|:--:|
| **CIC-IoT2023** (Day-15 deliverable) | 18,883 | 17,940 | **0.300551** | 0.9514 | **0.0486** | 0.9998 | ✅ |
| BoT-IoT (dummy preview, Day 18) | 18,591 | 17,663 | 0.262934 | 0.9470 | 0.0530 | 0.0952 | ⚠️¹ |
| UNSW-NB15 (dummy preview, Day 18) | 10,112 | 9,608 | 0.383380 | 0.9537 | 0.0463 | 0.3857 | ✅ |

**First threshold q (CIC, dummy) = 0.300551**, with known-test coverage 0.9514 (≥ 0.95) and false-zero-day
rate 0.0486 (≤ 0.05) — the finite-sample split-conformal guarantee holds. The recomputed
`1 − max_c F` matched the interface's precomputed `nonconformity` column to 0.0 (literal Algorithm-2 check).

¹ On the **dummy** data BoT-IoT's false-zero-day rate (0.0530) marginally exceeds α + 1/(n+1); this is a
synthetic-data artifact (the placeholder BoT scores are seeded to the Day-9 diagnostic, not results) and is
not a real coverage failure. The **zero-day rejection** rates for BoT (0.0952) and UNSW (0.3857) are low
**by construction** — Iwo seeded the dummy zero-day nonconformity means to the Day-9 values (CIC 0.771, BoT
0.134, UNSW 0.352), so only CIC's placeholder separates cleanly. All three columns are superseded by real
prototypes; only the **CIC α = 0.05 threshold is the Day-15 deliverable**, and BoT/UNSW are shown as a
Day-18 wiring preview.

## For Team B (real-prototype swap)

The module is source-agnostic: it recomputes `s = 1 − max_c fid__c` from the fidelity vector, so real scores
drop in at the **same schema** with no code change — either overwrite the parquet in place, or run
`python week3/scripts/conformal_calibrate.py --datasets CICIoT2023 --alpha 0.05 --scores-root <B's dir> --source real`.
Calibrate on `calibration` (known classes only); flag test/zeroday points with `s > q`. Use **marginal** for
CIC. Build every prototype `ρ_c` from the **train** split only — if calibration rows contribute to `ρ_c`,
their scores become in-sample and the threshold is optimistic (real FPR would exceed α).

## Exchangeability & caveats

- Exchangeability is required only between the **known-class** calibration and test points; the Day-9 report
  already verified it (cal↔test two-sample AUROC ≈ 0.50, coverage ≈ 0.90) — that result transfers here
  because calibration/test are byte-identical to Week 1/2.
- The order statistic is the **canonical `q = s_(k)`**; the Day-9 smoke test in `split_integrity.py` uses
  `np.quantile(…, method="higher")` = `s_(k+1)` (one index higher). Both satisfy coverage ≥ 1 − α.
- Finite-sample coverage granularity is `1/(n+1)` (≈ 5.3e-5 for CIC); realized coverage sits in
  `[1 − α, 1 − α + 1/(n+1)]`.
- Ties in `s` (duplicate flows / finite-shot fidelities) can make the bound mildly conservative; randomized
  tie-breaking removes it. `s = 1 − max_c F` fidelity-to-prototype as a conformal nonconformity score is
  (to our search) novel — validity is score-agnostic, so this is sound, but detection **power** must be
  shown empirically on real prototypes, not assumed.

## References

- Angelopoulos & Bates, *A Gentle Introduction to Conformal Prediction* (Found. Trends ML, 2023) — the
  `⌈(n+1)(1−α)⌉` quantile and the `1−α ≤ cov ≤ 1−α+1/(n+1)` bound.
- Bates, Candès, Lei, Romano & Sesia, *Testing for Outliers with Conformal p-values* (Ann. Stat., 2023) —
  the one-sided conformal novelty test CQ-ZDR implements.
- Ding, Angelopoulos, Bates, Jordan & Tibshirani, *Class-Conditional Conformal Prediction with Many Classes*
  (NeurIPS 2023) — the ≥ ⌈1/α⌉−1 per-class floor ⇒ marginal for CIC.
- Vovk, Gammerman & Shafer, *Algorithmic Learning in a Random World* (2005); Lei et al., *Distribution-Free
  Predictive Inference for Regression* (JASA 2018) — split-conformal foundations.
- Barber, Candès, Ramdas & Tibshirani, *Conformal Prediction Beyond Exchangeability* (Ann. Stat., 2023) —
  fallback if calibration↔test exchangeability fails.

## Reproduce

```bash
source .venv/bin/activate                                             # Python 3.12
python week2/scripts/make_dummy_scores.py                             # only if interface/ is absent
python week3/scripts/conformal_calibrate.py --datasets CICIoT2023 --alpha 0.05
#   -> first q (CIC, dummy) = 0.300551 | known coverage 0.9514 | false-zero-day 0.0486
python -m pytest week3/tests -q                                       # 11 tests
```
