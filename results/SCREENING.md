# Disclosure screen for everything in `results/`

All of Us forbids publishing any participant count below 20, or any set of
counts from which such a count can be derived. `results/` was made local-only on
2026-09-02 because it then held 81 aggregate files that had never been screened
against that rule. What is in it now has been screened, and this file is the
record.

**Screened 2026-09-04, before the files were first committed.**
**Re-screened 2026-09-05, when the figures were rebuilt as separate panels.**

## What is published

| Path | Content | Smallest quantity |
|---|---|---|
| `figures/Figure{1..5}_data.csv` | adjusted odds ratios, confidence bounds, standardized mean differences and percentage-point attenuations | not a count |
| `figures/eFigure2_data.csv` | absolute standardized mean differences | not a count |
| `figures/eFigure3_data.csv` | qualifying visits per day relative to the index date | 72 visits (day −10) |
| `figures/eFigure5_data.csv` | base-model odds ratios in both cohorts | not a count |
| `figures/flu/*.csv` | influenza odds ratios, confidence bounds, P values, interaction chi-squares | not a count |
| `figures/*.pdf`, `*.png` | the supplementary figures those values draw | — |
| `figures/panels/*.pdf`, `*.png` | the main-text figure panels, and the design strip that heads each figure | — |
| `figures/panels/README.md` | which panel belongs to which figure | — |
| `RUN.json` | cohort sizes and data versions | 1,672 case person-seasons |

## How it was screened

Every candidate file was scanned for integers between 1 and 19 appearing outside
a decimal. Every hit was inspected. All of them are one of: a degrees-of-freedom
value, a day index on the eFigure 3 axis, a Curated Data Repository version, a
figure or table number, a matplotlib parameter, or a fragment of a hex colour.
**No file contains a participant count, and none is derivable from what they do
contain**: odds ratios and standardized mean differences carry no denominator,
and the eFigure 3 series is visits rather than people, with a minimum of 72.

The one stratum in this study with fewer than 20 participants — education
"never attended school" — is suppressed in the manuscript and appears in no file
here. That was checked by name, not only by the numeric scan.

The 2026-09-05 re-screen covered what the panel rebuild added or renamed.
`Figure{2,3,4}_data.csv` were verified byte-identical to the files screened on
2026-09-04 under their old numbers, so only two files carry new content:
`Figure1_data.csv` (six standardized mean differences and 26 pairs of odds
ratios) and `Figure5_data.csv` (the race sequence and the per-domain
attenuations, unchanged apart from their panel letters). Neither has a single
integer in the 1–19 range. The panels themselves are drawn from
`figures/design_strip.py` and the five figure scripts, which were scanned in
the same pass; their hits are font sizes, marker sizes, drawing order, the
matched-set ratio, the 19 comorbidities of the base model, and the 14-day
outcome window. None is a participant count.

## What is not published, and why

Model fits, matched cohorts, balance tables and every person-level file stay on
the platform they were computed on: the All of Us Researcher Workbench workspace
bucket, and `/N/project/depot/hw56/ms_covid/` on Quartz for MarketScan. The Data
Availability statement promises code, not artifacts. Analysis runs where the data
lives; aggregate values are read off the platform and recorded, and rows are never
brought down to be analysed elsewhere.

## If something needs to be added

Screen it, add the row above, and commit it with the screen in the same commit.
`results/` is still ignored by default in `.gitignore`; the exceptions are
explicit, so a new file is not published by accident.
