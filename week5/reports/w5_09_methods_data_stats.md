# Week 5 · Day 31 (a) — Methods Subsections: Data + Conformal Statistics

Task (`qi26_12_Week_5.pdf`, Team A): *write the Data + Conformal-Statistics methods subsections (partition
protocol, calibration, coverage).* Deliverable: **methods subsections (data + stats)**.

This is manuscript copy, not a result report: the two subsections below are written to be dropped into
Article 1's Methods section by Team B (Day 30–31, Article-1 assembly). A LaTeX rendering of the identical
text ships as [`_generated/w5_09_methods.tex`](_generated/w5_09_methods.tex); the reproducibility appendix
that these subsections point at is [`w5_10_repro_appendix.md`](w5_10_repro_appendix.md).

**Provenance of the numbers.** The result quantities — *q*, *k*, *n*_cal, achieved FZR, band membership,
zero-day recall, the all-seed means and the per-class out-of-band counts — are the frozen Day-26/28 values
and are independently re-derived in the Day-30 cross-audit
([`w5_07_cross_audit.md`](w5_07_cross_audit.md), 90 PASS / 0 FAIL / 1 WARN). The **data-provenance**
numbers in the Data subsection — partition row counts, the two-sample AUROCs, the α = 0.10 coverage — are
Week-1/2 figures and trace to the Day-9 split-integrity report and the Day-13 leakage check, which the
Day-30 audit does not cover; they are cited from those sources, not from the audit. Cells marked **‡** ride
the Day-14 dummy fidelity interface and reprice on Team B's real prototypes with one flag; the protocol,
conventions and section structure do not change when they do.

---

## Subsection: Data

### Datasets and unified representation

We evaluate on three public IoT/network intrusion-detection corpora: **CIC-IoT2023**, **BoT-IoT** and
**UNSW-NB15**. The benchmark trio is a mentor-locked scope decision: TON_IoT and Edge-IIoTset were curated
under the same pipeline but set aside because their held-out zero-day split does not survive the shared
schema. Two stages compound: projecting onto the common 17 features maps many distinct attack flows onto
*identical* vectors (TON_IoT's 254 ransomware flows collapse to 8 unique vectors, 7 of which are shared
with non-ransomware traffic), and the cross-split de-duplication that follows resolves collisions with
train priority, so the surviving zero-day copies are dropped. The held-out families end at **1 row**
(TON_IoT) and **2 rows** (Edge-IIoTset), which cannot support a rejection-rate estimate. All three retained
datasets keep their zero-day splits intact (100%, 100% and 75% retention).

Because the three corpora publish incompatible column vocabularies, each is projected onto a shared
**17-feature unified flow schema** (flow duration; total/source/destination packet and byte counts;
overall, source and destination rates; four packet-size statistics; inter-arrival time; and harmonized
`protocol` and `conn_state` categoricals), together with three label columns: a fine `label_multiclass`, a
binary `label_binary`, and a 10-family ontology label `label_family`. Categoricals are frequency-encoded and
directional fields that a corpus does not publish are imputed — both, as below, fit on training data only.

### Curation pipeline and leakage controls

Curation runs through a **Quantum-Aware Dataset Curation Pipeline (QADCP)** whose defining property is that
it is **split-first**: every data-dependent parameter is fit on the training split alone and merely applied
to the others. This is a deliberate departure from the conventional capability ordering, in which scaling or
balancing precedes splitting and thereby leaks evaluation data into fitted parameters. Concretely, the
correlation prune (drop one of each |r| ≥ 0.95 pair), the median/IQR robust scalers, the angle-encoding
min/max ranges (mapping features to [0, π] for angle embedding; the published benchmark uses the qubit
budget of 8 from the nested 4/8/12/16 rankings), and the feature ranking are all fit on `train` and then
applied unchanged to calibration, test and zero-day.
Class balancing is applied to the training split only; evaluation splits are never resampled.

Two further leakage controls matter for the guarantee that follows. First, de-duplication is performed **on
the feature columns before splitting**, so one feature vector can land in exactly one split; cross-split
disjointness is subsequently asserted on feature-content hashes rather than row indices, which is what
catches a repeated flow shared across splits. This is the relevant control for CIC-IoT2023, whose leakage
vector is repeated and near-duplicate flows rather than identifier columns (the CIC feature set contains no
raw IP, port, MAC or timestamp fields). Measured cross-split flow overlap is **0** for every pair on every
dataset, and within-split duplication is **0**. Second, and central to the conformal argument, **the
threshold is calibrated on held-out known-class data and never on the unknown class**: calibrating on the
held-out family would leak precisely the signal the detector is meant to discover.

### Partition protocol

Each dataset is partitioned four ways — **Train / Calibration / Test / Zero-Day** — under a fixed seed
(42), so the partitions are deterministic and re-running the partitioner reproduces them exactly.

The zero-day split is a **held-out attack family**, not a random subsample: one or more entire attack
classes are removed from training, calibration and test, and appear only at evaluation time. The remaining
classes are stratified 70/10/10/10 into train/validation/calibration/test, with validation subsequently
folded into train to give the four-way conformal layout. Calibration contains **known classes only**, by
construction.

| Dataset | Train | Calibration | Test | Zero-Day | Known classes | Held-out zero-day family |
|---|---:|---:|---:|---:|---:|---|
| CIC-IoT2023 | 151,049 | 18,883 | 18,883 | 10,984 | 31 | `Mirai-greeth_flood`, `Mirai-greip_flood`, `Mirai-udpplain` |
| BoT-IoT | 148,729 | 18,591 | 18,591 | 683 | 4 | `Theft` |
| UNSW-NB15 | 81,215 | 10,112 | 10,086 | 1,216 | 8 | `Shellcode`, `Worms` |

Three invariants are asserted in the partitioner rather than merely documented: the zero-day family is
present only in `zeroday` and has zero rows in train, calibration and test; calibration is a subset of the
known classes; and the assignment is deterministic under the seed.

### Verifying the exchangeability prerequisite

Split-conformal validity requires **exchangeability** between the calibration set and each test point — a
condition strictly weaker than i.i.d., and one that cannot be proven, only falsified. We therefore treat it
as an empirical claim and attempt to falsify it, using a classifier two-sample test: a random forest is
trained to separate calibration rows (label 0) from test rows (label 1) and scored by 5-fold cross-validated
AUROC. An AUROC at chance means the two sets are indistinguishable on the features.

| Dataset | Cal↔Test TVD | χ² p | Two-sample AUROC | Split-conformal coverage (α = 0.10) |
|---|---:|---:|---:|---:|
| CIC-IoT2023 | 0.0000 | 1.000 | **0.4999** | 0.9019 |
| BoT-IoT | 0.0000 | 1.000 | **0.5038** | 0.9007 |
| UNSW-NB15 | 0.0019 | 0.999 | **0.5035** | 0.9063 |

Exchangeability is not rejected on any dataset. Note that this claim is scoped to the **known-class**
calibration↔test split. The held-out zero-day split is *deliberately* non-exchangeable with calibration —
that non-exchangeability is the detection signal — so the guarantee below covers the known-class portion of
the test stream, and zero-day detection is reported separately.

---

## Subsection: Conformal Statistics

### Nonconformity score and calibration

For a sample *x* encoded as a density matrix ρ*ₓ*, the quantum model supplies the Uhlmann fidelity
*F*(ρ*ₓ*, ρ*_c*) to every known-class prototype ρ*_c* (non-squared *F*, i.e. the square root of the *F*²
returned by PennyLane/Qiskit). The nonconformity score is

&nbsp;&nbsp;&nbsp;&nbsp;**s(x) = 1 − max_c F(ρ_x, ρ_c)**,

so a sample with low fidelity to every known prototype scores high and is more novel. Prototypes are built
from the **train** split only; if calibration rows contributed to ρ*_c*, calibration scores would be
in-sample and the resulting threshold optimistic.

The threshold is the **split-conformal order statistic** of *s* over the known-class calibration set of size
*n*:

&nbsp;&nbsp;&nbsp;&nbsp;**k = ⌈(1 − α)(n + 1)⌉**, &nbsp;&nbsp; **q = s₍k₎**

(the *k*-th smallest calibration score; *q* = +∞ if *k* > *n*). At test time a point is flagged zero-day iff
*s* > *q*. Under exchangeability of the known-class calibration and test points this gives a finite-sample
**marginal** guarantee

&nbsp;&nbsp;&nbsp;&nbsp;**1 − α ≤ P(s_test ≤ q) ≤ 1 − α + 1/(n + 1)**,

i.e. the false-zero-day rate on known traffic is at most α, with granularity 1/(*n*+1) (≈ 5.3 × 10⁻⁵ for
CIC-IoT2023). Validity is *score-agnostic*: it does not depend on the fidelity score being a good novelty
signal. **Detection power does**, and is therefore an empirical question reported separately rather than
inherited from the theorem — a coverage curve is not a power curve.

We use one primary α = 0.05 for the quantum and classical arms alike. The resulting thresholds:

| Dataset | n_cal | k = ⌈0.95(n+1)⌉ | threshold q ‡ | achieved false-zero-day rate ‡ |
|---|---:|---:|---:|---:|
| CIC-IoT2023 | 18,883 | 17,940 | 0.300551 | 0.0486 |
| BoT-IoT | 18,591 | 17,663 | 0.262934 | 0.0530 |
| UNSW-NB15 | 10,112 | 9,608 | 0.383380 | 0.0463 |

### Marginal, not class-conditional

Class-conditional (Mondrian) thresholds are degenerate when a class holds fewer than ⌈1/α⌉ − 1 calibration
points, which at α = 0.05 is a floor of **19 per class**. CIC-IoT2023 has four known classes with ≤ 9
calibration rows (`Backdoor_Malware`, `Recon-PingSweep`, `Uploading_Attack`, `XSS`), so we calibrate
**marginally** on all three datasets for comparability, and report class-conditional behaviour as a
diagnostic instead.

The scope of the marginal guarantee is stated precisely because it is easy to overclaim: marginal conformal
controls the false-alarm rate over the known-class **mixture** and carries **no per-class guarantee**. Rare
classes contribute few pooled calibration points and so do not skew *q* — the mixture guarantee is
unaffected by class imbalance — but an individual class may still be over- or under-covered. We therefore
judge each known class's test flag count against **its own** exact band; on the present interface **0 of 31,
0 of 4 and 0 of 8** classes fall outside their own band. Where a class does fall outside on real prototypes,
the appropriate remedy is **clustered conformal** — grouping rare classes until each cluster clears the
calibration floor — rather than fully class-conditional conformal, which several classes cannot support.

### Coverage verification

A bare `FZR ≤ α` assertion is the wrong acceptance test. Split conformal guarantees the *expectation*,
marginally over the calibration and test draws; on a finite test set the empirical rate fluctuates around
(*n*+1−*k*)/(*n*+1), so a naive threshold check rejects sound systems by luck roughly half the time. We
therefore judge each observation against the **exact finite-sample law**. Conditional on the calibration
draw, coverage is Beta-distributed, so the number of false flags *E* on *m* known test rows follows a
**Beta-Binomial**:

&nbsp;&nbsp;&nbsp;&nbsp;coverage | calibration ∼ Beta(*k*, *n*+1−*k*) &nbsp;⟹&nbsp; *E* ∼ BetaBinomial(*m*, *n*+1−*k*, *k*).

For each (dataset, α) we report the observed rate, its exact central 99% band, and a one-sided tail
*p*-value P(*E* ≥ *e*_obs). The band — not the point comparison against α — is the acceptance gate: a FAIL
means the guarantee is genuinely violated rather than unlucky. Below-band excursions are reported as
conservativeness (ties and score discreteness make the band conservative), not failures. This is also the
correct band for a *calibration-draw* plot; Clopper–Pearson describes a fixed-threshold proportion and is
the wrong object here.

| Dataset | m_test | false flags ‡ | achieved FZR ‡ | exact 99% band | p(E ≥ e) ‡ | verdict |
|---|---:|---:|---:|---|---:|---|
| CIC-IoT2023 | 18,883 | 918 | 0.0486 | [0.0443, 0.0559] | 0.73 | PASS |
| BoT-IoT | 18,591 | 986 | 0.0530 | [0.0443, 0.0559] | 0.090 | PASS |
| UNSW-NB15 | 10,086 | 467 | 0.0463 | [0.0423, 0.0581] | 0.89 | PASS |

BoT-IoT illustrates why the law matters: its rate exceeds α outright, yet sits comfortably inside the exact
band (*p* = 0.090), which is ordinary sampling noise on 18,591 test rows rather than a coverage failure.

Coverage is verified across the full **α-sweep 0.01–0.20** (20 values × 3 datasets = 60 verifications, all
passing the finite-sample verdict); the achieved rate tracks the diagonal *y* = α inside the band across the
whole range, which is the paper's headline coverage figure.

### Stability across seeds

Because the guarantee is marginal over the calibration/test draw, it must hold across draws rather than on
one split. We pool the known-class calibration ∪ test scores and re-draw them at the original sizes under
**seeds 42–46**, re-calibrating each re-split and judging it against its own exact band, with the zero-day
pool held fixed and scored at each re-split's *q*.

| Dataset | mean FZR (5 seeds) ‡ | 95% CI ‡ | in band | mean zero-day recall ‡ | recall 95% CI ‡ |
|---|---:|---|:--:|---:|---|
| CIC-IoT2023 | 0.0517 | [0.0498, 0.0537] | 5/5 | 0.9998 | [0.9998, 0.9998] |
| BoT-IoT | 0.0501 | [0.0476, 0.0527] | 5/5 | 0.0928 | [0.0912, 0.0945] |
| UNSW-NB15 | 0.0508 | [0.0473, 0.0542] | 5/5 | 0.3929 | [0.3884, 0.3975] |

All three datasets hold the exact band on all five re-splits, and every 95% CI covers the target α = 0.05.
The recall CIs quantify how little the power number moves with the calibration draw.

### Auditing the exchangeability assumption at deployment

Coverage arithmetic is only meaningful if the assumption underneath it holds, so the deployed pipeline is
audited with six inferential tests per dataset — two-sample KS and Mann-Whitney on calibration vs test
scores, a class-mix χ², a flag-rate-by-class χ², and two index-drift Spearman tests — with Holm step-down
over the declared family of 18 cells. **No violations** are detected.

Two methodological choices deserve statement. First, the textbook conformal *p*-value uniformity check —
*p_i* = (1 + #{*j* : *s_j* ≥ *s_i*})/(*n*+1) tested against U(0,1) — is reported **descriptively and
excluded from the inferential family**: every *p_i* is computed against the same calibration set, so the
*p*-values are exchangeable rather than independent, and the one-sample KS null is far too tight (measured
on this interface it rejects on ≈ 37% of genuinely exchangeable re-splits). It is also redundant with the
two-sample KS up to 1/(*n*+1), which carries the inference under the correct null. Second, the audit is
validated by **injected-violation drills** rather than assumed to have power: trimming the calibration tail,
shifting test scores, and skewing the test class mix are each injected and each detected. The class-mix
injection is the instructive case — the audit flags it decisively while the *marginal* false-alarm rate
stays inside the band, which is exactly the failure mode a coverage-only check cannot see.

A caveat travels with the remediation. Re-splitting repairs *split-induced* non-exchangeability, where the
pool is homogeneous and the boundary was drawn badly. It also makes a *deployment shift* look repaired,
because calibration and test become exchangeable draws from the shifted mixture — but that mixture is not
the deployment distribution. **A genuine deployment shift is answered by recalibrating on fresh data, never
by re-splitting**, and the re-split remedy is therefore opt-in rather than applied automatically.

### Significance protocol

All comparative claims go through one pre-declared protocol, chosen so that the test matches the object
being claimed.

| Component | Convention |
|---|---|
| Central tendency | mean ± sample std (ddof = 1); *t*-based 95% CI |
| Seed-level comparison | two-sided paired *t*-test, pairs matched **by seed**, over seeds 42–46 |
| Row-level comparison | **exact** two-sided binomial McNemar on discordant pairs, matched **by test row** |
| Effect size (paired) | Cohen's **d_z** = mean(diff)/std(diff), reported beside every *p* |
| Effect size (proportions) | Cohen's **h** |
| Multiplicity | Holm–Bonferroni step-down over the family declared **before** testing |
| Guards | zero-variance ⇒ *t* = 0, *p* = 1, *d* = 0, so a self-comparison cannot fake significance |

Seed-paired *t*-tests and row-paired McNemar answer different questions and are reported separately rather
than pooled: AUROC is threshold-free and speaks to ranking, whereas McNemar tests the flags a system
actually deploys. The dry run on classical baselines demonstrated the correction earning its keep — a raw
*p* = 0.011 in a nine-test family correctly lost significance under Holm at *p* = 0.056 — which is the error
the protocol exists to prevent.

Families are declared per comparison surface. For in-distribution detection these are closed-set
correctness against the classical multiclass detector (*m* = 3, one comparison per dataset) and known-split
false-alarm rate against every novelty head (*m* = 8; one dataset publishes no OC-SVM model, a real absence
rather than a missing value), corrected separately. We note explicitly that the false-alarm family compares
systems at their **shipped operating points** — the conformal detector at its guaranteed α = 0.05, each
heuristic head at its own frozen threshold, which targeted a 2α known-FPR budget — so it supports a
deployed-behaviour statement, not a matched-budget superiority claim; the like-for-like comparison at one
shared α is reported in the zero-day table.

Finally, the seed-level power floor is stated rather than left implicit: with *n* = 5 seeds the smallest
detectable paired effect is d_z ≈ 1.24, and ≈ 1.68 at 80% power. Any seed-level claim must clear that bar,
and this is why an effect size accompanies every reported *p*.

---

## Provenance and status

- **Final, will not move:** the partition protocol and its row counts; the exchangeability verification; the
  Beta-Binomial band construction (a function of *n*_cal, *k*, *m*_test and α only); the significance
  conventions and declared families; the classical baseline numbers.
- **‡ Provisional:** every quantity that reads through the quantum fidelity interface — *q*, achieved α,
  the 5-seed CIs, zero-day recall and the QS-Net cells of the comparison tables. These reprice on Team B's
  real prototypes with `--source real --scores-root <dir>`, no code change, and the rerun is the one the
  manuscript cites.

## References cited by these subsections

- Angelopoulos & Bates, *A Gentle Introduction to Conformal Prediction* (Found. Trends ML, 2023) — the
  ⌈(n+1)(1−α)⌉ quantile, the 1−α ≤ cov ≤ 1−α+1/(n+1) bound, §3.2 for the Beta/Beta-Binomial law.
- Vovk, *Conditional validity of inductive conformal predictors* (ACML, 2012) — the exact finite-sample
  coverage distribution.
- Vovk, Gammerman & Shafer, *Algorithmic Learning in a Random World* (2005); Lei et al., *Distribution-Free
  Predictive Inference for Regression* (JASA, 2018) — split-conformal foundations.
- Bates, Candès, Lei, Romano & Sesia, *Testing for Outliers with Conformal p-values* (Ann. Stat., 2023) —
  the one-sided conformal novelty test with known-only calibration.
- Barber, Candès, Ramdas & Tibshirani, *Conformal Prediction Beyond Exchangeability* (Ann. Stat., 2023) —
  exchangeability, and the fallback if it fails.
- Ding, Angelopoulos, Bates, Jordan & Tibshirani, *Class-Conditional Conformal Prediction with Many Classes*
  (NeurIPS, 2023) — the ⌈1/α⌉−1 per-class floor and clustered conformal.
- Novello et al., *OOD Detection Should Use Conformal Prediction* (2024) — conformal novelty detection framing.
- Demšar, *Statistical Comparisons of Classifiers over Multiple Data Sets* (JMLR, 2006) — effect sizes and
  multiplicity control in classifier comparison.

---

*Sources consolidated by these subsections:* [`../../week2/reports/w2_01_partition_spec.md`](../../week2/reports/w2_01_partition_spec.md) ·
[`w2_02_split_integrity.md`](../../week2/reports/w2_02_split_integrity.md) ·
[`w2_07_leakage_controls.md`](../../week2/reports/w2_07_leakage_controls.md) ·
[`../../week1/reports/08_qadcp_design.md`](../../week1/reports/08_qadcp_design.md) ·
[`12_unified_schema.md`](../../week1/reports/12_unified_schema.md) ·
[`../../week3/reports/w3_01_conformal_calibration.md`](../../week3/reports/w3_01_conformal_calibration.md) ·
[`w3_02_coverage_harness.md`](../../week3/reports/w3_02_coverage_harness.md) ·
[`w3_03_significance_dryrun.md`](../../week3/reports/w3_03_significance_dryrun.md) ·
[`../../week4/reports/w4_04_live_coverage.md`](../../week4/reports/w4_04_live_coverage.md) ·
[`w5_02_table_a.md`](w5_02_table_a.md) · [`w5_04_table_b.md`](w5_04_table_b.md) ·
[`w5_05_table_a_effects.md`](w5_05_table_a_effects.md) · [`w5_07_cross_audit.md`](w5_07_cross_audit.md).
