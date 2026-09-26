# =====================================================================
# Influenza feasibility count — CDR v9, All of Us Researcher Workbench
#
# Decide, BEFORE any modelling, whether the COVID design transplants to
# influenza. Four questions per season:
#
#   1. How many participants have an influenza index event?
#   2. How many are hospitalized within 14 days (same strict phenotype)?
#   3. How many of those also have Basics Survey data?
#   4. THE DENOMINATOR CHECK — was the index event captured in an
#      outpatient setting, or only at the ED/hospital door? If the
#      NON-hospitalized control pool is thin, or is dominated by
#      ED-captured cases, the test-positive case-control design does
#      not transplant and the comparator has to change.
#
# Nothing leaves the platform. Counts below 20 print as "<20".
# Run against CDR v9 (C2025Q4R6, EHR cutoff 2025-01-01) in workspace
# su_lab_v9, AFTER 01_concept_check.py passes. Seasons past the cutoff come
# back empty; empty is itself information, so they stay in.
# =====================================================================

import os

import pandas as pd

# RW 1.0 exported WORKSPACE_CDR; RW 2.0 may not. Resolve, then PRINT it —
# the CDR this actually ran against goes in the log, because "which version
# produced this number" is the question that bites later.
CDR = next(
    (
        os.environ[k]
        for k in ("WORKSPACE_CDR", "CDR_DATASET", "AOU_CDR", "WORKSPACE_CDR_DATASET")
        if os.environ.get(k)
    ),
    None,
)
if CDR is None:
    CDR = "wb-silky-artichoke-2408.C2025Q4R6"
    print(f"No CDR env var; falling back to the attached dataset: {CDR}")
print("CDR:", CDR)
assert "C2025Q4R6" in CDR, (
    f"Expected CDR v9 (C2025Q4R6) for the influenza analysis, got {CDR}. "
    "Refusing to run rather than silently produce numbers from another release."
)

# ── Visit concepts: identical to 01_aou_etl.py STEP 1 ────────────────
STRICT_IP_VISITS = "9201,32037,262,8717"  # IP, IP hospital, ER+IP, ER-hospital
ED_VISIT = "9203"  # ED; counts only if stay >= 1 day
OUTPATIENT_VISITS = "9202,581477,38004207,38004250"

# ── Influenza phenotype ─────────────────────────────────────────────
# Condition: descendants of SNOMED 4266367 "Influenza" (covers J09-J11).
FLU_ANCESTOR = 4266367
POSITIVE_RESULT_CONCEPTS = (
    "9191,4126681,36032716,36715206,45878745,45881802,45877985,45884084"
)

# Seasons run Oct 1 -> Apr 30. CDRv9's EHR cutoff is 2025-01-01, so
# 2024-25 is PARTIAL and is labelled 2024-25p. Never compare a partial
# season's count to a whole one.
SEASON_CASE = """
    CASE
      WHEN {d} BETWEEN DATE '2016-10-01' AND DATE '2017-04-30' THEN '2016-17'
      WHEN {d} BETWEEN DATE '2017-10-01' AND DATE '2018-04-30' THEN '2017-18'
      WHEN {d} BETWEEN DATE '2018-10-01' AND DATE '2019-04-30' THEN '2018-19'
      WHEN {d} BETWEEN DATE '2019-10-01' AND DATE '2020-04-30' THEN '2019-20'
      WHEN {d} BETWEEN DATE '2020-10-01' AND DATE '2021-04-30' THEN '2020-21'
      WHEN {d} BETWEEN DATE '2021-10-01' AND DATE '2022-04-30' THEN '2021-22'
      WHEN {d} BETWEEN DATE '2022-10-01' AND DATE '2023-04-30' THEN '2022-23'
      WHEN {d} BETWEEN DATE '2023-10-01' AND DATE '2024-04-30' THEN '2023-24'
      WHEN {d} BETWEEN DATE '2024-10-01' AND DATE '2025-01-01' THEN '2024-25p'
      ELSE 'offseason'
    END
"""

# =====================================================================
# One person can have influenza in several seasons. The index is the
# FIRST flu event WITHIN each season, not a global MIN — that is the
# one structural difference from the COVID query.
# =====================================================================
sql = f"""
WITH
  flu_dx AS (
    SELECT co.person_id, co.condition_start_date AS d
    FROM `{CDR}`.condition_occurrence co
    WHERE co.condition_concept_id IN (
      SELECT descendant_concept_id FROM `{CDR}`.concept_ancestor
      WHERE ancestor_concept_id = {FLU_ANCESTOR}
    )
  ),
  flu_lab AS (
    SELECT m.person_id, m.measurement_date AS d
    FROM `{CDR}`.measurement m
    JOIN `{CDR}`.concept c ON c.concept_id = m.measurement_concept_id
    WHERE LOWER(c.concept_name) LIKE '%influenza%'
      AND m.value_as_concept_id IN ({POSITIVE_RESULT_CONCEPTS})
  ),
  flu_all AS (
    SELECT person_id, d, 'dx'  AS src FROM flu_dx
    UNION ALL
    SELECT person_id, d, 'lab' AS src FROM flu_lab
  ),
  seasoned AS (
    SELECT person_id, d, src, {SEASON_CASE.format(d='d')} AS season
    FROM flu_all
  ),
  -- first flu event per person per season
  idx AS (
    SELECT person_id, season, MIN(d) AS flu_index_date
    FROM seasoned
    WHERE season != 'offseason'
    GROUP BY person_id, season
  ),
  -- eligibility mirrors the COVID cohort: has EHR conditions AND has
  -- a Basics Survey record (observation_source_concept_id 1585845)
  has_basics AS (
    SELECT DISTINCT person_id FROM `{CDR}`.observation
    WHERE observation_source_concept_id = 1585845
  ),
  has_ehr AS (
    SELECT DISTINCT person_id FROM `{CDR}`.condition_occurrence
  ),
  -- strict hospitalization, identical rule to 01_aou_etl.py
  hosp AS (
    SELECT DISTINCT i.person_id, i.season
    FROM idx i
    JOIN `{CDR}`.visit_occurrence vo ON i.person_id = vo.person_id
    WHERE vo.visit_start_date BETWEEN i.flu_index_date
          AND DATE_ADD(i.flu_index_date, INTERVAL 14 DAY)
      AND ( vo.visit_concept_id IN ({STRICT_IP_VISITS})
            OR ( vo.visit_concept_id = {ED_VISIT}
                 AND DATE_DIFF(COALESCE(vo.visit_end_date, vo.visit_start_date),
                               vo.visit_start_date, DAY) >= 1 ) )
  ),
  -- DENOMINATOR CHECK: setting of the visit on the index date itself
  idx_setting AS (
    SELECT i.person_id, i.season,
      MAX(CASE WHEN vo.visit_concept_id IN ({OUTPATIENT_VISITS})
               THEN 1 ELSE 0 END) AS idx_outpatient,
      MAX(CASE WHEN vo.visit_concept_id IN ({STRICT_IP_VISITS},{ED_VISIT})
               THEN 1 ELSE 0 END) AS idx_acute
    FROM idx i
    LEFT JOIN `{CDR}`.visit_occurrence vo
      ON i.person_id = vo.person_id
     AND i.flu_index_date BETWEEN vo.visit_start_date
         AND COALESCE(vo.visit_end_date, vo.visit_start_date)
    GROUP BY i.person_id, i.season
  )

SELECT
  i.season,
  COUNT(*)                                          AS n_flu,
  COUNTIF(b.person_id IS NOT NULL)                  AS n_flu_basics,
  COUNTIF(h.person_id IS NOT NULL)                  AS n_hosp,
  COUNTIF(h.person_id IS NOT NULL
          AND b.person_id IS NOT NULL)              AS n_hosp_basics,
  COUNTIF(h.person_id IS NULL
          AND b.person_id IS NOT NULL)              AS n_control_basics,
  COUNTIF(s.idx_outpatient = 1)                     AS n_idx_outpatient,
  COUNTIF(s.idx_acute = 1)                          AS n_idx_acute,
  COUNTIF(s.idx_outpatient = 0 AND s.idx_acute = 0) AS n_idx_novisit,
  COUNTIF(h.person_id IS NULL AND s.idx_outpatient = 1
          AND b.person_id IS NOT NULL)              AS n_control_outpatient
FROM idx i
JOIN has_ehr e     ON i.person_id = e.person_id
LEFT JOIN has_basics b ON i.person_id = b.person_id
LEFT JOIN hosp h       ON i.person_id = h.person_id AND i.season = h.season
LEFT JOIN idx_setting s ON i.person_id = s.person_id AND i.season = s.season
GROUP BY i.season
ORDER BY i.season
"""

df = pd.read_gbq(sql, dialect="standard", progress_bar_type=None)

# =====================================================================
# Reporting. All of Us policy: no count under 20 may leave the platform,
# nor any set from which one is derivable. Suppress on print.
# =====================================================================
COUNT_COLS = [c for c in df.columns if c.startswith("n_")]


def mask(v):
    return "<20" if (pd.notna(v) and 0 < v < 20) else v


shown = df.copy()
for c in COUNT_COLS:
    shown[c] = shown[c].map(mask)

pd.set_option("display.width", 200, "display.max_columns", 50)
print("\n=== Influenza feasibility by season (CDRv9) ===")
print(shown.to_string(index=False))

# ── The three numbers that decide the study ─────────────────────────
print("\n=== GO / NO-GO ===")
for _, r in df.iterrows():
    if r.season == "offseason":
        continue
    cases, ctrls = r.n_hosp_basics, r.n_control_basics
    op_share = r.n_control_outpatient / ctrls if ctrls else float("nan")
    verdict = []
    # 1. can the joint model be fitted at all
    verdict.append(
        "cases OK"
        if cases >= 400
        else "cases THIN" if cases >= 150 else "cases TOO FEW"
    )
    # 2. is there a real non-hospitalized denominator
    verdict.append("ctrl OK" if ctrls >= 4 * max(cases, 1) else "ctrl THIN")
    # 3. is the denominator outpatient-captured, or only ED-captured
    verdict.append(f"outpatient-captured controls {op_share:.0%}")
    print(
        f"  {r.season:9s}  cases={mask(cases)}  controls={mask(ctrls)}  "
        f"| {' | '.join(verdict)}"
    )

print("""
How to read this:

  cases       hospitalized within 14 d, with Basics. The joint model
              carries ~20 SDoH parameters + 19 Charlson + demographics.
              Under ~150 cases in a season, a null is uninformative:
              you cannot tell "the money axis is absent" from "we could
              not see it".

  controls    flu-positive, NOT hospitalized, with Basics. This is the
              number that decides whether the COVID design transplants.
              Adult influenza is largely tested at the ED/hospital door,
              so this pool can be both small and selected.

  outpatient-captured controls
              of those controls, the share whose index event was
              recorded at an outpatient visit. If this is low, the
              control pool is people who reached acute care but were
              sent home — a different population from COVID's
              community-tested controls, and the paper has to say so.

If controls are thin or ED-dominated in the recent seasons, the fallback
is not to abandon the story: switch the comparator to a matched
general-cohort design (flu hospitalization vs no flu hospitalization,
matched on encounter density). That changes the estimand from "among
the infected, who is hospitalized" to "who is hospitalized with flu at
all", and that has to be stated, not glossed.
""")
