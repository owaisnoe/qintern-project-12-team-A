# Week 5 · Day 28 — Table B (Zero-Day Guarantee, RQ2) FINAL + All-Seed Coverage CIs

Task (`qi26_12_Week_5.pdf`): *finalise Table B (zero-day): true-zero-day recall + achieved α vs target, all datasets, with the guarantee visibly holding; re-run coverage across all 5 seeds for the CI.* Seed 42 · α = 0.05 · trio CICIoT2023, BoT-IoT, UNSW-NB15 · quantum scores: **dummy**.

Day 28 keeps the Day-24 assembly discipline — the canonical cells still trace to the Day-21 freeze / Day-22 adapter / Day-19 classical arms and are never recomputed here — and adds the **all-seed coverage CIs**: the pooled KNOWN calibration ∪ test scores re-drawn at the original sizes under seeds 42–46 (Day-23 `fix_splits`), each re-split re-calibrated and judged against its own exact band, with the FIXED zero-day pool scored at each re-split's q. Rendered standalone for the manuscript in [`_generated/w5_04_table_b.md`](_generated/w5_04_table_b.md) + [`.tex`](_generated/w5_04_table_b.tex). Reproduced here:

| Dataset | q | target α | achieved α | 5-seed α (mean [95% CI]) | exact 99% band | in band | **QS-Net recall** | 5-seed recall (mean [95% CI]) | best classical | Δ |
|---|---:|---:|---:|---|---|:--:|---:|---|---|---:|
| CICIoT2023 | 0.300551 | 0.05 | 0.0486‡ | 0.0517 [0.0498, 0.0537]‡ | [0.0443, 0.0559] | held + 5/5‡ | **0.9998**‡ | 0.9998 [0.9998, 0.9998]‡ | 0.9978 (Isolation Forest) | +0.0020‡ |
| BoT-IoT | 0.262934 | 0.05 | 0.0530‡ | 0.0501 [0.0476, 0.0527]‡ | [0.0443, 0.0559] | held + 5/5‡ | **0.0952**‡ | 0.0928 [0.0912, 0.0945]‡ | 0.7233 (Isolation Forest) | -0.6281‡ |
| UNSW-NB15 | 0.383380 | 0.05 | 0.0463‡ | 0.0508 [0.0473, 0.0542]‡ | [0.0423, 0.0581] | held + 5/5‡ | **0.3857**‡ | 0.3929 [0.3884, 0.3975]‡ | 0.2656 (Autoencoder) | +0.1201‡ |

‡ provisional (Day-14 **dummy** fidelity interface). 

## Canonical vs re-split — what each column claims

- **achieved α (canonical)** — the Day-22 adapter at the *frozen* q on the canonical seed-42 split: the deployed operating point.
- **5-seed α CI** — the same mechanism under 5 fresh calibration/test draws: is the deployed rate a lucky split? Each re-split is judged against its own exact band; the CI describes the mechanism's spread, not a second estimate of the deployed rate.
- **5-seed recall CI** — the FIXED zero-day pool scored at each re-split's q: how sensitive the power number is to the calibration draw.

## All-seed coverage CIs (the Day-28 deliverable)

| Dataset | mean FZR | 95% CI | std | in band | CI covers α | mean recall | recall 95% CI |
|---|---:|---|---:|:--:|:--:|---:|---|
| CICIoT2023 | 0.0517 | [0.0498, 0.0537] | 0.0016 | 5/5 | ✅ | 0.9998 | [0.9998, 0.9998] |
| BoT-IoT | 0.0501 | [0.0476, 0.0527] | 0.0020 | 5/5 | ✅ | 0.0928 | [0.0912, 0.0945] |
| UNSW-NB15 | 0.0508 | [0.0473, 0.0542] | 0.0028 | 5/5 | ✅ | 0.3929 | [0.3884, 0.3975] |

**3/3 datasets hold the exact band on all 5 re-split seeds and every 95% CI covers the target α = 0.05** — the conformal false-alarm control is stable across the 5-seed convention, and the recall CIs quantify how little the power number moves with the calibration draw. Per-seed detail: [`_generated/w5_04_allseed_ci.csv`](_generated/w5_04_allseed_ci.csv).

## Cross-check against Day-26 Table A

The 5-seed FZR means here and Table A's all-seed coverage means come from the same seeds and machinery, so they must be identical: agrees to 1e-9 on every dataset.

## Which cells are already final

| Column group | Status | Why |
|---|---|---|
| n_cal, k, m_test, n_zero-day | **final** | fixed by the Day-14 partition freeze |
| exact 99% band | **final** | a function of (n_cal, k, m_test) and α only |
| best-classical recall | **final** | real Day-12 models on real features |
| q, achieved α, 5-seed CIs, guarantee, QS-Net recall, Δ | provisional | ride the Day-14 dummy fidelity interface |

## Bottom line

Table B is final in structure, caption, band and CI convention: the guarantee holds at the deployed threshold and across every re-split seed, with the target α inside every 95% CI. The ‡ cells reprice with one flag when Team B lands real prototypes, and that rerun is the one the manuscript cites.

CSV: `_generated/w5_04_table_b.csv` · per-seed: `_generated/w5_04_allseed_ci.csv` · JSON: `_generated/w5_04_table_b.json` · Table B: `_generated/w5_04_table_b.md` + `.tex`.
