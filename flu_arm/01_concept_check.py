# =====================================================================
# Basics Survey concept check: does the v7 mapping still hold in v9?
#
# This runs BEFORE the feasibility count and before any model, because
# it is the failure that does not raise an error. v8 added "new
# self-reported categories to more closely reflect the language" in The
# Basics, and v9 inherits them. In `01_aou_etl.py` the recode ends with
#
#     ELSE 'Missing'
#
# so a value_source_concept_id that the v7 mapping does not name is not
# an error -- it is silently counted as Missing. A new income bracket
# would quietly deflate the low-income cells and nothing would complain.
#
# Two questions, per domain:
#   A. Does every concept id in the v7 mapping still appear in v9?
#      A zero means the mapping is broken.
#   B. Does v9 contain any value the v7 mapping does not name?
#      A hit means the ELSE branch is swallowing a real category.
#
# All of Us policy: counts under 20 are masked on print.
# =====================================================================

import os

import pandas as pd

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
assert "C2025Q4R6" in CDR, f"Expected CDR v9 (C2025Q4R6), got {CDR}. Refusing to run."

# ── The v7 mapping, copied verbatim from 01_aou_etl.py STEP 4 ────────
# question concept id -> {value concept id: label}
V7_MAP = {
    "insurance": (
        43528428,
        {
            43529120: "Employer",
            43529210: "Medicare",
            43529209: "Medicaid",
        },
    ),
    "employment": (
        1585952,
        {
            1585953: "Employed",
            1585958: "Student",
            1585955: "Unemployed",
            1585956: "Unemployed",
            1585960: "Unemployed",
            1585957: "Others",
            1585959: "Others",
            1585954: "Others",
        },
    ),
    "income": (
        1585375,
        {
            1585376: "less_10k",
            1585377: "10k_25k",
            1585378: "25k_35k",
            1585379: "35k_100k",
            1585380: "35k_100k",
            1585381: "35k_100k",
            1585382: "100k_150k",
            1585383: "150k_200k",
            1585384: "more_200k",
        },
    ),
    "education": (
        1585940,
        {
            1585941: "Never_Attended",
            1585942: "Below_GED",
            1585943: "Below_GED",
            1585944: "Below_GED",
            1585945: "GED_or_College",
            1585946: "GED_or_College",
            1585947: "Advanced",
            1585948: "Advanced",
        },
    ),
    "housing": (
        1585370,
        {
            1585371: "Own",
            1585372: "Rent",
            1585373: "Others",
        },
    ),
    "housing_stability": (
        1585886,
        {
            1585887: "Unstable",
            1585888: "Stable",
        },
    ),
}

# The six ACS-6 disability items: question -> (yes, no)
V7_DISABILITY = {
    "disability_hearing": (903573, 903587, 903503),
    "disability_vision": (903574, 903504, 903597),
    "disability_cognition": (903575, 903599, 903600),
    "disability_mobility": (903576, 903602, 903603),
    "disability_selfcare": (903577, 903605, 903606),
    "disability_independent": (903578, 903608, 903609),
}

# Skip / prefer-not-to-answer, filtered out by the v7 ETL
SKIP_VALUES = {903079, 903096}
BASICS_Q = 1585845  # the item used to test "has Basics Survey data"


def mask(n):
    return "<20" if 0 < n < 20 else n


# =====================================================================
# One query: every value actually observed for each Basics question in
# v9, with how many distinct people gave it. We do not ask "is my list
# there" -- we ask v9 what it has, then compare. Asking the other way
# round is how a new category stays invisible.
# =====================================================================
qids = [q for q, _ in V7_MAP.values()] + [q for q, _, _ in V7_DISABILITY.values()]

sql = f"""
SELECT
  o.observation_source_concept_id       AS question_id,
  o.value_source_concept_id             AS value_id,
  c.concept_name                        AS value_name,
  COUNT(DISTINCT o.person_id)           AS n_people
FROM `{CDR}`.observation o
LEFT JOIN `{CDR}`.concept c
  ON c.concept_id = o.value_source_concept_id
WHERE o.observation_source_concept_id IN ({','.join(map(str, qids))})
GROUP BY 1, 2, 3
ORDER BY 1, n_people DESC
"""

obs = pd.read_gbq(sql, dialect="standard", progress_bar_type=None)
print(f"\n{len(obs)} question x value combinations in v9\n")

problems = []

for domain, (qid, mapping) in V7_MAP.items():
    got = obs[obs.question_id == qid]
    known = set(mapping) | SKIP_VALUES
    seen = set(got.value_id.dropna().astype(int))

    print("=" * 68)
    print(f"{domain}   (question {qid})")
    print("=" * 68)

    # A. every mapped value must still exist
    missing = [v for v in mapping if v not in seen]
    if missing:
        problems.append(f"{domain}: v7 values absent in v9 -> {missing}")
        print(f"  BROKEN: mapped values not present in v9: {missing}")

    # B. anything v9 has that the v7 mapping does not name
    extra = sorted(seen - known)
    for v in extra:
        row = got[got.value_id == v].iloc[0]
        n = int(row.n_people)
        problems.append(
            f"{domain}: UNMAPPED value {v} ({row.value_name}) n={mask(n)} "
            f"-- the v7 recode would put these in 'Missing'"
        )
        print(f"  UNMAPPED: {v}  {row.value_name}  n={mask(n)}")

    for _, r in got.iterrows():
        v = int(r.value_id) if pd.notna(r.value_id) else None
        label = mapping.get(v, "SKIP" if v in SKIP_VALUES else ">>> UNMAPPED <<<")
        print(
            f"    {str(v):>10}  n={str(mask(int(r.n_people))):>9}  "
            f"{label:<16} {r.value_name}"
        )
    print()

# ── ACS-6 disability items ───────────────────────────────────────────
print("=" * 68)
print("ACS-6 disability items")
print("=" * 68)
for name, (qid, yes, no) in V7_DISABILITY.items():
    got = obs[obs.question_id == qid]
    seen = set(got.value_id.dropna().astype(int))
    ok = yes in seen and no in seen
    if not ok:
        problems.append(f"{name}: yes={yes} no={no} not both present in v9")
    n_yes = int(got.loc[got.value_id == yes, "n_people"].sum())
    n_no = int(got.loc[got.value_id == no, "n_people"].sum())
    extra = sorted(seen - {yes, no} - SKIP_VALUES)
    flag = "OK " if ok else "BROKEN"
    print(
        f"  {flag} {name:<26} q={qid}  yes n={mask(n_yes):>9}  "
        f"no n={mask(n_no):>9}" + (f"  UNMAPPED {extra}" if extra else "")
    )
    for v in extra:
        row = got[got.value_id == v].iloc[0]
        problems.append(
            f"{name}: UNMAPPED value {v} ({row.value_name}) "
            f"n={mask(int(row.n_people))}"
        )

# ── Basics eligibility item ──────────────────────────────────────────
n_basics = pd.read_gbq(
    f"""SELECT COUNT(DISTINCT person_id) AS n
        FROM `{CDR}`.observation
        WHERE observation_source_concept_id = {BASICS_Q}""",
    dialect="standard",
    progress_bar_type=None,
).n.iloc[0]
print(
    f"\nParticipants with the Basics eligibility item ({BASICS_Q}): "
    f"{int(n_basics):,}"
)

# =====================================================================
# Verdict. This is a gate, not a report.
# =====================================================================
print("\n" + "=" * 68)
if problems:
    print(f"CONCEPT CHECK FAILED -- {len(problems)} problem(s)")
    print("=" * 68)
    for p in problems:
        print("  -", p)
    print("""
Do not run the feasibility count or any model until each line above is
resolved. The two repairs, in order of preference:

  1. An UNMAPPED value that is a genuinely new category: add it to the
     mapping in BOTH the v7 and v9 recodes, or collapse to whichever
     coarser grouping both releases can express. The exposures must mean
     the same thing in the influenza analysis as in the COVID analysis,
     or the comparison the paper rests on is not a comparison.
  2. A BROKEN value that simply moved concept id: remap it, and record
     the old and new ids in DECISIONS.md.

Silently accepting 'Missing' is not one of the options. That is the
failure this script exists to catch.""")
else:
    print("CONCEPT CHECK PASSED")
    print("=" * 68)
    print(
        "Every v7 Basics value is present in v9, and v9 contains no value\n"
        "the v7 recode would silently drop into 'Missing'. The six domains\n"
        "mean the same thing in both releases. Proceed to the count."
    )
