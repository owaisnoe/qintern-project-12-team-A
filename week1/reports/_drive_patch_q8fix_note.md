# Drive patch — quantum label fix (Jul 2026)

**Upload this folder's contents into your existing Team A / Week 1 Drive tree** — merge/overwrite, don't replace the whole Week 1 folder.

## What changed

- Fixed NaN labels in `quantum/q{4,8,12,16}_*.parquet` (Day 4 `qadcp.py` bug)
- Updated manifest hashes
- Added `validate_pipeline.py` `quantum_labels` gate
- New mentor note: `reports/17_unified_collapse_mentor_note.md`
- **Mentor decision:** benchmark locked to **CIC + BoT + UNSW**; TON/Edge set aside
- Updated: `reports/11_qsnet_interface.md`, `reports/14_handover_report.md`, `METADATA.md`

## How to upload (~250 MB, 255 files)

1. Open Google Drive → **Team A / Week 1** (your existing folder).
2. Drag the subfolders below from this patch into Week 1 and choose **Replace** when prompted:

| Drag this | Into Drive |
|-----------|------------|
| `datasets/` | `Week 1/datasets/` (overwrites `*/qadcp/quantum/` and `*/unified/qadcp/quantum/` only) |
| `manifest/` | `Week 1/manifest/` |
| `scripts/` | `Week 1/scripts/` |
| `reports/17_unified_collapse_mentor_note.md` | `Week 1/reports/` |
| `reports/11_qsnet_interface.md` | `Week 1/reports/` (overwrite) |
| `reports/14_handover_report.md` | `Week 1/reports/` (overwrite) |
| `METADATA.md` | `Week 1/` (overwrite) |

3. Tell Team B to re-sync and run:
   ```bash
   python week1/scripts/make_manifest.py --verify   # expect: 0 mismatch
   ```

## Folder layout

```
drive_upload_patch/
├── README.md                 ← this file
├── datasets/
│   └── <name>/
│       ├── qadcp/quantum/          # v0.1 — fixed q4/q8/q12/q16/pca8_*
│       └── unified/qadcp/quantum/    # v1.0 — fixed q4/q8/q12/q16/pca8_*
├── manifest/
│   ├── MANIFEST.md
│   └── manifest.json
├── scripts/
│   ├── qadcp.py
│   └── validate_pipeline.py
└── reports/
    └── 17_unified_collapse_mentor_note.md
```

## Not in this patch (unchanged — no re-upload needed)

- `datasets/*/processed/`, parent `qadcp/*.parquet` (train/zeroday/etc.)
- Reports 00–16, figures, dashboard, raw data

## Still open (not fixed here)

~~TON/Edge unified zeroday collapse~~ — **resolved:** mentor locked benchmark to **CIC + BoT + UNSW**; TON/Edge set aside. See `reports/17_unified_collapse_mentor_note.md`.
