#!/usr/bin/env python3
"""
COVID-19 Severity × SDoH — Supplementary Tables Formatter
Reads aggregate CSVs from the pipeline and outputs publication-ready
supplementary tables. Runs ANYWHERE (no PII needed).

Usage: python 06_supplement.py [results_dir]

Inputs (from results/aou_v7/ and results/ms/):
  01b_phenotype_components.csv, 07b_control_reuse.csv,
  race_attenuation_table.csv, wave_stratified_income.csv,
  aids_sensitivity.csv, all_model_coefficients.csv,
  sensitivity_summary_comparison.csv

Output: results/tables/eTable_S*.csv
"""

import os
import sys

import pandas as pd

BASE = sys.argv[1] if len(sys.argv) > 1 else "results"
AOU_DIR = os.path.join(BASE, "aou_v7")
MS_DIR = os.path.join(BASE, "ms")
TBL_DIR = os.path.join(BASE, "tables")
os.makedirs(TBL_DIR, exist_ok=True)

print("=" * 70)
print("SUPPLEMENTARY TABLES FORMATTER")
print("=" * 70)


def load_csv(directory, filename, required=True):
    path = os.path.join(directory, filename)
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f"  Loaded: {path} ({len(df)} rows)")
        return df
    elif required:
        print(f"  WARNING: {path} not found")
    return None


def fmt_aor(row, aor_col="AOR", lo_col="CI_lower", hi_col="CI_upper"):
    return f"{row[aor_col]:.2f} ({row[lo_col]:.2f}\u2013{row[hi_col]:.2f})"


def fmt_p(p):
    if p < 0.001:
        return "<0.001"
    elif p < 0.01:
        return f"{p:.3f}"
    else:
        return f"{p:.2f}"


# ═══════════════════════════════════════════════════════════════════════
# eTable S2b: Phenotype component decomposition
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("eTable S2b: Phenotype Component Decomposition")
print("=" * 60)

components = load_csv(AOU_DIR, "01b_phenotype_components.csv")
if components is not None:
    COMPONENT_LABELS = {
        "Inpatient (9201/32037)": "Inpatient",
        "ER-to-Inpatient (262/8717)": "ED-to-inpatient",
        "ED prolonged >=1d (9203)": "ED with stay \u22651 day",
        "ED same-day <1d (9203)": "ED same-day (excluded from strict)",
        "ED null-end-date (9203)": "ED null end date (excluded from strict)",
    }
    STRICT = {
        "Inpatient (9201/32037)": "Yes",
        "ER-to-Inpatient (262/8717)": "Yes",
        "ED prolonged >=1d (9203)": "Yes",
        "ED same-day <1d (9203)": "No",
        "ED null-end-date (9203)": "No",
    }
    total_broad = components.n_persons.sum()
    rows = []
    for _, r in components.iterrows():
        rows.append(
            {
                "Component": COMPONENT_LABELS.get(r.component, r.component),
                "In strict?": STRICT.get(r.component, ""),
                "N": f"{int(r.n_persons):,}",
                "% of broad": f"{r.n_persons / total_broad * 100:.1f}",
            }
        )
    et = pd.DataFrame(rows)
    et.to_csv(os.path.join(TBL_DIR, "eTable_S2b_phenotype_components.csv"), index=False)
    print(et.to_string(index=False))


# ═══════════════════════════════════════════════════════════════════════
# eTable S10: Cross-site AOR comparison
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("eTable S10: Cross-Site Comparison")
print("=" * 60)

aou_all = load_csv(AOU_DIR, "all_model_coefficients.csv")
ms_all = load_csv(MS_DIR, "all_model_coefficients.csv", required=False)

if aou_all is not None and ms_all is not None:
    aou_base = aou_all[aou_all.model == "base"].copy()
    ms_base = ms_all[ms_all.model == "base"].copy()

    VAR_LABELS = {
        "f.sexFemale": "Female sex",
        "f.vaccVaccinated": "Vaccinated",
        "f.age45-54": "Age 45\u201354",
        "f.age55-64": "Age 55\u201364",
        "f.age65+": "Age \u226565",
        "f.raceBlack": "Black race",
        "f.raceAsian": "Asian race",
        "f.raceOther": "Other race",
        "f.ethnicityHispanic": "Hispanic",
        "f.wavedelta": "Delta wave",
        "f.waveomicron": "Omicron wave",
    }
    COMO_LABELS = {
        c: c.replace("_", " ")
        for c in [
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
    }
    ALL_LABELS = {**VAR_LABELS, **COMO_LABELS}

    rows = []
    for var in list(VAR_LABELS.keys()) + list(COMO_LABELS.keys()):
        label = ALL_LABELS.get(var, var)
        aou_row = aou_base[aou_base.variable == var]
        ms_row = ms_base[ms_base.variable == var]

        aou_str = fmt_aor(aou_row.iloc[0]) if len(aou_row) > 0 else "\u2014"
        ms_str = fmt_aor(ms_row.iloc[0]) if len(ms_row) > 0 else "\u2014"

        if len(aou_row) > 0 and len(ms_row) > 0:
            concordant = (
                "Yes" if (aou_row.iloc[0].AOR > 1) == (ms_row.iloc[0].AOR > 1) else "No"
            )
        else:
            concordant = "\u2014"

        rows.append(
            {
                "Variable": label,
                "AoU AOR (95% CI)": aou_str,
                "MS AOR (95% CI)": ms_str,
                "Direction concordant?": concordant,
            }
        )

    et = pd.DataFrame(rows)
    et.to_csv(os.path.join(TBL_DIR, "eTable_S10_crosssite.csv"), index=False)
    conc_rows = [r for r in rows if r["Direction concordant?"] in ("Yes", "No")]
    n_yes = sum(1 for r in conc_rows if r["Direction concordant?"] == "Yes")
    print(f"  Concordance: {n_yes}/{len(conc_rows)} ({n_yes/len(conc_rows)*100:.0f}%)")


# ═══════════════════════════════════════════════════════════════════════
# eTable S11: Control reuse statistics
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("eTable S11: Control Reuse Statistics")
print("=" * 60)

aou_reuse = load_csv(AOU_DIR, "07b_control_reuse.csv")
if aou_reuse is None:
    aou_reuse = load_csv(AOU_DIR, "06b_control_reuse.csv")
ms_reuse = load_csv(MS_DIR, "07b_control_reuse.csv", required=False)
if ms_reuse is None:
    ms_reuse = load_csv(MS_DIR, "06b_control_reuse.csv", required=False)

if aou_reuse is not None:
    METRIC_LABELS = {
        "n_unique_controls": "Unique control individuals",
        "n_control_rows": "Total control observations",
        "median_reuse": "Median reuse count",
        "iqr_lower": "IQR lower bound",
        "iqr_upper": "IQR upper bound",
        "max_reuse": "Maximum reuse count",
        "caliper_sd": "Caliper (SD units)",
        "n_cases_dropped": "Cases dropped (no match)",
    }
    rows = []
    for _, r in aou_reuse.iterrows():
        row = {
            "Metric": METRIC_LABELS.get(r.metric, r.metric),
            "AoU": f"{r.value:,.0f}" if r.value >= 10 else f"{r.value:.1f}",
        }
        if ms_reuse is not None:
            ms_row = ms_reuse[ms_reuse.metric == r.metric]
            if len(ms_row) > 0:
                v = ms_row.iloc[0].value
                row["MarketScan"] = f"{v:,.0f}" if v >= 10 else f"{v:.1f}"
        rows.append(row)
    et = pd.DataFrame(rows)
    et.to_csv(os.path.join(TBL_DIR, "eTable_S11_control_reuse.csv"), index=False)
    print(et.to_string(index=False))


# ═══════════════════════════════════════════════════════════════════════
# eTable S12: Race attenuation table
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("eTable S12: Race Attenuation Table")
print("=" * 60)

race_att = load_csv(AOU_DIR, "race_attenuation_table.csv")
if race_att is not None:
    MODEL_LABELS = {
        "A_base_no_sdoh": "Base (no SDoH)",
        "B_income": "+ Income",
        "B_insurance": "+ Insurance",
        "B_housing": "+ Housing",
        "B_education": "+ Education",
        "B_employment": "+ Employment",
        "B_housing_stability": "+ Housing stability",
        "B_disability_lumped": "+ Disability",
        "C_joint_all_sdoh": "+ All SDoH jointly",
    }
    rows = []
    for model_key in MODEL_LABELS.keys():
        r = race_att[race_att.model == model_key]
        if len(r) == 0:
            continue
        r = r.iloc[0]
        att = (
            f"{r.pct_attenuation:.1f}%"
            if pd.notna(r.pct_attenuation)
            else "\u2014 (reference)"
        )
        rows.append(
            {
                "Adjustment": MODEL_LABELS.get(model_key, model_key),
                "Black AOR (95% CI)": fmt_aor(r),
                "% attenuation": att,
            }
        )
    et = pd.DataFrame(rows)
    et.to_csv(os.path.join(TBL_DIR, "eTable_S12_race_attenuation.csv"), index=False)
    print(et.to_string(index=False))


# ═══════════════════════════════════════════════════════════════════════
# eTable S13: Wave-stratified income
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("eTable S13: Wave-Stratified Income")
print("=" * 60)

wave_income = load_csv(AOU_DIR, "wave_stratified_income.csv")
if wave_income is not None:
    INCOME_LABELS = {
        "f.incomeless_10k": "<$10,000",
        "f.income10k_25k": "$10\u201325K",
        "f.income25k_35k": "$25\u201335K",
        "f.income100k_150k": "$100\u2013150K",
        "f.income150k_200k": "$150\u2013200K",
        "f.incomemore_200k": "\u2265$200K",
        "f.incomeMissing": "Missing",
    }
    WAVE_LABELS = {
        "pre_delta": "Pre-Delta",
        "delta": "Delta",
        "omicron": "Omicron",
    }
    rows = []
    for _, r in wave_income.iterrows():
        rows.append(
            {
                "Wave": WAVE_LABELS.get(r.wave, r.wave),
                "Income": INCOME_LABELS.get(r.variable, r.variable),
                "AOR (95% CI)": fmt_aor(r),
                "P": fmt_p(r.p_value),
            }
        )
    et = pd.DataFrame(rows)
    et.to_csv(os.path.join(TBL_DIR, "eTable_S13_wave_income.csv"), index=False)
    print(et.to_string(index=False))


# ═══════════════════════════════════════════════════════════════════════
# eTable S14: AIDS sensitivity
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("eTable S14: AIDS Sensitivity")
print("=" * 60)

aids_sens = load_csv(AOU_DIR, "aids_sensitivity.csv")
if aids_sens is not None:
    rows = []
    for _, r in aids_sens.iterrows():
        rows.append(
            {
                "Phenotype": r.phenotype,
                "Variable": r.variable,
                "AOR (95% CI)": fmt_aor(r),
                "P": fmt_p(r.p_value) if r.p_value < 0.05 else "NS",
            }
        )
    et = pd.DataFrame(rows)
    et.to_csv(os.path.join(TBL_DIR, "eTable_S14_aids_sensitivity.csv"), index=False)
    print(et.to_string(index=False))


# ═══════════════════════════════════════════════════════════════════════
# eTable S15: Comparator table
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("eTable S15: Comparator Table")
print("=" * 60)

comparator = pd.DataFrame(
    [
        {
            "Study": "Choi et al. 2025",
            "Data": "AoU v7",
            "N COVID+": "25,650",
            "N hosp (%)": "662 (2.6%)",
            "SDoH domains": "3",
            "Key": "Income dose-response; education null",
        },
        {
            "Study": "Vaidya et al. 2024",
            "Data": "N3C",
            "N COVID+": "280,441",
            "N hosp (%)": "NR",
            "SDoH domains": "3",
            "Key": "EHR-coded SDoH underdocumented",
        },
        {
            "Study": "Gatz et al. 2024",
            "Data": "AoU v7",
            "N COVID+": "13,310",
            "N hosp (%)": "N/A (acidosis)",
            "SDoH domains": "6",
            "Key": "PSM+clogit precedent in AoU",
        },
        {
            "Study": "This study",
            "Data": "AoU v7 + MS",
            "N COVID+": "25,160 + 4.4M",
            "N hosp (%)": "4,064 (16.2%) + 139K (3.2%)",
            "SDoH domains": "6",
            "Key": "Joint SDoH, race attenuation, transportability",
        },
    ]
)
comparator.to_csv(os.path.join(TBL_DIR, "eTable_S15_comparator.csv"), index=False)
print(comparator.to_string(index=False))


# ═══════════════════════════════════════════════════════════════════════
# eTable S16: Sensitivity analyses summary (NEW for revision)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("eTable S16: Sensitivity Analyses Summary")
print("=" * 60)

sens = load_csv(AOU_DIR, "sensitivity_summary_comparison.csv")
if sens is not None:
    print(sens.to_string(index=False))
    sens.to_csv(os.path.join(TBL_DIR, "eTable_S16_sensitivity.csv"), index=False)
    print(f"  Saved: eTable_S16_sensitivity.csv")


# ═══════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════
print(f"\n{'='*70}")
print("SUPPLEMENTARY TABLES COMPLETE")
print("=" * 70)

n_files = len([f for f in os.listdir(TBL_DIR) if f.startswith("eTable")])
print(f"  {n_files} eTable files in {TBL_DIR}/")
