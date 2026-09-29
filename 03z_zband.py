"""03z_zband.py -- Z-code capture by the income bands that Figure 2 compares.

Figure 2C and eTable 10 first counted Z codes among participants reporting household income
below $25 000 (the two lowest Basics bands pooled). The senior author asked that the panel use
the same bands as Figure 2A-B, so this counts, among matched participants reporting income below
$10 000 and, for comparison, $35 000 to $99 999 (the reference band), those with a record dated
before the index date of:

  z59        any Z59 code (housing and economic circumstances)
  income     Z59.5 (extreme poverty), Z59.6 (low income), Z59.7 (insufficient social insurance
             and welfare support), Z59.86 (financial insecurity), Z59.87 (material hardship)
  housing    Z59.0x, Z59.1, Z59.81x
  any        any Z55-Z65 code

Codes are read from the source concept in condition_occurrence and observation, as in
01d_zcode_capture.py and 03z_z59.py. Influenza rows are person-seasons. Counts of 20 or fewer
print as "<=20", a count whose complement is 20 or fewer as "masked", and a Z59 subgroup whose
difference from the Z59 count is 20 or fewer as "masked"; a count must also rest on more than 20
distinct participants.
  ARM=covid python3 03z_zband.py      (or ARM=flu)
"""

import os

import pandas as pd

ARM = os.environ.get("ARM", "covid")
CDR = os.environ.get("WORKSPACE_CDR")
W = pd.read_csv(
    f"/home/jupyter/jno_v26/W_r10_{ARM}.csv", usecols=["person_id", "d"]
).drop_duplicates()
W["d"] = pd.to_datetime(W.d)
if ARM == "covid":
    X = pd.read_csv(
        "/home/jupyter/workspace/rw-migration-aou-rw-46c7ae9e/data/covid_sdoh/aou_v7_5domain/04_sdoh.csv",
        usecols=["person_id", "income"],
    )
else:
    X = pd.read_csv(
        "/home/jupyter/flu/07_matched_cohort.csv", usecols=["person_id", "income"]
    ).drop_duplicates("person_id")
BANDS = {"below_10k": ["less_10k"], "35k_to_99k": ["35k_100k"]}
print("income levels present:", sorted(X.income.dropna().unique()))
ids_all = ",".join(str(int(p)) for p in W.person_id.unique())


def q(sql):
    return pd.read_gbq(sql, dialect="standard", progress_bar_type=None)


Z = q(f"""
SELECT co.person_id, c.concept_code AS code, co.condition_start_date AS dt
FROM `{CDR}`.condition_occurrence co JOIN `{CDR}`.concept c ON c.concept_id = co.condition_source_concept_id
WHERE c.vocabulary_id = 'ICD10CM' AND REGEXP_CONTAINS(c.concept_code, r'^Z(5[5-9]|6[0-5])')
  AND co.person_id IN ({ids_all})
UNION ALL
SELECT o.person_id, c.concept_code, o.observation_date
FROM `{CDR}`.observation o JOIN `{CDR}`.concept c ON c.concept_id = o.observation_source_concept_id
WHERE c.vocabulary_id = 'ICD10CM' AND REGEXP_CONTAINS(c.concept_code, r'^Z(5[5-9]|6[0-5])')
  AND o.person_id IN ({ids_all})""")
Z["dt"] = pd.to_datetime(Z.dt)
M = Z.merge(W, on="person_id")
M = M[M.dt < M.d]
G = {
    "z59": r"^Z59",
    "income": r"^Z59\.(5|6|7|86|87)",
    "housing": r"^Z59\.(0|1|81)",
    "any": r"^Z(5[5-9]|6[0-5])",
}


def cell(k, n, kp):
    if k <= 20 or kp <= 20:
        return "<=20", "masked"
    if n - k <= 20:
        return "masked", "masked"
    return str(k), f"{100 * k / n:.1f}"


rows = []
for b, lv in BANDS.items():
    base = W[W.person_id.isin(set(X.person_id[X.income.isin(lv)]))]
    key = set(zip(base.person_id, base.d))
    n, npers = len(key), base.person_id.nunique()
    for g, pat in G.items():
        hit = M[M.code.str.contains(pat, regex=True)]
        pairs = set(zip(hit.person_id, hit.d)) & key
        kk, pc = cell(len(pairs), n, len({p for p, _ in pairs}))
        rows.append(
            {
                "arm": ARM,
                "band": b,
                "group": g,
                "n": n if npers > 20 else "<=20",
                "k": kk,
                "pct": pc,
            }
        )
o = pd.DataFrame(rows)
# A subgroup of Z59 (income, housing) is also masked when its difference from the Z59
# count is 20 or fewer, so that no count of 1 to 20 can be recovered by subtraction.
for b in BANDS:
    z = o[(o.band == b) & (o.group == "z59")].k.iloc[0]
    for g in ("income", "housing"):
        i = o.index[(o.band == b) & (o.group == g)][0]
        if z.isdigit() and o.at[i, "k"].isdigit() and int(z) - int(o.at[i, "k"]) <= 20:
            o.loc[i, ["k", "pct"]] = "masked"
os.makedirs("/home/jupyter/jno_v26", exist_ok=True)
o.to_csv(f"/home/jupyter/jno_v26/zband_{ARM}.csv", index=False)
print(
    "Z codes dated before the index date, by reported income band (matched participants)"
)
print(o.to_string(index=False))
print("DONE")
