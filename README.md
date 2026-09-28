# Income, Insurance, and Respiratory Viral Hospitalization

Propensity-matched case-control analysis of survey-derived social determinants and
hospitalization after COVID-19 (CDR v7, 3 waves) and influenza (CDR v9, seasons before,
during, and after the pandemic) in the NIH *All of Us* Research Program, with a
clinical-model comparison in Merative MarketScan Commercial Claims.

Manuscript in preparation for *JAMA Network Open* (retargeted from *JAMIA*).
The influenza-arm scripts are in `flu_arm/`; see `flu_arm/README.md` for the one
extraction step whose script was not retained. The R10 phenotype, capture, and
absolute-scale checks are `03z_*.py`, `03z_*.R`, and `03w_sens.R` with `SPART=R10`.

## Status

**2026-09-02 — pre-index matching-variable correction.** The propensity model
originally measured its matching variables over each participant's whole record,
including the hospitalization itself, so the outcome leaked into the matching.
`01_aou_etl.py` STEP 6 now restricts them to records dated before the index date
(`223f715`). Every downstream number changed: the All of Us cohort went from
4,064/15,856 to 3,997/15,523, and the MarketScan matched set from 693,682 to
637,679 observations.

**Any output produced before that commit is invalid**, and identifying which is
which takes more than a timestamp. Four times during the reconciliation a file sat
at the right path with a fresh mtime and held pre-correction values, because a sync
had copied an old bucket object over it. Check artifacts by content: the corrected
All of Us base model reads female 0.768, Black race 2.387, chronic pulmonary 0.904,
and the joint SDoH model reads Medicaid 1.193, unemployment 1.350. Note that
`analysis/validate_numbers.py` and `analysis/gate.sh` resolve artifacts by path, so
they will pass a stale file without complaint.

Headline results are deliberately not repeated here — they go stale, and a stale
number in a repository is read as a current one. The manuscript is the source.

## Repository layout

Everything in this repository is production code. The manuscript package, the
project record and superseded code are local-only and untracked; see
`.gitignore` for what and why.

```
01-08*, 03*             the pipeline, in run order (flu_arm/ for influenza)
analysis/               validate_v25.py (asserts every printed number) and
                        CLAIM_LEDGER_v25.md, generated from it
figures/                the code that draws every current figure
results/figures/v25/    what the main figures draw (local only until screened)
working/v25/            manuscript sources and build (local only)
submission_v25/         the current package: .docx, PDF, figures (local only)
archive/                earlier versions, reviews, superseded code (local only)
```

## Pipeline

```
DATA (01*)                            on-platform, person-level
  01_aou_etl.py                       AoU ETL (BigQuery -> CSV)
  01_ms_etl.py                        MarketScan ETL (DuckDB -> CSV)
  01b_psm.R                           PSM via MatchIt + cobalt balance
  01c_sensitivity_etl.py              Sensitivity flags (BQ, AoU only)

MODELS (02*, 03)                      on-platform, reads CSV
  02_models.R                         Base + per-domain + joint + race attenuation
  02b_variance_sensitivity.R          Efron refit + cluster-robust SEs
  02c_wave_stratified_race_insurance.R  Within-wave race and Medicaid models
  02d_wave_interaction.R              Pooled exposure-by-wave interaction tests
  03_sensitivity.R                    Reviewer sensitivity S1-S5 (AoU only)
  03b_income_mi.R                     Multiple imputation of the survey items
  03c_employment_split_and_flu_wald.R Employment split; influenza Wald tests

TABLES (04, 06-08)                    04 on-platform; the rest off-platform
  04_tables.py                        Table 1 (demographics), Table 2 (SDoH)
  05_figures.py                       table3_sdoh_summary.csv, the cross-site
                                      comparison, CONSORT counts.  Its figure
                                      output is superseded -- see below
  06_supplement.py                    Supplementary eTables
  07_build_tables_docx.py             Table 1 and the MarketScan eTable as .docx
  08_build_maintext_tables.py         Tables 1-3 in one house style
  06b_ms_balance_medians.py           eTable 8 post-matching medians (Quartz)

FIGURES                               off-platform, from aggregate values
  figures/style.py                    shared style, palette, export
  figures/fig1_hero_v26.py            Figure 1
  figures/fig2_v26.py                 Figure 2
  figures/efig1_flow.py               eFigure 1, from efig1_consort_three_panel.drawio
  figures/efig2_phenotype_tree.py     eFigure 2
  figures/efig3_missing_indicator.py  eFigure 3
  figures/efig4_marketscan.py         eFigure 4
  figures/efig5_balance.py            eFigure 5
  figures/efig6_calendar.py           eFigure 6
  figures/efig7_flu_split.py          eFigure 7
  figures/efig8_income_shape.py       eFigure 8

CHECKS                                off-platform
  analysis/validate_v25.py            check | displays | ledger
```

## Which figure comes from what

Every figure is drawn from aggregate values, never from rows. The scripts above
name the frozen run each value was read from. The figures of earlier versions
(the JAMIA draft, v23, v24) and their scripts are in `archive/`.

## Reproduction

```bash
# -- All of Us (Researcher Workbench) --------------------------------
python  01_aou_etl.py v7                      # cohort -> matching variables
Rscript 01b_psm.R aou_v7                      # PSM -> matched cohort + balance
Rscript 02_models.R aou_v7                    # base, per-domain, joint, attenuation
Rscript 02b_variance_sensitivity.R aou_v7     # eTable 10b Panel A
Rscript 02c_wave_stratified_race_insurance.R aou_v7   # eTables 11b, 11c
Rscript 02d_wave_interaction.R aou_v7         # wave interaction tests
python  01c_sensitivity_etl.py v7             # sensitivity flags
Rscript 03_sensitivity.R aou_v7               # S1-S5
python  04_tables.py aou_v7                   # Tables 1, 2

# -- MarketScan (Quartz) --------------------------------------------
sbatch ms_resume_from_psm.sbatch               # ETL -> PSM -> models -> Table 1
sbatch ms_variance_sensitivity.sbatch          # eTable 10b Panel B

# -- Figures, tables, supplement (anywhere, from aggregate values) ---
# the manuscript itself: working/v25/build_all.sh (local only)
python  figures/fig1_hero_v26.py                # and the other scripts under FIGURES
python  05_figures.py                          # tables and CONSORT counts only
python  06_supplement.py
python  08_build_maintext_tables.py
```

Quartz jobs carry their own module and library-path preamble; `r/4.5.1` is only
offered under `gnu/9.3.0`, whose `libstdc++` lacks the symbol its bundled Rcpp
needs, so both scripts preload a newer one scoped to R. Both also refuse to run
if the input is not the corrected cohort.

## Data policy

`results/` is **local-only by default** (`a0b2add`, `8c0b56d`). It previously
held 81 aggregate files in the public tree, with person-level files kept out by
care rather than by rule — one `git add results/` away from a disclosure.

Two things in it are published, named explicitly in `.gitignore` rather than
force-added: `results/RUN.json` and `results/SCREENING.md`. The earlier
screened figure files were withdrawn on 2026-09-28 when they were superseded.
They were screened against the under-20 rule before they were first committed and
the screen is `results/SCREENING.md`. Model fits, matched cohorts and balance
tables are not published; they stay in the Workbench workspace bucket and on
Quartz.

Analysis runs where the data lives. Aggregate output — coefficients, intervals,
balance tables, counts of 20 or more — may be read off the platform; rows are not
brought down to be analysed elsewhere. All of Us also forbids publishing any
participant count below 20, or any set of counts from which such a count can be
derived by subtraction, which is what governs the collapsed education stratum in
Table 2.

<details>
<summary>File I/O contract</summary>

### 01_aou_etl.py -> results/aou_{v7|v8}/
| Output | Description |
|---|---|
| `01_covid_cohort.csv` | person_id, covid_index_date, severity, severity_broad, pandemic_wave |
| `01b_phenotype_components.csv` | visit-type decomposition (aggregate) |
| `02_demographics.csv` | sex_at_birth, race, ethnicity, age_group, age_at_covid |
| `03_charlson.csv` | 19 Charlson + AIDS binary flags |
| `04_sdoh.csv` | 6 SDoH domains + insurance type |
| `04b_sdoh_timing.csv` | basics_survey_date, sdoh_days_before_covid, sdoh_pre_index |
| `05_vaccination.csv` | person_id, vaccination |
| `06_matching_variables.csv` | survey_ord, num_diagnosis, ehr_length_days (pre-index only) |

### 01_ms_etl.py -> results/ms/
| Output | Description |
|---|---|
| `01_covid_cohort.csv` | person_id, covid_index_date, severity, severity_broad, pandemic_wave |
| `02_demographics.csv` | sex_at_birth, race, ethnicity, age_group, plan_type, region_name |
| `03_charlson.csv` | 19 Charlson + AIDS binary flags |
| `04_sdoh.csv` | person_id only (placeholder — MarketScan has no SDoH survey) |
| `05_vaccination.csv` | person_id, vaccination |
| `06_matching_variables.csv` | enrollment_ord, num_diagnosis, coverage_span_days (pre-index only) |

### 01b_psm.R -> results/{cohort}/
| Output | Description |
|---|---|
| `07_matched_cohort.csv` | person_id, Treatment, stratum (before the follow-up trim) |
| `07b_control_reuse.csv` | reuse statistics (eTable 10) |
| `07c_smd_pre_matching.csv` | pre-matching SMDs, matching variables |
| `07d_smd_post_matching.csv` | post-matching SMDs, full covariates |
| `07e_matchit_summary.txt` | MatchIt audit trail |
| `08_regression_base.csv` | analytic file: matched + demographics + Charlson + vaccination + wave |
| `efig_love_plot_{cohort}.pdf` | Love plot (cobalt) |

### 01c_sensitivity_etl.py -> results/aou_{v7|v8}/
| Output | Description |
|---|---|
| `09a_case_visit_components.csv` | per-case IP/ER/ED flags |
| `09b_control_ed_flags.csv` | per-control acute-care flags |
| `09c_responder_vs_nonresponder.csv` | survey responder comparison |
| `09d_income_collapsed.csv` | three-level income |

### 02_models.R -> results/{cohort}/
| Output | Description |
|---|---|
| `base_model_coefficients.csv` | model A |
| `{domain}_coefficients.csv` | models B, one per SDoH domain |
| `joint_sdoh_coefficients.csv` | model C — also the comparison row in 03_sensitivity.R |
| `race_attenuation_table.csv` | eTable 11a |
| `wave_stratified_income.csv` | eTable 12 |
| `aids_sensitivity.csv` | HIV/AIDS phenotype comparison |
| `all_model_coefficients.csv` | combined |

### 02b / 02c / 02d -> results/{cohort}/
| Output | Description |
|---|---|
| `variance_sensitivity_etable11b.csv` | eTable 10b — exact vs cluster-robust intervals |
| `wave_stratified_race.csv` | Black-race AOR per wave, base and joint |
| `wave_stratified_insurance.csv` | Medicaid AOR per wave, domain-specific |
| `wave_stratified_race_attenuation.csv` | eTable 11b |
| `wave_joint_sdoh_{wave}_coefficients.csv` | full within-wave joint model — eTable 11c |
| `wave_interaction_tests.csv` | omnibus exposure-by-wave tests |
| `wave_interaction_contrasts.csv` | pre-specified contrasts (Figure 5) |

### 03_sensitivity.R -> results/aou_{v7|v8}/
| Output | Description |
|---|---|
| `sensitivity_S1-S5_*.csv` | five sensitivity model coefficient sets |
| `sensitivity_summary_comparison.csv` | eTable 13 |

</details>

## Design

| | All of Us | MarketScan |
|---|---|---|
| Source | Controlled Tier v7, C2022Q4R13 | Commercial Claims 2020–2023 |
| Outcome | 14-day strict hospitalization (IP + ER-to-IP + ED ≥ 1 day) | inpatient claim with U07.1 ≤ 14 days |
| Matching | 1:4 nearest neighbour, with replacement, 0.2 SD caliper (MatchIt) | same |
| PS covariates | survey date, diagnosis count, EHR length — all pre-index | enrollment date, diagnosis count, coverage span — all pre-index |
| Analysis | conditional logistic regression (`survival::clogit`, exact) | same |
| Race and ethnicity | in the base model | not captured |
| SDoH | six domains, entered singly and jointly | plan type and region only |
| Charlson | Glasheen 2019 CDMF CCI, 19 conditions | same code sets |
| Pandemic wave | pre-Delta / Delta / Omicron covariate | same |
| Role | primary analysis | clinical-model comparison |

## Requirements

```
Python  3.10                      R  4.5.1
  pandas      2.3.3                 survival   3.8.3
  numpy       1.26.4                MatchIt    4.7.2
  matplotlib  3.7.3                 cobalt     4.6.2
  duckdb      1.4.3                 dplyr      1.1.4
  python-docx 1.1.2                 readr      2.1.5
                                    sandwich   3.1.1
                                    lmtest     0.9.40
```

## License

[MIT](LICENSE)

## Contact

- [Jing Su](mailto:su1@iu.edu) — general questions
- [Haining Wang](mailto:hw56@iu.edu) — reproduction

Su Lab in Biomedical Informatics, Biostatistics & Health Data Science ·
Indiana University School of Medicine
