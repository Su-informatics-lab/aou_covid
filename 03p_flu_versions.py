"""03p_flu_versions.py -- which Basics insurance item each influenza-arm person answered.

Same question as 03p_insurance_versions.py, for the influenza arm (CDR v9): does the
insurance level the influenza cohort labels as not administered correspond to
participants captured only by the original item (1585389) and not by the revised
item (43528428)? Aggregates screened at 20. Run on the su_lab_v9 VM.
"""

import os

import pandas as pd

CDR = os.environ["WORKSPACE_CDR"]
m = pd.read_csv(
    "/home/jupyter/flu/07_matched_cohort.csv", usecols=["person_id", "insurance_type"]
)
p = m.drop_duplicates("person_id")
ids = ",".join(str(int(x)) for x in p.person_id)
f = pd.read_gbq(
    f"""
SELECT person_id,
  MAX(IF(observation_source_concept_id = 1585389, 1, 0)) AS old_item,
  MAX(IF(observation_source_concept_id = 43528428, 1, 0)) AS new_item
FROM `{CDR}`.observation
WHERE observation_source_concept_id IN (1585389, 43528428) AND person_id IN ({ids})
GROUP BY 1""",
    dialect="standard",
    progress_bar_type=None,
)
p = p.merge(f, on="person_id", how="left").fillna({"old_item": 0, "new_item": 0})
t = (
    p.groupby(["insurance_type", "old_item", "new_item"])
    .size()
    .reset_index(name="persons")
)
t["persons"] = t["persons"].where(t["persons"] >= 20)
print("CDR:", CDR, "| persons", len(p))
print(t.to_string())
os.makedirs("/home/jupyter/jno_v25", exist_ok=True)
t.to_csv("/home/jupyter/jno_v25/P_flu_version_by_level.csv", index=False)
print("DONE")
