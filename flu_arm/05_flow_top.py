# =====================================================================
# eFigure 1B, top of the influenza flow -- CDR v9 (C2025Q4R6), su_lab_v9
#
# The influenza panel began at 15,043 influenza person-seasons. The senior
# author asked that it begin, like the COVID-19 panel, from the whole All of
# Us repository. This counts, with the index definition of
# 00_flu_feasibility.py (first influenza diagnosis or positive influenza test
# in each season, October 1 to April 30, 2018-19 through 2023-24):
#   1. participants in CDR v9
#   2. participants with >=1 influenza index event in those 6 seasons
#   3. the person-seasons those participants contribute (expected 15,043)
# Laboratory concepts are matched by name as in 00_flu_feasibility.py, but
# parainfluenza, Haemophilus influenzae, and antibody assays are excluded:
# the feasibility script's name match admitted them, and 258 lab-only
# person-seasons it counts (mostly parainfluenza PCR) are absent from the
# extraction's index file (flu_index_v9.pkl, 15,043 rows).
# and, for reference, how many of (2) have condition data and a Basics survey
# record at any date. Aggregates only; counts below 20 print as "<20".
# =====================================================================

import os

import pandas as pd

CDR = os.environ.get("WORKSPACE_CDR")
print("CDR:", CDR)
assert CDR and "C2025Q4R6" in CDR, CDR
POS = "9191,4126681,36032716,36715206,45878745,45881802,45877985,45884084"
SEASONS = [(y, f"{y}-{str(y + 1)[2:]}") for y in range(2018, 2024)]
case = (
    "CASE "
    + " ".join(
        f"WHEN d BETWEEN DATE '{y}-10-01' AND DATE '{y + 1}-04-30' THEN '{s}'"
        for y, s in SEASONS
    )
    + " ELSE NULL END"
)

sql = f"""
WITH
  flu_dx AS (
    SELECT person_id, condition_start_date AS d FROM `{CDR}`.condition_occurrence
    WHERE condition_concept_id IN (SELECT descendant_concept_id FROM `{CDR}`.concept_ancestor
                                   WHERE ancestor_concept_id = 4266367)),
  flu_lab AS (
    SELECT m.person_id, m.measurement_date AS d FROM `{CDR}`.measurement m
    JOIN `{CDR}`.concept c ON c.concept_id = m.measurement_concept_id
    WHERE LOWER(c.concept_name) LIKE '%influenza%' AND m.value_as_concept_id IN ({POS})
      AND LOWER(c.concept_name) NOT LIKE '%parainfluenza%'
      AND LOWER(c.concept_name) NOT LIKE '%haemophilus%'
      AND LOWER(c.concept_name) NOT LIKE '%antibod%'),
  ev AS (SELECT person_id, {case} AS season FROM (SELECT * FROM flu_dx UNION ALL SELECT * FROM flu_lab)),
  ps AS (SELECT DISTINCT person_id, season FROM ev WHERE season IS NOT NULL),
  basics AS (SELECT DISTINCT person_id FROM `{CDR}`.observation WHERE observation_source_concept_id = 1585845),
  ehr AS (SELECT DISTINCT person_id FROM `{CDR}`.condition_occurrence)
SELECT
  (SELECT COUNT(*) FROM `{CDR}`.person) AS n_participants,
  (SELECT COUNT(DISTINCT person_id) FROM ps) AS n_flu_persons,
  (SELECT COUNT(*) FROM ps) AS n_flu_person_seasons,
  (SELECT COUNT(DISTINCT person_id) FROM ps WHERE person_id IN (SELECT person_id FROM basics)
     AND person_id IN (SELECT person_id FROM ehr)) AS n_flu_persons_basics_ehr,
  (SELECT COUNT(*) FROM `{CDR}`.person WHERE person_id IN (SELECT person_id FROM basics)
     AND person_id IN (SELECT person_id FROM ehr)) AS n_basics_ehr
"""
r = pd.read_gbq(sql, dialect="standard", progress_bar_type=None)
bys = pd.read_gbq(
    sql.split("SELECT\n  (SELECT COUNT(*)")[0]
    + "SELECT season, COUNT(*) AS n FROM ps GROUP BY season ORDER BY season",
    dialect="standard",
    progress_bar_type=None,
)
mask = lambda v: "<20" if 0 < v < 20 else f"{v:,}"
for k, v in r.iloc[0].items():
    print(f"{k:28s} {mask(int(v))}")
print(bys.assign(n=bys.n.map(lambda v: mask(int(v)))).to_string(index=False))
print("DONE")
