#!/usr/bin/env python3
"""
COVID-19 Severity × SDoH — Pre/Post Matching Balance (SMD)
FULL-COVARIATE VERSION: computes SMDs for matching variables,
demographics, comorbidities, vaccination, wave, AND SDoH.

Runs ON-PLATFORM (AoU Workbench or Quartz HPC).

Changes from v5:
  - Full-covariate SMDs (all model covariates, not just 3 matching vars)
  - Post-matching SDoH SMDs (expected to be non-trivial since SDoH
    was NOT in the propensity model — that's the methodological point)
  - Love plot includes all covariates
  - AoU cell suppression for N < 20

Usage: python 05_smd_onplatform.py aou_v7
       python 05_smd_onplatform.py ms

Output: results/{cohort}/etable_smd_pre_matching.csv
        results/{cohort}/etable_smd_post_matching.csv
        results/{cohort}/etable_smd_full_covariates.csv  (NEW)
        results/figures/efig_love_plot_{cohort}_full.pdf  (NEW)
"""

import os
import sys

import numpy as np
import pandas as pd

if len(sys.argv) < 2 or sys.argv[1] not in ("aou_v7", "aou_v8", "ms"):
    print("Usage: python 05_smd_onplatform.py [aou_v7|aou_v8|ms]")
    sys.exit(1)

COHORT = sys.argv[1]
IS_AOU = COHORT.startswith("aou")
RESULTS = f"results/{COHORT}"
RECOMPUTE = "--recompute" in sys.argv

print("=" * 70)
print(f"PRE/POST MATCHING BALANCE (FULL COVARIATES)  [{COHORT.upper()}]")
print("=" * 70)

# ── Load data ─────────────────────────────────────────────────────────
cohort = pd.read_csv(f"{RESULTS}/01_covid_cohort.csv")
matched = pd.read_csv(f"{RESULTS}/06_matched_cohort.csv")
reg = pd.read_csv(f"{RESULTS}/07_regression_base.csv")

# SDoH (AoU only)
sdoh_path = f"{RESULTS}/04_sdoh.csv"
has_sdoh = IS_AOU and os.path.exists(sdoh_path)
if has_sdoh:
    sdoh = pd.read_csv(sdoh_path)
    if sdoh.shape[1] <= 1:
        has_sdoh = False

print(f"  Cohort: {len(cohort):,}  |  Matched: {len(matched):,}")
print(f"  Regression df: {len(reg):,}  |  SDoH: {has_sdoh}")


# ── SMD functions ─────────────────────────────────────────────────────
def smd_continuous(cases, controls, col):
    """SMD for continuous variable (Cohen's d, pooled SD)."""
    c = cases[col].dropna()
    k = controls[col].dropna()
    if len(c) == 0 or len(k) == 0:
        return np.nan
    m1, s1 = c.mean(), c.std()
    m2, s2 = k.mean(), k.std()
    pooled_sd = np.sqrt((s1**2 + s2**2) / 2)
    if pooled_sd == 0:
        return 0.0
    return (m1 - m2) / pooled_sd


def smd_binary(cases, controls, col, val=1):
    """SMD for binary/indicator variable."""
    p1 = (cases[col] == val).mean()
    p2 = (controls[col] == val).mean()
    pooled_sd = np.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / 2)
    if pooled_sd == 0:
        return 0.0
    return (p1 - p2) / pooled_sd


def smd_categorical(cases, controls, col, target_val):
    """SMD for a specific level of a categorical variable."""
    p1 = (cases[col] == target_val).mean() if col in cases.columns else 0
    p2 = (controls[col] == target_val).mean() if col in controls.columns else 0
    pooled_sd = np.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / 2)
    if pooled_sd == 0:
        return 0.0
    return (p1 - p2) / pooled_sd


def fmt_pct(cases, controls, col, val):
    """Format as 'N (%)' for a categorical level."""
    cn = (cases[col] == val).sum() if col in cases.columns else 0
    kn = (controls[col] == val).sum() if col in controls.columns else 0
    cp = cn / len(cases) * 100 if len(cases) > 0 else 0
    kp = kn / len(controls) * 100 if len(controls) > 0 else 0
    return f"{cn:,} ({cp:.1f}%)", f"{kn:,} ({kp:.1f}%)"


# ── Reconstruct matching variables ───────────────────────────────────
CACHE_PATH = f"{RESULTS}/cache_match_vars.csv"

if os.path.exists(CACHE_PATH) and not RECOMPUTE:
    print(f"  Loading cached match vars from {CACHE_PATH}")
    match_vars = pd.read_csv(CACHE_PATH)
    if IS_AOU:
        MATCH_COLS = ["enrollment_ord", "num_diagnosis", "ehr_length_days"]
        MATCH_LABELS = {
            "enrollment_ord": "Enrollment date (ordinal)",
            "num_diagnosis": "Number of diagnoses",
            "ehr_length_days": "Length of EHR history (days)",
        }
    else:
        MATCH_COLS = ["enrollment_ord", "num_diagnosis", "coverage_span_days"]
        MATCH_LABELS = {
            "enrollment_ord": "Enrollment date (ordinal)",
            "num_diagnosis": "Number of diagnoses",
            "coverage_span_days": "Coverage span (days)",
        }
elif IS_AOU:
    CDR = os.environ.get("WORKSPACE_CDR", "")
    print(f"  CDR: {CDR}")

    match_sql = f"""
    SELECT p.person_id,
      MIN(o.observation_date) AS basics_survey_date,
      COUNT(DISTINCT co.condition_concept_id) AS num_diagnosis,
      DATE_DIFF(MAX(co.condition_start_date),
                MIN(co.condition_start_date), DAY) AS ehr_length_days
    FROM `{CDR}`.person p
    JOIN `{CDR}`.observation o
      ON p.person_id = o.person_id
      AND o.observation_source_concept_id = 1585845
    JOIN `{CDR}`.condition_occurrence co
      ON p.person_id = co.person_id
    WHERE p.person_id IN ({','.join(map(str, cohort.person_id.tolist()))})
    GROUP BY p.person_id
    """
    print("  Querying matching variables from BigQuery...")
    match_vars = pd.read_gbq(match_sql, dialect="standard")
    match_vars["enrollment_ord"] = pd.to_datetime(
        match_vars["basics_survey_date"]
    ).apply(lambda x: x.toordinal() if pd.notna(x) else np.nan)

    MATCH_LABELS = {
        "enrollment_ord": "Enrollment date (ordinal)",
        "num_diagnosis": "Number of diagnoses",
        "ehr_length_days": "Length of EHR history (days)",
    }
    MATCH_COLS = list(MATCH_LABELS.keys())

else:  # MarketScan
    import duckdb

    MS_DIR = "/N/project/Marketscan1/parquet"
    YEARS = ["2020", "2021", "2022", "2023"]
    con = duckdb.connect(database=":memory:")
    con.execute("PRAGMA threads=4")

    dx_unions = []
    for y in YEARS:
        for src, cols in [
            ("i", ["PDX"] + [f"DX{i}" for i in range(1, 16)]),
            ("o", ["DX1", "DX2", "DX3", "DX4"]),
        ]:
            f = f"{MS_DIR}/mscan_{y}_{src}.parquet"
            if not os.path.exists(f):
                continue
            for col in cols:
                dx_unions.append(f"""
                SELECT ENROLID AS person_id,
                       REPLACE(UPPER(CAST({col} AS VARCHAR)),'.','') AS dx_code
                FROM read_parquet('{f}') WHERE {col} IS NOT NULL""")

    con.register("covid_pids", pd.DataFrame({"person_id": cohort.person_id.tolist()}))
    con.sql(f"""
    CREATE TABLE dx_long AS
    SELECT DISTINCT person_id, dx_code
    FROM ({' UNION ALL '.join(dx_unions)}) sub
    WHERE person_id IN (SELECT person_id FROM covid_pids)
    """)
    dx_counts = con.sql("""
    SELECT person_id, COUNT(DISTINCT dx_code) AS num_diagnosis
    FROM dx_long GROUP BY person_id
    """).df()

    enroll_unions = []
    for y in YEARS:
        f = f"{MS_DIR}/mscan_{y}_t.parquet"
        if os.path.exists(f):
            enroll_unions.append(
                f"SELECT ENROLID AS person_id, DTSTART, DTEND FROM read_parquet('{f}')"
            )

    enroll_dates = con.sql(f"""
    SELECT e.person_id,
           MIN(e.DTSTART) AS first_enrollment,
           DATEDIFF('day', MIN(e.DTSTART), MAX(e.DTEND)) AS coverage_span_days
    FROM ({' UNION ALL '.join(enroll_unions)}) e
    WHERE e.person_id IN (SELECT person_id FROM covid_pids)
    GROUP BY e.person_id
    """).df()
    enroll_dates["enrollment_ord"] = pd.to_datetime(
        enroll_dates["first_enrollment"]
    ).apply(lambda x: x.toordinal() if pd.notna(x) else np.nan)

    match_vars = dx_counts.merge(
        enroll_dates[["person_id", "enrollment_ord", "coverage_span_days"]],
        on="person_id",
        how="inner",
    )
    con.close()

    MATCH_LABELS = {
        "enrollment_ord": "Enrollment date (ordinal)",
        "num_diagnosis": "Number of diagnoses",
        "coverage_span_days": "Coverage span (days)",
    }
    MATCH_COLS = list(MATCH_LABELS.keys())

# Cache matching vars
match_vars.to_csv(CACHE_PATH, index=False)
print(f"  Cached: {CACHE_PATH}")


# ══════════════════════════════════════════════════════════════════════
# MATCHING VARIABLE SMDs (eTables S6/S7 — same as before)
# ══════════════════════════════════════════════════════════════════════


def format_median_iqr(series):
    med = series.median()
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    return f"{med:,.0f} ({q1:,.0f}\u2013{q3:,.0f})"


mv = match_vars.merge(cohort[["person_id", "severity"]], on="person_id")
mv = mv.dropna(subset=MATCH_COLS)

pre_cases = mv[mv.severity == 1]
pre_controls = mv[mv.severity == 0]

print(f"\n{'='*60}")
print("eTable S6: Pre-Matching Balance (matching variables)")
print("=" * 60)

pre_rows = []
for col in MATCH_COLS:
    smd = smd_continuous(pre_cases, pre_controls, col)
    pre_rows.append(
        {
            "Variable": MATCH_LABELS[col],
            f"Cases (N={len(pre_cases):,})": format_median_iqr(pre_cases[col]),
            f"Controls (N={len(pre_controls):,})": format_median_iqr(pre_controls[col]),
            "SMD": f"{smd:.3f}",
        }
    )
pre_df = pd.DataFrame(pre_rows)
pre_df.to_csv(f"{RESULTS}/etable_smd_pre_matching.csv", index=False)
print(pre_df.to_string(index=False))

# Post-matching (matching vars only)
post = matched.merge(match_vars, on="person_id", how="left").dropna(subset=MATCH_COLS)
post_cases = post[post.Treatment == 1]
post_controls = post[post.Treatment == 0]

print(f"\n{'='*60}")
print("eTable S7: Post-Matching Balance (matching variables)")
print("=" * 60)

post_rows = []
for col in MATCH_COLS:
    smd = smd_continuous(post_cases, post_controls, col)
    post_rows.append(
        {
            "Variable": MATCH_LABELS[col],
            f"Cases (N={len(post_cases):,})": format_median_iqr(post_cases[col]),
            f"Controls (N={len(post_controls):,})": format_median_iqr(
                post_controls[col]
            ),
            "SMD": f"{smd:.3f}",
        }
    )
post_df = pd.DataFrame(post_rows)
post_df.to_csv(f"{RESULTS}/etable_smd_post_matching.csv", index=False)
print(post_df.to_string(index=False))


# ══════════════════════════════════════════════════════════════════════
# FULL-COVARIATE SMDs (NEW — eTables S7b)
# All model covariates: demographics, comorbidities, vaccination, wave
# Plus post-matching SDoH imbalance (expected to be non-trivial)
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print("FULL-COVARIATE POST-MATCHING BALANCE")
print("=" * 60)

# Build full regression df with SDoH
if has_sdoh:
    reg_full = reg.merge(sdoh, on="person_id", how="left")
else:
    reg_full = reg.copy()

full_cases = reg_full[reg_full.Treatment == 1]
full_controls = reg_full[reg_full.Treatment == 0]

# Comorbidity columns
COMO = [
    "Myocardial_Infarction",
    "Congestive_Heart_Failure",
    "Peripheral_Vascular_Disease",
    "Cerebrovascular_Disease",
    "Dementia",
    "Chronic_Pulmonary_Disease",
    "Rheumatic_Disease",
    "Peptic_Ulcer_Disease",
    "Liver_Disease_Mild",
    "Liver_Disease_Moderate_Severe",
    "Diabetes_without_Chronic_Complications",
    "Diabetes_with_Chronic_Complications",
    "Hemiplegia_Paraplegia",
    "Renal_Disease_Mild_Moderate",
    "Renal_Disease_Severe",
    "HIV",
    "Metastatic_Solid_Tumor",
    "Malignancy",
    "AIDS",
]

# Labels for display
COMO_LABELS = {c: c.replace("_", " ") for c in COMO}

full_smd_rows = []

# Group: Matching variables
for col in MATCH_COLS:
    if col in reg_full.columns:
        smd = smd_continuous(full_cases, full_controls, col)
        full_smd_rows.append(
            {
                "Group": "Matching",
                "Variable": MATCH_LABELS[col],
                "Post-matching SMD": smd,
            }
        )

# Group: Demographics (categorical)
DEMO_CATS = {
    "sex_at_birth": {"Female": "Female sex", "Male": "Male sex", "Other": "Other sex"},
    "age_group": {
        "<45": "Age <45",
        "45-54": "Age 45\u201354",
        "55-64": "Age 55\u201364",
        "65+": "Age \u226565",
    },
}
if IS_AOU:
    DEMO_CATS["race"] = {
        "White": "White",
        "Black": "Black",
        "Asian": "Asian",
        "Other": "Other race",
    }
    DEMO_CATS["ethnicity"] = {
        "Not Hispanic": "Not Hispanic",
        "Hispanic": "Hispanic",
        "Other": "Other ethnicity",
    }

for col, vals in DEMO_CATS.items():
    if col not in reg_full.columns:
        continue
    for val, label in vals.items():
        smd = smd_categorical(full_cases, full_controls, col, val)
        full_smd_rows.append(
            {
                "Group": "Demographics",
                "Variable": label,
                "Post-matching SMD": smd,
            }
        )

# Group: Vaccination
if "vaccination" in reg_full.columns:
    smd = smd_categorical(full_cases, full_controls, "vaccination", "Vaccinated")
    full_smd_rows.append(
        {
            "Group": "Clinical",
            "Variable": "Vaccinated before index",
            "Post-matching SMD": smd,
        }
    )

# Group: Pandemic wave
if "pandemic_wave" in reg_full.columns:
    for w, label in [
        ("pre_delta", "Pre-Delta"),
        ("delta", "Delta"),
        ("omicron", "Omicron"),
    ]:
        smd = smd_categorical(full_cases, full_controls, "pandemic_wave", w)
        full_smd_rows.append(
            {
                "Group": "Clinical",
                "Variable": f"Wave: {label}",
                "Post-matching SMD": smd,
            }
        )

# Group: Charlson comorbidities
for col in COMO:
    if col not in reg_full.columns:
        continue
    smd = smd_binary(full_cases, full_controls, col)
    full_smd_rows.append(
        {
            "Group": "Comorbidities",
            "Variable": COMO_LABELS[col],
            "Post-matching SMD": smd,
        }
    )

# Group: SDoH (AoU only — expected non-trivial post-matching)
if has_sdoh:
    SDOH_CATS = {
        "insurance_type": {
            "Employer": "Insurance: Employer",
            "Medicare": "Insurance: Medicare",
            "Medicaid": "Insurance: Medicaid",
            "Other_None": "Insurance: Other/None",
        },
        "income": {
            "less_10k": "Income: <$10K",
            "10k_25k": "Income: $10\u201325K",
            "25k_35k": "Income: $25\u201335K",
            "35k_100k": "Income: $35\u2013100K",
            "100k_150k": "Income: $100\u2013150K",
            "150k_200k": "Income: $150\u2013200K",
            "more_200k": "Income: \u2265$200K",
        },
        "education": {
            "Below_GED": "Education: Below GED",
            "GED_or_College": "Education: GED/some college",
            "Advanced": "Education: College+",
        },
        "employment": {
            "Employed": "Employment: Employed",
            "Unemployed": "Employment: Unemployed",
            "Others": "Employment: Retired/other",
        },
        "housing": {
            "Own": "Housing: Own",
            "Rent": "Housing: Rent",
        },
        "housing_stability": {
            "Stable": "Housing: Stable",
            "Unstable": "Housing: Unstable",
        },
        "disability_any": {
            "Yes": "Disability: Any",
            "No": "Disability: No",
        },
    }

    for col, vals in SDOH_CATS.items():
        if col not in reg_full.columns:
            continue
        for val, label in vals.items():
            smd = smd_categorical(full_cases, full_controls, col, val)
            full_smd_rows.append(
                {
                    "Group": "SDoH",
                    "Variable": label,
                    "Post-matching SMD": smd,
                }
            )

full_smd_df = pd.DataFrame(full_smd_rows)
full_smd_df["Abs SMD"] = full_smd_df["Post-matching SMD"].abs()
full_smd_df.to_csv(f"{RESULTS}/etable_smd_full_covariates.csv", index=False)

print(f"\n  {'Variable':50s} {'SMD':>8s}  {'|SMD|':>8s}")
print("  " + "-" * 70)
for _, r in full_smd_df.iterrows():
    flag = (
        "  ***"
        if abs(r["Post-matching SMD"]) > 0.10
        else "  **" if abs(r["Post-matching SMD"]) > 0.05 else ""
    )
    print(f"  {r.Variable:50s} {r['Post-matching SMD']:+.4f}  {r['Abs SMD']:.4f}{flag}")

n_imbalanced = (full_smd_df["Abs SMD"] > 0.10).sum()
print(f"\n  Variables with |SMD| > 0.10: {n_imbalanced}")
print(f"  Variables with |SMD| > 0.05: {(full_smd_df['Abs SMD'] > 0.05).sum()}")

# Highlight SDoH imbalance (expected because SDoH not in propensity model)
if has_sdoh:
    sdoh_rows = full_smd_df[full_smd_df.Group == "SDoH"]
    sdoh_imbalanced = sdoh_rows[sdoh_rows["Abs SMD"] > 0.05]
    if len(sdoh_imbalanced) > 0:
        print(
            f"\n  SDoH variables with |SMD| > 0.05 (expected — SDoH not in PS model):"
        )
        for _, r in sdoh_imbalanced.iterrows():
            print(f"    {r.Variable:50s} {r['Post-matching SMD']:+.4f}")


# ══════════════════════════════════════════════════════════════════════
# eFigure S1: FULL-COVARIATE LOVE PLOT
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print("eFigure S1: Full-Covariate Love Plot")
print("=" * 60)

import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42
mpl.rcParams["font.family"] = "sans-serif"
mpl.rcParams["font.sans-serif"] = ["Arial", "Helvetica", "DejaVu Sans"]
mpl.rcParams["font.size"] = 6
mpl.rcParams["axes.linewidth"] = 0.5
mpl.rcParams["figure.facecolor"] = "white"
mpl.rcParams["savefig.dpi"] = 600

# Color coding by group
GROUP_COLORS = {
    "Matching": "#E69F00",  # amber
    "Demographics": "#56B4E9",  # sky blue
    "Clinical": "#009E73",  # green
    "Comorbidities": "#0072B2",  # blue
    "SDoH": "#D55E00",  # vermillion
}

# Sort: matching first, then by |SMD| descending within group
group_order = ["Matching", "Demographics", "Clinical", "Comorbidities", "SDoH"]
full_smd_df["group_order"] = full_smd_df.Group.apply(
    lambda x: group_order.index(x) if x in group_order else 99
)
plot_df = full_smd_df.sort_values(
    ["group_order", "Abs SMD"], ascending=[True, False]
).reset_index(drop=True)

n_vars = len(plot_df)
fig_height = max(4, n_vars * 0.18 + 1.0)

fig, ax = plt.subplots(figsize=(4.724, min(fig_height, 12)))
y = np.arange(n_vars)[::-1]

# Plot points colored by group
for i, (_, r) in enumerate(plot_df.iterrows()):
    color = GROUP_COLORS.get(r.Group, "#999999")
    ax.scatter(
        r["Abs SMD"],
        y[i],
        color=color,
        s=20,
        zorder=3,
        edgecolors="black",
        linewidths=0.3,
    )

# Reference lines
ax.axvline(0.10, color="black", linewidth=0.5, linestyle="--", zorder=1)
ax.axvline(0.05, color="#999999", linewidth=0.3, linestyle=":", zorder=1)

# Add threshold labels at top
ax.text(0.10, y[0] + 0.7, "|SMD|=0.1", fontsize=5, ha="center", color="black")
ax.text(0.05, y[0] + 0.7, "0.05", fontsize=5, ha="center", color="#999999")

ax.set_yticks(y)
ax.set_yticklabels(plot_df.Variable.tolist(), fontsize=5)
ax.set_xlabel("|Standardized Mean Difference|", fontsize=7)
ax.set_xlim(-0.01, max(plot_df["Abs SMD"].max() * 1.15, 0.15))
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Add group labels via colored patches in legend
from matplotlib.lines import Line2D

legend_handles = [
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=c,
        markeredgecolor="black",
        markeredgewidth=0.3,
        markersize=5,
        label=g,
    )
    for g, c in GROUP_COLORS.items()
    if g in plot_df.Group.values
]
ax.legend(
    handles=legend_handles, fontsize=5, loc="lower right", frameon=False, borderpad=0.5
)

# Add gray band for SDoH section to highlight
if has_sdoh:
    sdoh_indices = [
        i for i, (_, r) in enumerate(plot_df.iterrows()) if r.Group == "SDoH"
    ]
    if sdoh_indices:
        ymin = y[max(sdoh_indices)] - 0.4
        ymax = y[min(sdoh_indices)] + 0.4
        ax.axhspan(ymin, ymax, color="#FFF3E0", alpha=0.5, zorder=0)

FIG_DIR = os.path.join(os.path.dirname(RESULTS), "figures")
os.makedirs(FIG_DIR, exist_ok=True)
love_path = os.path.join(FIG_DIR, f"efig_love_plot_{COHORT}_full")
fig.savefig(f"{love_path}.pdf", bbox_inches="tight")
fig.savefig(f"{love_path}.png", bbox_inches="tight")
print(f"  Saved: {love_path}.pdf/.png")
plt.close(fig)


# ── Also produce the simple 3-variable Love plot (backward compat) ────
print("\n  Also generating simple matching-variable Love plot...")

pre_smds_abs = [abs(smd_continuous(pre_cases, pre_controls, c)) for c in MATCH_COLS]
post_smds_abs = [abs(smd_continuous(post_cases, post_controls, c)) for c in MATCH_COLS]
labels_simple = [MATCH_LABELS[c] for c in MATCH_COLS]

fig2, ax2 = plt.subplots(figsize=(4.724, 2.5))
y2 = np.arange(len(labels_simple))[::-1]

ax2.scatter(
    pre_smds_abs,
    y2,
    marker="o",
    facecolors="none",
    edgecolors="#D55E00",
    s=40,
    linewidths=1.0,
    zorder=3,
    label="Before matching",
)
ax2.scatter(
    post_smds_abs,
    y2,
    marker="o",
    facecolors="#0072B2",
    edgecolors="#0072B2",
    s=40,
    linewidths=1.0,
    zorder=4,
    label="After matching",
)

for i in range(len(labels_simple)):
    ax2.annotate(
        "",
        xy=(post_smds_abs[i], y2[i]),
        xytext=(pre_smds_abs[i], y2[i]),
        arrowprops=dict(arrowstyle="->", color="#999999", lw=0.6),
    )

ax2.axvline(0.1, color="black", linewidth=0.5, linestyle="--", zorder=1)
ax2.text(0.105, y2.max() + 0.3, "|SMD| = 0.1", fontsize=6, va="bottom")
ax2.set_yticks(y2)
ax2.set_yticklabels(labels_simple, fontsize=7)
ax2.set_xlabel("|Standardized Mean Difference|", fontsize=7)
ax2.set_xlim(-0.02, max(max(pre_smds_abs), 0.15) * 1.15)
ax2.legend(fontsize=6, loc="upper right")
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

simple_path = os.path.join(FIG_DIR, f"efig_love_plot_{COHORT}")
fig2.savefig(f"{simple_path}.pdf", bbox_inches="tight")
fig2.savefig(f"{simple_path}.png", bbox_inches="tight")
print(f"  Saved: {simple_path}.pdf/.png")
plt.close(fig2)


# ── Summary ───────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("OUTPUTS")
print("=" * 60)
print(f"  {RESULTS}/etable_smd_pre_matching.csv       (eTable S6)")
print(f"  {RESULTS}/etable_smd_post_matching.csv       (eTable S7)")
print(f"  {RESULTS}/etable_smd_full_covariates.csv     (eTable S7b)")
print(f"  {FIG_DIR}/efig_love_plot_{COHORT}_full.pdf   (eFigure S1)")
print(f"  {FIG_DIR}/efig_love_plot_{COHORT}.pdf        (eFigure S1 simple)")
print("\nAll CSVs contain ONLY aggregate statistics. Safe to export.")
