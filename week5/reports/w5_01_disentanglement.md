# Week 5 · Day 26 — Disentanglement (RQ3): Separation AUROC

Task (`qi26_12_Week_5.pdf`): *support the disentanglement experiment — supply adversarial-known vs true-zero-day labels + scoring, compute the **separation AUROC**.* Team A owns the labels and the scoring rule; Team B runs the full integration and hands over the real separation scores.

Score: the Day-15 novelty score **s = 1 − max_c F(ρ_x, ρ_c)** (higher ⇒ more novel). Seed 42 · scores: **dummy** · AUROC = Mann–Whitney U / (n₊·n₋) · 95% CI = seed-42 stratified bootstrap (2000 resamples).

**Separation AUROC** = P(s(true-zero-day) > s(adversarial-known)) — true-zero-day is the POSITIVE class. 1.0 ⇒ the novelty score cleanly separates genuine novelty from adversarially-disguised known attacks; 0.5 ⇒ it cannot disentangle them (Proposition 2's separable budget ε\*: below ε\* the two stay separable, past it AUROC decays to 0.5).

## CICIoT2023

| Panel | positive | negative | n₊ | n₋ | **AUROC** | 95% CI |
|---|---|---|---:|---:|---:|---|
| **separation** | true_zeroday | adv_known | 5,492 | 5,492 | **0.4994**‡ | [0.4886, 0.5106] |
| zeroday_vs_clean | true_zeroday | clean_known | 5,492 | 18,883 | **0.9998** | [0.9998, 0.9999] |
| adv_vs_clean | adv_known | clean_known | 5,492 | 18,883 | **0.9998** | [0.9998, 0.9999] |

mean s — clean_known 0.1205 · true_zeroday 0.7714 · adv_known 0.7712.

## Reading the table (dummy interface)

‡ **Provisional — the separation column rides the Day-14 dummy interface.** Team B's real FGSM/PGD adversarial-known scores are not in yet, so `adv_known` is a seeded second half of the zero-day pool: an independent draw from the **same** distribution as `true_zeroday`. That makes the separation AUROC ≈ 0.5 **by construction** — a deliberate honest null, not a result, and not a synthesised easy separation. It cannot be read as evidence that the score can (or cannot) truly disentangle the two.
- `zeroday_vs_clean` and `adv_vs_clean` both come out high because both halves sit far from the KNOWN prototypes — which is exactly *why* separation is the hard question: two populations that each look novel against clean traffic need not be separable from each other.
- The identical command reprices every cell the moment Team B ships `rq3_scores.parquet` (`--source real --scores-root <dir>`); only the separation row is then a genuine RQ3 result.

## What Team A supplies vs what Team B supplies

- **Team A (this module):** the labels (role ∈ {clean_known, adv_known, true_zeroday}), the scoring rule (s = 1 − max_c F), the AUROC + bootstrap-CI machinery, and the 3-way panel.
- **Team B (Day 26):** the real per-sample fidelities behind each role — in particular the adversarially-perturbed known attacks (FGSM/PGD at budget ε) that populate `adv_known`.

CSV: `_generated/w5_01_disentanglement.csv` · JSON: `_generated/w5_01_disentanglement.json`.
