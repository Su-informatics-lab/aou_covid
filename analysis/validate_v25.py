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
    "e21": "supplement eTable 21 (working/v25/platform_03u/covid_crude.csv, flu_crude.csv; 03v_crude.py)",
    "r10": "working/v25/platform_r10/ (sens_r10_*.csv, describe_r10_*.csv, ard_*.csv, z59_*.csv; 03z_extract.py, 03z_dxlink.py, 03z_describe.R, 03z_ard.R, 03z_z59.py, 03w_sens.R SPART=R10)",
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
            "flu_int_model",
            (
                "a period-interaction model gave 1.67 in the 2 seasons before SARS-CoV-2 and 1.66 in the 2 after influenza returned (ratio of odds ratios, 0.99; 95% CI, 0.66-1.49)",
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
            (
                "(ratio, Omicron to pre-Delta, 1.07; 95% CI, 0.83-1.38; Figure 2A)",
                "03o",
                "income ROR Omicron/pre-Delta",
            ),
        ),
        (
            "int_inc",
            (
                "(P = .59 and P = .91; eTables 7 and 20)",
                "03d",
                "income x era, COVID-19 and influenza",
            ),
        ),
        (
            "med_pre",
            (
                "1.92 alone and 1.38 (95% CI, 1.16-1.65) jointly",
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
            "flu_med_ror",
            (
                "(in a period-interaction model, 1.13 before the pandemic and 0.84 after influenza returned; ratio, 0.74; 95% CI, 0.51-1.07; eFigure 8)",
                "03o",
                "Medicaid, period-interaction model, and ROR, influenza",
            ),
        ),
        (
            "race_joint",
            ("AOR was 2.07 (95% CI, 1.87-2.30", "03o", "Black vs White, joint"),
        ),
        (
            "race_flu",
            (
                "34% (95% CI, 23% to 46%) in influenza",
                "03o",
                "Black attenuation, influenza",
            ),
        ),
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
                "changed no attenuation by more than 2 points; trend models agreed",
                "03oAB",
                "max |KHB - log| 0.64 COVID, 1.5 influenza",
            ),
        ),
        (
            "c_black_att",
            ("16% (95% CI, 12% to 21%)", "03oAB", "Black attenuation, COVID-19"),
        ),
        (
            "abs_black",
            (
                "accounted for 16% (COVID-19) and 34% (influenza) of the Black–White log odds ratio",
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
                "against 43% and 39% for being out of work or unable to work and 55% and 59% for renting",
                "03oAB",
                "unemployment and renting attenuation",
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
            "shared",
            (
                "(0.33, 0.32, and 0.31 on the log scale)",
                "fig2",
                "Medicaid shared part by wave, COVID-19",
            ),
        ),
        (
            "medicare_cv",
            (
                "ratio in the model with both interactions, 0.65; 95% CI, 0.51-0.84",
                "03u",
                "Medicare ROR Omicron/pre-Delta, COVID-19, combined model 0.653 (0.509-0.837)",
            ),
        ),
        (
            "medicare_flu",
            (
                "but not in influenza (1.03; 95% CI, 0.66-1.61; eTable 22)",
                "03u",
                "Medicare ROR after/before, influenza, combined model",
            ),
        ),
        (
            "asym",
            (
                "2.27 (95% CI, 1.38-3.74; joint test across Delta and Omicron, P < .001)",
                "03u",
                "ratio of RORs; D1 F = 7.78 on 2 df, P = .0004",
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
                "hospitalized about 10 percentage points more often (crude) than those with $35 000 to $99 999 in every era",
                "e21",
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
                "ranged from 7.2% to 16.2% and the ratio of the 2 proportions from 1.68 to 2.44",
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
                "from 15.3 to 9.4 and 9.7 points (eTable 21)",
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
                "the income ratio ranged from 0.98 to 1.45, the upper value after adjustment for EHR site (era test, P = .50)",
                "03w",
                "tip1 0.98; site_pre 1.447 (1.065-1.965), D1 .499 (03w SPART=SITEPRE, merged by 03w_merge_sitepre.py)",
            ),
        ),
        (
            "exp_yes",
            (
                "Medicaid fell in both expansion and nonexpansion states, imprecisely in the latter",
                "03w",
                "expansion_Yes",
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
        (
            "housing_stab",
            (
                "(COVID-19 AOR, 1.00) and fell slightly below 1 jointly (0.88; 95% CI, 0.79-0.97; influenza, 0.97; 95% CI, 0.83-1.13)",
                "03n",
                "unstable housing alone 1.0021 (0.9080-1.1060), joint 0.8765 (0.7899-0.9727); influenza joint 0.97 (0.83-1.13), 03f",
            ),
        ),
        (
            "r10_preadm",
            (
                "excluded (ratio, 0.66)",
                "r10",
                "sens_r10_covid.csv no_preadm Medicaid 0.6622",
            ),
        ),
        (
            "r10_ip_ed24",
            (
                "inpatient stay (0.64) or an emergency stay of 24 hours or more (0.65)",
                "r10",
                "case_ip 0.6358; case_ed24 0.6532",
            ),
        ),
        (
            "r10_dxwin",
            (
                "infection or respiratory diagnosis was required (0.79; 95% CI, 0.61-1.01)",
                "r10",
                "sens_r10c_covid.csv case_dxwin2 Medicaid 0.7895 (0.6149-1.0136)",
            ),
        ),
        (
            "r10_severe",
            (
                "(1.18; 95% CI, 0.79-1.75)",
                "r10",
                "case_severe Medicaid 1.1764 (0.7895-1.7530)",
            ),
        ),
        (
            "r10_link",
            (
                "54.0% of employer-insured and 85.1% of Medicaid-insured Omicron cases, 12.5 points apart after standardizing to site mix",
                "r10",
                "describe_r10_covid linked 170/315, 325/382; r10b_covid.txt site-standardized 76.1% vs 63.6%",
            ),
        ),
        (
            "r10_inc_range",
            (
                "ranged from 1.01 to 1.66",
                "r10",
                "income ROR over eTable 24A alternatives: min case_ip 1.0070, max case_dx2 1.6629",
            ),
        ),
        (
            "r10_ard_med",
            (
                "the Medicaid difference fell from 6.1 to 0.6",
                "r10",
                "ard_covid_x.csv Medicaid 6.1307, 0.6440",
            ),
        ),
        (
            "r10_z59_income",
            (
                "1.2% had a code specific to income",
                "r10",
                "z59_covid.csv income 46/3817",
            ),
        ),
        (
            "r10_z59_disc",
            ("about 1 in 80 a code specific to income", "r10", "46/3817 = 1 in 83"),
        ),
        (
            "r10_abs_range",
            (
                "across 9 alternative outcome definitions, 0.64 to 1.18",
                "r10",
                "eTable 24A Medicaid: min case_ip 0.6358, max case_severe 1.1764 (9 alternatives)",
            ),
        ),
        (
            "r10_lab",
            (
                "among laboratory-confirmed cases (0.65; 95% CI, 0.49-0.87)",
                "r10",
                "case_lab Medicaid 0.6509 (0.4854-0.8727)",
            ),
        ),
        (
            "r10_inf",
            (
                "an infection diagnosis (0.73; 95% CI, 0.56-0.95)",
                "r10",
                "case_infwin2 Medicaid 0.7273 (0.5586-0.9470)",
            ),
        ),
        (
            "r10_labdx",
            (
                "(0.95; 95% CI, 0.67-1.34)",
                "r10",
                "case_lab_dxwin2 Medicaid 0.9462 (0.6685-1.3394)",
            ),
        ),
        (
            "r10_ard_inc",
            (
                "grew from 0.9 to 3.4 percentage points (difference, 2.5; 95% CI, −0.8 to 6.2)",
                "r10",
                "ard_covid_x.csv income 0.8816, 3.3628; difference 2.48 (-0.80 to 6.24)",
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
    """eTables 20A-B and the figures render the same era-specific estimates. They
    must agree. Figure 2A plots every eTable 20A cell (alone and jointly); Figure
    1C plots the jointly adjusted ones. A withheld cell must be a dash in the
    table and empty in both figure data files (v25; the v24 Table 2 against
    Figure 1 check no longer applies because v25 Figure 1 shows no Table 2
    estimate)."""
    import csv
    import os
    import re
    from decimal import ROUND_HALF_UP, Decimal

    q = lambda v: str(Decimal(v).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    fmt = lambda a, l, h: "%s (%s-%s)" % (q(a), q(l), q(h)) if a else "\u2014"
    sup = open(
        os.path.join(root, "working/v25/supplement_v25.md"), encoding="utf-8"
    ).read()
    blk = sup[sup.index("**A. The domain alone and jointly, by era.**") :]
    blk = blk[: blk.index("**B.")]
    tab = {}
    for line in blk.splitlines():
        m = re.match(
            r"\| (Medicaid|Income <\$10 000) \| (Alone|Jointly) \|(.*)\|$", line
        )
        if m:
            cells = [c.strip() for c in m.group(3).split("|")]
            term = "medicaid" if m.group(1) == "Medicaid" else "income_lt10k"
            tab[(term, "alone" if m.group(2) == "Alone" else "joint")] = cells
    bad = 0
    f2 = csv.DictReader(
        open(
            os.path.join(root, "results/figures/v25/Figure2_era_attenuation_data.csv"),
            encoding="utf-8",
        )
    )
    for r in f2:
        col = int(r["era_order"]) - 1 + (3 if r["pathogen"] == "Influenza" else 0)
        want = tab[(r["term"], r["model"])][col]
        got = fmt(r["aor"], r["lo"], r["hi"])
        if got != want:
            print(
                "  DISAGREE Figure 2B/eFigure 8 %-9s %-12s %-6s era %s: eTable20A=%s figure=%s"
                % (r["pathogen"], r["term"], r["model"], r["era_order"], want, got)
            )
            bad += 1
    f1 = list(
        csv.DictReader(
            open(
                os.path.join(root, "results/figures/v25/Figure1_timeline_data.csv"),
                encoding="utf-8",
            )
        )
    )
    for pth, off in (("COVID-19", 0), ("Influenza", 3)):
        for term in ("medicaid", "income_lt10k"):
            rows = [r for r in f1 if r["pathogen"] == pth and r["term"] == term]
            for k, r in enumerate(sorted(rows, key=lambda r: r["start"])):
                want = tab[(term, "joint")][off + k]
                got = fmt(r["aor"], r["lo"], r["hi"])
                if got != want:
                    print(
                        "  DISAGREE eFigure 7 %-9s %-12s %s: eTable20A=%s figure=%s"
                        % (pth, term, r["era"], want, got)
                    )
                    bad += 1
    # eTable 20B against the Figure 2A forest (v26)
    blkb = sup[sup.index("**B. Ratios of odds ratios") :]
    blkb = blkb[: blkb.index("\n\n", blkb.index("| Medicaid"))]
    rowsb = {}
    for line in blkb.splitlines():
        m = re.match(r"\| (Income <\$10 000|Medicaid) \|(.*)\|$", line)
        if m:
            rowsb["medicaid" if m.group(1) == "Medicaid" else "income_lt10k"] = [
                c.strip() for c in m.group(2).split("|")
            ]
    colb = {"Delta vs pre-Delta": 0, "Omicron vs pre-Delta": 1, "After vs before": 2}
    for r in csv.DictReader(
        open(
            os.path.join(root, "results/figures/v25/Figure2_ror_data.csv"),
            encoding="utf-8",
        )
    ):
        want = rowsb[r["term"]][colb[r["contrast"]]]
        got = fmt(r["ror"], r["lo"], r["hi"])
        if got != want:
            print(
                "  DISAGREE Figure 2A %-9s %-12s %s: eTable20B=%s figure=%s"
                % (r["pathogen"], r["term"], r["contrast"], want, got)
            )
            bad += 1
    print(
        "\neTable 20A/20B against Figure 2 and eFigure 7 data: %d discrepancies." % bad
    )
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
