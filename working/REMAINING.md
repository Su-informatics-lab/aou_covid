# What the manuscript still needs · 2026-09-02

Current draft: `working/JAMIA_manuscript_v19.0.docx` (3,968 words, limit 4,000)
and `working/JAMIA_supplementary_v19.0.docx`. Full round record in
`reviews/2026-09-02_v19_platform_completion.md`.

## Blocking

1. **Figures 1 and 2 (draw.io), by the PI.** Panel (a) All of Us: exclusion box
   437, `Enrollment date` → `Survey date`, counts 25,160 → 4,064 / 21,096, 3,997
   with complete matching variables, 19,520 observations in 3,997 strata with
   15,523 controls. Panel (b) MarketScan: the whole CONSORT chain changed.
   Per-box values are in `working/MS_SUPPLEMENT_UPDATES.md`.
2. **eTable 10b Panel B.** The MarketScan variance comparison is the last
   `[STALE]` marker in the supplement. Submit `ms_variance_sensitivity.sbatch` on
   Quartz; it guards its own input and prints the finished table.
3. **A manual read-through.**

## Not blocking

- STROBE / RECORD reporting checklist (stage 8) has not been done.
- `submission/` still holds the v18.6 package. Rebuild it from `working/` once
  the two figures land.
- `results/` blobs remain in the history of ~60 commits. The lab decided to leave
  them; only the tip was cleaned (`8c0b56d`).

## Standing rules that produced this state

- Verify artifacts by **content fingerprint**, never by path or mtime. Four files
  during this reconciliation had the right path, a fresh timestamp, and
  pre-correction contents.
- Every interval read off a screen goes through the log-scale symmetry check
  `2·ln(AOR) − ln(lo) − ln(hi) ≈ 0`, with the tolerance computed from the printed
  precision. It has caught four misreads and produced no false alarm.
- When the prose and a generated table disagree, the table wins.
