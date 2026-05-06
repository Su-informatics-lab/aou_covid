#!/usr/bin/env python3
"""
COVID-19 Severity × SDoH — Supplementary Tables Formatter
Reads aggregate CSVs produced by the pipeline and outputs
publication-ready supplementary tables.

Runs ANYWHERE (no PII needed, only aggregate CSVs).

Usage: python 06_supplement_tables.py [results_dir]

Inputs (from results/aou_v7/):
  01b_phenotype_components.csv      → eTable S2b
  06b_control_reuse.csv             → eTable S11
  race_attenuation_table.csv        → eTable S12
  wave_stratified_income.csv        → eTable S13
  aids_sensitivity.csv              → eTable S14
  all_model_coefficients.csv        → eTable S10 (cross-site)
  predicted_probability_contrast.csv

Inputs (from results/ms/):
  all_model_coefficients.csv
  06b_control_reuse.csv

Output: results/tables/eTable_S*.csv  (one per supplementary table)
        results/tables/comparator_table.csv  (eTable S15)

License: MIT
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
print(f"  AoU:    {AOU_DIR}/")
print(f"  MS:     {MS_DIR}/")
print(f"  Output: {TBL_DIR}/")
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
    """Format AOR (95% CI) string."""
    return f"{row[aor_col]:.2f} ({row[lo_col]:.2f}\u2013{row[hi_col]:.2f})"


def fmt_p(p):
    if p < 0.001:
        return "<0.001"
    elif p < 0.01:
        return f"{p:.3f}"
    else:
        return f"{p:.2f}"


# ══════════════════════════════════════════════════════════════════════
# eTable S2b: Phenotype component decomposition
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("eTable S2b: Phenotype Component Decomposition")
print("=" * 60)

components = load_csv(AOU_DIR, "01b_phenotype_components.csv")
if components is not None:
    # Map to publication labels
    COMPONENT_LABELS = {
        "Inpatient (9201/32037)": "Inpatient",
        "ER-to-Inpatient (262/8717)": "ED-to-inpatient",
        "ED prolonged >=1d (9203)": "ED with stay \u22651 day",
        "ED same-day <1d (9203)": "ED same-day (excluded from strict)",
        "ED null-end-date (9203)": "ED null end date (excluded from strict)",
    }
    CONCEPT_IDS = {
        "Inpatient (9201/32037)": "9201, 32037",
        "ER-to-Inpatient (262/8717)": "262, 8717",
        "ED prolonged >=1d (9203)": "9203",
        "ED same-day <1d (9203)": "9203",
        "ED null-end-date (9203)": "9203",
    }
    RULES = {
        "Inpatient (9201/32037)": "Any visit within 14 days of index",
        "ER-to-Inpatient (262/8717)": "Any visit within 14 days of index",
        "ED prolonged >=1d (9203)": "visit_end_date \u2212 visit_start_date \u2265 1 day",
        "ED same-day <1d (9203)": "Same-day only; no inpatient linkage",
        "ED null-end-date (9203)": "visit_end_date is NULL",
    }
    STRICT = {
        "Inpatient (9201/32037)": "Yes",
        "ER-to-Inpatient (262/8717)": "Yes",
        "ED prolonged >=1d (9203)": "Yes",
        "ED same-day <1d (9203)": "No (sensitivity only)",
        "ED null-end-date (9203)": "No (sensitivity only)",
    }

    total_broad = components.n_persons.sum()
    rows = []
    for _, r in components.iterrows():
        key = r.component
        rows.append(
            {
                "Component": COMPONENT_LABELS.get(key, key),
                "OMOP Concept IDs": CONCEPT_IDS.get(key, ""),
                "Rule": RULES.get(key, ""),
                "In strict outcome?": STRICT.get(key, ""),
                "N persons": f"{int(r.n_persons):,}",
                "% of broad": f"{r.n_persons / total_broad * 100:.1f}",
            }
        )

    # Add totals
    strict_n = sum(
        r.n_persons
        for _, r in components.iterrows()
        if STRICT.get(r.component, "") == "Yes"
    )
    rows.append(
        {
            "Component": "Total (strict primary outcome)",
            "OMOP Concept IDs": "",
            "Rule": "",
            "In strict outcome?": "",
            "N persons": f"{int(strict_n):,}",
            "% of broad": f"{strict_n / total_broad * 100:.1f}",
        }
    )
    rows.append(
        {
            "Component": "Total (broad sensitivity outcome)",
            "OMOP Concept IDs": "",
            "Rule": "",
            "In strict outcome?": "",
            "N persons": f"{int(total_broad):,}",
            "% of broad": "100.0",
        }
    )

    et_s2b = pd.DataFrame(rows)
    et_s2b.to_csv(
        os.path.join(TBL_DIR, "eTable_S2b_phenotype_components.csv"), index=False
    )
    print(et_s2b.to_string(index=False))


# ══════════════════════════════════════════════════════════════════════
# eTable S10: Cross-site comparison (UPDATED with v7 strict AORs)
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("eTable S10: Cross-Site Comparison (updated v7)")
print("=" * 60)

aou_all = load_csv(AOU_DIR, "all_model_coefficients.csv")
ms_all = load_csv(MS_DIR, "all_model_coefficients.csv", required=False)

if aou_all is not None and ms_all is not None:
    aou_base = aou_all[aou_all.model == "base"].copy()
    ms_base = ms_all[ms_all.model == "base"].copy()

    # Human-readable variable labels
    VAR_LABELS = {
        "f.sexFemale": "Female sex",
        "f.sexOther": "Other sex",
        "f.vaccVaccinated": "Vaccinated before index",
        "f.age45-54": "Age 45\u201354",
        "f.age55-64": "Age 55\u201364",
        "f.age65+": "Age \u226565",
        "f.raceBlack": "Black race",
        "f.raceAsian": "Asian race",
        "f.raceOther": "Other race",
        "f.ethnicityHispanic": "Hispanic ethnicity",
        "f.ethnicityOther": "Other ethnicity",
        "f.wavedelta": "Delta wave",
        "f.waveomicron": "Omicron wave",
    }
    COMO_LABELS = {
        "Myocardial_Infarction": "Myocardial infarction",
        "Congestive_Heart_Failure": "Congestive heart failure",
        "Peripheral_Vascular_Disease": "Peripheral vascular disease",
        "Cerebrovascular_Disease": "Cerebrovascular disease",
        "Dementia": "Dementia",
        "Chronic_Pulmonary_Disease": "Chronic pulmonary disease",
        "Rheumatic_Disease": "Rheumatic disease",
        "Peptic_Ulcer_Disease": "Peptic ulcer disease",
        "Liver_Disease_Mild": "Liver disease (mild)",
        "Liver_Disease_Moderate_Severe": "Liver disease (mod/severe)",
        "Diabetes_without_Chronic_Complications": "DM w/o complications",
        "Diabetes_with_Chronic_Complications": "DM w/ complications",
        "Hemiplegia_Paraplegia": "Hemiplegia/paraplegia",
        "Renal_Disease_Mild_Moderate": "Renal disease (mild/mod)",
        "Renal_Disease_Severe": "Renal disease (severe)",
        "HIV": "HIV",
        "Metastatic_Solid_Tumor": "Metastatic solid tumor",
        "Malignancy": "Malignancy",
        "AIDS": "AIDS",
    }
    ALL_LABELS = {**VAR_LABELS, **COMO_LABELS}

    # Shared variables (exclude MS-only plan/region and AoU-only race/ethnicity)
    shared_vars = set(aou_base.variable) & set(ms_base.variable)

    rows = []
    for var in list(VAR_LABELS.keys()) + list(COMO_LABELS.keys()):
        label = ALL_LABELS.get(var, var)
        aou_row = aou_base[aou_base.variable == var]
        ms_row = ms_base[ms_base.variable == var]

        aou_str = fmt_aor(aou_row.iloc[0]) if len(aou_row) > 0 else "\u2014"
        ms_str = fmt_aor(ms_row.iloc[0]) if len(ms_row) > 0 else "\u2014"

        aou_sig = ""
        if len(aou_row) > 0 and aou_row.iloc[0].p_value < 0.05:
            aou_sig = "*"
        ms_sig = ""
        if len(ms_row) > 0 and ms_row.iloc[0].p_value < 0.05:
            ms_sig = "*"

        # Direction concordance
        if len(aou_row) > 0 and len(ms_row) > 0:
            aou_dir = "Risk" if aou_row.iloc[0].AOR > 1 else "Protective"
            ms_dir = "Risk" if ms_row.iloc[0].AOR > 1 else "Protective"
            concordant = "Yes" if aou_dir == ms_dir else "No"
        else:
            concordant = "\u2014"

        rows.append(
            {
                "Variable": label,
                "AoU AOR (95% CI)": f"{aou_str}{aou_sig}",
                "MS AOR (95% CI)": f"{ms_str}{ms_sig}",
                "Direction concordant?": concordant,
            }
        )

    et_s10 = pd.DataFrame(rows)
    et_s10.to_csv(os.path.join(TBL_DIR, "eTable_S10_crosssite.csv"), index=False)
    print(et_s10.to_string(index=False))

    # Concordance summary
    conc_rows = [r for r in rows if r["Direction concordant?"] in ("Yes", "No")]
    n_yes = sum(1 for r in conc_rows if r["Direction concordant?"] == "Yes")
    print(
        f"\n  Direction concordance: {n_yes}/{len(conc_rows)}"
        f" ({n_yes/len(conc_rows)*100:.0f}%)"
    )


# ══════════════════════════════════════════════════════════════════════
# eTable S11: Control reuse statistics
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("eTable S11: Control Reuse Statistics")
print("=" * 60)

aou_reuse = load_csv(AOU_DIR, "06b_control_reuse.csv")
ms_reuse = load_csv(MS_DIR, "06b_control_reuse.csv", required=False)

if aou_reuse is not None:
    METRIC_LABELS = {
        "n_unique_controls": "Unique control individuals",
        "n_control_rows": "Total control observations (with reuse)",
        "median_reuse": "Median times a control appears",
        "iqr_lower": "IQR lower bound (reuse count)",
        "iqr_upper": "IQR upper bound (reuse count)",
        "max_reuse": "Maximum reuse count",
    }

    rows = []
    for _, r in aou_reuse.iterrows():
        row = {
            "Metric": METRIC_LABELS.get(r.metric, r.metric),
            "AoU": f"{r.value:,.0f}" if r.value >= 10 else f"{r.value:.0f}",
        }
        if ms_reuse is not None:
            ms_row = ms_reuse[ms_reuse.metric == r.metric]
            if len(ms_row) > 0:
                v = ms_row.iloc[0].value
                row["MarketScan"] = f"{v:,.0f}" if v >= 10 else f"{v:.0f}"
        rows.append(row)

    et_s11 = pd.DataFrame(rows)
    et_s11.to_csv(os.path.join(TBL_DIR, "eTable_S11_control_reuse.csv"), index=False)
    print(et_s11.to_string(index=False))


# ══════════════════════════════════════════════════════════════════════
# eTable S12: Race attenuation table
# ══════════════════════════════════════════════════════════════════════
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
    # Order
    MODEL_ORDER = list(MODEL_LABELS.keys())

    rows = []
    for model_key in MODEL_ORDER:
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
                "Black race AOR (95% CI)": fmt_aor(r),
                "% attenuation from base": att,
            }
        )

    et_s12 = pd.DataFrame(rows)
    et_s12.to_csv(os.path.join(TBL_DIR, "eTable_S12_race_attenuation.csv"), index=False)
    print(et_s12.to_string(index=False))


# ══════════════════════════════════════════════════════════════════════
# eTable S13: Wave-stratified income gradient
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("eTable S13: Wave-Stratified Income")
print("=" * 60)

wave_income = load_csv(AOU_DIR, "wave_stratified_income.csv")
if wave_income is not None:
    INCOME_LABELS = {
        "f.incomeless_10k": "<$10,000",
        "f.income10k_25k": "$10,000\u201324,999",
        "f.income25k_35k": "$25,000\u201334,999",
        "f.income100k_150k": "$100,000\u2013149,999",
        "f.income150k_200k": "$150,000\u2013199,999",
        "f.incomemore_200k": "\u2265$200,000",
        "f.incomeMissing": "Missing",
    }
    WAVE_LABELS = {
        "pre_delta": "Pre-Delta (before Jun 2021)",
        "delta": "Delta (Jun\u2013Dec 2021)",
        "omicron": "Omicron (Dec 2021+)",
    }

    rows = []
    for _, r in wave_income.iterrows():
        rows.append(
            {
                "Pandemic wave": WAVE_LABELS.get(r.wave, r.wave),
                "Income level (ref: $35\u2013100K)": INCOME_LABELS.get(
                    r.variable, r.variable
                ),
                "AOR (95% CI)": fmt_aor(r),
                "P": fmt_p(r.p_value),
            }
        )

    et_s13 = pd.DataFrame(rows)
    et_s13.to_csv(os.path.join(TBL_DIR, "eTable_S13_wave_income.csv"), index=False)
    print(et_s13.to_string(index=False))


# ══════════════════════════════════════════════════════════════════════
# eTable S14: AIDS sensitivity analyses
# ══════════════════════════════════════════════════════════════════════
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
                "Variable in model": r.variable,
                "AOR (95% CI)": fmt_aor(r),
                "P": fmt_p(r.p_value) if r.p_value < 0.05 else "NS",
            }
        )

    # Add AoU AIDS prevalence context
    et_s14 = pd.DataFrame(rows)
    et_s14.to_csv(os.path.join(TBL_DIR, "eTable_S14_aids_sensitivity.csv"), index=False)
    print(et_s14.to_string(index=False))


# ══════════════════════════════════════════════════════════════════════
# eTable S15: Comparator table (Choi / Vaidya / Gatz / this study)
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("eTable S15: Comparator Table")
print("=" * 60)

comparator = pd.DataFrame(
    [
        {
            "Study": "Choi et al. 2025",
            "Journal": "Front Public Health 13:1690430",
            "Data source": "AoU (CDR v7, 2021\u20132023)",
            "N COVID+": "25,650",
            "N hospitalized (%)": "662 (2.6%)",
            "Outcome": "Inpatient hospitalization",
            "SDoH source": "Survey + ZIP-3 ADI",
            "SDoH domains": "3 (income, education, ADI)",
            "Confounder adjustment": "Unmatched logistic, 5 chronic conditions + BMI/smoking",
            "Race analyzed?": "Yes",
            "Transportability / validation": "None",
            "Key SDoH findings": "Income dose-response confirmed; education null after adjustment",
        },
        {
            "Study": "Vaidya et al. 2024",
            "Journal": "J Clin Transl Sci 8:e167",
            "Data source": "N3C (multi-site EHR)",
            "N COVID+": "280,441",
            "N hospitalized (%)": "NR",
            "Outcome": "Hospitalization",
            "SDoH source": "Epic SDoH module + LOINC",
            "SDoH domains": "3 (HP2030 aligned)",
            "Confounder adjustment": "Mixed-effects logistic",
            "Race analyzed?": "Yes (stratified)",
            "Transportability / validation": "None",
            "Key SDoH findings": "SDoH associated with hospitalization in PWH; EHR-coded SDoH severely underdocumented",
        },
        {
            "Study": "Gatz et al. 2024",
            "Journal": "JAMIA 31(12):2932\u20132939",
            "Data source": "AoU (CDR v7)",
            "N COVID+": "13,310",
            "N hospitalized (%)": "N/A (acidosis outcome)",
            "Outcome": "Severe acidosis",
            "SDoH source": "Survey",
            "SDoH domains": "6 (income, insurance, education, employment, housing, disability)",
            "Confounder adjustment": "PSM + clogit + 19 Charlson",
            "Race analyzed?": "Yes",
            "Transportability / validation": "None",
            "Key SDoH findings": "Multiple SDoH domains associated with severe acidosis; methodological precedent for PSM+clogit in AoU",
        },
        {
            "Study": "This study (v6)",
            "Journal": "JAMIA (submitted)",
            "Data source": "AoU (CDR v7) + MarketScan 2020\u20132023",
            "N COVID+": "25,160 (AoU) + 4,423,200 (MS)",
            "N hospitalized (%)": "4,064 (16.2%) AoU; 139,489 (3.2%) MS",
            "Outcome": "Strict hospitalization (14-day, ED \u22651d); broad sensitivity (30-day)",
            "SDoH source": "Survey (AoU); plan type/region (MS)",
            "SDoH domains": "6 (income, insurance, education, employment, housing, disability)",
            "Confounder adjustment": "PSM + clogit + 19 Charlson + pandemic wave; domain-by-domain + joint SDoH model",
            "Race analyzed?": "Yes (with attenuation table)",
            "Transportability / validation": "Clinical-model transportability in MarketScan claims",
            "Key SDoH findings": "Income dose-response; Medicaid risk; education attenuated by joint adjustment; 13.6% Black-race attenuation by measured SDoH; income gradient persists through Omicron",
        },
    ]
)

comparator.to_csv(os.path.join(TBL_DIR, "eTable_S15_comparator.csv"), index=False)
print(comparator.to_string(index=False))


# ══════════════════════════════════════════════════════════════════════
# UPDATED CONSORT COUNTS (v7 strict phenotype)
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("CONSORT COUNTS (v7 strict phenotype)")
print("=" * 60)

consort = pd.DataFrame(
    [
        {"Site": "AoU", "Metric": "total_participants", "Value": 413457},
        {"Site": "AoU", "Metric": "covid_positive", "Value": 25160},
        {"Site": "AoU", "Metric": "hospitalized_strict_14d", "Value": 4064},
        {"Site": "AoU", "Metric": "hospitalized_broad_30d", "Value": 6531},
        {"Site": "AoU", "Metric": "ed_only_reclassified", "Value": 2467},
        {"Site": "AoU", "Metric": "outpatient_controls", "Value": 21096},
        {"Site": "AoU", "Metric": "matched_observations", "Value": 20285},
        {"Site": "AoU", "Metric": "matched_strata", "Value": 4064},
        {"Site": "AoU", "Metric": "unique_controls", "Value": 9876},
        {"Site": "AoU", "Metric": "control_observations", "Value": 16221},
        {"Site": "AoU", "Metric": "caliper", "Value": 0.114},
        {"Site": "AoU", "Metric": "dropped", "Value": 0},
        {"Site": "MS", "Metric": "covid_positive", "Value": 4423200},
        {"Site": "MS", "Metric": "hospitalized_strict_14d", "Value": 139489},
        {"Site": "MS", "Metric": "matched_observations", "Value": 697354},
        {"Site": "MS", "Metric": "matched_strata", "Value": 139472},
    ]
)
consort.to_csv(os.path.join(TBL_DIR, "consort_counts_v7.csv"), index=False)
print(consort.to_string(index=False))


# ══════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*70}")
print("SUPPLEMENTARY TABLES COMPLETE")
print("=" * 70)

n_files = len([f for f in os.listdir(TBL_DIR) if f.startswith("eTable")])
print(f"  {n_files} eTable files in {TBL_DIR}/")
print()
print("  eTable numbering for supplement:")
print("    S1   COVID-19 identification codes (static, keep)")
print("    S2a  Hospitalization visit concepts + phenotype rules (static, update text)")
print(
    "    S2b  Phenotype component decomposition (eTable_S2b_phenotype_components.csv)"
)
print("    S3   Vaccination codes (static, keep)")
print("    S4   Charlson code sets (static, keep)")
print("    S5   SDoH code sets (static, keep)")
print("    S6   Pre-matching balance, AoU (from 05_smd_onplatform.py)")
print(
    "    S7   Post-matching balance, AoU — FULL COVARIATES (from 05_smd_onplatform.py)"
)
print("    S8   Pre/post balance, MarketScan (from 05_smd_onplatform.py)")
print("    S9   MarketScan demographics (from 03_tables_onplatform.py)")
print("    S10  Cross-site AOR comparison (eTable_S10_crosssite.csv)")
print("    S11  Control reuse statistics (eTable_S11_control_reuse.csv)")
print("    S12  Race attenuation table (eTable_S12_race_attenuation.csv)")
print("    S13  Wave-stratified income (eTable_S13_wave_income.csv)")
print("    S14  AIDS sensitivity (eTable_S14_aids_sensitivity.csv)")
print("    S15  Comparator table (eTable_S15_comparator.csv)")
print("    eFig S1  Full-covariate Love plot (from 05_smd_onplatform.py)")
print("    eMethod  Missing data (static text, update)")
print()
print("  Run AFTER: 01_aou_etl.py, 02_models.R, 04_figures.py")
print("  Run BEFORE: building supplementary docx")
