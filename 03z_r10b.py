"""03z_r10b.py -- second-round R10 checks (Gottlieb, Adler-Milstein, Hua Xu personas).

For every matched row (COVID-19: person and index date; influenza: person-season) this adds,
next to W_r10_<arm>.csv, as W_r10c_<arm>.csv:

  q_dx2     infection or respiratory diagnosis linked to a qualifying visit, standard
            concepts only (descendants of SNOMED 320136 or of the infection concept); the
            condition_source_value clauses of 03z_extract.py are dropped
  dx_win2   the same diagnosis dated index - 3 to + 30 days, on any visit or none
  inf_win2  as dx_win2, the infection concept only
  ed24b     an ED visit in the window lasting >= 24 h by its date-times; missing when either
            date-time is null or both are exactly midnight (a date loaded without a time),
            instead of counting such visits as short (null) or as 24 h (midnight)
  lab_idx   a positive laboratory result for the infection on the index date (COVID-19: the
            65 SARS-CoV-2 concepts of 01_aou_etl.py; influenza: a measurement whose concept
            name contains "influenza" but not "influenzae" and does not name an antibody)
  (influenza only) flu_dx_idx, flu_good_idx, flu_bad_idx: influenza diagnosis, virus test,
            or only an H. influenzae / antibody result on the index date
  scr_ehr, scr_oth  an economic screening item (LOINC; food, housing, transportation,
            financial strain, income) before the index date from an EHR site vs from any
            other source (survey or portal), by the _ext table src_id

Printed aggregates (counts below 20 as "<20"; complements below 20 masked):
  the influenza index audit; ED >= 24 h computability; diagnosis linkage among cases by
  insurance and era, crude and standardized to the site mix of the cases (site = predominant
  EHR site before the index date, 03w_sitepre.py); the timing of unlinked visits relative to
  the repository cutoff; screening provenance.
  ARM=covid python3 03z_r10b.py      (or ARM=flu)
"""

import os

import pandas as pd

ARM = os.environ.get("ARM", "covid")
CDR = os.environ.get("WORKSPACE_CDR")
MIN = 20
W = pd.read_csv(f"/home/jupyter/jno_v26/W_r10_{ARM}.csv")
Wb = pd.read_csv(
    f"/home/jupyter/jno_v26/W_r10b_{ARM}.csv", usecols=["person_id", "d", "link_any"]
)
W = W.merge(Wb, on=["person_id", "d"], how="left")
W["d"] = pd.to_datetime(W.d)
WP = pd.read_csv(
    f"/home/jupyter/jno_v26/W_person_{ARM}.csv", usecols=["person_id", "site_pre"]
)
XP = (
    "/home/jupyter/workspace/rw-migration-aou-rw-46c7ae9e/data/covid_sdoh/aou_v7_5domain/04_sdoh.csv"
    if ARM == "covid"
    else "/home/jupyter/flu/07_matched_cohort.csv"
)
ICOL = [c for c in pd.read_csv(XP, nrows=0).columns if "insur" in c.lower()][0]
X = (
    pd.read_csv(XP, usecols=["person_id", ICOL])
    .drop_duplicates("person_id")
    .rename(columns={ICOL: "insurance_type"})
)
if ARM == "covid":
    INF, CUTOFF = "37311061", pd.Timestamp("2022-07-01")
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
    LAB = """measurement_concept_id IN (586520,586523,586525,586526,586529,706157,706159,715261,715272,
      723470,723472,757678,36032061,36032174,36032258,36661371,586518,586524,706154,706175,723464,723467,
      723478,36031453,586516,706158,706160,706163,706171,706172,715260,723469,36031213,36661377,586528,
      706161,706165,706167,723463,723468,723471,757677,36031238,36031944,586519,706166,706169,706173,
      723465,723476,757685,36031506,706155,706156,706170,723466,36031652,36661370,706168,706174,715262,
      723477,36032419,36661378,37310257)"""
else:
    INF, CUTOFF = "4266367", pd.Timestamp("2025-01-01")
    season = W.d.dt.year - (W.d.dt.month < 10)
    W["era"] = pd.cut(
        season, [2017, 2019, 2021, 2023], labels=["1_pre", "2_pandemic", "3_post"]
    ).astype(str)
POS = "9191,4126681,36032716,36715206,45878745,45881802,45877985,45884084"
IP, ED = "9201,32037,262,8717", "9203"
ds = W.d.dt.strftime("%Y-%m-%d")
IDX = ",".join(
    f"STRUCT({int(p)} AS person_id, DATE '{x}' AS d)" for p, x in zip(W.person_id, ds)
)
KEY = ["person_id", "d"]


def q(sql):
    return pd.read_gbq(sql, dialect="standard", progress_bar_type=None)


def show(k):
    return str(k) if k >= MIN else "<20"


def pct(k, n):
    return f"{100 * k / n:.1f}%" if k >= MIN and n - k >= MIN else "masked"


def dkey(t):
    t["d"] = pd.to_datetime(t.d)
    return t


## qualifying visits and ED date-times
V = dkey(q(f"""WITH idx AS (SELECT * FROM UNNEST([{IDX}]))
SELECT idx.person_id, idx.d, vo.visit_occurrence_id, vo.visit_concept_id,
       vo.visit_start_date AS vs, COALESCE(vo.visit_end_date, vo.visit_start_date) AS ve,
       vo.visit_start_datetime AS vst, vo.visit_end_datetime AS vet
FROM idx JOIN `{CDR}`.visit_occurrence vo ON vo.person_id = idx.person_id
WHERE vo.visit_start_date BETWEEN idx.d AND DATE_ADD(idx.d, INTERVAL 14 DAY)
  AND vo.visit_concept_id IN ({IP},{ED})"""))
V["vs"], V["ve"] = pd.to_datetime(V.vs), pd.to_datetime(V.ve)
ipset = [int(x) for x in IP.split(",")]
V["qual"] = V.visit_concept_id.isin(ipset) | (
    (V.visit_concept_id == int(ED)) & ((V.ve - V.vs).dt.days >= 1)
)
st, en = pd.to_datetime(V.vst, utc=True), pd.to_datetime(V.vet, utc=True)
midnight = (
    (st.dt.hour == 0) & (st.dt.minute == 0) & (en.dt.hour == 0) & (en.dt.minute == 0)
)
bad = st.isna() | en.isna() | midnight
hrs = (en - st).dt.total_seconds() / 3600
isED = V.visit_concept_id == int(ED)
V["ed24"] = pd.Series(pd.NA, index=V.index, dtype="Int64")
V.loc[isED & ~bad, "ed24"] = (hrs[isED & ~bad] >= 24).astype(int)
E = V[isED].groupby(KEY).agg(ed24b=("ed24", "max"), ed_n=("ed24", "size")).reset_index()

## diagnoses, standard concepts only
vids = (
    ",".join(str(int(x)) for x in V.loc[V.qual, "visit_occurrence_id"].unique()) or "0"
)
D1 = q(
    f"""WITH rc AS (SELECT descendant_concept_id AS cid FROM `{CDR}`.concept_ancestor
  WHERE ancestor_concept_id IN (320136, {INF}))
SELECT DISTINCT visit_occurrence_id FROM `{CDR}`.condition_occurrence
WHERE visit_occurrence_id IN ({vids}) AND condition_concept_id IN (SELECT cid FROM rc)"""
)
V["dx2"] = V.visit_occurrence_id.isin(set(D1.visit_occurrence_id)) & V.qual
QD = V.groupby(KEY).dx2.any().astype(int).rename("q_dx2").reset_index()
DW = dkey(q(f"""WITH idx AS (SELECT * FROM UNNEST([{IDX}])),
rc AS (SELECT descendant_concept_id AS cid FROM `{CDR}`.concept_ancestor WHERE ancestor_concept_id IN (320136, {INF})),
ic AS (SELECT descendant_concept_id AS cid FROM `{CDR}`.concept_ancestor WHERE ancestor_concept_id = {INF})
SELECT idx.person_id, idx.d, MAX(1) AS dx_win2,
  MAX(IF(co.condition_concept_id IN (SELECT cid FROM ic), 1, 0)) AS inf_win2
FROM idx JOIN `{CDR}`.condition_occurrence co ON co.person_id = idx.person_id
WHERE co.condition_start_date BETWEEN DATE_SUB(idx.d, INTERVAL 3 DAY) AND DATE_ADD(idx.d, INTERVAL 30 DAY)
  AND co.condition_concept_id IN (SELECT cid FROM rc)
GROUP BY 1, 2"""))

## laboratory index
if ARM == "covid":
    LB = dkey(q(f"""WITH idx AS (SELECT * FROM UNNEST([{IDX}]))
SELECT DISTINCT idx.person_id, idx.d, 1 AS lab_idx
FROM idx JOIN `{CDR}`.measurement m ON m.person_id = idx.person_id AND m.measurement_date = idx.d
WHERE {LAB} AND m.value_as_concept_id IN ({POS})"""))
else:
    LB = dkey(q(f"""WITH idx AS (SELECT * FROM UNNEST([{IDX}])),
m AS (
  SELECT idx.person_id, idx.d, LOWER(c.concept_name) AS nm
  FROM idx JOIN `{CDR}`.measurement m ON m.person_id = idx.person_id AND m.measurement_date = idx.d
  JOIN `{CDR}`.concept c ON c.concept_id = m.measurement_concept_id
  WHERE LOWER(c.concept_name) LIKE '%influenza%' AND m.value_as_concept_id IN ({POS})),
f AS (
  SELECT DISTINCT idx.person_id, idx.d FROM idx JOIN `{CDR}`.condition_occurrence co
    ON co.person_id = idx.person_id AND co.condition_start_date = idx.d
  WHERE co.condition_concept_id IN (SELECT descendant_concept_id FROM `{CDR}`.concept_ancestor
                                    WHERE ancestor_concept_id = {INF}))
SELECT idx.person_id, idx.d,
  IF(f.person_id IS NULL, 0, 1) AS flu_dx_idx,
  COALESCE(MAX(IF(NOT REGEXP_CONTAINS(m.nm, r'influenzae|antibod|\\bab\\b|igg|igm|titer'), 1, 0)), 0) AS flu_good_idx,
  COALESCE(MAX(IF(REGEXP_CONTAINS(m.nm, r'influenzae|antibod|\\bab\\b|igg|igm|titer'), 1, 0)), 0) AS flu_bad_idx
FROM idx LEFT JOIN m ON m.person_id = idx.person_id AND m.d = idx.d
LEFT JOIN f ON f.person_id = idx.person_id AND f.d = idx.d
GROUP BY 1, 2, 3"""))
    LB["lab_idx"] = LB.flu_good_idx

## economic screening items by source
ECON = "'88122-7','88123-5','88124-3','76513-1','93033-9','71802-3','93030-5','93031-3','96778-6','63586-2'"
SC = dkey(q(f"""WITH idx AS (SELECT * FROM UNNEST([{IDX}])),
c AS (SELECT concept_id FROM `{CDR}`.concept WHERE vocabulary_id = 'LOINC' AND concept_code IN ({ECON})),
r AS (
  SELECT o.person_id, o.observation_date AS dt, x.src_id FROM `{CDR}`.observation o
  JOIN `{CDR}`.observation_ext x ON x.observation_id = o.observation_id
  WHERE o.observation_concept_id IN (SELECT concept_id FROM c) OR o.observation_source_concept_id IN (SELECT concept_id FROM c)
  UNION ALL
  SELECT m.person_id, m.measurement_date, x.src_id FROM `{CDR}`.measurement m
  JOIN `{CDR}`.measurement_ext x ON x.measurement_id = m.measurement_id
  WHERE m.measurement_concept_id IN (SELECT concept_id FROM c) OR m.measurement_source_concept_id IN (SELECT concept_id FROM c))
SELECT idx.person_id, idx.d,
  MAX(IF(r.dt < idx.d AND STARTS_WITH(LOWER(r.src_id), 'ehr'), 1, 0)) AS scr_ehr,
  MAX(IF(r.dt < idx.d AND NOT STARTS_WITH(LOWER(r.src_id), 'ehr'), 1, 0)) AS scr_oth,
  STRING_AGG(DISTINCT IF(r.dt < idx.d AND NOT STARTS_WITH(LOWER(r.src_id), 'ehr'), r.src_id, NULL)) AS oth_src
FROM idx JOIN r ON r.person_id = idx.person_id GROUP BY 1, 2"""))

out = W.copy()
for t in (QD, DW, LB, E, SC):
    out = out.merge(t, on=KEY, how="left")
for c in ["q_dx2", "dx_win2", "inf_win2", "lab_idx", "scr_ehr", "scr_oth"] + (
    ["flu_dx_idx", "flu_good_idx", "flu_bad_idx"] if ARM == "flu" else []
):
    out[c] = out[c].fillna(0).astype(int)
out["d"] = out.d.dt.strftime("%Y-%m-%d")
keep = KEY + ["q_dx2", "dx_win2", "inf_win2", "ed24b", "lab_idx", "scr_ehr", "scr_oth"]
keep += ["flu_dx_idx", "flu_good_idx", "flu_bad_idx"] if ARM == "flu" else []
out[keep].to_csv(f"/home/jupyter/jno_v26/W_r10c_{ARM}.csv", index=False)
out["d"] = pd.to_datetime(out.d)

## ---- aggregates
case = out.q_ip.eq(1) | out.q_los.notna()
print(f"rows {len(out)} | cases {int(case.sum())}")
for c in ["q_dx2", "dx_win2", "inf_win2", "lab_idx"]:
    print(f"  cases with {c}: {show(int(out.loc[case, c].sum()))}")
edonly = case & out.q_ip.eq(0)
n_ed = int(edonly.sum())
k_ok = int(out.loc[edonly, "ed24b"].notna().sum())
k_24 = int((out.loc[edonly, "ed24b"] == 1).sum())
print(
    f"ED-only cases {show(n_ed)}: date-times usable {show(k_ok)}; >= 24 h {show(k_24)} ({pct(k_24, n_ed)} of ED-only)"
)

if ARM == "flu":
    a = out
    only_bad = a.flu_bad_idx.eq(1) & a.flu_dx_idx.eq(0) & a.flu_good_idx.eq(0)
    neither = a.flu_bad_idx.eq(0) & a.flu_dx_idx.eq(0) & a.flu_good_idx.eq(0)
    print("\ninfluenza index audit (all matched person-season rows; cases in brackets)")
    for lab, m in [
        ("influenza diagnosis on index date", a.flu_dx_idx.eq(1)),
        ("virus test, no diagnosis", a.flu_dx_idx.eq(0) & a.flu_good_idx.eq(1)),
        ("only H. influenzae or antibody result", only_bad),
        ("none of these on index date", neither),
    ]:
        print(
            f"  {lab}: {show(int(m.sum()))} of {len(a)} [{show(int((m & case).sum()))} of {int(case.sum())}]"
        )

## linkage among cases by insurance and era, crude and site-standardized
C = out[case].merge(X, on="person_id", how="left").merge(WP, on="person_id", how="left")
C["ins"] = C.insurance_type.astype(str).str.lower()
C["site_pre"] = C.site_pre.fillna("None")
print(
    "\nqualifying visit has any linked condition row, cases (crude | site-standardized, sites with both payers)"
)
for e in sorted(C.era.unique()):
    ce = C[C.era == e]
    both = ce.groupby("site_pre").ins.apply(
        lambda s: s.str.startswith("medicaid").any()
        and s.str.startswith("employer").any()
    )
    sites = both[both].index
    w = ce[ce.site_pre.isin(sites)].site_pre.value_counts(normalize=True)
    row = []
    for g in ["medicaid", "employer"]:
        cg = ce[ce.ins.str.startswith(g)]
        crude = pct(int(cg.link_any.sum()), len(cg))
        rates = cg[cg.site_pre.isin(sites)].groupby("site_pre").link_any.mean()
        std = (rates * w).sum() / w[rates.index].sum() if len(rates) else float("nan")
        row.append(f"{g} {crude} | {100 * std:.1f}%")
    print(f"  {e}: " + "; ".join(row) + f" (site levels {len(sites)})")
last = sorted(C.era.unique())[-1]
cl = C[(C.era == last)]
print(f"\nunlinked qualifying visits in {last}, index within 60 days of the cutoff:")
for g in ["medicaid", "employer"]:
    u = cl[cl.ins.str.startswith(g) & cl.link_any.eq(0)]
    k = int((u.d >= CUTOFF - pd.Timedelta(days=60)).sum())
    print(f"  {g}: {show(k)} of {show(len(u))} unlinked")

## screening provenance (person level)
P = out.sort_values(KEY).drop_duplicates("person_id")
print(
    f"\neconomic screening item before index, persons {len(P)}: EHR-sourced {show(int(P.scr_ehr.sum()))};"
    f" other sources {show(int(P.scr_oth.sum()))}"
)
srcs = (
    out.oth_src.dropna()
    .str.split(",")
    .explode()
    .str.replace(r"\d+", "#", regex=True)
    .value_counts()
)
print("  other source labels (digits masked):", dict(srcs[srcs >= MIN]))
print("DONE")
