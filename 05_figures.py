#!/usr/bin/env python3
"""
COVID-19 Severity x SDoH -- Publication Figures & Tables  (v3)
JAMIA (OUP) submission-ready.
Usage: python 05_figures.py [results_dir]
"""

import os
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
from matplotlib.transforms import blended_transform_factory

# ── rcParams (JAMIA/OUP — larger fonts for readability) ───────────────
mpl.rcParams.update(
    {
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 8,
        "axes.labelsize": 9,
        "axes.titlesize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "legend.title_fontsize": 8,
        "axes.linewidth": 0.5,
        "xtick.major.width": 0.5,
        "ytick.major.width": 0.5,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "xtick.minor.width": 0.3,
        "ytick.minor.width": 0.3,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "lines.linewidth": 1.0,
        "lines.markersize": 4,
        "legend.frameon": False,
        "legend.borderpad": 0.3,
        "axes.grid": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.04,
    }
)

C_RISK = "#D55E00"
C_PROTECT = "#0072B2"
C_NS = "#999999"
C_BAND = "#F5F5F5"
W_DOUBLE = 7.008

BASE = sys.argv[1] if len(sys.argv) > 1 else "results"
FIG_DIR = os.path.join(BASE, "figures")
TBL_DIR = os.path.join(BASE, "tables")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(TBL_DIR, exist_ok=True)

aou = pd.read_csv(os.path.join(BASE, "aou_v7", "all_model_coefficients.csv"))
ms_path = os.path.join(BASE, "ms", "all_model_coefficients.csv")
has_ms = os.path.exists(ms_path)
if has_ms:
    ms = pd.read_csv(ms_path)


def save_fig(fig, name):
    for ext in ["pdf", "png"]:
        fig.savefig(
            os.path.join(FIG_DIR, f"{name}.{ext}"), dpi=600 if ext == "png" else 300
        )
    print(f"  Saved: {FIG_DIR}/{name}.pdf/.png")
    plt.close(fig)


def _dec_fmt(x, pos):
    if x == int(x):
        return f"{int(x)}"
    return f"{x:.2f}".rstrip("0").rstrip(".")


# ===================================================================
# FOREST PLOT ENGINE v3
# ===================================================================
def plot_forest_v3(ax, groups, coef_df, xlim, xticks, ci_cap_x=None):
    rows = []
    gi = 0
    for header, ref, items in groups:
        ref_str = f"  (ref: {ref})" if ref else ""
        rows.append(("header", f"{header}{ref_str}", None, gi))
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
            rows.append(
                (
                    "data",
                    f"    {label}",
                    {
                        "aor": float(r.AOR),
                        "lo": float(r.CI_lower),
                        "hi": float(r.CI_upper),
                        "p": float(r.p_value),
                    },
                    gi,
                )
            )
        gi += 1

    n = len(rows)
    positions = list(range(n - 1, -1, -1))

    # Alternating bands
    gi_spans = {}
    for i, (typ, lab, dat, gidx) in enumerate(rows):
        if gidx not in gi_spans:
            gi_spans[gidx] = [i, i]
        gi_spans[gidx][1] = i
    for gidx, (start, end) in gi_spans.items():
        if gidx % 2 == 0:
            ax.axhspan(
                positions[end] - 0.45,
                positions[start] + 0.45,
                color=C_BAND,
                zorder=0,
                linewidth=0,
            )

    # Render
    y_ticks = []
    y_labels = []
    for i, (typ, lab, dat, gidx) in enumerate(rows):
        y = positions[i]
        y_ticks.append(y)
        y_labels.append(lab)
        if typ != "data":
            continue
        r = dat
        c = (
            C_RISK
            if (r["p"] < 0.05 and r["aor"] > 1)
            else (C_PROTECT if (r["p"] < 0.05 and r["aor"] < 1) else C_NS)
        )

        lo_plot, hi_plot, arrow_hi = r["lo"], r["hi"], False
        if ci_cap_x is not None and r["hi"] > ci_cap_x:
            hi_plot = ci_cap_x
            arrow_hi = True

        ax.errorbar(
            r["aor"],
            y,
            xerr=[[r["aor"] - lo_plot], [hi_plot - r["aor"]]],
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

        if arrow_hi:
            arrow_len = 0.07 * (xlim[1] - xlim[0])
            ax.annotate(
                "",
                xy=(hi_plot + arrow_len, y),
                xytext=(hi_plot, y),
                arrowprops=dict(arrowstyle="-|>", color=c, lw=1.5, mutation_scale=12),
                clip_on=False,
                zorder=5,
            )

    ax.axvline(1.0, color="black", linewidth=0.5, zorder=1)
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels, fontsize=7.5)
    ax.tick_params(axis="y", length=0, pad=3)

    for i, (typ, lab, dat, gidx) in enumerate(rows):
        if typ == "header":
            ax.get_yticklabels()[i].set_fontweight("bold")
            ax.get_yticklabels()[i].set_fontsize(8)

    ax.set_xlabel("Adjusted odds ratio (95% CI)", fontsize=9)
    ax.set_xscale("log")
    ax.set_xlim(*xlim)
    ax.set_xticks(xticks)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(_dec_fmt))
    ax.xaxis.set_minor_formatter(ticker.NullFormatter())

    tt = blended_transform_factory(ax.transAxes, ax.transData)
    for i, (typ, lab, dat, gidx) in enumerate(rows):
        if typ != "data":
            continue
        r = dat
        sig = "*" if r["p"] < 0.05 else ""
        txt = f'{r["aor"]:.2f} ({r["lo"]:.2f}\u2013{r["hi"]:.2f}){sig}'
        ax.text(
            1.01,
            positions[i],
            txt,
            va="center",
            ha="left",
            fontsize=6.5,
            family="sans-serif",
            transform=tt,
        )


# ===================================================================
# FIGURE 3: BASE MODEL FOREST
# ===================================================================
print("\n" + "=" * 60 + "\nFIGURE 3: Base Model Forest Plot\n" + "=" * 60)
base = aou[aou.model == "base"].copy()

BASE_GROUPS = [
    ("Sex", "Male", [("f.sexFemale", "Female"), ("f.sexOther", "Other")]),
    (
        "Age",
        "<45",
        [
            ("f.age45-54", "45\u201354"),
            ("f.age55-64", "55\u201364"),
            ("f.age65+", "\u226565"),
        ],
    ),
    ("Vaccination", "Unvaccinated", [("f.vaccVaccinated", "Vaccinated")]),
    (
        "Race",
        "White",
        [("f.raceBlack", "Black"), ("f.raceAsian", "Asian"), ("f.raceOther", "Other")],
    ),
    (
        "Ethnicity",
        "Not Hispanic",
        [("f.ethnicityHispanic", "Hispanic"), ("f.ethnicityOther", "Other")],
    ),
    ("Wave", "Pre-Delta", [("f.wavedelta", "Delta"), ("f.waveomicron", "Omicron")]),
    (
        "Comorbidity (ref: absence of condition)",
        None,
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

fig, ax = plt.subplots(figsize=(W_DOUBLE, 8.5))
plot_forest_v3(
    ax,
    BASE_GROUPS,
    base,
    xlim=(0.35, 3.2),
    xticks=[0.4, 0.5, 0.6, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0],
)
fig.subplots_adjust(left=0.24, right=0.78)
save_fig(fig, "fig3_base_forest")


# ===================================================================
# FIGURE 4: SDoH FOREST
# ===================================================================
print("\n" + "=" * 60 + "\nFIGURE 4: SDoH Forest Plot\n" + "=" * 60)

SDOH_GROUPS = [
    (
        "Income",
        "$35\u2013100K",
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
        "Employer",
        [
            ("insurance", "f.insuranceMedicare", "Medicare"),
            ("insurance", "f.insuranceMedicaid", "Medicaid"),
            ("insurance", "f.insuranceOther_None", "Other/None"),
        ],
    ),
    (
        "Education",
        "Advanced degree",
        [
            ("education", "f.educationNever_Attended", "Never attended"),
            ("education", "f.educationBelow_GED", "Below GED"),
            ("education", "f.educationGED_or_College", "GED/some college"),
        ],
    ),
    (
        "Employment",
        "Employed",
        [
            ("employment", "f.employmentUnemployed", "Unemployed"),
            ("employment", "f.employmentStudent", "Student"),
            ("employment", "f.employmentOthers", "Others/retired"),
        ],
    ),
    (
        "Housing",
        "Own",
        [
            ("housing", "f.housingRent", "Rent"),
            ("housing", "f.housingOthers", "Other"),
        ],
    ),
    (
        "Housing stability",
        "Stable",
        [
            ("housing_stability", "f.housing_stabilityUnstable", "Unstable"),
        ],
    ),
    (
        "Disability",
        "None",
        [
            ("disability_lumped", "f.disability_anyYes", "Any disability"),
        ],
    ),
]

fig, ax = plt.subplots(figsize=(W_DOUBLE, 6.5))
plot_forest_v3(
    ax,
    SDOH_GROUPS,
    aou,
    xlim=(0.55, 4.0),
    xticks=[0.6, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0],
    ci_cap_x=4.0,
)
fig.subplots_adjust(left=0.24, right=0.78)
save_fig(fig, "fig4_sdoh_forest")


# ===================================================================
# FIGURE 5: WAVE-STRATIFIED INCOME
# ===================================================================
print("\n" + "=" * 60 + "\nFIGURE 5: Wave-Stratified Income\n" + "=" * 60)

wave_path = os.path.join(BASE, "aou_v7", "wave_stratified_income.csv")
matched_path = os.path.join(BASE, "aou_v7", "07_matched_cohort.csv")
if not os.path.exists(matched_path):
    matched_path = os.path.join(BASE, "aou_v7", "06_matched_cohort.csv")
cohort_path = os.path.join(BASE, "aou_v7", "01_covid_cohort.csv")

if os.path.exists(wave_path):
    df_w = pd.read_csv(wave_path)
    wave_n = {}
    if os.path.exists(matched_path) and os.path.exists(cohort_path):
        matched_w = pd.read_csv(matched_path)
        cohort_w = pd.read_csv(cohort_path)
        mw = matched_w.merge(cohort_w[["person_id", "pandemic_wave"]], on="person_id")
        wave_n = mw[mw.Treatment == 1].pandemic_wave.value_counts().to_dict()

    INCOME_LABELS = {
        "f.incomeless_10k": "<$10,000",
        "f.income10k_25k": "$10,000\u201324,999",
        "f.income25k_35k": "$25,000\u201334,999",
    }
    WAVES_ORDER = ["pre_delta", "delta", "omicron"]
    WAVE_NAMES = {"pre_delta": "Pre-Delta", "delta": "Delta", "omicron": "Omicron"}
    INCOMES_ORDER = ["f.incomeless_10k", "f.income10k_25k", "f.income25k_35k"]
    df_w = df_w[
        df_w["variable"].isin(INCOMES_ORDER) & df_w["wave"].isin(WAVES_ORDER)
    ].copy()

    wave_groups = []
    for w in WAVES_ORDER:
        name = WAVE_NAMES[w]
        n_str = f"N = {wave_n[w]:,}" if w in wave_n else ""
        header = f"{name} ({n_str})" if n_str else name
        items = [
            (w, inc, INCOME_LABELS[inc])
            for inc in INCOMES_ORDER
            if len(df_w[(df_w["variable"] == inc) & (df_w["wave"] == w)]) > 0
        ]
        wave_groups.append((header, "$35,000\u201399,999", items))

    wave_coef = df_w.copy()
    wave_coef["model"] = wave_coef["wave"]

    fig, ax = plt.subplots(figsize=(W_DOUBLE, 4.0))
    plot_forest_v3(
        ax,
        wave_groups,
        wave_coef,
        xlim=(0.55, 4.5),
        xticks=[0.6, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0],
    )
    ax.set_xlabel(
        "Adjusted odds ratio (95% CI), reference: $35,000\u201399,999", fontsize=9
    )
    fig.subplots_adjust(left=0.24, right=0.78)
    save_fig(fig, "fig5_wave_income")
else:
    print(f"  WARNING: {wave_path} not found, skipping Figure 5")


# ===================================================================
# TABLE 3
# ===================================================================
print("\n" + "=" * 60 + "\nTABLE 3: SDoH AOR Summary\n" + "=" * 60)
joint = aou[aou.model == "joint_sdoh"].copy()
table3_rows = []
for domain, ref, items in SDOH_GROUPS:
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
            "Reference": ref,
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


# ===================================================================
# eTABLE: AoU vs MS
# ===================================================================
if has_ms:
    print("\n" + "=" * 60 + "\neTABLE: Cross-Site Comparison\n" + "=" * 60)
    aou_base = aou[aou.model == "base"][
        ["variable", "AOR", "CI_lower", "CI_upper", "p_value"]
    ].copy()
    aou_base.columns = ["Variable", "AoU_AOR", "AoU_CI_lo", "AoU_CI_hi", "AoU_p"]
    ms_base = ms[ms.model == "base"][
        ["variable", "AOR", "CI_lower", "CI_upper", "p_value"]
    ].copy()
    ms_base.columns = ["Variable", "MS_AOR", "MS_CI_lo", "MS_CI_hi", "MS_p"]
    comp = aou_base.merge(ms_base, on="Variable", how="outer")
    comp["Concordant"] = (comp.AoU_AOR > 1) == (comp.MS_AOR > 1)
    comp.to_csv(os.path.join(TBL_DIR, "etable_ms_comparison.csv"), index=False)
    shared = comp.dropna(subset=["AoU_AOR", "MS_AOR"])
    print(f"  Concordant: {shared.Concordant.sum()}/{len(shared)}")


# ===================================================================
# CONSORT COUNTS
# ===================================================================
print("\n" + "=" * 60 + "\nCONSORT COUNTS\n" + "=" * 60)
consort_rows = [
    {"Site": "AoU", "Metric": "total_participants", "Value": 413457},
    {"Site": "AoU", "Metric": "covid_positive", "Value": 25160},
    {"Site": "AoU", "Metric": "hospitalized_strict_14d", "Value": 4064},
    {"Site": "AoU", "Metric": "outpatient_controls", "Value": 21096},
]


def read_reuse(site_dir):
    for fname in ["07b_control_reuse.csv", "06b_control_reuse.csv"]:
        path = os.path.join(site_dir, fname)
        if os.path.exists(path):
            df = pd.read_csv(path)
            return {r.metric: r.value for _, r in df.iterrows()}
    return None


aou_reuse = read_reuse(os.path.join(BASE, "aou_v7"))
if aou_reuse:
    n_ctrl = int(aou_reuse.get("n_control_rows", 0))
    consort_rows.extend(
        [
            {"Site": "AoU", "Metric": "matched_observations", "Value": 4064 + n_ctrl},
            {"Site": "AoU", "Metric": "control_observations", "Value": n_ctrl},
        ]
    )
consort_rows.append({"Site": "MS", "Metric": "covid_positive", "Value": 4423200})
ms_reuse = read_reuse(os.path.join(BASE, "ms"))
if ms_reuse:
    ms_ctrl = int(ms_reuse.get("n_control_rows", 0))
    ms_dropped = int(ms_reuse.get("n_cases_dropped", 0))
    ms_cases = 139489 - ms_dropped
    consort_rows.extend(
        [
            {
                "Site": "MS",
                "Metric": "matched_observations",
                "Value": ms_cases + ms_ctrl,
            },
            {"Site": "MS", "Metric": "matched_strata", "Value": ms_cases},
        ]
    )
pd.DataFrame(consort_rows).to_csv(
    os.path.join(TBL_DIR, "consort_counts.csv"), index=False
)
print(f"  Saved: {TBL_DIR}/consort_counts.csv")
print(f"\n{'='*60}\nALL OUTPUTS: {FIG_DIR}/ and {TBL_DIR}/\n{'='*60}")
