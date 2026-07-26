# Table B — Zero-Day Guarantee (RQ2)

**Caption.** Split-conformal zero-day guarantee at a single primary α = 0.05, seed 42. For each dataset: the deployed threshold q = s_(k), k = ⌈(1−α)(n+1)⌉ calibrated on held-out KNOWN traffic; the **achieved** false-zero-day rate on the KNOWN test split; the exact 99% finite-sample acceptance band for that rate under exchangeability (E ~ BetaBinomial(m, n+1−k, k)); and, at the same operating point, the **true-zero-day recall** — the fraction of genuinely novel attack traffic flagged. Coverage bounds false alarms only, so recall is reported beside it and never in its place.

| Dataset | n_cal | q | target α | achieved α | exact 99% band | guarantee | exchangeability | n_zero-day | **QS-Net recall** | best classical | Δ |
|---|---:|---:|---:|---:|---|:--:|:--:|---:|---:|---|---:|
| CICIoT2023 | 18,883 | 0.300551 | 0.05 | 0.0486‡ | [0.0443, 0.0559] | **held**‡ | PASS‡ | 10,984 | **0.9998**‡ | 0.9978 (Isolation Forest) | +0.0020‡ |
| BoT-IoT | 18,591 | 0.262934 | 0.05 | 0.0530‡ | [0.0443, 0.0559] | **held**‡ | PASS‡ | 683 | **0.0952**‡ | 0.7233 (Isolation Forest) | -0.6281‡ |
| UNSW-NB15 | 10,112 | 0.383380 | 0.05 | 0.0463‡ | [0.0423, 0.0581] | **held**‡ | PASS‡ | 1,216 | **0.3857**‡ | 0.2656 (Autoencoder) | +0.1201‡ |

‡ **Provisional — rides the Day-14 `dummy` fidelity interface.** These cells reprice unchanged-in-form when Team B's real prototypes land (`--source real --scores-root <dir>`); the columns without ‡ are already final.

**Why the band is already final.** The acceptance region depends only on the split sizes and α — n_cal, k and m_test are fixed by the Day-14 partition freeze — so the tolerance this table will be judged against does not move when the scores change. What is open is only where the achieved rate lands inside it.

**Reading the Δ column.** Δ = QS-Net recall − best classical recall at the same α. It is the RQ2 headline and it is *signed*: negative cells are where the quantum detector loses, and they stay in the table (Day-25 RQ5 honesty).

