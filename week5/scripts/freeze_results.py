#!/usr/bin/env python3
"""
Week 5 · Day 26 (Team A) — FREEZE the Day-26/27 result artefacts + confirm reproducibility.

Task (`qi26_12_Week_5.pdf`): *Freeze Team-A result artefacts and confirm every RQ2/RQ5 number reproduces.*
Deliverable: a versioned, SHA-256-pinned `week5/RESULTS_FROZEN/` package of the results week's outputs, so
the manuscript (and Day 32's "reproducible from one script" sign-off) cites a fixed surface — and a
`--reproduce` check that re-runs the three result mains and confirms the headline scalars come back bit-for-
bit.

Why a freeze here, and what is pinned
-------------------------------------
Week 5 is the results week; after it, only manuscript writing. So the numbers behind Table A (RQ1), the
disentanglement AUROC (RQ3), and Figure 2 (the coverage headline) must stop moving. This module pins:

  the three result modules      week5/scripts/{disentanglement,table_a,figure2_coverage}.py
  disentanglement (RQ3)         w5_01_disentanglement.{md,json,csv}
  Table A (RQ1)                 w5_02_table_a.{md,json,csv} + w5_02_table_a.{md,tex} + w5_02_per_class_fzr.csv
  Figure 2 (coverage headline)  w5_03_figure2.{md,json} + w5_03_figure2_data.csv + figures/w5_fig2_coverage.png

with a SHA-256 + bytes + rows manifest under `week5/RESULTS_FROZEN/`. `--verify` re-hashes → 0 mismatch.

Two gates this freeze adds over the Day-21 integration freeze
-------------------------------------------------------------
1. **LF gate (`_assert_lf`).** A fresh clone with `core.autocrlf=true` (Windows) rewrites committed text
   files to CRLF on checkout, so their bytes — and SHA-256 — differ from the Linux-frozen blob, and
   `--verify` fails through no fault of the results. The repo-root `.gitattributes` (`* text=auto eol=lf`,
   binaries pinned) prevents that; this gate is belt-and-braces: the freeze aborts if any pinned TEXT file
   already contains a CRLF, so a CRLF blob can never be frozen in the first place. Run the freeze on Linux.
2. **Reproducibility check (`--reproduce`).** The three mains are deterministic (seed 42), so re-running them
   must return identical headline scalars. `--reproduce` re-runs all three and asserts every pinned scalar
   (each separation/OVR AUROC, every Table-A cell, each all-seed / per-class / 5-seed coverage number)
   matches the frozen snapshot to 1e-9. This is the "confirm every number reproduces" deliverable.

Reprice on real prototypes: `--source real --scores-root <team-B dir>` freezes the real-fidelity results
package; the schema is identical, so nothing downstream changes.

Run (freeze):     python week5/scripts/freeze_results.py
Freeze as-is:     python week5/scripts/freeze_results.py --no-regenerate # pin on-disk artefacts, no re-run
Verify:           python week5/scripts/freeze_results.py --verify      # re-hash, expect 0 mismatch
Reproduce-check:  python week5/scripts/freeze_results.py --reproduce   # re-run mains, expect 0 mismatch

`freeze(..., regenerate=False)` (CLI `--no-regenerate`) pins the already-committed full-trio artefacts
without re-running the mains, so a partial-dataset call can never overwrite the committed 3-dataset
reports/figure on disk (the CIC-only clobber guard — belt-and-braces with the tests' output sandboxing).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week3" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))
sys.path.insert(0, str(BASE / "week5" / "scripts"))

from conformal_calibrate import IFACE, TRIO          # noqa: E402
from freeze_integration import _rows, _sha256        # noqa: E402  (Day-21 — reuse the hash/row helpers)
import disentanglement as dis                          # noqa: E402  (Day-26 RQ3)
import table_a as ta                                   # noqa: E402  (Day-26 RQ1 + coverage diagnostics)
import figure2_coverage as fig2                        # noqa: E402  (Day-27 coverage headline)

RESULTS = BASE / "week5" / "RESULTS_FROZEN"
VERSION = "1.0"
SEED = 42
PRIMARY_ALPHA = 0.05
MANIFEST = RESULTS / f"results_manifest_v{VERSION}.json"
SCALARS = RESULTS / "results_frozen_scalars.json"

TEXT_SUFFIXES = {".md", ".tex", ".csv", ".json", ".py"}

# The result surface the manuscript cites (repo-relative). Produced by the three Day-26/27 mains.
PINNED = [
    "week5/scripts/disentanglement.py",
    "week5/scripts/table_a.py",
    "week5/scripts/figure2_coverage.py",
    "week5/reports/w5_01_disentanglement.md",
    "week5/reports/w5_02_table_a.md",
    "week5/reports/w5_03_figure2.md",
    "week5/reports/_generated/w5_01_disentanglement.json",
    "week5/reports/_generated/w5_01_disentanglement.csv",
    "week5/reports/_generated/w5_02_table_a.json",
    "week5/reports/_generated/w5_02_table_a.csv",
    "week5/reports/_generated/w5_02_table_a.md",
    "week5/reports/_generated/w5_02_table_a.tex",
    "week5/reports/_generated/w5_02_per_class_fzr.csv",
    "week5/reports/_generated/w5_03_figure2.json",
    "week5/reports/_generated/w5_03_figure2_data.csv",
    "week5/reports/figures/w5_fig2_coverage.png",
]


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


# ---------------------------------------------------------------- LF gate

def _assert_lf(path: Path):
    """Abort if a pinned TEXT file contains a CRLF — a CRLF blob must never enter the freeze (Windows trap)."""
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return
    if b"\r\n" in path.read_bytes():
        try:
            disp = path.relative_to(BASE).as_posix()
        except ValueError:
            disp = path.name
        raise SystemExit(
            f"CRLF detected in {disp} — refusing to freeze. "
            f"Re-checkout on Linux (the repo-root .gitattributes pins eol=lf) and re-run.")


# ---------------------------------------------------------------- run the three result mains

def run_all(datasets, alpha, scores_root, source):
    """Run the Day-26/27 mains (deterministic, seed 42) and return their result dicts."""
    common = ["--datasets", *datasets, "--alpha", str(alpha),
              "--scores-root", str(scores_root), "--source", source]
    d = dis.main(common)
    t = ta.main(common)
    f = fig2.main(common)
    return d, t, f


def key_scalars(d, t, f):
    """The reproducibility-critical scalars, flattened to `key -> number` for an exact 1e-9 compare."""
    s = {}
    for ds, r in d["results"].items():
        for p in r["panels"]:
            s[f"dis/{ds}/{p['panel']}/auroc"] = p["auroc"]
    for r in t["rows"]:
        tag = "xgboost" if r["arm"] == "classical" else "qsnet"
        for metric in ("accuracy", "macro_f1", "auroc_ovr_macro"):
            s[f"tableA/{r['dataset']}/{tag}/{metric}"] = r[metric]
    for m in t["mcnemar"]:
        s[f"mcnemar/{m['dataset']}/p_holm"] = m["p_holm"]
    for c in t["coverage_all_seed"]:
        s[f"allseed/{c['dataset']}/mean_fzr"] = c["mean_fzr"]
    for pc in t["per_class_fzr"]:
        s[f"perclass/{pc['dataset']}/n_out_of_band"] = pc["n_out_of_band"]
    for p in f["points"]:
        s[f"fig2/{p['dataset']}/mean_fzr"] = p["mean_fzr"]
    return s


# ---------------------------------------------------------------- freeze / verify / reproduce

def _load_ondisk_results():
    """Load the three mains' JSON outputs from disk — for regenerate=False. Lets freeze() pin the
    already-committed full-trio artefacts WITHOUT re-running the mains, so a partial-dataset call (e.g. a
    test freezing CIC only) can never overwrite the committed 3-dataset reports/figure on disk. The main
    JSONs ARE the mains' return dicts (each is `json.dump(out)`), so key_scalars reads them unchanged."""
    out = []
    for rel in ("w5_01_disentanglement.json", "w5_02_table_a.json", "w5_03_figure2.json"):
        p = BASE / "week5" / "reports" / "_generated" / rel
        if not p.exists():
            raise SystemExit(f"regenerate=False but {rel} is absent — run the mains first "
                             f"(or freeze with regenerate=True).")
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return tuple(out)


def freeze(datasets, alpha, scores_root, source, regenerate=True):
    RESULTS.mkdir(parents=True, exist_ok=True)
    if regenerate:
        log("running the three Day-26/27 result mains (deterministic, seed 42) ...")
        d, t, f = run_all(datasets, alpha, scores_root, source)
    else:
        log("regenerate=False — pinning the existing on-disk artefacts (mains NOT re-run)")
        d, t, f = _load_ondisk_results()
    scalars = key_scalars(d, t, f)

    missing = [rel for rel in PINNED if not (BASE / rel).exists()]
    if missing:
        for m in missing:
            log(f"  ERROR missing result artefact: {m}")
        raise SystemExit(f"freeze aborted — {len(missing)} artefact(s) absent (did a main fail?)")

    recs = []
    for rel in PINNED:
        p = BASE / rel
        _assert_lf(p)                              # LF gate — refuse to freeze a CRLF text blob
        recs.append({"path": rel, "sha256": _sha256(p), "bytes": p.stat().st_size, "rows": _rows(p)})

    (SCALARS).write_text(json.dumps({"version": VERSION, "seed": SEED, "primary_alpha": alpha,
                                     "source_kind": source, "n_scalars": len(scalars),
                                     "scalars": scalars}, indent=1), encoding="utf-8")
    total = sum(r["bytes"] for r in recs)
    manifest = {
        "package": "QS-Net / QuantumSentinel — Team A — Week-5 RESULTS freeze",
        "version": VERSION, "day": 26, "seed": SEED,
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "primary_alpha": alpha, "source_kind": source, "benchmark_trio": list(datasets),
        "scope": "Day-26/27 result artefacts (RQ1 Table A, RQ3 disentanglement AUROC, Figure 2 coverage "
                 "headline) + the three result modules. frozen_utc is metadata, NOT part of --verify. "
                 "Every quantum number is PROVISIONAL on the Day-14 dummy interface unless source=real.",
        "reproducibility": "python week5/scripts/freeze_results.py --reproduce  (re-runs the mains, asserts "
                           "every scalar in results_frozen_scalars.json to 1e-9)",
        "n_scalars_pinned": len(scalars),
        "n_files": len(recs), "total_bytes": total, "files": recs,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    (RESULTS / "VERSION").write_text(
        f"QS-Net Team A — Week-5 RESULTS freeze\nversion: {VERSION}\nseed: {SEED}\n"
        f"primary_alpha: {alpha}\nsource: {source}\ntrio: {', '.join(datasets)}\n"
        f"files: {len(recs)}  bytes: {total}  scalars: {len(scalars)}\n"
        f"manifest: RESULTS_FROZEN/{MANIFEST.name}\n", encoding="utf-8")
    _write_index(manifest, scalars, source)
    log(f"RESULTS FREEZE v{VERSION}: pinned {len(recs)} files ({total/1e3:.1f} kB) + {len(scalars)} "
        f"scalars, source={source}")
    return manifest


def verify():
    if not MANIFEST.exists():
        print(f"NO RESULTS MANIFEST at {MANIFEST.relative_to(BASE)} — run without --verify first.")
        return 2
    pinned = {r["path"]: r for r in json.loads(MANIFEST.read_text())["files"]}
    missing, changed = [], []
    for rel, rec in pinned.items():
        p = BASE / rel
        if not p.exists():
            missing.append(rel)
        elif _sha256(p) != rec["sha256"]:
            changed.append(rel)
    for p in missing:
        print(f"  MISSING  {p}")
    for p in changed:
        print(f"  CHANGED  {p}")
    if not missing and not changed:
        print(f"RESULTS VERIFY OK — {len(pinned)} files, 0 mismatch.")
        return 0
    print(f"RESULTS VERIFY FAILED — {len(missing)} missing, {len(changed)} changed.")
    return 1


def reproduce_check(datasets, alpha, scores_root, source, tol=1e-9):
    """Re-run the three mains and assert every frozen scalar comes back within `tol`."""
    if not SCALARS.exists():
        print(f"NO FROZEN SCALARS at {SCALARS.relative_to(BASE)} — run the freeze first.")
        return 2
    frozen = json.loads(SCALARS.read_text())["scalars"]
    log("re-running the three mains for the reproducibility check ...")
    d, t, f = run_all(datasets, alpha, scores_root, source)
    now = key_scalars(d, t, f)

    mism = []
    for k, v in frozen.items():
        if k not in now:
            mism.append((k, v, "MISSING")); continue
        a, b = now[k], v
        if a is None or b is None:
            if a is not b:
                mism.append((k, b, a))
        elif abs(float(a) - float(b)) > tol:
            mism.append((k, b, a))
    for k, exp, got in mism:
        print(f"  MISMATCH  {k}: frozen={exp} reproduced={got}")
    if not mism:
        print(f"RESULTS REPRODUCE OK — {len(frozen)} scalars, 0 mismatch (tol {tol:g}).")
        return 0
    print(f"RESULTS REPRODUCE FAILED — {len(mism)}/{len(frozen)} scalars differ.")
    return 1


def _write_index(manifest, scalars, source):
    prov = " · **PROVISIONAL** (Day-14 dummy interface)" if source == "dummy" else ""
    L = [f"# RESULTS_FROZEN — QS-Net Team A · Week-5 results · **v{manifest['version']}**", "",
         f"**RESULTS FREEZE (Day 26).** Seed {manifest['seed']} · primary α = {manifest['primary_alpha']} "
         f"· source `{manifest['source_kind']}`{prov} · trio {', '.join(manifest['benchmark_trio'])} · "
         f"{manifest['n_files']} files · {manifest['total_bytes']/1e3:.1f} kB · "
         f"{manifest['n_scalars_pinned']} scalars · frozen {manifest['frozen_utc']}.", "",
         "The Day-26/27 result surface the manuscript cites — RQ1 Table A, RQ3 disentanglement AUROC, and "
         "the Figure-2 coverage headline — SHA-256-pinned so the numbers stop moving during writing week. "
         f"Every file is listed in [`{MANIFEST.name}`]({MANIFEST.name}).", "",
         "```bash",
         "python week5/scripts/freeze_results.py --verify      # re-hash, expect 0 mismatch",
         "python week5/scripts/freeze_results.py --reproduce   # re-run the mains, expect 0 mismatch",
         "```", "",
         "## Contents",
         "- **disentanglement (RQ3):** `w5_01_disentanglement.{md,json,csv}` — separation AUROC panel.",
         "- **Table A (RQ1):** `w5_02_table_a.{md,json,csv}` + skeleton `.md`/`.tex` + "
         "`w5_02_per_class_fzr.csv`.",
         "- **Figure 2 (coverage headline):** `w5_03_figure2.{md,json}` + `w5_03_figure2_data.csv` + "
         "`figures/w5_fig2_coverage.png`.",
         "- **result modules:** `week5/scripts/{disentanglement,table_a,figure2_coverage}.py`.",
         "- **`results_frozen_scalars.json`** — the pinned headline scalars for `--reproduce`.", "",
         "## Gates",
         "- **LF gate.** The freeze refuses any pinned text file containing a CRLF; the repo-root "
         "`.gitattributes` (`* text=auto eol=lf`) keeps a fresh clone byte-identical so `--verify` passes "
         "off a clean checkout on any OS. Run the freeze on Linux.",
         f"- **Reproducibility.** `--reproduce` re-runs the three deterministic mains and asserts all "
         f"{manifest['n_scalars_pinned']} pinned scalars return to 1e-9."]
    if source == "dummy":
        L += ["", "> **Provisional.** Every quantum number rides the Day-14 dummy fidelity interface. "
              "Re-cut as v1.1 on Team B's real prototypes: `--source real --scores-root <dir>`."]
    (RESULTS / "RESULTS_FROZEN.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Day-26 Week-5 results freeze — pin + confirm reproducibility")
    ap.add_argument("--datasets", nargs="+", default=list(TRIO))
    ap.add_argument("--alpha", type=float, default=PRIMARY_ALPHA)
    ap.add_argument("--scores-root", default=str(IFACE))
    ap.add_argument("--source", choices=["dummy", "real"], default="dummy")
    ap.add_argument("--verify", action="store_true", help="re-hash and diff against the freeze manifest")
    ap.add_argument("--reproduce", action="store_true",
                    help="re-run the three mains and assert every frozen scalar reproduces to 1e-9")
    ap.add_argument("--no-regenerate", action="store_true",
                    help="pin the existing on-disk artefacts without re-running the mains — freeze then "
                         "cannot overwrite the committed full-trio outputs with a partial run")
    args = ap.parse_args(argv)
    if args.verify:
        sys.exit(verify())
    if args.reproduce:
        sys.exit(reproduce_check(args.datasets, args.alpha, args.scores_root, args.source))
    freeze(args.datasets, args.alpha, args.scores_root, args.source, regenerate=not args.no_regenerate)


if __name__ == "__main__":
    main()
