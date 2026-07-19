# Team A → Team C — Feature Selection Data Interface

**QS-Net / QuantumSentinel** · Week 1 · Team A (dataset curation) → Team C (feature selection).

Team C's Week 1 task: implement MI, RF importance, BPSO, QPSO; benchmark and deliver optimized
feature subsets for Team B's quantum models.

## What Team A provides

| Item | Location | Purpose |
|------|----------|---------|
| Feature catalogue | [`feature_inventory.csv`](feature_inventory.csv) + [`02_feature_inventory.md`](02_feature_inventory.md) | per-dataset column inventory, drops, semantic mapping |
| Clean scaled features (v0.1) | `datasets/<name>/qadcp/train.parquet` | **primary input** for per-dataset selection (dataset-native columns) |
| Unified features (v1.0) | `datasets/<name>/unified/qadcp/train.parquet` | cross-dataset selection on 17 shared columns |
| Semantic groups | `datasets/<name>/qadcp/feature_groups.json` | timing / rate / volume / flags_state / protocol / connection_ctx |
| Baseline ranking (beat this) | `datasets/<name>/qadcp/qubit_budgets.json` | S6b univariate \|Pearson r\| vs `label_binary` on train |
| Encoder A/B reference | [`10_pca_baseline.md`](10_pca_baseline.md) | ranked-8 vs PCA-8 on 8-qubit budget |
| Zero-day tiers | `datasets/<name>/qadcp/zero_day_tiers.json` | Easy/Medium/Hard holdout difficulty |

## Labels for supervised selection

| Label column | Use when |
|--------------|----------|
| `label_binary` | attack vs benign detection (matches S6b baseline ranking) |
| `label_multiclass` | per-attack-type selection (finer granularity) |
| `label_family` | cross-dataset 10-family ontology |

**Do not use `zeroday` split for fitting selectors** — it contains held-out families excluded from training.

## Leakage rules (mandatory)

1. **Fit selectors on `train` only** — never val/calibration/test/zeroday
2. Use `val` for hyperparameter tuning of selection algorithms only
3. All scalers/encoders in QADCP were train-fit — do not re-fit on full dataset
4. Report selected feature count vs qubit budget (4/8/12/16)

## Recommended starting point

**Dataset:** CIC-IoT2023 (largest known-class train set, Hard-tier zero-day Mirai)

```python
import pandas as pd
import json

name = "CICIoT2023"
train = pd.read_parquet(f"datasets/{name}/qadcp/train.parquet")
labels = ["label_multiclass", "label_binary", "label_family"]
X = train.drop(columns=labels)
y_bin = train["label_binary"]
y_mc = train["label_multiclass"]

groups = json.loads(open(f"datasets/{name}/qadcp/feature_groups.json").read())
budgets = json.loads(open(f"datasets/{name}/qadcp/qubit_budgets.json").read())
baseline_ranking = budgets["ranking"]           # S6b baseline to beat
top8_baseline = budgets["budgets"]["8"]         # current ranked-8 feature names
```

## How your output plugs into QADCP

Team C's selected features replace the S6b ranking in `qubit_budgets.json`:

1. Run selection on `train.parquet` features
2. Output ranked feature list (top 4/8/12/16)
3. Team B uses your list for angle encoding instead of the baseline `qubit_budgets.json` ranking
4. Compare downstream QML accuracy: **your selection vs S6b vs PCA-8** ([`10_pca_baseline.md`](10_pca_baseline.md))

## v0.1 vs v1.0 — which to use?

| Goal | Package |
|------|---------|
| Richest per-dataset features (16–38 cols) | **v0.1** `qadcp/train.parquet` |
| Cross-dataset comparable features (17 cols) | **v1.0** `unified/qadcp/train.parquet` |
| Feature inventory / semantic groups | v0.1 (full column names) |

For Week 1 benchmarking, start with **v0.1 CIC-IoT2023** (30 features after corr prune).
Use v1.0 when comparing selection stability across datasets.

## Feature counts per dataset (v0.1 train)

| Dataset | Features | Train rows | Classes (train) |
|---------|--------:|-----------:|----------------:|
| CICIoT2023 | 30 | 132,166 | 31 |
| TON_IoT | 22 | 62,215 | 9 |
| BoT-IoT | 16 | 130,205 | 4 |
| Edge-IIoTset | 38 | 89,971 | 13 |
| UNSW-NB15 | 38 | 84,730 | 8 |

## Concerns

- **S6b baseline is univariate** — ignores feature interactions; your MI/BPSO/QPSO should beat it
- **High correlation pairs** already pruned at \|r\|≥0.95 in QADCP — do not re-introduce redundant pairs
- **Ordinal encoding in v0.1** — Day-3 categoricals are ordinal; v1.0 unified uses frequency encoding
- **Checkpoint scale** — ~200k row caps; selection stability on full raw scale unverified

## Reproduce QADCP outputs Team C depends on

```bash
cd "Team A" && source ../.venv/bin/activate
python week1/scripts/preprocess.py
python week1/scripts/qadcp.py
python week1/scripts/pca_baseline.py
```

Full handover: [`14_handover_report.md`](14_handover_report.md) · Team B interface: [`11_qsnet_interface.md`](11_qsnet_interface.md)
