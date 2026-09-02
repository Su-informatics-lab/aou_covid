#!/usr/bin/env python3
"""Print every All of Us value the manuscript still carries as [STALE].

Everything here already exists in results/aou_v7 and results/tables from the
2026-09-02 re-run. Nothing is recomputed; these were simply never printed, so
16 markers sit in working/ms_v191_rerun_WORKING.docx waiting on them.

Read the numbers off the screen. Do not package and download: several of these
files carry cells covering fewer than 20 participants -- the "never attended
school" education stratum is the known one -- and the All of Us rule on
aggregate statistics applies to each value individually.

Run inside the workspace:  python print_aou_stale.py
"""
import os
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)
pd.set_option("display.max_rows", 200)

R = os.path.expanduser("~/covid/repo/results/aou_v7")
T = os.path.expanduser("~/covid/repo/results/tables")
COLS = ["variable", "AOR", "CI_lower", "CI_upper", "p_value"]


def show(path, title, pattern=None, published=None, cols=COLS):
    print("\n" + "=" * 78)
    print(title)
    if published:
        print("  published (v18.6): " + published)
    print("=" * 78)
    if not os.path.exists(path):
        print(f"  [MISSING] {path}")
        return
    d = pd.read_csv(path)
    if pattern is not None:
        d = d[d.iloc[:, 0].astype(str).str.contains(pattern, case=False, na=False)]
    keep = [c for c in cols if c in d.columns]
    print((d[keep] if keep else d).to_string(index=False))


# 1 -- base model: the wave and comorbidity rows the manuscript still needs
show(f"{R}/base_model_coefficients.csv",
     "1. BASE MODEL — wave and comorbidities  (manuscript para 44)",
     pattern="wave|Renal|Liver|Metastatic|Cerebro|Congestive|Dementia|Rheumatic|"
             "Peptic|Diabetes|Hemiplegia|Malignancy|AIDS|HIV|Myocardial|Peripheral|"
             "Pulmonary",
     published="Delta 1.24 (1.12-1.38), Omicron 1.04 (0.96-1.13); dementia null")

# 2 -- domain-specific models: Table 3's first column, and the 2.79 product
show(f"{R}/all_model_coefficients.csv",
     "2. DOMAIN-SPECIFIC SDoH — Table 3 column 1  (manuscript para 59)",
     pattern="f.insurance|f.income|f.education|f.employment|f.housing|f.disability",
     published="Medicaid 1.59, <10k 1.46, BelowGED 1.35, Unemployed 1.41, "
               "Student 1.61, Rent 1.28; product of the three = 2.79")

# 3 -- joint model: the levels not yet in the manuscript
show(f"{R}/joint_sdoh_coefficients.csv",
     "3. JOINT SDoH — the remaining levels  (manuscript para 65)",
     pattern="f.insurance|f.income|f.education|f.employment|f.housing|f.disability",
     published="Student 1.52, non-employment 1.26, 100-150k 1.24, 150-200k 1.26, "
               "disability 0.86, housing other 0.86")

# 4 -- sensitivity analyses
for tag, lab in (("S1_IP_only_cases", "S1 inpatient-only cases"),
                 ("S2_clean_controls", "S2 controls without acute care"),
                 ("S3_pre_index_sdoh", "S3 pre-infection surveys"),
                 ("S4_no_vaccination", "S4 vaccination removed"),
                 ("S5_income_collapsed", "S5 income collapsed")):
    show(f"{R}/sensitivity_{tag}_coefficients.csv",
         f"4. SENSITIVITY {lab}  (manuscript para 74)",
         pattern="f.income|f.housingRent|f.insuranceMedicaid|f.employmentUnemployed",
         published="S3 income 1.18->1.13 and rent 1.13->1.09; S5 <35k 1.16"
         if tag == "S3_pre_index_sdoh" or tag == "S5_income_collapsed" else None)

# 5 -- wave-stratified income, eTable 13
show(f"{T}/eTable_S13_wave_income.csv",
     "5. WAVE-STRATIFIED INCOME — eTable 13  (manuscript paras 69, 87)",
     published="<10k: 1.49 pre-Delta, 2.11 Delta, 1.64 Omicron")

# 6 -- wave-stratified race and insurance, eTables 12b and 12c
for f, lab, pub in (
    ("wave_stratified_race_attenuation.csv", "6a. WAVE RACE ATTENUATION — eTable 12b",
     "3.00/2.64 11.5%, 2.98/2.17 29.1%, 1.65/1.42 30.1%"),
    ("wave_stratified_insurance.csv", "6b. WAVE MEDICAID — eTable 12c",
     "1.71 pre-Delta, 2.24 Delta, 1.46 Omicron (domain-specific)")):
    show(f"{R}/{f}", lab, published=pub, cols=[])

# 7 -- control reuse and effective sample size
print("\n" + "=" * 78)
print("7. CONTROL REUSE AND EFFECTIVE SAMPLE SIZE  (manuscript paras 41, 96)")
print("  published (v18.6): 9,691 unique controls, max reuse 13, ESS 6,952")
print("=" * 78)
p = f"{R}/07b_control_reuse.csv"
print(pd.read_csv(p).to_string(index=False) if os.path.exists(p) else f"  [MISSING] {p}")
p = f"{R}/07e_matchit_summary.txt"
if os.path.exists(p):
    txt = open(p).read()
    for line in txt.splitlines():
        if any(k in line.lower() for k in ("effective", "ess", "sample size", "matched")):
            print("  " + line.strip())

# 8 -- Table 2, for the differential income missingness
show(f"{R}/table2_sdoh.csv",
     "8. TABLE 2 — income missingness  (manuscript para 96)",
     pattern="Missing|Income|less|10k|25k|35k|100k|150k|200k",
     published="26.7% of cases vs 19.8% of controls",
     cols=["Variable", "Cases_n", "Cases_pct", "Controls_n", "Controls_pct"])

print("\n" + "=" * 78)
print("Each value above closes one [STALE] marker in")
print("working/ms_v191_rerun_WORKING.docx. Read them off; do not download.")
print("=" * 78)
