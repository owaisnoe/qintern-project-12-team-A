# Table A — In-Distribution Detection (RQ1)

**Caption.** Closed-set detection on the KNOWN test split at seed 42: accuracy, macro-F1, and one-vs-rest macro AUROC for each system per dataset. XGBoost is the frozen Day-12 detector on real features; QS-Net is the CQ-ZDR head. `*` on QS-Net accuracy = exact McNemar vs XGBoost significant at α = 0.05 after Holm over the dataset family.

| Dataset | System | scores | accuracy | macro-F1 | OVR-AUROC | McNemar vs XGBoost (p Holm) |
|---|---|---|---:|---:|---:|---:|
| CICIoT2023 | XGBoost (detector) | real | 0.9896 | 0.8043 | 0.9990 | — (reference) |
| CICIoT2023 | QS-Net (CQ-ZDR) | dummy | 0.9034*‡ | 0.6598‡ | 0.9438‡ | 0.00e+00‡ |
| BoT-IoT | XGBoost (detector) | real | 0.9515 | 0.9727 | 0.9955 | — (reference) |
| BoT-IoT | QS-Net (CQ-ZDR) | dummy | 0.9396*‡ | 0.8339‡ | 0.9509‡ | 1.45e-06‡ |
| UNSW-NB15 | XGBoost (detector) | real | 0.8020 | 0.6016 | 0.9695 | — (reference) |
| UNSW-NB15 | QS-Net (CQ-ZDR) | dummy | 0.7966‡ | 0.5513‡ | 0.8711‡ | 3.53e-01‡ |

‡ **Provisional — rides the Day-14 `dummy` fidelity interface.** The QS-Net cells (and the McNemar that compares them to the real detector) reprice unchanged-in-form on Team B's real prototypes (`--source real --scores-root <dir>`); the XGBoost row is already final (real Day-12 model on real features).

**Reading the table.** RQ1 asks whether each system is a competent KNOWN-class detector before its novelty behaviour (Table B) is meaningful. XGBoost sets a strong closed-set bar; the QS-Net numbers here are the dummy placeholder and exist to prove the table assembles and the McNemar pairing is row-aligned. The sign and significance convention is what carries into the manuscript; the numbers arrive with Team B's real fidelities.

