#!/usr/bin/env python3
"""Week 2 Day 13: multi-seed statistics harness for the classical baselines.

The Day-11/12 single-run numbers are machine dependent: XGBoost ``hist`` training is not
bit-identical across machines or thread counts, so a lone seed-42 macro-F1 cannot be the
final bar. This harness re-runs the whole baseline stack (XGBoost detector + Isolation Forest,
Autoencoder, and One-Class SVM novelty heads) across a fixed seed set with ``n_jobs=1`` and
reports mean, sample standard deviation, and a t-based 95% confidence interval for every
headline metric on all three mentor-locked datasets (CIC-IoT2023, BoT-IoT, UNSW-NB15). These
aggregate statistics supersede either single-run number.

Determinism contract
--------------------
* ``n_jobs=1`` removes XGBoost/sklearn thread-scheduling nondeterminism, so each (dataset, seed)
  pair is reproducible on a fixed package set.
* Only the base seed varies across runs; the detector, every novelty head, and every
  class-capped subsample are reseeded from it, so the spread measures genuine seed sensitivity.
* Nothing here is fit or tuned on ``test``/``zeroday`` rows; the harness only re-invokes the
  audited ``run_dataset`` in memory (``save=False``) and never overwrites the canonical
  seed-42 artifacts under ``week2/baselines/``.

Outputs (``week2/reports/_generated/``):
* ``stats_harness.json``  — full mean/std/CI tree plus per-seed values.
* ``stats_harness.csv``   — one flat row per (dataset, head, metric).
* ``day13_all_datasets.json`` / ``.csv`` — the seed-42 slice, i.e. the all-dataset single-run
  table with the Day-13 metric additions (AUPRC, balanced accuracy, per-attack zero-day).

Run from the project root (``Team A``) with the pinned Python 3.12 venv::

    ../.venv/bin/python week2/scripts/stats_harness.py
    ../.venv/bin/python week2/scripts/stats_harness.py --seeds 42 43 44 45 46 --datasets CICIoT2023 BoT-IoT UNSW-NB15
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import sklearn
import xgboost
from scipy import stats

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from classical_baselines import DATASETS, run_dataset  # noqa: E402

BASE = Path(__file__).resolve().parents[2]
GENERATED = BASE / "week2" / "reports" / "_generated"

DEFAULT_SEEDS = [42, 43, 44, 45, 46]
CANONICAL_SEED = 42

# Metrics aggregated per dataset. (result-path tuple -> output label)
DETECTOR_METRICS = {
    "accuracy": ("detector", "multiclass", "accuracy"),
    "balanced_accuracy": ("detector", "multiclass", "balanced_accuracy"),
    "f1_macro": ("detector", "multiclass", "f1_macro"),
    "auroc_ovr_macro": ("detector", "multiclass", "auroc_ovr_macro"),
    "auprc_ovr_macro": ("detector", "multiclass", "auprc_ovr_macro"),
    "binary_accuracy": ("detector", "binary_attack", "accuracy"),
    "binary_f1_macro": ("detector", "binary_attack", "f1_macro"),
    "binary_auroc": ("detector", "binary_attack", "auroc"),
}
HEAD_METRICS = [
    "zero_day_auroc",
    "zero_day_auprc",
    "fpr_at_95_tpr",
    "known_false_positive_rate",
    "zero_day_true_positive_rate",
    "balanced_accuracy",
]
HEADS = ["isolation_forest", "autoencoder", "ocsvm"]


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def dig(result: dict, path: tuple[str, ...]) -> float:
    node = result
    for key in path:
        node = node[key]
    return float(node)


def mean_std_ci(values: list[float], confidence: float = 0.95) -> dict:
    """Sample mean, std (ddof=1), and a two-sided t confidence interval."""
    array = np.asarray(values, dtype=np.float64)
    n = int(array.size)
    mean = float(array.mean())
    if n > 1:
        std = float(array.std(ddof=1))
        half_width = float(stats.t.ppf(0.5 + confidence / 2.0, n - 1) * std / np.sqrt(n))
    else:
        std = 0.0
        half_width = 0.0
    return {
        "mean": mean,
        "std": std,
        "ci95_low": mean - half_width,
        "ci95_high": mean + half_width,
        "ci95_half_width": half_width,
        "n": n,
        "values": [float(v) for v in array.tolist()],
    }


def harness_args(base) -> SimpleNamespace:
    """Baseline runner configuration shared by every seed (thread-count pinned to n_jobs)."""
    return SimpleNamespace(
        alpha=base.alpha,
        xgb_estimators=base.xgb_estimators,
        iforest_estimators=base.iforest_estimators,
        ae_max_iter=base.ae_max_iter,
        xgb_cap_per_class=0,
        novelty_cap_per_class=base.novelty_cap_per_class,
        ocsvm_cap=base.ocsvm_cap,
        ocsvm_nu=base.ocsvm_nu,
        jobs=base.jobs,
        no_save_models=True,
        no_summary=True,
    )


def aggregate(dataset: str, per_seed: list[dict]) -> dict:
    detector = {
        label: mean_std_ci([dig(result, path) for result in per_seed])
        for label, path in DETECTOR_METRICS.items()
    }
    heads = {}
    for head in HEADS:
        heads[head] = {
            metric: mean_std_ci([float(result["novelty_heads"][head][metric]) for result in per_seed])
            for metric in HEAD_METRICS
        }
    # Per-held-out-attack zero-day AUROC, aggregated across seeds per family and head.
    per_attack = {}
    for head in HEADS:
        families = sorted(per_seed[0]["novelty_heads"][head]["per_attack_zero_day"].keys())
        per_attack[head] = {
            family: {
                "zero_day_auroc": mean_std_ci(
                    [float(r["novelty_heads"][head]["per_attack_zero_day"][family]["zero_day_auroc"]) for r in per_seed]
                ),
                "zero_day_auprc": mean_std_ci(
                    [float(r["novelty_heads"][head]["per_attack_zero_day"][family]["zero_day_auprc"]) for r in per_seed]
                ),
                "detection_rate_at_threshold": mean_std_ci(
                    [float(r["novelty_heads"][head]["per_attack_zero_day"][family]["detection_rate_at_threshold"]) for r in per_seed]
                ),
                "zero_day_rows": int(per_seed[0]["novelty_heads"][head]["per_attack_zero_day"][family]["zero_day_rows"]),
            }
            for family in families
        }
    return {
        "dataset": dataset,
        "row_counts": per_seed[0]["row_counts"],
        "known_classes": per_seed[0]["known_classes"],
        "zero_day_classes": per_seed[0]["zero_day_classes"],
        "detector": detector,
        "novelty_heads": heads,
        "per_attack_zero_day": per_attack,
    }


def flat_rows(aggregated: dict[str, dict], seeds: list[int]) -> list[dict]:
    rows: list[dict] = []
    for dataset, agg in aggregated.items():
        for metric, stat in agg["detector"].items():
            rows.append({"dataset": dataset, "group": "detector", "head": "", "metric": metric, **_stat_cols(stat)})
        for head, metrics in agg["novelty_heads"].items():
            for metric, stat in metrics.items():
                rows.append({"dataset": dataset, "group": "novelty_head", "head": head, "metric": metric, **_stat_cols(stat)})
        for head, families in agg["per_attack_zero_day"].items():
            for family, entries in families.items():
                stat = entries["zero_day_auroc"]
                rows.append({
                    "dataset": dataset, "group": "per_attack_zero_day", "head": head,
                    "metric": f"zero_day_auroc[{family}]", **_stat_cols(stat),
                })
    return rows


def _stat_cols(stat: dict) -> dict:
    return {
        "mean": stat["mean"],
        "std": stat["std"],
        "ci95_low": stat["ci95_low"],
        "ci95_high": stat["ci95_high"],
        "n": stat["n"],
    }


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", nargs="+", choices=DATASETS, default=list(DATASETS))
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS)
    parser.add_argument("--alpha", type=float, default=0.10)
    parser.add_argument("--xgb-estimators", type=int, default=120)
    parser.add_argument("--iforest-estimators", type=int, default=300)
    parser.add_argument("--ae-max-iter", type=int, default=80)
    parser.add_argument("--novelty-cap-per-class", type=int, default=2000)
    parser.add_argument("--ocsvm-cap", type=int, default=6000)
    parser.add_argument("--ocsvm-nu", type=float, default=0.10)
    parser.add_argument("--jobs", type=int, default=1, help="Pin to 1 for machine-stable statistics")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runner_args = harness_args(args)
    environment = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "xgboost": xgboost.__version__,
    }
    log(f"Day-13 stats harness | seeds={args.seeds}, jobs={args.jobs}, datasets={args.datasets}")

    aggregated: dict[str, dict] = {}
    seed42_results: dict[str, dict] = {}
    for dataset in args.datasets:
        per_seed = []
        for seed in args.seeds:
            result = run_dataset(dataset, runner_args, seed=seed, save=False)
            per_seed.append(result)
            if seed == CANONICAL_SEED:
                seed42_results[dataset] = result
        aggregated[dataset] = aggregate(dataset, per_seed)
        f1 = aggregated[dataset]["detector"]["f1_macro"]
        log(f"  {dataset}: closed F1 = {f1['mean']:.4f} +/- {f1['std']:.4f} "
            f"(95% CI [{f1['ci95_low']:.4f}, {f1['ci95_high']:.4f}], n={f1['n']})")

    GENERATED.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "description": "Day-13 multi-seed baseline statistics (mean, std, 95% CI).",
        "seeds": args.seeds,
        "n_jobs": args.jobs,
        "alpha": args.alpha,
        "supersedes": "single-run seed-42 macro-F1 (machine-dependent XGBoost hist training)",
        "environment": environment,
        "datasets": aggregated,
    }
    (GENERATED / "stats_harness.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pd.DataFrame(flat_rows(aggregated, args.seeds)).to_csv(GENERATED / "stats_harness.csv", index=False)

    # Seed-42 slice = the all-dataset single-run table with the Day-13 metric additions.
    if seed42_results:
        from classical_baselines import summary_rows

        (GENERATED / "day13_all_datasets.json").write_text(
            json.dumps({"seed": CANONICAL_SEED, "n_jobs": args.jobs, "environment": environment,
                        "datasets": seed42_results}, indent=2),
            encoding="utf-8",
        )
        pd.DataFrame(summary_rows(seed42_results)).to_csv(
            GENERATED / "day13_all_datasets.csv", index=False
        )

    log("done -> week2/reports/_generated/{stats_harness.json,stats_harness.csv,"
        "day13_all_datasets.json,day13_all_datasets.csv}")


if __name__ == "__main__":
    main()
