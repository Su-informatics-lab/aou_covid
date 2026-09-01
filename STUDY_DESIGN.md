# All of Us COVID-19 × SDoH — Study Design (v1.0, frozen 2026-09-01)

**Target journal:** JAMIA, Research and Applications
**Pipeline:** frozen at commit `17f3d00` + branch `review/v18.7-reconcile`
**Data:** All of Us Controlled Tier CDR v7 `C2022Q4R13` (cutoff 1 July 2022);
MarketScan Commercial Claims 2020–2023

## Story arc

Hospitalization during COVID-19 fell disproportionately on Black, Hispanic and
lower-income people, and that much is settled. What is not settled is which
specific, measurable social conditions carry the excess, because the field's
default exposure — an area-level deprivation index — is a poor proxy for the
circumstances of an individual patient, and the individual-level alternative,
social risk coded in the EHR, is documented in fewer than 2% of encounters.

All of Us links a social survey to OMOP-standardized EHR at a scale that lets
both problems be sidestepped at once. The question this design can answer, and
prior work could not, is which social domains carry *independent* signal once
they are modelled together, and which are standing in for one another.

In 4,064 hospitalized cases matched to 15,856 controls on encounter density
rather than clinical severity, Medicaid coverage, unemployment, renting and the
two lowest income strata survive mutual adjustment; education below GED does
not. Six-domain adjustment moves the Black-race odds ratio from 2.30 to 2.00, so
measured individual socioeconomic position accounts for only a small part of it.

## Research question

1. Which of six survey-derived social domains remain associated with COVID-19
   hospitalization after mutual adjustment and after control for 19 Charlson
   comorbidities, vaccination and pandemic wave?
2. How much do those domains attenuate the Black-race hospitalization
   coefficient?
3. How do the social and racial associations differ across pandemic waves?

## Design

Retrospective matched case-control. Conditional logistic regression within
strata balanced on **encounter-density proxies** — enrollment date, diagnosis
count, EHR length (All of Us) or coverage span (MarketScan) — deliberately *not*
on clinical or social characteristics.

The estimand is a **within-stratum association**, not a total effect of social
position. Diagnosis count may lie on the SDoH-to-hospitalization pathway, so
matching on it is conservative by construction. This is stated in Limitations
and is not a defect to be argued away.

## Exposures, outcome, covariates

- **Outcome (strict, primary):** inpatient (9201, 32037), ED-to-inpatient (262,
  8717), or ED with recorded stay ≥1 day (9203), within 14 days of the index
  date. Broad 30-day outcome is the S1 sensitivity analysis.
- **Index date:** earliest of a documented positive SARS-CoV-2 test or ICD-10
  U07.1.
- **Six SDoH domains** from The Basics Survey: insurance, income, education,
  employment, housing tenure, housing stability, disability (ACS-6). Missingness
  is an explicit level, and its mechanism differs by domain — refusal for
  income/education/employment/housing, non-administration for disability and
  insurance. Do not describe it as one number.
- **Charlson:** Glasheen 2019 CDMF sets, ascertained only from pre-index records.

## Analysis plan

- **Base model:** sex, race, ethnicity, age, wave, vaccination, 19 Charlson.
- **Domain-specific models:** base + one SDoH domain. This is the total
  association a domain carries — what a single-item screen would capture.
- **Joint model:** base + all six domains. This is what remains after overlapping
  domains are removed.
- The two are **complementary, not ranked.** Neither supersedes the other.
- **Race attenuation:** proportional reduction in the log adjusted odds ratio
  (change-in-estimate). Because the odds ratio is non-collapsible, part of any
  such change is a scale artefact; report as indicative, not as an explained
  fraction.
- **Profile contrast:** the product of the three mutually adjusted AORs, with a
  delta-method interval. A conditional logistic model does **not** identify an
  absolute hospitalization probability; do not compute one.
- Standard errors clustered on person identifier (matching is with replacement).

## What remains exploratory

- The wave-stratified attenuation trend. The three values (11.5%, 29.1%, 30.1%)
  were never compared formally, the Delta interval is very wide, and the rise
  happens once between pre-Delta and Delta rather than progressively.
- The inverse disability estimate, at 65.4% missingness.
- The AIDS cross-cohort discordance, which is sensitive to the phenotype.

## Frozen; changing any of the above requires a DECISIONS.md entry
