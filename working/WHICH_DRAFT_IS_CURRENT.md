# Which draft is current

| File | State |
|---|---|
| `working/JAMIA_manuscript_v19.0.docx` | **current.** Both re-runs folded in; no `[STALE]` markers in the main text. |
| `working/JAMIA_supplementary_v19.0.docx` | **current.** No `[STALE]` markers left. |
| `working/figs19/Figure3-5.pdf` | **current.** Redrawn from the re-run coefficients on 2026-09-02. |
| `working/drawio/fig1_consort.drawio` + `.png` | **current.** The authoritative Figure 1. Hand-tuned by the PI after the scripted first draft; the PNG is what goes in the manuscript. |
| `working/efig2_phenotype_algorithm.drawio` | **current.** A decision tree with no counts, so the pre-index correction does not touch it. |
| `working/ms_v191_rerun_WORKING.docx` | superseded by v19.0. Kept only so the diff of the previous rewrite stays readable. |
| `submission/02_manuscript.docx` | v18.6 throughout, internally consistent, and **not** to be submitted. |
| `submission/03_figures/pdf/Figure3-5.pdf` | v18.6. Figures 1 and 2 there are the draw.io panels and are being redrawn by the PI. |

Figure 1's numbers are guarded by `figures/fig1_consort_check.py`, which reads the
.drawio and asserts all seventeen identities in the two flow chains. Run it after
any edit to the diagram. It does not regenerate the file: the layout is the
author's.

The round record for the current state is
`reviews/2026-09-02_v19_platform_completion.md`.
