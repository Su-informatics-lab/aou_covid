#!/usr/bin/env python3
"""
COVID-19 Severity × SDoH — Pre/Post Matching Balance (SMD)
Mirrors Gatz et al. JAMIA 2024 eTables 8-9.

Runs ON-PLATFORM (AoU Workbench or Quartz HPC).
Computes standardized mean differences for matching variables
before and after propensity score matching.

Usage: python 05_smd_onplatform.py aou_v7
       python 05_smd_onplatform.py ms

Output: results/{cohort}/etable_smd_pre_matching.csv  (safe to export)
        results/{cohort}/etable_smd_post_matching.csv  (safe to export)
"""

import os
import sys

import numpy as np
import pandas as pd

if len(sys.argv) < 2 or sys.argv[1] not in ("aou_v7", "aou_v8", "ms"):
    print("Usage: python 05_smd_onplatform.py [aou_v7|aou_v8|ms]")
    sys.exit(1)

COHORT = sys.argv[1]
IS_AOU = COHORT.startswith("aou")
RESULTS = f"results/{COHORT}"
RECOMPUTE = "--recompute" in sys.argv

print("=" * 70)
print(f"PRE/POST MATCHING BALANCE (SMD)  [{COHORT.upper()}]")
print("=" * 70)

# ── Load data ─────────────────────────────────────────────────────────
cohort = pd.read_csv(f"{RESULTS}/01_covid_cohort.csv")
matched = pd.read_csv(f"{RESULTS}/06_matched_cohort.csv")

print(f"  Cohort: {len(cohort):,}  |  Matched: {len(matched):,}")

# ── Reconstruct matching variables (with cache) ──────────────────────
CACHE_PATH = f"{RESULTS}/cache_match_vars.csv"

if os.path.exists(CACHE_PATH) and not RECOMPUTE:
    print(f"  Loading cached match vars from {CACHE_PATH}")
    match_vars = pd.read_csv(CACHE_PATH)
    if IS_AOU:
        MATCH_COLS = ["enrollment_ord", "num_diagnosis", "ehr_length_days"]
        VAR_LABELS = {
            "enrollment_ord": "Enrollment date (ordinal)",
            "num_diagnosis": "Number of diagnoses",
            "ehr_length_days": "Length of EHR history (days)",
        }
    else:
        MATCH_COLS = ["enrollment_ord", "num_diagnosis", "coverage_span_days"]
        VAR_LABELS = {
            "enrollment_ord": "Enrollment date (ordinal)",
            "num_diagnosis": "Number of diagnoses",
            "coverage_span_days": "Coverage span (days)",
        }

elif IS_AOU:
    CDR = os.environ.get("WORKSPACE_CDR", "")
    print(f"  CDR: {CDR}")

    match_sql = f"""
    SELECT p.person_id,
      MIN(o.observation_date) AS basics_survey_date,
      COUNT(DISTINCT co.condition_concept_id) AS num_diagnosis,
      DATE_DIFF(MAX(co.condition_start_date),
                MIN(co.condition_start_date), DAY) AS ehr_length_days
    FROM `{CDR}`.person p
    JOIN `{CDR}`.observation o
      ON p.person_id = o.person_id
      AND o.observation_source_concept_id = 1585845
    JOIN `{CDR}`.condition_occurrence co
      ON p.person_id = co.person_id
    WHERE p.person_id IN ({','.join(map(str, cohort.person_id.tolist()))})
    GROUP BY p.person_id
    """
    print("  Querying matching variables from BigQuery...")
    match_vars = pd.read_gbq(match_sql, dialect="standard")
    match_vars["enrollment_ord"] = pd.to_datetime(
        match_vars["basics_survey_date"]
    ).apply(lambda x: x.toordinal() if pd.notna(x) else np.nan)

    VAR_LABELS = {
        "enrollment_ord": "Enrollment date (ordinal)",
        "num_diagnosis": "Number of diagnoses",
        "ehr_length_days": "Length of EHR history (days)",
    }
    MATCH_COLS = ["enrollment_ord", "num_diagnosis", "ehr_length_days"]

else:  # MarketScan
    import duckdb

    MS_DIR = "/N/project/Marketscan1/parquet"
    YEARS = ["2020", "2021", "2022", "2023"]
    con = duckdb.connect(database=":memory:")
    con.execute("PRAGMA threads=4")

    # Diagnosis counts from dx_long
    print("  Building diagnosis counts...")
    dx_unions = []
    for y in YEARS:
        for src, cols in [
            ("i", ["PDX"] + [f"DX{i}" for i in range(1, 16)]),
            ("o", ["DX1", "DX2", "DX3", "DX4"]),
        ]:
            f = f"{MS_DIR}/mscan_{y}_{src}.parquet"
            if not os.path.exists(f):
                continue
            for col in cols:
                dx_unions.append(f"""
                SELECT ENROLID AS person_id,
                       REPLACE(UPPER(CAST({col} AS VARCHAR)),'.','') AS dx_code
                FROM read_parquet('{f}') WHERE {col} IS NOT NULL""")

    con.register("covid_pids", pd.DataFrame({"person_id": cohort.person_id.tolist()}))
    con.sql(f"""
    CREATE TABLE dx_long AS
    SELECT DISTINCT person_id, dx_code
    FROM ({' UNION ALL '.join(dx_unions)}) sub
    WHERE person_id IN (SELECT person_id FROM covid_pids)
    """)
    dx_counts = con.sql("""
    SELECT person_id, COUNT(DISTINCT dx_code) AS num_diagnosis
    FROM dx_long GROUP BY person_id
    """).df()

    # Enrollment dates
    print("  Computing enrollment dates...")
    enroll_unions = []
    for y in YEARS:
        f = f"{MS_DIR}/mscan_{y}_t.parquet"
        if os.path.exists(f):
            enroll_unions.append(
                f"SELECT ENROLID AS person_id, DTSTART, DTEND FROM read_parquet('{f}')"
            )

    enroll_dates = con.sql(f"""
    SELECT e.person_id,
           MIN(e.DTSTART) AS first_enrollment,
           DATEDIFF('day', MIN(e.DTSTART), MAX(e.DTEND)) AS coverage_span_days
    FROM ({' UNION ALL '.join(enroll_unions)}) e
    WHERE e.person_id IN (SELECT person_id FROM covid_pids)
    GROUP BY e.person_id
    """).df()
    enroll_dates["enrollment_ord"] = pd.to_datetime(
        enroll_dates["first_enrollment"]
    ).apply(lambda x: x.toordinal() if pd.notna(x) else np.nan)

    match_vars = dx_counts.merge(
        enroll_dates[["person_id", "enrollment_ord", "coverage_span_days"]],
        on="person_id",
        how="inner",
    )
    con.close()

    VAR_LABELS = {
        "enrollment_ord": "Enrollment date (ordinal)",
        "num_diagnosis": "Number of diagnoses",
        "coverage_span_days": "Coverage span (days)",
    }
    MATCH_COLS = ["enrollment_ord", "num_diagnosis", "coverage_span_days"]


# ── Merge with cohort and matched cohort ──────────────────────────────
mv = match_vars.merge(cohort[["person_id", "severity"]], on="person_id")
mv = mv.dropna(subset=MATCH_COLS)
print(f"  Match variables available: {len(mv):,}")

# Save cache
match_vars.to_csv(CACHE_PATH, index=False)
print(f"  Cached: {CACHE_PATH} (use --recompute to refresh)")


# ── SMD function ──────────────────────────────────────────────────────
def compute_smd(cases, controls, col):
    """Standardized mean difference (Cohen's d, pooled SD)."""
    m1, s1 = cases[col].mean(), cases[col].std()
    m2, s2 = controls[col].mean(), controls[col].std()
    pooled_sd = np.sqrt((s1**2 + s2**2) / 2)
    if pooled_sd == 0:
        return 0.0
    return (m1 - m2) / pooled_sd


def format_median_iqr(series):
    """Format as 'median (IQR: Q1 – Q3)'."""
    med = series.median()
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    return f"{med:,.0f} ({q1:,.0f} – {q3:,.0f})"


# ── eTable S6: PRE-MATCHING BALANCE ───────────────────────────────────
print(f"\n{'='*60}")
print("eTable S6: Pre-Matching Balance")
print("=" * 60)

pre_cases = mv[mv.severity == 1]
pre_controls = mv[mv.severity == 0]

pre_rows = []
for col in MATCH_COLS:
    label = VAR_LABELS[col]
    smd = compute_smd(pre_cases, pre_controls, col)
    pre_rows.append(
        {
            "Variable": label,
            f"Cases (N={len(pre_cases):,})": format_median_iqr(pre_cases[col]),
            f"Controls (N={len(pre_controls):,})": format_median_iqr(pre_controls[col]),
            "SMD": f"{smd:.3f}",
        }
    )

pre_df = pd.DataFrame(pre_rows)
pre_df.to_csv(f"{RESULTS}/etable_smd_pre_matching.csv", index=False)
print(pre_df.to_string(index=False))

# ── eTable S7: POST-MATCHING BALANCE ─────────────────────────────────
print(f"\n{'='*60}")
print("eTable S7: Post-Matching Balance")
print("=" * 60)

post = matched.merge(match_vars, on="person_id", how="left")
post = post.dropna(subset=MATCH_COLS)

post_cases = post[post.Treatment == 1]
post_controls = post[post.Treatment == 0]

post_rows = []
for col in MATCH_COLS:
    label = VAR_LABELS[col]
    smd = compute_smd(post_cases, post_controls, col)
    post_rows.append(
        {
            "Variable": label,
            f"Cases (N={len(post_cases):,})": format_median_iqr(post_cases[col]),
            f"Controls (N={len(post_controls):,})": format_median_iqr(
                post_controls[col]
            ),
            "SMD": f"{smd:.3f}",
        }
    )

post_df = pd.DataFrame(post_rows)
post_df.to_csv(f"{RESULTS}/etable_smd_post_matching.csv", index=False)
print(post_df.to_string(index=False))

# ── Summary ───────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("BALANCE IMPROVEMENT SUMMARY")
print("=" * 60)
for col in MATCH_COLS:
    pre_smd = compute_smd(pre_cases, pre_controls, col)
    post_smd = compute_smd(post_cases, post_controls, col)
    pct_change = (
        (abs(post_smd) - abs(pre_smd)) / abs(pre_smd) * 100 if pre_smd != 0 else 0
    )
    status = "✓ improved" if abs(post_smd) < abs(pre_smd) else "✗ worse"
    print(
        f"  {VAR_LABELS[col]:40s} {abs(pre_smd):.3f} → {abs(post_smd):.3f}  ({pct_change:+.0f}%)  {status}"
    )

print(f"\nSaved: {RESULTS}/etable_smd_pre_matching.csv")
print(f"Saved: {RESULTS}/etable_smd_post_matching.csv")
print("\nThese CSVs contain ONLY aggregate statistics (no PII). Safe to export.")

# ── eFigure: LOVE PLOT (SMD before/after matching) ────────────────────
print(f"\n{'='*60}")
print("eFigure: Love Plot (SMD Balance)")
print("=" * 60)

import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42
mpl.rcParams["font.family"] = "sans-serif"
mpl.rcParams["font.sans-serif"] = ["Arial", "Helvetica", "DejaVu Sans"]
mpl.rcParams["font.size"] = 7
mpl.rcParams["axes.linewidth"] = 0.5
mpl.rcParams["figure.facecolor"] = "white"
mpl.rcParams["savefig.dpi"] = 300

labels, pre_smds, post_smds = [], [], []
for col in MATCH_COLS:
    labels.append(VAR_LABELS[col])
    pre_smds.append(abs(compute_smd(pre_cases, pre_controls, col)))
    post_smds.append(abs(compute_smd(post_cases, post_controls, col)))

fig, ax = plt.subplots(figsize=(4.724, 2.5))  # 1.5-column width
y = np.arange(len(labels))[::-1]

ax.scatter(
    pre_smds,
    y,
    marker="o",
    facecolors="none",
    edgecolors="#D55E00",
    s=40,
    linewidths=1.0,
    zorder=3,
    label="Before matching",
)
ax.scatter(
    post_smds,
    y,
    marker="o",
    facecolors="#0072B2",
    edgecolors="#0072B2",
    s=40,
    linewidths=1.0,
    zorder=4,
    label="After matching",
)

# Connect pre→post with arrows
for i in range(len(labels)):
    ax.annotate(
        "",
        xy=(post_smds[i], y[i]),
        xytext=(pre_smds[i], y[i]),
        arrowprops=dict(arrowstyle="->", color="#999999", lw=0.6),
    )

# Reference line at |SMD| = 0.1
ax.axvline(0.1, color="black", linewidth=0.5, linestyle="--", zorder=1)
ax.text(0.105, y.max() + 0.3, "|SMD| = 0.1", fontsize=6, va="bottom")

ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=7)
ax.set_xlabel("|Standardized Mean Difference|", fontsize=7)
ax.set_xlim(-0.02, max(max(pre_smds), 0.15) * 1.15)
ax.legend(fontsize=6, loc="upper right")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

FIG_DIR = os.path.join(os.path.dirname(RESULTS), "figures")
os.makedirs(FIG_DIR, exist_ok=True)
love_path = os.path.join(FIG_DIR, f"efig_love_plot_{COHORT}")
fig.savefig(f"{love_path}.pdf", bbox_inches="tight")
fig.savefig(f"{love_path}.png", bbox_inches="tight")
print(f"  Saved: {love_path}.pdf/.png")
plt.close(fig)
