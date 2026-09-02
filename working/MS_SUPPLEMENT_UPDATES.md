# MarketScan re-run — exact replacements for the supplement and Figure 1

**Source:** Slurm job `10186336` on Quartz, finished 2026-09-01 23:02 EDT, exit 0.
Log: `/N/project/depot/hw56/ms_covid/aou_covid/slurm_ms_resume_psm_10186336.out`
Artifacts: `/N/project/depot/hw56/ms_covid/aou_covid/results/ms/`

The run resumed from `01b_psm.R`. The ETL that produced its inputs (job `10186030`)
carried the pre-index restriction on `coverage_span_days`, and the guard in the
sbatch re-verified both invariants before resuming rather than trusting the earlier
log: coverage-span SMD −0.3630 (threshold |SMD| ≥ 0.20) and Dementia 5,527 (< 10,000).

Everything below is transcribed from an artifact file, not from the log's prose.

---

## eTable 8 — pre/post-matching balance, MarketScan

Replace the whole table **and the caption**.

| Variable (median, IQR) | Cases (N = 127,901) | Controls (N = 3,881,727) | SMD |
|---|---|---|---|
| Enrollment date (ordinal) | 737,425 (737,425–737,425) | 737,425 (737,425–737,669) | −0.241 |
| Number of diagnoses | 17 (8–33) | 14 (7–26) | 0.199 |
| Coverage span (days) | 398 (256–622) | 559 (316–751) | −0.400 |

Post-matching SMDs (`07c_smd_pre_matching.csv`, `smd_adjusted`):
enrollment date **0.063**, number of diagnoses **−0.012**, coverage span **−0.045**.

**Caption changes — two factual claims in the old caption are now false.**

- `All post-matching |SMD| < 0.03` → **`< 0.07`**. The enrollment-date SMD is 0.063.
- `139,472 cases and 4,283,335 controls ... 17 cases and 376 controls ... excluded for
  missing matching variables` → **`127,901 cases and 3,881,727 controls; 11,571 cases and
  401,608 controls from the raw cohort (139,472 and 4,283,335) were excluded for missing
  matching variables before propensity score estimation, because coverage span and
  diagnosis count are now measured only over records dated before the index date.`**

The exclusion grew from 393 participants to 413,179. That is the single largest
consequence of the fix and it is now stated in Limitations.

---

## eTable 9 — plan type and region, matched cohort

From `table1_demographics.csv`. Cases N = 127,696; controls N = 509,983.

| | Cases | Controls |
|---|---|---|
| PPO | 62,135 (48.7) | 249,710 (49.0) |
| HMO | 16,525 (12.9) | 59,564 (11.7) |
| POS | 12,157 (9.5) | 51,463 (10.1) |
| HDHP | 15,428 (12.1) | 62,391 (12.2) |
| CDHP | 181 (0.1) | 561 (0.1) |
| EPO | 1,471 (1.2) | 6,281 (1.2) |
| Comprehensive | 3,241 (2.5) | 9,543 (1.9) |
| Basic | <20 | 38 (0.0) |
| Unknown | 16,542 (13.0) | 70,432 (13.8) |
| South | 67,378 (52.8) | 266,702 (52.3) |
| North Central | 26,150 (20.5) | 96,184 (18.9) |
| West | 16,298 (12.8) | 60,035 (11.8) |
| Northeast | 17,585 (13.8) | 86,166 (16.9) |
| Unknown | 285 (0.2) | 896 (0.2) |

---

## eTable 10 — cross-site comparison

**The AoU column is still v18.6 and must be replaced from the Workbench
`base_model_coefficients.csv` before this table is rebuilt.** The MarketScan column below
is final. `*` = P < 0.05.

| Variable | MS v18.6 | MS re-run | |
|---|---|---|---|
| Female sex | 0.50 (0.49–0.50)* | 0.75 (0.74–0.76)* | |
| Vaccinated before index | 0.48 (0.47–0.50)* | 0.50 (0.49–0.52)* | |
| Age 45–54 | 1.46 (1.44–1.48)* | 1.75 (1.72–1.78)* | |
| Age 55–64 | 1.78 (1.75–1.81)* | 2.39 (2.35–2.43)* | |
| Age ≥65 | 1.73 (1.51–1.98)* | 2.52 (2.16–2.93)* | |
| Delta wave | 1.47 (1.44–1.49)* | 1.11 (1.06–1.17)* | |
| Omicron wave | 0.47 (0.47–0.48)* | 0.73 (0.70–0.76)* | |
| Myocardial infarction | 0.94 (0.89–0.99)* | 1.05 (0.99–1.11) | **reversed** |
| CHF | 1.36 (1.31–1.41)* | 1.66 (1.59–1.72)* | |
| Peripheral vascular disease | 0.86 (0.83–0.89)* | 1.06 (1.02–1.10)* | **reversed** |
| Cerebrovascular | 0.86 (0.83–0.89)* | 1.06 (1.02–1.10)* | **reversed** |
| Dementia | 1.27 (1.16–1.39)* | 1.61 (1.45–1.77)* | |
| Chronic pulmonary | 0.86 (0.84–0.87)* | 1.16 (1.14–1.19)* | **reversed** |
| Rheumatic disease | 0.82 (0.79–0.85)* | 1.09 (1.05–1.14)* | **reversed** |
| Peptic ulcer | 0.79 (0.73–0.84)* | 1.01 (0.94–1.08) | **reversed** |
| Liver mild | 0.78 (0.76–0.81)* | 1.06 (1.03–1.09)* | **reversed** |
| Liver mod/severe | 1.43 (1.31–1.56)* | 1.99 (1.81–2.19)* | |
| DM w/o complic. | 1.41 (1.38–1.44)* | 1.81 (1.77–1.84)* | |
| DM w/ complic. | 1.46 (1.42–1.50)* | 2.02 (1.96–2.08)* | |
| Hemiplegia/paraplegia | 1.71 (1.59–1.83)* | 2.18 (2.02–2.34)* | |
| Renal mild/mod | 1.29 (1.25–1.34)* | 1.58 (1.53–1.64)* | |
| Renal severe | 2.45 (2.31–2.59)* | 3.31 (3.11–3.53)* | |
| HIV | 0.86 (0.76–0.96)* | 1.25 (1.11–1.40)* | **reversed** |
| Metastatic tumor | 1.68 (1.59–1.77)* | 2.63 (2.48–2.79)* | |
| Malignancy | 0.94 (0.91–0.98)* | 1.22 (1.18–1.27)* | **reversed** |
| AIDS | 1.27 (1.03–1.58)* | 1.69 (1.34–2.12)* | |

Nine comorbidities were significantly inverse in v18.6. All nine reversed; seven of them
are now significantly elevated, and myocardial infarction and peptic ulcer sit at the null.
**No MarketScan comorbidity is below 1.0 in the corrected model** (minimum, peptic ulcer,
1.0063).

The caption's `Twenty of the 25 comparable estimates were concordant` cannot be recomputed
until the AoU column is refreshed. Do not carry the old sentence forward.

---

## eTable 11b — variance sensitivity, MarketScan

Full table in `variance_sensitivity_etable11b.csv`. Headline: median CI ratio **1.00**;
**one** variable changes significance status under the cluster-robust estimator —
`f.planCDHP`, 1.18, exact (0.99–1.42) against robust (1.01–1.39).

Note for Methods: `vcovCL` failed on the exact partial-likelihood fit ("score residuals are
not available for the exact method"), so the reported MarketScan model uses model-based
standard errors, and the robust column comes from a refit under Efron's approximation.
This is now stated in the Methods paragraph on variance.

---

## eTable 14 — AIDS phenotype sensitivity

The primary MarketScan AIDS estimate moves **1.27 (1.03–1.58) → 1.69 (1.34–2.12)**, and
HIV moves **0.86 (0.76–0.96) → 1.25 (1.11–1.40)**.

The old caption argued that the cross-cohort AIDS difference was sensitive to the
phenotype, and that *"Replacing it with HIV alone ... reverses the MarketScan direction."*
That sentence rested on MarketScan HIV being 0.86. **HIV is now 1.25 and the reversal no
longer happens.** The alternative-phenotype rows were not re-run; rerun
`02c_aids_sensitivity.R ms` (or equivalent) before rewriting this caption, and do not
carry the old argument forward.

---

## Figure 1, panel (b) — draw.io

Panel (b) needs a full renumber, not a single box edit.

```
COVID-positive                            4,423,200
  ├── hospitalized cases                    139,472
  └── outpatient controls                 4,283,335
Complete matching variables (pre-index)   4,009,628
  ├── cases                                 127,901
  └── controls                            3,881,727
PSM 1:4, nearest neighbour with replacement, caliper 0.2 SD logit PS
  ├── cases matched                         127,900   (1 dropped, no match in caliper)
  └── control observations                  511,581   (444,575 unique individuals)
Trim: 1,598 control observations with index > 2023-12-17 (CDR cutoff − 14 d)
      204 strata left with no control
Analytic set                                637,679 observations in 127,696 strata
  ├── cases                                 127,696
  └── control observations                  509,983   (443,061 unique individuals)
```

The matching box's first item is `Enrollment date`, which is correct for MarketScan —
the `Survey date` rename applies to panel (a) only.

---

## Figure 3

The MarketScan series must be re-plotted from `results/ms/base_model_coefficients.csv`.
Blocked on the AoU series, which is re-plotted from the Workbench in the same script.
Legend already says n = 637,679.

---
---

# All of Us extraction, 2026-09-02 (added after the Workbench session)

Source: `gs://rw-migration-aou-rw-46c7ae9e/data/covid_sdoh/aou_v7/`, read through the
Workbench terminal. **The copy in `~/covid/repo/results/aou_v7/` on the VM is the
v18.6 output, not the re-run** — it was checked against three marker values and does
not match. Do not read from it. The bucket also holds an `aou_v8/` tree and a loose
copy at the `data/covid_sdoh/` root, both from a CDR v8 run that this manuscript does
not use.

Every value below was printed twice in different formats and checked for log-scale
interval symmetry. Four screen-reading errors were caught that way and corrected:
HIV lower bound 0.7783→**0.7703**, domain-specific `f.income10k_25k`
1.489→**1.4091**, joint `f.insuranceOther_None` 1.180→**1.1078**, joint
`f.employmentStudent` lower bound 1.0583→**1.0503**.

## eTable 10 — cross-site comparison, both columns final

26 estimates are comparable (sex, vaccination, 3 age strata, 2 wave indicators,
19 Charlson). **21 concordant, 5 discordant**: peripheral vascular disease, chronic
pulmonary disease, peptic ulcer disease, mild liver disease, AIDS. The caption's old
sentence ("Twenty of the 25 comparable estimates were concordant") is replaced by
twenty-one of 26.

The full table is in `etable10_full.md` next to this file.

Note for the caption: the Omicron row counts as concordant only because the All of Us
point estimate is 0.9998. Say so, or the criterion looks stronger than it is.

## Control reuse — eTable 11

Post-trim (the number the text should use): **15,523 control observations from 9,784
unique individuals, maximum reuse 10**. Pre-trim, from `07b_control_reuse.csv`:
15,960 rows, 10,032 unique, median 1 (IQR 1–2), max 10, 0 cases dropped.
v18.6 printed 9,691 unique and max reuse 13 — both wrong now.

## Table 3 — domain-specific column (all from `all_model_coefficients.csv`)

insurance: Medicare 1.152 (1.014–1.309) · Medicaid 1.536 (1.380–1.710) · other/none
1.328 (1.146–1.538) · missing 0.981 (0.864–1.114)
income: <10k 1.505 (1.326–1.708) · 10–25k **1.4091 (1.2439–1.5962)** · 25–35k 1.176
(1.012–1.367) · 100–150k 1.170 (1.002–1.368) · 150–200k 1.206 (0.971–1.498) · >200k
1.088 (0.887–1.336) · missing 1.710 (1.529–1.912)
employment: student 1.4779 (1.1395–1.9168) · unemployed 1.547 (1.398–1.711) · others
1.398 (1.254–1.557) · missing 1.340 (1.069–1.682)
housing: rent 1.282 (1.175–1.400) · other 1.129 (0.980–1.300) · missing 1.252
(1.032–1.520) · unstable 1.002 (0.908–1.105) · stability missing 1.328 (0.999–1.764)
education: below GED 1.290 (1.130–1.474) · GED/college 1.107 (1.015–1.206) · missing
1.564 (1.223–2.000)

Product of the three profile domains (Medicaid × 10–25k × rent) = **2.77** (was 2.79).

## Table 3 — joint column

income: <10k 1.211 (1.046–1.402) · 10–25k 1.205 (1.053–1.380) · 25–35k 1.096
(0.939–1.280) · 100–150k 1.213 (1.035–1.421) · 150–200k 1.258 (1.008–1.569) · >200k
1.147 (0.930–1.415) · missing 1.489 (1.318–1.681)
insurance: Medicare 0.982 (0.855–1.128) · Medicaid 1.193 (1.047–1.360) · other/none
**1.1078 (0.9455–1.2980)** · missing 0.833 (0.725–0.956)
education: below GED 1.0602 (0.9191–1.2229) · GED/college 1.0110 (0.9200–1.1100) ·
missing 1.2825 (0.9950–1.6533)
employment: student **1.368043 (1.050294–1.781921)** · unemployed 1.3501
(1.1984–1.5211) · others 1.2837 (1.1422–1.4427) · missing 1.1030 (0.8694–1.4015)
housing: rent 1.1613 (1.0542–1.2792) · other 0.9785 (0.8410–1.1384) · missing 1.0169
(0.8262–1.2517) · unstable 0.9085 (0.8191–1.0076) · stability missing 1.1832
(0.8819–1.5875)
disability: any 0.9235 (0.8077–1.0560) · missing 1.0015 (0.9071–1.1058)

## eTable 15 — sensitivity, partial

S2 clean controls: unemployed 1.2114 (1.0743–1.3659) · rent 1.1573 (1.0497–1.2760)
S3 pre-index surveys: income<10k 1.1293 (0.9665–1.3195) · 10–25k 1.1862
(1.0270–1.3700) · Medicaid 1.4353 (1.2435–1.6567) · rent 1.0895 (0.9809–1.2102)
S4 no vaccination: income<10k 1.1995 (1.0398–1.3838) · 10–25k 1.1975 (1.0454–1.3717)
· Medicaid 1.3005 (1.1427–1.4802) · unemployed 1.2539 (1.1158–1.4092) · rent 1.1333
(1.0302–1.2468)
S5 income collapsed: Medicaid 1.3302 (1.1686–1.5141) · unemployed 1.2384
(1.1036–1.3897)

**Not captured, must be re-read:** all of S1 (inpatient-only cases); the S5 collapsed
income level (its variable name is not `f.incomeless_35k`, so the filter missed it);
S3 unemployed and S5 renting, which failed the symmetry check and are therefore
unsafe as read.

---

# Education: the below-20 category (decided 2026-09-02)

**Not merged.** The model keeps `Never_Attended` as its own level. Merging it into
`Below_GED` would have meant rerunning `02_models.R`, which overwrites the bucket
prefix every number in this manuscript was read from and verified against — a full
re-verification, to relocate 34 participants out of 19,520 observations. Keeping the
category separate also keeps the 2,208-participant `Below_GED` estimate from
absorbing 34 extreme cases.

The factor as it stands, from `02_models.R`:
`levels = c("Advanced","Never_Attended","Below_GED","GED_or_College","Missing")`,
reference `Advanced`.

**Rules to apply when the artefacts are rebuilt:**

1. **Table 2, education block.** Do not print a `Never attended school` row. Count
   those participants inside the `Below high school or GED` row so the block sums to
   N. The caption already says this. Reason: the policy forbids a count under 20 *and*
   any count from which one could be derived — with the row simply removed, the
   residual against the column total is the suppressed count. In the v18.6 table it
   comes out as exactly 16 cases and 18 controls by subtraction, so the current
   submission copy is already non-compliant.
2. **Table 3 and Figure 4.** Do not show the `Never_Attended` estimate. Filter
   `f.educationNever_Attended` out of the plotting frame in `05_figures.py`.
3. **Main text.** One sentence in the domain-specific paragraph says the category was
   carried in the models and is not reported. No estimate, no count. Already written.
4. **eTable.** If the estimate is wanted anywhere, an eTable may carry the AOR and
   interval — the policy governs participant counts, not coefficients — but never the
   count, and never a total from which the count follows. Default is to omit it.
