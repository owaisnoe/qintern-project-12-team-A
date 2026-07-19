#!/usr/bin/env python3
"""Week 2 Days 11-12: classical detector and zero-day novelty baselines.

Baseline systems
----------------
1. XGBoost known-class detector + Isolation Forest novelty head.
2. The same XGBoost detector + bottleneck autoencoder novelty head.

The shared detector makes the novelty-head comparison controlled. XGBoost is trained only on
``train.csv``. Each novelty head is fitted only on a class-capped subset of that same known-only
training split. ``calibration.csv`` selects each novelty threshold with the finite-sample conformal
quantile. ``test.csv`` and ``zeroday.csv`` are evaluation-only; zero-day rows never influence a fit,
hyperparameter, score normalization, or threshold.

Primary Day-12 metrics are multiclass Accuracy, F1-macro, macro one-vs-rest AUROC on known-only test
rows, and zero-day AUROC for known test versus the held-out class. Binary attack-detection and
thresholded novelty diagnostics are emitted alongside them.

Run from the project root:

    python week2/scripts/classical_baselines.py
    python week2/scripts/classical_baselines.py --datasets CICIoT2023 BoT-IoT UNSW-NB15
"""
from __future__ import annotations

import argparse
import json
import platform
import time
import warnings
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.ensemble import IsolationForest
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM
from xgboost import XGBClassifier

from baseline_metrics import (
    binary_metrics,
    conformal_novelty_threshold,
    multiclass_metrics,
    novelty_metrics,
    per_attack_zero_day_metrics,
)

BASE = Path(__file__).resolve().parents[2]
PARTITIONS = BASE / "week2" / "partitions"
OUTPUT = BASE / "week2" / "baselines"
GENERATED = BASE / "week2" / "reports" / "_generated"

SEED = 42
ALPHA = 0.10
DATASETS = ["CICIoT2023", "BoT-IoT", "UNSW-NB15"]
LABEL_COLUMNS = ["label_multiclass", "label_binary", "label_family"]


@dataclass(frozen=True)
class DatasetBundle:
    name: str
    features: list[str]
    train: pd.DataFrame
    calibration: pd.DataFrame
    test: pd.DataFrame
    zeroday: pd.DataFrame
    metadata: dict


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def feature_matrix(frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    return np.ascontiguousarray(frame[features].to_numpy(dtype=np.float32, copy=True))


def class_capped(
    frame: pd.DataFrame, cap: int, seed: int, *, label: str = "label_multiclass"
) -> pd.DataFrame:
    """Deterministically cap each known class while retaining every rare-class row."""
    if cap <= 0:
        return frame.reset_index(drop=True)
    groups = []
    for index, (_, group) in enumerate(frame.groupby(label, sort=True, observed=True)):
        if len(group) > cap:
            group = group.sample(n=cap, random_state=seed + index)
        groups.append(group)
    return pd.concat(groups, ignore_index=True).sample(frac=1.0, random_state=seed).reset_index(drop=True)


def load_bundle(name: str) -> DatasetBundle:
    directory = PARTITIONS / name
    metadata = json.loads((directory / "partition_meta.json").read_text(encoding="utf-8"))
    frames = {
        split: pd.read_csv(directory / f"{split}.csv")
        for split in ("train", "calibration", "test", "zeroday")
    }
    features = list(metadata["features"])
    expected = features + LABEL_COLUMNS

    for split, frame in frames.items():
        if list(frame.columns) != expected:
            raise ValueError(f"{name}/{split}: columns do not match partition_meta.json")
        matrix = frame[features].to_numpy(dtype=np.float64)
        if not np.isfinite(matrix).all():
            raise ValueError(f"{name}/{split}: feature matrix contains NaN or infinite values")
        if not set(frame["label_binary"].unique()).issubset({0, 1}):
            raise ValueError(f"{name}/{split}: label_binary must contain only 0 and 1")

    known = set(frames["train"]["label_multiclass"].unique())
    zero_day = set(frames["zeroday"]["label_multiclass"].unique())
    if not zero_day or not known.isdisjoint(zero_day):
        raise ValueError(f"{name}: zero-day classes are empty or leak into train")
    for split in ("calibration", "test"):
        if set(frames[split]["label_multiclass"].unique()) != known:
            raise ValueError(f"{name}/{split}: known-class membership differs from train")

    mapping_counts = frames["train"].groupby("label_multiclass")["label_binary"].nunique()
    if not (mapping_counts == 1).all():
        raise ValueError(f"{name}: a multiclass label maps to multiple binary labels")

    return DatasetBundle(name=name, features=features, metadata=metadata, **frames)


def detector_class_weights(labels: pd.Series) -> np.ndarray:
    """Tempered inverse-frequency weights for the highly imbalanced CIC class vocabulary."""
    counts = labels.value_counts()
    raw = labels.map(
        lambda value: np.sqrt(len(labels) / (len(counts) * counts[value]))
    ).to_numpy(dtype=float, copy=True)
    raw /= raw.mean()
    return np.clip(raw, 0.25, 20.0).astype(np.float32)


def fit_detector(bundle: DatasetBundle, args, seed: int) -> tuple[XGBClassifier, dict, dict[str, np.ndarray]]:
    fit_frame = class_capped(bundle.train, args.xgb_cap_per_class, seed)
    classes = sorted(bundle.metadata["known_classes"])
    class_to_index = {name: index for index, name in enumerate(classes)}
    y_fit = fit_frame["label_multiclass"].map(class_to_index).to_numpy(np.int32)
    weights = detector_class_weights(fit_frame["label_multiclass"])

    parameters = {
        "objective": "multi:softprob",
        "num_class": len(classes),
        "n_estimators": args.xgb_estimators,
        "max_depth": 6,
        "learning_rate": 0.10,
        "subsample": 0.90,
        "colsample_bytree": 0.90,
        "min_child_weight": 1.0,
        "reg_lambda": 1.0,
        "tree_method": "hist",
        "eval_metric": "mlogloss",
        "random_state": seed,
        "n_jobs": args.jobs,
        "verbosity": 0,
    }
    model = XGBClassifier(**parameters)
    started = time.perf_counter()
    model.fit(feature_matrix(fit_frame, bundle.features), y_fit, sample_weight=weights)
    log(f"  XGBoost fitted on {len(fit_frame):,} known rows in {time.perf_counter() - started:.1f}s")
    if list(model.classes_) != list(range(len(classes))):
        raise RuntimeError("XGBoost class index ordering does not match the persisted class map")

    probabilities = {
        split: model.predict_proba(feature_matrix(getattr(bundle, split), bundle.features))
        for split in ("calibration", "test", "zeroday")
    }
    test_prediction = np.asarray(classes)[np.argmax(probabilities["test"], axis=1)]
    multiclass = multiclass_metrics(
        bundle.test["label_multiclass"].to_numpy(),
        test_prediction,
        probabilities["test"],
        classes,
    )

    class_binary = (
        bundle.train.groupby("label_multiclass", sort=True)["label_binary"].first().to_dict()
    )
    attack_columns = [index for index, value in enumerate(classes) if int(class_binary[value]) == 1]
    if not attack_columns or len(attack_columns) == len(classes):
        raise ValueError(f"{bundle.name}: detector needs at least one benign and one attack class")
    attack_probability = probabilities["test"][:, attack_columns].sum(axis=1)
    binary = binary_metrics(bundle.test["label_binary"].to_numpy(), attack_probability)

    metrics = {
        "multiclass": multiclass,
        "binary_attack": binary,
        "fit_rows": int(len(fit_frame)),
        "classes": classes,
        "class_to_binary": {key: int(value) for key, value in class_binary.items()},
        "parameters": parameters,
    }
    outputs = {
        **probabilities,
        "test_prediction": test_prediction,
        "test_attack_probability": attack_probability,
        "zero_prediction": np.asarray(classes)[np.argmax(probabilities["zeroday"], axis=1)],
        "zero_attack_probability": probabilities["zeroday"][:, attack_columns].sum(axis=1),
    }
    return model, metrics, outputs


def score_isolation_forest(model: IsolationForest, frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    return -model.score_samples(feature_matrix(frame, features))


def fit_isolation_forest(bundle: DatasetBundle, args, seed: int) -> tuple[dict, dict[str, np.ndarray], IsolationForest]:
    fit_frame = class_capped(bundle.train, args.novelty_cap_per_class, seed)
    model = IsolationForest(
        n_estimators=args.iforest_estimators,
        max_samples=min(2048, len(fit_frame)),
        contamination="auto",
        n_jobs=args.jobs,
        random_state=seed,
    )
    started = time.perf_counter()
    model.fit(feature_matrix(fit_frame, bundle.features))
    log(f"  Isolation Forest fitted on {len(fit_frame):,} class-capped rows in {time.perf_counter() - started:.1f}s")

    scores = {
        split: score_isolation_forest(model, getattr(bundle, split), bundle.features)
        for split in ("calibration", "test", "zeroday")
    }
    threshold = conformal_novelty_threshold(scores["calibration"], args.alpha)
    metrics = novelty_metrics(scores["test"], scores["zeroday"], threshold)
    metrics.update({
        "fit_rows": int(len(fit_frame)),
        "calibration_rows": int(len(bundle.calibration)),
        "alpha": float(args.alpha),
        "parameters": {
            "n_estimators": args.iforest_estimators,
            "max_samples": min(2048, len(fit_frame)),
            "contamination": "auto",
        },
    })
    return metrics, scores, model


def autoencoder_scores(artifact: dict, frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    scaled = artifact["scaler"].transform(feature_matrix(frame, features))
    reconstructed = artifact["model"].predict(scaled)
    return np.mean(np.square(scaled - reconstructed), axis=1)


def fit_autoencoder(bundle: DatasetBundle, args, seed: int) -> tuple[dict, dict[str, np.ndarray], dict]:
    fit_frame = class_capped(bundle.train, args.novelty_cap_per_class, seed)
    matrix = feature_matrix(fit_frame, bundle.features)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(matrix)
    model = MLPRegressor(
        hidden_layer_sizes=(12, 6, 12),
        activation="relu",
        solver="adam",
        alpha=1e-4,
        batch_size=min(512, max(1, int(len(fit_frame) * 0.8))),
        learning_rate_init=1e-3,
        max_iter=args.ae_max_iter,
        shuffle=True,
        random_state=seed,
        early_stopping=True,
        validation_fraction=0.10,
        n_iter_no_change=8,
        tol=1e-4,
    )
    started = time.perf_counter()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model.fit(scaled, scaled)
    log(f"  Autoencoder fitted on {len(fit_frame):,} class-capped rows in {time.perf_counter() - started:.1f}s")

    artifact = {"scaler": scaler, "model": model}
    scores = {
        split: autoencoder_scores(artifact, getattr(bundle, split), bundle.features)
        for split in ("calibration", "test", "zeroday")
    }
    threshold = conformal_novelty_threshold(scores["calibration"], args.alpha)
    metrics = novelty_metrics(scores["test"], scores["zeroday"], threshold)
    metrics.update({
        "fit_rows": int(len(fit_frame)),
        "calibration_rows": int(len(bundle.calibration)),
        "alpha": float(args.alpha),
        "training_iterations": int(model.n_iter_),
        "final_loss": float(model.loss_),
        "parameters": {
            "hidden_layer_sizes": [12, 6, 12],
            "activation": "relu",
            "solver": "adam",
            "max_iter": args.ae_max_iter,
            "early_stopping": True,
        },
    })
    return metrics, scores, artifact


def ocsvm_scores(artifact: dict, frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    scaled = artifact["scaler"].transform(feature_matrix(frame, features))
    # decision_function is positive for inliers; negate so larger means more novel.
    return -artifact["model"].decision_function(scaled)


def fit_ocsvm(bundle: DatasetBundle, args, seed: int) -> tuple[dict, dict[str, np.ndarray], dict]:
    """RBF One-Class SVM novelty head.

    OC-SVM training is O(n^2) in the fit rows, so the class-capped known-only subset is further
    capped deterministically at ``args.ocsvm_cap`` before the kernel fit. Features are standardized
    with train-fitted parameters because the RBF kernel is scale-sensitive.
    """
    fit_frame = class_capped(bundle.train, args.novelty_cap_per_class, seed)
    if len(fit_frame) > args.ocsvm_cap:
        fit_frame = fit_frame.sample(n=args.ocsvm_cap, random_state=seed).reset_index(drop=True)
    matrix = feature_matrix(fit_frame, bundle.features)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(matrix)
    model = OneClassSVM(kernel="rbf", gamma="scale", nu=args.ocsvm_nu)
    started = time.perf_counter()
    model.fit(scaled)
    log(f"  One-Class SVM fitted on {len(fit_frame):,} class-capped rows in {time.perf_counter() - started:.1f}s")

    artifact = {"scaler": scaler, "model": model}
    scores = {
        split: ocsvm_scores(artifact, getattr(bundle, split), bundle.features)
        for split in ("calibration", "test", "zeroday")
    }
    threshold = conformal_novelty_threshold(scores["calibration"], args.alpha)
    metrics = novelty_metrics(scores["test"], scores["zeroday"], threshold)
    metrics.update({
        "fit_rows": int(len(fit_frame)),
        "calibration_rows": int(len(bundle.calibration)),
        "alpha": float(args.alpha),
        "parameters": {
            "kernel": "rbf",
            "gamma": "scale",
            "nu": float(args.ocsvm_nu),
            "ocsvm_cap": int(args.ocsvm_cap),
        },
    })
    return metrics, scores, artifact


def save_predictions(
    bundle: DatasetBundle,
    detector_outputs: dict[str, np.ndarray],
    head_scores: dict[str, dict[str, np.ndarray]],
    head_metrics: dict[str, dict],
    output_dir: Path,
) -> None:
    pieces = []
    for split, frame, predicted_key, attack_key in (
        ("test", bundle.test, "test_prediction", "test_attack_probability"),
        ("zeroday", bundle.zeroday, "zero_prediction", "zero_attack_probability"),
    ):
        result = pd.DataFrame({
            "split": split,
            "row_index": np.arange(len(frame), dtype=np.int64),
            "true_label_multiclass": frame["label_multiclass"].to_numpy(),
            "true_label_binary": frame["label_binary"].to_numpy(),
            "xgboost_prediction": detector_outputs[predicted_key],
            "xgboost_attack_probability": detector_outputs[attack_key],
        })
        for head_name, scores in head_scores.items():
            result[f"{head_name}_novelty_score"] = scores[split]
            result[f"{head_name}_is_novel"] = scores[split] > head_metrics[head_name]["threshold"]
        pieces.append(result)
    # Preserve model scores when the CSV is reloaded for an independent audit.
    pd.concat(pieces, ignore_index=True).to_csv(
        output_dir / "predictions.csv", index=False, float_format="%.17g"
    )


def run_dataset(name: str, args, seed: int | None = None, save: bool = True) -> dict:
    seed = SEED if seed is None else int(seed)
    log(f"{name}: loading and validating four Week-2 splits (seed={seed})")
    bundle = load_bundle(name)
    output_dir = OUTPUT / name

    detector, detector_metrics, detector_outputs = fit_detector(bundle, args, seed)
    if_metrics, if_scores, if_model = fit_isolation_forest(bundle, args, seed)
    ae_metrics, ae_scores, ae_artifact = fit_autoencoder(bundle, args, seed)
    oc_metrics, oc_scores, oc_artifact = fit_ocsvm(bundle, args, seed)
    head_scores = {
        "isolation_forest": if_scores,
        "autoencoder": ae_scores,
        "ocsvm": oc_scores,
    }
    heads = {"isolation_forest": if_metrics, "autoencoder": ae_metrics, "ocsvm": oc_metrics}

    # Per-held-out-attack zero-day breakdown for every novelty head (Day-13 addition).
    zero_day_families = bundle.zeroday["label_multiclass"].to_numpy()
    for head_name, metrics in heads.items():
        metrics["per_attack_zero_day"] = per_attack_zero_day_metrics(
            head_scores[head_name]["test"],
            head_scores[head_name]["zeroday"],
            zero_day_families,
            metrics["threshold"],
        )

    if save:
        output_dir.mkdir(parents=True, exist_ok=True)
        if not args.no_save_models:
            detector.save_model(output_dir / "xgboost_detector.json")
            joblib.dump(if_model, output_dir / "isolation_forest.joblib", compress=3)
            joblib.dump(ae_artifact, output_dir / "autoencoder.joblib", compress=3)
            joblib.dump(oc_artifact, output_dir / "ocsvm.joblib", compress=3)
        save_predictions(bundle, detector_outputs, head_scores, heads, output_dir)

    result = {
        "schema_version": "1.1",
        "dataset": name,
        "seed": seed,
        "n_jobs": int(args.jobs),
        "alpha": float(args.alpha),
        "features": bundle.features,
        "row_counts": {split: int(len(getattr(bundle, split))) for split in ("train", "calibration", "test", "zeroday")},
        "known_classes": sorted(bundle.metadata["known_classes"]),
        "zero_day_classes": sorted(bundle.metadata["zero_day_families"]),
        "evaluation_contract": {
            "detector_fit": "train only (known classes)",
            "novelty_fit": "class-capped train only (known classes)",
            "threshold_selection": "known-only calibration, finite-sample conformal quantile",
            "closed_set_evaluation": "known-only test",
            "zero_day_evaluation": "known test (0) vs held-out zeroday (1)",
            "zero_day_used_for_fitting_or_tuning": False,
            "novelty_score_direction": "higher means more novel",
        },
        "detector": detector_metrics,
        "novelty_heads": heads,
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "xgboost": xgboost.__version__,
        },
    }
    if save:
        (output_dir / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    log(
        f"  results: closed F1={detector_metrics['multiclass']['f1_macro']:.4f}; "
        f"zero-day AUROC IF={if_metrics['zero_day_auroc']:.4f}, "
        f"AE={ae_metrics['zero_day_auroc']:.4f}, OC-SVM={oc_metrics['zero_day_auroc']:.4f}"
    )
    return result


HEAD_LABELS = {
    "isolation_forest": "XGBoost + Isolation Forest",
    "autoencoder": "XGBoost + Autoencoder",
    "ocsvm": "XGBoost + One-Class SVM",
}


def summary_rows(results: dict[str, dict]) -> list[dict]:
    rows = []
    for dataset, result in results.items():
        multiclass = result["detector"]["multiclass"]
        binary = result["detector"]["binary_attack"]
        for head_name, head in result["novelty_heads"].items():
            rows.append({
                "dataset": dataset,
                "baseline": HEAD_LABELS.get(head_name, f"XGBoost + {head_name}"),
                "novelty_head": head_name,
                "accuracy": multiclass["accuracy"],
                "balanced_accuracy": multiclass["balanced_accuracy"],
                "f1_macro": multiclass["f1_macro"],
                "auroc_ovr_macro": multiclass["auroc_ovr_macro"],
                "auprc_ovr_macro": multiclass["auprc_ovr_macro"],
                "zero_day_auroc": head["zero_day_auroc"],
                "zero_day_auprc": head["zero_day_auprc"],
                "binary_accuracy": binary["accuracy"],
                "binary_f1_macro": binary["f1_macro"],
                "binary_auroc": binary["auroc"],
                "novelty_accuracy": head["accuracy"],
                "novelty_balanced_accuracy": head["balanced_accuracy"],
                "novelty_f1_macro": head["f1_macro"],
                "known_false_positive_rate": head["known_false_positive_rate"],
                "zero_day_true_positive_rate": head["zero_day_true_positive_rate"],
                "fpr_at_95_tpr": head["fpr_at_95_tpr"],
                "alpha": result["alpha"],
                "seed": result["seed"],
            })
    return rows


def write_summaries(results: dict[str, dict]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "baseline_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    pd.DataFrame(summary_rows(results)).to_csv(GENERATED / "baseline_results.csv", index=False)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", nargs="+", choices=DATASETS, default=[DATASETS[0]])
    parser.add_argument("--seed", type=int, default=SEED, help="Base seed for detector, heads, and subsampling")
    parser.add_argument("--alpha", type=float, default=ALPHA, help="Known-class novelty false-positive target")
    parser.add_argument("--xgb-estimators", type=int, default=120)
    parser.add_argument("--iforest-estimators", type=int, default=300)
    parser.add_argument("--ae-max-iter", type=int, default=80)
    parser.add_argument("--xgb-cap-per-class", type=int, default=0, help="0 uses all detector training rows")
    parser.add_argument("--novelty-cap-per-class", type=int, default=2000)
    parser.add_argument("--ocsvm-cap", type=int, default=6000, help="Hard cap on OC-SVM fit rows (O(n^2) kernel)")
    parser.add_argument("--ocsvm-nu", type=float, default=0.10, help="OC-SVM support-vector / outlier upper bound")
    parser.add_argument("--jobs", type=int, default=-1, help="Thread count; use 1 for machine-stable results")
    parser.add_argument("--no-save-models", action="store_true")
    parser.add_argument("--no-summary", action="store_true", help="Skip writing the shared baseline_results summary")
    args = parser.parse_args()
    if not 0.0 < args.alpha < 1.0:
        parser.error("--alpha must be strictly between 0 and 1")
    if not 0.0 < args.ocsvm_nu <= 1.0:
        parser.error("--ocsvm-nu must be in (0, 1]")
    for name in ("xgb_estimators", "iforest_estimators", "ae_max_iter", "novelty_cap_per_class", "ocsvm_cap"):
        if getattr(args, name) <= 0:
            parser.error(f"--{name.replace('_', '-')} must be positive")
    return args


def main() -> None:
    args = parse_args()
    log(f"Week-2 classical baselines | seed={args.seed}, alpha={args.alpha}, jobs={args.jobs}")
    results = {name: run_dataset(name, args, seed=args.seed) for name in args.datasets}
    if not args.no_summary:
        write_summaries(results)
    log("done -> week2/baselines/<dataset>/ + week2/reports/_generated/baseline_results.{csv,json}")


if __name__ == "__main__":
    main()
