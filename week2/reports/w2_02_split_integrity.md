# Week 2 · Day 9 — Split-Integrity & Conformal-Exchangeability Report

**QS-Net / QuantumSentinel — Team A** · Week 2 · Day 9.
Task (`qi26_12_Week 2.pdf`): *verify exchangeability prerequisites for conformal — calibration and test
drawn i.i.d. from the same known-class distribution; add stratified sampling + fixed seeds so splits are
reproducible.*
Script: [`../scripts/split_integrity.py`](../scripts/split_integrity.py) (seed 42, α = 0.10) ·
JSON: `week2/reports/_generated/split_integrity.json`.

## 1. Why this matters

CQ-ZDR (Algorithm 2) sets its zero-day rejection threshold by **split-conformal prediction**, which
requires **exchangeability** between the calibration set and each test point — strictly weaker than i.i.d.,
but it **cannot be proven, only falsified** (Barber, Candès, Ramdas & Tibshirani, *Conformal Prediction
Beyond Exchangeability*, 2023). A held-out zero-day point is **deliberately non-exchangeable** with the
known-class calibration set — that is the detection signal, and the 1 − α guarantee then covers the
**known-class** portion of the test stream (Angelopoulos & Bates 2023; Novello et al., *OOD Detection
Should Use Conformal Prediction*, 2024). So we (a) **hard-assert** the disjointness the guarantee needs and
(b) **empirically falsify-test** exchangeability of the known-class calibration↔test split.

## 2. Four checks per dataset

| # | Check | Method | Pass criterion |
|---|---|---|---|
| 1 | **Disjointness** | feature-hash set ops | `zeroday ∩ cal = ∅` · `train ∩ (cal ∪ test) = ∅` · zero-day family ∉ known splits · calibration known-only |
| 2 | **Class-distribution match** (cal vs test) | TVD, χ², KS on class proportions | identical class set; TVD ≈ 0; χ² p ≫ 0.05 |
| 3 | **Classifier two-sample test** | RF trained to separate cal (0) from test (1); 5-fold CV AUROC | **AUROC ≈ 0.5** (indistinguishable ⟺ exchangeable) |
| 4 | **Conformal coverage** | split-conformal, nonconformity = 1 − p_true (RF on train); marginal coverage on test | **empirical coverage ≈ 1 − α = 0.90** |

## 3. Results (measured)

| Dataset | Disjoint | Cal known-only | Cal↔Test TVD | χ² p | **2-sample AUROC** | **Conformal coverage** (α=0.1) | Zero-day nonconf.¹ | Exchangeable |
|---|:--:|:--:|---:|---:|---:|---:|---:|:--:|
| **CIC-IoT2023** | ✅ | ✅ | 0.0000 | 1.000 | **0.4999** | **0.9019** | 0.771 | ✅ |
| **BoT-IoT** | ✅ | ✅ | 0.0000 | 1.000 | **0.5038** | **0.9007** | 0.134 | ✅ |
| **UNSW-NB15** | ✅ | ✅ | 0.0019 | 0.999 | **0.5035** | **0.9063** | 0.352 | ✅ |

¹ Mean nonconformity (1 − max known-class prob) on the zero-day split — higher ⇒ more separable/rejectable.

**Reading the numbers:**
- **Two-sample AUROC ≈ 0.50** on all three — a classifier *cannot* tell calibration from test on the
  features. This is the decisive falsification test: exchangeability is **not rejected**.
- **Coverage ≈ 0.90 = 1 − α** on all three — the split-conformal set covers the true known class at the
  target rate, so the guarantee is operational (any large miss would be the exchangeability alarm).
- **Zero-day nonconformity** ranks the holdouts by rejectability: CIC Mirai (0.77, strongly rejectable —
  matches its **Hard**-tier "flags as attack, can't characterize"), UNSW Worms/Shellcode (0.35), BoT Theft
  (0.13 — the hardest to reject in the 17-feature space; consistent with its borderline unified retention).
  This is diagnostic only — CQ-ZDR (Team B) computes the actual rejection threshold from the quantum model.

## 4. Reproducibility

Seed 42; stratified split inherited from the Week-1 QADCP (deterministic). Re-running
`make_partitions.py` → `split_integrity.py` reproduces every number. Calibration/test are byte-identical to
Week 1 (only `val` was folded into `train`), so this exchangeability result transfers directly to the
shipped partitions.

## Concerns & Recommendations

- **CIC-IoT2023 has 4 ultra-rare known classes** (`Backdoor_Malware`, `Recon-PingSweep`, `Uploading_Attack`,
  `XSS`; ≤ 9 rows each in cal/test). **Marginal** conformal (calibration n = 18,883) is unaffected and
  verified above, but **class-conditional / Mondrian** thresholds at 90–95 % are too sparse for these
  classes (need ≈ 10 / ≈ 20 calibration points per class). **Recommendation:** Team B uses **marginal**
  conformal for CIC (or merges the rare classes) — BoT and UNSW have no sub-10 classes and support either mode.
- **BoT-IoT Theft is weakly separable** in the 17-feature unified space (zero-day nonconformity 0.13). It is
  a valid held-out class (683 rows, isolated) but a genuinely hard zero-day — report its rejection rate
  separately, not pooled.
- Exchangeability holds for the **known-class** cal↔test split by construction; it says nothing about the
  zero-day split (which is *meant* to be non-exchangeable) — that is the intended CQ-ZDR detection regime.

---
*Reproduce:* `python week2/scripts/make_partitions.py && python week2/scripts/split_integrity.py`
→ `week2/reports/_generated/split_integrity.json`.
