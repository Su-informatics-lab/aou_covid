"""03w_sitepre.py -- EHR site from visits BEFORE the index date (R7 review).

03w_extract.py took each participant's predominant EHR site over all visits, which
includes the index admission and later care, so the covariate was partly an outcome.
This adds site_pre: the src_id contributing most visits that START before the index
date (COVID-19: the participant's covid_index_date; influenza: the earliest
flu_index_date). Sites with fewer than 50 matched persons are pooled as "Other";
participants with no earlier visit are "None". Person-level output stays on the VM
(W_person_<arm>.csv gains the column); only screened aggregates are printed.

Run on each VM after 03w_extract.py:  ARM=covid python3 03w_sitepre.py
"""

import os

import pandas as pd

ARM = os.environ.get("ARM", "covid")
CDR = os.environ["WORKSPACE_CDR"]
MIN = 20
WP = f"/home/jupyter/jno_v26/W_person_{ARM}.csv"
P = pd.read_csv(WP)
if ARM == "covid":
    B = "/home/jupyter/workspace/rw-migration-aou-rw-46c7ae9e/data/covid_sdoh/aou_v7"
    ix = pd.read_csv(
        os.path.join(B, "01_covid_cohort.csv"),
        usecols=["person_id", "covid_index_date"],
    )
    ix = ix.rename(columns={"covid_index_date": "d"})
else:
    m = pd.read_csv(
        "/home/jupyter/flu/07_matched_cohort.csv",
        usecols=["person_id", "flu_index_date"],
    )
    ix = (
        m.groupby("person_id")
        .flu_index_date.min()
        .reset_index()
        .rename(columns={"flu_index_date": "d"})
    )
ix = ix[ix.person_id.isin(P.person_id)]
ix["d"] = pd.to_datetime(ix.d).dt.strftime("%Y-%m-%d")
assert ix.person_id.nunique() == P.person_id.nunique(), (
    ix.person_id.nunique(),
    P.person_id.nunique(),
)
structs = ",".join(
    f"STRUCT({int(r.person_id)} AS person_id, DATE '{r.d}' AS d)"
    for r in ix.itertuples()
)
sql = f"""WITH idx AS (SELECT * FROM UNNEST([{structs}])),
v AS (SELECT vo.person_id, e.src_id, COUNT(*) AS n
      FROM `{CDR}`.visit_occurrence vo JOIN `{CDR}`.visit_occurrence_ext e USING (visit_occurrence_id)
      JOIN idx ON vo.person_id = idx.person_id
      WHERE vo.visit_start_date < idx.d GROUP BY 1, 2)
SELECT person_id, ARRAY_AGG(src_id ORDER BY n DESC, src_id LIMIT 1)[OFFSET(0)] AS site_pre FROM v GROUP BY 1"""
print("query bytes:", len(sql))
s = pd.read_gbq(sql, dialect="standard", progress_bar_type=None)
P = P.drop(columns=[c for c in ["site_pre"] if c in P.columns]).merge(
    s, on="person_id", how="left"
)
P["site_pre"] = P.site_pre.fillna("None").astype(str)
big = P.site_pre.value_counts()
P.loc[P.site_pre.isin(big[big < 50].index), "site_pre"] = "Other"
P.to_csv(WP, index=False)
n_none = (P.site_pre == "None").sum()
n_other = (P.site_pre == "Other").sum()
same = (P.site_pre == P.site.astype(str)).mean()
print(
    "site_pre levels:",
    P.site_pre.nunique(),
    "| Other:",
    n_other if n_other >= MIN else "<20",
    "| None (no earlier visit):",
    n_none if n_none >= MIN else "<20",
    "| agrees with all-visit site: %.3f" % same,
)
print("DONE")
