#!/usr/bin/env python3
"""
COVID-19 Severity × SDoH — AoU ETL
Runs on AoU Researcher Workbench (Controlled Tier).

Steps 1–6: cohort, demographics, Charlson, SDoH, vaccination,
matching variable extraction. PSM is handled by 01b_psm.R (MatchIt).

Features:
  - Strict hospitalization phenotype (ED 9203 requires duration >= 1d)
  - Both severity_strict and severity_broad flags
  - Phenotype component decomposition table
  - Pandemic wave variable (pre_delta / delta / omicron)
  - SDoH timing: survey_date - covid_index_date
  - Insurance recoded as hierarchical categorical
    (Medicaid > Medicare > Employer > Other_None > Missing)
  - Charlson codes: canonical Glasheen 2019 from DualR cross-site ETL
  - AIDS two-step: HIV AND OI co-occurrence, AIDS->HIV trump rule

Usage: python 01_aou_etl.py v7
       python 01_aou_etl.py v8

Output: results/aou_{version}/*.csv  (01–06)
Next:   Rscript 01b_psm.R aou_{version}
License: MIT
"""

import os
import subprocess
import sys
import warnings

warnings.filterwarnings("ignore", message=".*read_gbq is deprecated.*")

import numpy as np
import pandas as pd

# ─── Parse version argument ──────────────────────────────────────────
if len(sys.argv) < 2 or sys.argv[1] not in ("v7", "v8"):
    print("Usage: python 01_aou_etl.py [v7|v8]")
    sys.exit(1)
VERSION = sys.argv[1]

CDR = os.environ["WORKSPACE_CDR"]
BUCKET = os.environ["WORKSPACE_BUCKET"]
CDR_TAG = CDR.split(".")[-1]
RESULTS = f"results/aou_{VERSION}"
BUCKET_DIR = f"{BUCKET}/data/covid_sdoh/aou_{VERSION}"
os.makedirs(RESULTS, exist_ok=True)

print("=" * 70)
print(f"COVID-19 SEVERITY × SDoH — AoU ETL  [{VERSION.upper()}]")
print("=" * 70)
print(f"  CDR:     {CDR}")
print(f"  Tag:     {CDR_TAG}")
print(f"  Output:  {RESULTS}/")
print(f"  Bucket:  {BUCKET_DIR}/")
print("=" * 70)


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


# =====================================================================
# STEP 1: COVID-19 COHORT
# strict vs broad hospitalization phenotype ────────────────────
# =====================================================================
print("\n" + "=" * 70)
print("STEP 1: COVID-19 Cohort  (strict + broad phenotype)")
print("=" * 70)

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

# Visit concept ID groups ──────────────────────────────────────
# Strict inpatient (no duration ambiguity):
#   9201  = Inpatient Visit
#   32037 = Inpatient Hospital
#   262   = ER and Inpatient Visit (by definition includes IP)
#   8717  = ER - Hospital (implies hospital-level setting)
# Ambiguous:
#   9203  = Emergency Room Visit (may be same-day ED-only)
STRICT_IP_VISITS = "9201,32037,262,8717"
ED_VISIT = "9203"

cohort_sql = f"""
WITH
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
  u099 AS (
    SELECT person_id, MIN(condition_start_date) AS u099_date
    FROM `{CDR}`.condition_occurrence
    WHERE condition_concept_id IN (710706, 705076)
       OR condition_source_value LIKE '%U09.9%'
    GROUP BY person_id
  ),
  covid_all AS (
    SELECT
      COALESCE(u.person_id, l.person_id, u9.person_id) AS person_id,
      u.u07_date, l.lab_date, u9.u099_date,
      LEAST(
        IFNULL(u.u07_date, DATE '9999-12-31'),
        IFNULL(l.lab_date, DATE '9999-12-31')
      ) AS covid_index_date
    FROM u07 u
    FULL OUTER JOIN pos_lab l ON u.person_id = l.person_id
    FULL OUTER JOIN u099 u9 ON COALESCE(u.person_id, l.person_id) = u9.person_id
  ),
  eligible AS (
    SELECT ca.*
    FROM covid_all ca
    WHERE ca.person_id IN (SELECT DISTINCT person_id
                           FROM `{CDR}`.condition_occurrence)
      AND ca.person_id IN (SELECT DISTINCT person_id
                           FROM `{CDR}`.observation
                           WHERE observation_source_concept_id = 1585845)
      AND ca.covid_index_date < DATE '9999-12-31'
  ),
  -- ── strict hospitalization ─────────────────────────────────────
  -- IP visits (9201,32037,262,8717) always count.
  -- ED visits (9203) count ONLY if stay duration >= 1 day.
  hosp_strict AS (
    SELECT DISTINCT e.person_id
    FROM eligible e
    JOIN `{CDR}`.visit_occurrence vo ON e.person_id = vo.person_id
    WHERE vo.visit_start_date BETWEEN e.covid_index_date
          AND DATE_ADD(e.covid_index_date, INTERVAL 14 DAY)
      AND (
            vo.visit_concept_id IN ({STRICT_IP_VISITS})
            OR (
              vo.visit_concept_id = {ED_VISIT}
              AND DATE_DIFF(
                COALESCE(vo.visit_end_date, vo.visit_start_date),
                vo.visit_start_date, DAY) >= 1
            )
          )
  ),
  -- Broad: any of the 5 visit types within 30 days (v5 definition)
  hosp_broad AS (
    SELECT DISTINCT e.person_id
    FROM eligible e
    JOIN `{CDR}`.visit_occurrence vo ON e.person_id = vo.person_id
    WHERE vo.visit_concept_id IN ({STRICT_IP_VISITS},{ED_VISIT})
      AND vo.visit_start_date BETWEEN e.covid_index_date
          AND DATE_ADD(e.covid_index_date, INTERVAL 30 DAY)
  ),
  died AS (SELECT DISTINCT person_id FROM `{CDR}`.death)

SELECT e.person_id, e.covid_index_date,
  CASE WHEN e.u07_date IS NOT NULL AND e.lab_date IS NOT NULL THEN 'both'
       WHEN e.u07_date IS NOT NULL THEN 'u07_condition'
       ELSE 'positive_lab' END AS covid_source,
  CASE WHEN hs.person_id IS NOT NULL THEN 1 ELSE 0 END AS severity,
  CASE WHEN hb.person_id IS NOT NULL THEN 1 ELSE 0 END AS severity_broad,
  CASE WHEN e.u099_date IS NOT NULL THEN 1 ELSE 0 END AS has_u099,
  CASE WHEN d.person_id IS NOT NULL THEN 1 ELSE 0 END AS has_death
FROM eligible e
LEFT JOIN hosp_strict hs ON e.person_id = hs.person_id
LEFT JOIN hosp_broad  hb ON e.person_id = hb.person_id
LEFT JOIN died d ON e.person_id = d.person_id
"""

covid_cohort = query(cohort_sql, "COVID cohort")

n_strict = covid_cohort.severity.sum()
n_broad = covid_cohort.severity_broad.sum()
n_ed_only = n_broad - n_strict
print(
    f"\n  Total COVID+: {len(covid_cohort):,}"
    f"\n  Hospitalized (STRICT): {n_strict:,}  ({n_strict/len(covid_cohort)*100:.1f}%)"
    f"\n  Hospitalized (BROAD):  {n_broad:,}  ({n_broad/len(covid_cohort)*100:.1f}%)"
    f"\n  ED-only same-day (reclassified): {n_ed_only:,}"
    f"\n  U09.9: {covid_cohort.has_u099.sum():,}  |  Death: {covid_cohort.has_death.sum():,}"
)

# pandemic wave ────────────────────────────────────────────────
covid_cohort["covid_index_date"] = pd.to_datetime(covid_cohort["covid_index_date"])
covid_cohort["pandemic_wave"] = "pre_delta"
covid_cohort.loc[covid_cohort.covid_index_date >= "2021-06-15", "pandemic_wave"] = (
    "delta"
)
covid_cohort.loc[covid_cohort.covid_index_date >= "2021-12-15", "pandemic_wave"] = (
    "omicron"
)
print(f"  Wave: {covid_cohort.pandemic_wave.value_counts().to_dict()}")

save(covid_cohort, "01_covid_cohort.csv")


# phenotype component decomposition ────────────────────────────
print("\n  Computing phenotype component decomposition...")
decomp_sql = f"""
WITH cohort AS (
  SELECT person_id, CAST(covid_index_date AS DATE) AS covid_index_date
  FROM (
    SELECT COALESCE(u.person_id, l.person_id) AS person_id,
      LEAST(IFNULL(MIN(u.u07_date), DATE '9999-12-31'),
            IFNULL(MIN(l.lab_date), DATE '9999-12-31')) AS covid_index_date
    FROM (
      SELECT person_id, MIN(condition_start_date) AS u07_date
      FROM `{CDR}`.condition_occurrence
      WHERE condition_concept_id = 37311061
      GROUP BY person_id
    ) u
    FULL OUTER JOIN (
      SELECT person_id, MIN(measurement_date) AS lab_date
      FROM `{CDR}`.measurement
      WHERE measurement_concept_id IN ({COVID_LAB_CONCEPTS})
        AND value_as_concept_id IN ({POSITIVE_RESULT_CONCEPTS})
      GROUP BY person_id
    ) l ON u.person_id = l.person_id
  )
  WHERE covid_index_date < DATE '9999-12-31'
    AND person_id IN (SELECT DISTINCT person_id
                      FROM `{CDR}`.condition_occurrence)
    AND person_id IN (SELECT DISTINCT person_id
                      FROM `{CDR}`.observation
                      WHERE observation_source_concept_id = 1585845)
),
hosp_visits AS (
  SELECT vo.person_id, vo.visit_concept_id,
    DATE_DIFF(COALESCE(vo.visit_end_date, vo.visit_start_date),
              vo.visit_start_date, DAY) AS visit_duration_days,
    vo.visit_end_date
  FROM `{CDR}`.visit_occurrence vo
  JOIN cohort c ON vo.person_id = c.person_id
  WHERE vo.visit_concept_id IN ({STRICT_IP_VISITS},{ED_VISIT})
    AND vo.visit_start_date BETWEEN c.covid_index_date
        AND DATE_ADD(c.covid_index_date, INTERVAL 30 DAY)
)
SELECT
  CASE
    WHEN visit_concept_id IN (9201, 32037) THEN 'Inpatient (9201/32037)'
    WHEN visit_concept_id IN (262, 8717)   THEN 'ER-to-Inpatient (262/8717)'
    WHEN visit_concept_id = 9203 AND visit_duration_days >= 1
         THEN 'ED prolonged >=1d (9203)'
    WHEN visit_concept_id = 9203 AND visit_duration_days = 0
         THEN 'ED same-day <1d (9203)'
    WHEN visit_concept_id = 9203 AND visit_end_date IS NULL
         THEN 'ED null-end-date (9203)'
    ELSE 'Other'
  END AS component,
  COUNT(DISTINCT person_id) AS n_persons
FROM hosp_visits
GROUP BY 1
ORDER BY n_persons DESC
"""
try:
    components = query(decomp_sql, "Phenotype components")
    save(components, "01b_phenotype_components.csv")
    print("\n  Phenotype component decomposition:")
    for _, row in components.iterrows():
        print(f"    {row.component:40s}  N={row.n_persons:,}")
except Exception as e:
    print(f"  WARNING: Component decomposition failed: {e}")
    print("  Continuing...")


# =====================================================================
# STEP 2: DEMOGRAPHICS
# =====================================================================
print("\n" + "=" * 70)
print("STEP 2: Demographics")
print("=" * 70)

demo_all = query(
    f"""
SELECT p.person_id, p.year_of_birth, p.sex_at_birth_concept_id,
       r.concept_name AS race_name, e.concept_name AS ethnicity_name
FROM `{CDR}`.person p
LEFT JOIN `{CDR}`.concept r ON p.race_source_concept_id = r.concept_id
LEFT JOIN `{CDR}`.concept e ON p.ethnicity_concept_id = e.concept_id
""",
    "Demographics",
)

demo = demo_all[demo_all.person_id.isin(covid_cohort.person_id)].copy()
demo["sex_at_birth"] = (
    demo["sex_at_birth_concept_id"]
    .map({45878463: "Female", 45880669: "Male"})
    .fillna("Other")
)
demo["race"] = demo["race_name"].apply(
    lambda x: (
        "White"
        if "White" in str(x)
        else (
            "Black"
            if "Black" in str(x)
            else ("Asian" if "Asian" in str(x) else "Other")
        )
    )
)
demo["ethnicity"] = demo["ethnicity_name"].apply(
    lambda x: (
        "Not Hispanic"
        if "Not Hispanic" in str(x)
        else ("Hispanic" if "Hispanic" in str(x) else "Other")
    )
)
demo = demo.merge(covid_cohort[["person_id", "covid_index_date"]], on="person_id")
demo["covid_index_date"] = pd.to_datetime(demo["covid_index_date"])
demo["age_at_covid"] = demo["covid_index_date"].dt.year - demo["year_of_birth"]
demo["age_group"] = pd.cut(
    demo["age_at_covid"],
    bins=[0, 45, 55, 65, 200],
    labels=["<45", "45-54", "55-64", "65+"],
    right=False,
)
demo_out = demo[
    [
        "person_id",
        "sex_at_birth",
        "race",
        "ethnicity",
        "age_at_covid",
        "age_group",
        "year_of_birth",
    ]
]

for col in ["sex_at_birth", "race", "ethnicity", "age_group"]:
    print(f"\n  {col}: {demo_out[col].value_counts().to_dict()}")
save(demo_out, "02_demographics.csv")


# =====================================================================
# STEP 3: CHARLSON COMORBIDITIES (Glasheen 2019)
# =====================================================================
print("\n" + "=" * 70)
print("STEP 3: Charlson Comorbidities")
print("=" * 70)


# Charlson code sets: Glasheen 2019 CDMF CCI (the BIBLE)
# Source: Glasheen WP et al. Am Health Drug Benefits 2019;12(4):188-197
# Tables SI-3a through SI-3s, CDMF CCI columns only.
CHARLSON = {
    "Myocardial_Infarction": {"9": ["410", "412"], "10": ["I21", "I22", "I252"]},
    "Congestive_Heart_Failure": {
        "9": [
            "39891",
            "40201",
            "40211",
            "40291",
            "40401",
            "40403",
            "40411",
            "40413",
            "40491",
            "40493",
            "4254",
            "4255",
            "4256",
            "4257",
            "4258",
            "4259",
            "428",
        ],
        "10": [
            "I110",
            "I130",
            "I132",
            "I255",
            "I420",
            "I425",
            "I426",
            "I427",
            "I428",
            "I429",
            "I43",
            "I50",
            "P290",
        ],
    },
    "Peripheral_Vascular_Disease": {
        "9": [
            "0930",
            "4373",
            "440",
            "441",
            "4431",
            "4432",
            "4438",
            "4439",
            "4471",
            "5571",
            "5579",
            "V434",
        ],
        "10": [
            "I70",
            "I71",
            "I731",
            "I738",
            "I739",
            "I771",
            "I790",
            "I791",
            "I798",
            "K551",
            "K558",
            "K559",
            "Z958",
            "Z959",
        ],
    },
    "Cerebrovascular_Disease": {
        "9": [
            "36234",
            "430",
            "431",
            "432",
            "433",
            "434",
            "435",
            "436",
            "437",
            "438",
        ],
        "10": [
            "G45",
            "G46",
            "H340",
            "H341",
            "H342",
            "I60",
            "I61",
            "I62",
            "I63",
            "I64",
            "I65",
            "I66",
            "I67",
            "I68",
        ],
    },
    "Dementia": {
        "9": [
            "290",
            "2940",
            "2941",
            "2942",
            "2948",
            "3310",
            "3311",
            "3312",
            "3317",
            "797",
        ],
        "10": [
            "F01",
            "F02",
            "F03",
            "F04",
            "F05",
            "F061",
            "F068",
            "G132",
            "G138",
            "G30",
            "G310",
            "G311",
            "G312",
            "G914",
            "G94",
            "R4181",
            "R54",
        ],
    },
    "Chronic_Pulmonary_Disease": {
        "9": [
            "490",
            "491",
            "492",
            "493",
            "494",
            "495",
            "496",
            "500",
            "501",
            "502",
            "503",
            "504",
            "505",
            "5064",
            "5081",
            "5088",
        ],
        "10": [
            "J40",
            "J41",
            "J42",
            "J43",
            "J44",
            "J45",
            "J46",
            "J47",
            "J60",
            "J61",
            "J62",
            "J63",
            "J64",
            "J65",
            "J66",
            "J67",
            "J684",
            "J701",
            "J703",
        ],
    },
    "Rheumatic_Disease": {
        "9": [
            "4465",
            "7100",
            "7101",
            "7102",
            "7103",
            "7104",
            "7140",
            "7141",
            "7142",
            "7148",
            "725",
        ],
        "10": [
            "M05",
            "M06",
            "M315",
            "M32",
            "M33",
            "M34",
            "M351",
            "M353",
            "M360",
        ],
    },
    "Peptic_Ulcer_Disease": {
        "9": ["531", "532", "533", "534"],
        "10": ["K25", "K26", "K27", "K28"],
    },
    "Liver_Disease_Mild": {
        "9": [
            "07022",
            "07023",
            "07032",
            "07033",
            "07044",
            "07054",
            "0706",
            "0709",
            "570",
            "571",
            "5733",
            "5734",
            "5738",
            "5739",
            "V427",
        ],
        "10": [
            "B18",
            "K700",
            "K701",
            "K702",
            "K703",
            "K709",
            "K713",
            "K714",
            "K715",
            "K717",
            "K73",
            "K74",
            "K760",
            "K762",
            "K763",
            "K764",
            "K768",
            "K769",
            "Z944",
        ],
    },
    "Liver_Disease_Moderate_Severe": {
        "9": [
            "4560",
            "4561",
            "4562",
            "5722",
            "5723",
            "5724",
            "5728",
        ],
        "10": [
            "I850",
            "I864",
            "K704",
            "K711",
            "K721",
            "K729",
            "K765",
            "K766",
            "K767",
        ],
    },
    "Diabetes_without_Chronic_Complications": {
        "9": [
            "2490",
            "2491",
            "2492",
            "2493",
            "2499",
            "2508",
            "2509",
        ],
        "10": [
            "E080",
            "E081",
            "E086",
            "E088",
            "E089",
            "E090",
            "E091",
            "E096",
            "E098",
            "E099",
            "E100",
            "E101",
            "E106",
            "E108",
            "E109",
            "E110",
            "E111",
            "E116",
            "E118",
            "E119",
            "E130",
            "E131",
            "E136",
            "E138",
            "E139",
        ],
    },
    "Diabetes_with_Chronic_Complications": {
        "9": ["2504", "2505", "2506", "2507"],
        "10": [
            "E082",
            "E083",
            "E084",
            "E085",
            "E092",
            "E093",
            "E094",
            "E095",
            "E102",
            "E103",
            "E104",
            "E105",
            "E107",
            "E112",
            "E113",
            "E114",
            "E115",
            "E117",
            "E132",
            "E133",
            "E134",
            "E135",
            "E137",
        ],
    },
    "Hemiplegia_Paraplegia": {
        "9": ["3341", "342", "343", "344"],
        "10": [
            "G041",
            "G114",
            "G800",
            "G801",
            "G802",
            "G81",
            "G82",
            "G83",
        ],
    },
    "Renal_Disease_Mild_Moderate": {
        "9": [
            "40300",
            "40310",
            "40390",
            "40400",
            "40401",
            "40410",
            "40411",
            "40490",
            "40491",
            "582",
            "583",
            "5851",
            "5852",
            "5853",
            "5854",
            "5859",
            "V420",
        ],
        "10": [
            "I129",
            "I130",
            "I1310",
            "N03",
            "N05",
            "N181",
            "N182",
            "N183",
            "N184",
            "N189",
            "Z940",
        ],
    },
    "Renal_Disease_Severe": {
        "9": [
            "40301",
            "40311",
            "40391",
            "40402",
            "40403",
            "40412",
            "40413",
            "40492",
            "40493",
            "5855",
            "5856",
            "586",
            "5880",
            "V451",
            "V56",
        ],
        "10": [
            "I120",
            "I1311",
            "I132",
            "N185",
            "N186",
            "N19",
            "N250",
            "Z49",
            "Z992",
        ],
    },
    "HIV": {"9": ["042"], "10": ["B20"]},
    "Metastatic_Solid_Tumor": {
        "9": ["196", "197", "198", "1990"],
        "10": ["C77", "C78", "C79", "C800", "C802"],
    },
    "Malignancy": {
        "9": [
            "14",
            "15",
            "16",
            "170",
            "171",
            "172",
            "174",
            "175",
            "176",
            "179",
            "18",
            "190",
            "191",
            "192",
            "193",
            "194",
            "195",
            "1991",
            "200",
            "201",
            "202",
            "203",
            "204",
            "205",
            "206",
            "207",
            "208",
            "2386",
        ],
        "10": [
            "C0",
            "C1",
            "C2",
            "C30",
            "C31",
            "C32",
            "C33",
            "C34",
            "C37",
            "C38",
            "C39",
            "C40",
            "C41",
            "C43",
            "C45",
            "C46",
            "C47",
            "C48",
            "C49",
            "C50",
            "C51",
            "C52",
            "C53",
            "C54",
            "C55",
            "C56",
            "C57",
            "C58",
            "C60",
            "C61",
            "C62",
            "C63",
            "C76",
            "C801",
            "C81",
            "C82",
            "C83",
            "C84",
            "C85",
            "C88",
            "C9",
        ],
    },
}

# AIDS-defining OI codes (MUST co-occur with HIV for AIDS flag)
# NO HIV codes (042/B20) in this list — those are in CHARLSON["HIV"]
AIDS_OI = {
    "9": [
        "112",
        "180",
        "114",
        "1175",
        "0074",
        "0785",
        "3483",
        "054",
        "115",
        "0072",
        "176",
        "200",
        "201",
        "202",
        "203",
        "204",
        "205",
        "206",
        "207",
        "208",
        "209",
        "031",
        "010",
        "011",
        "012",
        "013",
        "014",
        "015",
        "016",
        "017",
        "018",
        "1363",
        "V1261",
        "0463",
        "0031",
        "130",
        "7994",
    ],
    "10": [
        "B37",
        "C53",
        "B38",
        "B45",
        "A072",
        "B25",
        "G934",
        "B00",
        "B39",
        "A073",
        "C46",
        "C81",
        "C82",
        "C83",
        "C84",
        "C85",
        "C86",
        "C87",
        "C88",
        "C9",
        "C90",
        "C91",
        "C92",
        "C93",
        "C94",
        "C95",
        "C96",
        "A31",
        "A15",
        "A16",
        "A17",
        "A18",
        "A19",
        "B59",
        "Z8701",
        "A812",
        "A021",
        "B58",
        "R64",
    ],
}

# Build prefix-match SQL via concept table (Chenxi's approach)
# Joins condition_occurrence -> concept on condition_source_concept_id
# and filters vocabulary_id IN ('ICD9CM','ICD10CM') for precise matching.
conditions_list = []
for condition, codes in CHARLSON.items():
    prefix_clauses = []
    for ver, voc in [("9", "ICD9CM"), ("10", "ICD10CM")]:
        for c in codes.get(ver, []):
            prefix_clauses.append(
                f"(STARTS_WITH(UPPER(REPLACE(c.concept_code,'.','')),"
                f"'{c}') AND c.vocabulary_id = '{voc}')"
            )
    if prefix_clauses:
        conditions_list.append(
            f"MAX(CASE WHEN {' OR '.join(prefix_clauses)} THEN 1 ELSE 0 END)"
            f" AS {condition}"
        )

# OI intermediate flag for AIDS two-step (computed in same query)
oi_clauses = []
for ver, voc in [("9", "ICD9CM"), ("10", "ICD10CM")]:
    for c in AIDS_OI.get(ver, []):
        oi_clauses.append(
            f"(STARTS_WITH(UPPER(REPLACE(c.concept_code,'.','')),"
            f"'{c}') AND c.vocabulary_id = '{voc}')"
        )
conditions_list.append(
    f"MAX(CASE WHEN {' OR '.join(oi_clauses)} THEN 1 ELSE 0 END) AS has_oi"
)

pids_str = ",".join(map(str, covid_cohort.person_id.tolist()))
charlson_sql = f"""
SELECT co.person_id, {','.join(conditions_list)}
FROM `{CDR}`.condition_occurrence co
JOIN `{CDR}`.concept c
  ON c.concept_id = co.condition_source_concept_id
WHERE co.person_id IN ({pids_str})
  AND c.vocabulary_id IN ('ICD9CM', 'ICD10CM')
GROUP BY co.person_id
"""
charlson = query(charlson_sql, "Charlson")

# Fill missing COVID patients with 0
charlson = covid_cohort[["person_id"]].merge(charlson, on="person_id", how="left")
for col in list(CHARLSON.keys()) + ["has_oi"]:
    charlson[col] = charlson[col].fillna(0).astype(int)

# AIDS = HIV AND OI co-occurrence (DualR canonical pattern)
charlson["AIDS"] = ((charlson["HIV"] == 1) & (charlson["has_oi"] == 1)).astype(int)
# Hierarchy rule 6: AIDS=1 -> HIV=0
charlson["HIV"] = ((charlson["HIV"] == 1) & (charlson["AIDS"] == 0)).astype(int)
charlson.drop(columns=["has_oi"], inplace=True)

# Verify
aids_n = charlson["AIDS"].sum()
hiv_n = charlson["HIV"].sum()
aids_pct = aids_n / len(charlson) * 100
hiv_pct = hiv_n / len(charlson) * 100
print(
    f"  AIDS verified: HIV={hiv_n:,} ({hiv_pct:.2f}%)  AIDS={aids_n:,} ({aids_pct:.2f}%)"
    f"  total HIV-infected={aids_n + hiv_n:,}"
)
assert aids_pct < 2.0, f"AIDS {aids_pct:.2f}% > 2% — check OI codes"

# Hierarchical trump rules (Glasheen 2019)
TRUMP_RULES = [
    ("AIDS", "HIV"),  # already applied above, enforced again
    ("Hemiplegia_Paraplegia", "Cerebrovascular_Disease"),
    ("Liver_Disease_Moderate_Severe", "Liver_Disease_Mild"),
    ("Diabetes_with_Chronic_Complications", "Diabetes_without_Chronic_Complications"),
    ("Renal_Disease_Severe", "Renal_Disease_Mild_Moderate"),
    ("Metastatic_Solid_Tumor", "Malignancy"),
]
for winner, loser in TRUMP_RULES:
    charlson.loc[charlson[winner] == 1, loser] = 0

como_cols = list(CHARLSON.keys()) + ["AIDS"]
print(f"\n  Charlson computed for {len(charlson):,} patients")
for col in como_cols:
    n = charlson[col].sum()
    print(f"    {col:50s} {n:>6,} ({n/len(charlson)*100:5.2f}%)")
save(charlson, "03_charlson.csv")


# =====================================================================
# STEP 4: SOCIAL DETERMINANTS OF HEALTH
# Insurance recoded as hierarchical categorical
# =====================================================================
print("\n" + "=" * 70)
print("STEP 4: Social Determinants of Health")
print("=" * 70)

# ── Disability (6 sub-domains + lumped) ──────────────────────────────
DISABILITY_Q = {
    "disability_hearing": {"q": 903573, "yes": 903587, "no": 903503},
    "disability_vision": {"q": 903574, "yes": 903504, "no": 903597},
    "disability_cognition": {"q": 903575, "yes": 903599, "no": 903600},
    "disability_mobility": {"q": 903576, "yes": 903602, "no": 903603},
    "disability_selfcare": {"q": 903577, "yes": 903605, "no": 903606},
    "disability_independent": {"q": 903578, "yes": 903608, "no": 903609},
}

dcases = [f"""MAX(CASE WHEN observation_source_concept_id={v['q']}
             AND value_source_concept_id={v['yes']} THEN 'Yes'
        WHEN observation_source_concept_id={v['q']}
             AND value_source_concept_id={v['no']} THEN 'No'
        ELSE NULL END) AS {k}""" for k, v in DISABILITY_Q.items()]

disability = query(
    f"""
SELECT person_id, {','.join(dcases)}
FROM `{CDR}`.observation
WHERE observation_source_concept_id IN
  ({','.join([str(v['q']) for v in DISABILITY_Q.values()])})
GROUP BY person_id""",
    "Disability",
)
disability = disability[disability.person_id.isin(covid_cohort.person_id)].copy()

dcols = list(DISABILITY_Q.keys())
disability["disability_any"] = "Missing"
disability.loc[
    disability[dcols].apply(lambda r: "Yes" in r.values, axis=1), "disability_any"
] = "Yes"
disability.loc[
    disability[dcols].apply(lambda r: all(v == "No" for v in r.values if v), axis=1)
    & (disability["disability_any"] != "Yes"),
    "disability_any",
] = "No"


#  Insurance — hierarchical categorical ────────────────────────
# Query binary flags first, then recode hierarchically.
# Hierarchy: Medicaid > Medicare > Employer > Other_None > Missing
# Rationale: Medicaid eligibility signals low income (disparity signal).
# Dual-eligible (Medicaid + Medicare) classified as Medicaid.
insurance_raw = query(
    f"""
SELECT person_id,
  MAX(CASE WHEN value_source_concept_id=43529120 THEN 1 ELSE 0 END) AS ins_employer,
  MAX(CASE WHEN value_source_concept_id=43529210 THEN 1 ELSE 0 END) AS ins_medicare,
  MAX(CASE WHEN value_source_concept_id=43529209 THEN 1 ELSE 0 END) AS ins_medicaid
FROM `{CDR}`.observation
WHERE observation_source_concept_id=43528428
GROUP BY person_id""",
    "Insurance",
)
insurance_raw = insurance_raw[
    insurance_raw.person_id.isin(covid_cohort.person_id)
].copy()

# Identify who answered the insurance question at all
ins_respondents = set(insurance_raw.person_id)

# Hierarchical recode
insurance_raw["insurance_type"] = "Other_None"  # default: answered but none of 3
insurance_raw.loc[insurance_raw.ins_employer == 1, "insurance_type"] = "Employer"
insurance_raw.loc[insurance_raw.ins_medicare == 1, "insurance_type"] = "Medicare"
insurance_raw.loc[insurance_raw.ins_medicaid == 1, "insurance_type"] = "Medicaid"

# Build insurance df for all cohort members (non-respondents → Missing)
insurance = covid_cohort[["person_id"]].merge(
    insurance_raw[["person_id", "insurance_type"]], on="person_id", how="left"
)
insurance["insurance_type"] = insurance["insurance_type"].fillna("Missing")

print(f"  Insurance distribution:")
print(f"  {insurance.insurance_type.value_counts().to_dict()}")

# Also keep binary flags for backward compatibility in sensitivity analyses
insurance = insurance.merge(
    insurance_raw[["person_id", "ins_employer", "ins_medicare", "ins_medicaid"]],
    on="person_id",
    how="left",
)
insurance[["ins_employer", "ins_medicare", "ins_medicaid"]] = (
    insurance[["ins_employer", "ins_medicare", "ins_medicaid"]].fillna(0).astype(int)
)


# ── Other SDoH (unchanged from v5) ──────────────────────────────────
def extract_categorical(concept_id, mapping, label):
    sql = f"""SELECT person_id,
      CASE {' '.join([f"WHEN value_source_concept_id={k} THEN '{v}'"
                      for k, v in mapping.items()])}
      ELSE 'Missing' END AS {label}
    FROM `{CDR}`.observation
    WHERE observation_source_concept_id={concept_id}
      AND value_source_concept_id NOT IN (903079,903096)"""
    df = query(sql, label.title())
    df = df[df.person_id.isin(covid_cohort.person_id)]
    return df.groupby("person_id", as_index=False).first()


employment = extract_categorical(
    1585952,
    {
        1585953: "Employed",
        1585958: "Student",
        1585955: "Unemployed",
        1585956: "Unemployed",
        1585960: "Unemployed",
        1585957: "Others",
        1585959: "Others",
        1585954: "Others",
    },
    "employment",
)

income = extract_categorical(
    1585375,
    {
        1585376: "less_10k",
        1585377: "10k_25k",
        1585378: "25k_35k",
        1585379: "35k_100k",
        1585380: "35k_100k",
        1585381: "35k_100k",
        1585382: "100k_150k",
        1585383: "150k_200k",
        1585384: "more_200k",
    },
    "income",
)

education = extract_categorical(
    1585940,
    {
        1585941: "Never_Attended",
        1585942: "Below_GED",
        1585943: "Below_GED",
        1585944: "Below_GED",
        1585945: "GED_or_College",
        1585946: "GED_or_College",
        1585947: "Advanced",
        1585948: "Advanced",
    },
    "education",
)

housing = extract_categorical(
    1585370,
    {1585371: "Own", 1585372: "Rent", 1585373: "Others"},
    "housing",
)

housing_stab = query(
    f"""
SELECT person_id,
  CASE WHEN value_source_concept_id=1585887 THEN 'Unstable'
       WHEN value_source_concept_id=1585888 THEN 'Stable'
       ELSE 'Missing' END AS housing_stability
FROM `{CDR}`.observation
WHERE observation_source_concept_id=1585886
  AND value_source_concept_id NOT IN (903096)""",
    "Housing stability",
)
housing_stab = housing_stab[housing_stab.person_id.isin(covid_cohort.person_id)]
housing_stab = housing_stab.groupby("person_id", as_index=False).first()

# ── Merge all SDoH ──────────────────────────────────────────────────
sdoh = covid_cohort[["person_id"]].copy()
for df, name in [
    (disability, "disability"),
    (
        insurance[
            [
                "person_id",
                "insurance_type",
                "ins_employer",
                "ins_medicare",
                "ins_medicaid",
            ]
        ],
        "insurance",
    ),
    (employment, "employment"),
    (income, "income"),
    (education, "education"),
    (housing, "housing"),
    (housing_stab, "housing_stability"),
]:
    sdoh = sdoh.merge(df, on="person_id", how="left")
save(sdoh, "04_sdoh.csv")


#  SDoH timing (P1.2) ──────────────────────────────────────────
print("\n  Computing SDoH timing...")
sdoh_timing_sql = f"""
SELECT person_id, MIN(observation_date) AS basics_survey_date
FROM `{CDR}`.observation
WHERE observation_source_concept_id = 1585845
GROUP BY person_id"""
sdoh_timing = query(sdoh_timing_sql, "SDoH timing")
sdoh_timing = sdoh_timing[sdoh_timing.person_id.isin(covid_cohort.person_id)].copy()
sdoh_timing = sdoh_timing.merge(
    covid_cohort[["person_id", "covid_index_date"]], on="person_id"
)
sdoh_timing["basics_survey_date"] = pd.to_datetime(sdoh_timing["basics_survey_date"])
sdoh_timing["covid_index_date"] = pd.to_datetime(sdoh_timing["covid_index_date"])
sdoh_timing["sdoh_days_before_covid"] = (
    sdoh_timing["covid_index_date"] - sdoh_timing["basics_survey_date"]
).dt.days
sdoh_timing["sdoh_pre_index"] = (sdoh_timing["sdoh_days_before_covid"] >= 0).astype(int)

n_pre = sdoh_timing.sdoh_pre_index.sum()
n_post = (sdoh_timing.sdoh_pre_index == 0).sum()
med = sdoh_timing.sdoh_days_before_covid.median()
q1 = sdoh_timing.sdoh_days_before_covid.quantile(0.25)
q3 = sdoh_timing.sdoh_days_before_covid.quantile(0.75)
print(f"  Median {med:.0f} days before COVID (IQR {q1:.0f}–{q3:.0f})")
print(f"  Pre-index: {n_pre:,} ({n_pre/len(sdoh_timing)*100:.1f}%)")
print(f"  Post-index: {n_post:,} ({n_post/len(sdoh_timing)*100:.1f}%)")
save(
    sdoh_timing[
        ["person_id", "basics_survey_date", "sdoh_days_before_covid", "sdoh_pre_index"]
    ],
    "04b_sdoh_timing.csv",
)


# =====================================================================
# STEP 5: VACCINATION
# =====================================================================
print("\n" + "=" * 70)
print("STEP 5: Vaccination")
print("=" * 70)

vacc = query(
    f"""
SELECT person_id, MIN(drug_exposure_start_date) AS first_vacc_date
FROM `{CDR}`.drug_exposure
WHERE drug_concept_id IN (37003436,37003518,37003446,702866,702834,
                          724907,724906,724905,739906)
GROUP BY person_id""",
    "Vaccination",
)
vacc = vacc[vacc.person_id.isin(covid_cohort.person_id)].copy()
vacc = vacc.merge(covid_cohort[["person_id", "covid_index_date"]], on="person_id")
vacc["pre_covid"] = pd.to_datetime(vacc["first_vacc_date"]) <= pd.to_datetime(
    vacc["covid_index_date"]
)

vacc_status = covid_cohort[["person_id"]].merge(
    vacc[["person_id", "pre_covid"]], on="person_id", how="left"
)
vacc_status["vaccination"] = "Unknown"
vacc_status.loc[vacc_status.pre_covid == True, "vaccination"] = "Vaccinated"
print(f"  {vacc_status.vaccination.value_counts().to_dict()}")
save(vacc_status[["person_id", "vaccination"]], "05_vaccination.csv")


# =====================================================================
# STEP 6: MATCHING VARIABLE EXTRACTION
# Extracts EHR-observability proxies for 01b_psm.R (MatchIt).
# PSM is now handled in R — see 01b_psm.R.
# =====================================================================
print("\n" + "=" * 70)
print("STEP 6: Matching Variable Extraction  (for 01b_psm.R)")
print("=" * 70)

match_vars = query(
    f"""
SELECT p.person_id,
  MIN(o.observation_date) AS basics_survey_date,
  COUNT(DISTINCT co.condition_concept_id) AS num_diagnosis,
  DATE_DIFF(MAX(co.condition_start_date),
            MIN(co.condition_start_date), DAY) AS ehr_length_days
FROM `{CDR}`.person p
JOIN `{CDR}`.observation o
  ON p.person_id=o.person_id
  AND o.observation_source_concept_id=1585845
JOIN `{CDR}`.condition_occurrence co
  ON p.person_id=co.person_id
GROUP BY p.person_id""",
    "Matching variables",
)

match_df = match_vars[match_vars.person_id.isin(covid_cohort.person_id)].copy()

# Convert survey date to ordinal (days since epoch) for MatchIt
match_df["enrollment_ord"] = pd.to_datetime(match_df["basics_survey_date"]).apply(
    lambda x: x.toordinal() if pd.notna(x) else np.nan
)

n_complete = match_df.dropna(
    subset=["enrollment_ord", "num_diagnosis", "ehr_length_days"]
).shape[0]
print(f"  Complete matching variables: {n_complete:,} / {len(match_df):,}")
print(
    f"  Cases with matching vars: "
    f"{match_df[match_df.person_id.isin(covid_cohort[covid_cohort.severity==1].person_id)].dropna(subset=['enrollment_ord','num_diagnosis','ehr_length_days']).shape[0]:,}"
)

save(
    match_df[
        [
            "person_id",
            "basics_survey_date",
            "enrollment_ord",
            "num_diagnosis",
            "ehr_length_days",
        ]
    ],
    "06_matching_variables.csv",
)


# =====================================================================
# ETL COMPLETE — next step: Rscript 01b_psm.R aou_{version}
# =====================================================================
print(f"\n{'='*70}")
n_files = len([f for f in os.listdir(RESULTS) if f.endswith(".csv")])
print(f"AoU ETL [{VERSION.upper()}] COMPLETE — {n_files} files in {RESULTS}/")
print("=" * 70)
print(f"\n  Next: Rscript 01b_psm.R aou_{VERSION}")
print(f"  (PSM via MatchIt → 07_matched_cohort.csv, 08_regression_base.csv)")
