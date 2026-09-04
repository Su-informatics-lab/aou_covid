# Disclosure screen for everything in `results/`

All of Us forbids publishing any participant count below 20, or any set of
counts from which such a count can be derived. `results/` was made local-only on
2026-09-02 because it then held 81 aggregate files that had never been screened
against that rule. What is in it now has been screened, and this file is the
record.

**Screened 2026-09-04, before the files were first committed.**

## What is published

| Path | Content | Smallest quantity |
|---|---|---|
| `figures/Figure{1..5}_data*.csv` | adjusted odds ratios and 95% confidence bounds | not a count |
| `figures/eFigure2_data.csv` | absolute standardized mean differences | not a count |
| `figures/eFigure3_data.csv` | qualifying visits per day relative to the index date | 72 visits (day −10) |
| `figures/flu/*.csv` | influenza odds ratios, confidence bounds, P values, interaction chi-squares | not a count |
| `figures/*.pdf`, `*.png` | the figures those values draw | — |
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
