# COVID-19 Hospitalization × Social Determinants of Health

Propensity-matched case-control analysis of survey-derived SDoH and COVID-19
hospitalization in the NIH *All of Us* Research Program, with a clinical-model
comparison in Merative MarketScan Commercial Claims.

Manuscript in preparation for *JAMIA* (Research and Applications).

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
01-08*                  the pipeline, in run order
analysis/               number checks: validate_numbers.py, ledger.py, gate.sh
figures/                the code that draws every figure in the manuscript
results/figures/        what each figure draws: one CSV per figure, and the
                        figure itself.  Screened; see results/SCREENING.md
results/                everything else in it is local only
submission/             the manuscript package (local only)
archive/                project record, drafts, superseded code (local only)
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
  figures/fig1_domain_vs_joint.py     Figure 1
  figures/fig2_era.py                 Figure 2
  figures/fig3_covid_vs_flu.py        Figure 3
  figures/fig4_race_attenuation.py    Figure 4
  figures/efig2_balance.py            eFigure 2
  figures/efig3_visits.py             eFigure 3
  figures/efig5_clinical_check.py     eFigure 5
  figures/export_source_data.py       writes results/figures/*_data.csv
  eFigure 1 (participant flow) and eFigure 4 (phenotype decision tree) are
  draw.io diagrams; their sources live with the submission package.

CHECKS                                off-platform
  analysis/validate_numbers.py        assert manuscript values against outputs
  analysis/ledger.py                  generate the claim ledger from those asserts
  analysis/gate.sh                    run the chain
```

## Which figure comes from what

Every figure is drawn from aggregate values, never from rows. Each script carries
those values as literals with the frozen run they were read from, and
`export_source_data.py` writes them out, so the CSV in `results/figures/` is by
construction the numbers the figure draws.

| Figure | Script | Values |
|---|---|---|
| Figure 1. Test 1. Domain-specific against jointly adjusted | `figures/fig1_domain_vs_joint.py` | `results/figures/Figure1_data.csv` |
| Figure 2. Test 2. What changed across pandemic eras | `figures/fig2_era.py` | `results/figures/Figure2_data.csv` |
| Figure 3. Test 3. COVID-19 against influenza | `figures/fig3_covid_vs_flu.py` | `results/figures/Figure3_data_panel_a.csv`, `results/figures/flu/` |
| Figure 4. Test 4. What the five domains account for in the Black-race association | `figures/fig4_race_attenuation.py` | `results/figures/Figure4_data.csv` |
| eFigure 2. Matching balance | `figures/efig2_balance.py` | `results/figures/eFigure2_data.csv` |
| eFigure 3. Visit timing around the index date | `figures/efig3_visits.py` | `results/figures/eFigure3_data.csv` |
| eFigure 5. The clinical model in both cohorts | `figures/efig5_clinical_check.py` | `results/figures/eFigure5_data.csv` |
| eFigure 1, eFigure 4 | draw.io, sources with the submission package | — |

```bash
python figures/fig1_domain_vs_joint.py    # and the other six: each writes its
                                          # own PDF and PNG into results/figures
python figures/export_source_data.py      # regenerate every *_data.csv
```

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
python  figures/export_source_data.py          # every figure and every *_data.csv
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

Three things in it are published, named explicitly in `.gitignore` rather than
force-added: `results/figures/`, `results/RUN.json` and `results/SCREENING.md`.
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
