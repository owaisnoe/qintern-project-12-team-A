"""Render the QADCP workflow diagram -> reports/figures/qadcp_workflow.png (Day 4).

Companion to reports/08_qadcp_design.md and scripts/qadcp.py. Pure matplotlib,
no graphviz dependency; regenerate after any pipeline change.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parents[1] / "reports" / "figures" / "qadcp_workflow.png"

INK, ACCENT, FIT, GATE = "#15304b", "#0b6e4f", "#8a4b08", "#8b1a1a"
STAGES = [  # (y, title, subtitle, kind)
    (0, "S0 · VALIDATE", "manifest SHA-256 --verify · schema contract · checkpoint invariants\n(0 NaN, 0 dup feature rows, clean labels)", "gate"),
    (1, "S1 · CLEAN  (= Day-3 preprocess.py)", "schema normalize · label harmonize · structural drops · '-'/blank→NaN\nimpute · encode · feature-space dedup (per-class dedup report)", "flow"),
    (2, "S2 · FEATURE ENGINEERING", "unified family label (10-family ontology) · derived binary\n+ Day-6: unified core features (duration/pkts/bytes/rate/state)", "flow"),
    (3, "S3 · FEATURE GROUPING", "semantic tags: timing · rate · volume · flags_state · protocol · ctx\n→ feature_groups.json (Team C selection, group-wise qubit allocation)", "flow"),
    (4, "S7a · SPLIT FIRST  (leakage-safe order)", "zero-day families → zeroday split ONLY (Mirai / ransomware / Theft / …)\nrest: stratified 70/10/10/10 → Train / Val / Calibration / Test", "flow"),
    (5, "S6a · CORR PRUNE  +  S7b · RESOLVE NEW DUPES", "drop one of each |r|≥0.95 pair (train-fit) — column drops re-create duplicates,\nnow across splits → keep 1 copy, priority train>val>cal>test>zeroday", "fit"),
    (6, "S4 · NORMALIZATION", "median/IQR robust scaling — params FIT ON TRAIN ONLY\n→ scalers.json → transform Val/Cal/Test/Zero-Day", "fit"),
    (7, "S5 · BALANCING  (train only)", "majority classes capped (20k) · rare classes 100% preserved\nVal/Cal/Test/Zero-Day NEVER balanced (true distributions)", "fit"),
    (8, "S6b · QUANTUM-READY PREP", "feature ranking (Team C refines) · nested qubit budgets 4/8/12/16\nangle encoding → [0, π] (train-fit min/max, others clipped) → q16_*.parquet", "fit"),
    (9, "S8 · ACCEPTANCE GATES + PACKAGE", "splits disjoint (hash check) · zero-day isolated from train/val/cal/test\nrare classes intact · 0 NaN · → qadcp_report.json + re-graded scorecard", "gate"),
]
KIND_FC = {"flow": "#eaf1f8", "fit": "#e8f5ef", "gate": "#fdeeee"}
KIND_EC = {"flow": INK, "fit": ACCENT, "gate": GATE}

fig, ax = plt.subplots(figsize=(11.5, 14))
ax.set_xlim(0, 10)
ax.set_ylim(-0.6, len(STAGES) * 1.5 + 1.2)
ax.axis("off")
ax.invert_yaxis()

ax.text(5.0, -0.35, "QADCP — Quantum-Aware Dataset Curation Pipeline (execution order)",
        ha="center", fontsize=15, fontweight="bold", color=INK)
ax.text(5.0, 0.05, "QS-Net · Team A · Day 4  —  capability list per task sheet; order rearranged so every "
        "parameter is fit on Train only", ha="center", fontsize=9.5, color="#555555")

for i, (row, title, sub, kind) in enumerate(STAGES):
    y = 0.7 + row * 1.5
    box = FancyBboxPatch((1.2, y), 7.6, 1.12, boxstyle="round,pad=0.06,rounding_size=0.12",
                         fc=KIND_FC[kind], ec=KIND_EC[kind], lw=1.8)
    ax.add_patch(box)
    ax.text(5.0, y + 0.30, title, ha="center", fontsize=11.5, fontweight="bold", color=KIND_EC[kind])
    ax.text(5.0, y + 0.78, sub, ha="center", fontsize=8.4, color="#333333")
    if i < len(STAGES) - 1:
        ax.add_patch(FancyArrowPatch((5.0, y + 1.22), (5.0, y + 1.48),
                                     arrowstyle="-|>", mutation_scale=18, color=INK, lw=1.6))

# fit-on-train bracket around S6a-S6b
yb0, yb1 = 0.7 + 5 * 1.5 - 0.12, 0.7 + 8 * 1.5 + 1.24
ax.plot([9.15, 9.35, 9.35, 9.15], [yb0, yb0, yb1, yb1], color=FIT, lw=2)
ax.text(9.55, (yb0 + yb1) / 2, "fit on TRAIN only →\ntransform all splits\n(scalers.json persists params)",
        rotation=90, va="center", ha="center", fontsize=9, color=FIT, fontweight="bold")

# side note: entry points
ax.text(0.55, 0.7 + 1.5 * 1 + 0.56,
        "raw 41 GB (manifest-pinned)\n—or—\nDay-3 checkpoint *_clean.parquet",
        rotation=90, va="center", ha="center", fontsize=8.2, color="#555555")

# outputs strip
yo = 0.7 + len(STAGES) * 1.5 + 0.05
ax.text(5.0, yo + 0.25,
        "datasets/<name>/qadcp/ :  train · val · calibration · test · zeroday · train_balanced  (.parquet)\n"
        "+ quantum/q16_*.parquet ([0,π] angle-ready) · scalers.json · feature_groups.json · "
        "qubit_budgets.json · qadcp_report.json",
        ha="center", fontsize=9, color=INK,
        bbox=dict(boxstyle="round,pad=0.5", fc="#f7f7f2", ec=INK, lw=1.2))

OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=160, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT}")
