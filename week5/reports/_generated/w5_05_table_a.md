# Table A — In-Distribution Detection (RQ1), FINAL with effects

**Caption.** Closed-set detection on the KNOWN test split at seed 42: accuracy, macro-F1, one-vs-rest macro AUROC per system. `*` on QS-Net accuracy = exact McNemar vs XGBoost significant at α = 0.05 after Holm over the dataset family; the effect columns give Cohen's h on the accuracy gap and the paired d_z on per-sample correctness (Demšar 2006 — effect sizes beside p-values). In-distribution false-alarm significance vs the novelty heads is the companion family (`w5_05_known_fa.csv`).

| Dataset | System | scores | accuracy | macro-F1 | OVR-AUROC | p Holm (vs XGB) | Cohen's h | d_z |
|---|---|---|---:|---:|---:|---:|---:|---:|
| CICIoT2023 | XGBoost (detector) | real | 0.9896 | 0.8043 | 0.9990 | — (reference) | — | — |
| CICIoT2023 | QS-Net (CQ-ZDR) | dummy | 0.9034*‡ | 0.6598‡ | 0.9438‡ | 0.00e+00‡ | -0.427‡ | -0.276‡ |
| BoT-IoT | XGBoost (detector) | real | 0.9515 | 0.9727 | 0.9955 | — (reference) | — | — |
| BoT-IoT | QS-Net (CQ-ZDR) | dummy | 0.9396*‡ | 0.8339‡ | 0.9509‡ | 1.45e-06‡ | -0.052‡ | -0.036‡ |
| UNSW-NB15 | XGBoost (detector) | real | 0.8020 | 0.6016 | 0.9695 | — (reference) | — | — |
| UNSW-NB15 | QS-Net (CQ-ZDR) | dummy | 0.7966‡ | 0.5513‡ | 0.8711‡ | 3.53e-01‡ | -0.013‡ | -0.009‡ |

‡ **Provisional — rides the Day-14 `dummy` fidelity interface**; reprices on Team B's real prototypes (`--source real --scores-root <dir>`). The XGBoost row is final (real frozen Day-12 model). Negative h / d_z = QS-Net below XGBoost; the sign stays in the table (RQ5 honesty).

