# AK — Week 5 Days 26-27 Handoff (Disentanglement AUROC, Table A, Results Freeze, Figure 2)

Covers AK's Week-5 contribution to the results week: the RQ3 disentanglement separation AUROC (Day 26), the
RQ1 in-distribution detection table with significance + coverage diagnostics (Day 26), the Team-A results
freeze (Day 26), and the headline coverage figure (Day 27). All reuse the consolidated Week-4 code
(conformal / coverage / stats / freeze) and the Week-3 conformal machinery. Team A owns Proposition 3
(conformal coverage); Days 28-32 (final figures/tables + Team-B hand-off) continue from here.

## What was implemented

1. **Day 26 — disentanglement (RQ3)** (`week5/scripts/disentanglement.py`, `w5_01_disentanglement.md`). The
   separation AUROC as a 3-way panel on the Day-15 novelty score `s = 1 − max_c F`: `separation` (true-zero-day
   POSITIVE vs adversarial-known NEGATIVE — the RQ3 headline), `zeroday_vs_clean`, `adv_vs_clean`. AUROC =
   Mann-Whitney U / (n₊·n₋); 95% CI by a seed-42 stratified bootstrap. Team A supplies the labels + the scoring
   rule + the AUROC machinery; Team B supplies the real adversarial (FGSM/PGD) fidelities via a new
   `rq3_scores.parquet` interface (`--source real`).
2. **Day 26 — Table A (RQ1) + significance + coverage** (`week5/scripts/table_a.py`, `w5_02_table_a.md`).
   Closed-set detection on the KNOWN test split: accuracy / macro-F1 / OVR-macro AUROC. XGBoost is **real**
   (read from the frozen Day-12 `results.json`, never recomputed); QS-Net is **provisional** from the dummy
   interface. Significance = exact McNemar QS-Net vs XGBoost (Day-17 `stats_protocol`), Holm over the dataset
   family. Plus the **all-seed coverage check** (pooled re-split seeds 42-46) and the **per-class achieved-FZR
   diagnostic** (each class judged against its own exact BetaBinomial band). `.md` + booktabs `.tex`.
3. **Day 26 — results freeze** (`week5/scripts/freeze_results.py`, `RESULTS_FROZEN/`). SHA-256 manifest over
   the Day-26/27 artefacts + a scalar snapshot; `--verify` re-hashes, `--reproduce` re-runs the three
   deterministic mains and asserts every headline scalar reproduces to 1e-9. Adds an `_assert_lf` gate.
4. **Day 27 — Figure 2 (headline)** (`week5/scripts/figure2_coverage.py`, `w5_03_figure2.md`). Reliability
   diagram: achieved false-zero-day rate vs target α, identity diagonal, per-dataset series over the exact
   **Beta-Binomial** validity band, 5-seed points (seeds 42-46) at the headline α.
5. **Repo hygiene** — a repo-root `.gitattributes` (`* text=auto eol=lf` + pinned binaries) so a fresh clone
   is byte-identical on any OS and the SHA-256 freeze manifests `--verify` clean off a Windows checkout; and a
   source fix so `scores_root` is written repo-relative (absolute home paths had leaked into committed JSON).

## What went well

- **Pure reuse.** Every module builds on the consolidated Week-4 code — `conformal_calibrate`,
  `coverage_harness.coverage_band` (exact band), `live_coverage.fix_splits` (5-seed re-split),
  `stats_protocol.{mcnemar_exact,holm_bonferroni}`, and the `freeze_integration` skeleton — no math
  re-implemented. The suite grew 110 → 135 tests, all green.
- **The provisional/final split is airtight.** XGBoost and the exact bands are real/final; every QS-Net cell
  and the McNemar carry the ‡ marker and reprice with one flag. No dummy number can pass as a result.
- **The coverage story is clean end-to-end:** all-seed coverage holds the band 5/5 on all three datasets, and
  Figure 2 shows the achieved rate tracking the diagonal inside the exact band — the paper's headline picture.
- **The per-class diagnostic answers the class-imbalance flag with the correct mechanism:** rare classes do
  not skew the marginal threshold; the real gap is the absence of a per-class guarantee, and the fix is
  clustered conformal — not full class-conditioning (several classes sit below the ⌈1/α⌉−1 = 19 floor).

## Challenges and issues

1. **Dummy vs real.** Team B's real prototypes are not in, so QS-Net (Table A), the separation AUROC, and
   Figure 2's series are Day-14 **placeholders**; only the XGBoost row and the exact bands are real. Every
   output tags `source_kind` and reprices with `--source real --scores-root <dir>`.
2. **The separation AUROC is a deliberate honest null on the dummy.** With no real adversarial scores,
   `adv_known` is a seeded independent half of the zero-day pool, so separation AUROC ≈ 0.5 by construction.
   This is reported as plumbing (and stated on the report + the score), not as "the score cannot disentangle".
3. **Fresh-clone freeze verify was a Windows-checkout issue, not a data issue.** The manifests were already
   LF-consistent on Linux; a `core.autocrlf=true` checkout rewrote text files to CRLF and broke the hashes.
   Fixed at the root with `.gitattributes` (the source of truth), belt-and-braces with the `_assert_lf` gate.
4. **Absolute-path leak.** Four committed JSONs recorded an absolute `scores_root` (home dir + OS username).
   Fixed at the source (repo-relative) across `conformal_calibrate` / `freeze_integration` /
   `conformal_integration` / `significance`, and the committed values scrubbed with no numeric change.

## Concerns and recommendations

- **Team B:** ship real per-seed QS-Net scores (reprices Table A/B + Figure 2 and unblocks QS-Net entering the
  Day-25 5-seed paired-t), and the RQ3 separation scores (`rq3_scores.parquet`) for the Day-26 hand-off. Keep
  the Week-4 conventions: non-squared Uhlmann fidelity (`sqrt()` PennyLane/Qiskit's F²), one primary α.
- **Report coverage AND recall/power together** (Proposition 3): Table A is the closed-set half, Table B the
  zero-day half; neither stands alone.
- **Days 23-25 still need a task-handoff doc** (Days 18-22 and 26-27 have theirs) — not AK's to author.
- **Re-clone check:** after the `.gitattributes` lands, confirm a fresh clone `--verify`s clean on Windows.

## Measured results (Days 26-27, dummy interface, α = 0.05)

**Day 26 — disentanglement (separation AUROC, true-zero-day vs adv-known):** CIC 0.4994 [0.4886, 0.5106];
BoT 0.4763 [0.4335, 0.5181]; UNSW 0.5104 [0.4796, 0.5416] — all bracket 0.5 (honest null). Novelty is
detectable: zeroday_vs_clean 0.9998 / 0.5881 / 0.8477 and adv_vs_clean 0.9998 / 0.6083 / 0.8405.

**Day 26 — Table A (RQ1):**

| Dataset | XGBoost acc / F1 / AUROC (real) | QS-Net acc / F1 / AUROC (prov.) | McNemar p (Holm) |
|---|---|---|---|
| CIC-IoT2023 | 0.9896 / 0.8043 / 0.9990 | 0.9034 / 0.6598 / 0.9438 | ~0 (sig) |
| BoT-IoT | 0.9515 / 0.9727 / 0.9955 | 0.9396 / 0.8339 / 0.9509 | 1.45e-6 (sig) |
| UNSW-NB15 | 0.8020 / 0.6016 / 0.9695 | 0.7966 / 0.5513 / 0.8711 | 0.35 (ns) |

All-seed coverage (seeds 42-46): mean FZR 0.0518 / 0.0501 / 0.0508, **inside the exact 99% band on 5/5 seeds
for all three**. Per-class achieved-FZR diagnostic: **0 / 31, 0 / 4, 0 / 8** classes outside their own band on
the dummy (real scores are where a rare class would show, pointing to clustered conformal if so).

**Day 26 — freeze:** 16 artefacts + 39 scalars pinned; `--verify` 0 mismatch; `--reproduce` 39/39 scalars to
1e-9.

**Day 27 — Figure 2:** achieved FZR tracks the diagonal inside the exact BetaBinomial band across α ∈
[0.01, 0.20] on all three; 5-seed means at α = 0.05 are 0.0518 / 0.0501 / 0.0508, each inside its band.

## References

- Separation AUROC / OOD-vs-adversarial: Hendrycks & Gimpel 2017 (MSP); Lee et al. 2018 (Mahalanobis);
  Karunanayake et al. 2025 (OOD-vs-adversarial survey). Separable budget ε\* = Proposition 2.
- Figure 2 band: Vovk 2012; Angelopoulos & Bates 2023 §3.2 (coverage | cal ~ Beta(k, n+1−k); E ~
  BetaBinomial). The correct band for a calibration-draw plot — **not** Clopper–Pearson (the fixed-threshold
  proportion CI).
- Per-class / clustered conformal: Ding, Angelopoulos, Bates, Jordan & Tibshirani 2023 (class-conditional /
  clustered); Sadinle, Lei & Wasserman 2019; Vovk (Mondrian) 2005.
- Significance: exact McNemar + Holm–Bonferroni (Day-17 `stats_protocol.py`); Demšar 2006 (report effect
  sizes alongside p-values).

## Do not commit
- `../.venv/`, any `__pycache__/` (gitignored); the raw dataset archives (outside git). *(Small `_generated/`
  result files, the figure PNG, and `RESULTS_FROZEN/` ARE committed, matching the repo convention.)*

## Verification performed
- `python -m pytest week2/tests week3/tests week4/tests week5/tests -q` → **135 passed, 8 subtests**.
- `disentanglement.py` → 3-way AUROC panel, separation ≈ 0.5 (honest null), CIs bracket 0.5.
- `table_a.py` → Table A `.md`/`.tex`, McNemar+Holm (2 sig / 1 ns), all-seed coverage 5/5, per-class FZR CSV.
- `figure2_coverage.py` → reliability PNG, 5-seed points inside the exact band.
- `freeze_results.py` → `--verify` 0 mismatch, `--reproduce` 39/39 scalars to 1e-9.
- `freeze_integration.py --verify` → 34 files, 0 mismatch after the source scrub + re-freeze.

## Chat update

```text
Team A - Week 5 Days 26 and 27 done, on the week5-ak branch (Week 4 first consolidated onto main via a PR:
the un-revert restored Days 18 to 20 that main had reverted, then the week4 line merged clean; 110 tests
green there).

Day 26 (disentanglement, RQ3): separation AUROC with true-zero-day as positive and adversarial-known as
negative, reported as a 3-way panel. On the dummy interface it is about 0.5 on all three datasets, which is
the honest null - with no real FGSM or PGD scores yet, adversarial-known is a seeded independent half of the
zero-day pool, so the two are indistinguishable by construction. Novelty itself is detectable
(zeroday-vs-clean and adv-vs-clean both high). Reprices to a real result when Team B ships the separation
scores.

Day 26 (Table A, RQ1 in-distribution detection): accuracy, macro-F1, one-vs-rest macro AUROC per system.
XGBoost is real and final from the Day-12 results.json; QS-Net is provisional from the dummy interface. Exact
McNemar QS-Net vs XGBoost, Holm over the 3-dataset family: significant on CIC and BoT, not significant on
UNSW (p 0.35). All-seed coverage (pooled re-split seeds 42 to 46) holds the exact 99 percent band 5 of 5 on
every dataset, mean false-alarm rate about 0.05.

On the class-imbalance point: I added a per-class achieved false-alarm diagnostic. The mechanism is that rare
classes do not skew the marginal threshold - the mixture guarantee still holds - the real gap is that
marginal conformal gives no per-class coverage guarantee, so a rare class can be individually under or over
covered. Zero classes are out of their own band on the dummy; if one is on real scores, the fix is clustered
conformal (Ding et al. 2023), not full class-conditional (several classes are below the 19-per-class floor).

Day 27 (Figure 2, the headline coverage plot): empirical false-zero-day rate vs target alpha, tracking the
diagonal inside the exact Beta-Binomial band on all three datasets, with the 5-seed points at alpha 0.05
sitting inside the band. Data and figure are in week5/reports.

I also froze the Day-26/27 results (SHA-256 + a reproduce check that re-runs the mains and confirms every
number to 1e-9), and added a repo-root .gitattributes so a fresh clone verifies clean on Windows too (the
earlier fresh-clone verify failures were a CRLF checkout issue, not a data issue). One hygiene fix: a few
committed JSONs had an absolute local path in a scores_root field - now written repo-relative at the source.

Everything quantum this week is still the dummy interface and tagged provisional; the table structure, the
significance convention and the figure are final and reprice with one flag on the real prototypes.

To confirm: Team B real per-seed scores ETA (reprices Table A, Table B and Figure 2, and lets QS-Net enter
the 5-seed paired-t); the Day-26 separation-score hand-off (rq3_scores.parquet with role, sample_id, fid
columns); and the non-squared fidelity plus single-alpha spec. Also Days 23 to 25 still need a task handoff
doc. Full suite 135 tests green. Thanks.
```
