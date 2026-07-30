# Week 4 · Day 24 — RQ2 Across All Datasets + Table B (Zero-Day Guarantee) Skeleton

Task (`WEEK 4.pdf`): *Produce RQ2 outputs across all datasets: true-zero-day recall + achieved α. Assemble Table B (zero-day guarantee) skeleton.* Deliverables: **RQ2 results (all datasets)** + **Table B skeleton**. Seed 42 · primary α = 0.05 · trio CICIoT2023, BoT-IoT, UNSW-NB15 · quantum scores: **dummy**.

This day **assembles**; it does not recompute. Every cell traces to the artifact that produced it — the deployed q from the Day-21 freeze, the achieved α and recall from the Day-22 adapter running at that q, the exchangeability verdict from the Day-23 audit, and the classical arms from Day 19 at the same α. The one thing computed here is the exact band, because it is free: it depends on (n_cal, k, m_test) alone.

## Table B — the deliverable

Rendered standalone for the manuscript in [`_generated/w4_05_table_b.md`](_generated/w4_05_table_b.md) and [`_generated/w4_05_table_b.tex`](_generated/w4_05_table_b.tex) (booktabs). Reproduced here:

| Dataset | n_cal | q | target α | achieved α | exact 99% band | guarantee | exchangeability | n_zero-day | **QS-Net recall** | best classical | Δ |
|---|---:|---:|---:|---:|---|:--:|:--:|---:|---:|---|---:|
| CICIoT2023 | 18,883 | 0.300551 | 0.05 | 0.0486‡ | [0.0443, 0.0559] | **held**‡ | PASS‡ | 10,984 | **0.9998**‡ | 0.9978 (Isolation Forest) | +0.0020‡ |
| BoT-IoT | 18,591 | 0.262934 | 0.05 | 0.0530‡ | [0.0443, 0.0559] | **held**‡ | PASS‡ | 683 | **0.0952**‡ | 0.7233 (Isolation Forest) | -0.6281‡ |
| UNSW-NB15 | 10,112 | 0.383380 | 0.05 | 0.0463‡ | [0.0423, 0.0581] | **held**‡ | PASS‡ | 1,216 | **0.3857**‡ | 0.2656 (Autoencoder) | +0.1201‡ |

‡ provisional (Day-14 **dummy** fidelity interface). 

**The guarantee holds on 3/3 datasets** — every achieved rate lands inside its exact 99% band — and is literally ≤ α on 2/3. The one dataset that reads above α (BoT-IoT, 0.0530) is the familiar finite-sample fluctuation, not a violation: the band's upper edge is 0.0559 and the tail p-value is 0.09. That distinction is exactly why Table B publishes the band and not just a `≤ α` tick.

## Which cells are already final

| Column group | Status | Why |
|---|---|---|
| n_cal, k, m_test, n_zero-day | **final** | fixed by the Day-14 partition freeze |
| exact 99% band | **final** | a function of (n_cal, k, m_test) and α only — no scores enter it |
| best-classical recall | **final** | real Day-12 models on real features (never dummy) |
| q, achieved α, guarantee, exchangeability, QS-Net recall, Δ | provisional | ride the Day-14 dummy fidelity interface |

This is the practically useful part of Day 24 for the manuscript: **the tolerance Table B will be judged against is already publishable.** The acceptance region for the achieved rate is set by the split design, not by the detector, so it does not move when Team B's real fidelities arrive. Only where the achieved rate lands inside it is open.

## RQ2 results — all datasets, all systems

Coverage and recall on the same row for every arm, all calibrated at the same primary α (the Day-19 like-for-like rule). The quantum arm is the integrated pipeline at the **frozen** q; the classical arms are the frozen Day-12 heads re-thresholded at that α.

| Dataset | System | scores | q | achieved α | in band | n_zero-day | **true-zero-day recall** |
|---|---|---|---:|---:|:--:|---:|---:|
| CICIoT2023 | QS-Net (CQ-ZDR) | dummy | 0.300551 | 0.0486 | ✅ | 10,984 | **0.9998** |
| CICIoT2023 | Isolation Forest | real | 0.513429 | 0.0483 | ✅ | 10,984 | **0.9978** |
| CICIoT2023 | Autoencoder | real | 0.534323 | 0.0475 | ✅ | 10,984 | **0.4994** |
| BoT-IoT | QS-Net (CQ-ZDR) | dummy | 0.262934 | 0.0530 | ✅ | 683 | **0.0952** |
| BoT-IoT | Isolation Forest | real | 0.490030 | 0.0458 | ✅ | 683 | **0.7233** |
| BoT-IoT | OC-SVM | real | -0.774626 | 0.0478 | ✅ | 683 | **0.7218** |
| BoT-IoT | Autoencoder | real | 0.099035 | 0.0501 | ✅ | 683 | **0.5417** |
| UNSW-NB15 | QS-Net (CQ-ZDR) | dummy | 0.383380 | 0.0463 | ✅ | 1,216 | **0.3857** |
| UNSW-NB15 | Isolation Forest | real | 0.558992 | 0.0505 | ✅ | 1,216 | **0.0000** |
| UNSW-NB15 | OC-SVM | real | 5.783827 | 0.0513 | ✅ | 1,216 | **0.0033** |
| UNSW-NB15 | Autoencoder | real | 1.710545 | 0.0519 | ✅ | 1,216 | **0.2656** |

**11/11 system-dataset cells hold the guarantee.** That is the point of the left half of the table and it is deliberately boring: *every* system, quantum and classical, sits at ≈ 1−α, because they are all calibrated by the same conformal rule at the same α. Coverage is not what distinguishes them.

**Recall is.** And it does not favour one arm uniformly — the honest reading, which Day 25 (RQ5) has to carry into the paper:

- **CICIoT2023** — QS-Net 0.9998 vs 0.9978 (Isolation Forest), Δ = +0.0020 → comparable.
- **BoT-IoT** — QS-Net 0.0952 vs 0.7233 (Isolation Forest), Δ = -0.6281 → **quantum behind**.
- **UNSW-NB15** — QS-Net 0.3857 vs 0.2656 (Autoencoder), Δ = +0.1201 → **quantum ahead**.

On the dummy interface that pattern is an artifact of the Day-14 generator, **not a result** — it is reported now only to prove the table assembles and the sign convention works. The identical command reproduces it on real prototypes.

### Notes carried from the source artifacts

- CICIoT2023: classical head 'ocsvm' unavailable (Day-12 skipped) — omitted.

## Provenance

| Table-B input | Day | Artifact |
|---|---|---|
| frozen | 21 | `week4/INTEGRATION/frozen_thresholds.json` |
| integration | 22 | `week4/reports/_generated/w4_03_conformal_integration.json` |
| live | 23 | `week4/reports/_generated/w4_04_live_coverage.json` |
| recall | 19 | `week4/reports/_generated/w4_01_zeroday_recall.json` |

Nothing in Table B is computed from scratch here, so the table cannot silently disagree with the reports it summarises — if a source artifact is regenerated, re-running this module is the only step needed to bring the table with it.

Figure: `figures/w4_05_rq2_coverage_vs_recall.png` (written) — the guarantee panel and the power panel side by side, which is the paper's coverage-≠-power separation in one image.

## Bottom line

RQ2 is assembled across all 3 datasets: the conformal guarantee holds on 3/3 at the frozen threshold, the exchangeability assumption behind it was audited clean on Day 23, and true-zero-day recall is reported beside it for every system rather than in its place. Table B's structure, caption, band column and sign convention are final; the ‡ cells reprice when Team B lands real fidelities, and that rerun is the one that goes in the manuscript.

CSV: `_generated/w4_05_rq2_results.csv` · JSON: `_generated/w4_05_rq2_results.json` · Table B: `_generated/w4_05_table_b.md` + `.tex`.
