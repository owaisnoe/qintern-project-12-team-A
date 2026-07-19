#!/usr/bin/env python3
"""
Week 2 · Day 14 (Team A) — DATA FREEZE: version and pin the whole Week-2 deliverable surface as v1.0.

Emits a Week-2-scoped freeze manifest that pins every deliverable file (partitions, RQ3, baselines,
generated reports, the dummy-score interface, scripts, reports) by SHA-256 + byte size + row count.
This is deliberately **independent of the Week-1 raw-tree manifest**: per the Day-13 handoff, this
checkout has no raw data (0 of 193 raw CSVs), so re-running week1/make_manifest.py here would produce a
divergent partial manifest. The freeze pins only what Team A actually ships this week, so it is
self-consistent on any checkout that carries the week2/ tree.

Outputs (under week2/FROZEN/):
  freeze_manifest_v1.0.json   {package, version, seed, trio, files:[{path, sha256, bytes, rows}]}
  VERSION                     one-line version marker
  FROZEN_PACKAGE.md           human index of the frozen package

Run (freeze):  python week2/scripts/freeze_package.py            # writes FROZEN/ (run AFTER make_dummy_scores)
Verify:        python week2/scripts/freeze_package.py --verify   # re-hash, expect 0 mismatch
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]      # Team A/
WEEK2 = BASE / "week2"
FROZEN = WEEK2 / "FROZEN"

VERSION = "1.0"
SEED = 42
TRIO = ["CICIoT2023", "BoT-IoT", "UNSW-NB15"]
MANIFEST = FROZEN / f"freeze_manifest_v{VERSION}.json"

# Everything under week2/ is frozen except transient / self / non-deliverable noise.
EXCLUDE_DIRS = {"__pycache__", "FROZEN"}
EXCLUDE_SUFFIX = {".pyc", ".pyo"}
EXCLUDE_NAMES = {".DS_Store"}


def _iter_files():
    for p in sorted(WEEK2.rglob("*")):
        if not p.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in p.relative_to(WEEK2).parts):
            continue
        if p.suffix in EXCLUDE_SUFFIX or p.name in EXCLUDE_NAMES:
            continue
        yield p


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _rows(path: Path):
    """Row count for tabular deliverables (data rows, header excluded); None otherwise."""
    try:
        if path.suffix == ".csv":
            with path.open("rb") as fh:
                n = sum(1 for _ in fh)
            return max(0, n - 1)
        if path.suffix == ".parquet":
            import pyarrow.parquet as pq
            return pq.ParquetFile(path).metadata.num_rows
    except Exception:
        return None
    return None


def build_records() -> list[dict]:
    recs = []
    for p in _iter_files():
        recs.append({
            "path": p.relative_to(BASE).as_posix(),
            "sha256": _sha256(p),
            "bytes": p.stat().st_size,
            "rows": _rows(p),
        })
    return recs


def freeze() -> None:
    FROZEN.mkdir(parents=True, exist_ok=True)
    recs = build_records()
    total_bytes = sum(r["bytes"] for r in recs)
    manifest = {
        "package": "QS-Net / QuantumSentinel — Team A — Week-2 data package",
        "version": VERSION,
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "seed": SEED,
        "benchmark_trio": TRIO,
        "scope": "Week-2 deliverable surface only (partitions, RQ3, baselines, interface, reports, "
                 "scripts). Independent of the Week-1 raw-tree manifest (no raw data in this checkout).",
        "note": "DATA FREEZE (Day 14). File hashes are content-only; frozen_utc is metadata and is NOT "
                "part of --verify. Re-hash with --verify (expect 0 mismatch).",
        "n_files": len(recs),
        "total_bytes": total_bytes,
        "files": recs,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=1))

    (FROZEN / "VERSION").write_text(
        f"QS-Net Team A — Week-2 data package\n"
        f"version: {VERSION}\n"
        f"freeze: DATA FREEZE (Week 2, Day 14)\n"
        f"seed: {SEED}\n"
        f"trio: CIC-IoT2023, BoT-IoT, UNSW-NB15\n"
        f"files: {len(recs)}  bytes: {total_bytes}\n"
        f"manifest: FROZEN/{MANIFEST.name}\n"
    )
    _write_index(manifest)
    print(f"FROZEN v{VERSION}: pinned {len(recs)} files, {total_bytes/1e6:.1f} MB")
    print(f"  -> {MANIFEST.relative_to(BASE)}")


def _write_index(manifest: dict) -> None:
    by_top: dict[str, list[dict]] = {}
    for r in manifest["files"]:
        # group by the first sub-directory under week2/ (files directly under week2/ -> "(root)")
        sub = Path(r["path"]).relative_to("week2").parts
        top = sub[0] if len(sub) > 1 else "(root)"
        by_top.setdefault(top, []).append(r)
    lines = [
        f"# FROZEN — QS-Net Team A · Week-2 data package · **v{manifest['version']}**",
        "",
        f"**DATA FREEZE (Day 14).** Seed {manifest['seed']} · benchmark trio "
        f"{', '.join(manifest['benchmark_trio'])} · {manifest['n_files']} files · "
        f"{manifest['total_bytes']/1e6:.1f} MB · frozen {manifest['frozen_utc']}.",
        "",
        "Every file below is pinned by SHA-256 in "
        f"[`{MANIFEST.name}`]({MANIFEST.name}). Verify with:",
        "",
        "```bash",
        "python week2/scripts/freeze_package.py --verify   # expect 0 mismatch",
        "```",
        "",
        "This freeze is **Week-2-scoped and self-contained** — it does not depend on the Week-1 raw-tree "
        "manifest (this checkout carries no raw data). See the Day-14 report "
        "[`../reports/w2_06_data_freeze.md`](../reports/w2_06_data_freeze.md).",
        "",
        "| Group | Files | Bytes |",
        "|---|---:|---:|",
    ]
    for top in sorted(by_top):
        grp = by_top[top]
        lines.append(f"| `week2/{top}/` | {len(grp)} | {sum(g['bytes'] for g in grp):,} |")
    (FROZEN / "FROZEN_PACKAGE.md").write_text("\n".join(lines) + "\n")


def verify() -> int:
    if not MANIFEST.exists():
        print(f"NO FREEZE MANIFEST at {MANIFEST.relative_to(BASE)} — run without --verify first.")
        return 2
    pinned = {r["path"]: r for r in json.loads(MANIFEST.read_text())["files"]}
    current = {r["path"]: r for r in build_records()}

    missing = sorted(set(pinned) - set(current))
    added = sorted(set(current) - set(pinned))
    changed = [p for p in sorted(set(pinned) & set(current))
               if pinned[p]["sha256"] != current[p]["sha256"]]

    for p in missing:
        print(f"  MISSING  {p}")
    for p in added:
        print(f"  ADDED    {p}  (not in freeze)")
    for p in changed:
        print(f"  CHANGED  {p}")

    n_bad = len(missing) + len(added) + len(changed)
    if n_bad == 0:
        print(f"FREEZE VERIFY OK — {len(pinned)} files, 0 mismatch.")
        return 0
    print(f"FREEZE VERIFY FAILED — {len(missing)} missing, {len(added)} added, {len(changed)} changed.")
    return 1


def main() -> None:
    ap = argparse.ArgumentParser(description="Day-14 DATA FREEZE — pin the Week-2 package as v1.0")
    ap.add_argument("--verify", action="store_true", help="re-hash and diff against the freeze manifest")
    args = ap.parse_args()
    if args.verify:
        sys.exit(verify())
    freeze()


if __name__ == "__main__":
    main()
