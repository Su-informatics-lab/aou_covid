"""eTable 8, post-matching panel: median (IQR) of the three MarketScan matching
variables in the final analytic cohort.

Runs on the Quartz login node in about 3 seconds and under 1 GB, so it needs no
SLURM allocation. Reads only aggregate-safe columns and prints only quantiles and
standardized mean differences over 127,696 cases and 509,983 control observations.

Convention, which matters because two matched sets exist:

  medians  -> 08_regression_base.csv, the final analytic cohort, after the 1,802
              observations near the data cutoff were removed. Computed over analytic
              ROWS, so a control reused in k strata counts k times. This is what the
              N in the eTable 8 header refers to, and it matches eTable 7 for
              All of Us.
  SMDs     -> left as MatchIt reported them in 07c_smd_pre_matching.csv, that is,
              weighted and computed on the matched set before the trim. Recomputing
              them on the analytic cohort would silently change three numbers that
              eFigure 2b, the Figure 1 legend and eMethod 1 all carry.

The raw MatchIt output is loaded as well, purely so the two can be compared.
"""

import time

import numpy as np
import pandas as pd

D = "/N/project/depot/hw56/ms_covid/aou_covid/results/ms"
VARS = ["enrollment_ord", "num_diagnosis", "coverage_span_days"]


def panel(df, mv, label):
    m = df.merge(mv, on="person_id", how="left")
    print(f"\n=== {label} ===")
    print(
        "rows",
        len(m),
        "| cases",
        int((m.Treatment == 1).sum()),
        "| control rows",
        int((m.Treatment == 0).sum()),
        "| unique control persons",
        m.loc[m.Treatment == 0, "person_id"].nunique(),
        "| unmerged",
        int(m[VARS].isna().any(axis=1).sum()),
    )
    for v in VARS:
        cells = []
        for g in (1, 0):
            x = m.loc[m.Treatment == g, v].dropna()
            q1, q2, q3 = np.percentile(x, [25, 50, 75])
            cells.append(f"{q2:,.0f} ({q1:,.0f}-{q3:,.0f})")
        tr = m.loc[m.Treatment == 1, v].dropna()
        ct = m.loc[m.Treatment == 0, v].dropna()
        smd_treated = (tr.mean() - ct.mean()) / tr.std(ddof=1)
        pooled = np.sqrt((tr.var(ddof=1) + ct.var(ddof=1)) / 2)
        smd_pooled = (tr.mean() - ct.mean()) / pooled
        print(
            f"{v:22s} cases {cells[0]:28s} controls {cells[1]:28s} "
            f"SMD_treated {smd_treated:+.4f}  SMD_pooled {smd_pooled:+.4f}"
        )


def main():
    t0 = time.time()
    mv = pd.read_csv(f"{D}/06_matching_variables.csv", usecols=["person_id"] + VARS)
    final = pd.read_csv(
        f"{D}/08_regression_base.csv", usecols=["person_id", "Treatment", "stratum"]
    )
    raw = pd.read_csv(f"{D}/07_matched_cohort.csv")
    panel(final, mv, "FINAL analytic cohort (08_regression_base, post cutoff trim)")
    panel(raw, mv, "RAW MatchIt output (07_matched_cohort, pre trim)")
    print(f"\nelapsed {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
