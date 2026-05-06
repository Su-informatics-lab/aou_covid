#!/usr/bin/env python3
"""
COVID-19 Severity x SDoH — Figure 5: Wave-Stratified Income Forest Plot

Generates a hierarchical forest plot showing the persistence of the
lower-income association with COVID-19 hospitalization across pandemic
waves. Three lower-income strata (<$10K, $10-25K, $25-35K) within each
of three waves (pre-Delta, Delta, Omicron), AORs with 95% CIs.

Reads:
    results/aou_v7/wave_stratified_income.csv   (from 02_models.R)
    results/aou_v7/06_matched_cohort.csv        (for case counts per wave)
    results/aou_v7/01_covid_cohort.csv          (for wave assignment)

Outputs:
    results/figures/fig5_wave_income.pdf
    results/figures/fig5_wave_income.png

Usage:
    python 04b_fig5_wave.py                  # default: results/
    python 04b_fig5_wave.py /path/to/results

Style: JAMIA / Nature Portfolio (Arial 7pt, 600 DPI, Wong/Okabe-Ito palette).
License: MIT
"""

import os
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.transforms import blended_transform_factory

# ── JAMIA / Nature-style rcParams (match 04_figures.py) ───────────────
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42
mpl.rcParams["font.family"] = "sans-serif"
mpl.rcParams["font.sans-serif"] = ["Arial", "Helvetica", "DejaVu Sans"]
mpl.rcParams["font.size"] = 7
mpl.rcParams["axes.labelsize"] = 7
mpl.rcParams["axes.titlesize"] = 8
mpl.rcParams["xtick.labelsize"] = 6
mpl.rcParams["ytick.labelsize"] = 7
mpl.rcParams["legend.fontsize"] = 6
mpl.rcParams["axes.linewidth"] = 0.5
mpl.rcParams["xtick.major.width"] = 0.5
mpl.rcParams["ytick.major.width"] = 0.5
mpl.rcParams["xtick.major.size"] = 3
mpl.rcParams["ytick.major.size"] = 3
mpl.rcParams["xtick.direction"] = "out"
mpl.rcParams["ytick.direction"] = "out"
mpl.rcParams["lines.linewidth"] = 1.0
mpl.rcParams["lines.markersize"] = 4
mpl.rcParams["legend.frameon"] = False
mpl.rcParams["axes.grid"] = False
mpl.rcParams["axes.spines.top"] = False
mpl.rcParams["axes.spines.right"] = False
mpl.rcParams["figure.facecolor"] = "white"
mpl.rcParams["savefig.facecolor"] = "white"
mpl.rcParams["savefig.dpi"] = 600
mpl.rcParams["savefig.bbox"] = "tight"
mpl.rcParams["savefig.pad_inches"] = 0.05

# Wong/Okabe-Ito palette
C_RISK = "#D55E00"  # vermillion — significant risk
C_PROTECT = "#0072B2"  # blue — significant protective
C_NS = "#999999"  # grey — non-significant

# Widths (Nature standard)
W_DOUBLE = 7.205  # 183 mm

# ── Paths ─────────────────────────────────────────────────────────────
BASE = sys.argv[1] if len(sys.argv) > 1 else "results"
INPUT = os.path.join(BASE, "aou_v7", "wave_stratified_income.csv")
MATCHED = os.path.join(BASE, "aou_v7", "06_matched_cohort.csv")
COHORT = os.path.join(BASE, "aou_v7", "01_covid_cohort.csv")
FIG_DIR = os.path.join(BASE, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# ── Load & validate ───────────────────────────────────────────────────
if not os.path.exists(INPUT):
    print(f"ERROR: {INPUT} not found.")
    print(
        "       Run: Rscript 02_models.R aou_v7   (produces wave_stratified_income.csv)"
    )
    sys.exit(1)

df = pd.read_csv(INPUT)
print(f"Loaded {len(df)} rows from {INPUT}")

# Compute per-wave case counts (for panel labels)
wave_n = {}
if os.path.exists(MATCHED) and os.path.exists(COHORT):
    matched = pd.read_csv(MATCHED)
    cohort = pd.read_csv(COHORT)
    mw = matched.merge(cohort[["person_id", "pandemic_wave"]], on="person_id")
    wave_n = mw[mw.Treatment == 1].pandemic_wave.value_counts().to_dict()
    print(f"Per-wave case counts: {wave_n}")
else:
    print("(matched cohort / cohort CSVs not found; panel labels will omit N)")

# ── Mappings ──────────────────────────────────────────────────────────
INCOME_LABELS = {
    "f.incomeless_10k": "<$10,000",
    "f.income10k_25k": "$10,000\u201324,999",
    "f.income25k_35k": "$25,000\u201334,999",
}
WAVE_LABELS = {
    "pre_delta": "Pre-Delta",
    "delta": "Delta",
    "omicron": "Omicron",
}
WAVES_ORDER = ["pre_delta", "delta", "omicron"]
INCOMES_ORDER = ["f.incomeless_10k", "f.income10k_25k", "f.income25k_35k"]

# ── Filter to lower-income strata ─────────────────────────────────────
df = df[df["variable"].isin(INCOMES_ORDER) & df["wave"].isin(WAVES_ORDER)].copy()
if len(df) == 0:
    print("ERROR: no rows match the expected income strata after filtering.")
    sys.exit(1)

# ── Build hierarchical layout (waves as groups, incomes within) ───────
plot_rows, y_labels, group_spans = [], [], []
y = 0
for gi, w in enumerate(WAVES_ORDER):
    y_start = y
    n_in_group = 0
    for inc in INCOMES_ORDER:
        sub = df[(df["variable"] == inc) & (df["wave"] == w)]
        if len(sub) == 0:
            continue
        r = sub.iloc[0]
        plot_rows.append(
            {
                "y": y,
                "aor": float(r.AOR),
                "lo": float(r.CI_lower),
                "hi": float(r.CI_upper),
                "p": float(r.p_value),
            }
        )
        y_labels.append("  " + INCOME_LABELS[inc])
        y += 1
        n_in_group += 1
    if n_in_group == 0:
        continue
    label = WAVE_LABELS[w]
    if w in wave_n:
        label += f" (N={wave_n[w]:,} cases)"
    group_spans.append((label, y_start, y - 1, gi))
    y += 0.4

max_y = y - 0.4
positions = [max_y - r["y"] for r in plot_rows]

# ── Plot ──────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(W_DOUBLE, 4.0))

# Alternating gray bands per wave group
for grp, ys, ye, gi in group_spans:
    if gi % 2 == 0:
        ax.axhspan(max_y - ye - 0.45, max_y - ys + 0.45, color="#F5F5F5", zorder=0)
    y_mid = max_y - (ys + ye) / 2
    ax.text(
        -0.14,
        y_mid,
        grp,
        fontsize=7.5,
        fontweight="bold",
        ha="right",
        va="center",
        transform=ax.get_yaxis_transform(),
        color="#333333",
    )

# Points + CIs
for i, r in enumerate(plot_rows):
    c = (
        C_RISK
        if (r["p"] < 0.05 and r["aor"] > 1)
        else (C_PROTECT if (r["p"] < 0.05 and r["aor"] < 1) else C_NS)
    )
    ax.errorbar(
        r["aor"],
        positions[i],
        xerr=[[r["aor"] - r["lo"]], [r["hi"] - r["aor"]]],
        fmt="o",
        color=c,
        ecolor=c,
        elinewidth=0.8,
        capsize=2,
        capthick=0.6,
        markersize=4.5,
        markeredgecolor="black",
        markeredgewidth=0.3,
        zorder=3,
    )

# Reference line at AOR = 1
ax.axvline(1.0, color="black", linewidth=0.5, linestyle="-", zorder=1)

# Y-axis: income strata labels
ax.set_yticks(positions)
ax.set_yticklabels(y_labels, fontsize=7.5)

# X-axis: log AOR
ax.set_xlabel("Adjusted Odds Ratio (95% CI), reference $35,000\u201399,999", fontsize=8)
ax.set_xscale("log")
ax.set_xlim(0.55, 4.5)
ax.set_xticks([0.6, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0])
ax.get_xaxis().set_major_formatter(mpl.ticker.ScalarFormatter())

# Numeric annotations to the right of each row
tt = blended_transform_factory(ax.transAxes, ax.transData)
for i, r in enumerate(plot_rows):
    sig = "\u2020" if r["p"] < 0.05 else ""
    ax.text(
        1.02,
        positions[i],
        f'{r["aor"]:.2f} ({r["lo"]:.2f}\u2013{r["hi"]:.2f}){sig}',
        va="center",
        ha="left",
        fontsize=7,
        family="monospace",
        transform=tt,
    )

# ── Save ──────────────────────────────────────────────────────────────
for ext in ["pdf", "png"]:
    out = os.path.join(FIG_DIR, f"fig5_wave_income.{ext}")
    fig.savefig(out)
    print(f"  Saved: {out}")
plt.close(fig)
