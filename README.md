# COVID-19 Severity × Social Determinants of Health

Propensity-matched case-control analysis of survey-derived SDoH and
COVID-19 hospitalization in the NIH *All of Us* Research Program,
with clinical-model transportability evaluation in Merative MarketScan
Commercial Claims.

## Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  DATA (01*)  — runs on-platform, person-level               │
├─────────────────────────────────────────────────────────────┤
│  01_aou_etl.py        AoU ETL (BigQuery → CSV)              │
│  01_ms_etl.py         MarketScan ETL (DuckDB → CSV)         │
│  01b_psm.R            PSM via MatchIt + cobalt balance       │
│  01c_sensitivity_etl.py  Sensitivity flags (BQ, AoU only)   │
├─────────────────────────────────────────────────────────────┤
│  MODELS (02–03)  — runs on-platform, reads CSV              │
├─────────────────────────────────────────────────────────────┤
│  02_models.R          Base + SDoH + joint + race attenuation │
│  03_sensitivity.R     Reviewer sensitivity S1–S5             │
├─────────────────────────────────────────────────────────────┤
│  OUTPUT (04–06)  — 04 on-platform; 05–06 off-platform       │
├─────────────────────────────────────────────────────────────┤
│  04_tables.py         Table 1 (demographics), Table 2 (SDoH) │
│  05_figures.py        Figures 3–5, Table 3, cross-site eTable │
│  06_supplement.py     All supplementary eTables (S2b–S16)    │
└─────────────────────────────────────────────────────────────┘
```

## Reproduction

```bash
# ── AoU (on Researcher Workbench) ──────────────────────────
python 01_aou_etl.py v7             # Steps 1–6: cohort → matching vars
Rscript 01b_psm.R aou_v7            # PSM (MatchIt) → matched cohort + balance
Rscript 02_models.R aou_v7          # Base + 6 SDoH domain + joint + wave-stratified
python 01c_sensitivity_etl.py v7    # Sensitivity flags (phenotype components, etc.)
Rscript 03_sensitivity.R aou_v7     # S1–S5 reviewer sensitivity analyses
python 04_tables.py aou_v7          # Table 1, Table 2

# ── MarketScan (on Quartz HPC) ─────────────────────────────
python 01_ms_etl.py                  # Steps 1–5: cohort → matching vars
Rscript 01b_psm.R ms                # PSM (MatchIt) → matched cohort + balance
Rscript 02_models.R ms              # Base model only (no SDoH surveys)
python 04_tables.py ms               # Table 1

# ── Figures & supplement (anywhere, from aggregate CSVs) ────
python 05_figures.py                 # Figs 3–5, Table 3, cross-site eTable
python 06_supplement.py              # All supplementary eTables (S2b–S16)
```

<details>
<summary>File I/O Contract (click to expand)</summary>

### 01_aou_etl.py → results/aou_{v7|v8}/
| Output | Description |
|---|---|
| `01_covid_cohort.csv` | person_id, covid_index_date, severity, severity_broad, pandemic_wave |
| `01b_phenotype_components.csv` | Visit-type decomposition (aggregate) |
| `02_demographics.csv` | sex_at_birth, race, ethnicity, age_group, age_at_covid |
| `03_charlson.csv` | 19 Charlson + AIDS binary flags |
| `04_sdoh.csv` | 6 SDoH domains + insurance type |
| `04b_sdoh_timing.csv` | basics_survey_date, sdoh_days_before_covid, sdoh_pre_index |
| `05_vaccination.csv` | person_id, vaccination |
| `06_matching_variables.csv` | enrollment_ord, num_diagnosis, ehr_length_days |

### 01_ms_etl.py → results/ms/
| Output | Description |
|---|---|
| `01_covid_cohort.csv` | person_id, covid_index_date, severity, severity_broad, pandemic_wave |
| `02_demographics.csv` | sex_at_birth, race, ethnicity, age_group, plan_type, region_name |
| `03_charlson.csv` | 19 Charlson + AIDS binary flags |
| `04_sdoh.csv` | person_id only (placeholder — MS has no SDoH surveys) |
| `05_vaccination.csv` | person_id, vaccination |
| `06_matching_variables.csv` | enrollment_ord, num_diagnosis, coverage_span_days |

### 01b_psm.R → results/{cohort}/
| Output | Description |
|---|---|
| `07_matched_cohort.csv` | person_id, Treatment, stratum |
| `07b_control_reuse.csv` | Reuse statistics |
| `07c_smd_pre_matching.csv` | Pre-matching SMDs (matching vars) |
| `07d_smd_post_matching.csv` | Post-matching SMDs (full covariates) |
| `07e_matchit_summary.txt` | MatchIt audit trail |
| `08_regression_base.csv` | Merged: matched + demo + Charlson + vacc + wave |
| `efig_love_plot_{cohort}.pdf` | Love plot (cobalt) |

### 01c_sensitivity_etl.py → results/aou_{v7|v8}/
| Output | Description |
|---|---|
| `09a_case_visit_components.csv` | Per-case IP/ER/ED flags |
| `09b_control_ed_flags.csv` | Per-control acute-care flags |
| `09c_responder_vs_nonresponder.csv` | Survey responder comparison |
| `09d_income_collapsed.csv` | 3-level income |

### 02_models.R → results/{cohort}/
| Output | Description |
|---|---|
| `base_model_coefficients.csv` | Model A |
| `{domain}_coefficients.csv` | Models B (one per SDoH domain) |
| `joint_sdoh_coefficients.csv` | Model C |
| `race_attenuation_table.csv` | Black AOR across specifications |
| `wave_stratified_income.csv` | Income × wave |
| `aids_sensitivity.csv` | HIV/AIDS phenotype comparison |
| `all_model_coefficients.csv` | Combined |

### 03_sensitivity.R → results/aou_{v7|v8}/
| Output | Description |
|---|---|
| `sensitivity_S1–S5_*.csv` | 5 sensitivity model coefficients |
| `sensitivity_summary_comparison.csv` | Side-by-side key AORs |

</details>

[//]: # (## Design)

[//]: # ()
[//]: # (| | AoU | MarketScan |)

[//]: # (|---|---|---|)

[//]: # (| **Source** | Controlled Tier v7 C2022Q4R13 | Commercial Claims 2020–2023 |)

[//]: # (| **Outcome** | 14-day strict hospitalization &#40;IP + ER-to-IP + ED≥1d&#41; | Inpatient claim with U07.1 ≤14 days |)

[//]: # (| **Matching** | 1:4 NN, replacement, 0.2 SD caliper &#40;MatchIt&#41; | Same |)

[//]: # (| **PS covariates** | Enrollment date, Dx count, EHR length | Enrollment date, Dx count, coverage span |)

[//]: # (| **Analysis** | Conditional logistic &#40;survival::clogit&#41; | Same |)

[//]: # (| **Race/ethnicity** | In base model | Not available |)

[//]: # (| **SDoH** | 6 domains: domain-by-domain &#40;B&#41; + joint &#40;C&#41; | Plan type + region only |)

[//]: # (| **Charlson** | Glasheen 2019 CDMF CCI, 19 conditions | Same codes |)

[//]: # (| **Pandemic wave** | Pre-Delta / Delta / Omicron covariate | Same |)

[//]: # (| **Framing** | Primary analysis | Clinical-model transportability |)

[//]: # (## Key Results &#40;AoU, strict 14-day phenotype&#41;)

[//]: # ()
[//]: # (- **Cohort:** 25,160 COVID+ → 4,064 hospitalized &#40;16.2%&#41; → 20,308 matched obs)

[//]: # (- **Income:** <$10K AOR 1.42 &#40;domain&#41;, 1.16 &#40;joint&#41;; gradient persists through Omicron)

[//]: # (- **Insurance:** Medicaid AOR 1.55 &#40;domain&#41;, 1.32 &#40;joint&#41; vs employer)

[//]: # (- **Race attenuation:** Black AOR 2.26 → 1.99 after all SDoH &#40;15.7%&#41;)

[//]: # (- **Joint model:** Medicaid, low income, unemployment, renter, disability independently significant)

[//]: # (- **Sensitivity &#40;S1–S5&#41;:** All key SDoH associations robust across 5 specifications)

## Requirements

```
Python  3.10
  pandas          2.3.3
  numpy           1.26.4
  matplotlib      3.7.3
  duckdb          1.4.3

R       4.5.1
  survival        3.8.3
  MatchIt         4.7.2
  cobalt          4.6.2
  dplyr           1.1.4
  readr           2.1.5
  sandwich        3.1.1
  lmtest          0.9.40
```

## License

[MIT](LICENSE)

## Contact

- [Jing Su](mailto:su1@iu.edu) for general questions.
- [Haining Wang](mailto:hw56@iu.edu) for reproduction.


Su Lab in Biomedical Informatics, Biostatistics & Health Data Science · Indiana University School of Medicine
