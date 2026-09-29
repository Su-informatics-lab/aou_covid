"""03z_z59.py -- Z59 subcodes among low-income reporters, by era (R10 review: Gottlieb persona).

eTable 13 (01d_zcode_capture.py) counted the whole Z59 block, which mixes housing, food, and
economic codes. This splits it, among matched participants reporting household income below
$25 000, by era, with a record dated before the index date:

  any        any Z59 code
  income     codes specific to income or material hardship: Z59.5 (extreme poverty), Z59.6
             (low income), Z59.7 (insufficient social insurance and welfare support), Z59.86
             (financial insecurity), Z59.87 (material hardship)
  housing    Z59.0x (homelessness), Z59.1 (inadequate housing), Z59.81x (housing instability)
  food       Z59.4x (lack of adequate food; food insecurity)

Codes are read as eTable 13 reads them: from the source concept (what the coder entered) in both
condition_occurrence and observation, because Z codes usually map to the Observation domain and
condition_source_value is not reliably the ICD code. (The z_inc / z59_any flags in
03z_extract.py read condition_source_value and are superseded by this script.)
Counts of 20 or fewer print as "<=20", a count whose complement is 20 or fewer as "masked", and an
all-era total that would reveal the pooled count of the masked era cells as "masked".
  ARM=covid python3 03z_z59.py      (or ARM=flu)
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
    W["era"] = pd.cut(
        W.d,
        [
            pd.Timestamp("2000-01-01"),
            pd.Timestamp("2021-06-30"),
            pd.Timestamp("2021-12-18"),
            pd.Timestamp("2030-01-01"),
        ],
        labels=["1_pre_delta", "2_delta", "3_omicron"],
    ).astype(str)
else:
    X = pd.read_csv(
        "/home/jupyter/flu/07_matched_cohort.csv", usecols=["person_id", "income"]
    ).drop_duplicates("person_id")
    season = W.d.dt.year - (W.d.dt.month < 10)
    W["era"] = pd.cut(
        season, [2017, 2019, 2021, 2023], labels=["1_pre", "2_pandemic", "3_post"]
    ).astype(str)
low = set(X.person_id[X.income.isin(["less_10k", "10k_25k"])])
W = W[W.person_id.isin(low)]
ids = ",".join(str(int(p)) for p in W.person_id.unique())


def q(sql):
    return pd.read_gbq(sql, dialect="standard", progress_bar_type=None)


Z = q(
    f"""
SELECT co.person_id, c.concept_code AS code, co.condition_start_date AS dt
FROM `{CDR}`.condition_occurrence co JOIN `{CDR}`.concept c ON c.concept_id = co.condition_source_concept_id
WHERE c.vocabulary_id = 'ICD10CM' AND c.concept_code LIKE 'Z59%' AND co.person_id IN ({ids})
UNION ALL
SELECT o.person_id, c.concept_code, o.observation_date
FROM `{CDR}`.observation o JOIN `{CDR}`.concept c ON c.concept_id = o.observation_source_concept_id
WHERE c.vocabulary_id = 'ICD10CM' AND c.concept_code LIKE 'Z59%' AND o.person_id IN ({ids})"""
)
Z["dt"] = pd.to_datetime(Z.dt)
M = Z.merge(W, on="person_id")
M = M[M.dt < M.d]
G = {
    "any": r"^Z59",
    "income": r"^Z59\.(5|6|7|86|87)",
    "housing": r"^Z59\.(0|1|81)",
    "food": r"^Z59\.4",
}


def cell(k, n, kp):
    ## R10 Codex: the published policy prohibits counts of 1 to 20, so 20 is masked too, and
    ## a count must also rest on more than 20 distinct participants (influenza rows are
    ## person-seasons)
    if k <= 20 or kp <= 20:
        return "<=20", "masked"
    if n - k <= 20:
        return "masked", "masked"
    return str(k), f"{100 * k / n:.1f}"


rows, raw = [], {}
for e in ["all"] + sorted(W.era.unique()):
    base = W if e == "all" else W[W.era == e]
    key = set(zip(base.person_id, base.d))
    n = len(key)
    for g, pat in G.items():
        hit = M[M.code.str.contains(pat, regex=True)]
        pairs = set(zip(hit.person_id, hit.d)) & key
        k, kp = len(pairs), len({p for p, _ in pairs})
        raw[(e, g)] = (k, n)
        kk, pc = cell(k, n, kp)
        rows.append(
            {
                "arm": ARM,
                "era": e,
                "group": g,
                "n": n if n > 20 else "<=20",
                "k": kk,
                "pct": pc,
            }
        )
o = pd.DataFrame(rows)
## complementary masking: when any era cell is masked, the all-era total minus the shown era
## cells is the pooled count of the masked ones; if that pooled count (or its complement) is
## below 20, the total is masked too (R10b: the earlier rule caught only a single masked cell)
for g in G:
    k_all, n_all = raw[("all", g)]
    eras = [e for e in W.era.unique()]
    shown = [
        e
        for e in eras
        if o[(o.era == e) & (o.group == g)].k.iloc[0] not in ("<=20", "masked")
    ]
    if len(shown) < len(eras):
        k_p = k_all - sum(raw[(e, g)][0] for e in shown)
        n_p = n_all - sum(raw[(e, g)][1] for e in shown)
        if k_p <= 20 or n_p - k_p <= 20:
            o.loc[(o.group == g) & (o.era == "all"), ["k", "pct"]] = "masked"
o.to_csv(f"/home/jupyter/jno_v26/z59_{ARM}.csv", index=False)
print(
    "income < $25 000 reporters (person-index rows); Z59 codes dated before the index date"
)
print(o.to_string(index=False))
print("DONE")
