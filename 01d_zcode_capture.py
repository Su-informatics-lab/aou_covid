#!/usr/bin/env python3
"""
01d_zcode_capture.py — what the record would have said about the people whose
survey answers carry the result.

Runs on the All of Us Researcher Workbench (Controlled Tier). Nothing
person-level leaves it; every table written here is aggregate and every cell
below 20 is suppressed before it is written.

Why this exists. The paper's case for survey-measured social determinants rests
on a claim borrowed from the literature: ICD-10-CM Z55-Z65 codes, the way a
health system records social risk, are entered for a very small share of
encounters. Borrowing it is weaker than measuring it, and we can measure it on
the same participants whose survey answers produce the result. The question is
not how often Z codes appear in general. It is: of the participants whose survey
says low income, or unemployed, or unstable housing, how many does the record
say anything about?

That number is the measurement rationale for Test 1, stated on our own cohort
instead of cited.

Usage: python 01d_zcode_capture.py v7
Output: results/aou_{version}/10_zcode_capture*.csv
"""

import os
import sys

import pandas as pd

if len(sys.argv) < 2 or sys.argv[1] not in ("v7", "v8", "v9"):
    print("Usage: python 01d_zcode_capture.py [v7|v8|v9]")
    sys.exit(1)
VERSION = sys.argv[1]

CDR = os.environ["WORKSPACE_CDR"]
RESULTS = f"results/aou_{VERSION}"
MIN_CELL = 20  # All of Us: no published count below 20, and none derivable

#  The Z-code blocks, with what each is for. Z58 (physical environment) is
#  included for completeness; it is rarely populated.
BLOCKS = {
    "Z55": "education and literacy",
    "Z56": "employment and unemployment",
    "Z57": "occupational exposure",
    "Z58": "physical environment",
    "Z59": "housing and economic circumstances",
    "Z60": "social environment",
    "Z62": "upbringing",
    "Z63": "primary support group and family",
    "Z64": "certain psychosocial circumstances",
    "Z65": "other psychosocial circumstances",
}

cohort = pd.read_csv(os.path.join(RESULTS, "01_covid_cohort.csv"))
sdoh = pd.read_csv(os.path.join(RESULTS, "04_sdoh.csv"))
matched = pd.read_csv(os.path.join(RESULTS, "08_regression_base.csv"))
people = sorted(set(matched.person_id))
print(f"matched cohort: {len(matched):,} observations, {len(people):,} people")

ids = ",".join(str(p) for p in people)
like = " OR ".join(f"c.concept_code LIKE '{b}%'" for b in BLOCKS)

#  Source concept, not standard concept: the Z code is what the coder entered,
#  and the standard mapping scatters these across SNOMED findings and
#  observations. condition_occurrence and observation are both searched because
#  sites file these in either.
SQL = f"""
WITH z AS (
  SELECT co.person_id,
         SUBSTR(c.concept_code, 1, 3) AS block,
         co.condition_start_date      AS evt_date
  FROM `{CDR}`.condition_occurrence co
  JOIN `{CDR}`.concept c ON c.concept_id = co.condition_source_concept_id
  WHERE c.vocabulary_id = 'ICD10CM' AND ({like})
    AND co.person_id IN ({ids})
  UNION ALL
  SELECT o.person_id,
         SUBSTR(c.concept_code, 1, 3) AS block,
         o.observation_date           AS evt_date
  FROM `{CDR}`.observation o
  JOIN `{CDR}`.concept c ON c.concept_id = o.observation_source_concept_id
  WHERE c.vocabulary_id = 'ICD10CM' AND ({like})
    AND o.person_id IN ({ids})
)
SELECT person_id, block, MIN(evt_date) AS first_date, COUNT(*) AS n_records
FROM z GROUP BY person_id, block
"""
print("querying Z55-Z65 ...")
z = pd.read_gbq(SQL, dialect="standard")
print(f"  {len(z):,} person-block rows, {z.person_id.nunique():,} distinct people")

idx = cohort[["person_id", "covid_index_date"]].copy()
idx["covid_index_date"] = pd.to_datetime(idx["covid_index_date"])
z = z.merge(idx, on="person_id", how="left")
z["first_date"] = pd.to_datetime(z["first_date"])
z["pre_index"] = z["first_date"] < z["covid_index_date"]
zpre = z[z.pre_index]

n = len(people)


def suppress(df, col):
    """All of Us forbids publishing a count below 20, or a set from which one is
    derivable. A suppressed cell keeps its label and loses its number."""
    out = df.copy()
    small = out[col] < MIN_CELL
    out.loc[small, col] = pd.NA
    out["suppressed"] = small.values
    return out


rows = [
    {
        "block": b,
        "meaning": BLOCKS[b],
        "people_with_code_pre_index": int(zpre[zpre.block == b].person_id.nunique()),
    }
    for b in BLOCKS
]
per_block = pd.DataFrame(rows)
per_block["pct_of_cohort"] = (per_block.people_with_code_pre_index / n * 100).round(2)
per_block.loc[per_block.people_with_code_pre_index < MIN_CELL, "pct_of_cohort"] = pd.NA
per_block = suppress(per_block, "people_with_code_pre_index")
per_block.to_csv(os.path.join(RESULTS, "10_zcode_capture_by_block.csv"), index=False)
print("\nZ-code capture before the index date, by block:")
print(per_block.to_string(index=False))

any_z = zpre.person_id.nunique()
print(f"\nany Z55-Z65 before index: {any_z:,} of {n:,} ({any_z / n * 100:.2f}%)")

#  The comparison that matters: the survey says one thing, does the record say
#  anything at all?
PAIRS = [
    (
        "income",
        lambda s: s.isin(["less_10k", "10k_25k"]),
        ["Z59"],
        "income below $25,000",
    ),
    ("employment", lambda s: s.eq("Unemployed"), ["Z56"], "unemployed"),
    ("housing_stability", lambda s: s.eq("Unstable"), ["Z59"], "unstable housing"),
    ("education", lambda s: s.eq("Below_GED"), ["Z55"], "education below GED"),
]
sd = sdoh[sdoh.person_id.isin(people)].set_index("person_id")
out = []
for col, pred, blocks, label in PAIRS:
    if col not in sd.columns:
        print(f"  ! {col} not in 04_sdoh.csv, skipped")
        continue
    grp = sd.index[pred(sd[col].astype(str))]
    hit_block = zpre[zpre.block.isin(blocks)].person_id.unique()
    hit_any = zpre.person_id.unique()
    out.append(
        {
            "survey_answer": label,
            "people": len(grp),
            "with_matching_z_block": int(pd.Index(grp).isin(hit_block).sum()),
            "with_any_z_code": int(pd.Index(grp).isin(hit_any).sum()),
            "z_blocks_searched": "+".join(blocks),
        }
    )
cap = pd.DataFrame(out)
for c in ("people", "with_matching_z_block", "with_any_z_code"):
    cap[c + "_pct"] = (cap[c] / cap["people"] * 100).round(2)
    cap.loc[cap[c] < MIN_CELL, [c, c + "_pct"]] = pd.NA
cap.to_csv(os.path.join(RESULTS, "10_zcode_capture_vs_survey.csv"), index=False)
print("\nwhat the record says about the people the survey identifies:")
print(cap.to_string(index=False))
print("\nDONE. Read the two CSVs off the platform and record them locally;")
print("do not sync them into the repository without screening.")
