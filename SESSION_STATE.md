# Session state

**Updated:** 2026-09-01 · **Branch:** `review/v18.7-reconcile` · **Stage:** 6 → 7
**Next action:** internal review of the branch, then re-run `02c` on the Workbench.

---

## Where the project is

Stages 1–5 were done long ago; stage 8 was being attempted. **Stage 6 had never
been done**, and that is the whole story of this round: `orient.py` found no
frozen run, no claim ledger and no gate script, and the v18.5 audit then found
the manuscript disagreeing with this repository in 29 cells of Table 1, in every
pre-matching SMD, and in eTable 14 — where a P of 0.068 was printed as 0.03.

None of those were analysis errors. All were transcription drift, and a
five-line assertion would have caught each one. That gate now exists.

## Done this round

**Code (3 real faults, all fixed on this branch)**

| File | Fault | Fix |
|---|---|---|
| `02_models.R` | inverse logit applied to a centred `clogit` linear predictor; "1.31-fold predicted probability" was not a probability | profile odds ratio with a delta-method interval; writes `profile_odds_ratio_contrast.csv` |
| `04_tables.py` | `sdoh_section` counted named levels + `.isna()`, dropping unmapped values; insurance emitted `Missing` twice | Missing is `~isin(levels)`; the block now raises unless it partitions the cohort |
| `02c_…R` | declared three outputs, wrote none that reached the repo | stops if any of the four wave outputs is missing |

**Gate (stage 6)** — `analysis/{ledger.py, validate_numbers.py, gate.sh}`.
Runs green: **117 assertions against 8 frozen sources, 0 failing.**
`submission/CLAIM_LEDGER.md` is generated from the same assertions.

**Documents** — manuscript and supplement corrected against the repository;
five figures redrawn on one semantic colour grammar; JAMIA submission package
assembled. See `V18.6_changelog.md` and `submission/`.

## Open, in priority order

1. **eTable 12b / 12c are UNVERIFIED.** Re-run `Rscript
   02c_wave_stratified_race_insurance.R aou_v7` on the Workbench, commit the
   four `wave_stratified_*.csv`, then add their assertions to
   `validate_numbers.py` (a placeholder comment marks the spot). Until then the
   Delta-wave numbers trace only to constants in `make_figures.py`.
2. **Re-run `02_models.R`** for `profile_odds_ratio_contrast.csv`, then put the
   interval into the Results sentence that currently gives 1.78 bare.
3. **Re-run `04_tables.py`** and re-paste Table 2. Housing tenure Missing goes
   169 → 170 (cases) and 571 → 576 (controls); insurance loses its duplicate row.
4. **`Background and Significance` section is missing.** JAMIA requires it for
   Research and Applications. Desk-reject risk. ~250–350 words, most liftable
   from the second half of the Introduction.
5. **Length.** Main text 5,506 against 4,000; abstract 315 against 250.
6. **Table 1 is 49 rows**; JAMIA moves tables over two pages online-only. Split
   it or accept that.
7. Reference author counts (15 refs list 4–6; JAMIA wants 3 then et al.);
   refs 35 and 45 are preprints cited with inconsistent years.

## How to run the gate

```bash
bash analysis/gate.sh check     # fails on the first drift
bash analysis/gate.sh ledger    # regenerates submission/CLAIM_LEDGER.md
```

Both documents are flattened together, because a number in eTable 10 must trace
to the same artifact as the same number in Table 1. Put `check` in CI before the
next submission.

## What the gate does not do

It proves the manuscript still says what the artifact says. It does **not** prove
the artifact is right. The direction check between Table 1 crude rates and
eTable 10 odds ratios is the one coherence test written so far; more are worth
adding, especially for any statistic derived from other reported statistics.
