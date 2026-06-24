#!/usr/bin/env python3
"""
COVID-19 Severity × SDoH — Table 1 & Table 2 (Aggregate Only)
Runs ON-PLATFORM (AoU Workbench or Quartz). Reads person-level CSVs,
outputs ONLY aggregate counts safe to export. Applies AoU <20 cell suppression.

Usage: python 04_tables.py aou_v7
       python 04_tables.py ms

Output: results/{cohort}/table1_demographics.csv
        results/{cohort}/table2_sdoh.csv  (AoU only)
"""

import os
import sys

import pandas as pd

if len(sys.argv) < 2 or sys.argv[1] not in ("aou_v7", "aou_v8", "ms"):
    print("Usage: python 04_tables.py [aou_v7|aou_v8|ms]")
    sys.exit(1)

COHORT = sys.argv[1]
RESULTS = f"results/{COHORT}"

# ── Auto-detect old vs new pipeline ──────────────────────────────────
reg_path = os.path.join(RESULTS, "08_regression_base.csv")
if not os.path.exists(reg_path):
    reg_path = os.path.join(RESULTS, "07_regression_base.csv")
if not os.path.exists(reg_path):
    print(f"  ERROR: No regression base found in {RESULTS}/")
    sys.exit(1)

reg = pd.read_csv(reg_path)
print(f"Loaded {reg_path}: {len(reg):,} rows")

matched_path = os.path.join(RESULTS, "07_matched_cohort.csv")
if not os.path.exists(matched_path):
    matched_path = os.path.join(RESULTS, "06_matched_cohort.csv")


# ── AoU cell suppression ─────────────────────────────────────────────
def safe_n(n, total):
    if n < 20:
        return "<20", ""
    return f"{n:,}", f"({n/total*100:.1f})"


def table_row(label, case_n, case_total, ctrl_n, ctrl_total):
    cn, cp = safe_n(case_n, case_total)
    ctn, ctp = safe_n(ctrl_n, ctrl_total)
    return {
        "Variable": label,
        "Cases_n": cn,
        "Cases_pct": cp,
        "Controls_n": ctn,
        "Controls_pct": ctp,
    }


# ── Split cases vs controls ──────────────────────────────────────────
cases = reg[reg.Treatment == 1]
ctrls = reg[reg.Treatment == 0]
nc, nk = len(cases), len(ctrls)

print(f"\n{'='*70}")
print(f"TABLE 1: Demographic and Clinical Characteristics [{COHORT.upper()}]")
print(f"{'='*70}")
print(f"  Cases: {nc:,}  |  Controls: {nk:,}\n")

rows = []
rows.append(
    {
        "Variable": "N",
        "Cases_n": f"{nc:,}",
        "Cases_pct": "",
        "Controls_n": f"{nk:,}",
        "Controls_pct": "",
    }
)

# Sex
for val in ["Female", "Male", "Other"]:
    cn = (cases.sex_at_birth == val).sum()
    kn = (ctrls.sex_at_birth == val).sum()
    rows.append(table_row(f"  {val}", cn, nc, kn, nk))

# Race (AoU only)
if "race" in reg.columns and reg.race.nunique() > 1 and any(reg.race != "Unknown"):
    rows.append(
        {
            "Variable": "Race",
            "Cases_n": "",
            "Cases_pct": "",
            "Controls_n": "",
            "Controls_pct": "",
        }
    )
    for val in ["White", "Black", "Asian", "Other"]:
        cn = (cases.race == val).sum()
        kn = (ctrls.race == val).sum()
        rows.append(table_row(f"  {val}", cn, nc, kn, nk))

# Ethnicity (AoU only)
if "ethnicity" in reg.columns and any(reg.ethnicity != "Unknown"):
    rows.append(
        {
            "Variable": "Ethnicity",
            "Cases_n": "",
            "Cases_pct": "",
            "Controls_n": "",
            "Controls_pct": "",
        }
    )
    for val in ["Not Hispanic", "Hispanic", "Other"]:
        cn = (cases.ethnicity == val).sum()
        kn = (ctrls.ethnicity == val).sum()
        rows.append(table_row(f"  {val}", cn, nc, kn, nk))

# Age
rows.append(
    {
        "Variable": "Age group",
        "Cases_n": "",
        "Cases_pct": "",
        "Controls_n": "",
        "Controls_pct": "",
    }
)
for val in ["<45", "45-54", "55-64", "65+"]:
    cn = (cases.age_group == val).sum()
    kn = (ctrls.age_group == val).sum()
    rows.append(table_row(f"  {val}", cn, nc, kn, nk))

if "age_at_covid" in reg.columns:
    cm, cs = cases.age_at_covid.mean(), cases.age_at_covid.std()
    km, ks = ctrls.age_at_covid.mean(), ctrls.age_at_covid.std()
    rows.append(
        {
            "Variable": "  Mean age (SD)",
            "Cases_n": f"{cm:.1f}",
            "Cases_pct": f"({cs:.1f})",
            "Controls_n": f"{km:.1f}",
            "Controls_pct": f"({ks:.1f})",
        }
    )

# Vaccination
rows.append(
    {
        "Variable": "Vaccination",
        "Cases_n": "",
        "Cases_pct": "",
        "Controls_n": "",
        "Controls_pct": "",
    }
)
for val in ["Vaccinated", "Unknown"]:
    cn = (cases.vaccination == val).sum()
    kn = (ctrls.vaccination == val).sum()
    rows.append(table_row(f"  {val}", cn, nc, kn, nk))

# Plan type (MS only)
if "plan_type" in reg.columns:
    rows.append(
        {
            "Variable": "Plan type",
            "Cases_n": "",
            "Cases_pct": "",
            "Controls_n": "",
            "Controls_pct": "",
        }
    )
    for val in [
        "PPO",
        "HMO",
        "POS",
        "HDHP",
        "CDHP",
        "EPO",
        "Comprehensive",
        "Basic",
        "Unknown",
    ]:
        cn = (cases.plan_type == val).sum()
        kn = (ctrls.plan_type == val).sum()
        if cn + kn > 0:
            rows.append(table_row(f"  {val}", cn, nc, kn, nk))

# Region (MS only)
if "region_name" in reg.columns:
    rows.append(
        {
            "Variable": "Region",
            "Cases_n": "",
            "Cases_pct": "",
            "Controls_n": "",
            "Controls_pct": "",
        }
    )
    for val in ["South", "NorthCentral", "West", "Northeast", "Unknown"]:
        cn = (cases.region_name == val).sum()
        kn = (ctrls.region_name == val).sum()
        if cn + kn > 0:
            rows.append(table_row(f"  {val}", cn, nc, kn, nk))

# Charlson comorbidities
como_cols = [
    c
    for c in reg.columns
    if c
    in [
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
        "AIDS",
        "Metastatic_Solid_Tumor",
        "Malignancy",
    ]
]

rows.append(
    {
        "Variable": "Charlson comorbidities",
        "Cases_n": "",
        "Cases_pct": "",
        "Controls_n": "",
        "Controls_pct": "",
    }
)
for col in como_cols:
    cn = cases[col].sum()
    kn = ctrls[col].sum()
    label = col.replace("_", " ")
    rows.append(table_row(f"  {label}", int(cn), nc, int(kn), nk))

table1 = pd.DataFrame(rows)
table1.to_csv(f"{RESULTS}/table1_demographics.csv", index=False)

print(f"{'Variable':45s} {'Cases':>15s} {'Controls':>15s}")
print("-" * 75)
for _, r in table1.iterrows():
    c_str = f"{r.Cases_n} {r.Cases_pct}" if r.Cases_pct else r.Cases_n
    k_str = f"{r.Controls_n} {r.Controls_pct}" if r.Controls_pct else r.Controls_n
    print(f"{r.Variable:45s} {c_str:>15s} {k_str:>15s}")

print(f"\nSaved: {RESULTS}/table1_demographics.csv")


# ══════════════════════════════════════════════════════════════════════
# TABLE 2: SDoH (AoU only)
# ══════════════════════════════════════════════════════════════════════
sdoh_path = f"{RESULTS}/04_sdoh.csv"

if os.path.exists(sdoh_path) and COHORT.startswith("aou"):
    print(f"\n{'='*70}")
    print(f"TABLE 2: SDoH Characteristics [{COHORT.upper()}]")
    print(f"{'='*70}")

    sdoh = pd.read_csv(sdoh_path)
    matched = pd.read_csv(reg_path)  # fixme: use post-trim 08_regression_base.csv
    sdoh_matched = matched[["person_id", "Treatment"]].merge(
        sdoh, on="person_id", how="left"
    )
    s_cases = sdoh_matched[sdoh_matched.Treatment == 1]
    s_ctrls = sdoh_matched[sdoh_matched.Treatment == 0]
    snc, snk = len(s_cases), len(s_ctrls)

    rows2 = []

    def sdoh_section(df_c, df_k, col, values, section_label):
        rows2.append(
            {
                "Variable": section_label,
                "Cases_n": "",
                "Cases_pct": "",
                "Controls_n": "",
                "Controls_pct": "",
            }
        )
        for val in values:
            cn = (df_c[col] == val).sum() if col in df_c.columns else 0
            kn = (df_k[col] == val).sum() if col in df_k.columns else 0
            rows2.append(table_row(f"  {val}", int(cn), snc, int(kn), snk))
        cn = df_c[col].isna().sum() if col in df_c.columns else snc
        kn = df_k[col].isna().sum() if col in df_k.columns else snk
        rows2.append(table_row("  Missing", int(cn), snc, int(kn), snk))

    sdoh_section(
        s_cases,
        s_ctrls,
        "income",
        [
            "less_10k",
            "10k_25k",
            "25k_35k",
            "35k_100k",
            "100k_150k",
            "150k_200k",
            "more_200k",
        ],
        "Income",
    )
    sdoh_section(
        s_cases,
        s_ctrls,
        "employment",
        ["Employed", "Student", "Unemployed", "Others"],
        "Employment",
    )
    sdoh_section(
        s_cases,
        s_ctrls,
        "education",
        ["Never_Attended", "Below_GED", "GED_or_College", "Advanced"],
        "Education",
    )
    sdoh_section(s_cases, s_ctrls, "housing", ["Own", "Rent", "Others"], "Housing")
    sdoh_section(
        s_cases,
        s_ctrls,
        "housing_stability",
        ["Stable", "Unstable"],
        "Housing Stability",
    )
    sdoh_section(s_cases, s_ctrls, "disability_any", ["Yes", "No"], "Disability (any)")

    # Insurance (hierarchical categorical from insurance_type column)
    sdoh_section(
        s_cases,
        s_ctrls,
        "insurance_type",
        ["Employer", "Medicare", "Medicaid", "Other_None", "Missing"],
        "Insurance type",
    )

    table2 = pd.DataFrame(rows2)
    table2.to_csv(f"{RESULTS}/table2_sdoh.csv", index=False)

    print(f"{'Variable':45s} {'Cases':>15s} {'Controls':>15s}")
    print("-" * 75)
    for _, r in table2.iterrows():
        c_str = f"{r.Cases_n} {r.Cases_pct}" if r.Cases_pct else r.Cases_n
        k_str = f"{r.Controls_n} {r.Controls_pct}" if r.Controls_pct else r.Controls_n
        print(f"{r.Variable:45s} {c_str:>15s} {k_str:>15s}")

    print(f"\nSaved: {RESULTS}/table2_sdoh.csv")
else:
    print(f"\n  No SDoH data for {COHORT} — skipping Table 2.")

print(f"\n{'='*70}")
print("DONE. Output CSVs contain ONLY aggregate counts (no person_id).")
print("Safe to export, commit to GitHub, or paste into chat.")
print("=" * 70)
