# JAMIA v18.5 — Round 3, verified against the repo

Source of truth: `Su-informatics-lab/aou_covid` (GitHub `17f3d00`) and the local working
copy at `~/Desktop/github/aou_covid`. The results CSVs are identical in both.

Every item below is now marked **CONFIRMED** (repo disagrees with the manuscript),
**REFUTED** (I was wrong in Round 3 draft 1), or **INTERPRETATION** (numbers agree with the
repo; the problem is what the text says about them).

Written in ASD-STE100 Simplified Technical English.

---

## I WAS WRONG ABOUT TWO ITEMS

### REFUTED — eTable 12a percentages

I said the attenuation percentages cannot be reproduced from the printed AORs.
`results/aou_v7/race_attenuation_table.csv` holds the unrounded values (base AOR
2.297423). Apply the stated formula to those: +Housing gives 8.3%, +Education 5.6%,
+Employment 3.3%. Every value reproduces exactly.
**eTable 12a is correct. No change is needed.**

### REFUTED (direction inverted) — eFigure 1 against eTable 6 and eTable 8

I said eFigure 1 was wrong. The opposite is true. See CONFIRMED-6 below.
**eFigure 1 is correct. eTable 6, eTable 8, eMethod, and main text line 81 are wrong.**

---

## CONFIRMED — the repo contradicts the manuscript

### C1. Table 1, MarketScan column: 29 of 29 cells are wrong

I rebuilt Table 1 with the repo's own script (`08_build_maintext_tables.py`, which reads
`results/ms/table1_demographics.csv`) and compared it with the manuscript.

* **The AoU column matches the repo exactly.** Zero differences.
* **The MarketScan column differs in every populated cell.**
* The manuscript's column body sums to 139,472 cases and 557,888 controls.
  `results/ms/07b_control_reuse.csv` records `n_control_rows = 557,888` as the **pre-trim**
  matched set. The manuscript's Table 1 is the pre-trim set with a post-trim N row.
* The comorbidity rows are also **pre-index-restriction** counts. See
  `results/ms/probe_charlson_preindex_comparison.csv`.

The direction faults I flagged are real and this is their cause:

| Row | Manuscript | Repo (correct) |
|---|---|---|
| Chronic pulmonary disease | 38,472 (27.6) / 140,660 (25.2) | **18,418 (13.2) / 92,037 (16.6)** |
| Liver disease, mild | 20,199 (14.5) / 53,984 (9.7) | **7,881 (5.7) / 38,981 (7.0)** |
| Rheumatic disease | 5,510 (4.0) / 15,310 (2.7) | **3,604 (2.6) / 20,162 (3.6)** |
| Peptic ulcer disease | 2,848 (2.0) / 7,122 (1.3) | **1,174 (0.8) / 6,366 (1.1)** |
| Malignancy | 7,196 (5.2) / 20,042 (3.6) | **4,951 (3.5) / 19,657 (3.5)** |
| Cerebrovascular disease | 9,969 (7.1) / 49,340 (8.8) | **4,215 (3.0) / 17,307 (3.1)** |
| Myocardial infarction | 9,080 (6.5) / 24,032 (4.3) | **2,729 (2.0) / 7,733 (1.4)** |

With the repo values, every crude direction agrees with the MarketScan AOR in eTable 10.

Three more differences outside the comorbidity block:

* Female: 67,916 / 377,888 → **67,914 / 375,330**
* Vaccination "Recorded before index": 109,739 (19.7) → **108,286 (19.5)**
* Sex "Other" for MarketScan: manuscript says NA; the repo says **`<20`** (a suppressed
  small cell, not an absent field). Table 1 footnote a must change.

**Fix:** run `python 08_build_maintext_tables.py` and paste the generated Table 1.
The corrected MarketScan column is in the appendix of this document.

### C2. eTable 14 reports a null result as significant

`results/tables/eTable_S14_aids_sensitivity.csv` and
`results/aou_v7/aids_sensitivity.csv`:

| Row | Manuscript eTable 14 | Repo |
|---|---|---|
| Two-step (HIV+OI), AoU | 0.74 (0.56–0.98), **P = 0.03** | **0.76 (0.57–1.02), P = 0.068, NS** |
| HIV alone, AoU | 1.00 (0.69–1.45), NS | **0.96 (0.68–1.38), NS** |
| Two-step, MarketScan | 1.59 (1.38–1.83) | **no MarketScan column exists** |
| HIV alone, MarketScan | 1.17 (1.04–1.31) | **no MarketScan column exists** |

* The repo's AoU AIDS estimate is **0.76 (0.57–1.02), P = 0.068**. It is not significant.
  It also equals eTable 10, so the two tables do agree in the repo.
* The values 1.59 and 1.17 occur nowhere in the repo. The MarketScan base model gives
  **AIDS 1.27 (1.03–1.58)** and **HIV 0.86 (0.76–0.96)** (`results/ms/base_model_coefficients.csv`).
* The eTable 14 caption states the phenotype "produced a significant inverse association in
  AoU (AOR 0.74, P = 0.034)". **This claims significance for a result with P = 0.068.**

**Fix:** replace eTable 14 with the repo output. Delete the MarketScan column or fill it
from `results/ms/base_model_coefficients.csv`. Rewrite the caption and Discussion line 425.

### C3. The predicted probability of 1.31 is computed incorrectly

`02_models.R` lines 384–389:

```r
lp_a <- predict(joint_fit, newdata = pa, type = "lp")
lp_b <- predict(joint_fit, newdata = pb, type = "lp")
prob_a <- mean(1 / (1 + exp(-lp_a)), na.rm = TRUE)
prob_b <- mean(1 / (1 + exp(-lp_b)), na.rm = TRUE)
ratio  <- prob_b / prob_a
```

* `joint_fit` is a conditional logistic model. For `coxph`/`clogit`, `type = "lp"` returns a
  linear predictor that is **centered on the covariate means and has no intercept**.
* The code applies the inverse logit to that centered value. The output looks like a
  probability but is not one. The stored values are 0.438 and 0.573
  (`results/aou_v7/predicted_probability_contrast.csv`). A 43.8% baseline hospitalization
  probability is an artifact of the centering.
* The ratio 1.307 is compressed because the inverse logit is flattest near 0.5.
* The quantity the model does identify is the odds ratio for the profile contrast:
  `exp(lp_b − lp_a)` = **about 1.72**.
* Line 417 uses the 1.31 to argue the combined association is "more modest than
  multiplying separate domain-specific AORs would imply". That argument is an artifact of
  the flawed transformation, not a finding. The joint AORs do multiply to about 1.72.

**Fix:** report the odds ratio (about 1.72), or delete both sentences. This is a code
fault, so it must be corrected in `02_models.R` as well.

### C4. Every pre-matching SMD in eTable 6, eTable 8, eMethod and line 81 is wrong

MatchIt writes its own summary. `results/aou_v7/07e_matchit_summary.txt` and
`results/ms/07e_matchit_summary.txt`:

| Value | Manuscript | Repo (MatchIt) |
|---|---|---|
| AoU, number of diagnoses, pre | 0.554 | **0.489** |
| AoU, enrollment date, pre | −0.087 | **−0.092** |
| AoU, enrollment date, post | 0.011 | **0.025** |
| MarketScan, number of diagnoses, pre | 0.700 | **0.613** |
| MarketScan, enrollment date, pre | −0.245 | **−0.280** |

* **eFigure 1 plots 0.49 and 0.61. eFigure 1 is the correct artifact.**
* Line 81, eTable 6, eTable 8, and eMethod all carry 0.554 and 0.700. Those values do not
  exist in the repo.
* eMethod's "reduced from 0.554 to 0.006 (99% reduction)" must become 0.489 to 0.006.
* eTable 7a still passes its own claim: post-matching enrollment 0.025 is below 0.03.

### C5. Figure 3 shows 17 of 19 comorbidities, by design, and the legend describes a different figure

`make_figures.py`, constant `FIG3`, hardcodes 17 comorbidities. **Myocardial infarction and
peripheral vascular disease are deliberately excluded.** All 17 values match
`results/tables/eTable_S10_crosssite.csv` exactly, so the figure is internally correct.

* The Figure 3 alt text says "19 Charlson comorbidities". It shows 17.
* The Figure 3 legend describes a vermillion / blue / grey scheme keyed to significance.
  The figure is keyed to cohort (blue = AoU, orange = MarketScan). The legend and alt text
  belong to an earlier figure.
* `FIG3` includes the MarketScan Delta and Omicron wave AORs. Table 1 footnote a says
  wave "was not tabulated for MarketScan". The footnote is wrong.

### C6. eTable 10 in the manuscript drops 5 rows that the repo has

`results/tables/eTable_S10_crosssite.csv` has 30 rows. The manuscript prints 25.
Missing: **Asian race, Other race, Hispanic, Myocardial infarction, Peripheral vascular
disease.** Both omitted comorbidities are concordant (MI: 0.93 against 0.94;
PVD: 0.92 against 0.86), so including them raises the concordance count. The caption does
not say the table is a subset.

### C7. eTable 11b Panel A drops 10 rows that the repo has

`results/aou_v7/variance_sensitivity_etable11b.csv` has 32 rows. The manuscript prints 22.
Missing: MI, PVD, rheumatic disease, peptic ulcer, DM without complications, DM with
complications, hemiplegia, renal mild/moderate, malignancy, ethnicity "Other".
**The two largest CI ratios in the file are among the dropped rows** (rheumatic 1.10;
MI 1.05). The caption does not say the panel is a subset.

### C8. Table 2 housing tenure: the shortfall is a real pipeline fault

`results/aou_v7/table2_sdoh.csv` has the same shortfall as the manuscript:
Own + Rent + Others + Missing = 4,063 (cases) and 15,851 (controls), against N of 4,064
and 15,856. The manuscript transcribed the CSV correctly. **The pipeline is losing 1 case
and 5 controls.**

The same file also has a **duplicate "Missing" row under Insurance type**:

```
  Missing,558,(13.7),"2,684",(16.9)
  Missing,<20,,<20,
```

The manuscript prints only the first. This is the string-`"Missing"` against `NaN`-missing
split. Housing loses its people; insurance emits them as a second row. **Fix the ETL, then
regenerate Table 2.**

### C9. eTable 11 mixes pre-trim and post-trim counts

`07b_control_reuse.csv` gives pre-trim values: AoU 9,928 unique / 16,244 rows;
MarketScan 465,670 unique / 557,888 rows.

* AoU in the manuscript: 9,691 unique / 15,856 rows. Both post-trim. Consistent, but
  9,691 is in no committed file.
* MarketScan in the manuscript: **465,670 unique (pre-trim) with 554,214 rows (post-trim)**.
  The pair does not belong together.

### C10. Effective sample size is never reported

MatchIt reports `Matched (ESS)`: **AoU controls 6,952.4**, MarketScan controls 379,100.2.
The manuscript reports 15,856 and 554,214 control observations throughout. Matching with
replacement inflates the apparent sample. The ESS is the honest measure of precision and
appears nowhere.

---

## INTERPRETATION — the numbers match the repo; the text does not match the numbers

These are not transcription faults. The repo confirms every value. The problem is what the
manuscript says about them.

* **Delta wave is omitted from the whole narrative.** `make_figures.py` constant
  `RACE_WAVE` holds `("Delta", 644, 2.98,1.79,4.96, 2.17,1.21,3.89, 29.1)`. The series is
  11.5% → **29.1%** → 30.1%, and the Delta base AOR (2.98) equals pre-Delta (3.00). The
  strings "29.1" and "2.98" appear nowhere in the main text, although Figure 5b prints
  −29.1%. The claim of a rise across waves rests on the two endpoints.
* **The income pattern is not monotone.** `table3_sdoh_summary.csv` confirms joint AORs of
  1.24** for $100–150K and 1.26* for $150–200K against 1.18* for <$10K. The Abstract and
  the Conclusions say "lower income".
* **eTable 13 confirms pre-Delta $100–150K = 1.41 (1.07–1.86), P = 0.02**, larger than
  $10–25K in the same wave. `INCOME_WAVE` in `make_figures.py` limits Figure 5a to the
  three lowest strata by design. That is a valid choice, but the legend must say so.
* **Figure 5a's own significance flags contradict the Figure 5 legend.** `INCOME_WAVE`
  marks Delta $10,000–24,999 as `""` (not significant). The legend says "The two lowest
  strata remained elevated in every wave."
* **S3 sensitivity.** `eTable_S16_sensitivity.csv` confirms income <$10K 1.129
  (0.966–1.319) and renter 1.090 (0.981–1.210). Swapping standard errors between the
  primary and S3 fits shows the point estimates moved to the null; the width did not cause
  the change. Line 389 attributes it to sample size.
* **Cross-cohort discordance.** eTable 10 flags 5 "No" rows. Line 393 reports 2. The
  largest omission is Omicron wave (AoU 1.04 against MarketScan 0.47).
* **Housing "Other" 0.86 (0.74–1.00) with an asterisk** comes from the pipeline. It is a
  display-precision issue, not a transcription error. Print three decimals, or state the
  rounding rule. Line 371 also never reports this level, although it becomes significant.
* All remaining Round 3 items on citations (refs 14, 25, 31, 39, 42), on Choi et al.'s
  design, on the Delta strata loss, on the corrupted corporate authors, and on the word
  limits are unchanged. None of them depend on the repo.

---

## REPRODUCIBILITY GAP

`02c_wave_stratified_race_insurance.R` writes `wave_stratified_race.csv`,
`wave_stratified_insurance.csv`, and `wave_stratified_race_attenuation.csv`.
**None of the three is committed.** Only `wave_stratified_income.csv` is present.

So eTable 12b and eTable 12c cannot be verified from any model output. Their values survive
only as hardcoded constants inside `make_figures.py`. The Data Availability statement points
reviewers at this repo. Commit the three CSVs.

---

## FIX ORDER

1. Regenerate Table 1 (`08_build_maintext_tables.py`). 29 cells.
2. Replace eTable 14 with the repo output. Remove the "significant" claim.
3. Correct the predicted-probability calculation in `02_models.R`. Report about 1.72, or
   delete the sentence at line 375 and the argument at line 417.
4. Correct the SMD values in eTable 6, eTable 8, eMethod, and line 81.
5. Rewrite the Figure 3 legend and alt text. State the 17-of-19 selection.
6. Fix the housing-tenure and insurance leaks in the ETL. Regenerate Table 2.
7. Restore the dropped rows in eTable 10 and eTable 11b, or declare the subsets.
8. Add the Delta wave to the temporal narrative.
9. Correct refs 14, 25, 42; fix refs 1, 2; correct the Choi et al. design description.
10. Cut the main text to 4,000 words and the abstract to 250.

---

## APPENDIX — corrected MarketScan column for Table 1

```
Row                                        Cases            Controls
N                                        139,468             554,214
Female                             67,914 (48.7)      375,330 (67.7)
Male                               71,554 (51.3)      178,884 (32.3)
Other                                        <20                 <20
<45                                53,369 (38.3)      284,866 (51.4)
45–54                              37,833 (27.1)      130,590 (23.6)
55–64                              47,908 (34.4)      137,688 (24.8)
≥65                                    358 (0.3)         1,070 (0.2)
Mean age (s.d.)                      45.6 (14.6)         41.2 (15.9)
Recorded before index               11,300 (8.1)      108,286 (19.5)
No record                         128,168 (91.9)      445,928 (80.5)
Myocardial infarction                2,729 (2.0)         7,733 (1.4)
Congestive heart failure             6,614 (4.7)        15,123 (2.7)
Peripheral vascular disease          5,866 (4.2)        20,464 (3.7)
Cerebrovascular disease              4,215 (3.0)        17,307 (3.1)
Dementia                               769 (0.6)         2,202 (0.4)
Chronic pulmonary disease          18,418 (13.2)       92,037 (16.6)
Rheumatic disease                    3,604 (2.6)        20,162 (3.6)
Peptic ulcer disease                 1,174 (0.8)         6,366 (1.1)
Liver disease, mild                  7,881 (5.7)        38,981 (7.0)
Liver disease, moderate/severe         889 (0.6)         1,984 (0.4)
Diabetes without complications     19,085 (13.7)        52,613 (9.5)
Diabetes with complications         11,696 (8.4)        26,591 (4.8)
Hemiplegia or paraplegia             1,460 (1.0)         3,423 (0.6)
Renal disease, mild/moderate         6,199 (4.4)        15,289 (2.8)
Renal disease, severe                2,816 (2.0)         3,855 (0.7)
HIV                                    444 (0.3)         1,610 (0.3)
Metastatic solid tumor               2,295 (1.6)         6,099 (1.1)
Malignancy                           4,951 (3.5)        19,657 (3.5)
AIDS                                   127 (0.1)           393 (0.1)
```

Race, ethnicity, and pandemic wave stay NA in Table 1. Note that Figure 3 and eTable 10 do
report MarketScan wave AORs, so footnote a must say that wave was modelled but not
tabulated.
