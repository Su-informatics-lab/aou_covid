# Decisions

Append only. Numbered, dated, with the reason. Never edit an entry — the record
of what was replaced is most of the value. Supersede it with a new one.

---

## D1 — 2026-09-01 — Match on encounter density, not clinical severity

Patients with more health-system contact accumulate more recorded diagnoses, so
an SDoH association derived from EHR can be an artefact of differential
engagement rather than of social position. Matching on enrollment date,
diagnosis count and EHR length balances data availability directly.

Cost, accepted: diagnosis count may lie on the causal pathway, so the estimates
are conservative within-stratum associations rather than total effects. Stated
in Limitations.

## D2 — 2026-09-01 — Report domain-specific and joint models as complementary

An earlier draft implied the joint model superseded the domain-specific one. It
does not. The domain-specific estimate is the total association a domain
carries, which is the quantity a single-item screen would capture; the joint
estimate is what survives mutual adjustment. Both are reported for all six
domains, and Figure 4 shows them paired.

## D3 — 2026-09-01 — The profile contrast is an odds ratio, not a probability

`02_models.R` applied the inverse logit to a `clogit` linear predictor. That
predictor is centred on the covariate means and carries no intercept, so the
resulting 0.438 "baseline probability" was an artefact of the centring and the
1.31 "probability ratio" was compressed by the flatness of the logistic curve
near 0.5.

Replaced with the profile odds ratio — a linear combination of fitted
coefficients, so it also carries an exact delta-method interval. Point estimate
1.78 (= 1.33 × 1.18 × 1.13); the interval appears once the pipeline is re-run on
the Workbench. The Discussion argument that rested on 1.31 being "more modest
than multiplying separate AORs" was removed: 1.78 *is* that product. The
defensible comparison is joint 1.78 against domain-specific 2.79.

Supersedes the P0.4 block as written before this date.

## D4 — 2026-09-01 — Report the Delta wave

The temporal claim was built on two endpoints, 11.5% and 30.1%, while Figure 5b
printed a third annotation the text never mentioned. With Delta included the
series is 11.5% → 29.1% → 30.1%, and the Black-race base AOR is 3.00 → 2.98 →
1.65. The rise happens once, between pre-Delta and Delta, and the Delta interval
(1.79–4.96) makes the three attenuation values statistically indistinguishable.

All three waves are now reported in the Abstract, Results, Discussion,
Conclusions and both figure legends, with an explicit statement that no formal
test compared them.

## D5 — 2026-09-01 — State the income non-monotonicity in the Abstract

In the joint model $100,000–149,999 (1.24) and $150,000–199,999 (1.26) are
significant and larger than the lowest stratum (1.18). Writing "lower income" in
the Abstract while Table 3 shows this is a claim a reviewer falsifies by reading
one table. The Abstract and Conclusions now name the non-monotonicity.

Rejected alternative: leading with the collapsed <$35,000 result (S5, 1.16,
1.04–1.30), which is a clean low-income contrast. Rejected because it hides the
pattern rather than reporting it.

## D6 — 2026-09-01 — Table 2 blocks must partition the cohort

`04_tables.py::sdoh_section` counted the named levels and then `.isna()`, so any
value that was neither — an unmapped answer concept arriving as the literal
string "Missing" — was counted in no row. Housing tenure lost 1 case and 5
controls. Insurance, which passed "Missing" inside its level list, emitted the
row twice.

Missing is now defined as `~isin(levels)`, which captures NaN and unmapped
strings alike, and the function raises if a block does not sum to N. A silently
wrong table is worse than a failed build.

## D7 — 2026-09-01 — A number gate, and the ledger generated from it

Every defect found in the v18.5 audit was a transcription drift: the pipeline was
right and the document had fallen behind it. Nothing caught them because nothing
was checking.

`analysis/validate_numbers.py` asserts each printed number against the artifact
it came from and fails the build on drift; `analysis/gate.sh ledger` runs the
same assertions with the assertion replaced by a recorder and writes
`submission/CLAIM_LEDGER.md`, so the mapping is a byproduct of the test and the
two cannot disagree. Retired denominators go in `v.banned`, with legitimate
reuses recorded via `v.allow` rather than silently skipped.

## D8 — 2026-09-01 — 02c must verify its own outputs

`wave_stratified_race.csv`, `wave_stratified_insurance.csv` and
`wave_stratified_race_attenuation.csv` were declared by the script, absent from
the repository, and eTable 12b/12c depended on them — so those tables survived
only as hardcoded constants in `make_figures.py` and could not be reproduced
from the repository the Data Availability statement names.

`02c` now stops if any of the four wave outputs is missing. **eTable 12b and 12c
remain UNVERIFIED until 02c is re-run on the Workbench and the CSVs committed.**
This is the single largest open item.

## D9 — 2026-09-01 — One semantic colour grammar across all five figures

Navy = All of Us / joint / adjusted. Coral = domain-specific / base. Teal =
MarketScan. Grey + open marker = not significant. Wave uses one hue light to
dark because it is ordered. Significance is carried by fill as well as hue, so
the figures survive greyscale. Measured colourblind-safe (min ΔE 25.9 normal,
15.0 deuteranopia).
