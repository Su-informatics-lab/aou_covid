"""03v_crude.py -- crude and age-sex-standardized hospitalization by income and
insurance among infected participants (persona review R3p, 2026-09-25).

The paper reports odds ratios within matched strata and one absolute figure (16.2%
of 25,160 infected COVID-19 participants hospitalized). A clinician asks how often
patients in each income band were hospitalized, and whether the absolute gap moved
as severity fell. This is descriptive: the full infected cohort before matching,
observed survey responses (missing kept as its own level), no imputation.

  pct       hospitalized / infected, Wilson 95% CI
  pct_std   directly standardized to the arm's own age-group x sex distribution;
            an age-sex stratum absent from a subgroup is dropped and the
            remaining weights renormalized
  rd_*      risk difference vs the reference band ($35 000-99 999; employer
            insurance), crude and standardized, Wald 95% CI on the crude
Every exported cell has >= 20 hospitalized and >= 20 not hospitalized, counted both
as rows and as distinct participants (influenza rows are person-seasons, and a
participant can contribute more than one; Codex R8); when one
level of a variable is suppressed within an era, the next smallest is suppressed
too, so no suppressed count is recoverable from the era total; when the reference
level is suppressed, no risk difference is exported for that era; and when a
level has a suppressed era cell, a second era cell of that level is suppressed,
so the all-period count cannot be differenced to recover it.

Run on the Workbench:  ARM=covid python3 03v_crude.py   (or ARM=flu, influenza workspace)
"""

import os

import numpy as np
import pandas as pd

ARM = os.environ.get("ARM", "covid")
MIN = 20
if ARM == "covid":
    B = "/home/jupyter/workspace/rw-migration-aou-rw-46c7ae9e/data/covid_sdoh"
    c = pd.read_csv(f"{B}/aou_v7/01_covid_cohort.csv")
    dm = pd.read_csv(f"{B}/aou_v7/02_demographics.csv")
    sd = pd.read_csv(f"{B}/aou_v7_5domain/04_sdoh.csv")
    df = c.merge(dm[["person_id", "sex_at_birth", "age_group"]], on="person_id").merge(
        sd[["person_id", "income", "insurance_type"]], on="person_id"
    )
    assert len(df) == len(c) == 25160, len(df)
    df["hosp"] = (df.severity == 1).astype(int)
    d = pd.to_datetime(df.covid_index_date)
    df["era"] = np.where(
        d < "2021-06-15",
        "1_pre_delta",
        np.where(d < "2021-12-15", "2_delta", "3_omicron"),
    )
    OUT = "/home/jupyter/jno_v26"
else:
    # every eligible person-season that entered matching (9,169; eFigure 1):
    # Treatment = hospitalization phenotype, the others infected and not hospitalized
    df = pd.read_csv("/home/jupyter/flu/flu_prematch.csv")
    assert len(df) == 9169, len(df)
    df["hosp"] = df.Treatment.astype(int)
    df["era"] = df.period
    OUT = "/home/jupyter/jno_v26"
os.makedirs(OUT, exist_ok=True)

INC = {
    "less_10k": "<$10 000",
    "10k_25k": "$10 000-24 999",
    "25k_35k": "$25 000-34 999",
    "35k_100k": "$35 000-99 999",
    "100k_150k": ">=$100 000",
    "150k_200k": ">=$100 000",
    "more_200k": ">=$100 000",
}
df["income_band"] = df.income.map(INC).fillna("Missing")
df["insurance"] = df.insurance_type.fillna("Missing").replace(
    {"Missing": "Not captured by revised item", "Other_None": "Other or none"}
)
df["sex_at_birth"] = df.sex_at_birth.where(
    df.sex_at_birth.isin(["Female", "Male"]), "Other"
)
std_w = df.groupby(["age_group", "sex_at_birth"]).size() / len(df)


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return 100 * (mid - half), 100 * (mid + half)


def std_rate(g):
    r = g.groupby(["age_group", "sex_at_birth"]).hosp.mean()
    w = std_w.reindex(r.index).fillna(0)
    return 100 * float((r * w).sum() / w.sum())


rows = []
for var, ref in [("income_band", "$35 000-99 999"), ("insurance", "Employer")]:
    for era in ["all"] + sorted(df.era.unique()):
        e = df if era == "all" else df[df.era == era]
        refg = e[e[var] == ref]
        pr, nr = refg.hosp.mean(), len(refg)
        sr = std_rate(refg)
        block = []
        for lev, g in e.groupby(var):
            n, k = len(g), int(g.hosp.sum())
            # influenza rows are person-seasons: the threshold applies to people
            kp = g.loc[g.hosp == 1, "person_id"].nunique()
            np_ = g.loc[g.hosp == 0, "person_id"].nunique()
            lo, hi = wilson(k, n)
            p = k / n
            se = np.sqrt(p * (1 - p) / n + pr * (1 - pr) / nr)
            block.append(
                dict(
                    arm=ARM,
                    variable=var,
                    era=era,
                    level=lev,
                    n=n,
                    hosp=k,
                    hosp_persons=kp,
                    nonhosp_persons=np_,
                    pct=100 * p,
                    lo=lo,
                    hi=hi,
                    pct_std=std_rate(g),
                    rd=100 * (p - pr),
                    rd_lo=100 * (p - pr - 1.96 * se),
                    rd_hi=100 * (p - pr + 1.96 * se),
                    rd_std=std_rate(g) - sr,
                )
            )
        b = pd.DataFrame(block)
        bad = (
            (b.hosp < MIN)
            | (b.n - b.hosp < MIN)
            | (b.hosp_persons < MIN)
            | (b.nonhosp_persons < MIN)
        )
        if bad.sum() == 1:  # complementary suppression
            bad[b[~bad].n.idxmin()] = True
        b.loc[
            bad,
            [c_ for c_ in b.columns if c_ not in ("arm", "variable", "era", "level")],
        ] = np.nan
        if bad[
            b.level == ref
        ].any():  # a risk difference would reveal the suppressed reference
            b[["rd", "rd_lo", "rd_hi", "rd_std"]] = np.nan
        b["suppressed"] = bad
        rows.append(b)
o = pd.concat(rows, ignore_index=True)
## Cross-era complementary suppression: a level's all-period count minus its
## published era counts would reveal a suppressed era cell, so in every level with
## a suppressed era cell the smallest other published era cell is suppressed too
## (and, if that cell is the reference, the era's risk differences go with it).
CNT = [
    c_
    for c_ in o.columns
    if c_ not in ("arm", "variable", "era", "level", "suppressed")
]
for (var, lev), g in o[o.era != "all"].groupby(["variable", "level"]):
    if g.suppressed.sum() == 1:
        j = g[~g.suppressed].n.idxmin()
        o.loc[j, CNT] = np.nan
        o.loc[j, "suppressed"] = True
        ref = "$35 000-99 999" if var == "income_band" else "Employer"
        if lev == ref:
            o.loc[
                (o.variable == var) & (o.era == o.loc[j, "era"]),
                ["rd", "rd_lo", "rd_hi", "rd_std"],
            ] = np.nan
## the within-era rule must still hold after the cross-era step
for (var, era), g in o[o.era != "all"].groupby(["variable", "era"]):
    assert g.suppressed.sum() != 1, (var, era)
tot = df.groupby("era").agg(n=("hosp", "size"), hosp=("hosp", "sum")).reset_index()
print("totals by era:\n", tot.to_string(index=False))
o.to_csv(f"{OUT}/crude_{ARM}.csv", index=False)
pd.set_option("display.width", 200)
print(o.round(1).to_string(index=False))
print("DONE")
