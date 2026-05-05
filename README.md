# COVID-19 Severity × Social Determinants of Health

Propensity-matched case-control study of SDoH disparities in COVID-19
hospitalization using the NIH All of Us Research Program, with external
validation in MarketScan Commercial Claims.

**Manuscript**: Targeting JAMIA (Journal of the American Medical Informatics
Association), Research and Applications.

## Study Design

- **Primary**: AoU Controlled Tier v7 (CDR C2022Q4R13, cutoff Jul 2022)
- **Sensitivity**: AoU Controlled Tier v8 (CDR C2023Q3R4, cutoff Oct 2023)
- **External validation**: MarketScan Commercial Claims (2020–2023)
- **Design**: 1:4 propensity-score matched case-control
- **Outcome**: COVID-19 hospitalization within 30 days of index
- **Analysis**: Conditional logistic regression (survival::clogit)

## Repository Structure

```
aou_covid/
├── README.md
├── 01_ms_etl.py            # MarketScan ETL (Quartz HPC, DuckDB)
├── 01_aou_etl.py           # AoU ETL (Workbench, BigQuery)
│                           #   Usage: python 01_aou_etl.py v7
│                           #          python 01_aou_etl.py v8
├── 02_models.R             # Shared models (AoU + MarketScan)
│                           #   Usage: Rscript 02_models.R aou_v7
│                           #          Rscript 02_models.R aou_v8
│                           #          Rscript 02_models.R ms
├── pilot_audit.py          # Diagnostic audit blocks
├── .gitignore
└── results/
    ├── aou_v7/             # AoU v7 outputs
    │   ├── 01_covid_cohort.csv
    │   ├── 02_demographics.csv
    │   ├── 03_charlson.csv
    │   ├── 04_sdoh.csv
    │   ├── 05_vaccination.csv
    │   ├── 06_matched_cohort.csv
    │   ├── 07_regression_base.csv
    │   ├── base_model_coefficients.csv
    │   ├── all_model_coefficients.csv
    │   └── *_clogit.RData
    ├── aou_v8/             # AoU v8 outputs (same structure)
    └── ms/                 # MarketScan outputs
        ├── 01_covid_cohort.csv
        ├── 02_demographics.csv    # includes plan_type, region_name
        ├── 03_charlson.csv
        ├── 04_sdoh.csv            # placeholder (empty)
        ├── 05_vaccination.csv
        ├── 06_matched_cohort.csv
        ├── 07_regression_base.csv
        ├── base_model_coefficients.csv
        └── all_model_coefficients.csv
```

## Execution

### AoU (on Researcher Workbench)

```bash
python 01_aou_etl.py v7          # ETL → results/aou_v7/
Rscript 02_models.R aou_v7       # Models → results/aou_v7/

python 01_aou_etl.py v8          # ETL → results/aou_v8/
Rscript 02_models.R aou_v8       # Models → results/aou_v8/
```

### MarketScan (on Quartz HPC)

```bash
python 01_ms_etl.py              # ETL → results/ms/
Rscript 02_models.R ms           # Models → results/ms/
```

## Key Design Decisions

| Feature | AoU | MarketScan |
|---------|-----|-----------|
| Race/ethnicity | In base model | Not available |
| SDoH surveys | 13 models | Not available |
| Plan type | Not in base model | In base model (PPO ref) |
| Region | Not in base model | In base model (South ref) |
| Vaccination | OMOP drug_concept_id | NDC prefix matching |
| Charlson | OMOP concept table + ICD vocab filter | Direct ICD code matching |

## Code Sets

- **Charlson**: Glasheen et al., Am Health Drug Benefits 2019;12(4):188–197
- **SDoH surveys**: Gatz, Su et al., JAMIA 2024;31(12):2932–2939, eTable 5
- **COVID identification**: U07.1 (concept 37311061) + 62 lab concepts

## Requirements

- AoU Researcher Workbench (Controlled Tier access)
- Quartz HPC (for MarketScan)
- Python 3.10+, pandas, scikit-learn, numpy
- R 4.x, survival, dplyr, readr
- DuckDB (MarketScan only)

## License

MIT

## References

- Gatz, Su et al. Health Disparities in the Risk of Severe Acidosis.
  *JAMIA* 2024;31(12):2932–2939. doi:10.1093/jamia/ocae256
- Glasheen et al. Charlson Comorbidity Index: ICD-9 Update and ICD-10
  Translation. *Am Health Drug Benefits* 2019;12(4):188–197.
