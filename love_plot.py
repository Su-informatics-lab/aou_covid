#!/usr/bin/env python3
"""
Generate eFigure 1: Full-covariate Love plot (post-matching |SMD|).
Reads 07d_smd_post_matching.csv for AoU and MarketScan.

Usage:
  python efig1_love_plot.py

Outputs:
  results/figures/efig1_love_plot.pdf
  results/figures/efig1_love_plot.png
"""

import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ── Nature / JAMIA style ──────────────────────────────────────────────
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42
mpl.rcParams["font.family"] = "sans-serif"
mpl.rcParams["font.sans-serif"] = ["Arial", "Helvetica", "DejaVu Sans"]
mpl.rcParams["font.size"] = 7
mpl.rcParams["axes.labelsize"] = 7
mpl.rcParams["axes.titlesize"] = 7
mpl.rcParams["xtick.labelsize"] = 6
mpl.rcParams["ytick.labelsize"] = 6
mpl.rcParams["legend.fontsize"] = 6
mpl.rcParams["axes.linewidth"] = 0.5
mpl.rcParams["xtick.major.width"] = 0.5
mpl.rcParams["ytick.major.width"] = 0.5
mpl.rcParams["xtick.direction"] = "out"
mpl.rcParams["ytick.direction"] = "out"
mpl.rcParams["axes.spines.top"] = False
mpl.rcParams["axes.spines.right"] = False
mpl.rcParams["axes.grid"] = False
mpl.rcParams["legend.frameon"] = False
mpl.rcParams["figure.facecolor"] = "white"
mpl.rcParams["savefig.facecolor"] = "white"
mpl.rcParams["savefig.dpi"] = 600
mpl.rcParams["savefig.bbox"] = "tight"
mpl.rcParams["savefig.pad_inches"] = 0.02

# Wong/Okabe-Ito palette
COLORS = {
    "Matching": "#E69F00",  # orange/amber
    "Demographics": "#56B4E9",  # sky blue
    "Clinical": "#009E73",  # bluish green
    "Comorbidities": "#0072B2",  # blue
    "SDoH": "#D55E00",  # vermillion
}

# ── Pretty variable labels ────────────────────────────────────────────
LABEL_MAP = {
    "sex_at_birth: Female": "Female",
    "sex_at_birth: Male": "Male",
    "age_group: <45": "Age <45",
    "age_group: 45-54": "Age 45–54",
    "age_group: 55-64": "Age 55–64",
    "age_group: 65+": "Age ≥65",
    "race: White": "White",
    "race: Black": "Black",
    "race: Asian": "Asian",
    "race: Other": "Other race",
    "ethnicity: Not Hispanic": "Not Hispanic",
    "ethnicity: Hispanic": "Hispanic",
    "ethnicity: Other": "Other ethnicity",
    "Vaccinated": "Vaccinated",
    "Wave: pre_delta": "Pre-Delta",
    "Wave: delta": "Delta",
    "Wave: omicron": "Omicron",
    "Myocardial Infarction": "MI",
    "Congestive Heart Failure": "CHF",
    "Peripheral Vascular Disease": "PVD",
    "Cerebrovascular Disease": "Cerebrovascular",
    "Chronic Pulmonary Disease": "Pulmonary",
    "Rheumatic Disease": "Rheumatic",
    "Peptic Ulcer Disease": "Peptic ulcer",
    "Liver Disease Mild": "Liver (mild)",
    "Liver Disease Moderate Severe": "Liver (mod/severe)",
    "Diabetes without Chronic Complications": "DM w/o complic.",
    "Diabetes with Chronic Complications": "DM w/ complic.",
    "Hemiplegia Paraplegia": "Hemiplegia",
    "Renal Disease Mild Moderate": "Renal (mild/mod)",
    "Renal Disease Severe": "Renal (severe)",
    "Metastatic Solid Tumor": "Metastatic tumor",
    "insurance_type: Employer": "Ins: Employer",
    "insurance_type: Medicare": "Ins: Medicare",
    "insurance_type: Medicaid": "Ins: Medicaid",
    "insurance_type: Other_None": "Ins: Other/None",
    "income: less_10k": "Income <$10K",
    "income: 10k_25k": "Income $10–25K",
    "income: 25k_35k": "Income $25–35K",
    "income: 35k_100k": "Income $35–100K",
    "income: 100k_150k": "Income $100–150K",
    "income: 150k_200k": "Income $150–200K",
    "income: more_200k": "Income >$200K",
    "education: Below_GED": "Edu: Below GED",
    "education: GED_or_College": "Edu: GED/College",
    "education: Advanced": "Edu: Advanced",
    "employment: Employed": "Employed",
    "employment: Unemployed": "Unemployed",
    "employment: Others": "Retired/other",
    "housing: Own": "Own home",
    "housing: Rent": "Rent",
    "housing_stability: Stable": "Housing stable",
    "housing_stability: Unstable": "Housing unstable",
    "disability_any: Yes": "Disability: Yes",
    "disability_any: No": "Disability: No",
    # MS-specific
    "plan_type: PPO": "Plan: PPO",
    "plan_type: HMO": "Plan: HMO",
    "plan_type: POS": "Plan: POS",
    "plan_type: HDHP": "Plan: HDHP",
    "plan_type: CDHP": "Plan: CDHP",
    "plan_type: EPO": "Plan: EPO",
    "plan_type: Comprehensive": "Plan: Comprehensive",
    "plan_type: Basic": "Plan: Basic",
    "plan_type: Unknown": "Plan: Unknown",
    "region: South": "Region: South",
    "region: NorthCentral": "Region: NorthCentral",
    "region: West": "Region: West",
    "region: Northeast": "Region: Northeast",
    "region: Unknown": "Region: Unknown",
}


def plot_love(ax, df, title, panel_label):
    """Plot a Love plot on a given axes."""
    # Sort by group then abs_smd descending
    group_order = ["SDoH", "Comorbidities", "Clinical", "Demographics"]
    df = df.copy()
    df["group_rank"] = (
        df["group"].map({g: i for i, g in enumerate(group_order)}).fillna(99)
    )
    df = df.sort_values(["group_rank", "abs_smd"], ascending=[True, True])
    df = df.reset_index(drop=True)

    # Pretty labels
    df["label"] = df["variable"].map(LABEL_MAP).fillna(df["variable"])

    y = np.arange(len(df))

    for grp in df["group"].unique():
        mask = df["group"] == grp
        color = COLORS.get(grp, "#999999")
        ax.scatter(
            df.loc[mask, "abs_smd"],
            y[mask],
            c=color,
            s=14,
            zorder=3,
            label=grp,
            edgecolors="none",
            alpha=0.85,
        )

    # Threshold lines
    ax.axvline(0.10, color="#333333", linestyle="--", linewidth=0.6, zorder=1)
    ax.axvline(0.05, color="#999999", linestyle=":", linewidth=0.5, zorder=1)

    ax.set_yticks(y)
    ax.set_yticklabels(df["label"], fontsize=5.5)
    ax.set_xlabel("|Standardized Mean Difference|")
    ax.set_xlim(-0.01, None)
    ax.set_ylim(-0.8, len(df) - 0.2)

    # Panel label
    ax.text(
        -0.02,
        1.02,
        panel_label,
        transform=ax.transAxes,
        fontsize=8,
        fontweight="bold",
        va="bottom",
        ha="right",
    )
    ax.set_title(title, fontsize=7, pad=4)

    # Legend (deduplicated, ordered)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ordered = [g for g in group_order if g in by_label]
    ax.legend(
        [by_label[g] for g in ordered],
        ordered,
        loc="lower right",
        fontsize=5.5,
        markerscale=1.2,
    )

    # Annotate threshold lines
    ax.text(0.10, len(df) - 0.5, "|SMD| = 0.10", fontsize=5, ha="left", color="#333333")
    ax.text(0.05, len(df) - 1.2, "0.05", fontsize=5, ha="left", color="#999999")


# ── Main ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    aou_path = "results/aou_v7/07d_smd_post_matching.csv"
    ms_path = "results/ms/07d_smd_post_matching.csv"
    out_dir = "results/figures"
    os.makedirs(out_dir, exist_ok=True)

    aou = pd.read_csv(aou_path)
    ms = pd.read_csv(ms_path)

    # Calculate figure height based on number of variables
    n_aou = len(aou)
    n_ms = len(ms)
    h_per_row = 0.16
    fig_h = max(n_aou, n_ms) * h_per_row + 0.8

    fig, (ax1, ax2) = plt.subplots(
        1,
        2,
        figsize=(7.205, fig_h),  # double-column width
        gridspec_kw={"wspace": 0.55},
    )

    plot_love(ax1, aou, "All of Us", "a")
    plot_love(ax2, ms, "MarketScan", "b")

    fig.savefig(os.path.join(out_dir, "efig1_love_plot.pdf"), format="pdf")
    fig.savefig(os.path.join(out_dir, "efig1_love_plot.png"), format="png", dpi=600)
    print(f"Saved: {out_dir}/efig1_love_plot.pdf and .png")
    print(f"  AoU: {n_aou} variables, max |SMD| = {aou.abs_smd.max():.3f}")
    print(f"  MS:  {n_ms} variables, max |SMD| = {ms.abs_smd.max():.3f}")
    plt.close()
