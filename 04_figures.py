#!/usr/bin/env python3
"""
COVID-19 Severity × SDoH — Publication Figures & Tables
Generates all display items from coefficient CSVs (no PII needed).

Usage: python 04_figures.py                 # default results/ directory
       python 04_figures.py /path/to/dir    # custom location

Inputs:  results/aou_v7/all_model_coefficients.csv
         results/ms/all_model_coefficients.csv  (optional)
Outputs: results/figures/fig1_consort.pdf
         results/figures/fig2_base_forest.pdf
         results/figures/fig3_sdoh_forest.pdf
         results/tables/table3_sdoh_summary.csv
         results/tables/etable_ms_comparison.csv
         results/tables/consort_counts.csv

Figure specs: JAMIA (OUP) + Nature Portfolio style
  - Arial/Helvetica, 7 pt body, 6 pt ticks
  - Panel labels: bold lowercase (a, b)
  - 600 DPI, PDF + PNG export
  - Wong/Okabe-Ito colorblind-safe palette
  - No gridlines, minimal spines
"""

import os
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.transforms import blended_transform_factory

# ── JAMIA / Nature-style rcParams ─────────────────────────────────────
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

# Wong/Okabe-Ito colorblind-safe palette
C_RISK = "#D55E00"  # vermillion — significant risk
C_PROTECT = "#0072B2"  # blue — significant protective
C_NS = "#999999"  # grey — non-significant
C_BOX = "#4477AA"  # box fill for CONSORT
C_BOX_EX = "#CC6677"  # exclusion boxes

# ── Widths (Nature standard) ──────────────────────────────────────────
W_SINGLE = 3.504  # 89 mm
W_DOUBLE = 7.205  # 183 mm
W_1_5 = 4.724  # 120 mm
MAX_H = 9.724  # 247 mm

# ── Paths ─────────────────────────────────────────────────────────────
BASE = sys.argv[1] if len(sys.argv) > 1 else "results"
FIG_DIR = os.path.join(BASE, "figures")
TBL_DIR = os.path.join(BASE, "tables")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(TBL_DIR, exist_ok=True)

# ── Load data ─────────────────────────────────────────────────────────
aou_path = os.path.join(BASE, "aou_v7", "all_model_coefficients.csv")
ms_path = os.path.join(BASE, "ms", "all_model_coefficients.csv")

aou = pd.read_csv(aou_path)
print(f"AoU v7: {len(aou)} rows, {aou.model.nunique()} models")

has_ms = os.path.exists(ms_path)
if has_ms:
    ms = pd.read_csv(ms_path)
    print(f"MarketScan: {len(ms)} rows, {ms.model.nunique()} models")


def save_fig(fig, name):
    for ext in ["pdf", "png"]:
        fig.savefig(os.path.join(FIG_DIR, f"{name}.{ext}"))
    print(f"  Saved: {FIG_DIR}/{name}.pdf/.png")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════
# FIGURE 1: CONSORT — Use fig1_consort.drawio (draw.io) instead.
# The matplotlib CONSORT is commented out; draw.io produces cleaner
# flow diagrams with editable text.
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("FIGURE 1: CONSORT — skipped (use fig1_consort.drawio)")
print("=" * 60)


"""  # CONSORT code commented out — use fig1_consort.drawio instead
    box = FancyBboxPatch(
        (x - w / 2, y - h / 2),
        w,
        h,
        boxstyle="round,pad=0.02",
        facecolor=color,
        edgecolor="black",
        linewidth=0.5,
        alpha=0.15,
        zorder=1,
    )
    ax.add_patch(box)
    # Border
    box2 = FancyBboxPatch(
        (x - w / 2, y - h / 2),
        w,
        h,
        boxstyle="round,pad=0.02",
        facecolor="none",
        edgecolor="black",
        linewidth=0.5,
        zorder=2,
    )
    ax.add_patch(box2)
    ax.text(
        x,
        y,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight="bold" if bold else "normal",
        zorder=3,
        wrap=True,
        linespacing=1.3,
    )


def draw_arrow(ax, x1, y1, x2, y2):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", color="black", lw=0.7),
    )


def draw_consort_panel(ax, data, title, panel_label):
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylim(-0.1, 1.1)
    ax.axis("off")
    ax.set_title(title, fontsize=8, fontweight="bold", pad=8)
    ax.text(
        -0.02,
        1.08,
        panel_label,
        fontsize=9,
        fontweight="bold",
        transform=ax.transAxes,
        va="top",
    )

    bw, bh = 0.55, 0.11  # box width, height

    # Top: total
    draw_box(ax, 0.5, 1.0, bw, bh, data["top"], fontsize=5.5, bold=True)

    # Exclusion (right side)
    if "exclude" in data:
        draw_box(ax, 1.2, 0.82, 0.45, bh, data["exclude"], color=C_BOX_EX, fontsize=5)
        draw_arrow(ax, 0.5, 1.0 - bh / 2, 0.5, 0.82 + bh / 2 + 0.02)
        ax.annotate(
            "",
            xy=(0.97, 0.82),
            xytext=(0.77, 0.82),
            arrowprops=dict(arrowstyle="->", color="black", lw=0.5),
        )

    # COVID positive
    y_covid = 0.72 if "exclude" not in data else 0.64
    draw_box(ax, 0.5, y_covid, bw, bh, data["covid"], fontsize=5.5)
    draw_arrow(
        ax,
        0.5,
        (1.0 if "exclude" not in data else 0.82) - bh / 2,
        0.5,
        y_covid + bh / 2 + 0.02,
    )

    # Split: cases / controls
    y_split = y_covid - 0.22
    draw_box(ax, 0.15, y_split, 0.4, bh, data["cases"], fontsize=5.5)
    draw_box(ax, 0.85, y_split, 0.4, bh, data["controls"], fontsize=5.5)
    draw_arrow(ax, 0.35, y_covid - bh / 2, 0.15, y_split + bh / 2 + 0.02)
    draw_arrow(ax, 0.65, y_covid - bh / 2, 0.85, y_split + bh / 2 + 0.02)

    # PSM
    y_psm = y_split - 0.18
    draw_box(ax, 0.5, y_psm, bw + 0.15, bh, data["psm"], fontsize=5.5, bold=True)
    draw_arrow(ax, 0.15, y_split - bh / 2, 0.5, y_psm + bh / 2 + 0.02)
    draw_arrow(ax, 0.85, y_split - bh / 2, 0.5, y_psm + bh / 2 + 0.02)

    # Final
    y_final = y_psm - 0.18
    draw_box(ax, 0.5, y_final, bw + 0.15, bh, data["final"], fontsize=5.5, bold=True)
    draw_arrow(ax, 0.5, y_psm - bh / 2, 0.5, y_final + bh / 2 + 0.02)


aou_data = {
    "top": "AoU participants\nN = 413,457",
    "exclude": "Excluded: no EHR or\nBasics Survey\nn = 161,410",
    "covid": "COVID-19 positive\nn = 25,160",
    "cases": "Hospitalized ≤30d\n(cases)\nn = 6,531 (26.0%)",
    "controls": "Outpatient only\n(controls)\nn = 18,629 (74.0%)",
    "psm": "PSM 1:4, caliper = 0.112\ndropped = 0",
    "final": "Matched cohort\n32,606 obs (6,531 strata)",
}

ms_data = {
    "top": "MarketScan enrolled\nN ≈ 23.3M (2020)",
    "covid": "COVID-19 positive (U07.1)\nn = 4,423,200",
    "cases": "Hospitalized\n(cases)\nn = 149,796 (3.4%)",
    "controls": "Outpatient only\n(controls)\nn = 4,273,404 (96.6%)",
    "psm": "PSM 1:4, caliper-based\ndropped = 4",
    "final": "Matched cohort\n748,857 obs (149,773 strata)",
}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(W_DOUBLE, 4.5))
draw_consort_panel(ax1, aou_data, "All of Us Research Program", "a")
draw_consort_panel(ax2, ms_data, "MarketScan Commercial Claims", "b")
plt.subplots_adjust(wspace=0.15)
save_fig(fig, "fig1_consort")
"""  # end CONSORT comment block


# ══════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════
# FIGURE 2: BASE MODEL FOREST PLOT (hierarchical labels + gray bands)
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("FIGURE 2: Base Model Forest Plot")
print("=" * 60)

base = aou[aou.model == "base"].copy()

BASE_GROUPS = [
    ("Sex", [("f.sexFemale", "Female"), ("f.sexOther", "Other")]),
    (
        "Age",
        [
            ("f.age45-54", "45\u201354"),
            ("f.age55-64", "55\u201364"),
            ("f.age65+", "\u226565"),
        ],
    ),
    ("Vaccination", [("f.vaccVaccinated", "Vaccinated")]),
    (
        "Race",
        [("f.raceBlack", "Black"), ("f.raceAsian", "Asian"), ("f.raceOther", "Other")],
    ),
    ("Ethnicity", [("f.ethnicityHispanic", "Hispanic"), ("f.ethnicityOther", "Other")]),
    (
        "Comorbidities",
        [
            ("Cerebrovascular_Disease", "Cerebrovascular"),
            ("Congestive_Heart_Failure", "Heart failure"),
            ("Renal_Disease_Severe", "Renal (severe)"),
            ("Chronic_Pulmonary_Disease", "Pulmonary"),
            ("Diabetes_with_Chronic_Complications", "DM w/ complic."),
            ("Diabetes_without_Chronic_Complications", "DM w/o complic."),
            ("Liver_Disease_Mild", "Liver (mild)"),
            ("Malignancy", "Malignancy"),
            ("AIDS", "AIDS"),
            ("HIV", "HIV"),
            ("Myocardial_Infarction", "MI"),
            ("Hemiplegia_Paraplegia", "Hemiplegia"),
            ("Renal_Disease_Mild_Moderate", "Renal (mild/mod)"),
            ("Peripheral_Vascular_Disease", "PVD"),
        ],
    ),
]


def plot_hierarchical_forest(ax, groups, coef_df, panel_label, xlim, xticks):
    """Generic hierarchical forest plot with gray band interleaving."""
    plot_rows, y_labels, group_spans = [], [], []
    y = 0
    for gi, (grp, items) in enumerate(groups):
        y_start = y
        for item in items:
            if len(item) == 2:
                var, label = item
                subset = coef_df[coef_df.variable == var]
            else:
                model, var, label = item
                subset = coef_df[(coef_df.model == model) & (coef_df.variable == var)]
            if len(subset) == 0:
                continue
            r = subset.iloc[0]
            plot_rows.append(
                {
                    "y": y,
                    "aor": float(r.AOR),
                    "lo": float(r.CI_lower),
                    "hi": float(r.CI_upper),
                    "p": float(r.p_value),
                }
            )
            y_labels.append("  " + label)
            y += 1
        group_spans.append((grp, y_start, y - 1, gi))
        y += 0.4

    max_y = y - 0.4
    positions = [max_y - r["y"] for r in plot_rows]

    # Gray bands
    for grp, ys, ye, gi in group_spans:
        if gi % 2 == 0:
            ax.axhspan(max_y - ye - 0.45, max_y - ys + 0.45, color="#F5F5F5", zorder=0)
        y_mid = max_y - (ys + ye) / 2
        ax.text(
            -0.12,
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

    ax.axvline(1.0, color="black", linewidth=0.5, linestyle="-", zorder=1)
    ax.set_yticks(positions)
    ax.set_yticklabels(y_labels, fontsize=7.5)
    ax.set_xlabel("Adjusted Odds Ratio (95% CI)", fontsize=8)
    ax.set_xscale("log")
    ax.set_xlim(*xlim)
    ax.set_xticks(xticks)
    ax.get_xaxis().set_major_formatter(mpl.ticker.ScalarFormatter())
    ax.text(
        -0.02,
        1.02,
        panel_label,
        fontsize=10,
        fontweight="bold",
        transform=ax.transAxes,
        va="bottom",
    )

    # AOR text
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
    return plot_rows


fig, ax = plt.subplots(figsize=(W_DOUBLE, 6.5))
plot_hierarchical_forest(
    ax,
    BASE_GROUPS,
    base,
    "a",
    xlim=(0.4, 3.2),
    xticks=[0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0],
)
save_fig(fig, "fig2_base_forest")


# ══════════════════════════════════════════════════════════════════════
# FIGURE 3: SDoH FOREST PLOT (hierarchical labels + gray bands)
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("FIGURE 3: SDoH Forest Plot")
print("=" * 60)

SDOH_GROUPS = [
    (
        "Income",
        [
            ("income", "f.incomeless_10k", "<$10K"),
            ("income", "f.income10k_25k", "$10\u201325K"),
            ("income", "f.income25k_35k", "$25\u201335K"),
            ("income", "f.income100k_150k", "$100\u2013150K"),
            ("income", "f.income150k_200k", "$150\u2013200K"),
            ("income", "f.incomemore_200k", ">$200K"),
        ],
    ),
    (
        "Insurance",
        [
            ("insurance", "ins_employer", "Employer"),
            ("insurance", "ins_medicare", "Medicare"),
            ("insurance", "ins_medicaid", "Medicaid"),
        ],
    ),
    (
        "Education",
        [
            ("education", "f.educationNever_Attended", "Never attended"),
            ("education", "f.educationBelow_GED", "Below GED"),
            ("education", "f.educationGED_or_College", "GED/some college"),
        ],
    ),
    (
        "Employment",
        [
            ("employment", "f.employmentUnemployed", "Unemployed"),
            ("employment", "f.employmentStudent", "Student"),
            ("employment", "f.employmentOthers", "Others/retired"),
        ],
    ),
    (
        "Housing",
        [("housing", "f.housingRent", "Rent"), ("housing", "f.housingOthers", "Other")],
    ),
    ("Stability", [("housing_stability", "f.housing_stabilityUnstable", "Unstable")]),
    ("Disability", [("disability_lumped", "f.disability_anyYes", "Any disability")]),
]

fig, ax = plt.subplots(figsize=(W_DOUBLE, 6.0))
plot_hierarchical_forest(
    ax,
    SDOH_GROUPS,
    aou,
    "b",
    xlim=(0.55, 4.5),
    xticks=[0.6, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0],
)
save_fig(fig, "fig3_sdoh_forest")


# TABLE 3: SDoH AOR SUMMARY
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("TABLE 3: SDoH AOR Summary")
print("=" * 60)

table3_rows = []
for domain, items in SDOH_GROUPS:
    for model, var, label in items:
        subset = aou[(aou.model == model) & (aou.variable == var)]
        if len(subset) == 0:
            continue
        r = subset.iloc[0]
        sig = (
            "***"
            if r.p_value < 0.001
            else ("**" if r.p_value < 0.01 else ("*" if r.p_value < 0.05 else ""))
        )
        table3_rows.append(
            {
                "Domain": domain,
                "Variable": label,
                "AOR": f"{r.AOR:.2f}",
                "95% CI": f"{r.CI_lower:.2f}\u2013{r.CI_upper:.2f}",
                "P-value": (
                    f"{r.p_value:.2e}" if r.p_value < 0.001 else f"{r.p_value:.3f}"
                ),
                "Sig": sig,
            }
        )
table3 = pd.DataFrame(table3_rows)
table3.to_csv(os.path.join(TBL_DIR, "table3_sdoh_summary.csv"), index=False)
print(table3.to_string(index=False))
print(f"  Saved: {TBL_DIR}/table3_sdoh_summary.csv")


# ══════════════════════════════════════════════════════════════════════
# eTABLE: AoU vs MS COMPARISON
# ══════════════════════════════════════════════════════════════════════
if has_ms:
    print("\n" + "=" * 60)
    print("eTABLE: Cross-Site Comparison")
    print("=" * 60)

    aou_base = aou[aou.model == "base"][
        ["variable", "AOR", "CI_lower", "CI_upper", "p_value"]
    ].copy()
    aou_base.columns = ["Variable", "AoU_AOR", "AoU_CI_lo", "AoU_CI_hi", "AoU_p"]
    ms_base = ms[ms.model == "base"][
        ["variable", "AOR", "CI_lower", "CI_upper", "p_value"]
    ].copy()
    ms_base.columns = ["Variable", "MS_AOR", "MS_CI_lo", "MS_CI_hi", "MS_p"]

    comp = aou_base.merge(ms_base, on="Variable", how="outer")
    comp["AoU_dir"] = comp.AoU_AOR.apply(
        lambda x: "Risk" if x > 1 else "Protective" if pd.notna(x) else ""
    )
    comp["MS_dir"] = comp.MS_AOR.apply(
        lambda x: "Risk" if x > 1 else "Protective" if pd.notna(x) else ""
    )
    comp["Concordant"] = comp.AoU_dir == comp.MS_dir
    comp.to_csv(os.path.join(TBL_DIR, "etable_ms_comparison.csv"), index=False)

    shared = comp.dropna(subset=["AoU_AOR", "MS_AOR"])
    n_conc = shared.Concordant.sum()
    print(f"  Concordant: {n_conc}/{len(shared)} ({n_conc/len(shared)*100:.0f}%)")
    print(f"  Saved: {TBL_DIR}/etable_ms_comparison.csv")


# ══════════════════════════════════════════════════════════════════════
# CONSORT COUNTS (for reference / manuscript)
# ══════════════════════════════════════════════════════════════════════
consort = pd.DataFrame(
    [
        {"Site": "AoU", "Metric": "total_participants", "Value": 413457},
        {"Site": "AoU", "Metric": "eligible_ehr_survey", "Value": 252047},
        {"Site": "AoU", "Metric": "covid_positive", "Value": 25160},
        {"Site": "AoU", "Metric": "hospitalized_30d", "Value": 6531},
        {"Site": "AoU", "Metric": "outpatient_only", "Value": 18629},
        {"Site": "AoU", "Metric": "matched_total", "Value": 32606},
        {"Site": "AoU", "Metric": "strata", "Value": 6531},
        {"Site": "AoU", "Metric": "dropped", "Value": 0},
        {"Site": "AoU", "Metric": "caliper", "Value": 0.1118},
        {"Site": "MS", "Metric": "covid_positive", "Value": 4423200},
        {"Site": "MS", "Metric": "hospitalized", "Value": 149796},
        {"Site": "MS", "Metric": "outpatient", "Value": 4273404},
        {"Site": "MS", "Metric": "matched_total", "Value": 748857},
        {"Site": "MS", "Metric": "strata", "Value": 149773},
        {"Site": "MS", "Metric": "dropped", "Value": 4},
    ]
)
consort.to_csv(os.path.join(TBL_DIR, "consort_counts.csv"), index=False)
print(f"\n  Saved: {TBL_DIR}/consort_counts.csv")

print(f"\n{'='*60}")
print(f"ALL OUTPUTS: {FIG_DIR}/ and {TBL_DIR}/")
print("=" * 60)
