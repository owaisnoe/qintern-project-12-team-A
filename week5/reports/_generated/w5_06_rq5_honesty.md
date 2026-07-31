# RQ5 Honesty Summary — where quantum helps, and where it does not

Compiled from the Day-25 significance suite (`w4_06_significance.json`), seed 42, α = 0.05, scores **dummy**. Verdict rule: *ahead/behind* needs the zero-day McNemar to survive Holm AND the paired bootstrap CI to exclude 0; *equivalent* is a TOST-style call inside the ±0.05 recall margin; anything else stays *unresolved*. Effect sizes (Cohen's h) accompany every verdict.

**Headline count: quantum ahead 4 · behind 3 · equivalent 1 · unresolved 0** (dataset × baseline pairs, zero-day recall).

| Dataset | baseline | Δrecall (QS−base) | 95% CI | h | p Holm (McNemar zd) | verdict |
|---|---|---:|---|---:|---:|---|
| BoT-IoT | Autoencoder | -0.5300‡ | [-0.5710, -0.4876]‡ | -1.197‡ | 1.33e-84‡ | quantum behind (McNemar sig. + CI excludes 0) |
| BoT-IoT | Isolation Forest | -0.6281‡ | [-0.6706, -0.5886]‡ | -1.407‡ | 9.72e-107‡ | quantum behind (McNemar sig. + CI excludes 0) |
| BoT-IoT | OC-SVM | -0.6384‡ | [-0.6779, -0.5988]‡ | -1.429‡ | 1.18e-108‡ | quantum behind (McNemar sig. + CI excludes 0) |
| CICIoT2023 | Autoencoder | +0.3388‡ | [+0.3298, +0.3476]‡ | +1.216‡ | 0.00e+00‡ | quantum ahead (McNemar sig. + CI excludes 0) |
| CICIoT2023 | Isolation Forest | +0.0000‡ | [-0.0004, +0.0004]‡ | +0.000‡ | 1.00e+00‡ | equivalent (95% CI inside ±0.05 recall) |
| UNSW-NB15 | Autoencoder | +0.1176‡ | [+0.0831, +0.1538]‡ | +0.252‡ | 6.58e-10‡ | quantum ahead (McNemar sig. + CI excludes 0) |
| UNSW-NB15 | Isolation Forest | +0.3191‡ | [+0.2878, +0.3495]‡ | +0.818‡ | 5.45e-78‡ | quantum ahead (McNemar sig. + CI excludes 0) |
| UNSW-NB15 | OC-SVM | +0.3470‡ | [+0.3183, +0.3766]‡ | +0.944‡ | 1.50e-102‡ | quantum ahead (McNemar sig. + CI excludes 0) |

‡ **Provisional — every quantum number rides the Day-14 `dummy` fidelity interface**, so these verdicts are an artifact of the dummy generator and exist to prove the honesty machinery runs end-to-end. The identical compilation on Team B's real prototypes is the one the manuscript prints — including any negative rows. Negative rows are the point of RQ5: they stay in the table.

**Seed-level honesty floor.** With n = 5 seeds, the smallest significant paired effect is d_z ≈ 1.24 (80% power ≈ 1.68); QS-Net enters the seed-level family only when Team B ships per-seed scores (Team B emitting one score directory per training seed, then rerunning this module with --scores-root <dir> per seed).

