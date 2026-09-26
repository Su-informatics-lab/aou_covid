"""03z_snomed.py -- structured social findings coded in SNOMED (R10 review: Gottlieb, Hua
Xu personas). The Z-code analysis (eTable 13) searched ICD-10-CM Z55-Z65 only; EHRs can
also carry social findings as SNOMED concepts in the observation or condition tables.

Concepts: standard SNOMED concepts in the Observation or Condition domain whose names
describe economic hardship, food or housing insecurity, homelessness, unemployment, or
transportation barriers (the list printed below is the audit trail). Counts, among
matched participants, those with any such record before the index date, overall and
among those who reported household income below $25 000. Aggregates only; counts below
20 print as "<20".
  ARM=covid python3 03z_snomed.py      (or ARM=flu)
"""

import os

import pandas as pd

ARM = os.environ.get("ARM", "covid")
CDR = os.environ.get("WORKSPACE_CDR")
W = pd.read_csv(
    f"/home/jupyter/jno_v26/W_r10_{ARM}.csv", usecols=["person_id", "d"]
).drop_duplicates()
if ARM == "covid":
    X = pd.read_csv(
        "/home/jupyter/workspace/rw-migration-aou-rw-46c7ae9e/data/covid_sdoh/aou_v7_5domain/04_sdoh.csv",
        usecols=["person_id", "income"],
    )
else:
    X = pd.read_csv(
        "/home/jupyter/flu/07_matched_cohort.csv", usecols=["person_id", "income"]
    ).drop_duplicates("person_id")
low = set(X.person_id[X.income.isin(["less_10k", "10k_25k"])])
IDX = ",".join(
    f"STRUCT({int(r.person_id)} AS person_id, DATE '{r.d}' AS d)"
    for r in W.itertuples()
)
PAT = (
    r"(?i)(financial (insecurity|difficult|hardship|strain|problem)|poverty|low income|insufficient income|"
    r"unable to afford|food insecur|lack of (adequate )?food|homeless|housing (instability|insecur|problem)|"
    r"inadequate housing|unemploy|lack of transportation|transportation insecur)"
)
## names the pattern catches that are not social findings (psychiatric signs, poverty-level
## bands above poverty, resolved problems)
NOT = r"(?i)(speech|thought|delusion|more than 300|201-300|101-200|percentage|solved|declined|discharge from)"


def q(sql):
    return pd.read_gbq(sql, dialect="standard", progress_bar_type=None)


C = q(
    f"""SELECT concept_id, concept_name, domain_id FROM `{CDR}`.concept
WHERE vocabulary_id = 'SNOMED' AND standard_concept = 'S' AND domain_id IN ('Observation', 'Condition')
  AND REGEXP_CONTAINS(concept_name, r'{PAT}') AND NOT REGEXP_CONTAINS(concept_name, r'{NOT}')"""
)
print("SNOMED social-finding concepts matched:", len(C))
print(C.head(60).to_string(index=False))
ids = ",".join(str(int(x)) for x in C.concept_id) or "0"
R = q(f"""WITH idx AS (SELECT * FROM UNNEST([{IDX}])),
r AS (
  SELECT person_id, observation_date AS dt, observation_concept_id AS cid FROM `{CDR}`.observation
  WHERE observation_concept_id IN ({ids})
  UNION ALL
  SELECT person_id, condition_start_date AS dt, condition_concept_id AS cid FROM `{CDR}`.condition_occurrence
  WHERE condition_concept_id IN ({ids}))
SELECT idx.person_id, r.cid, MAX(IF(r.dt < idx.d, 1, 0)) AS any_pre
FROM idx LEFT JOIN r ON r.person_id = idx.person_id GROUP BY 1, 2""")
## persons per concept (before index), concepts with >= 20 persons only
K = R[R.any_pre == 1].groupby("cid").person_id.nunique().sort_values(ascending=False)
K = (
    K[K >= 20]
    .rename("persons")
    .reset_index()
    .merge(C, left_on="cid", right_on="concept_id")
)
print("\nconcepts recorded before index for >= 20 matched persons:")
print(K[["concept_id", "concept_name", "persons"]].to_string(index=False))


def show(x):
    return str(x) if x >= 20 else "<20"


P = R.groupby("person_id").any_pre.max().reset_index()
n_all, k_all = len(P), int(P.any_pre.sum())
L = P[P.person_id.isin(low)]
n_low, k_low = len(L), int(L.any_pre.sum())
print(
    f"\nmatched persons with a SNOMED social finding before index: {show(k_all)} of {n_all}"
    + (f" ({100 * k_all / n_all:.1f}%)" if k_all >= 20 else "")
)
print(
    f"  among those reporting income below $25 000: {show(k_low)} of {n_low}"
    + (f" ({100 * k_low / n_low:.1f}%)" if k_low >= 20 else "")
)

## economic items from the structured screening instruments (food, housing, transportation,
## financial strain, income): the 03z_extract flag also counted physical activity, stress,
## loneliness and interpersonal-violence items, which are not economic
ECON = [
    "88122-7",
    "88123-5",
    "88124-3",
    "76513-1",
    "93033-9",
    "71802-3",
    "93030-5",
    "93031-3",
    "96778-6",
    "63586-2",
]
codes = ",".join(f"'{x}'" for x in ECON)
E = q(f"""WITH idx AS (SELECT * FROM UNNEST([{IDX}])),
c AS (SELECT concept_id FROM `{CDR}`.concept WHERE vocabulary_id = 'LOINC' AND concept_code IN ({codes})),
r AS (
  SELECT person_id, observation_date AS dt FROM `{CDR}`.observation
  WHERE observation_concept_id IN (SELECT concept_id FROM c) OR observation_source_concept_id IN (SELECT concept_id FROM c)
  UNION ALL
  SELECT person_id, measurement_date AS dt FROM `{CDR}`.measurement
  WHERE measurement_concept_id IN (SELECT concept_id FROM c) OR measurement_source_concept_id IN (SELECT concept_id FROM c))
SELECT idx.person_id, MAX(IF(r.dt < idx.d, 1, 0)) AS econ_pre
FROM idx LEFT JOIN r ON r.person_id = idx.person_id GROUP BY 1""")
P = E.groupby("person_id").econ_pre.max().reset_index()
n_all, k_all = len(P), int(P.econ_pre.sum())
L = P[P.person_id.isin(low)]
n_low, k_low = len(L), int(L.econ_pre.sum())
print(
    f"\nmatched persons with an economic screening item before index: {show(k_all)} of {n_all}"
    + (f" ({100 * k_all / n_all:.1f}%)" if k_all >= 20 else "")
)
print(
    f"  among those reporting income below $25 000: {show(k_low)} of {n_low}"
    + (f" ({100 * k_low / n_low:.1f}%)" if k_low >= 20 else "")
)
print("DONE")
