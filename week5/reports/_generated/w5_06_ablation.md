# Conformal-vs-Heuristic Ablation (the guarantee's value)

**Caption.** Same novelty score s = 1 − max_c F on every row; only the threshold rule varies. Conformal: q = s_(k), k = ⌈(1−α)(n+1)⌉ on a held-out calibration split (the +1). Heuristic: the in-sample (1−α) percentile (no held-out split, no +1). Fixed: a hand-tuned τ = 0.5. Achieved false-zero-day rate on the KNOWN test split at α = 0.05, judged against the exact 99% BetaBinomial band; recall at the same threshold. Only the conformal rule carries a finite-sample certificate.

| Dataset | rule | τ | achieved FZR | in band | zero-day recall |
|---|---|---:|---:|:--:|---:|
| CICIoT2023 | **conformal (held-out, +1)** | 0.3006 | 0.0486‡ | ✅ | 0.9998‡ |
| CICIoT2023 | in-sample percentile (no +1) | 0.3005 | 0.0487‡ | ✅ | 0.9998‡ |
| CICIoT2023 | fixed τ = 0.5 | 0.5000 | 0.0013‡ | ⚠ | 0.9790‡ |
| BoT-IoT | **conformal (held-out, +1)** | 0.2629 | 0.0530‡ | ✅ | 0.0952‡ |
| BoT-IoT | in-sample percentile (no +1) | 0.2629 | 0.0531‡ | ✅ | 0.0952‡ |
| BoT-IoT | fixed τ = 0.5 | 0.5000 | 0.0009‡ | ⚠ | 0.0029‡ |
| UNSW-NB15 | **conformal (held-out, +1)** | 0.3834 | 0.0463‡ | ✅ | 0.3857‡ |
| UNSW-NB15 | in-sample percentile (no +1) | 0.3830 | 0.0465‡ | ✅ | 0.3865‡ |
| UNSW-NB15 | fixed τ = 0.5 | 0.5000 | 0.0075‡ | ⚠ | 0.1398‡ |

‡ **Provisional — rides the Day-14 `dummy` fidelity interface**; the asset reprices on Team B's real prototypes (`--source real --scores-root <dir>`). The *contrast between rules* — the deliverable — is structural: only conformal has the certificate, at any score quality.

