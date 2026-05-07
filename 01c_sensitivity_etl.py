#!/usr/bin/env python3
"""
COVID-19 Severity × SDoH — Sensitivity ETL Add-on
Runs on AoU Researcher Workbench AFTER 01_aou_etl.py.

Produces person-level flags needed for reviewer-requested sensitivity
analyses. Does NOT re-run matching; works with existing matched cohort.

Outputs (to results/aou_{version}/):
  08a_case_visit_components.csv     Per-case visit type flags
  08b_control_ed_flags.csv          Per-control ED utilization flags
  08c_responder_vs_nonresponder.csv SDoH survey responder comparison table
  08d_income_collapsed.csv          3-level income for sensitivity model

Usage: python 01c_sensitivity_etl.py v7
License: MIT
"""

import os
import subprocess
import sys
import warnings

warnings.filterwarnings("ignore", message=".*read_gbq is deprecated.*")

import pandas as pd

# ─── Parse version argument ──────────────────────────────────────────
if len(sys.argv) < 2 or sys.argv[1] not in ("v7", "v8"):
    print("Usage: python 01c_sensitivity_etl.py [v7|v8]")
    sys.exit(1)
VERSION = sys.argv[1]

CDR = os.environ["WORKSPACE_CDR"]
BUCKET = os.environ["WORKSPACE_BUCKET"]
RESULTS = f"results/aou_{VERSION}"
BUCKET_DIR = f"{BUCKET}/data/covid_sdoh/aou_{VERSION}"
os.makedirs(RESULTS, exist_ok=True)

print("=" * 70)
print(f"SENSITIVITY ETL ADD-ON  [{VERSION.upper()}]")
print("=" * 70)

# ── Reusable COVID lab/condition constants (same as 01_aou_etl.py) ───
COVID_LAB_CONCEPTS = (
    "586520,586523,586525,586526,586529,706157,706159,715261,715272,"
    "723470,723472,757678,36032061,36032174,36032258,36661371,586518,"
    "586524,706154,706175,723464,723467,723478,36031453,586516,706158,"
    "706160,706163,706171,706172,715260,723469,36031213,36661377,586528,"
    "706161,706165,706167,723463,723468,723471,757677,36031238,36031944,"
    "586519,706166,706169,706173,723465,723476,757685,36031506,706155,"
    "706156,706170,723466,36031652,36661370,706168,706174,715262,723477,"
    "36032419,36661378,37310257"
)
POSITIVE_RESULT_CONCEPTS = (
    "9191,4126681,36032716,36715206,45878745,45881802,45877985,45884084"
)

# ── Reusable CTE: covid_index_date per person ────────────────────────
# Same logic as 01_aou_etl.py cohort_sql.  Used by queries 1, 2, 3.
COVID_CTE = f"""
  u07 AS (
    SELECT person_id, MIN(condition_start_date) AS u07_date
    FROM `{CDR}`.condition_occurrence
    WHERE condition_concept_id = 37311061
    GROUP BY person_id
  ),
  pos_lab AS (
    SELECT person_id, MIN(measurement_date) AS lab_date
    FROM `{CDR}`.measurement
    WHERE measurement_concept_id IN ({COVID_LAB_CONCEPTS})
      AND value_as_concept_id IN ({POSITIVE_RESULT_CONCEPTS})
    GROUP BY person_id
  ),
  covid AS (
    SELECT
      COALESCE(u.person_id, l.person_id) AS person_id,
      LEAST(
        IFNULL(u.u07_date, DATE '9999-12-31'),
        IFNULL(l.lab_date,  DATE '9999-12-31')
      ) AS covid_index_date
    FROM u07 u
    FULL OUTER JOIN pos_lab l ON u.person_id = l.person_id
  ),
  eligible AS (
    SELECT c.*
    FROM covid c
    WHERE c.covid_index_date < DATE '9999-12-31'
      AND c.person_id IN (
        SELECT DISTINCT person_id FROM `{CDR}`.condition_occurrence)
      AND c.person_id IN (
        SELECT DISTINCT person_id FROM `{CDR}`.observation
        WHERE observation_source_concept_id = 1585845)
  )
"""


def query(sql, label=""):
    print(f"\n  [{label}] Running query...")
    df = pd.read_gbq(sql, dialect="standard")
    print(f"  [{label}] → {len(df):,} rows, {df.shape[1]} cols")
    return df


def save(df, filename):
    filepath = os.path.join(RESULTS, filename)
    df.to_csv(filepath, index=False)
    subprocess.run(["gsutil", "cp", filepath, f"{BUCKET_DIR}/"], capture_output=True)
    print(f"  Saved: {filepath} ({len(df):,} rows)")


# ── Load existing cohort and matched data ────────────────────────────
cohort = pd.read_csv(os.path.join(RESULTS, "01_covid_cohort.csv"))
matched = pd.read_csv(os.path.join(RESULTS, "07_regression_base.csv"))
sdoh = pd.read_csv(os.path.join(RESULTS, "04_sdoh.csv"))
timing = pd.read_csv(os.path.join(RESULTS, "04b_sdoh_timing.csv"))

cases = matched[matched.Treatment == 1]
controls = matched[matched.Treatment == 0]
print(f"  Cohort: {len(cohort):,} | Matched: {len(matched):,}")
print(f"  Cases: {len(cases):,} | Controls: {len(controls):,}")


# =====================================================================
# 1. CASE VISIT COMPONENTS (person-level)
# =====================================================================
print("\n" + "=" * 70)
print("1. Case visit components (person-level)")
print("=" * 70)

case_component_sql = f"""
WITH
{COVID_CTE}
SELECT
  e.person_id,
  MAX(CASE WHEN vo.visit_concept_id IN (9201, 32037) THEN 1 ELSE 0 END)
    AS has_ip,
  MAX(CASE WHEN vo.visit_concept_id IN (262, 8717) THEN 1 ELSE 0 END)
    AS has_er_to_ip,
  MAX(CASE WHEN vo.visit_concept_id = 9203
            AND DATE_DIFF(COALESCE(vo.visit_end_date, vo.visit_start_date),
                          vo.visit_start_date, DAY) >= 1
       THEN 1 ELSE 0 END)
    AS has_ed_prolonged,
  MAX(CASE WHEN vo.visit_concept_id = 9203
            AND DATE_DIFF(COALESCE(vo.visit_end_date, vo.visit_start_date),
                          vo.visit_start_date, DAY) = 0
       THEN 1 ELSE 0 END)
    AS has_ed_sameday
FROM eligible e
JOIN `{CDR}`.visit_occurrence vo ON e.person_id = vo.person_id
WHERE vo.visit_start_date BETWEEN e.covid_index_date
      AND DATE_ADD(e.covid_index_date, INTERVAL 14 DAY)
  AND vo.visit_concept_id IN (9201, 32037, 262, 8717, 9203)
GROUP BY e.person_id
"""

case_components = query(case_component_sql, "Case visit components")

# Filter to matched cases only
case_components = case_components[
    case_components.person_id.isin(cases.person_id.unique())
].copy()

# Derive phenotype categories
case_components["ip_only"] = (
    ((case_components.has_ip == 1) | (case_components.has_er_to_ip == 1))
    & (case_components.has_ed_prolonged == 0)
).astype(int)

case_components["ip_or_er_to_ip"] = (
    (case_components.has_ip == 1) | (case_components.has_er_to_ip == 1)
).astype(int)

case_components["ed_prolonged_only"] = (
    (case_components.has_ed_prolonged == 1)
    & (case_components.has_ip == 0)
    & (case_components.has_er_to_ip == 0)
).astype(int)

save(case_components, "08a_case_visit_components.csv")

print("\n  Component summary (matched cases):")
print(f"    Has IP (9201/32037):           {case_components.has_ip.sum():,}")
print(f"    Has ER-to-IP (262/8717):       {case_components.has_er_to_ip.sum():,}")
print(f"    Has ED prolonged (9203, >=1d): {case_components.has_ed_prolonged.sum():,}")
print(f"    Has ED same-day (9203, 0d):    {case_components.has_ed_sameday.sum():,}")
print(f"    IP or ER-to-IP (no ED-only):   {case_components.ip_only.sum():,}")
print(
    f"    ED-prolonged-only cases:        {case_components.ed_prolonged_only.sum():,}"
)


# =====================================================================
# 2. CONTROL ED FLAGS
# =====================================================================
print("\n" + "=" * 70)
print("2. Control ED utilization flags")
print("=" * 70)

ctrl_ed_sql = f"""
WITH
{COVID_CTE}
SELECT
  e.person_id,
  MAX(CASE WHEN vo.visit_concept_id = 9203
            AND DATE_DIFF(COALESCE(vo.visit_end_date, vo.visit_start_date),
                          vo.visit_start_date, DAY) = 0
       THEN 1 ELSE 0 END) AS ctrl_had_sameday_ed_14d,
  MAX(CASE WHEN vo.visit_concept_id IN (9201, 32037, 262, 8717, 9203)
       THEN 1 ELSE 0 END) AS ctrl_had_any_acute_14d
FROM eligible e
JOIN `{CDR}`.visit_occurrence vo ON e.person_id = vo.person_id
WHERE vo.visit_start_date BETWEEN e.covid_index_date
      AND DATE_ADD(e.covid_index_date, INTERVAL 14 DAY)
  AND vo.visit_concept_id IN (9201, 32037, 262, 8717, 9203)
GROUP BY e.person_id
"""

ctrl_ed = query(ctrl_ed_sql, "Control ED flags")
ctrl_unique = controls.person_id.unique()
ctrl_ed = ctrl_ed[ctrl_ed.person_id.isin(ctrl_unique)].copy()

# Controls NOT in this table had zero acute-care visits → clean
n_clean = len(set(ctrl_unique) - set(ctrl_ed.person_id))
n_sameday = ctrl_ed.ctrl_had_sameday_ed_14d.sum()
n_any = ctrl_ed.ctrl_had_any_acute_14d.sum()
print(f"\n  Unique controls: {len(ctrl_unique):,}")
print(f"  With same-day ED (14d): {n_sameday:,}")
print(f"  With any acute care (14d): {n_any:,}")
print(f"  Clean (no acute care): {n_clean:,}")

save(ctrl_ed, "08b_control_ed_flags.csv")


# =====================================================================
# 3. RESPONDER VS NONRESPONDER TABLE
# =====================================================================
print("\n" + "=" * 70)
print("3. SDoH survey responder vs nonresponder comparison")
print("=" * 70)

# Among ALL COVID+ AoU participants with EHR data (not just those with
# Basics Survey), compare responders vs nonresponders on demographics,
# comorbidity burden, and hospitalization rate.
resp_sql = f"""
WITH
{COVID_CTE},
  -- Basics Survey completion flag
  basics AS (
    SELECT DISTINCT person_id, 1 AS has_basics
    FROM `{CDR}`.observation
    WHERE observation_source_concept_id = 1585845
  ),
  -- Broaden eligible to ALL COVID+ with EHR data (drop Basics req)
  covid_ehr AS (
    SELECT c.*
    FROM covid c
    WHERE c.covid_index_date < DATE '9999-12-31'
      AND c.person_id IN (
        SELECT DISTINCT person_id FROM `{CDR}`.condition_occurrence)
  ),
  -- Strict hospitalization (same phenotype as main analysis)
  hosp AS (
    SELECT DISTINCT ce.person_id
    FROM covid_ehr ce
    JOIN `{CDR}`.visit_occurrence vo ON ce.person_id = vo.person_id
    WHERE vo.visit_start_date BETWEEN ce.covid_index_date
          AND DATE_ADD(ce.covid_index_date, INTERVAL 14 DAY)
      AND (
        vo.visit_concept_id IN (9201, 32037, 262, 8717)
        OR (vo.visit_concept_id = 9203
            AND DATE_DIFF(COALESCE(vo.visit_end_date, vo.visit_start_date),
                          vo.visit_start_date, DAY) >= 1)
      )
  ),
  -- Demographics
  demo AS (
    SELECT p.person_id,
      EXTRACT(YEAR FROM ce.covid_index_date) - p.year_of_birth AS age,
      p.sex_at_birth_concept_id,
      r.concept_name AS race_name
    FROM `{CDR}`.person p
    JOIN covid_ehr ce ON p.person_id = ce.person_id
    LEFT JOIN `{CDR}`.concept r ON p.race_concept_id = r.concept_id
  ),
  -- Diagnosis count (proxy for comorbidity burden)
  dx_count AS (
    SELECT person_id, COUNT(DISTINCT condition_concept_id) AS num_dx
    FROM `{CDR}`.condition_occurrence
    GROUP BY person_id
  )

SELECT
  ce.person_id,
  IFNULL(b.has_basics, 0) AS has_basics,
  CASE WHEN h.person_id IS NOT NULL THEN 1 ELSE 0 END AS hospitalized,
  d.age,
  CASE WHEN d.sex_at_birth_concept_id = 45878463 THEN 'Female'
       WHEN d.sex_at_birth_concept_id = 45880669 THEN 'Male'
       ELSE 'Other' END AS sex,
  d.race_name,
  dx.num_dx
FROM covid_ehr ce
LEFT JOIN basics b ON ce.person_id = b.person_id
LEFT JOIN hosp h ON ce.person_id = h.person_id
LEFT JOIN demo d ON ce.person_id = d.person_id
LEFT JOIN dx_count dx ON ce.person_id = dx.person_id
"""

resp_df = query(resp_sql, "Responder comparison")
save(resp_df, "08c_responder_vs_nonresponder.csv")

# Print summary
for grp, label in [
    (1, "Responders (has Basics Survey)"),
    (0, "Nonresponders (no Basics Survey)"),
]:
    sub = resp_df[resp_df.has_basics == grp]
    print(f"\n  {label} (N={len(sub):,}):")
    print(f"    Hospitalized: {sub.hospitalized.mean()*100:.1f}%")
    print(f"    Age (median): {sub.age.median():.0f}")
    print(f"    Female: {(sub.sex=='Female').mean()*100:.1f}%")
    print(f"    Num Dx (median): {sub.num_dx.median():.0f}")
    if "race_name" in sub.columns:
        top_races = sub.race_name.value_counts(normalize=True).head(5)
        for race, pct in top_races.items():
            print(f"    {race}: {pct*100:.1f}%")


# =====================================================================
# 4. COLLAPSED INCOME (3-level)
# =====================================================================
print("\n" + "=" * 70)
print("4. Collapsed income variable")
print("=" * 70)

sdoh_income = sdoh[["person_id", "income"]].copy()
sdoh_income["income_3cat"] = sdoh_income["income"].map(
    {
        "less_10k": "lt_35k",
        "10k_25k": "lt_35k",
        "25k_35k": "lt_35k",
        "35k_100k": "35k_100k",
        "100k_150k": "gt_100k",
        "150k_200k": "gt_100k",
        "more_200k": "gt_100k",
    }
)
sdoh_income.loc[sdoh_income.income_3cat.isna(), "income_3cat"] = "Missing"
save(sdoh_income[["person_id", "income_3cat"]], "08d_income_collapsed.csv")
print(f"  Income 3-cat distribution:\n{sdoh_income.income_3cat.value_counts()}")


print("\n" + "=" * 70)
print("SENSITIVITY ETL COMPLETE")
print("=" * 70)
