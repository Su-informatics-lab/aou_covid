# Social Determinants of COVID-19 Severity in the All of Us Research Program

A case-control study examining health disparities in COVID-19 hospitalization risk across social determinants of health (SDoH), using electronic health records and participant surveys from the NIH All of Us Research Program.

## Study Design

- **Outcome**: Severe COVID-19 (hospitalization within 30 days of positive test or diagnosis)
- **Design**: Retrospective case-control with 1:4 propensity score matching
- **Matching**: Nearest neighbor on enrollment date, diagnosis count, and EHR length; caliper = 0.2 × SD(logit propensity score); with replacement
- **Base model**: Conditional logistic regression adjusting for sex, race, ethnicity, age, vaccination status, and 19 Charlson comorbidities (Glasheen 2019)
- **SDoH models**: Each adds one SDoH domain to the base model (insurance, disability, employment, income, education, housing, housing stability)

## Repository Structure

```
aou_covid/
├── README.md
├── 01_etl.py          # Data extraction, Charlson flags, SDoH, propensity matching
├── 02_models.R        # Base model + 13 SDoH conditional logistic regression models
├── pilot_audit.py     # Data availability checks (run before 01_etl.py)
└── results/           # Generated outputs (not tracked in git)
    ├── *_01_covid_cohort.csv
    ├── *_02_demographics.csv
    ├── *_03_charlson.csv
    ├── *_04_sdoh.csv
    ├── *_05_vaccination.csv
    ├── *_06_matched_cohort.csv
    ├── *_07_regression_base.csv
    ├── all_model_coefficients.csv
    └── *_clogit.RData
```

## Requirements

### Platform

This analysis runs on the [All of Us Researcher Workbench](https://www.researchallofus.org/) (Controlled Tier). Access requires registration and a data use agreement with the All of Us Research Program.

### Python dependencies

```
python==3.10.16
pandas==2.3.3
numpy==1.26.4
scikit-learn==1.4.2
```

### R dependencies

```
survival==3.8.3
dplyr==1.1.4
readr==2.1.5
ggplot2==3.5.2
```

## Reproduction

### 1. Create a workspace

Create a new workspace on the All of Us Researcher Workbench with Controlled Tier access (v7 or v8). Clone this repository into the workspace.

### 2. Run the data pipeline

```bash
python 01_etl.py
```

Outputs seven CSV files to `results/` and mirrors them to the workspace bucket. Runtime: approximately 30 minutes.

### 3. Run the regression models

```bash
Rscript 02_models.R
```

Reads the CSV files from step 2, runs 14 conditional logistic regression models (1 base + 13 SDoH), and saves coefficient tables to `results/`. Runtime: approximately 10 minutes.

### 4. Outputs

All outputs are written to `results/`:

| File | Description |
|------|-------------|
| `*_01_covid_cohort.csv` | COVID-positive cohort with severity indicator |
| `*_02_demographics.csv` | Sex, race, ethnicity, age |
| `*_03_charlson.csv` | 19 Charlson comorbidity flags |
| `*_04_sdoh.csv` | Disability, insurance, employment, income, education, housing |
| `*_05_vaccination.csv` | Pre-COVID vaccination status |
| `*_06_matched_cohort.csv` | Propensity-matched cohort with stratum IDs |
| `*_07_regression_base.csv` | Merged regression-ready dataframe |
| `all_model_coefficients.csv` | Combined AOR, 95% CI, and p-values for all models |
| `*_clogit.RData` | Saved R model objects |

## Data Sources

- **Electronic health records**: OMOP CDM v5.3 (condition, drug exposure, visit, measurement)
- **Surveys**: All of Us Basics Survey (demographics, SDoH, disability)
- **COVID identification**: ICD-10 U07.1 (condition_concept_id 37311061) and SARS-CoV-2 lab results
- **Comorbidities**: Charlson Comorbidity Index per Glasheen et al. (2019), ICD-9/10 code sets
- **SDoH concept IDs**: All of Us observation table (insurance 43528428; disability 903573–903578; employment 1585952; income 1585375; education 1585940; housing 1585370; housing stability 1585886)

## Key References

- Glasheen WP et al. Charlson Comorbidity Index: ICD-9 Update and ICD-10 Translation. *Am Health Drug Benefits*. 2019;12(4):188-197.
- Austin PC. An Introduction to Propensity Score Methods for Reducing the Effects of Confounding in Observational Studies. *Multivariate Behav Res*. 2011;46(3):399-424.
- All of Us Research Program Investigators. The "All of Us" Research Program. *N Engl J Med*. 2019;381:668-676.

## License

Code: [MIT License](https://opensource.org/licenses/MIT)

Data access requires separate approval through the [All of Us Research Program](https://www.researchallofus.org/).

## Citation

If you use this code, please cite the associated publication and acknowledge the All of Us Research Program.
