# Table B — Zero-Day Guarantee (RQ2), FINAL

**Caption.** Split-conformal zero-day guarantee at the single primary α = 0.05, seed 42. Per dataset: the deployed threshold q = s_(k) (frozen Day 21) with the achieved false-zero-day rate on the canonical KNOWN test split and its exact 99% BetaBinomial acceptance band; the **5-seed re-split** mean achieved rate with a t-based 95% CI (pooled calibration ∪ test re-drawn under seeds 42–46, each re-split judged against its own exact band); and, at the same operating points, the **true-zero-day recall** (canonical + 5-seed CI) beside the best classical head calibrated at the same α. Coverage bounds false alarms only; recall is the separate power axis.

| Dataset | n_cal | q | target α | achieved α | 5-seed α (mean [95% CI]) | exact 99% band | in band | n_zero-day | **QS-Net recall** | 5-seed recall (mean [95% CI]) | best classical | Δ |
|---|---:|---:|---:|---:|---|---|:--:|---:|---:|---|---|---:|
| CICIoT2023 | 18,883 | 0.300551 | 0.05 | 0.0486‡ | 0.0517 [0.0498, 0.0537]‡ | [0.0443, 0.0559] | **held** + 5/5 seeds‡ | 10,984 | **0.9998**‡ | 0.9998 [0.9998, 0.9998]‡ | 0.9978 (Isolation Forest) | +0.0020‡ |
| BoT-IoT | 18,591 | 0.262934 | 0.05 | 0.0530‡ | 0.0501 [0.0476, 0.0527]‡ | [0.0443, 0.0559] | **held** + 5/5 seeds‡ | 683 | **0.0952**‡ | 0.0928 [0.0912, 0.0945]‡ | 0.7233 (Isolation Forest) | -0.6281‡ |
| UNSW-NB15 | 10,112 | 0.383380 | 0.05 | 0.0463‡ | 0.0508 [0.0473, 0.0542]‡ | [0.0423, 0.0581] | **held** + 5/5 seeds‡ | 1,216 | **0.3857**‡ | 0.3929 [0.3884, 0.3975]‡ | 0.2656 (Autoencoder) | +0.1201‡ |

‡ **Provisional — rides the Day-14 `dummy` fidelity interface.** These cells reprice unchanged-in-form on Team B's real prototypes (`--source real --scores-root <dir>`); the columns without ‡ (n_cal, band, n_zero-day, best-classical recall) are already final.

**The guarantee visibly holds: 3/3 datasets stay inside their exact band on all 5 re-split seeds**, every 5-seed mean sits on the target (α = 0.05) with its 95% CI covering it, and the canonical deployed rate lands inside the band on every dataset. The re-split CI is the stability evidence — the canonical cell is the deployed operating point; the CI says it is not a lucky split.

