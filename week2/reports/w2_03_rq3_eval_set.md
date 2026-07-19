# Week 2 · Day 10 — RQ3 Adversarial-vs-Zero-Day Evaluation-Set Specification

**QS-Net / QuantumSentinel — Team A** · Week 2 · Day 10.
Task (`qi26_12_Week 2.pdf`): *construct the adversarial-vs-zero-day evaluation set for RQ3 — known-attack
samples to be perturbed later (FGSM/PGD by Team B) plus the genuine held-out zero-day class; define a
labelling schema that keeps 'adversarial-known' and 'true-zero-day' distinguishable in evaluation.*
Script: [`../scripts/make_rq3_evalset.py`](../scripts/make_rq3_evalset.py) (seed 42) ·
Data: `week2/rq3/<name>/{adversarial_source_pool,eval_clean}.csv` + `rq3_schema.json`.

## 1. RQ3 — the question and why it's hard

**RQ3:** can the detector tell an **adversarially-perturbed known attack** apart from a **genuinely novel
(zero-day) attack**? This is hard because an adversarial example is **semantically in-distribution** (a
perturbed *known* class) yet lands in **OOD regions** of the representation — so a single novelty score
tends to flag **both** and cannot separate them (Karunanayake et al., *Out-of-Distribution Data: An
Acquaintance of Adversarial Examples*, ACM Computing Surveys 2024). The evaluation must therefore keep the
two causes **factorially independent**, or the result is uninterpretable.

## 2. Design — a two-axis factorial eval set (never a flat label)

| | **clean** | **adversarial** (Team B: FGSM/PGD) |
|---|---|---|
| **origin = known** | `clean_known` ✅ shipped | `adv_known` ← perturb the pool |
| **origin = novel** (zero-day) | `true_zeroday` ✅ shipped | *(not generated — never perturb zero-day)* |

- **Axis A — origin ∈ {known, novel}.** `novel` = the held-out zero-day class (never in train/calibration).
- **Axis B — perturb ∈ {clean, adversarial}.** Team B fills `adversarial` by attacking the source pool.
- **Adversarial seeds come only from KNOWN attacks — never from the zero-day class** — so a model that
  confuses `adv_known` with `true_zeroday` reveals the RQ3 failure, not a data artifact.

## 3. Labelling schema (column contract)

Every row carries: `sample_id` (stable, traceable through perturbation), `dataset`, `attack_class`,
**`origin`** {known, novel}, **`perturb`** {clean, adversarial}, **`role`** {clean_known, adv_source,
true_zeroday, adv_known}, **`should_flag_novel`** (= origin==novel), **`should_flag_adversarial`**
(= perturb==adversarial), then the 17 unified features + `label_binary` + `label_family`.

## 4. What ships (measured)

| Dataset | `adv_source_pool` (clean known attacks → perturb) | `clean_known` | `true_zeroday` (clean-novel) | pool classes |
|---|---:|---:|---:|---:|
| **CIC-IoT2023** | 3,273 | 3,473 | 3,000 | 30 |
| **BoT-IoT** | 600 | 800 | 683 | 3 |
| **UNSW-NB15** | 956 | 1,156 | 1,216 | 7 |

Balanced (≤ 200 rows / known class); zero-day capped to ~3,000 balanced across its families. **Invariant
(asserted):** the adversarial-source pool contains **only known attacks — 0 zero-day rows**.

## 5. Adversarial-generation contract (for Team B)

- **Attacks:** FGSM and PGD, applied in the **classical 17-feature space *before* angle encoding** — the
  real attack surface (quantum-state-space perturbations barely move VQC accuracy; West et al., *Benchmarking
  Adversarially Robust QML at Scale*, 2022).
- **ε-budget** is in **robust-scaled feature units** (features come pre-scaled from the Week-1 unified
  `scalers.json`; angle-encode *after* perturbing). Log `{attack, eps, seed_class}` per adversarial sample.
- **Seed only from `adversarial_source_pool.csv`**; keep the original `sample_id` so each `adv_known` row
  traces to its clean known-attack source. This produces the `adv_known` cell (origin=known, perturb=adversarial).

## 6. Metrics (defined here; computed by Team B)

- **Novelty AUROC / FPR@95** — `clean_known` vs `true_zeroday` **only** (perturbation excluded so it cannot
  contaminate the novelty benchmark).
- **Adversarial-detection AUROC** — `clean_known` vs `adv_known`.
- **RQ3 result = the 3×3 confusion matrix** over {`clean_known`, `adv_known`, `true_zeroday`}: the
  **off-diagonal `adv_known` ↔ `true_zeroday` confusion rate** is the headline number (how often the model
  mistakes a perturbed known attack for a genuine zero-day, and vice-versa).
- Report **closed-set known-class accuracy** alongside (Shao et al., *Open-set Adversarial Defense*, 2020).

## Concerns & Recommendations

- **Keep the axes independent:** do **not** perturb zero-day samples and do **not** add novel classes to the
  adversarial pool — otherwise the 3×3 confusion conflates the two effects and RQ3 becomes unanswerable.
- **ε reported in scaled units** — because angle encoding wraps features into radians, an ε in raw units ≠ an
  ε in radians; fixing the unit at the scaled-feature stage keeps the classical baseline and the VQC comparable.
- **BoT-IoT zero-day (Theft) is weakly separable** even when clean ([`w2_02`](w2_02_split_integrity.md)) —
  expect the `adv_known ↔ true_zeroday` confusion to be highest on BoT; report per-dataset, never pooled.

---
*Reproduce:* `python week2/scripts/make_partitions.py && python week2/scripts/make_rq3_evalset.py`
→ `week2/rq3/<name>/{adversarial_source_pool,eval_clean}.csv` + `rq3_schema.json`.
