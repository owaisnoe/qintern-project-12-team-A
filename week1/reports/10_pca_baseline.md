# Deliverable (Day 4/5) — PCA-8 Quantum-Ready Baseline: ranked-8 vs PCA-8 on one 8-qubit budget

**QS-Net / QuantumSentinel — Team A** · Week 1 · AK (@Thedaemon-AK).
Contribution requested in team coordination: provide the **PCA** dimensionality-reduction alternative
to the QADCP **ranked** features, as a *separate* script that reads the frozen `qadcp/` outputs
(so Owais's verified pipeline stays untouched and Team B's data contract is stable).
Implementation: [`scripts/pca_baseline.py`](../scripts/pca_baseline.py) (seed 42) ·
Outputs: `datasets/<name>/qadcp/quantum/pca8_<split>.parquet` + `qadcp/pca_baseline.json` ·
Summary: `datasets/_pca_baseline_summary.json`.

## 1. Why a second reduction — the choice Team C has to make

Angle encoding spends **one qubit per feature**, so on a NISQ-realistic **8-qubit** budget we must
pick 8 numbers per flow. QADCP's [`08`](08_qadcp_design.md) S6b does this by a **supervised ranking**
(|Pearson r| vs `label_binary`, on train) — the top-8 named features. That is one defensible encoder;
the other canonical choice is **PCA-8** — 8 unsupervised orthogonal directions of maximum variance.
They optimize different things, so Team B/C should not guess — they should **run both on the same
8-qubit budget and compare downstream QML accuracy**. This script supplies the PCA arm of that A/B.

## 2. Method — same leakage-safe, quantum-ready guarantees as `qadcp.py`

For each dataset, reading only the shipped `qadcp/{train,val,calibration,test,zeroday}.parquet`:

| Step | What | Guarantee |
|---|---|---|
| **Fit** | `PCA(n_components=8)` fit on **`train.parquet` only** (robust-scaled feature space) | no leakage — val/cal/test/zeroday are `.transform()`-ed, never re-fit |
| **Project** | transform every split with the train-fit PCA | identical basis across splits |
| **Angle-encode** | per component, min/max **from train**, rescale to **[0, π]**, others clipped | quantum-ready — same convention as `qadcp.py` S6b `AngleEmbedding` |
| **Emit** | `quantum/pca8_<split>.parquet` (`pca_1..pca_8` + the 3 labels) next to the ranked `q{4,8,12,16}_*` | drop-in comparison files; labels carried through |

Determinism: seed 42, `svd_solver` default (deterministic for these sizes). The 3-label schema
(`label_multiclass` / `label_binary` / `label_family`) is preserved so the two encoders are compared
on identical rows and labels.

## 3. Results — measured (all five datasets)

| Dataset | Components | Explained variance (train) | Rows (train / val / cal / test / zeroday) |
|---|:--:|---:|---|
| CIC-IoT2023 | 8 | **0.9998** | 132,166 / 18,883 / 18,883 / 18,883 / 10,984 |
| TON_IoT | 8 | **0.9999** | 62,215 / 8,889 / 8,889 / 8,889 / 254 |
| BoT-IoT¹ | 8 | **0.9941** | 130,205 / 18,601 / 18,601 / 18,601 / **683** |
| Edge-IIoTset | 8 | **0.9995** | 89,971 / 12,853 / 12,857 / 12,872 / 10,548 |
| UNSW-NB15 | 8 | **0.9727** | 84,730 / 12,104 / 12,104 / 12,104 / 1,615 |

¹ BoT-IoT includes the **Theft** zero-day recovered by the raw-mode re-run
([`08`](08_qadcp_design.md) §4², [`09`](09_zero_day_benchmark.md) §6) — PCA-8 was re-fit on the
regenerated 16-feature space.

**Low-rank insight (a qubit-budget signal):** on four of five datasets 8 PCs capture **≥ 99.4 %** of
the post-prune variance — i.e. after correlation pruning the feature space is *effectively ≤ 8-
dimensional*, so **q8 loses almost no linear information and even q4 is worth benchmarking**. UNSW-NB15
is the exception (0.973): its variance is spread across more directions, so it is the dataset where the
qubit budget will most affect a PCA-encoded model — the natural stress test for the ranked-vs-PCA A/B.

## 4. Ranked-8 vs PCA-8 — the trade-off

| | **Ranked-8** (`qadcp.py` S6b, in `quantum/q8_*` = first 8 of `qubit_budgets.json['budgets']['8']`) | **PCA-8** (this script, `quantum/pca8_*`) |
|---|---|---|
| Supervision | **Supervised** (\|r\| vs binary label) — tuned toward attack/benign separability | **Unsupervised** — maximizes variance, label-blind |
| Axes | Named physical features (CIC: `urg_count, Duration, flow_duration, Variance, Std, HTTPS, Tot sum, Header_Length`) — **interpretable** | Linear mixtures `pca_1..8` — **decorrelated** but not individually interpretable |
| Redundancy | Two ranked features can still be correlated (ranking is univariate) | Components are **orthogonal by construction** — no wasted qubit on correlated axes |
| Failure mode | May under-rank a feature that is weak alone but strong in combination | May **discard a low-variance, highly-discriminative** feature (variance ≠ discriminability) |
| Zero-day fit | Tuned on *known* labels → may transfer worse to *unseen* families | Label-blind → arguably fairer for zero-day geometry (the CQ-ZDR use case) |

Neither dominates a priori: ranking optimizes *known-class* separability, PCA optimizes *reconstruction*.
For QS-Net's **conformal zero-day rejection** (calibrated on known classes, tested on unseen families),
the label-blind PCA basis is a genuinely interesting counterpoint — hence the A/B rather than a default.

## 5. How Team B/C consume this

1. Train the identical VQC/quantum-kernel twice — once on `quantum/q8_<split>` (ranked), once on
   `quantum/pca8_<split>` (PCA) — same seed, same splits, same `AngleEmbedding`.
2. Compare **per-tier zero-day** metrics ([`09`](09_zero_day_benchmark.md) §4: recall@Easy/Medium/Hard),
   not just pooled test accuracy — the encoders may trade known-class accuracy for zero-day robustness.
3. Team C then replaces *either* baseline with a proper selector (MI / wrapper / quantum feature
   selection); both baselines are the reference points that a better selector must beat.

## 6. Limitations

1. **PCA is linear.** It cannot expose nonlinear structure that a quantum kernel might exploit; a
   low linear-evr (UNSW) does *not* mean the features are uninformative, only that variance is spread.
2. **Variance ≠ discriminability.** A tiny-variance flag (e.g. a rare protocol bit) can be decisive for
   one attack family yet be down-weighted by PCA — this is exactly where ranked-8 may win, and why both
   ship.
3. **Fit on the robust-scaled space** (`qadcp.py` S4 output), so PCA inherits that scaling; a different
   pre-scaling would rotate the components. This is intentional — both encoders start from the *same*
   scaled features so the comparison is apples-to-apples.
4. **8 components only.** `pca8_*` targets the 8-qubit budget; if the mentor sets a different budget,
   re-run with `N_COMPONENTS` matched (the script is one constant away from q4/q12/q16 PCA arms).

## Concerns & Recommendations

**Concern:** four of five datasets are near-100 % explained by 8 PCs, which means the *linear* content
of the curated feature space is nearly rank-8 — a QML model that only sees linear structure would gain
little beyond q8, and the quantum advantage (if any) must come from **nonlinear** encoding/kernels, not
from more qubits. **Recommendations:** (1) Team B benchmarks **q4 and q8** first (cheap, NISQ-realistic)
before q12/q16 — the evr says the marginal linear return is small; (2) run the **ranked-vs-PCA A/B on
UNSW-NB15 first** — it is the only dataset where the encoder choice clearly moves information; (3) keep
both encoders frozen as reference baselines so Team C's advanced selector has a fair bar to clear.

---
*Reproduce:* `python week1/scripts/qadcp.py && python week1/scripts/pca_baseline.py`
(numpy + pandas + pyarrow + scikit-learn 1.8; seed 42; fit-on-train, angle ∈ [0, π];
per-dataset `qadcp/pca_baseline.json` + `datasets/_pca_baseline_summary.json`).
