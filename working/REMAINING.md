# What the manuscript still needs · 2026-09-02

Current draft: `working/JAMIA_manuscript_v19.0.docx` (3,979 words, limit 4,000)
and `working/JAMIA_supplementary_v19.0.docx` (no `[STALE]` markers left).
Figure 1 is `working/drawio/fig1_consort.drawio` + its PNG; Figures 3–5 are
`working/figs19/`. Round record: `reviews/2026-09-02_v19_platform_completion.md`.

## Blocking

1. **Paste the new Figure 1 PNG into the manuscript**, replacing the old
   flowchart image. Figure 2 needs no change: it is a decision tree and carries
   no counts, so the pre-index correction does not touch it.
2. **Save and close the manuscript in Word.** It is open with unsaved changes,
   so it is the one file this round left uncommitted.
3. **A manual read-through.** The body is 3,979 words against a 4,000 limit, so
   anything added has to be paid for.

## Before submission, not before the read-through

4. **Rebuild `submission/` from `working/`.** Everything in it is the v18.6
   package: manuscript, supplement, figures, and a title page whose word count
   still reads 3,590 / 245 against the current 3,979 / 250.
5. **Two open items in `submission/AUTHOR_INFO_NEEDED.md`**: verify Jing Su's
   ORCID (it was inferred from dblp and Crossref, not read off an IU page), and
   write the AI-use statement, which JAMIA wants in the cover letter *and* in
   Methods or Acknowledgements — two places, not one.
6. **CRediT roles, funding and conflicts go into the ScholarOne form** per
   author. Having them in the document does not satisfy the system.
7. **STROBE / RECORD checklist** has never been done.

## Housekeeping

- The Workbench app `AoU_Jupyter_ComputeEngine_20260901` may still be running at
  $0.24/hr. Stop it if nothing else needs it.
- `results/` blobs remain in the history of ~60 commits. The lab decided to
  leave them; only the tip was cleaned (`8c0b56d`).

## Standing rules that produced this state

- Verify artifacts by **content fingerprint**, never by path or mtime. Five
  files during this reconciliation had the right path, a recent timestamp, and
  pre-correction contents.
- Every interval read off a screen goes through the log-scale symmetry check
  `2·ln(AOR) − ln(lo) − ln(hi) ≈ 0`, with the tolerance computed from the
  printed precision. Four misreads caught, no false alarms.
- When the prose and a generated table disagree, the table wins.
- Figure 1's counts are guarded by `figures/fig1_consort_check.py`. Run it after
  any edit to the diagram; it reads the file and asserts both flow chains.
