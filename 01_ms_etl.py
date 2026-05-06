#!/usr/bin/env python3
"""
COVID-19 Severity × SDoH — MarketScan ETL (Clinical Transportability)
Runs on Quartz HPC with DuckDB. Reads from /N/project/Marketscan1/parquet/.

Consistent with AoU implementation:
  - 14-day hospitalization window (primary), visit-linked (inpatient file)
  - Charlson: Shihui/Chenxi 2021 (NCI update of Glasheen 2019)
  - AIDS: two-step (HIV AND OI), AIDS→HIV trump rule
  - Pandemic wave variable
  - Control reuse statistics

Usage: python 01_ms_etl.py
Output: results/ms/*.csv
"""

import os
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

import duckdb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

MS_DIR = "/N/project/Marketscan1/parquet"
RESULTS = "results/ms"
os.makedirs(RESULTS, exist_ok=True)
YEARS = ["2020", "2021", "2022", "2023"]

con = duckdb.connect(database=":memory:")
con.execute("PRAGMA threads=7")
con.execute("SET memory_limit='65GB'")

print("=" * 70)
print("COVID-19 SEVERITY — MarketScan CLINICAL TRANSPORTABILITY")
print("=" * 70)
print(f"  Source: {MS_DIR}")
print(f"  Years:  {YEARS}")
print(f"  Output: {RESULTS}/")
print("=" * 70)

# =====================================================================
# STEP 1: COVID COHORT (14-day hospitalization window)
# =====================================================================
print("\n" + "=" * 70)
print("STEP 1: COVID Cohort (U07.1, 14-day hospitalization window)")
print("=" * 70)

ip_unions = []
for y in YEARS:
    f = f"{MS_DIR}/mscan_{y}_i.parquet"
    if not os.path.exists(f):
        continue
    dx_cols = ["PDX"] + [f"DX{i}" for i in range(1, 16)]
    for col in dx_cols:
        ip_unions.append(f"""
        SELECT ENROLID, ADMDATE AS event_date, {col} AS dx, 'inpatient' AS src
        FROM read_parquet('{f}')
        WHERE {col} IS NOT NULL AND REPLACE(UPPER(CAST({col} AS VARCHAR)),'.','') LIKE 'U071%'
        """)

op_unions = []
for y in YEARS:
    f = f"{MS_DIR}/mscan_{y}_o.parquet"
    if not os.path.exists(f):
        continue
    for col in ["DX1", "DX2", "DX3", "DX4"]:
        op_unions.append(f"""
        SELECT ENROLID, SVCDATE AS event_date, {col} AS dx, 'outpatient' AS src
        FROM read_parquet('{f}')
        WHERE {col} IS NOT NULL AND REPLACE(UPPER(CAST({col} AS VARCHAR)),'.','') LIKE 'U071%'
        """)

print(
    f"  Building COVID union from {len(ip_unions)} inpatient"
    f" + {len(op_unions)} outpatient queries..."
)

# 14-day window: hospitalization = inpatient COVID claim within 14 days of index
covid_sql = f"""
WITH covid_all AS (
    {' UNION ALL '.join(ip_unions + op_unions)}
),
covid_index AS (
    SELECT ENROLID AS person_id,
           MIN(event_date) AS covid_index_date
    FROM covid_all
    GROUP BY ENROLID
),
covid_severity AS (
    SELECT ci.person_id, ci.covid_index_date,
           MAX(CASE WHEN ca.src = 'inpatient'
                     AND ca.event_date BETWEEN ci.covid_index_date
                         AND ci.covid_index_date + INTERVAL 14 DAY
                    THEN 1 ELSE 0 END) AS severity,
           MAX(CASE WHEN ca.src = 'inpatient'
                    THEN 1 ELSE 0 END) AS severity_broad
    FROM covid_index ci
    LEFT JOIN covid_all ca ON ci.person_id = ca.ENROLID
    GROUP BY ci.person_id, ci.covid_index_date
)
SELECT * FROM covid_severity
"""

covid_cohort = con.sql(covid_sql).df()
print(f"  Total COVID+: {len(covid_cohort):,}")

n_strict = covid_cohort.severity.sum()
n_broad = covid_cohort.severity_broad.sum()
print(
    f"  Hospitalized (14-day strict): {n_strict:,} ({n_strict/len(covid_cohort)*100:.1f}%)"
)
print(
    f"  Hospitalized (any-time broad): {n_broad:,} ({n_broad/len(covid_cohort)*100:.1f}%)"
)

# Pandemic wave
covid_cohort["covid_index_date"] = pd.to_datetime(covid_cohort["covid_index_date"])
covid_cohort["pandemic_wave"] = "pre_delta"
covid_cohort.loc[covid_cohort.covid_index_date >= "2021-06-15", "pandemic_wave"] = (
    "delta"
)
covid_cohort.loc[covid_cohort.covid_index_date >= "2021-12-15", "pandemic_wave"] = (
    "omicron"
)
print(f"  Wave: {covid_cohort.pandemic_wave.value_counts().to_dict()}")

covid_cohort[
    ["person_id", "covid_index_date", "severity", "severity_broad", "pandemic_wave"]
].to_csv(f"{RESULTS}/01_covid_cohort.csv", index=False)
print(f"  Saved: {RESULTS}/01_covid_cohort.csv")


# =====================================================================
# STEP 2: DEMOGRAPHICS (from enrollment)
# =====================================================================
print("\n" + "=" * 70)
print("STEP 2: Demographics + Plan Type")
print("=" * 70)

enroll_unions = []
for y in YEARS:
    f = f"{MS_DIR}/mscan_{y}_t.parquet"
    if os.path.exists(f):
        enroll_unions.append(
            f"SELECT ENROLID, DOBYR, AGE, SEX, REGION, PLANTYP FROM read_parquet('{f}')"
        )

pids_list = covid_cohort.person_id.tolist()
con.register("covid_pids", pd.DataFrame({"person_id": pids_list}))

demo_sql = f"""
WITH enroll AS ({' UNION ALL '.join(enroll_unions)})
SELECT e.ENROLID AS person_id,
       FIRST(e.DOBYR) AS year_of_birth,
       FIRST(e.AGE) AS age,
       FIRST(e.SEX) AS sex_raw,
       FIRST(e.REGION) AS region,
       FIRST(e.PLANTYP) AS plantyp
FROM enroll e
INNER JOIN covid_pids cp ON e.ENROLID = cp.person_id
GROUP BY e.ENROLID
"""

demo = con.sql(demo_sql).df()
print(f"  Matched demographics: {len(demo):,}")

demo["sex_at_birth"] = demo["sex_raw"].apply(
    lambda x: (
        "Male"
        if str(x).strip().upper() in ("1", "M", "MALE")
        else ("Female" if str(x).strip().upper() in ("2", "F", "FEMALE") else "Other")
    )
)

demo["age_at_covid"] = demo["age"].fillna(0).astype(int)
demo["age_group"] = pd.cut(
    demo["age_at_covid"],
    bins=[0, 45, 55, 65, 200],
    labels=["<45", "45-54", "55-64", "65+"],
    right=False,
)

PLAN_MAP = {
    1: "Basic",
    2: "Comprehensive",
    3: "EPO",
    4: "HMO",
    5: "POS",
    6: "PPO",
    7: "CDHP",
    8: "HDHP",
    9: "Unknown",
}
demo["plan_type"] = demo["plantyp"].map(PLAN_MAP).fillna("Unknown")

REGION_MAP = {
    "1": "Northeast",
    "2": "NorthCentral",
    "3": "South",
    "4": "West",
    "5": "Unknown",
}
demo["region_name"] = demo["region"].astype(str).map(REGION_MAP).fillna("Unknown")

demo["race"] = "Unknown"
demo["ethnicity"] = "Unknown"

demo_out = demo[
    [
        "person_id",
        "sex_at_birth",
        "race",
        "ethnicity",
        "age_at_covid",
        "age_group",
        "year_of_birth",
        "plan_type",
        "region_name",
    ]
]

print(f"  Sex: {demo_out.sex_at_birth.value_counts().to_dict()}")
print(f"  Age: {demo_out.age_group.value_counts().to_dict()}")
demo_out.to_csv(f"{RESULTS}/02_demographics.csv", index=False)


# =====================================================================
# STEP 3: CHARLSON COMORBIDITIES
# Glasheen 2019 CDMF CCI (the BIBLE)
# Flat lists (ICD-9 + ICD-10 mixed) for MarketScan prefix matching
# =====================================================================
print("\n" + "=" * 70)
print("STEP 3: Charlson Comorbidities")
print("=" * 70)

print("  Building long-format diagnosis table...")
dx_unions = []
for y in YEARS:
    ip_f = f"{MS_DIR}/mscan_{y}_i.parquet"
    if os.path.exists(ip_f):
        for col in ["PDX"] + [f"DX{i}" for i in range(1, 16)]:
            dx_unions.append(f"""
            SELECT ENROLID AS person_id, REPLACE(UPPER(CAST({col} AS VARCHAR)),'.','') AS dx_code
            FROM read_parquet('{ip_f}') WHERE {col} IS NOT NULL""")
    op_f = f"{MS_DIR}/mscan_{y}_o.parquet"
    if os.path.exists(op_f):
        for col in ["DX1", "DX2", "DX3", "DX4"]:
            dx_unions.append(f"""
            SELECT ENROLID AS person_id, REPLACE(UPPER(CAST({col} AS VARCHAR)),'.','') AS dx_code
            FROM read_parquet('{op_f}') WHERE {col} IS NOT NULL""")

con.sql(f"""
CREATE OR REPLACE TABLE dx_long AS
SELECT DISTINCT person_id, dx_code
FROM ({' UNION ALL '.join(dx_unions)}) sub
WHERE person_id IN (SELECT person_id FROM covid_pids)
""")
dx_count = con.sql("SELECT COUNT(*) FROM dx_long").fetchone()[0]
print(f"  Diagnosis rows (COVID patients): {dx_count:,}")

# Charlson code sets: Glasheen 2019 CDMF CCI (the BIBLE)
# Source: Glasheen WP et al. Am Health Drug Benefits 2019;12(4):188-197
# Flat lists (ICD-9 + ICD-10 mixed) for MarketScan prefix matching.
CHARLSON = {
    "Myocardial_Infarction": ["410", "412", "I21", "I22", "I252"],
    "Congestive_Heart_Failure": [
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
    "Peripheral_Vascular_Disease": [
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
    "Cerebrovascular_Disease": [
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
    "Dementia": [
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
    "Chronic_Pulmonary_Disease": [
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
    "Rheumatic_Disease": [
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
    "Peptic_Ulcer_Disease": [
        "531",
        "532",
        "533",
        "534",
        "K25",
        "K26",
        "K27",
        "K28",
    ],
    "Liver_Disease_Mild": [
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
    "Liver_Disease_Moderate_Severe": [
        "4560",
        "4561",
        "4562",
        "5722",
        "5723",
        "5724",
        "5728",
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
    "Diabetes_without_Chronic_Complications": [
        "2490",
        "2491",
        "2492",
        "2493",
        "2499",
        "2508",
        "2509",
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
    "Diabetes_with_Chronic_Complications": [
        "2504",
        "2505",
        "2506",
        "2507",
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
    "Hemiplegia_Paraplegia": [
        "3341",
        "342",
        "343",
        "344",
        "G041",
        "G114",
        "G800",
        "G801",
        "G802",
        "G81",
        "G82",
        "G83",
    ],
    "Renal_Disease_Mild_Moderate": [
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
    "Renal_Disease_Severe": [
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
    "HIV": ["042", "B20"],
    "Metastatic_Solid_Tumor": [
        "196",
        "197",
        "198",
        "1990",
        "C77",
        "C78",
        "C79",
        "C800",
        "C802",
    ],
    "Malignancy": [
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
}

TRUMP_RULES = [
    ("AIDS", "HIV"),
    ("Hemiplegia_Paraplegia", "Cerebrovascular_Disease"),
    ("Liver_Disease_Moderate_Severe", "Liver_Disease_Mild"),
    ("Diabetes_with_Chronic_Complications", "Diabetes_without_Chronic_Complications"),
    ("Renal_Disease_Severe", "Renal_Disease_Mild_Moderate"),
    ("Metastatic_Solid_Tumor", "Malignancy"),
]

# AIDS OI codes — NOT in CHARLSON. AIDS = HIV AND OI (two-step, per DualR).
# NO HIV codes (042/B20) in this list.
AIDS_OI = [
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
]

flag_exprs = []
for name, codes in CHARLSON.items():
    likes = " OR ".join([f"dx_code LIKE '{c}%'" for c in codes])
    flag_exprs.append(f"MAX(CASE WHEN ({likes}) THEN 1 ELSE 0 END) AS {name}")
# OI intermediate flag
oi_likes = " OR ".join([f"dx_code LIKE '{c}%'" for c in AIDS_OI])
flag_exprs.append(f"MAX(CASE WHEN ({oi_likes}) THEN 1 ELSE 0 END) AS has_oi")

charlson = con.sql(f"""
SELECT person_id, {','.join(flag_exprs)}
FROM dx_long
GROUP BY person_id
""").df()

charlson = covid_cohort[["person_id"]].merge(charlson, on="person_id", how="left")
for col in list(CHARLSON.keys()) + ["has_oi"]:
    charlson[col] = charlson[col].fillna(0).astype(int)

# AIDS = HIV AND OI (two-step)
charlson["AIDS"] = ((charlson["HIV"] == 1) & (charlson["has_oi"] == 1)).astype(int)
charlson["HIV"] = ((charlson["HIV"] == 1) & (charlson["AIDS"] == 0)).astype(int)
charlson.drop(columns=["has_oi"], inplace=True)

aids_prev = charlson["AIDS"].sum() / len(charlson) * 100
print(
    f"  AIDS verified: HIV={charlson['HIV'].sum():,}  AIDS={charlson['AIDS'].sum():,}"
    f" ({aids_prev:.3f}%)"
)
assert aids_prev < 2.0, f"AIDS prevalence {aids_prev:.2f}% > 2%"

for winner, loser in TRUMP_RULES:
    charlson.loc[charlson[winner] == 1, loser] = 0

all_como_cols = list(CHARLSON.keys()) + ["AIDS"]
print(f"\n  Charlson computed for {len(charlson):,} patients")
for col in all_como_cols:
    n = charlson[col].sum()
    print(f"    {col:45s} {n:>8,} ({n/len(charlson)*100:5.1f}%)")
charlson.to_csv(f"{RESULTS}/03_charlson.csv", index=False)


# =====================================================================
# STEP 4: VACCINATION (NDC-based from drug claims)
# =====================================================================
print("\n" + "=" * 70)
print("STEP 4: Vaccination (NDC)")
print("=" * 70)

vacc_unions = []
for y in ["2021", "2022", "2023"]:
    f = f"{MS_DIR}/mscan_{y}_d.parquet"
    if os.path.exists(f):
        vacc_unions.append(f"""
        SELECT ENROLID AS person_id, SVCDATE AS vacc_date
        FROM read_parquet('{f}')
        WHERE CAST(NDCNUM AS VARCHAR) LIKE '59267%'
           OR CAST(NDCNUM AS VARCHAR) LIKE '80777%'
           OR CAST(NDCNUM AS VARCHAR) LIKE '59676%'
        """)

if vacc_unions:
    vacc = con.sql(f"""
    SELECT person_id, MIN(vacc_date) AS first_vacc_date
    FROM ({' UNION ALL '.join(vacc_unions)})
    WHERE person_id IN (SELECT person_id FROM covid_pids)
    GROUP BY person_id
    """).df()
else:
    vacc = pd.DataFrame(columns=["person_id", "first_vacc_date"])

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
vacc_status[["person_id", "vaccination"]].to_csv(
    f"{RESULTS}/05_vaccination.csv", index=False
)


# =====================================================================
# STEP 5: PROPENSITY SCORE MATCHING (1:4, with replacement)
# =====================================================================
print("\n" + "=" * 70)
print("STEP 5: Propensity Score Matching (strict 14-day phenotype)")
print("=" * 70)

match_df = covid_cohort[["person_id", "severity"]].copy()

dx_counts = con.sql("""
SELECT person_id, COUNT(DISTINCT dx_code) AS num_diagnosis
FROM dx_long GROUP BY person_id
""").df()
match_df = match_df.merge(dx_counts, on="person_id", how="left")
match_df["num_diagnosis"] = match_df["num_diagnosis"].fillna(0)

print("  Computing enrollment dates for matching...")
enroll_date_unions = []
for y in YEARS:
    f = f"{MS_DIR}/mscan_{y}_t.parquet"
    if os.path.exists(f):
        enroll_date_unions.append(
            f"SELECT ENROLID AS person_id, DTSTART, DTEND FROM read_parquet('{f}')"
        )

enroll_dates = con.sql(f"""
SELECT e.person_id,
       MIN(e.DTSTART) AS first_enrollment,
       DATEDIFF('day', MIN(e.DTSTART), MAX(e.DTEND)) AS coverage_span_days
FROM ({' UNION ALL '.join(enroll_date_unions)}) e
WHERE e.person_id IN (SELECT person_id FROM covid_pids)
GROUP BY e.person_id
""").df()
enroll_dates["enroll_ord"] = pd.to_datetime(enroll_dates["first_enrollment"]).apply(
    lambda x: x.toordinal() if pd.notna(x) else np.nan
)

match_df = match_df.merge(
    enroll_dates[["person_id", "enroll_ord", "coverage_span_days"]],
    on="person_id",
    how="left",
)
match_df = match_df.dropna(subset=["enroll_ord", "num_diagnosis", "coverage_span_days"])
print(
    f"  Matching on: enroll_ord, num_diagnosis, coverage_span_days (N={len(match_df):,})"
)

X = StandardScaler().fit_transform(
    match_df[["enroll_ord", "num_diagnosis", "coverage_span_days"]].values
)
lr = LogisticRegression(max_iter=1000, random_state=42).fit(
    X, match_df["severity"].values
)
match_df["ps"] = lr.predict_proba(X)[:, 1]

logit_ps = np.log(match_df["ps"] / (1 - match_df["ps"]))
caliper = 0.2 * logit_ps.std()

cases = match_df[match_df.severity == 1]
controls = match_df[match_df.severity == 0]
nn = NearestNeighbors(n_neighbors=min(20, len(controls)), metric="euclidean")
nn.fit(controls[["ps"]].values)
_, indices = nn.kneighbors(cases[["ps"]].values)

records, dropped = [], 0
for i, (cidx, ctrl_idx) in enumerate(zip(cases.index, indices)):
    case_logit = np.log(cases.loc[cidx, "ps"] / (1 - cases.loc[cidx, "ps"]))
    valid = [
        controls.index[ci]
        for ci in ctrl_idx
        if abs(
            case_logit
            - np.log(
                controls.loc[controls.index[ci], "ps"]
                / (1 - controls.loc[controls.index[ci], "ps"])
            )
        )
        <= caliper
    ][:4]
    if not valid:
        dropped += 1
        continue
    records.append(
        {"person_id": cases.loc[cidx, "person_id"], "Treatment": 1, "stratum": i + 1}
    )
    for vi in valid:
        records.append(
            {
                "person_id": controls.loc[vi, "person_id"],
                "Treatment": 0,
                "stratum": i + 1,
            }
        )

matched = pd.DataFrame(records)
nc = matched[matched.Treatment == 1].person_id.nunique()
nr = (matched.Treatment == 0).sum()
print(
    f"  Cases: {nc:,}  |  Control rows: {nr:,}  |  Ratio: 1:{nr/nc:.1f}  |  Dropped: {dropped}"
)

# Control reuse statistics
ctrl_rows = matched[matched.Treatment == 0]
ctrl_reuse = ctrl_rows.groupby("person_id").size()
print(
    f"  Control reuse: {len(ctrl_reuse):,} unique, median {ctrl_reuse.median():.0f}"
    f" (IQR {ctrl_reuse.quantile(0.25):.0f}–{ctrl_reuse.quantile(0.75):.0f}),"
    f" max {ctrl_reuse.max()}"
)

pd.DataFrame(
    {
        "metric": [
            "n_unique_controls",
            "median_reuse",
            "iqr_lower",
            "iqr_upper",
            "max_reuse",
            "n_control_rows",
        ],
        "value": [
            len(ctrl_reuse),
            ctrl_reuse.median(),
            ctrl_reuse.quantile(0.25),
            ctrl_reuse.quantile(0.75),
            ctrl_reuse.max(),
            len(ctrl_rows),
        ],
    }
).to_csv(f"{RESULTS}/06b_control_reuse.csv", index=False)

matched.to_csv(f"{RESULTS}/06_matched_cohort.csv", index=False)


# =====================================================================
# STEP 6: FINAL REGRESSION DATAFRAME
# =====================================================================
print("\n" + "=" * 70)
print("STEP 6: Final Regression DataFrame")
print("=" * 70)

reg = matched.merge(demo_out, on="person_id", how="left")
reg = reg.merge(charlson, on="person_id", how="left")
como_cols = list(CHARLSON.keys()) + ["AIDS"]
reg[como_cols] = reg[como_cols].fillna(0).astype(int)
reg = reg.merge(vacc_status[["person_id", "vaccination"]], on="person_id", how="left")
reg["vaccination"] = reg["vaccination"].fillna("Unknown")

# Add pandemic wave and broad severity
reg = reg.merge(
    covid_cohort[["person_id", "pandemic_wave", "severity_broad"]],
    on="person_id",
    how="left",
)
reg["pandemic_wave"] = reg["pandemic_wave"].fillna("unknown")

print(f"  Shape: {reg.shape}")
reg.to_csv(f"{RESULTS}/07_regression_base.csv", index=False)

# No SDoH in MarketScan — create empty placeholder
pd.DataFrame({"person_id": covid_cohort.person_id}).to_csv(
    f"{RESULTS}/04_sdoh.csv", index=False
)

n_files = len([f for f in os.listdir(RESULTS) if f.endswith(".csv")])
print(f"\n{'='*70}")
print(f"PIPELINE COMPLETE — {n_files} files in {RESULTS}/")
print("=" * 70)

con.close()
