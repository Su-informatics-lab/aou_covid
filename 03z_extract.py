"""03z_extract.py -- flags for the R10 review analyses (Gottlieb, Adler-Milstein, Hua Xu
personas, 2026-09-25). Person-level output stays on the VM; only screened aggregates
print.

For every matched row (COVID-19: person and index date; influenza: person-season and
its index date) this adds, from the OMOP tables:

  pre_adm    an inpatient-type visit, or an ED visit spanning >= 1 calendar day, that
             started 1-3 days before the index date or was still open on it -- a
             hospitalization the case window (index to index + 14 days) cannot see
  q_ip       the qualifying hospitalization includes an inpatient-type visit
             (otherwise the row qualified only through the extended-ED rule)
  q_ed24     an ED visit in the window lasted >= 24 hours by its datetimes
  q_dx       a qualifying visit carries a diagnosis of the infection or of a
             respiratory disorder (descendants of SNOMED 320136, 37311061 COVID-19,
             4266367 influenza; or ICD-10-CM J or U07.1 source codes)
  q_icu      a qualifying visit is an intensive care visit (visit concept 32037)
  q_los      the longest qualifying stay, in calendar days
  death30    death recorded within 30 days of the index date
  z_inc      a pre-index ICD-10-CM code specific to income: Z59.5 (extreme poverty),
             Z59.6 (low income), Z59.86/Z59.87 (financial insecurity; material hardship)
             NOT USED: this and z59_any read condition_source_value, which is not reliably the
             ICD code in these CDRs, and miss the observation table; 03z_z59.py replaces them
  scr_any    a pre-index record of a structured social-needs screening item (LOINC
             panels and items listed in SCREEN_LOINC, in observation or measurement)
  payer_any  any payer_plan_period row for the person
  ins_after  the survey insurance item (43528428 or 1585389) was answered after the
             index date (first answer)
Also prints the survey concept behind the timing file (1585845).
  ARM=covid python3 03z_extract.py      (or ARM=flu on the influenza workspace)
"""

import os

import pandas as pd

ARM = os.environ.get("ARM", "covid")
CDR = os.environ.get("WORKSPACE_CDR")
MIN = 20
if ARM == "covid":
    B = "/home/jupyter/workspace/rw-migration-aou-rw-46c7ae9e/data/covid_sdoh/aou_v7"
    W = pd.read_csv("/home/jupyter/jno_v26/W_person_covid.csv", usecols=["person_id"])
    c = pd.read_csv(
        os.path.join(B, "01_covid_cohort.csv"),
        usecols=["person_id", "covid_index_date"],
    )
    ix = c[c.person_id.isin(W.person_id)].rename(columns={"covid_index_date": "d"})
    INF = "37311061"
else:
    m = pd.read_csv(
        "/home/jupyter/flu/07_matched_cohort.csv",
        usecols=["person_id", "flu_index_date"],
    )
    ix = m.drop_duplicates().rename(columns={"flu_index_date": "d"})
    INF = "4266367"
ix["d"] = pd.to_datetime(ix.d).dt.strftime("%Y-%m-%d")
ix = ix.drop_duplicates()
IDX = ",".join(
    f"STRUCT({int(r.person_id)} AS person_id, DATE '{r.d}' AS d)"
    for r in ix.itertuples()
)
IP, ED = "9201,32037,262,8717", "9203"
# structured social-needs screening (verify codes against the concept table printout)
SCREEN_LOINC = [
    "96777-8",
    "96778-6",
    "93025-5",
    "88122-7",
    "88123-5",
    "88124-3",
    "71802-3",
    "93033-9",
    "76513-1",
    "93031-3",
    "93030-5",
    "96779-4",
    "96780-2",
    "96781-0",
    "96782-8",
    "63586-2",
    "95618-5",
    "95617-7",
    "95616-9",
    "89555-7",
    "93159-2",
    "93038-8",
]


def q(sql):
    return pd.read_gbq(sql, dialect="standard", progress_bar_type=None)


## visits around the index date, and diagnosis-bearing visits, in 2 plain queries; the
## flags are computed in pandas (a single query with the semi-joins inside the aggregate
## ran for > 45 minutes)
V = q(f"""WITH idx AS (SELECT * FROM UNNEST([{IDX}]))
SELECT idx.person_id, idx.d, vo.visit_occurrence_id, vo.visit_concept_id,
       vo.visit_start_date AS vs, COALESCE(vo.visit_end_date, vo.visit_start_date) AS ve,
       vo.visit_start_datetime AS vst, vo.visit_end_datetime AS vet
FROM idx JOIN `{CDR}`.visit_occurrence vo ON vo.person_id = idx.person_id
WHERE vo.visit_start_date BETWEEN DATE_SUB(idx.d, INTERVAL 30 DAY) AND DATE_ADD(idx.d, INTERVAL 14 DAY)
  AND vo.visit_concept_id IN ({IP},{ED})""")
DX = q(
    f"""WITH idx AS (SELECT * FROM UNNEST([{IDX}])),
rc AS (SELECT descendant_concept_id AS cid FROM `{CDR}`.concept_ancestor WHERE ancestor_concept_id IN (320136, {INF}))
SELECT DISTINCT co.visit_occurrence_id
FROM idx JOIN `{CDR}`.condition_occurrence co ON co.person_id = idx.person_id
WHERE co.condition_start_date BETWEEN idx.d AND DATE_ADD(idx.d, INTERVAL 45 DAY)
  AND co.visit_occurrence_id IS NOT NULL
  AND (co.condition_concept_id IN (SELECT cid FROM rc)
       OR co.condition_source_value LIKE 'J%' OR co.condition_source_value LIKE 'U07.1%')"""
)
dxset = set(DX.visit_occurrence_id)
for c_ in ("d", "vs", "ve"):
    V[c_] = pd.to_datetime(V[c_])
V["ip"] = V.visit_concept_id.isin([int(x) for x in IP.split(",")])
V["ed1"] = (V.visit_concept_id == int(ED)) & ((V.ve - V.vs).dt.days >= 1)
hrs = (
    pd.to_datetime(V.vet, utc=True) - pd.to_datetime(V.vst, utc=True)
).dt.total_seconds() / 3600
V["ed24"] = (V.visit_concept_id == int(ED)) & (hrs >= 24)
V["inwin"] = (V.vs >= V.d) & (V.vs <= V.d + pd.Timedelta(days=14))
V["qual"] = V.inwin & (V.ip | V.ed1)
V["dx"] = V.visit_occurrence_id.isin(dxset)
V["pre"] = (V.ip | V.ed1) & (
    ((V.vs >= V.d - pd.Timedelta(days=3)) & (V.vs <= V.d - pd.Timedelta(days=1)))
    | ((V.vs < V.d) & (V.ve >= V.d))
)
V["los"] = (V.ve - V.vs).dt.days.where(V.qual)
g = V.groupby(["person_id", "d"])
F = pd.DataFrame(
    {
        "pre_adm": g.pre.any().astype(int),
        "q_ip": (V.inwin & V.ip).groupby([V.person_id, V.d]).any().astype(int),
        "q_ed24": (V.inwin & V.ed24).groupby([V.person_id, V.d]).any().astype(int),
        "q_dx": (V.qual & V.dx).groupby([V.person_id, V.d]).any().astype(int),
        "q_icu": (V.inwin & (V.visit_concept_id == 32037))
        .groupby([V.person_id, V.d])
        .any()
        .astype(int),
        "q_los": g.los.max(),
    }
).reset_index()
print("visit rows:", len(V), "| diagnosis-bearing visits:", len(dxset))
D = q(f"""WITH idx AS (SELECT * FROM UNNEST([{IDX}]))
SELECT idx.person_id, idx.d, MAX(IF(de.death_date BETWEEN idx.d AND DATE_ADD(idx.d, INTERVAL 30 DAY), 1, 0)) AS death30
FROM idx LEFT JOIN `{CDR}`.death de ON de.person_id = idx.person_id GROUP BY 1, 2""")
Z = q(f"""WITH idx AS (SELECT * FROM UNNEST([{IDX}]))
SELECT idx.person_id, idx.d,
  MAX(IF(REGEXP_CONTAINS(co.condition_source_value, r'^Z59\\.?(5|6|86|87)'), 1, 0)) AS z_inc,
  MAX(IF(REGEXP_CONTAINS(co.condition_source_value, r'^Z59'), 1, 0)) AS z59_any
FROM idx LEFT JOIN `{CDR}`.condition_occurrence co
  ON co.person_id = idx.person_id AND co.condition_start_date < idx.d
  AND co.condition_source_value LIKE 'Z59%'
GROUP BY 1, 2""")
codes = ",".join(f"'{x}'" for x in SCREEN_LOINC)
CON = q(f"""SELECT concept_id, concept_code, concept_name FROM `{CDR}`.concept
WHERE vocabulary_id = 'LOINC' AND concept_code IN ({codes})""")
print("screening LOINC concepts found in the CDR:", len(CON))
print(CON.to_string(index=False))
ids = ",".join(str(int(x)) for x in CON.concept_id) or "0"
S = q(f"""WITH idx AS (SELECT * FROM UNNEST([{IDX}])),
r AS (
  SELECT person_id, observation_date AS dt FROM `{CDR}`.observation
  WHERE observation_concept_id IN ({ids}) OR observation_source_concept_id IN ({ids})
  UNION ALL
  SELECT person_id, measurement_date AS dt FROM `{CDR}`.measurement
  WHERE measurement_concept_id IN ({ids}) OR measurement_source_concept_id IN ({ids}))
SELECT idx.person_id, idx.d, MAX(IF(r.dt < idx.d, 1, 0)) AS scr_any
FROM idx LEFT JOIN r ON r.person_id = idx.person_id GROUP BY 1, 2""")
try:
    P = q(
        f"""WITH idx AS (SELECT DISTINCT person_id FROM UNNEST([{IDX}]))
    SELECT idx.person_id, COUNT(p.person_id) > 0 AS payer_any
    FROM idx LEFT JOIN `{CDR}`.payer_plan_period p ON p.person_id = idx.person_id GROUP BY 1"""
    )
except Exception as e:  # the table may not be released in this CDR
    print("payer_plan_period not available:", str(e)[:160])
    P = pd.DataFrame({"person_id": ix.person_id.unique(), "payer_any": False})
I = q(f"""WITH idx AS (SELECT * FROM UNNEST([{IDX}]))
SELECT idx.person_id, idx.d, MIN(o.observation_date) AS ins_date
FROM idx LEFT JOIN `{CDR}`.observation o ON o.person_id = idx.person_id
  AND o.observation_source_concept_id IN (43528428, 1585389)
GROUP BY 1, 2""")
T = q(
    f"SELECT concept_id, concept_name, vocabulary_id FROM `{CDR}`.concept WHERE concept_id IN (1585845, 43528428, 1585389)"
)
print("\nsurvey concepts:\n", T.to_string(index=False))

out = ix.copy()
out["d"] = pd.to_datetime(out.d).dt.date
for t in (F, D, Z, S, I):
    t["d"] = pd.to_datetime(t.d).dt.date
    out = out.merge(t, on=["person_id", "d"], how="left")
out = out.merge(P, on="person_id", how="left")
for cname in (
    "pre_adm",
    "q_ip",
    "q_ed24",
    "q_dx",
    "q_icu",
    "death30",
    "z_inc",
    "z59_any",
    "scr_any",
):
    out[cname] = out[cname].fillna(0).astype(int)
out["payer_any"] = out.payer_any.fillna(False).astype(int)
out["ins_after"] = (pd.to_datetime(out.ins_date) > pd.to_datetime(out.d)).astype(int)
out.to_csv(f"/home/jupyter/jno_v26/W_r10_{ARM}.csv", index=False)


def show(x):
    return x if x >= MIN else "<20"


print("\nrows:", len(out), "| persons:", out.person_id.nunique())
for cname in (
    "pre_adm",
    "q_ip",
    "q_ed24",
    "q_dx",
    "q_icu",
    "death30",
    "z_inc",
    "z59_any",
    "scr_any",
    "payer_any",
    "ins_after",
):
    n = int(out[cname].sum())
    print(f"  {cname:10s} rows flagged: {show(n)}")
print("DONE")
