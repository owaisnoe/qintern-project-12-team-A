# Week 4 · Day 19 — Zero-Day Recall + Quantum-vs-Classical Novelty

Task (`qi26_12_Week_4.pdf`): *zero-day detection recall at the calibrated α; compare against the classical Isolation-Forest / OC-SVM novelty heads.* All systems calibrated to the **same α = 0.05** with the single Day-15 rule q = s_(k), k = ⌈(1−α)(n+1)⌉ ([`../../week3/scripts/conformal_calibrate.py`](../../week3/scripts/conformal_calibrate.py)); flag a point as zero-day iff its novelty score > q.

**Coverage and recall reported together** (Proposition 3 §5.2: the conformal guarantee bounds *false alarms* only — a detector flagging nothing has perfect coverage — so detection **power** (zero-day recall) is a separate axis). Quantum = CQ-ZDR on the Day-14 fidelity interface (**dummy** placeholder, reprices at real prototypes); classical = the **real** frozen Day-12 models re-thresholded at α. Seed 42.

## CICIoT2023

| System | scores | n_cal | q | known coverage | false-zero-day (≤ α) | **zero-day recall** |
|---|---|---:|---:|---:|---:|---:|
| quantum_cqzdr | dummy | 18,883 | 0.300551 | 0.9514 | 0.0486 | **0.9998** |
| classical_isolation_forest | real | 18,883 | 0.513429 | 0.9517 | 0.0483 | **0.9978** |
| classical_autoencoder | real | 18,883 | 0.534323 | 0.9525 | 0.0475 | **0.4994** |

## BoT-IoT

| System | scores | n_cal | q | known coverage | false-zero-day (≤ α) | **zero-day recall** |
|---|---|---:|---:|---:|---:|---:|
| quantum_cqzdr | dummy | 18,591 | 0.262934 | 0.9470 | 0.0530 | **0.0952** |
| classical_isolation_forest | real | 18,591 | 0.490030 | 0.9542 | 0.0458 | **0.7233** |
| classical_ocsvm | real | 18,591 | -0.774626 | 0.9522 | 0.0478 | **0.7218** |
| classical_autoencoder | real | 18,591 | 0.099035 | 0.9499 | 0.0501 | **0.5417** |

## UNSW-NB15

| System | scores | n_cal | q | known coverage | false-zero-day (≤ α) | **zero-day recall** |
|---|---|---:|---:|---:|---:|---:|
| quantum_cqzdr | dummy | 10,112 | 0.383380 | 0.9537 | 0.0463 | **0.3857** |
| classical_isolation_forest | real | 10,112 | 0.558992 | 0.9495 | 0.0505 | **0.0000** |
| classical_ocsvm | real | 10,112 | 5.783827 | 0.9487 | 0.0513 | **0.0033** |
| classical_autoencoder | real | 10,112 | 1.710545 | 0.9481 | 0.0519 | **0.2656** |

## Reading the table
- All systems hold coverage ≈ 1−α at the same α (that is the guarantee); what differs is **recall** — the paper's separation. Report both, never recall alone.
- The **quantum** column is the Day-14 **dummy** placeholder (CIC's near-1.0 recall is a synthetic artifact seeded to the Day-9 diagnostic, not a result); the **classical** column is real. The identical command reprices the quantum arm the moment Team B lands real fidelities (`--source real --scores-root <team-B dir>`).
- **CIC-IoT2023 has no OC-SVM** (Day-12 shipped Isolation-Forest + Autoencoder); its OC-SVM row is omitted, not synthesized.

### Notes
- CICIoT2023: classical head 'ocsvm' unavailable (Day-12 skipped) — omitted.
