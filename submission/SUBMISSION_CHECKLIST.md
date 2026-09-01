# JAMIA submission package — Research and Applications

Requirements verified against **https://academic.oup.com/jamia/pages/General_Instructions**
(the only official author-instructions page; `/pages/Author_Guidelines` returns 404).
Submission site: **ScholarOne — http://mc.manuscriptcentral.com/jamia**

---

## Answer to "are figures and tables submitted separately?"

**Figures: separate. Tables: not separate.** JAMIA's exact words:

- *"Images must be uploaded as separate files."* — one file per figure, no embedding.
- *"Tables should be in Word format and placed in the main text where the table is first cited."*
  And: *"Tables embedded as Excel files within the manuscript are NOT accepted."*
- *"Figure legends should be provided at the end of the manuscript"* — legends go in the
  manuscript file, not with the images. **This is done; the legends were moved out of the
  body to a FIGURE LEGENDS section at the end.**
- **Alt text is mandatory** and sits directly under each legend, prefixed `Alt text:`.
  **This is done for all five figures.**

---

## What is in this folder

| Path | Upload as | Status |
|---|---|---|
| `01_cover_letter.docx` | Cover Letter | ready — carries the four required declarations |
| `02_manuscript.docx` | Main Document | see open items below |
| `03_figures/pdf/Figure1–5.pdf` | Image (one per file) | ready — vector, selectable text, fonts embedded |
| `03_figures/tif/` | fallback if a raster is demanded | 600 dpi LZW TIFF |
| `03_figures/png/` | for co-authors and Word, not for upload | 600 dpi |
| `04_supplementary/JAMIA_supplementary.docx` | **Supplementary File** | ready |
| `06_for_editors_only/` | **Supplementary file for Editors only** | empty — nothing to declare |
| `07_figure_source/` | not uploaded | the plotting code, for the repo |

Counts: **5 figures** (limit 6) · **3 tables** (limit 4) · **46 references** (unlimited).

---

## Figures

Redrawn from the frozen analysis outputs. One semantic colour grammar across all five,
so a reader who learns it in Figure 1 can read Figures 3–5 without re-reading a legend:

| Colour | Meaning | Where |
|---|---|---|
| **Navy `#3C5488`** | All of Us · joint model · after SDoH adjustment — *the adjusted estimate* | Fig 1a, 3, 4, 5b |
| **Coral `#E64B35`** | domain-specific model · base model — *the unadjusted estimate* | Fig 4, 5b |
| **Teal `#00A087`** | MarketScan — *the external cohort* | Fig 1b, 3 |
| **Grey `#8491B4`** | not statistically significant (also an open marker) | all |
| Light→dark blue ramp | pandemic wave, pre-Delta → Delta → Omicron (ordered, so one hue) | Fig 5a |

Palette is **NPG** (ggsci's *Nature Publishing Group*-inspired set). Be precise about the
claim: these values are eyedropped from published NPG figures, **not** a palette Nature or
JAMIA has ever endorsed. What is defensible is the measurement — the four-colour grammar
tests **safe**: minimum ΔE 25.9 (normal vision), 15.0 (deuteranopia), 20.6 (protanopia),
13.1 (tritanopia); every colour clears 3:1 against white; none is too pale for a hairline.
Significance is carried by **filled versus open markers as well as colour**, so the figures
survive greyscale.

Technical: all five are exactly **6.875 in** wide (JAMIA double column) so production
reduces every figure by the same factor. Vector PDF, RGB, Type-42 embedded
**Liberation Sans** (metrically identical to Arial), 6–7 pt in-panel text, 0.5–0.9 pt
rules, no gridlines, white background, text left as live text so the production team can
edit it.

**Unverifiable and worth one email to the editorial office** — JAMIA states none of these
and defers to an OUP page that renders client-side and returns no content: accepted figure
formats, required DPI, column widths, and whether colour costs anything in print. PDF plus
600 dpi TIFF covers every plausible answer.

---

## Open items before you hit submit

1. **`Background and Significance` section is missing.** JAMIA requires it in the main text
   of a Research and Applications article, in addition to the structured abstract. The
   current manuscript goes INTRODUCTION → METHODS. This is a desk-reject risk and needs
   roughly 250–350 words, most of which can be lifted from the second half of the
   Introduction.
2. **Length.** Main text **5,506** against 4,000; abstract **315** against 250. Declare the
   word count on the title page, excluding title page, abstract, references, figures and
   tables.
3. **Title page** needs: corresponding author's postal address and telephone; each
   co-author's department, institution, city, country and degree; up to five keywords,
   MeSH-preferred; the declared word count.
4. **Table 1 is 49 rows.** JAMIA: *"Tables submitted that are longer/larger than 2 pages
   will be published as online only supplementary material."* Either split it (demographics
   in the main text, the 19 Charlson rows to the supplement) or accept that it moves online.
5. **Reference author counts.** JAMIA wants three authors then "et al."; 15 references list
   four to six. Citations are already converted to JAMIA's bracketed in-text style
   (`[6]`, `[1, 4, 39]`, `[22-25]`, no space before the bracket).
6. **Double-space** the manuscript before upload.
7. **CRediT roles, funding, and conflicts** are entered in ScholarOne at submission, not
   only in the document.
8. **Refs 35 and 45 are still preprints**, cited as 2024 and 2025 though both carry
   2024.10.xx DOIs. Pick one year and mark both "preprint".
9. **Ethics/IRB, ORCID, suggested reviewers, and STROBE** are absent from JAMIA's official
   page — no requirement is evidenced. Include an IRB statement anyway; reviewers expect it.

---

## Still open in the analysis (from the v18.6 audit)

- `02_models.R` lines 384–389 still compute the invalid predicted probability. The
  manuscript now reports the profile odds ratio (1.78) instead, but the code is unfixed.
- `results/aou_v7/table2_sdoh.csv` loses 1 case and 5 controls from housing tenure and
  emits a duplicate `Missing,<20` row under insurance. Table 2 reproduces the leak.
- `wave_stratified_race_attenuation.csv`, `wave_stratified_race.csv` and
  `wave_stratified_insurance.csv` are written by `02c_…R` but never committed, so eTables
  12b and 12c cannot be reproduced from the repo the Data Availability statement names.
- No claim ledger and no gate script exist. Every error found in the v18.5 audit was a
  transcription drift a validator would have caught.
