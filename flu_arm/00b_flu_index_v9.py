# Influenza index extraction -- CDR v9 (C2025Q4R6), su_lab_v9 workspace.
#
# Recovered 2026-09-29 from the IPython history of the influenza workspace
# (~/.ipython/profile_default/history.sqlite, session 1 started 2026-09-03 19:21 UTC,
# line 8, the last cell to write flu/flu_index_v9.pkl; the file is dated 19:30 UTC).
# This cell was run interactively and was not saved as a script; it is committed here
# verbatim so the source of record for the 15,043 influenza person-seasons is in the repo.
#
# Rule, as run:
#   index event  a condition descending from SNOMED 4266367 "Influenza", or a
#                measurement whose concept name contains "influenza" (not
#                "parainfluenza") with one of 8 positive-result value concepts
#   season       October 1 to April 30, 2018-19 through 2023-24; first event per season
#   restriction  participants with any condition_occurrence record
#   case         inpatient-type visit (9201, 32037, 262, 8717) or an emergency visit (9203)
#                ending on a later calendar day, starting within 14 days of the index
# Not excluded, unlike the laboratory-confirmed sensitivity rule (eMethod 6): measurement
# names for Haemophilus influenzae and antibody assays also contain "influenza".
# Output is person-level and stays on the Workbench.
import os

import pandas as pd

CDR = os.environ["WORKSPACE_CDR"]
STRICT = "9201,32037,262,8717"
ED = "9203"
OP = "9202,581477,38004207,38004250"
POS = "9191,4126681,36032716,36715206,45878745,45881802,45877985,45884084"
S = """CASE
  WHEN d BETWEEN DATE '2018-10-01' AND DATE '2019-04-30' THEN '2018-19'
  WHEN d BETWEEN DATE '2019-10-01' AND DATE '2020-04-30' THEN '2019-20'
  WHEN d BETWEEN DATE '2020-10-01' AND DATE '2021-04-30' THEN '2020-21'
  WHEN d BETWEEN DATE '2021-10-01' AND DATE '2022-04-30' THEN '2021-22'
  WHEN d BETWEEN DATE '2022-10-01' AND DATE '2023-04-30' THEN '2022-23'
  WHEN d BETWEEN DATE '2023-10-01' AND DATE '2024-04-30' THEN '2023-24'
  ELSE 'excluded' END"""
P = """CASE WHEN i.season IN ('2018-19','2019-20') THEN '1_pre'
            WHEN i.season IN ('2020-21','2021-22') THEN '2_pandemic'
            ELSE '3_post' END"""
sql = f"""
WITH flu_dx AS (SELECT co.person_id, co.condition_start_date d FROM `{CDR}`.condition_occurrence co
  WHERE co.condition_concept_id IN (SELECT descendant_concept_id FROM `{CDR}`.concept_ancestor WHERE ancestor_concept_id=4266367)),
flu_lab AS (SELECT m.person_id, m.measurement_date d FROM `{CDR}`.measurement m
  JOIN `{CDR}`.concept c ON c.concept_id=m.measurement_concept_id
  WHERE LOWER(c.concept_name) LIKE '%influenza%'
    AND LOWER(c.concept_name) NOT LIKE '%parainfluenza%'
    AND m.value_as_concept_id IN ({POS})),
allf AS (SELECT * FROM flu_dx UNION ALL SELECT * FROM flu_lab),
sea AS (SELECT person_id, d, {S} season FROM allf),
idx AS (SELECT person_id, season, MIN(d) fdate FROM sea WHERE season!='excluded' GROUP BY 1,2),
bas AS (SELECT DISTINCT person_id FROM `{CDR}`.observation WHERE observation_source_concept_id=1585845),
ehr AS (SELECT DISTINCT person_id FROM `{CDR}`.condition_occurrence),
hosp AS (SELECT DISTINCT i.person_id, i.season FROM idx i
  JOIN `{CDR}`.visit_occurrence vo ON i.person_id=vo.person_id
  WHERE vo.visit_start_date BETWEEN i.fdate AND DATE_ADD(i.fdate, INTERVAL 14 DAY)
   AND (vo.visit_concept_id IN ({STRICT}) OR (vo.visit_concept_id={ED}
        AND DATE_DIFF(COALESCE(vo.visit_end_date,vo.visit_start_date), vo.visit_start_date, DAY)>=1))),
setg AS (SELECT i.person_id, i.season,
    MAX(CASE WHEN vo.visit_concept_id IN ({OP}) THEN 1 ELSE 0 END) op
  FROM idx i LEFT JOIN `{CDR}`.visit_occurrence vo ON i.person_id=vo.person_id
   AND i.fdate BETWEEN vo.visit_start_date AND COALESCE(vo.visit_end_date,vo.visit_start_date)
  GROUP BY 1,2)
SELECT i.person_id, i.season, {P} period,
  CASE WHEN h.person_id IS NOT NULL THEN 1 ELSE 0 END is_case,
  CASE WHEN b.person_id IS NOT NULL THEN 1 ELSE 0 END has_basics,
  IFNULL(s.op,0) idx_outpatient
FROM idx i JOIN ehr e ON i.person_id=e.person_id
LEFT JOIN bas b ON i.person_id=b.person_id
LEFT JOIN hosp h ON i.person_id=h.person_id AND i.season=h.season
LEFT JOIN setg s ON i.person_id=s.person_id AND i.season=s.season"""
d = pd.read_gbq(sql, dialect="standard", progress_bar_type=None)
d.to_pickle("flu/flu_index_v9.pkl")
print("person-seasons:", len(d), " distinct people:", d.person_id.nunique())
