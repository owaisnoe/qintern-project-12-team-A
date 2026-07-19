#!/usr/bin/env python3
"""
Build the machine-readable feature inventory (Deliverable ② companion) from the
per-dataset profile JSONs produced by profile_datasets.py.

Emits week1/reports/feature_inventory.csv with one row per (dataset, column):
    dataset, column, dtype, n_unique, n_missing, example, is_label, role, drop_reason

`role` is keep/drop/label. Drops come from (a) curated per-dataset identifier/empty
lists and (b) auto-detected zero-variance columns read from each profile's
quality.constant_columns. See 00_findings_and_flaws.md / 02_feature_inventory.md.

Run inside the Python 3.12 venv, after profile_datasets.py:
    python week1/scripts/build_feature_inventory.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WEEK1 = HERE.parent
GEN = WEEK1 / "reports" / "_generated"
OUT = WEEK1 / "reports" / "feature_inventory.csv"

KEYS = ("ciciot", "toniot", "botiot", "edge", "unsw", "unsw_raw")

LABELS = {
    "ciciot": {"label"},
    "toniot": {"label", "type"},
    "botiot": {"attack", "category", "subcategory"},
    "edge": {"Attack_label", "Attack_type"},
    "unsw": {"attack_cat", "label"},
    "unsw_raw": {"attack_cat", "Label"},
}

# Curated identifier / empty drops (zero-variance drops are added automatically below).
MANUAL_DROP = {
    "ciciot": {},
    "toniot": {c: "leaky identifier" for c in ("src_ip", "dst_ip", "src_port", "dst_port")},
    "botiot": {c: "leaky identifier" for c in
               ("pkSeqID", "stime", "ltime", "seq", "saddr", "daddr", "sport", "dport")},
    "edge": {},
    "unsw": {"id": "identifier"},
    "unsw_raw": {c: "leaky identifier" for c in
                 ("srcip", "sport", "dstip", "dsport", "Stime", "Ltime")},
}


def main() -> None:
    rows = []
    for key in KEYS:
        path = GEN / f"{key}_profile.json"
        if not path.exists():
            print(f"  (skip {key}: {path.name} not found)")
            continue
        prof = json.loads(path.read_text(encoding="utf-8"))
        name = prof["name"]
        drops = dict(MANUAL_DROP[key])
        for c in prof.get("quality", {}).get("constant_columns", []):
            drops.setdefault(c, "zero-variance / empty")
        for c in prof["columns"]:
            col = c["name"]
            is_label = col in LABELS[key]
            drop_reason = drops.get(col, "")
            role = "label" if is_label else ("drop" if drop_reason else "keep")
            rows.append({
                "dataset": name, "column": col, "dtype": c["dtype"],
                "n_unique": c["n_unique"], "n_missing": c["n_missing"],
                "example": c["example"], "is_label": is_label,
                "role": role, "drop_reason": drop_reason,
            })

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    kept = sum(r["role"] == "keep" for r in rows)
    dropped = sum(r["role"] == "drop" for r in rows)
    labels = sum(r["role"] == "label" for r in rows)
    print(f"Wrote {OUT.relative_to(WEEK1.parent)}: {len(rows)} columns "
          f"({kept} keep, {dropped} drop, {labels} label)")


if __name__ == "__main__":
    main()
