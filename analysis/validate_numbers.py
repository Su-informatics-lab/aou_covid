#!/usr/bin/env python3
"""Assert every number the JAMIA manuscript prints against the artifact it came from.

    bash analysis/gate.sh check     # fails on the first drift; belongs in the build
    bash analysis/gate.sh ledger    # writes submission/CLAIM_LEDGER.md

Why this file exists
--------------------
At the v18.5 audit the manuscript disagreed with this repository in 29 cells of
Table 1, in every pre-matching SMD, and in eTable 14, where a P of 0.068 was
printed as 0.03. Every one of those was a transcription drift: the pipeline was
right and the document had fallen behind it. Nothing caught them because nothing
was checking. Each assertion below is one of those failures, turned into a test.

Three rules while extending this file.

  * Assert against a committed artifact, never a recomputation. Recomputing here
    would just move the drift somewhere else.
  * Use `v.interval` for an estimate and its bounds. Three separate `require`
    calls all pass when the bounds came from a different run than the estimate,
    because each number does appear somewhere.
  * Put every retired denominator in `v.banned`. Matching a small set of numbers
    the study has carried and dropped is far more reliable than parsing
    sentences, because the sentence around a stale number usually changed too.
"""

from ledger import Validator

RESULTS = "results"


def _num(x):
    return float(str(x).replace(",", "").strip())


def assertions(v: Validator, text: str) -> None:

    # ================================================================== TABLE 1
    # The v18.5 failure. Table 1's MarketScan column was the pre-trim,
    # pre-index-restriction set while its N row was post-trim, so the column
    # summed to 139,472 / 557,888 against a stated 139,468 / 554,214.
    aou = v.frame(f"{RESULTS}/aou_v7/table1_demographics.csv")
    ms = v.frame(f"{RESULTS}/ms/table1_demographics.csv")

    for frame, cohort in ((aou, "All of Us"), (ms, "MarketScan")):
        n = v.one(frame, Variable="N")
        v.require(text, n["Cases_n"], f"{cohort} matched cases, Table 1 N row")
        v.require(text, n["Controls_n"], f"{cohort} matched controls, Table 1 N row")

    # The direction check that would have caught the stale comorbidity block:
    # a crude rate lower in cases must not sit beside an AOR above 1.
    cross = v.frame(f"{RESULTS}/tables/eTable_S10_crosssite.csv")
    for label, csv_row in (("Chronic Pulmonary Disease", "Chronic Pulmonary Disease"),
                           ("Liver Disease Mild", "Liver Disease Mild"),
                           ("Rheumatic Disease", "Rheumatic Disease"),
                           ("Peptic Ulcer Disease", "Peptic Ulcer Disease"),
                           ("Malignancy", "Malignancy")):
        t1 = v.one(ms, Variable=f"  {label}")
        ao = v.one(cross, Variable=csv_row)
        crude_up = _num(t1["Cases_pct"].strip("()")) > _num(t1["Controls_pct"].strip("()"))
        aor_up = _num(ao["MS AOR (95% CI)"].split(" ")[0]) > 1.0
        if crude_up != aor_up:
            v._fail(
                f"Table 1 vs eTable 10 disagree in direction for {label}: "
                f"crude {t1['Cases_pct']} vs {t1['Controls_pct']}, "
                f"AOR {ao['MS AOR (95% CI)']}. This is the pre-trim signature."
            )

    # ================================================================== TABLE 3
    t3 = v.frame(f"{RESULTS}/tables/table3_sdoh_summary.csv")

    def sdoh(domain, variable, label):
        r = v.one(t3, Domain=domain, Variable=variable)
        d_lo, d_hi = r["Domain 95% CI"].split("–")
        j_lo, j_hi = r["Joint 95% CI"].split("–")
        d = r["Domain AOR"].rstrip("*")
        j = r["Joint AOR"].rstrip("*")
        v.interval(text, _num(d), _num(d_lo), _num(d_hi), f"{label}, domain-specific")
        v.interval(text, _num(j), _num(j_lo), _num(j_hi), f"{label}, joint")

    sdoh("Insurance", "Medicaid", "Medicaid")
    sdoh("Income", "<$10K", "income below $10,000")
    sdoh("Income", "$10–25K", "income $10,000–24,999")
    sdoh("Employment", "Unemployed", "unemployment")
    sdoh("Housing", "Rent", "renting")
    # The two brackets that make the income pattern non-monotonic. They are
    # significant in the joint model and larger than the lowest stratum, and the
    # Abstract and Conclusions must say so.
    sdoh("Income", "$100–150K", "income $100,000–149,999")
    sdoh("Income", "$150–200K", "income $150,000–199,999")

    # ============================================================ RACE ATTENUATION
    att = v.frame(f"{RESULTS}/tables/eTable_S12_race_attenuation.csv")
    base = v.one(att, Adjustment="Base (no SDoH)")
    joint = v.one(att, Adjustment="+ All SDoH jointly")
    for row, lab in ((base, "Black-race AOR, base model"),
                     (joint, "Black-race AOR, joint SDoH model")):
        est, rng = row["Black AOR (95% CI)"].split(" (")
        lo, hi = rng.rstrip(")").split("–")
        v.interval(text, _num(est), _num(lo), _num(hi), lab)
    v.require(text, joint["% attenuation"].rstrip("%"),
              "joint SDoH attenuation of the Black-race coefficient, %")

    # ============================================================ CROSS-COHORT
    for name, lab in (("Female sex", "female sex"),
                      ("Omicron wave", "Omicron wave"),
                      ("Cerebrovascular Disease", "cerebrovascular disease"),
                      ("AIDS", "AIDS")):
        r = v.one(cross, Variable=name)
        for col, side in (("AoU AOR (95% CI)", "All of Us"),
                          ("MS AOR (95% CI)", "MarketScan")):
            cell = r[col].replace("*", "")
            if cell.strip() in {"—", "-", ""}:
                continue
            est, rng = cell.split(" (")
            lo, hi = rng.rstrip(")").split("–")
            v.interval(text, _num(est), _num(lo), _num(hi), f"{lab}, {side}")

    # ============================================================ WAVE / INCOME
    wave = v.frame(f"{RESULTS}/tables/eTable_S13_wave_income.csv")
    for w, inc, lab in (("Pre-Delta", "<$10,000", "pre-Delta income below $10,000"),
                        ("Delta", "<$10,000", "Delta income below $10,000"),
                        ("Omicron", "<$10,000", "Omicron income below $10,000"),
                        ("Pre-Delta", "$100–150K",
                         "pre-Delta income $100,000–149,999")):
        r = v.one(wave, Wave=w, Income=inc)
        est, rng = r["AOR (95% CI)"].split(" (")
        lo, hi = rng.rstrip(")").split("–")
        v.interval(text, _num(est), _num(lo), _num(hi), lab)

    # ================================================================ AIDS / eT14
    # eTable 14 printed 0.74 (0.56-0.98), P = 0.03 for a result the pipeline
    # returns as 0.76 (0.57-1.02), P = 0.068. A null was published as significant.
    aids = v.frame(f"{RESULTS}/aou_v7/aids_sensitivity.csv")
    a = v.one(aids, variable="AIDS", phenotype="Two-step (HIV+OI)")
    v.interval(text, _num(a["AOR"]), _num(a["CI_lower"]), _num(a["CI_upper"]),
               "AoU AIDS, two-step phenotype", dp=2)
    if _num(a["p_value"]) >= 0.05 and _num(a["CI_lower"]) < 1.0 < _num(a["CI_upper"]):
        # Ban the distinctive wrong interval, not the bare P value: "0.03" also
        # appears legitimately as the post-matching |SMD| threshold.
        v.banned(text, "0.74 (0.56",
                 "eTable 14 printed a significant AIDS estimate for a result the "
                 "pipeline returns as 0.76 (0.57-1.02), P = 0.068")

    # ============================================================== SENSITIVITY
    sens = v.frame(f"{RESULTS}/tables/eTable_S16_sensitivity.csv")
    for var, lab in (("f.incomeless_10k", "S3 income below $10,000"),
                     ("f.housingRent", "S3 renting")):
        r = v.one(sens, sensitivity="S3", variable=var)
        v.interval(text, _num(r["AOR"]), _num(r["CI_lower"]), _num(r["CI_upper"]), lab)

    # ==================================================== RETIRED DENOMINATORS
    # Every number the study has carried and dropped. If one reappears the
    # manuscript has been rebuilt from a stale source.
    v.allow(r"eTable 12b|29\.1|attenuation", "2.98 and 29.1 are live Delta-wave values")
    v.allow(r"[Pp]re-matching|hospitalized|narrowing to",
            "139,472 is the correct MarketScan count BEFORE matching and the trim; "
            "it is legitimate in Figure 1 and eTable 8, and wrong only as a "
            "matched-cohort N, which the Table 1 assertions above enforce")

    for value, why in [
        # pre-trim / pre-index-restriction MarketScan Table 1
        ("38,472", "pre-trim MarketScan chronic pulmonary, cases"),
        ("140,660", "pre-trim MarketScan chronic pulmonary, controls"),
        ("377,888", "pre-trim MarketScan female controls"),
        ("557,888", "pre-trim MarketScan control observations"),
        ("139,472 cases", "pre-match MarketScan case count used as an N"),
        ("109,739", "pre-trim MarketScan vaccinated controls"),
        ("20,199", "pre-index-restriction MarketScan mild liver disease"),
        ("9,080", "pre-index-restriction MarketScan myocardial infarction"),
        # wrong standardized mean differences
        ("0.554", "MatchIt reports 0.489 for the All of Us diagnosis-count SMD"),
        ("0.700", "MatchIt reports 0.613 for the MarketScan diagnosis-count SMD"),
        # the invalid predicted probability
        ("1.31-fold", "inverse logit of a centred clogit linear predictor; the "
                      "identified quantity is the profile odds ratio"),
        ("model-predicted probability", "not identified by a conditional "
                                        "logistic model"),
        # eTable 14
        ("1.59 (1.38", "MarketScan AIDS value present in no pipeline output"),
    ]:
        v.banned(text, value, why)

    # ==================================================================== FIGURES
    for i in range(1, 6):
        v.figure(f"results/figures/Figure{i}.pdf",
                 f"submission/03_figures/pdf/Figure{i}.pdf")


# ---------------------------------------------------------------------------
# NOT ASSERTED, and why. The ledger prints unasserted numbers; these are the
# ones we know about and have decided about, so they are recorded here too.
#
#   eTable 12b, eTable 12c  -- no committed artifact. 02c writes
#       wave_stratified_race_attenuation.csv, wave_stratified_race.csv and
#       wave_stratified_insurance.csv, none of which is in the repository. The
#       values survive only as constants in make_figures.py. 02c now fails
#       loudly if they are absent; re-run it on the Workbench and add the
#       assertions here. Until then eTable 12b/12c are UNVERIFIED.
#
#   Effective sample sizes (6,952 / 379,100) -- in 07e_matchit_summary.txt,
#       which is free text rather than a frame. Parse it or move the numbers
#       into a CSV.
#
#   Figures 1 and 2 -- hand-drawn diagrams, no numeric artifact behind them
#       beyond the counts already asserted from Table 1.
# ---------------------------------------------------------------------------
