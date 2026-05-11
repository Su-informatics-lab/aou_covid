#!/usr/bin/env python3
"""
COVID-19 Severity × SDoH — Publication Figures & Tables
Nature Portfolio style (Arial 7pt, Wong/Okabe-Ito, 600 DPI vector).

Usage: python 05_figures.py [results_dir]

Inputs:  results/aou_v7/all_model_coefficients.csv
         results/aou_v7/wave_stratified_income.csv
         results/ms/all_model_coefficients.csv  (optional)

Outputs: results/figures/fig3_base_forest.pdf
         results/figures/fig4_sdoh_forest.pdf
         results/figures/fig5_wave_income.pdf
         results/tables/table3_sdoh_summary.csv
         results/tables/etable_ms_comparison.csv
"""

import os
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
from matplotlib.transforms import blended_transform_factory

# ═══════════════════════════════════════════════════════════════════════
# NATURE PORTFOLIO MANDATORY rcParams (from nature-visualizer skill)
# ═══════════════════════════════════════════════════════════════════════
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
mpl.rcParams["legend.title_fontsize"] = 7
mpl.rcParams["axes.linewidth"] = 0.5
mpl.rcParams["xtick.major.width"] = 0.5
mpl.rcParams["ytick.major.width"] = 0.5
mpl.rcParams["xtick.major.size"] = 3
mpl.rcParams["ytick.major.size"] = 3
mpl.rcParams["xtick.minor.width"] = 0.3
mpl.rcParams["ytick.minor.width"] = 0.3
mpl.rcParams["xtick.direction"] = "out"
mpl.rcParams["ytick.direction"] = "out"
mpl.rcParams["lines.linewidth"] = 1.0
mpl.rcParams["lines.markersize"] = 4
mpl.rcParams["legend.frameon"] = False
mpl.rcParams["legend.borderpad"] = 0.3
mpl.rcParams["axes.grid"] = False
mpl.rcParams["axes.spines.top"] = False
mpl.rcParams["axes.spines.right"] = False
mpl.rcParams["figure.facecolor"] = "white"
mpl.rcParams["savefig.facecolor"] = "white"
mpl.rcParams["savefig.dpi"] = 300
mpl.rcParams["savefig.bbox"] = "tight"
mpl.rcParams["savefig.pad_inches"] = 0.02
mpl.rcParams["figure.constrained_layout.use"] = True

# Wong/Okabe-Ito colorblind-safe palette
C_RISK = "#D55E00"  # vermillion — significant risk
C_PROTECT = "#0072B2"  # blue — significant protective
C_NS = "#999999"  # grey — non-significant

# Nature column widths
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
        fig.savefig(
            os.path.join(FIG_DIR, f"{name}.{ext}"), dpi=600 if ext == "png" else 300
        )
    print(f"  Saved: {FIG_DIR}/{name}.pdf/.png")
    plt.close(fig)


def add_panel_label(ax, label, x=-0.02, y=1.02):
    """Nature-style panel label: 8pt, bold, lowercase."""
    ax.text(
        x, y, label, fontsize=8, fontweight="bold", transform=ax.transAxes, va="bottom"
    )


# ═══════════════════════════════════════════════════════════════════════
# HIERARCHICAL FOREST PLOT ENGINE
# ═══════════════════════════════════════════════════════════════════════
def plot_hierarchical_forest(ax, groups, coef_df, panel_label, xlim, xticks):
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

    # Gray bands (alternating groups)
    for grp, ys, ye, gi in group_spans:
        if gi % 2 == 0:
            ax.axhspan(max_y - ye - 0.45, max_y - ys + 0.45, color="#F5F5F5", zorder=0)
        y_mid = max_y - (ys + ye) / 2
        ax.text(
            -0.12,
            y_mid,
            grp,
            fontsize=7,
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
    ax.set_yticklabels(y_labels, fontsize=6)
    ax.set_xlabel("Adjusted odds ratio (95% CI)", fontsize=7)
    ax.set_xscale("log")
    ax.set_xlim(*xlim)
    ax.set_xticks(xticks)
    ax.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
    add_panel_label(ax, panel_label)

    # AOR text annotations
    tt = blended_transform_factory(ax.transAxes, ax.transData)
    for i, r in enumerate(plot_rows):
        sig = "\u2020" if r["p"] < 0.05 else ""
        ax.text(
            1.02,
            positions[i],
            f'{r["aor"]:.2f} ({r["lo"]:.2f}\u2013{r["hi"]:.2f}){sig}',
            va="center",
            ha="left",
            fontsize=5.5,
            family="monospace",
            transform=tt,
        )
    return plot_rows


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 3: BASE MODEL FOREST PLOT
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("FIGURE 3: Base Model Forest Plot")
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
    ("Wave", [("f.wavedelta", "Delta"), ("f.waveomicron", "Omicron")]),
    (
        "Comorbidities",
        [
            ("Cerebrovascular_Disease", "Cerebrovascular"),
            ("Congestive_Heart_Failure", "Heart failure"),
            ("Renal_Disease_Severe", "Renal (severe)"),
            ("Metastatic_Solid_Tumor", "Metastatic tumor"),
            ("Liver_Disease_Moderate_Severe", "Liver (mod/severe)"),
            ("Dementia", "Dementia"),
            ("Myocardial_Infarction", "MI"),
            ("Renal_Disease_Mild_Moderate", "Renal (mild/mod)"),
            ("Chronic_Pulmonary_Disease", "Pulmonary"),
            ("Liver_Disease_Mild", "Liver (mild)"),
            ("Diabetes_with_Chronic_Complications", "DM w/ complic."),
            ("Diabetes_without_Chronic_Complications", "DM w/o complic."),
            ("Hemiplegia_Paraplegia", "Hemiplegia"),
            ("Peripheral_Vascular_Disease", "PVD"),
            ("AIDS", "AIDS"),
            ("HIV", "HIV"),
        ],
    ),
]

fig, ax = plt.subplots(figsize=(W_DOUBLE, 7.5))
plot_hierarchical_forest(
    ax,
    BASE_GROUPS,
    base,
    "a",
    xlim=(0.4, 3.2),
    xticks=[0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0],
)
save_fig(fig, "fig3_base_forest")


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 4: SDoH FOREST PLOT
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("FIGURE 4: SDoH Forest Plot")
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
            ("insurance", "f.insuranceMedicare", "Medicare"),
            ("insurance", "f.insuranceMedicaid", "Medicaid"),
            ("insurance", "f.insuranceOther_None", "Other/None"),
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
        [
            ("housing", "f.housingRent", "Rent"),
            ("housing", "f.housingOthers", "Other"),
        ],
    ),
    (
        "Stability",
        [
            ("housing_stability", "f.housing_stabilityUnstable", "Unstable"),
        ],
    ),
    (
        "Disability",
        [
            ("disability_lumped", "f.disability_anyYes", "Any disability"),
        ],
    ),
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
save_fig(fig, "fig4_sdoh_forest")


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 5: WAVE-STRATIFIED INCOME FOREST PLOT
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("FIGURE 5: Wave-Stratified Income Forest Plot")
print("=" * 60)

wave_path = os.path.join(BASE, "aou_v7", "wave_stratified_income.csv")
matched_path_w = os.path.join(BASE, "aou_v7", "07_matched_cohort.csv")
if not os.path.exists(matched_path_w):
    matched_path_w = os.path.join(BASE, "aou_v7", "06_matched_cohort.csv")
cohort_path_w = os.path.join(BASE, "aou_v7", "01_covid_cohort.csv")

if os.path.exists(wave_path):
    df_w = pd.read_csv(wave_path)

    # Per-wave case counts for labels
    wave_n = {}
    if os.path.exists(matched_path_w) and os.path.exists(cohort_path_w):
        matched_w = pd.read_csv(matched_path_w)
        cohort_w = pd.read_csv(cohort_path_w)
        mw = matched_w.merge(cohort_w[["person_id", "pandemic_wave"]], on="person_id")
        wave_n = mw[mw.Treatment == 1].pandemic_wave.value_counts().to_dict()

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

    df_w = df_w[
        df_w["variable"].isin(INCOMES_ORDER) & df_w["wave"].isin(WAVES_ORDER)
    ].copy()

    # Build hierarchical layout
    plot_rows_w, y_labels_w, group_spans_w = [], [], []
    y = 0
    for gi, w in enumerate(WAVES_ORDER):
        y_start = y
        n_in = 0
        for inc in INCOMES_ORDER:
            sub = df_w[(df_w["variable"] == inc) & (df_w["wave"] == w)]
            if len(sub) == 0:
                continue
            r = sub.iloc[0]
            plot_rows_w.append(
                {
                    "y": y,
                    "aor": float(r.AOR),
                    "lo": float(r.CI_lower),
                    "hi": float(r.CI_upper),
                    "p": float(r.p_value),
                }
            )
            y_labels_w.append("  " + INCOME_LABELS[inc])
            y += 1
            n_in += 1
        if n_in == 0:
            continue
        label = WAVE_LABELS[w]
        if w in wave_n:
            label += f" (N={wave_n[w]:,})"
        group_spans_w.append((label, y_start, y - 1, gi))
        y += 0.4

    max_y_w = y - 0.4
    positions_w = [max_y_w - r["y"] for r in plot_rows_w]

    fig, ax = plt.subplots(figsize=(W_DOUBLE, 4.0))

    for grp, ys, ye, gi in group_spans_w:
        if gi % 2 == 0:
            ax.axhspan(
                max_y_w - ye - 0.45, max_y_w - ys + 0.45, color="#F5F5F5", zorder=0
            )
        y_mid = max_y_w - (ys + ye) / 2
        ax.text(
            -0.14,
            y_mid,
            grp,
            fontsize=7,
            fontweight="bold",
            ha="right",
            va="center",
            transform=ax.get_yaxis_transform(),
            color="#333333",
        )

    for i, r in enumerate(plot_rows_w):
        c = (
            C_RISK
            if (r["p"] < 0.05 and r["aor"] > 1)
            else (C_PROTECT if (r["p"] < 0.05 and r["aor"] < 1) else C_NS)
        )
        ax.errorbar(
            r["aor"],
            positions_w[i],
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
    ax.set_yticks(positions_w)
    ax.set_yticklabels(y_labels_w, fontsize=6)
    ax.set_xlabel(
        "Adjusted odds ratio (95% CI), reference $35,000\u201399,999", fontsize=7
    )
    ax.set_xscale("log")
    ax.set_xlim(0.55, 4.5)
    ax.set_xticks([0.6, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0])
    ax.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
    add_panel_label(ax, "c")

    tt = blended_transform_factory(ax.transAxes, ax.transData)
    for i, r in enumerate(plot_rows_w):
        sig = "\u2020" if r["p"] < 0.05 else ""
        ax.text(
            1.02,
            positions_w[i],
            f'{r["aor"]:.2f} ({r["lo"]:.2f}\u2013{r["hi"]:.2f}){sig}',
            va="center",
            ha="left",
            fontsize=5.5,
            family="monospace",
            transform=tt,
        )

    save_fig(fig, "fig5_wave_income")
else:
    print(f"  WARNING: {wave_path} not found, skipping Figure 5")


# ═══════════════════════════════════════════════════════════════════════
# TABLE 3: SDoH AOR SUMMARY (domain-by-domain + joint)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("TABLE 3: SDoH AOR Summary")
print("=" * 60)

joint = aou[aou.model == "joint_sdoh"].copy()

table3_rows = []
for domain, items in SDOH_GROUPS:
    for model, var, label in items:
        subset_d = aou[(aou.model == model) & (aou.variable == var)]
        subset_j = joint[joint.variable == var]
        if len(subset_d) == 0:
            continue
        rd = subset_d.iloc[0]
        sig_d = (
            "***"
            if rd.p_value < 0.001
            else ("**" if rd.p_value < 0.01 else ("*" if rd.p_value < 0.05 else ""))
        )
        row = {
            "Domain": domain,
            "Variable": label,
            "Domain AOR": f"{rd.AOR:.2f}{sig_d}",
            "Domain 95% CI": f"{rd.CI_lower:.2f}\u2013{rd.CI_upper:.2f}",
        }
        if len(subset_j) > 0:
            rj = subset_j.iloc[0]
            sig_j = (
                "***"
                if rj.p_value < 0.001
                else ("**" if rj.p_value < 0.01 else ("*" if rj.p_value < 0.05 else ""))
            )
            row["Joint AOR"] = f"{rj.AOR:.2f}{sig_j}"
            row["Joint 95% CI"] = f"{rj.CI_lower:.2f}\u2013{rj.CI_upper:.2f}"
        else:
            row["Joint AOR"] = ""
            row["Joint 95% CI"] = ""
        table3_rows.append(row)

table3 = pd.DataFrame(table3_rows)
table3.to_csv(os.path.join(TBL_DIR, "table3_sdoh_summary.csv"), index=False)
print(table3.to_string(index=False))
print(f"  Saved: {TBL_DIR}/table3_sdoh_summary.csv")


# ═══════════════════════════════════════════════════════════════════════
# eTABLE: AoU vs MS COMPARISON
# ═══════════════════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════════════════
# CONSORT COUNTS — read PSM-dependent values from pipeline CSVs
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("CONSORT COUNTS")
print("=" * 60)

# ETL counts (stable, from 01_aou_etl.py / 01_ms_etl.py)
consort_rows = [
    {"Site": "AoU", "Metric": "total_participants", "Value": 413457},
    {"Site": "AoU", "Metric": "covid_positive", "Value": 25160},
    {"Site": "AoU", "Metric": "hospitalized_strict_14d", "Value": 4064},
    {"Site": "AoU", "Metric": "hospitalized_broad_30d", "Value": 6531},
    {"Site": "AoU", "Metric": "ed_only_reclassified", "Value": 2467},
    {"Site": "AoU", "Metric": "outpatient_controls", "Value": 21096},
]


# PSM-dependent counts — read from 07b_control_reuse.csv
def read_reuse(site_dir):
    """Read PSM counts from 07b_control_reuse.csv (MatchIt) or
    06b_control_reuse.csv (legacy sklearn)."""
    for fname in ["07b_control_reuse.csv", "06b_control_reuse.csv"]:
        path = os.path.join(site_dir, fname)
        if os.path.exists(path):
            df = pd.read_csv(path)
            out = {}
            for _, r in df.iterrows():
                out[r.metric] = r.value
            print(f"  Read PSM counts from {path}")
            return out
    return None


# AoU PSM counts
aou_reuse = read_reuse(os.path.join(BASE, "aou_v7"))
if aou_reuse:
    n_ctrl_rows = int(aou_reuse.get("n_control_rows", 0))
    n_unique = int(aou_reuse.get("n_unique_controls", 0))
    n_cases = 4064  # stable from ETL
    n_matched = n_cases + n_ctrl_rows
    consort_rows.extend(
        [
            {"Site": "AoU", "Metric": "matched_observations", "Value": n_matched},
            {"Site": "AoU", "Metric": "matched_strata", "Value": n_cases},
            {"Site": "AoU", "Metric": "unique_controls", "Value": n_unique},
            {"Site": "AoU", "Metric": "control_observations", "Value": n_ctrl_rows},
        ]
    )
    print(f"  AoU: {n_matched:,} matched obs, {n_unique:,} unique controls")
else:
    print("  WARNING: AoU 07b_control_reuse.csv not found, skipping PSM counts")

# MS counts
consort_rows.extend(
    [
        {"Site": "MS", "Metric": "covid_positive", "Value": 4423200},
        {"Site": "MS", "Metric": "hospitalized_strict_14d", "Value": 139489},
    ]
)

ms_reuse = read_reuse(os.path.join(BASE, "ms"))
if ms_reuse:
    ms_ctrl_rows = int(ms_reuse.get("n_control_rows", 0))
    ms_unique = int(ms_reuse.get("n_unique_controls", 0))
    ms_cases = 139489  # from ETL; some may be dropped by caliper
    ms_dropped = int(ms_reuse.get("n_cases_dropped", 0))
    ms_cases_matched = ms_cases - ms_dropped
    ms_matched = ms_cases_matched + ms_ctrl_rows
    consort_rows.extend(
        [
            {"Site": "MS", "Metric": "matched_observations", "Value": ms_matched},
            {"Site": "MS", "Metric": "matched_strata", "Value": ms_cases_matched},
        ]
    )
    print(f"  MS: {ms_matched:,} matched obs, {ms_cases_matched:,} strata")
else:
    print("  WARNING: MS 07b_control_reuse.csv not found, skipping MS PSM counts")

consort = pd.DataFrame(consort_rows)
consort.to_csv(os.path.join(TBL_DIR, "consort_counts.csv"), index=False)
print(f"  Saved: {TBL_DIR}/consort_counts.csv")

print(f"\n{'='*60}")
print(f"ALL OUTPUTS: {FIG_DIR}/ and {TBL_DIR}/")
print("=" * 60)
