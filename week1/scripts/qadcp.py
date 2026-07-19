"""QADCP — Quantum-Aware Dataset Curation Pipeline (Day 4 + Day 6 unified mode).

Run:
  python week1/scripts/qadcp.py
  python week1/scripts/qadcp.py --unified
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from _unified import CAT_COLS, frequency_encode, load_schema

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "datasets"
GEN = BASE / "week1" / "reports" / "_generated"

SEED = 42
SPLIT_FRACS = {"train": 0.70, "val": 0.10, "calibration": 0.10, "test": 0.10}
CORR_PRUNE = 0.95
QUBIT_BUDGETS = [4, 8, 12, 16]
MAX_PER_CLASS = 20_000
LABELS = ["label_multiclass", "label_binary", "label_family"]
DATASET_DIRS = ["CICIoT2023", "TON_IoT", "BoT-IoT", "Edge-IIoTset", "UNSW-NB15"]

FAMILY_PREFIX = {
    "CICIoT2023": [
        ("BenignTraffic", "benign"), ("DDoS-", "ddos"), ("DoS-", "dos"),
        ("Mirai-", "botnet_mirai"), ("Recon-", "recon"), ("VulnerabilityScan", "recon"),
        ("MITM-", "spoofing_mitm"), ("DNS_Spoofing", "spoofing_mitm"),
        ("SqlInjection", "web_injection"), ("CommandInjection", "web_injection"),
        ("XSS", "web_injection"), ("BrowserHijacking", "web_injection"),
        ("Uploading_Attack", "web_injection"), ("DictionaryBruteForce", "bruteforce_password"),
        ("Backdoor_Malware", "backdoor_malware_ransomware"),
    ],
    "TON_IoT": [
        ("normal", "benign"), ("ddos", "ddos"), ("dos", "dos"), ("scanning", "recon"),
        ("mitm", "spoofing_mitm"), ("injection", "web_injection"), ("xss", "web_injection"),
        ("password", "bruteforce_password"), ("backdoor", "backdoor_malware_ransomware"),
        ("ransomware", "backdoor_malware_ransomware"),
    ],
    "BoT-IoT": [
        ("Normal", "benign"), ("DDoS", "ddos"), ("DoS", "dos"),
        ("Reconnaissance", "recon"), ("Theft", "theft_exfiltration"),
    ],
    "Edge-IIoTset": [
        ("Normal", "benign"), ("DDoS_", "ddos"),
        ("Port_Scanning", "recon"), ("Vulnerability_scanner", "recon"), ("Fingerprinting", "recon"),
        ("MITM", "spoofing_mitm"), ("SQL_injection", "web_injection"), ("XSS", "web_injection"),
        ("Uploading", "web_injection"), ("Password", "bruteforce_password"),
        ("Backdoor", "backdoor_malware_ransomware"), ("Ransomware", "backdoor_malware_ransomware"),
    ],
    "UNSW-NB15": [
        ("Normal", "benign"), ("DoS", "dos"), ("Reconnaissance", "recon"),
        ("Backdoor", "backdoor_malware_ransomware"), ("Generic", "generic"),
        ("Exploits", "exploits"), ("Fuzzers", "fuzzers"), ("Shellcode", "shellcode"),
        ("Worms", "worms"), ("Analysis", "analysis"),
    ],
}

ZERO_DAY = {
    "CICIoT2023": ["Mirai-"],
    "TON_IoT": ["ransomware"],
    "BoT-IoT": ["Theft"],
    "Edge-IIoTset": ["Ransomware", "Fingerprinting"],
    "UNSW-NB15": ["Worms", "Shellcode"],
}

GROUP_RULES = [
    ("timing", ["duration", "dur", "iat", "jit", "time", "pkt_size"]),
    ("rate", ["rate", "srate", "drate", "load", "sload", "dload", "rate_src", "rate_dst"]),
    ("volume", ["byte", "pkt", "n_pkts", "n_bytes", "src_pkts", "dst_pkts", "src_bytes", "dst_bytes"]),
    ("flags_state", ["conn_state", "protocol", "flag", "flgs", "state"]),
    ("protocol", ["proto", "service", "http", "https", "dns", "tcp", "udp", "mqtt", "arp", "icmp"]),
    ("connection_ctx", ["ct_"]),
]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def family_of(label: str, dataset: str) -> str:
    for prefix, fam in FAMILY_PREFIX[dataset]:
        if label.startswith(prefix):
            return fam
    return "other"


def group_of(col: str) -> str:
    c = col.lower()
    for group, keys in GROUP_RULES:
        if any(k in c for k in keys):
            return group
    return "other"


def stratified_split(df: pd.DataFrame, rng: np.random.Generator) -> pd.Series:
    assign = pd.Series(index=df.index, dtype=object)
    for _, idx in df.groupby("label_multiclass", sort=False).groups.items():
        idx = np.asarray(list(idx))
        rng.shuffle(idx)
        n = len(idx)
        if n >= 10:
            n_val = int(round(SPLIT_FRACS["val"] * n))
            n_cal = int(round(SPLIT_FRACS["calibration"] * n))
            n_test = int(round(SPLIT_FRACS["test"] * n))
        elif n >= 4:
            n_val = n_cal = n_test = 1
        else:
            n_val = n_cal = n_test = 0
        assign.loc[idx[:n_val]] = "val"
        assign.loc[idx[n_val:n_val + n_cal]] = "calibration"
        assign.loc[idx[n_val + n_cal:n_val + n_cal + n_test]] = "test"
        assign.loc[idx[n_val + n_cal + n_test:]] = "train"
    return assign


def corr_prune(train_feats: pd.DataFrame, thresh: float) -> tuple[list[str], list[dict]]:
    corr = train_feats.corr().abs()
    cols = list(corr.columns)
    drop, pairs = set(), []
    for i in range(len(cols)):
        if cols[i] in drop:
            continue
        for j in range(i + 1, len(cols)):
            if cols[j] in drop:
                continue
            r = corr.iloc[i, j]
            if pd.notna(r) and r >= thresh:
                drop.add(cols[j])
                pairs.append({"kept": cols[i], "dropped": cols[j], "r": round(float(r), 4)})
    return sorted(drop), pairs


def apply_unified_encoding(splits: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], dict]:
    encoders: dict = {"fit_on": "train split only", "frequency": {}, "impute_medians": {}}

    for cat, out_col in [("protocol_cat", "protocol"), ("conn_state_cat", "conn_state")]:
        if cat not in splits["train"].columns:
            continue
        ref = splits["train"][cat]
        _, freq_map = frequency_encode(ref, ref)
        encoders["frequency"][out_col] = freq_map
        for s in splits:
            if len(splits[s]) and cat in splits[s].columns:
                splits[s][out_col], _ = frequency_encode(ref, splits[s][cat])
                splits[s] = splits[s].drop(columns=[cat])

    numeric = [c for c in splits["train"].columns if c not in LABELS and c not in CAT_COLS]
    for c in numeric:
        med = float(splits["train"][c].median()) if splits["train"][c].notna().any() else 0.0
        encoders["impute_medians"][c] = med
        for s in splits:
            if len(splits[s]) and c in splits[s].columns:
                splits[s][c] = splits[s][c].fillna(med)

    return splits, encoders


def process_dataframe(df: pd.DataFrame, name: str, out: Path, checkpoint: str,
                      unified: bool = False) -> dict:
    rng = np.random.default_rng(SEED)
    out.mkdir(parents=True, exist_ok=True)
    (out / "quantum").mkdir(parents=True, exist_ok=True)
    report: dict = {
        "dataset": name, "seed": SEED, "checkpoint": checkpoint,
        "mode": "unified" if unified else "v0.1",
    }

    df = df.copy()
    if not unified:
        feats_chk = [c for c in df.columns if c not in ("label_multiclass", "label_binary")]
        assert int(df[feats_chk].isna().sum().sum()) == 0, "S0: NaN in checkpoint"
        assert not df.duplicated(subset=feats_chk).any(), "S0: duplicate feature rows"
    report["s0_validate"] = {"rows": len(df), "gates": "pass"}

    df["label_family"] = df["label_multiclass"].astype(str).map(lambda s: family_of(s, name))
    unmapped = sorted(df.loc[df["label_family"] == "other", "label_multiclass"].unique())
    assert not unmapped, f"S2: unmapped labels {unmapped}"
    report["s2_engineer"] = {"families": df["label_family"].value_counts().to_dict()}

    zd_mask = df["label_multiclass"].astype(str).str.startswith(tuple(ZERO_DAY[name]))
    zeroday, rest = df[zd_mask].copy(), df[~zd_mask].copy()
    if not len(zeroday):
        log(f"  WARNING {name}: zero-day families {ZERO_DAY[name]} absent")
    assign = stratified_split(rest, rng)
    splits = {s: rest[assign == s].copy() for s in SPLIT_FRACS}
    splits["zeroday"] = zeroday

    if unified:
        splits, encoders = apply_unified_encoding(splits)
        (out / "encoders.json").write_text(json.dumps(encoders, indent=1))

    feats0 = [c for c in splits["train"].columns if c not in LABELS and c not in CAT_COLS]
    groups = {g: [] for g in ["timing", "rate", "volume", "flags_state", "protocol", "connection_ctx", "other"]}
    for c in feats0:
        groups.setdefault(group_of(c), []).append(c)
    (out / "feature_groups.json").write_text(json.dumps(groups, indent=1))
    report["s3_groups"] = {g: len(cs) for g, cs in groups.items() if cs}
    report["s7_split"] = {s: len(v) for s, v in splits.items()}
    report["s7_zero_day_labels"] = sorted(zeroday["label_multiclass"].unique().tolist())

    with np.errstate(invalid="ignore", divide="ignore"):
        if unified:
            drop_corr, corr_pairs = [], []
        else:
            drop_corr, corr_pairs = corr_prune(splits["train"][feats0], CORR_PRUNE)
    feats = [c for c in feats0 if c not in drop_corr]
    for s in splits:
        splits[s] = splits[s].drop(columns=[c for c in drop_corr if c in splits[s].columns])

    priority = ["train", "val", "calibration", "test", "zeroday"]
    seen: set = set()
    dropped_dupes = {}
    for sname in priority:
        s = splits[sname]
        if not len(s):
            continue
        h = pd.util.hash_pandas_object(s[feats], index=False)
        keep_mask = ~h.isin(seen) & ~h.duplicated()
        dropped_dupes[sname] = int((~keep_mask).sum())
        splits[sname] = s[keep_mask.to_numpy()]
        seen |= set(h[keep_mask.to_numpy()])
    report["s7b_postprune_dupes_dropped"] = dropped_dupes

    train = splits["train"]
    scalers = {}
    for c in feats:
        med = float(train[c].median())
        iqr = float(train[c].quantile(0.75) - train[c].quantile(0.25)) or 1.0
        scalers[c] = {"median": med, "iqr": iqr}
        for s in splits:
            splits[s][c] = (splits[s][c] - med) / iqr
    train = splits["train"]

    with np.errstate(invalid="ignore", divide="ignore"):
        rank = (train[feats].corrwith(train["label_binary"].astype(float))
                .abs().fillna(0.0).sort_values(ascending=False))
    ranking = rank.index.tolist()
    budgets_map = {b: ranking[:b] for b in QUBIT_BUDGETS if b <= len(ranking)}
    (out / "qubit_budgets.json").write_text(json.dumps({
        "ranking_metric": "|pearson r| vs label_binary on train (baseline; Team C refines)",
        "ranking": ranking,
        "budgets": {str(b): f for b, f in budgets_map.items()},
        "corr_pruned": corr_pairs,
    }, indent=1))
    report["s6_quantum"] = {
        "corr_pruned": len(drop_corr), "n_features": len(feats),
        "budgets": {str(b): len(f) for b, f in budgets_map.items()},
    }

    angle = {c: {"min": float(train[c].min()), "max": float(train[c].max())} for c in ranking}
    for qb in sorted(budgets_map):
        for sname, s in splits.items():
            if not len(s):
                continue
            q = pd.DataFrame({c: np.clip((s[c] - angle[c]["min"]) / ((angle[c]["max"] - angle[c]["min"]) or 1.0),
                                         0.0, 1.0) * np.pi for c in budgets_map[qb]})
            for lbl in LABELS:
                q[lbl] = s[lbl].to_numpy()
            q.to_parquet(out / "quantum" / f"q{qb}_{sname}.parquet", index=False)

    (out / "scalers.json").write_text(json.dumps({
        "fit_on": "train split only (leakage-safe)",
        "robust": scalers, "angle_[0,pi]": angle,
    }, indent=1))

    parts = []
    for lbl, g in train.groupby("label_multiclass", sort=False):
        parts.append(g.sample(n=MAX_PER_CLASS, random_state=SEED) if len(g) > MAX_PER_CLASS else g)
    balanced = pd.concat(parts).sample(frac=1, random_state=SEED).reset_index(drop=True)
    report["s5_balance"] = {
        "train": len(train), "train_balanced": len(balanced),
        "capped_classes": [l for l, g in train.groupby("label_multiclass") if len(g) > MAX_PER_CLASS],
    }

    all_cols = feats + LABELS
    if unified:
        order = [c for c in load_schema()["feature_order"] if c in all_cols]
        all_cols = order

    hashes = {s: set(pd.util.hash_pandas_object(v[feats], index=False))
              for s, v in splits.items() if len(v)}
    names_ = list(hashes)
    for i in range(len(names_)):
        for j in range(i + 1, len(names_)):
            assert not (hashes[names_[i]] & hashes[names_[j]]), f"S8 overlap {names_[i]}/{names_[j]}"
    for pat in ZERO_DAY[name]:
        for s in ("train", "val", "calibration", "test"):
            assert not splits[s]["label_multiclass"].astype(str).str.startswith(pat).any()
    rare = [l for l, n in train["label_multiclass"].value_counts().items() if n <= MAX_PER_CLASS]
    assert all(balanced["label_multiclass"].value_counts().get(l, 0)
               == train["label_multiclass"].value_counts()[l] for l in rare)
    for sname, s in splits.items():
        if len(s):
            assert int(s[all_cols].isna().sum().sum()) == 0, f"S8: NaN in {sname}"
            s[all_cols].to_parquet(out / f"{sname}.parquet", index=False)
    balanced[all_cols].to_parquet(out / "train_balanced.parquet", index=False)
    report["s8_gates"] = "pass (disjoint splits, zero-day isolated, rare classes kept, 0 NaN)"
    report["per_class_split"] = {
        s: splits[s]["label_multiclass"].value_counts().to_dict() for s in splits if len(splits[s])}
    (out / "qadcp_report.json").write_text(json.dumps(report, indent=1))
    qmax = max(budgets_map) if budgets_map else 0
    log(f"  {name}: " + " ".join(f"{s}={len(v):,}" for s, v in splits.items())
        + f" balanced={len(balanced):,} feats={len(feats)} q{qmax}")
    return report


def process(name: str, unified: bool = False) -> dict:
    if unified:
        src = DATA / name / "unified" / "processed" / f"{name}_unified.parquet"
        out = DATA / name / "unified" / "qadcp"
    else:
        src = DATA / name / "processed" / f"{name}_clean.parquet"
        out = DATA / name / "qadcp"
    df = pd.read_parquet(src)
    return process_dataframe(df, name, out, src.relative_to(BASE).as_posix(), unified=unified)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unified", action="store_true")
    args = parser.parse_args()
    GEN.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name in DATASET_DIRS:
        log(f"QADCP {name} ({'unified' if args.unified else 'v0.1'})")
        summary[name] = process(name, unified=args.unified)
    fname = "unified_qadcp_summary.json" if args.unified else "qadcp_summary.json"
    (GEN / fname).write_text(json.dumps(summary, indent=1))
    log(f"done -> reports/_generated/{fname}")


if __name__ == "__main__":
    sys.exit(main())
