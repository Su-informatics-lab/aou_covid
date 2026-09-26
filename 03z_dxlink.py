"""03z_dxlink.py -- is the diagnosis restriction a data-capture artifact? (R10, Hua Xu persona)

03z_extract.py flags a case's qualifying visit as diagnosis-bearing (q_dx) only when a COVID-19,
influenza, or respiratory condition row is linked to that visit by visit_occurrence_id. Under
ICD-10-CM guidance a confirmed infection is coded even when the admission is incidental, so a
low q_dx share can also mean that the site sent no linked diagnoses at all. For every matched
row this adds:

  link_any   the qualifying visit has >= 1 linked condition row of any kind
  dx_win     a COVID-19/influenza or respiratory condition dated index - 3 to index + 30 days,
             linked to any visit or to none
  inf_win    as dx_win, the infection itself only (COVID-19: descendants of 37311061 or U07.1;
             influenza: descendants of 4266367 or J09-J11)

and writes them next to W_r10_<arm>.csv as W_r10b_<arm>.csv. Aggregates only are printed.
  ARM=covid python3 03z_dxlink.py      (or ARM=flu)
"""

import os

import pandas as pd

ARM = os.environ.get("ARM", "covid")
CDR = os.environ.get("WORKSPACE_CDR")
W = pd.read_csv(f"/home/jupyter/jno_v26/W_r10_{ARM}.csv")
W["d"] = pd.to_datetime(W.d).dt.strftime("%Y-%m-%d")
INF = "37311061" if ARM == "covid" else "4266367"
SRC = (
    "co.condition_source_value LIKE 'U07.1%'"
    if ARM == "covid"
    else "REGEXP_CONTAINS(co.condition_source_value, r'^J(09|10|11)')"
)
IDX = ",".join(
    f"STRUCT({int(r.person_id)} AS person_id, DATE '{r.d}' AS d)"
    for r in W[["person_id", "d"]].drop_duplicates().itertuples()
)
IP, ED = "9201,32037,262,8717", "9203"


def q(sql):
    return pd.read_gbq(sql, dialect="standard", progress_bar_type=None)


## qualifying visits (same rule as 03z_extract.py) and whether any condition row links to them
V = q(f"""WITH idx AS (SELECT * FROM UNNEST([{IDX}]))
SELECT idx.person_id, idx.d, vo.visit_occurrence_id, vo.visit_concept_id,
       vo.visit_start_date AS vs, COALESCE(vo.visit_end_date, vo.visit_start_date) AS ve
FROM idx JOIN `{CDR}`.visit_occurrence vo ON vo.person_id = idx.person_id
WHERE vo.visit_start_date BETWEEN idx.d AND DATE_ADD(idx.d, INTERVAL 14 DAY)
  AND vo.visit_concept_id IN ({IP},{ED})""")
V["vs"], V["ve"] = pd.to_datetime(V.vs), pd.to_datetime(V.ve)
V = V[
    V.visit_concept_id.isin([int(x) for x in IP.split(",")])
    | ((V.ve - V.vs).dt.days >= 1)
]
ids = ",".join(str(int(x)) for x in V.visit_occurrence_id.unique()) or "0"
L = q(f"""SELECT DISTINCT visit_occurrence_id FROM `{CDR}`.condition_occurrence
WHERE visit_occurrence_id IN ({ids})""")
V["link"] = V.visit_occurrence_id.isin(set(L.visit_occurrence_id))
LK = (
    V.groupby(["person_id", "d"])
    .link.any()
    .astype(int)
    .rename("link_any")
    .reset_index()
)

## diagnoses in the window, with or without visit linkage
DX = q(f"""WITH idx AS (SELECT * FROM UNNEST([{IDX}])),
rc AS (SELECT descendant_concept_id AS cid FROM `{CDR}`.concept_ancestor WHERE ancestor_concept_id IN (320136, {INF})),
ic AS (SELECT descendant_concept_id AS cid FROM `{CDR}`.concept_ancestor WHERE ancestor_concept_id = {INF})
SELECT idx.person_id, idx.d,
  MAX(IF(co.condition_concept_id IN (SELECT cid FROM rc) OR co.condition_source_value LIKE 'J%'
         OR co.condition_source_value LIKE 'U07.1%', 1, 0)) AS dx_win,
  MAX(IF(co.condition_concept_id IN (SELECT cid FROM ic) OR {SRC}, 1, 0)) AS inf_win
FROM idx JOIN `{CDR}`.condition_occurrence co ON co.person_id = idx.person_id
WHERE co.condition_start_date BETWEEN DATE_SUB(idx.d, INTERVAL 3 DAY) AND DATE_ADD(idx.d, INTERVAL 30 DAY)
GROUP BY 1, 2""")

for t in (LK, DX):
    t["d"] = pd.to_datetime(t.d).dt.strftime("%Y-%m-%d")
out = W.merge(LK, on=["person_id", "d"], how="left").merge(
    DX, on=["person_id", "d"], how="left"
)
for c in ("link_any", "dx_win", "inf_win"):
    out[c] = out[c].fillna(0).astype(int)
out.to_csv(f"/home/jupyter/jno_v26/W_r10b_{ARM}.csv", index=False)
qual = out.q_ip.eq(1) | out.q_los.notna()
print("rows:", len(out), "| rows with a qualifying visit:", int(qual.sum()))
for c in ("link_any", "dx_win", "inf_win"):
    n = int(out.loc[qual, c].sum())
    print(f"  {c:9s} among rows with a qualifying visit: {n if n >= 20 else '<20'}")
print("DONE")
