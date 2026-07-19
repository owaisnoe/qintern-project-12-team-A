#!/usr/bin/env python3
"""
Reproducibility MANIFEST generator — QuantumSentinel / QS-Net, Team A.

Implements recommendation R6: pin, per file, the **source URL + row count +
SHA-256 checksum** so all three team members train on byte-identical data.
Scope: every `*.csv` under each dataset's `raw/` + each dataset's `*.zip`
download artifact (user-approved: 193 CSVs + 5 zips ≈ 41 GB).

Outputs (committed, small):
  week1/manifest/manifest.json   machine-readable (loaders can validate against it)
  week1/manifest/MANIFEST.md     human-readable: per-dataset source URLs + file table

Usage (inside the Python 3.12 venv):
  python week1/scripts/make_manifest.py            # generate
  python week1/scripts/make_manifest.py --verify   # re-hash current files vs manifest.json
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

from _paths import DATASETS, PROJ, WEEK1, DATASET_DIRS, SOURCES, UNSW_RAW, used_files

OUTDIR = WEEK1 / "manifest"
MANIFEST_JSON = OUTDIR / "manifest.json"
MANIFEST_MD = OUTDIR / "MANIFEST.md"
WEEK2 = PROJ / "week2"                           # Week-2 partitions + RQ3 eval sets
NO_HEADER = {str(p) for p in UNSW_RAW}          # UNSW-NB15 raw 4-part has no header row
CHUNK = 1 << 20                                  # 1 MiB


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def hash_and_count(path: Path, count_lines: bool) -> tuple[str, int]:
    """Stream a file once: SHA-256 (hex) and (optionally) newline count."""
    h = hashlib.sha256()
    lines = 0
    with path.open("rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
            if count_lines:
                lines += chunk.count(b"\n")
    return h.hexdigest(), lines


def dataset_files(name: str) -> list[Path]:
    """All source, curated, Week-2, and classical-baseline artifacts for a dataset."""
    ddir = DATASETS / name
    csvs = sorted((ddir / "raw").rglob("*.csv")) if (ddir / "raw").exists() else []
    zips = sorted(ddir.glob("*.zip"))
    proc = sorted(p for p in (ddir / "processed").rglob("*") if p.is_file() and p.name != ".gitkeep")
    qadcp = sorted(p for p in (ddir / "qadcp").rglob("*") if p.is_file() and p.name != ".gitkeep")
    unified = sorted(p for p in (ddir / "unified").rglob("*") if p.is_file() and p.name != ".gitkeep")
    w2 = sorted(p for d in ("partitions", "rq3")
                for p in (WEEK2 / d / name).rglob("*") if p.is_file() and p.name != ".gitkeep")
    baselines = sorted(p for p in (WEEK2 / "baselines" / name).rglob("*")
                       if p.is_file() and p.name != ".gitkeep") if (WEEK2 / "baselines" / name).exists() else []
    idir = WEEK2 / "interface" / "dummy_scores" / name          # Day-14 prototype-shaped score interface
    iface = sorted(p for p in idir.rglob("*")
                   if p.is_file() and p.name != ".gitkeep") if idir.exists() else []
    return csvs + zips + proc + qadcp + unified + w2 + baselines + iface


def generate() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    used = used_files()
    manifest = {
        "note": ("Pin source URL + row count + SHA-256 per file so all team members train on "
                 "byte-identical data. Kaggle mirrors/variants differ → the SHA-256 is the real pin."),
        "sha256_algo": "sha256", "datasets": {},
    }
    grand_bytes = 0
    for name in DATASET_DIRS:
        files = dataset_files(name)
        entries, ds_bytes = [], 0
        log(f"{name}: hashing {len(files)} files")
        for p in files:
            rel = p.relative_to(PROJ).as_posix()
            is_csv = p.suffix == ".csv"
            size = p.stat().st_size
            sha, lines = hash_and_count(p, count_lines=is_csv)
            ds_bytes += size
            kind = ("baseline" if "/baselines/" in rel
                    else "week2" if rel.startswith("week2/") or "/week2/" in rel
                    else "unified" if "/unified/" in rel
                    else "qadcp" if "/qadcp/" in rel else "processed" if "/processed/" in rel
                    else "zip" if p.suffix == ".zip" else "raw")
            entry = {"path": rel, "bytes": size, "sha256": sha, "kind": kind,
                     "used_by_pipeline": str(p) in used}
            if is_csv:
                entry["data_rows"] = lines if str(p) in NO_HEADER else max(lines - 1, 0)
            entries.append(entry)
            log(f"  {p.name:42s} {size/1e6:8.1f} MB  {sha[:12]}…")
        grand_bytes += ds_bytes
        manifest["datasets"][name] = {
            **SOURCES[name], "n_files": len(files), "total_bytes": ds_bytes, "files": entries,
        }
    manifest["total_bytes"] = grand_bytes
    MANIFEST_JSON.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_markdown(manifest)
    log(f"Wrote {MANIFEST_JSON.relative_to(PROJ)} and {MANIFEST_MD.relative_to(PROJ)} "
        f"({grand_bytes/1e9:.1f} GB hashed)")


def write_markdown(manifest: dict) -> None:
    L = ["# Dataset MANIFEST — source pinning & checksums",
         "",
         "**QS-Net / QuantumSentinel — Team A.** Implements R6 (see "
         "[`reports/00_findings_and_flaws.md`](../reports/00_findings_and_flaws.md) §5): every file is "
         "pinned by **source URL + row count + SHA-256** so all three of us train on byte-identical "
         "data. Kaggle mirrors/variants differ, so the **SHA-256 is the authoritative pin**.",
         "",
         "Layout: `datasets/<name>/raw/` (source) · `datasets/<name>/processed/` (Day-3 clean "
         "checkpoints) · `datasets/<name>/qadcp/` (Day-4/5 QADCP splits + `quantum/` angle & PCA-8 "
         "tensors) · `datasets/<name>/unified/` (Day-6 unified schema package) · "
         "`week2/partitions/`, `week2/rq3/`, and `week2/baselines/` (Week-2 artifacts) · "
         "`datasets/<name>/<name>.zip` (download artifact). Regenerate / verify:",
         "```bash",
         "python week1/scripts/make_manifest.py           # regenerate",
         "python week1/scripts/make_manifest.py --verify  # re-hash vs manifest.json (0 mismatches expected)",
         "```",
         f"Total hashed: **{manifest['total_bytes']/1e9:.1f} GB** across "
         f"{sum(d['n_files'] for d in manifest['datasets'].values())} files.",
         ""]
    for name, d in manifest["datasets"].items():
        L += [f"## {name}",
              f"- **Official:** <{d['official']}>",
              f"- **Source:** {d['source']}",
              f"- **Paper:** {d['paper']}",
              f"- Files: {d['n_files']} · {d['total_bytes']/1e9:.2f} GB",
              "",
              "| file | kind | MB | rows | used | sha256 (16) |",
              "|---|:--:|---:|---:|:--:|---|"]
        for e in d["files"]:
            rows = f"{e['data_rows']:,}" if "data_rows" in e else "—"
            used = "✓" if e["used_by_pipeline"] else ""
            name_only = e["path"].split("/")[-1]
            L.append(f"| `{name_only}` | {e.get('kind','')} | {e['bytes']/1e6:.1f} | {rows} | {used} | `{e['sha256'][:16]}` |")
        L.append("")
    L += ["## Concerns & Recommendations",
          "- **Mirror/slug ambiguity:** several datasets have many Kaggle mirrors (UNSW-NB15: "
          "alextamboli, primus11, harshwardhanbhangale…); the exact download slug for some is "
          "unconfirmed. The **official URL + SHA-256** here are authoritative — pin by checksum, not slug.",
          "- **Verify before training:** all three members run `--verify` before any experiment; a "
          "non-zero mismatch means someone has a different variant/mirror → re-sync from the pinned source.",
          "- **Curated outputs — pinned:** each dataset's `processed/*_clean.parquet` (Day-3) **and** its "
          "`qadcp/` splits + `quantum/` tensors (Day-4/5, incl. the `pca8_*` baseline) are hashed here too, "
          "so Team B/C consume checksum-pinned curated data — not just the raw.",
          "- **Classical baselines — pinned:** Week-2 `baselines/<name>/` model, prediction, and result "
          "artifacts are included for byte-identical handoff and audit.",
          "- **TON_IoT variant & CIC mirror:** row counts are valid variants/mirror (not errors); this "
          "manifest records exactly which bytes we standardized on.",
          ""]
    MANIFEST_MD.write_text("\n".join(L), encoding="utf-8")


def verify() -> int:
    if not MANIFEST_JSON.exists():
        log("No manifest.json — run without --verify first."); return 2
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    ok = miss = bad = 0
    for name, d in manifest["datasets"].items():
        for e in d["files"]:
            p = PROJ / e["path"]
            if not p.exists():
                log(f"MISSING  {e['path']}"); miss += 1; continue
            sha, _ = hash_and_count(p, count_lines=False)
            if sha == e["sha256"]:
                ok += 1
            else:
                log(f"MISMATCH {e['path']}\n   expected {e['sha256']}\n   actual   {sha}"); bad += 1
    log(f"verify: {ok} OK, {bad} mismatch, {miss} missing")
    return 0 if (bad == 0 and miss == 0) else 1


if __name__ == "__main__":
    sys.exit(verify() if "--verify" in sys.argv else (generate() or 0))
