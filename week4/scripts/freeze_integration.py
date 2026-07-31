#!/usr/bin/env python3
"""
Week 4 · Day 21 (Team A) — FREEZE the calibration + statistics interface for integration week.

Task (`qi26_12_Week_4.pdf`): *Freeze the calibration + statistics interface for integration week. Package
coverage + zero-day + significance outputs for Team B's inference pipeline.* Deliverables:
"Frozen calibration/stats package" / "Integration-ready outputs".

What this freezes (and why a freeze, not just a copy)
-----------------------------------------------------
Integration week (Days 22–25) connects Team B's real inference scores to Team A's conformal machinery. For
that hand-off to be reproducible, the *contract* must stop moving: the calibration rule, the score schema,
the primary α, and the per-dataset thresholds have to be pinned so a decision computed on Day 25 uses the
exact same q as Day 22. This module emits a versioned, SHA-256-pinned package under `week4/INTEGRATION/`:

  frozen_thresholds.json   the authoritative per-dataset conformal threshold q at the primary α (α = 0.05),
                           recomputed here from the single Day-15 rule (q = s_(k), k = ⌈(1−α)(n+1)⌉) on the
                           **known-only** calibration split, plus n_cal, k, achieved coverage / false-zero-day
                           and the exact-band verdict. This is the number Team B's Day-22 adapter loads — they
                           never recalibrate.
  interface_contract.json  the frozen score schema Team B must emit (the fid__<class> columns, the
                           nonconformity definition s = 1 − max_c F, the fidelity convention, α, seed) — a copy
                           of the Day-14 schema, pinned so it cannot drift under integration.
  INTEGRATION_PACKAGE.md   human index + Team-B plug-in instructions.
  integration_manifest_v1.0.json   SHA-256 + bytes + rows for every frozen file: the pinned code modules
                           (Day-15 calibrate, Day-16 coverage harness, Day-17 stats protocol, Day-19 recall),
                           the score interface, the packaged coverage / zero-day / significance outputs, and
                           the two files above. `--verify` re-hashes → 0 mismatch.

Determinism: `calibrate_dataset` is deterministic (seed 42), so the frozen thresholds are reproducible; the
`frozen_utc` field is metadata and is NOT part of `--verify` (same convention as the Week-2 freeze).

Reprice on real prototypes: pass `--scores-root <team-B dir> --source real`; the frozen package is then the
real-fidelity contract. The schema is identical, so no downstream code changes (Day-22 adapter included).

Run (freeze):  python week4/scripts/freeze_integration.py
Verify:        python week4/scripts/freeze_integration.py --verify   # re-hash, expect 0 mismatch
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]                 # Team A/
sys.path.insert(0, str(BASE / "week3" / "scripts"))

from conformal_calibrate import IFACE, TRIO, _rel, calibrate_dataset  # noqa: E402  (Day-15 single source)
from coverage_harness import verify_dataset                     # noqa: E402  (Day-16 exact-band verdict)

INTEG = BASE / "week4" / "INTEGRATION"
SCHEMA_SRC = BASE / "week2" / "interface" / "dummy_scores_schema.json"
VERSION = "1.0"
SEED = 42
PRIMARY_ALPHA = 0.05
MANIFEST = INTEG / f"integration_manifest_v{VERSION}.json"

# The code + data surface the integration hand-off depends on (pinned so it cannot drift during Days 22–25).
# Paths are repo-relative; missing optional outputs are skipped with a note (never a hard fail on a partial
# checkout), but the four core modules must exist.
CORE_MODULES = [
    "week3/scripts/conformal_calibrate.py",   # Day 15 — the threshold rule q = s_(k)
    "week3/scripts/coverage_harness.py",       # Day 16 — exact-band coverage verification
    "week3/scripts/stats_protocol.py",         # Day 17 — significance protocol
    "week4/scripts/zeroday_recall.py",         # Day 19 — detection-power (recall) arm
]
PACKAGED_OUTPUTS = [
    "week3/reports/_generated/w3_02_coverage_verification.json",   # coverage
    "week3/reports/_generated/w3_02_alpha_sweep.csv",
    "week3/reports/_generated/w3_04_coverage_table.json",         # coverage table v1 (Day 18)
    "week4/reports/_generated/w4_01_zeroday_recall.json",         # zero-day recall
    "week4/reports/_generated/w4_01_zeroday_recall.csv",
    "week3/reports/_generated/w3_03_significance_dryrun.json",    # significance
    "week3/reports/_generated/w3_03_significance_dryrun.csv",
]
INTERFACE_GLOB = "week2/interface/dummy_scores"                    # the score interface Team B fills


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _rows(path: Path):
    try:
        if path.suffix == ".csv":
            with path.open("rb") as fh:
                return max(0, sum(1 for _ in fh) - 1)
        if path.suffix == ".parquet":
            import pyarrow.parquet as pq
            return pq.ParquetFile(path).metadata.num_rows
    except Exception:
        return None
    return None


# ---------------------------------------------------------------- frozen thresholds (the deliverable core)

def compute_frozen_thresholds(datasets, alpha, scores_root, source):
    """Per-dataset authoritative q at the primary α + coverage verdict (Day-15 rule, Day-16 band)."""
    out = {}
    for ds in datasets:
        c = calibrate_dataset(ds, alpha, scores_root)          # q = s_(k) on known-only calibration
        v = verify_dataset(ds, alpha, scores_root)             # exact-band finite-sample verdict
        out[ds] = {
            "alpha": alpha,
            "mode": c["mode"],
            "n_known_classes": c["n_known_classes"],
            "n_cal": c["calibration_n"],
            "k": c["k"],
            "threshold_q": c["threshold_q"],                   # <-- the number Team B loads on Day 22
            "decision_rule": "flag zero-day iff  s = 1 - max_c F(rho_x, rho_c)  >  threshold_q",
            "known_test": c["known_test"],
            "zeroday_rejection_rate": c["zeroday"]["rejection_rate"],
            "achieved_coverage": v["known_coverage"],
            "false_zeroday_rate": v["fzr_observed"],
            "exact_band": [v["band_lo_rate"], v["band_hi_rate"]],
            "band_p_value_upper": v["p_value_upper"],
            "coverage_verdict": v["verdict"],
        }
    return out


def write_frozen_thresholds(datasets, alpha, scores_root, source):
    thresholds = compute_frozen_thresholds(datasets, alpha, scores_root, source)
    doc = {
        "package": "QS-Net / QuantumSentinel — Team A — Integration calibration package",
        "version": VERSION,
        "day": 21,
        "seed": SEED,
        "primary_alpha": alpha,
        "source_kind": source,
        "scores_root": _rel(scores_root),
        "decision_rule": "flag x as zero-day iff s(x) > threshold_q, with s = 1 - max_c F(rho_x, rho_c)",
        "nonconformity_def": "s = 1 - max_c F(rho_x, rho_c)  (non-squared Uhlmann fidelity F in [0,1])",
        "q_index_formula": "k = ceil((1-alpha)*(n+1)); q = s_(k)  (Day-15 CQ-ZDR / Algorithm 2)",
        "note": "Authoritative per-dataset thresholds for integration week. Team B's Day-22 adapter loads "
                "threshold_q and applies the decision rule; it does NOT recalibrate. Reprices on real "
                "prototypes via --source real --scores-root <dir> (identical schema).",
        "datasets": thresholds,
    }
    (INTEG / "frozen_thresholds.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return thresholds


def write_interface_contract():
    """Freeze the Day-14 score schema as the integration contract (pinned so it can't drift)."""
    schema = json.loads(SCHEMA_SRC.read_text(encoding="utf-8"))
    contract = {
        "package": "QS-Net — Team A — frozen score-interface contract",
        "version": VERSION,
        "day": 21,
        "seed": SEED,
        "primary_alpha": PRIMARY_ALPHA,
        "source_schema": "week2/interface/dummy_scores_schema.json (Day 14)",
        "fidelity_convention": "NON-SQUARED Uhlmann F in [0,1]. PennyLane qml.math.fidelity and Qiskit "
                               "state_fidelity return F^2 -> emit sqrt() into fid__<class>, or run the "
                               "adapter with --assume-fidelity-squared. s, F_in, F_out share one convention.",
        "required_columns": schema["base_columns"],
        "prototype_columns": schema["prototype_columns"],
        "nonconformity": schema["nonconformity"],
        "row_alignment": schema["row_alignment"],
        "column_dtypes": schema["column_dtypes"],
        "datasets": schema["datasets"],
    }
    (INTEG / "interface_contract.json").write_text(json.dumps(contract, indent=1), encoding="utf-8")
    return contract


# ---------------------------------------------------------------- manifest + index

def _resolve_files():
    """The concrete file list to pin: core modules (required), packaged outputs (optional), interface tree,
    plus the two files this freeze writes. Returns (records, missing_required, missing_optional)."""
    records, missing_required, missing_optional = [], [], []
    frozen_here = ["week4/INTEGRATION/frozen_thresholds.json",
                   "week4/INTEGRATION/interface_contract.json"]
    for rel in CORE_MODULES + frozen_here:
        p = BASE / rel
        if p.exists():
            records.append(rel)
        else:
            missing_required.append(rel)
    for rel in PACKAGED_OUTPUTS:
        p = BASE / rel
        (records if p.exists() else missing_optional).append(rel)
    # the score interface Team B fills (whole tree)
    for p in sorted((BASE / INTERFACE_GLOB).rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            records.append(p.relative_to(BASE).as_posix())
    # de-dup while keeping order
    seen, uniq = set(), []
    for r in records:
        if r not in seen:
            seen.add(r); uniq.append(r)
    return uniq, missing_required, missing_optional


def build_records(rels):
    recs = []
    for rel in rels:
        p = BASE / rel
        recs.append({"path": rel, "sha256": _sha256(p), "bytes": p.stat().st_size, "rows": _rows(p)})
    return recs


def freeze(datasets, alpha, scores_root, source):
    INTEG.mkdir(parents=True, exist_ok=True)
    thresholds = write_frozen_thresholds(datasets, alpha, scores_root, source)
    write_interface_contract()

    rels, missing_required, missing_optional = _resolve_files()
    if missing_required:
        for m in missing_required:
            log(f"  ERROR missing required module: {m}")
        raise SystemExit(f"freeze aborted — {len(missing_required)} required module(s) absent")
    recs = build_records(rels)
    total = sum(r["bytes"] for r in recs)
    manifest = {
        "package": "QS-Net / QuantumSentinel — Team A — Integration calibration/stats package",
        "version": VERSION, "day": 21, "seed": SEED,
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "primary_alpha": alpha, "source_kind": source, "benchmark_trio": list(datasets),
        "scope": "Integration hand-off surface: the pinned conformal/coverage/stats/recall code modules, the "
                 "score interface Team B fills, the packaged coverage/zero-day/significance outputs, and the "
                 "frozen thresholds + interface contract. frozen_utc is metadata, NOT part of --verify.",
        "missing_optional_outputs": missing_optional,
        "n_files": len(recs), "total_bytes": total, "files": recs,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    (INTEG / "VERSION").write_text(
        f"QS-Net Team A — Integration calibration/stats package\nversion: {VERSION}\n"
        f"freeze: INTEGRATION FREEZE (Week 4, Day 21)\nseed: {SEED}\nprimary_alpha: {alpha}\n"
        f"source: {source}\ntrio: {', '.join(datasets)}\nfiles: {len(recs)}  bytes: {total}\n"
        f"manifest: INTEGRATION/{MANIFEST.name}\n", encoding="utf-8")
    _write_index(manifest, thresholds)
    if missing_optional:
        log(f"note: {len(missing_optional)} optional output(s) absent, skipped: {missing_optional}")
    log(f"INTEGRATION FREEZE v{VERSION}: pinned {len(recs)} files, {total/1e6:.1f} MB, source={source}")
    for ds, t in thresholds.items():
        log(f"  {ds}: q={t['threshold_q']} coverage={t['achieved_coverage']} "
            f"FZR={t['false_zeroday_rate']} verdict={t['coverage_verdict']}")
    return manifest


def _write_index(manifest, thresholds):
    L = [f"# INTEGRATION — QS-Net Team A · calibration/stats package · **v{manifest['version']}**", "",
         f"**INTEGRATION FREEZE (Day 21).** Seed {manifest['seed']} · primary α = {manifest['primary_alpha']} "
         f"· source `{manifest['source_kind']}` · trio {', '.join(manifest['benchmark_trio'])} · "
         f"{manifest['n_files']} files · {manifest['total_bytes']/1e6:.1f} MB · frozen {manifest['frozen_utc']}.",
         "",
         "Frozen hand-off surface for integration week (Days 22–25): the calibration rule, the score schema, "
         "the primary α, and the per-dataset thresholds are pinned so a decision on Day 25 uses the same `q` "
         "as Day 22. Every file is SHA-256-pinned in "
         f"[`{MANIFEST.name}`]({MANIFEST.name}). Verify:", "",
         "```bash", "python week4/scripts/freeze_integration.py --verify   # expect 0 mismatch", "```", "",
         "## Frozen thresholds (α = %.2f, source: %s)" % (manifest["primary_alpha"], manifest["source_kind"]),
         "", "| Dataset | n_cal | k | threshold q | achieved coverage | false-zero-day | exact band | verdict |",
         "|---|---:|---:|---:|---:|---:|---|---|"]
    for ds, t in thresholds.items():
        q = "—" if t["threshold_q"] is None else f"{t['threshold_q']:.6f}"
        band = f"[{t['exact_band'][0]:.4f}, {t['exact_band'][1]:.4f}]"
        L.append(f"| {ds} | {t['n_cal']:,} | {t['k']:,} | {q} | {t['achieved_coverage']:.4f} | "
                 f"{t['false_zeroday_rate']:.4f} | {band} | {t['coverage_verdict']} |")
    L += ["", "## What Team B does with this (Day 22)",
          "1. Emit real inference scores into the **frozen schema** (`interface_contract.json`): one row per "
          "partition row, the `fid__<class>` Uhlmann-fidelity columns (**non-squared** F).",
          "2. Point the Day-22 adapter at your score dir; it loads `frozen_thresholds.json[<dataset>].threshold_q` "
          "and flags a point as zero-day iff `s = 1 − max_c F > q`. **No recalibration** — the threshold is frozen.",
          "3. Reprice the whole package on real prototypes with `--source real --scores-root <your dir>` "
          "(identical schema → no code change).", "",
          "## Contents",
          "- `frozen_thresholds.json` — authoritative per-dataset `q` + coverage verdict (the integration core).",
          "- `interface_contract.json` — the frozen score schema + fidelity convention Team B must emit.",
          "- pinned code: Day-15 `conformal_calibrate.py`, Day-16 `coverage_harness.py`, Day-17 "
          "`stats_protocol.py`, Day-19 `zeroday_recall.py`.",
          "- packaged outputs: coverage (`w3_02_*`, `w3_04_*`), zero-day recall (`w4_01_*`), significance "
          "(`w3_03_*`).",
          "- the score interface Team B fills (`week2/interface/dummy_scores/`)."]
    if manifest["missing_optional_outputs"]:
        L += ["", "> Note: optional outputs absent on this checkout (regenerate to include): "
              + ", ".join(f"`{m}`" for m in manifest["missing_optional_outputs"]) + "."]
    (INTEG / "INTEGRATION_PACKAGE.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def verify():
    if not MANIFEST.exists():
        print(f"NO INTEGRATION MANIFEST at {MANIFEST.relative_to(BASE)} — run without --verify first.")
        return 2
    pinned = {r["path"]: r for r in json.loads(MANIFEST.read_text())["files"]}
    current = {rel: None for rel in pinned}
    missing, changed = [], []
    for rel in pinned:
        p = BASE / rel
        if not p.exists():
            missing.append(rel); continue
        if _sha256(p) != pinned[rel]["sha256"]:
            changed.append(rel)
    for p in missing:
        print(f"  MISSING  {p}")
    for p in changed:
        print(f"  CHANGED  {p}")
    n_bad = len(missing) + len(changed)
    if n_bad == 0:
        print(f"INTEGRATION VERIFY OK — {len(pinned)} files, 0 mismatch.")
        return 0
    print(f"INTEGRATION VERIFY FAILED — {len(missing)} missing, {len(changed)} changed.")
    return 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Day-21 integration freeze — pin the calibration/stats package")
    ap.add_argument("--datasets", nargs="+", default=list(TRIO))
    ap.add_argument("--alpha", type=float, default=PRIMARY_ALPHA)
    ap.add_argument("--scores-root", default=str(IFACE))
    ap.add_argument("--source", choices=["dummy", "real"], default="dummy")
    ap.add_argument("--verify", action="store_true", help="re-hash and diff against the freeze manifest")
    args = ap.parse_args(argv)
    if args.verify:
        sys.exit(verify())
    freeze(args.datasets, args.alpha, args.scores_root, args.source)


if __name__ == "__main__":
    main()
