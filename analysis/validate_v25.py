# -*- coding: utf-8 -*-
"""Assert every number the v24 manuscript prints against the artifact it came
from, and then say which printed numbers no assertion covers.

Two passes, because they catch different failures.

  check    each claim is asserted against the frozen value it should equal. A
           failure here means the manuscript and the artifacts disagree, and the
           thing to change is the manuscript.
  ledger   the same assertions, recorded instead of enforced, so the mapping is
           readable rather than merely exit-zero.
  uncovered  every number in the manuscript that no assertion touches. This is
           the pass that matters most, because a validator only ever proves
           things about the claims someone remembered to write down.
  displays   Table 2 against Figure 1: the same estimate, rendered twice, must
           print the same string. This pass found two intervals rounded one
           step too far, which the claim check could not have caught because
           the manuscript and the table agreed with each other and both were
           wrong.

The frozen values below are transcribed from the run results in working/v23/
and, for every COVID-19 estimate the education merge touches and for the two
restriction analyses, from working/v24/03n_RESULTS.md (source key "03n").
Each carries the file it came from, so a reader can follow any single number
back to the script that produced it without opening the platform.
"""

import re
import sys
from collections import OrderedDict

SRC = {
    "03n": "working/v24/03n_RESULTS.md",
    "03o": "working/v25/03o_RESULTS.md",
    "03oAB": "working/v25/03o_RESULTS.md, COVID-19 A/B (r4_covid/AB_attenuation.csv)",
    "03h": "working/v23/03h_03i_RESULTS.md",
    "03d": "working/v23/03d_03e_RESULTS.md",
    "03f": "working/v23/03f_flu_mi40_RESULTS.md",
    "03p": "working/v25/platform_03p/ (P_refit.csv, README.md)",
    "t1": "working/v23/flu_table1_RESULTS.md",
    "ms19": "the previous version, carried unchanged",
    "cited": "the cited paper (full text read 2026-09-23 where noted in LIT_NOVELTY.md)",
    "policy": "Treasury and DOL official pages, accessed 2026-09-23",
    "03q": "working/v25/platform_03q/ (covid_era_refit.csv, flu_era_refit.csv, *_calib_bootstrap.csv)",
    "03u": "working/v25/platform_03u/ (covid_asym_test.csv, flu_asym_test.csv; 03u_asym.R)",
    "03v": "working/v25/platform_03u/ (covid_crude.csv, flu_crude.csv; 03v_crude.py)",
    "e8": "working/v25/tables/eTable8_era.csv",
    "t2": "working/v25/tables/Table2_data.csv",
    "fig2": "results/figures/v25/Figure2_era_attenuation_data.csv, log(alone) - log(joint): 0.329, 0.317, 0.313",
    "derived": "arithmetic on asserted values (see gloss)",
    "e13": "supplement eTable 13 (zcode/aou_v7/10_zcode_capture_vs_survey.csv: 414/3817 = 10.85%, 10.8%)",
    "03w": "working/v25/platform_03w/ (covid_sens_r6.csv, flu_sens_r6.csv, lag_by_era.txt; 03w_sens.R)",
}

# claim key -> (literal string that must appear, source key, one-line gloss)
CLAIMS = OrderedDict(
    [
        ("cohort_covid_cases", ("3,997 COVID-19 cases", "ms19", "matched cases")),
        (
            "cohort_covid_ctrl",
            ("15,523 control observations", "ms19", "control observations"),
        ),
        (
            "cohort_flu",
            (
                "1,672 influenza case person-seasons and 6,616 control observations",
                "t1",
                "influenza arm",
            ),
        ),
        (
            "cohort_screened",
            ("25,160", "ms19", "COVID-19 adults with record and survey data"),
        ),
        ("cohort_hosp", ("4,064 (16.2%)", "ms19", "met the hospitalization phenotype")),
        (
            "cohort_ctrl_people",
            (
                "9,784 individuals",
                "ms19",
                "individuals contributing control observations",
            ),
        ),
        (
            "cohort_flu_people",
            ("1,648 participants", "t1", "participants contributing influenza cases"),
        ),
        (
            "cohort_flu_ctrl_people",
            (
                "3,764 participants",
                "t1",
                "participants contributing influenza controls",
            ),
        ),
        (
            "abs_female",
            (
                "60.3% female (mean [SD] age, 57.5 [16.2] years)",
                "t1",
                "COVID-19 case sex and age",
            ),
        ),
        (
            "abs_flu_female",
            ("65.2% female (56.3 [16.3] years)", "t1", "influenza case sex and age"),
        ),
        ("survey_lag", ("692 days (IQR, 286-985 days)", "ms19", "survey-to-index lag")),
        ("wave_split", ("96.1%", "ms19", "strata in which wave varies")),
        (
            "version_n",
            (
                "2,153 of 13,781 matched persons",
                "03p",
                "persons captured only by the original insurance item",
            ),
        ),
        (
            "inc_alone_joint",
            ("1.72 alone to 1.50 jointly", "03n", "income <$10k, COVID-19"),
        ),
        (
            "inc_flu",
            (
                "22% (95% CI, 0% to 48%) in influenza (1.88 to 1.64)",
                "03o",
                "income <$10k attenuation, influenza",
            ),
        ),
        ("med_alone_joint", ("(1.54 to 1.11)", "03n", "Medicaid, COVID-19")),
        ("med_flu", ("(1.60 to 0.93)", "03h", "Medicaid, influenza")),
        ("edu", ("(1.30 to 1.01)", "03n", "education below GED, COVID-19")),
        (
            "flu_period",
            (
                "1.72 in the 2 seasons before SARS-CoV-2 and 1.64 in the 2 seasons after",
                "03f",
                "income <$10k within-period refits, influenza",
            ),
        ),
        (
            "flu_int_model",
            (
                "(in a period-interaction model, 1.67 and 1.66; ratio of odds ratios, 0.99; 95% CI, 0.66-1.49)",
                "03o",
                "income <$10k, period-interaction model, and its ROR, influenza",
            ),
        ),
        (
            "flu_ror_inc",
            ("0.99; 95% CI, 0.66-1.49", "03o", "income ROR after/before, influenza"),
        ),
        (
            "covid_waves_inc",
            (
                "1.44 before Delta, 1.57 during Delta, and 1.55 during Omicron",
                "03n",
                "income <$10k by wave",
            ),
        ),
        (
            "covid_ror_inc",
            ("1.07 (95% CI, 0.83-1.38)", "03o", "income ROR Omicron/pre-Delta"),
        ),
        (
            "int_inc",
            ("(P = .59 and P = .91)", "03d", "income x era, COVID-19 and influenza"),
        ),
        ("int_ins", ("(P = .002 and P = .01)", "03d", "insurance x era")),
        (
            "med_pre",
            (
                "1.93 alone and 1.38 (95% CI, 1.16-1.65) jointly",
                "03o",
                "Medicaid pre-Delta",
            ),
        ),
        (
            "med_later_alone",
            ("(1.23 and 1.25)", "03o", "Medicaid alone, Delta and Omicron"),
        ),
        (
            "med_later_joint",
            (
                "0.89 [95% CI, 0.68-1.17] and 0.91 [95% CI, 0.75-1.11]",
                "03o",
                "Medicaid joint, Delta and Omicron",
            ),
        ),
        (
            "med_ror",
            ("0.66 (95% CI, 0.52-0.83)", "03o", "Medicaid ROR Omicron/pre-Delta"),
        ),
        (
            "flu_med",
            (
                "jointly 1.46 (95% CI, 0.97-2.19) before the pandemic and 0.76 (95% CI, 0.58-1.00)",
                "03o",
                "Medicaid joint by period, influenza",
            ),
        ),
        (
            "flu_med_ror",
            (
                "(in a period-interaction model, 1.13 and 0.84; ratio, 0.74; 95% CI, 0.51-1.07)",
                "03o",
                "Medicaid, period-interaction model, and ROR, influenza",
            ),
        ),
        (
            "refit_new",
            (
                "the COVID-19 Medicaid ratio was 0.66 (95% CI, 0.52-0.84; eMethod 1)",
                "03p",
                "current-item respondents",
            ),
        ),
        (
            "med_share_flu",
            (
                "Income accounted for 58% and 63% of the Medicaid attenuation",
                "03o",
                "KHB share via income, Medicaid, both arms",
            ),
        ),
        (
            "med_emp_flu",
            (
                "employment for 42% and 30% (eTable 19)",
                "03o",
                "KHB share via employment, Medicaid, influenza",
            ),
        ),
        ("race_joint", ("2.07; 95% CI, 1.87-2.30", "03n", "Black vs White, joint")),
        (
            "race_flu",
            (
                "34% (95% CI, 23% to 46%) in influenza",
                "03o",
                "Black attenuation, influenza",
            ),
        ),
        (
            "r1",
            (
                "income did not vary by wave (P = .48) and insurance did (P = .01; Medicaid 1.51 before Delta, 0.99 during Omicron)",
                "03n",
                "pre-index surveys",
            ),
        ),
        ("r3", ("P = .26 and P = .009", "03n", "laboratory-confirmed")),
        ("mi_ind", ("(AOR, 1.19; eTable 9)", "ms19", "Medicaid, missing-indicator")),
        ("ontario", ("56.9%", "cited", "Wang et al, mediated share")),
        ("nl", ("14% to 19%", "cited", "Milkovska et al, vaccination share")),
        (
            "c_inc_att",
            ("26% (95% CI, 9% to 44%)", "03oAB", "income <$10k attenuation, COVID-19"),
        ),
        (
            "c_med_att",
            ("75% (95% CI, 52% to 112%)", "03oAB", "Medicaid attenuation, COVID-19"),
        ),
        (
            "c_khb",
            (
                "more than 2 percentage points, so rescaling",
                "03oAB",
                "max |KHB - log| 0.64 COVID, 1.5 influenza",
            ),
        ),
        (
            "c_med_shares",
            (
                "and employment for 42% and 30% (eTable 19)",
                "03oAB",
                "KHB shares, Medicaid",
            ),
        ),
        (
            "c_black_att",
            ("16% (95% CI, 12% to 21%)", "03oAB", "Black attenuation, COVID-19"),
        ),
        (
            "abs_black",
            (
                "accounted for 16% of the Black–White log odds ratio in COVID-19 and 34% in influenza",
                "03oAB",
                "abstract",
            ),
        ),
        (
            "abs_flu_med",
            (
                "influenza, imprecisely (ratio, 0.74; 95% CI, 0.51-1.07)",
                "03o",
                "abstract",
            ),
        ),
        (
            "flu_pan_inc",
            (
                "(1.12; 95% CI, 0.45-2.74)",
                "03f",
                "income <$10k, pandemic influenza, within-period refit",
            ),
        ),
        (
            "unemp_rent_att",
            (
                "out of work or unable to work was attenuated by 43% and 39%, and renting by 55% and 59%",
                "03oAB",
                "unemployment and renting attenuation, COVID-19 and influenza",
            ),
        ),
        (
            "edu_att",
            (
                "education below GED lost 95% in COVID-19 (1.30 to 1.01)",
                "03oAB",
                "education attenuation, COVID-19",
            ),
        ),
        (
            "abs_inc_joint",
            (
                "(AOR, 1.50 in COVID-19 and 1.64 in influenza)",
                "03n",
                "abstract, income <$10k joint",
            ),
        ),
        (
            "q_both",
            (
                "(P = .43 and P = .72) and insurance did (P = .002 and P = .01)",
                "03q",
                "era tests under case-by-era imputation",
            ),
        ),
        (
            "crude_inc",
            (
                "21.9% of those with income below $10 000 and 11.5% of those with $35 000 to $99 999",
                "03v",
                "crude hospitalization, COVID-19, 675/3,082 and 793/6,925",
            ),
        ),
        (
            "crude_waves",
            (
                "10.2, 10.3, and 10.6 percentage points",
                "03v",
                "crude risk difference by wave, COVID-19",
            ),
        ),
        (
            "zcode",
            (
                "5.8% of those reporting being out of work or unable to work had a Z56 code",
                "e13",
                "208 of 3,608",
            ),
        ),
        (
            "asym_med",
            (
                "the Medicaid ratio 0.57 (95% CI, 0.43-0.76)",
                "03u",
                "Medicaid ROR, combined model",
            ),
        ),
        (
            "nearpoor",
            (
                "1.38 in COVID-19 and 1.92 in influenza (Table 2)",
                "t2",
                "income $10-25k, joint",
            ),
        ),
        (
            "shared",
            (
                "(0.33, 0.32, and 0.31 on the log scale)",
                "fig2",
                "Medicaid shared part by wave, COVID-19",
            ),
        ),
        (
            "medicare_waves",
            (
                "1.17 before Delta, 0.79 during Omicron",
                "e8",
                "Medicare joint, pre-Delta and Omicron, COVID-19",
            ),
        ),
        (
            "medicare_ror",
            (
                "0.65; 95% CI, 0.51-0.84",
                "03u",
                "Medicare ROR Omicron/pre-Delta, combined model",
            ),
        ),
        (
            "medicare_flu",
            ("(1.03; 95% CI, 0.66-1.61", "03u", "Medicare ROR after/before, influenza"),
        ),
        (
            "asym",
            (
                "2.27 (95% CI, 1.38-3.74)",
                "03u",
                "ratio of RORs, income <$10k / Medicaid, Omicron vs pre-Delta",
            ),
        ),
        (
            "asym_d1",
            (
                "differed jointly across Delta and Omicron (P < .001)",
                "03u",
                "D1 F = 7.78 on 2 df, P = .0004",
            ),
        ),
        (
            "asym_inc",
            (
                "the income ratio was 1.30 (95% CI, 0.97-1.74)",
                "03u",
                "income ROR, combined model",
            ),
        ),
        ("asym_flu", ("1.85 (95% CI, 0.81-4.20", "03u", "ratio of RORs, influenza")),
        (
            "kp_gap",
            (
                "hospitalized about 10 percentage points more often than those with $35 000 to $99 999 in every era",
                "03v",
                "Key Points; crude gaps 10.2-12.0 points (eTable 21)",
            ),
        ),
        (
            "abs_gap",
            (
                "10 to 12 percentage points higher with income below $10 000 than with $35 000 to $99 999 in every era of both viruses (COVID-19 overall, 21.9% vs 11.5%)",
                "03v",
                "abstract; era gaps 10.2, 10.3, 10.6 and 12.0, 10.3, 11.0",
            ),
        ),
        (
            "crude_flu_eras",
            (
                "12.0, 10.3, and 11.0 in the 3 influenza periods",
                "03v",
                "crude gaps, influenza, by period",
            ),
        ),
        (
            "crude_mid_range",
            (
                "ranged from 7.2% to 16.2% and the ratio of the 2 proportions from 1.68 to 2.43",
                "03v",
                "middle-band proportion range and ratio range across 6 eras",
            ),
        ),
        (
            "inc_shared",
            (
                "as did income's (0.14 in each wave)",
                "fig2",
                "log(1.661/1.445)=0.139, log(1.808/1.568)=0.142, log(1.779/1.551)=0.137",
            ),
        ),
        (
            "disc_ratio",
            (
                "in COVID-19, about 1 in 5 against 1 in 9",
                "derived",
                "20.8%-22.6% and 10.2%-12.4% by wave (03v)",
            ),
        ),
        (
            "flat35b",
            (
                "In COVID-19 the income gradient was flat above $35 000 (11.3% at $100 000 or more); in influenza it continued modestly (13.6% and 11.3%; Figure 2B)",
                "03v",
                "COVID 542/4,786; influenza 317/2,335 and 179/1,580",
            ),
        ),
        (
            "miss_inc",
            (
                "hospitalized as often as the lowest band (21.4% in COVID-19)",
                "03v",
                "1,086/5,064",
            ),
        ),
        (
            "med_gap",
            (
                "from 15.3 to 9.4 and 9.7 points (Figure 1B)",
                "03v",
                "Medicaid-employer crude RD by wave",
            ),
        ),
        (
            "z59",
            (
                "10.8% of those reporting income below $25 000 a Z59 code",
                "e13",
                "414/3,817",
            ),
        ),
        (
            "lag_med",
            (
                "median, 499 days before Delta and 972 during Omicron among COVID-19 cases",
                "03w",
                "lag_by_era.txt",
            ),
        ),
        (
            "sens_med_range",
            (
                "Medicaid ratio of odds ratios ranged from 0.57 to 0.73, with every insurance-by-era test at P ≤ .007",
                "03w",
                "lag 0.57 ... site 0.73; D1 max .007 (region, harmB)",
            ),
        ),
        (
            "sens_inc_range",
            (
                "the income ratio ranged from 0.98 to 1.46, the upper value after adjustment for EHR site (era test, P = .48)",
                "03w",
                "tip1 0.98; site 1.46, D1 .48",
            ),
        ),
        (
            "exp_no",
            (
                "Among residents of nonexpansion states (595 cases), Medicaid fell further (0.20; 95% CI, 0.08-0.51)",
                "03w",
                "expansion_No",
            ),
        ),
        (
            "exp_yes",
            (
                "among residents of expansion states it was 0.60 (95% CI, 0.45-0.79)",
                "03w",
                "expansion_Yes",
            ),
        ),
        (
            "emp_rise",
            (
                "rose from 9.4% before Delta to 11.7% during Delta",
                "03v",
                "employer 336/3,560 and 135/1,157",
            ),
        ),
        (
            "z59_disc",
            (
                "fewer than 1 in 9 participants reporting low income carried a Z59 code",
                "e13",
                "10.8% < 11.1%",
            ),
        ),
    ]
)


def load(path):
    return open(path, encoding="utf-8").read()


def nosep(t):
    """Strip thousands separators so a house-style change to the digit
    grouping cannot present itself as a failed transcription check."""
    prev = None
    while prev != t:
        prev = t
        t = re.sub(r"(?<=\d)[,\u2009 ](?=\d{3}(?!\d))", "", t)
    return t


def run(ms_path, mode):
    txt = load(ms_path)
    body = txt.split("## Key Points", 1)[1]
    #  The reference list is bibliographic noise for this purpose: DOIs, years,
    #  volumes and page ranges are numbers nobody is asserting anything about.
    body = body.split("## References", 1)[0]
    ok, bad = [], []
    for key, (lit, src, gloss) in CLAIMS.items():
        (ok if nosep(lit) in nosep(body) else bad).append((key, lit, src, gloss))

    if mode == "check":
        for key, lit, src, gloss in bad:
            print("MISSING  %-24s %-34s %s" % (key, lit, gloss))
        print("\n%d of %d claims found in the manuscript." % (len(ok), len(CLAIMS)))
        return 1 if bad else 0

    if mode == "ledger":
        print("# Claim ledger — v25\n")
        print("Every number below is asserted by `analysis/validate_v25.py`. The")
        print("source column names the run result the value was transcribed from.\n")
        print("| claim | value as printed | source | what it is |")
        print("|---|---|---|---|")
        for key, lit, src, gloss in list(CLAIMS.items()) and [
            (k, v[0], v[1], v[2]) for k, v in CLAIMS.items()
        ]:
            mark = "" if nosep(lit) in nosep(body) else " **NOT FOUND**"
            print("| `%s` | %s%s | %s | %s |" % (key, lit, mark, SRC[src], gloss))
        return 0

    if mode == "uncovered":
        asserted = " ".join(v[0] for v in CLAIMS.values())
        nums = set()
        for m in re.finditer(r"(?<![\w.])\d[\d,]*(?:\.\d+)?%?", body):
            nums.add(m.group(0))
        loose = sorted(
            n for n in nums if n not in asserted and len(n.replace(",", "")) > 1
        )
        print("Numbers in the manuscript that no assertion covers:\n")
        for n in loose:
            ctx = re.search(r".{0,60}(?<![\w.])" + re.escape(n) + r".{0,60}", body)
            print("  %-12s %s" % (n, (ctx.group(0).replace("\n", " ") if ctx else "")))
        print(
            "\n%d uncovered tokens. Each is either arithmetic the text does"
            % len(loose)
        )
        print("itself, a figure from a cited paper, a degree of freedom, or a")
        print("number nobody has checked. They look identical until someone looks.")
        return 0


DISPLAY_MAP = {
    ("Insurance (vs employer-sponsored)", "Medicaid"): ("insurance", "Medicaid"),
    ("Insurance (vs employer-sponsored)", "Medicare"): ("insurance", "Medicare"),
    ("Insurance (vs employer-sponsored)", "Other or none"): ("insurance", "Other_None"),
    ("Insurance (vs employer-sponsored)", "Not administered"): ("insurance", "Missing"),
    ("Household income (vs $35 000-99 999)", "<$10 000"): ("income", "less_10k"),
    ("Household income (vs $35 000-99 999)", "$10 000-24 999"): ("income", "10k_25k"),
    ("Household income (vs $35 000-99 999)", "$25 000-34 999"): ("income", "25k_35k"),
    ("Household income (vs $35 000-99 999)", "$100 000-149 999"): (
        "income",
        "100k_150k",
    ),
    ("Household income (vs $35 000-99 999)", "$150 000-199 999"): (
        "income",
        "150k_200k",
    ),
    ("Household income (vs $35 000-99 999)", ">=$200 000"): ("income", "more_200k"),
    ("Employment (vs employed)", "Unemployed"): ("employment", "Unemployed"),
    ("Employment (vs employed)", "Retired or other"): ("employment", "Others"),
    ("Employment (vs employed)", "Student"): ("employment", "Student"),
    ("Housing tenure (vs owns home)", "Rents"): ("housing", "Rent"),
    ("Housing tenure (vs owns home)", "Other arrangement"): ("housing", "Others"),
    ("Housing stability (vs stable)", "Unstable"): ("stability", "Unstable"),
    ("Education", "Below high school or GED"): ("education", "Below_GED"),
    ("Education", "High school, GED, or some college"): ("education", "GED_or_College"),
    ("Education", "College graduate or higher"): ("education", "Advanced"),
}


def displays(root):
    """Table 2 and Figure 1 render the same estimates. They must agree."""
    import csv
    import os
    from decimal import ROUND_HALF_UP, Decimal

    f1 = {
        (r["arm"], r["domain"], r["level"]): r
        for r in csv.DictReader(
            open(
                os.path.join(root, "results/figures/v24/Figure1_data.csv"),
                encoding="utf-8",
            )
        )
    }
    t2 = list(
        csv.DictReader(
            open(
                os.path.join(root, "working/v24/tables/Table2_data.csv"),
                encoding="utf-8",
            )
        )
    )
    q = lambda v: str(Decimal(v).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    bad = 0
    for r in t2:
        dom, lev = DISPLAY_MAP[(r["section"], r["label"])]
        for arm, col in (("COVID-19", "covid"), ("Influenza", "flu")):
            want = r[col].strip()
            hit = f1.get((arm, dom, lev))
            if hit is None:
                if want != "reference":
                    print("  MISSING  Figure 1 row for %s %s/%s" % (arm, dom, lev))
                    bad += 1
                continue
            got = "%s (%s-%s)" % (
                q(hit["joint_aor"]),
                q(hit["joint_lo"]),
                q(hit["joint_hi"]),
            )
            if got != want:
                print(
                    "  DISAGREE %-11s %-16s %-10s Table2=%-20s Figure1=%s"
                    % (dom, lev, arm, want, got)
                )
                bad += 1
    print("\nTable 2 against Figure 1: %d discrepancies." % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    if mode == "displays":
        import os

        root = (
            sys.argv[2]
            if len(sys.argv) > 2
            else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        )
        sys.exit(displays(root))
    if len(sys.argv) > 2:
        ms = sys.argv[2]
    else:
        #  The manuscript sits in ms/ in the build tree and in working/v23/ in
        #  the repository. Look in both rather than making the caller care.
        import os

        here = os.path.dirname(os.path.abspath(__file__))
        for cand in ("../ms/manuscript_v25.md", "../working/v25/manuscript_v25.md"):
            ms = os.path.join(here, cand)
            if os.path.exists(ms):
                break
    sys.exit(run(ms, mode))
