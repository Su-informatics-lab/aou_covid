"""03w_extract.py -- person-level covariates for the R6 expert-review sensitivity
analyses (2026-09-25). Person-level output stays on the VM; only aggregates
screened at 20 are printed.

For every matched participant:
  state      Basics StreetAddress_PIIState (observation_source_concept_id 1585249)
  region     US Census region of that state; "Unknown" if absent
  expansion  state had implemented the ACA Medicaid expansion by January 2021
             (MO and OK implemented July 2021 and are coded non-expansion)
  site       the EHR site (visit_occurrence_ext.src_id) contributing most visits;
             sites with fewer than 50 matched persons pooled as "Other"
  old_ins    the original insurance item (1585389) recoded to the study hierarchy
             (Medicaid > Medicare > Employer > Other_None), two variants for
             "Private": as Employer (A) or as Other_None (B); NA if not answered
Survey timing comes from files already on each VM (COVID-19 04b_sdoh_timing.csv;
influenza basics_date in the cohort file) and is read by 03w_sens.R.

Run on each workspace VM:  ARM=covid python3 03w_extract.py   (or ARM=flu)
"""

import os

import pandas as pd

ARM = os.environ.get("ARM", "covid")
CDR = os.environ["WORKSPACE_CDR"]
q = lambda s: pd.read_gbq(s, dialect="standard", progress_bar_type=None)
MIN = 20
OUT = "/home/jupyter/jno_v26"
os.makedirs(OUT, exist_ok=True)
if ARM == "covid":
    B = "/home/jupyter/workspace/rw-migration-aou-rw-46c7ae9e/data/covid_sdoh/aou_v7"
    ids = pd.read_csv(
        os.path.join(B, "08_regression_base.csv"), usecols=["person_id"]
    ).person_id.unique()
else:
    ids = pd.read_csv(
        "/home/jupyter/flu/07_matched_cohort.csv", usecols=["person_id"]
    ).person_id.unique()
ids = [int(i) for i in ids]
print("ARM", ARM, "| CDR", CDR, "| matched persons", len(ids))
IDL = ",".join(str(i) for i in ids)

REGION = {}
for r, ss in {
    "Northeast": "CT ME MA NH RI VT NJ NY PA",
    "Midwest": "IL IN MI OH WI IA KS MN MO NE ND SD",
    "South": "DE DC FL GA MD NC SC VA WV AL KY MS TN AR LA OK TX",
    "West": "AZ CO ID MT NV NM UT WY AK CA HI OR WA",
}.items():
    for s_ in ss.split():
        REGION[s_] = r
EXPANDED = set(
    "AK AZ AR CA CO CT DE DC HI ID IL IN IA KY LA ME MD MA MI MN MT NE NV NH NJ NM NY ND OH OR PA RI UT VT VA WA WV".split()
)

st = q(
    f"""SELECT person_id, ANY_VALUE(value_source_value) AS v
FROM `{CDR}`.observation WHERE observation_source_concept_id = 1585249 AND person_id IN ({IDL}) GROUP BY 1"""
)
st["state"] = st.v.str.replace("PIIState_", "", regex=False).str.upper()
site = q(
    f"""WITH v AS (
  SELECT vo.person_id, e.src_id, COUNT(*) AS n
  FROM `{CDR}`.visit_occurrence vo JOIN `{CDR}`.visit_occurrence_ext e USING (visit_occurrence_id)
  WHERE vo.person_id IN ({IDL}) GROUP BY 1, 2)
SELECT person_id, ARRAY_AGG(src_id ORDER BY n DESC LIMIT 1)[OFFSET(0)] AS site FROM v GROUP BY 1"""
)
old = q(
    f"""SELECT person_id,
  MAX(IF(value_source_concept_id IN (1585393, 1585397, 1585394), 1, 0)) AS o_medicaid,
  MAX(IF(value_source_concept_id IN (1585391, 1585392), 1, 0)) AS o_medicare,
  MAX(IF(value_source_concept_id = 1585390, 1, 0)) AS o_private,
  MAX(IF(value_source_concept_id IN (1585395, 1585398, 1585399, 1585400), 1, 0)) AS o_other
FROM `{CDR}`.observation WHERE observation_source_concept_id = 1585389 AND person_id IN ({IDL}) GROUP BY 1"""
)
P = pd.DataFrame({"person_id": ids})
P = P.merge(st[["person_id", "state"]], on="person_id", how="left")
P["region"] = P.state.map(REGION).fillna("Unknown")
P["expansion"] = P.state.map(
    lambda s_: (
        "Unknown"
        if pd.isna(s_) or s_ not in REGION
        else ("Yes" if s_ in EXPANDED else "No")
    )
)
P = P.merge(site, on="person_id", how="left")
P["site"] = P.site.fillna("None").astype(str)
big = P.site.value_counts()
P.loc[P.site.isin(big[big < 50].index), "site"] = "Other"
P = P.merge(old, on="person_id", how="left")


def old_type(r, private_as):
    if pd.isna(r.o_medicaid):
        return None
    if r.o_medicaid == 1:
        return "Medicaid"
    if r.o_medicare == 1:
        return "Medicare"
    if r.o_private == 1:
        return private_as
    if r.o_other == 1:
        return "Other_None"
    return None


P["old_ins_A"] = P.apply(lambda r: old_type(r, "Employer"), axis=1)
P["old_ins_B"] = P.apply(lambda r: old_type(r, "Other_None"), axis=1)
P.to_csv(os.path.join(OUT, f"W_person_{ARM}.csv"), index=False)  # VM only

sc = lambda s_: s_.where(s_ >= MIN)
print("\nregion (persons, screened):\n", sc(P.region.value_counts()).to_string())
print("\nexpansion (persons, screened):\n", sc(P.expansion.value_counts()).to_string())
print(
    "\nsites: %d modelled levels (incl Other/None); persons in Other %s, None %s"
    % (
        P.site.nunique(),
        (P.site == "Other").sum() if (P.site == "Other").sum() >= MIN else "<20",
        (P.site == "None").sum() if (P.site == "None").sum() >= MIN else "<20",
    )
)
print("\nold item answered (persons):", int(P.o_medicaid.notna().sum()))
print(
    "\nold_ins_A (persons, screened):\n",
    sc(P.old_ins_A.value_counts(dropna=False)).to_string(),
)
print("DONE")
