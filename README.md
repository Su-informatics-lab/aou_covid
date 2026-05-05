# COVID-19 Severity × Social Determinants of Health

Propensity-matched case-control analysis of survey-derived SDoH and
COVID-19 hospitalization in the NIH *All of Us* Research Program,
with external validation in Merative MarketScan Commercial Claims.

Targets *JAMIA* (Research and Applications). Extends the PSM + conditional
logistic framework of [Gatz, Su et al. *JAMIA* 2024;31(12):2932–2939](https://doi.org/10.1093/jamia/ocae256).

## Repository

```
01_aou_etl.py           AoU ETL (BigQuery, arg: v7 | v8)
01_ms_etl.py            MarketScan ETL (DuckDB on Quartz HPC)
02_models.R             Conditional logistic regression (arg: aou_v7 | aou_v8 | ms)
03_tables_onplatform.py Table 1/2 from person-level data (runs on-platform)
04_figures.py           Figures 1–3, Table 3, eTables (runs anywhere, no PII)
05_smd_onplatform.py    Pre/post matching SMD + Love plot (runs on-platform)
results/                Aggregate outputs only (no person-level data)
```

## Reproduction

```bash
# ── AoU (on Researcher Workbench) ──────────────────────────
python 01_aou_etl.py v7            # 1. ETL → results/aou_v7/
Rscript 02_models.R aou_v7         # 2. 14 clogit models
python 03_tables_onplatform.py v7  # 3. Table 1 (demographics), Table 2 (SDoH)
python 05_smd_onplatform.py aou_v7 # 4. SMD balance + Love plot

# ── MarketScan (on Quartz HPC) ─────────────────────────────
python 01_ms_etl.py                # 1. ETL → results/ms/
Rscript 02_models.R ms             # 2. Base model only (no SDoH surveys)
python 03_tables_onplatform.py ms  # 3. Table 1
python 05_smd_onplatform.py ms     # 4. SMD balance + Love plot

# ── Figures & tables (anywhere, from coefficient CSVs) ─────
python 04_figures.py               # Figs 2–3, Table 3, cross-site eTable
```

## Design

| | AoU | MarketScan |
|---|---|---|
| **Source** | Controlled Tier v7 C2022Q4R13 | Commercial Claims 2020–2023 |
| **Outcome** | COVID-19 hospitalization ≤30 days | Same |
| **Matching** | 1:4 PSM (enrollment date, Dx count, EHR length) | 1:4 PSM (enrollment date, Dx count, coverage span) |
| **Analysis** | Conditional logistic (survival::clogit) | Same |
| **Race/ethnicity** | In base model | Not available |
| **SDoH** | 6 domains, 13 models (survey-derived) | Plan type + region only |
| **Charlson** | Glasheen 2019, 19 conditions, ICD via OMOP | Same codes, direct ICD |
| **Vaccination** | OMOP drug_concept_id | NDC prefix |

## Requirements

```
Python  ≥3.10    pandas ≥1.5  scikit-learn ≥1.2  numpy ≥1.24  duckdb ≥0.9 (MS only)
R       ≥4.5     survival ≥3.5  dplyr ≥1.1  readr ≥2.1
```

AoU Researcher Workbench (Controlled Tier). Quartz HPC with MarketScan parquet access.

## License

MIT
