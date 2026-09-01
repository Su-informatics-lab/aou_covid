# JAMIA submission package — Research and Applications

Requirements verified against **https://academic.oup.com/jamia/pages/General_Instructions**
(the only official author-instructions page; `/pages/Author_Guidelines` returns 404).
Submission site: **ScholarOne — http://mc.manuscriptcentral.com/jamia**

Package state: **v18.7, for internal review.** Read the next section before you upload
anything.

---

## Do not submit yet. One blocker, and it is a science blocker.

The matching variables in `01_aou_etl.py` had no index-date restriction. `num_diagnosis`
and `ehr_length_days` counted codes and history **after** the COVID index date, so the
propensity model partly matched on a product of the outcome: a hospitalized case accrues
diagnosis codes during the admission, and its controls were then chosen to have the same
code count without having been admitted.

`num_diagnosis` is the strongest term in the propensity model (pre-matching SMD 0.489),
so this is not a rounding-level concern. The SQL is fixed in commit `223f715`, but the
query has never been executed — BigQuery is not reachable from outside the Workbench.

**Every effect estimate in this package is therefore stale.** The package is complete and
internally consistent, and it is ready to become the submission the moment the pipeline is
re-run. It is not ready to be uploaded before that.

Full reasoning and the per-item disposition of Dr. Zhang's review are in
`08_internal_review/`.

---

## Answer to "are figures and tables submitted separately?"

**Figures: separate. Tables: not separate.** JAMIA's exact words:

- *"Images must be uploaded as separate files."* — one file per figure, no embedding.
- *"Tables should be in Word format and placed in the main text where the table is first
  cited."* And: *"Tables embedded as Excel files within the manuscript are NOT accepted."*
- *"Figure legends should be provided at the end of the manuscript"* — legends go in the
  manuscript file, not with the images. Done.
- **Alt text is mandatory** and sits directly under each legend, prefixed `Alt text:`.
  Done for all five figures.

---

## What is in this folder

| Path | Upload as | Status |
|---|---|---|
| `01_cover_letter.docx` | Cover Letter | AI declaration still blank, by your instruction |
| `02_manuscript.docx` | Main Document | format complete; numbers await the re-run |
| `03_figures/pdf/Figure1–5.pdf` | Image (one per file) | vector, live text, fonts embedded |
| `03_figures/tif/` | fallback if a raster is demanded | 600 dpi LZW TIFF |
| `03_figures/png/` | for co-authors and Word, not for upload | 600 dpi |
| `04_supplementary/JAMIA_supplementary.docx` | Supplementary File | ready |
| `05_claim_ledger/` | not uploaded | every printed number traced to its artifact |
| `06_for_editors_only/` | Supplementary file for Editors only | empty — nothing to declare |
| `07_figure_source/` | not uploaded | the plotting code, for the repo |
| `08_internal_review/` | **not uploaded** | review disposition and eTable 12 forensics |

Counts: **5 figures** (limit 6) · **3 tables** (limit 4) · **46 references** (unlimited).
Main text **3,590** / 4,000 · abstract **245** / 250.

---

## Format requirements: all closed this round

| Requirement | State |
|---|---|
| Double-spaced | 179 paragraphs at 2.0; tables left single-spaced |
| No stray highlighting | 7 yellow runs cleared; 0 remain |
| Title page: address, telephone, word count, MeSH keywords | complete |
| References: three authors then "et al." | 15 references trimmed |
| Preprints labelled | refs 36 and 46 marked `Preprint.`, both dated 2024 |
| All of Us authorization and DUA | new `ETHICS AND DATA USE` section |
| Alt text describes the graphic | all five rewritten |
| Bracketed in-text citations | `[6]`, `[1, 4, 39]`, `[22-25]`, no space before the bracket |
| `BACKGROUND AND SIGNIFICANCE` section | present, 379 words |

Two notes on judgement calls.

**Ethics wording.** You said no IRB is needed, so nothing in the manuscript claims a local
IRB determination. The section asserts only what is verifiable: the All of Us programme
holds IRB approval, participants consented, the authors hold Controlled Tier authorization
and completed the training, and the work ran in a registered workspace under the DUA and
the Data User Code of Conduct. If internal review wants a sentence about IU specifically,
that sentence has to come from you or Dr. Su.

**Preprint years.** Checked against PubMed on 1 September 2026: refs 36 and 46 are both
still medRxiv preprints with no journal version. Both carry a `2024.10.xx` DOI, so both are
dated by first posting. Ref 46's `[published Online First: 20250418]` became
`[revised 18 April 2025]`, because "Online First" reads as "already in a journal".

---

## Figures

Redrawn from the frozen analysis outputs, except Figures 1 and 2, which are your original
draw.io drawings, unchanged. One semantic colour grammar runs across Figures 3–5:

| Colour | Meaning |
|---|---|
| **Navy `#3C5488`** | All of Us · joint model · after SDoH adjustment |
| **Coral `#E64B35`** | domain-specific model · base model |
| **Teal `#00A087`** | MarketScan |
| **Grey `#8491B4`** | not statistically significant (also an open marker) |
| Light→dark blue ramp | pandemic wave, pre-Delta → Delta → Omicron |

Palette is **NPG** (ggsci's Nature Publishing Group-inspired set). Be precise about the
claim: the values are eyedropped from published NPG figures, **not** a palette Nature or
JAMIA has ever endorsed. What is defensible is the measurement — minimum ΔE 25.9 (normal
vision), 15.0 (deuteranopia), 20.6 (protanopia), 13.1 (tritanopia); every colour clears
3:1 against white. Significance is carried by **filled versus open markers as well as
colour**, so the figures survive greyscale.

Technical: 6.875 in wide (JAMIA double column), vector PDF, RGB, Type-42 embedded
Liberation Sans, 6–7 pt in-panel text, 0.5–0.9 pt rules, no gridlines, live text.

**Unverifiable, and worth one email to the editorial office** — JAMIA states none of these
and defers to an OUP page that renders client-side and returns no content: accepted figure
formats, required DPI, column widths, and whether colour costs anything in print. PDF plus
600 dpi TIFF covers every plausible answer.

---

## Open items, in the order they block submission

1. **Re-run the pipeline.** `01` → `01b` → `02` / `02b` / `02c` / `03` → `04` / `06` →
   `make_figures`. The post-re-run checklist is at the end of
   `08_internal_review/2026-09-01_zhang_internal_review_disposition.md`.
   `bash analysis/gate.sh check` **will fail widely, and that is correct** — update each
   assertion to the new result; never edit a result to satisfy an assertion.
2. **eTable 12b / 12c are UNVERIFIED.** No committed artifact supports them, and
   `06_supplement.py` contains no code that builds them. Run
   `Rscript 02c_wave_stratified_race_insurance.R aou_v7`, commit the four
   `wave_stratified_*.csv`, and add the assertions to `validate_numbers.py`.
   The forensics report explains why the numbers are nonetheless real.
3. **Table 2 housing "Missing"** should be 170 cases / 576 controls, not 169 / 571.
   That comes from re-running `04_tables.py`; it is not a hand edit.
4. **Profile odds-ratio interval.** The text prints 1.78 without its CI. Re-run
   `02_models.R` and take `profile_odds_ratio_contrast.csv`.
5. **AI declaration** in the cover letter is blank, marked
   `[TO BE COMPLETED BY THE AUTHORS]`, with JAMIA's own wording quoted beside it.
6. **Table 1 is 49 rows.** JAMIA: *"Tables submitted that are longer/larger than 2 pages
   will be published as online only supplementary material."* Either split it —
   demographics in the main text, the 19 Charlson rows to the supplement — or accept that
   it moves online.
7. **Figure 1 (draw.io)** does not show the 388 control observations dropped for
   incomplete follow-up. The legend states it; the diagram does not.
8. **Dr. Su's ORCID** `0000-0003-4917-6173` was inferred from dblp and Crossref, not read
   off an IU page. Confirm it before entering it in ScholarOne.
9. **CRediT roles, funding, and conflicts** are entered in the ScholarOne form at
   submission, not only in the document.
10. **Push the branch.** `git push -u origin review/v18.7-reconcile`, then
    `pre-commit run --all-files` before merging. The sandbox cannot reach your SSH key.

---

## Analysis side: fixed this round

| Fault | State |
|---|---|
| Matching variables carried post-index information | fixed in `223f715`; **not yet executed** |
| `02_models.R` applied an inverse logit to a centred clogit linear predictor | replaced by a profile odds ratio with a delta-method interval |
| `04_tables.py` lost 1 case and 5 controls from housing; duplicated an insurance Missing row | now `~isin(levels)`, and it raises if the partition does not hold |
| `02c` declared three CSVs it never committed | now `stop()`s if any output is absent |
| Nothing checked the manuscript against the pipeline | `analysis/gate.sh`: **117 assertions / 8 frozen sources / 0 failing** |
