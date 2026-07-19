# Google Drive Upload Guide — Team A · Week 1–2 deliverables

What to upload to **Team A's shared Google Drive folder**, and what to leave out. Total ≈ **310 MB**
(Week 1 ~200 MB + Week 2 ~110 MB).

> ⚠️ `reports/dashboard.html` and `reports/figures/*.png` are **git-ignored locally** (regeneratable),
> but they **are deliverables** — include them in the Drive upload. Git-ignored ≠ don't-share.

## ✅ Upload these (Week-1 deliverables)
| Item | Path | Size | Why |
|---|---|---:|---|
| README (index) | `week1/README.md` | 8 KB | entry point |
| This guide | `week1/UPLOAD.md` | 4 KB | so teammates see the packaging |
| Reports (Day 1 ①②③ + flaws) | `week1/reports/00–03_*.md` | ┐ | dataset comparison / feature inventory / attack summary / flaws |
| Reports (Day 2 EDA ①②③) | `week1/reports/04–06_*.md` | ┘ 80 KB | EDA report / dashboard index / data-quality report |
| Report (Day 3 pipeline) | `week1/reports/07_preprocessing_pipeline.md` | 8 KB | preprocessing pipeline + cleaned datasets |
| Report (Day 4 QADCP) | `week1/reports/08_qadcp_design.md` (+ `figures/qadcp_workflow.png`) | 13 KB | QADCP design: workflow diagram + implementation |
| Report (Day 5 zero-day) | `week1/reports/09_zero_day_benchmark.md` (+ `figures/zero_day_tiers.png`) | 9 KB | difficulty-aware zero-day benchmark (Easy/Medium/Hard) + similarity analysis |
| Report (Day 5 PCA baseline) | `week1/reports/10_pca_baseline.md` | 8 KB | ranked-8 vs PCA-8 on the 8-qubit budget (Team-C comparison) |
| Report (Day 6 unified package) | `week1/reports/12_unified_schema.md` + `13_unified_package.md` + `METADATA.md` | 20 KB | unified schema + package docs |
| Report (Day 7 handover) | `week1/reports/14_handover_report.md` | 10 KB | final handover report |
| Team C interface | `week1/reports/15_teamC_interface.md` | 6 KB | feature selection handover |
| Integration meeting | `week1/reports/16_integration_meeting.md` | 6 KB | presentation outline |
| Mentor note (benchmark lock) | `week1/reports/17_unified_collapse_mentor_note.md` | 8 KB | CIC/BoT/UNSW locked; TON/Edge set aside |
| Enriched exploration (appendix) | `week1/reports/18_enriched_schema_exploration.md` | 7 KB | superseded richer-schema study; novel-dataset template |
| Challenges & strengths | `week1/reports/19_dataset_challenges_and_strengths.md` | 8 KB | consolidated flaws + strengths + novel-dataset design inputs |
| Interface note (→ Team B) | `week1/reports/11_qsnet_interface.md` | 8 KB | QS-Net data interface (**v1.0 unified** + v0.1) |
| Feature inventory (machine-readable) | `week1/reports/feature_inventory.csv` | 20 KB | deliverable ② companion |
| Static figures | `week1/reports/figures/` (30 PNG) | 2.3 MB | visualization dashboard (static) |
| Interactive dashboard | `week1/reports/dashboard.html` | 4.7 MB | visualization dashboard (interactive, offline) |
| **Manifest** | `week1/manifest/MANIFEST.md` + `manifest.json` | 150 KB | SHA-256 pins (raw + processed + qadcp + unified + **week2** incl. score interface + **baseline**; one manifest covers Weeks 1–3 — 665 files) |
| Scripts | `week1/scripts/*.py` | 150 KB | reproducibility (incl. `validate_pipeline.py`, `validate_unified.py`, `_unified.py`) |
| Schema | `week1/schema/*.json` | 4 KB | unified schema v1.0 + v1.1 (enriched appendix) |
| Requirements | `requirements.txt` (repo root) | 1 KB | Python 3.12 env |
| **Curated data (Day 3–7)** | `datasets/*/processed/*` + `datasets/*/qadcp/**` + **`datasets/*/unified/**`** | ~200 MB | v0.1 + **v1.0 unified** package |
| **Week-2 package** (Days 8–14) | `week2/README.md` + `week2/reports/w2_0{1..7}_*.md` + `week2/scripts/*.py` + `week2/tests/*.py` + `week2/partitions/<name>/*` + `week2/rq3/<name>/*` + `week2/baselines/<name>/*` + `week2/interface/**` + `week2/FROZEN/**` + `week2/{AK,OWAIS,IWO}_TASK*_HANDOFF.md` | ~150 MB | conformal partitions + split-integrity + RQ3 + classical baselines (XGBoost/IF/AE/OC-SVM, all 3 datasets) + 5-seed stats + leakage check + DATA FREEZE v1.0 + prototype-shaped score interface + leakage-controls note (index: `week2/README.md`) |
| **Week-3 conformal calibration** (Day 15) | `week3/README.md` + `week3/reports/w3_01_conformal_calibration.md` + `week3/scripts/conformal_calibrate.py` + `week3/tests/*.py` + `week3/AK_TASK15_HANDOFF.md` | ~1 MB | CQ-ZDR split-conformal calibration module + first threshold q (CIC) — consumes the Day-14 score interface (index: `week3/README.md`) |

## ❌ Do NOT upload
- **`datasets/*/raw/`** (~41 GB raw CSVs + zips) — **pinned by `manifest/MANIFEST.md`**; teammates
  download from the source URLs and run `make_manifest.py --verify` (0 mismatch = identical bytes).
  **Upload `datasets/*/processed/` + `datasets/*/qadcp/` + `datasets/*/unified/`** — never the raw.
- **`.venv/`**, **`__pycache__/`**, **`week1/*.log`**, **`week1/reports/_generated/`** — regeneratable
  intermediates / environment.

## Suggested Drive layout (`Team A / Week 1 /`)
```
README.md   UPLOAD.md   METADATA.md
reports/      00–19_*.md   feature_inventory.csv
schema/       unified_schema.json   unified_schema_v2.json
figures/      *.png
dashboard.html
manifest/     MANIFEST.md   manifest.json
scripts/      *.py   requirements.txt
datasets/     <name>/processed/   <name>/qadcp/   <name>/unified/
week2/        reports/w2_*.md   scripts/*.py   partitions/   rq3/   baselines/   interface/   FROZEN/   *_HANDOFF.md
week3/        README.md   reports/w3_*.md   scripts/*.py   tests/   AK_TASK15_HANDOFF.md
```

## One-command bundles (optional)
Two git-ignored zips — the Week-1 package + the Week-2 partitions:
```bash
cd qi26_12
zip -rq week1/QS-Net_TeamA_Week1_deliverables.zip \
  week1/README.md week1/UPLOAD.md week1/METADATA.md \
  week1/schema/*.json \
  week1/reports/*.md week1/reports/feature_inventory.csv \
  week1/reports/figures week1/reports/dashboard.html \
  week1/manifest/MANIFEST.md week1/manifest/manifest.json \
  week1/scripts/*.py requirements.txt \
  datasets/*/processed datasets/*/qadcp datasets/*/unified -x '*/.gitkeep' '*/__pycache__/*'
zip -rq week2/QS-Net_TeamA_Week2_partitions.zip \
  week2/README.md week2/reports/w2_*.md week2/*_HANDOFF.md week2/scripts/*.py week2/tests/*.py \
  week2/partitions week2/rq3 week2/baselines week2/interface week2/FROZEN \
  -x '*/__pycache__/*' '*/_generated/*' '*/ja/*'
zip -rq week3/QS-Net_TeamA_Week3_conformal.zip \
  week3/README.md week3/reports/w3_*.md week3/AK_TASK15_HANDOFF.md week3/scripts/*.py week3/tests/*.py \
  -x '*/__pycache__/*' '*/_generated/*' '*/ja/*'
```
