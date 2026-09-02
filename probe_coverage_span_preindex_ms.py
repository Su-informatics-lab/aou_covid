#!/usr/bin/env python3
"""Coverage-span pre-index probe — MarketScan (Quartz).

Why this exists
---------------
`01_ms_etl.py` builds the third matching variable as

    DATEDIFF('day', MIN(e.DTSTART), MAX(e.DTEND))

with no index-date restriction, so a person's coverage span includes enrollment
that continues *after* the COVID index date. That is the same shape of mistake
the All of Us side carried in `num_diagnosis`, where post-index information
entered the propensity model and about a sixth of the imbalance turned out to
have been manufactured by the outcome.

MarketScan's other two matching variables are clean: `num_diagnosis` comes from
`dx_long`, created with `WHERE d.dx_date < c.covid_index_date` (01_ms_etl.py
line 276), and a first enrollment date cannot be moved by a later admission.
Coverage span is the one left.

Whether it matters is an empirical question, and re-running the MarketScan ETL
is a multi-hour DuckDB job over the full corpus, so it should be paid for by
evidence rather than by my guess.

The decisive statistic is not how much the variable moves. It is how much the
*case-versus-control* standardized difference moves, because that is what the
propensity model sees. The published pre-matching SMD for coverage span is
-0.137, against 0.613 for diagnosis count.

Everything aggregates inside DuckDB; only a handful of summary statistics reach
pandas, so this runs in a few hundred MB and does not need a compute node.

Reads only. Writes one small comparison CSV.

Usage:  python probe_coverage_span_preindex_ms.py
"""

import os
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

import duckdb
import numpy as np
import pandas as pd

MS_DIR = "/N/project/Marketscan1/parquet"
RESULTS = "results/ms"
YEARS = ["2020", "2021", "2022", "2023"]
COHORT = os.path.join(RESULTS, "01_covid_cohort.csv")

# Quartz login nodes cap memory well below what four years of enrollment
# records need, so this is an sbatch job. DuckDB is given a spill directory as
# well as a limit: the union scan is large and spilling is cheaper than dying.
MEM = os.environ.get("PROBE_MEM", "48GB")
TMP = os.environ.get("PROBE_TMP", os.path.join(os.getcwd(), "duckdb_tmp"))
os.makedirs(TMP, exist_ok=True)

con = duckdb.connect(database=":memory:")
con.execute(f"PRAGMA threads={os.environ.get('SLURM_CPUS_PER_TASK', '8')}")
con.execute(f"SET memory_limit='{MEM}'")
con.execute(f"SET temp_directory='{TMP}'")
con.execute("SET preserve_insertion_order=false")

print("=" * 72)
print("COVERAGE-SPAN PRE-INDEX PROBE — MarketScan (Quartz)")
print("=" * 72)

unions = []
for y in YEARS:
    f = f"{MS_DIR}/mscan_{y}_t.parquet"
    if os.path.exists(f):
        unions.append(
            f"SELECT ENROLID AS person_id, DTSTART, DTEND FROM read_parquet('{f}')"
        )
    else:
        print(f"  WARNING: missing {f}")
if not unions:
    raise SystemExit("no enrollment parquet found")

con.execute(f"""
CREATE OR REPLACE VIEW cohort AS
SELECT CAST(person_id AS BIGINT)            AS person_id,
       CAST(covid_index_date AS DATE)       AS covid_index_date,
       CAST(severity AS INTEGER)            AS severity
FROM read_csv_auto('{COHORT}')
""")
n = con.sql("SELECT COUNT(*) n, SUM(severity) cases FROM cohort").df().iloc[0]
print(f"  cohort: {int(n.n):,}   cases: {int(n.cases):,}")

print("  aggregating both spans inside DuckDB ...")
con.execute(f"""
CREATE OR REPLACE TEMP TABLE spans AS
WITH e AS (
  SELECT CAST(person_id AS BIGINT) AS person_id, DTSTART, DTEND
  FROM ({' UNION ALL '.join(unions)})
),
j AS (
  SELECT e.person_id, c.severity, c.covid_index_date, e.DTSTART, e.DTEND
  FROM e JOIN cohort c USING (person_id)
)
SELECT person_id,
       ANY_VALUE(severity)                                        AS severity,
       DATEDIFF('day', MIN(DTSTART), MAX(DTEND))                  AS span_all,
       DATEDIFF('day', MIN(DTSTART),
                LEAST(MAX(DTEND), ANY_VALUE(covid_index_date)))   AS span_preindex
FROM j
GROUP BY person_id
""")

stats = con.sql("""
SELECT severity,
       COUNT(*)                    AS n,
       AVG(span_all)               AS mean_all,
       VAR_SAMP(span_all)          AS var_all,
       MEDIAN(span_all)            AS med_all,
       AVG(span_preindex)          AS mean_pre,
       VAR_SAMP(span_preindex)     AS var_pre,
       MEDIAN(span_preindex)       AS med_pre
FROM spans WHERE span_all IS NOT NULL AND span_preindex IS NOT NULL
GROUP BY severity ORDER BY severity
""").df()
print(stats.to_string(index=False))

delta = con.sql("""
SELECT MEDIAN(span_all - span_preindex) AS med_removed,
       AVG(span_all - span_preindex)    AS mean_removed,
       AVG(CASE WHEN span_all = span_preindex THEN 1.0 ELSE 0.0 END) AS share_unchanged,
       CORR(span_all, span_preindex)    AS corr_two_versions
FROM spans WHERE span_all IS NOT NULL AND span_preindex IS NOT NULL
""").df().iloc[0]


def smd(mean_c, var_c, mean_k, var_k):
    sp = np.sqrt((var_c + var_k) / 2.0)
    return (mean_c - mean_k) / sp if sp > 0 else np.nan


ctrl = stats[stats.severity == 0].iloc[0]
case = stats[stats.severity == 1].iloc[0]
s_old = smd(case.mean_all, case.var_all, ctrl.mean_all, ctrl.var_all)
s_new = smd(case.mean_pre, case.var_pre, ctrl.mean_pre, ctrl.var_pre)

print()
print(f"  days removed by truncation: median {delta.med_removed:.0f}, "
      f"mean {delta.mean_removed:.1f}, share unchanged {100*delta.share_unchanged:.1f}%")
print(f"  correlation of the two versions: {delta.corr_two_versions:.4f}")
print()
print("=" * 72)
print(f"  pre-matching SMD, current   : {s_old:+.4f}   (published: -0.137)")
print(f"  pre-matching SMD, pre-index : {s_new:+.4f}")
print(f"  change                      : {abs(s_new - s_old):.4f}")
print()
print("  Read it against the variable that mattered on the All of Us side:")
print("  diagnosis count moved 0.489 -> 0.410, a change of 0.079, and that")
print("  shifted every downstream estimate. A change here far below 0.079 is")
print("  evidence the MarketScan matching would not move and the multi-hour ETL")
print("  re-run buys nothing. A change near or above it is evidence to run it.")
print("=" * 72)

out = pd.DataFrame([
    {"version": "current (no index restriction)", "column": "span_all",
     "n_cases": int(case.n), "n_controls": int(ctrl.n),
     "median_cases": float(case.med_all), "median_controls": float(ctrl.med_all),
     "smd_case_vs_control": float(s_old)},
    {"version": "truncated at the index date", "column": "span_preindex",
     "n_cases": int(case.n), "n_controls": int(ctrl.n),
     "median_cases": float(case.med_pre), "median_controls": float(ctrl.med_pre),
     "smd_case_vs_control": float(s_new)},
])
out.to_csv(os.path.join(RESULTS, "probe_coverage_span_preindex_comparison.csv"),
           index=False)
print(f"\n  saved {RESULTS}/probe_coverage_span_preindex_comparison.csv")
