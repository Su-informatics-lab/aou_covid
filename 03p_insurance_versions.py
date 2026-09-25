"""03p_insurance_versions.py -- which insurance question each matched participant saw.

All of Us replaced the Basics insurance item "What kind of health insurance or health
care coverage do you have?" (concept 1585389) with "Are you currently covered by any of
the following types of health insurance or health coverage plans?" (43528428), later added
branching so 43528428 is asked only after "Yes" to "Are you covered by health insurance?"
(1332874), and later added the response "Insurance through a current or former employer or
union" (43529120). The support page gives the replacement a repository release date
(10/17/2019) but no participant-level administration dates. This study's ETL reads only
43528428, so a participant who answered only the old item is coded "Missing".

This script establishes, from the data, when each change reached participants, and flags
each matched participant's version. Aggregates are printed and screened at 20; the
person-level flags stay on the VM for the refit in 03p_refit.R.

Run on the COVID-19 workspace VM:  python 03p_insurance_versions.py
"""

import os

import pandas as pd

CDR = os.environ["WORKSPACE_CDR"]
B = "/home/jupyter/workspace/rw-migration-aou-rw-46c7ae9e/data/covid_sdoh/aou_v7"
OUT = "/home/jupyter/jno_v24"
os.makedirs(OUT, exist_ok=True)
q = lambda s: pd.read_gbq(s, dialect="standard", progress_bar_type=None)
MIN_CELL = 20


def screen(df, cols):
    for c in cols:
        df[c] = df[c].where(df[c] >= MIN_CELL)
    return df


print("CDR:", CDR)
g = q(f"""
SELECT
  (SELECT MIN(observation_date) FROM `{CDR}`.observation
     WHERE observation_source_concept_id = 43528428 AND value_source_concept_id = 43529120) AS first_employer_option,
  (SELECT MIN(observation_date) FROM `{CDR}`.observation WHERE observation_source_concept_id = 43528428) AS first_new_item,
  (SELECT MAX(observation_date) FROM `{CDR}`.observation WHERE observation_source_concept_id = 1585389) AS last_old_item,
  (SELECT MIN(observation_date) FROM `{CDR}`.observation WHERE observation_source_concept_id = 1585389) AS first_old_item
""")
print("\n== when each version reached participants (whole CDR) ==\n", g.T)

#  Branching: before it, people who said they had no coverage still saw 43528428.
v = q(
    f"""
SELECT value_source_concept_id AS v, ANY_VALUE(value_source_value) AS label, COUNT(DISTINCT person_id) AS n
FROM `{CDR}`.observation WHERE observation_source_concept_id = 1332874 GROUP BY 1 ORDER BY n DESC"""
)
print("\n== responses to 1332874 (covered by any insurance?) ==\n", v)
br = q(f"""
WITH cov AS (SELECT person_id, value_source_concept_id AS cv FROM `{CDR}`.observation WHERE observation_source_concept_id = 1332874),
     nw AS (SELECT person_id, MIN(observation_date) AS d FROM `{CDR}`.observation WHERE observation_source_concept_id = 43528428 GROUP BY 1)
SELECT FORMAT_DATE('%Y-%m', nw.d) AS month, cov.cv, COUNT(DISTINCT nw.person_id) AS n_new_item
FROM nw JOIN cov USING (person_id) GROUP BY 1, 2 ORDER BY 1, 2""")
br = screen(br, ["n_new_item"])
br.to_csv(os.path.join(OUT, "P_branching_by_month.csv"), index=False)
print(
    "\n== 43528428 respondents by month and by their 1332874 answer (screened) ==\n",
    br.to_string(),
)

#  Employer option: monthly share of 43528428 respondents choosing it.
eo = q(
    f"""
SELECT FORMAT_DATE('%Y-%m', observation_date) AS month,
       COUNT(DISTINCT person_id) AS n_new_item,
       COUNT(DISTINCT IF(value_source_concept_id = 43529120, person_id, NULL)) AS n_employer
FROM `{CDR}`.observation WHERE observation_source_concept_id = 43528428 GROUP BY 1 ORDER BY 1"""
)
eo = screen(eo, ["n_new_item", "n_employer"])
eo.to_csv(os.path.join(OUT, "P_employer_option_by_month.csv"), index=False)
print("\n== employer option uptake by month (screened) ==\n", eo.to_string())

#  Person-level flags for the matched cohort (stay on the VM)
m = pd.read_csv(
    os.path.join(B, "08_regression_base.csv"), usecols=["person_id"]
).drop_duplicates()
f = q(
    f"""
SELECT person_id,
  MAX(IF(observation_source_concept_id = 1585389, 1, 0)) AS old_item,
  MAX(IF(observation_source_concept_id = 43528428, 1, 0)) AS new_item,
  MAX(IF(observation_source_concept_id = 43528428 AND value_source_concept_id = 43529120, 1, 0)) AS chose_employer,
  MIN(IF(observation_source_concept_id = 1585389, observation_date, NULL)) AS old_date,
  MIN(IF(observation_source_concept_id = 43528428, observation_date, NULL)) AS new_date
FROM `{CDR}`.observation WHERE observation_source_concept_id IN (1585389, 43528428) GROUP BY 1"""
)
f = m.merge(f, on="person_id", how="left").fillna(
    {"old_item": 0, "new_item": 0, "chose_employer": 0}
)
f.to_csv(os.path.join(OUT, "P_person_version_flags.csv"), index=False)  # VM only
tab = f.groupby(["old_item", "new_item"]).size().reset_index(name="persons")
print(
    "\n== matched persons by version answered (screened) ==\n",
    screen(tab, ["persons"]).to_string(),
)

#  What the old item says for the people currently coded Missing
ov = q(f"""
SELECT value_source_concept_id AS v, ANY_VALUE(value_source_value) AS label, COUNT(DISTINCT person_id) AS n
FROM `{CDR}`.observation
WHERE observation_source_concept_id = 1585389
  AND person_id IN UNNEST({f.loc[(f.old_item == 1) & (f.new_item == 0), 'person_id'].astype(int).tolist()})
GROUP BY 1 ORDER BY n DESC""")
ov = screen(ov, ["n"])
ov.to_csv(os.path.join(OUT, "P_old_item_responses.csv"), index=False)
print(
    "\n== old-item responses among matched persons coded Missing (screened) ==\n",
    ov.to_string(),
)
g.to_csv(os.path.join(OUT, "P_version_dates.csv"), index=False)
print("\nDONE")
