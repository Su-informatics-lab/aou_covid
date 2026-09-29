# Influenza arm (All of Us CDR v9, workspace su_lab_v9)

These scripts were copied from the influenza workspace VM on 2026-09-25. Paths refer to that VM
(`/home/jupyter/flu/`); person-level files never leave the Researcher Workbench.

| Script | What it does |
|---|---|
| `01_concept_check.py` | Checks the influenza code sets against the CDR v9 concept tables (descendants of SNOMED 4266367 and the positive-result laboratory concepts) before any count. |
| `00_flu_feasibility.py` | Per-season feasibility counts (seasons October 1 to April 30): index events, hospitalization within 14 days under the COVID-19 phenotype rules, survey availability, and where the index event was captured. Counts below 20 print as "<20". |
| `02_psm.R` | Matching: `flu_prematch.csv` to `07_matched_cohort.csv` (1:4 nearest neighbor with replacement on the logit propensity score for survey date, number of distinct diagnoses, and length of EHR history; caliper 0.2 SD; exact on season). |
| `03_models.R` | Base, alone, and joint conditional logistic models. |
| `04_interaction.R` | Period interaction models. |
| `05_flow_top.py` | Top of eFigure 1B (R11, 2026-09-28): counts the CDR v9 participants (747,029) and the participants and person-seasons in the extraction's index file (`flu_index_v9.pkl`: 15,043 person-seasons from 14,012 participants), so the panel starts from the whole repository. It also documents why a SQL re-derivation with the feasibility script's name match gives 15,301 person-seasons: that match admits parainfluenza assays (and *Haemophilus influenzae* and antibody tests), and the 258 extra person-seasons are all laboratory-only, mostly parainfluenza PCR. The index file remains the source of record. Output: `working/v25/platform_r11/flow_top_flu.txt`. |

The attenuation, era-contrast, sensitivity, and R10 analyses for this arm run from the
top-level scripts with `ARM=flu` (`03o_r4_attenuation.R`, `03w_sens.R`, `03x_cells.R`,
`03y_cells_extra.R`, `03z_*.py`, `03z_*.R`).

## What is not here

The step that built `flu_prematch.csv` from CDR v9 (index date as the first influenza diagnosis
or positive test in each season, the hospitalization phenotype, The Basics exposures restricted
to surveys completed on or before the index date, Charlson comorbidities, and the matching
variables) was run interactively on 2026-09-03, together with its intermediate files
(`flu_index_v9.pkl`, `01_flu_cohort.pkl` through `06_*.pkl`). Its script was not retained.
The files it produced remain on the workspace VM and bucket, and every downstream estimate is
reproducible from them with the scripts above; the extraction itself is not reproducible from
code in this repository. The manuscript's Data Sharing Statement says so.
