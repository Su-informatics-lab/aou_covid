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

R12 (2026-09-29): every COVID-19 value that depends on the pandemic wave (or on the base
model, which carries wave) is now asserted against working/v25/platform_r12/, the rerun on
the CDC COVID-NET wave boundaries; see SRC.

The frozen values below are transcribed from the run results in working/v25/inputs/ (copied from working/v23/)
and, for every COVID-19 estimate the education merge touches and for the two
restriction analyses, from working/v25/inputs/03n_RESULTS.md (source key "03n").
Each carries the file it came from, so a reader can follow any single number
back to the script that produced it without opening the platform.
"""

import re
import sys
from collections import OrderedDict

SRC = {
    "03n": "working/v25/platform_r12/jno_v24/ (R2_joint_merged.csv, R2_domain_specific_merged.csv, R2_wave_contrasts.csv, R2_wave_tests.csv; 03n_jno_reruns.R PARTS=R2, COVID-NET waves)",
    "03o": "working/v25/platform_r12/r4_covid/ (C_era_attenuation.csv, D_bounds.csv; 03o PART=CDEF, COVID-NET waves); influenza rows: working/v25/03o_RESULTS.md",
    "03oAB": "working/v25/platform_r12/r4_covid/AB_attenuation.csv (03o_ab_resume.R, COVID-NET waves); influenza rows: working/v25/03o_RESULTS.md",
    "03h": "working/v25/inputs/03h_03i_RESULTS.md",
    "03d": "working/v25/platform_r12/jno_v24/R2_wave_tests.csv (COVID-19 income x wave, COVID-NET waves); influenza: working/v25/inputs/03d_03e_RESULTS.md",
    "03f": "working/v25/inputs/03f_flu_mi40_RESULTS.md",
    "03p": "working/v25/platform_03p/ (README.md; wave-free version flags); refit: working/v25/platform_r12/jno_v24/P_refit.csv",
    "t1": "working/v25/inputs/flu_table1_RESULTS.md",
    "ms19": "the previous version, carried unchanged (wave_split rechecked in the R12 rerun: 0.9607, working/v25/platform_r12/OLD_NEW.md)",
    "cited": "the cited paper (full text read 2026-09-23 where noted in LIT_NOVELTY.md)",
    "policy": "Treasury and DOL official pages, accessed 2026-09-23",
    "03q": "working/v25/platform_r12/mi40c/era_refit.csv, working/v25/platform_r12/r4_covid/calib_bootstrap.csv (COVID-19, COVID-NET waves); working/v25/platform_03q/flu_*.csv (influenza)",
    "03u": "working/v25/platform_r12/r4_covid/asym_test.csv (COVID-19, COVID-NET waves); working/v25/platform_03u/flu_asym_test.csv (influenza; 03u_asym.R)",
    "03v": "working/v25/platform_r12/jno_v26/crude_covid.csv (COVID-19, COVID-NET waves); working/v25/platform_03u/flu_crude.csv (influenza; 03v_crude.py)",
    "e8": "working/v25/tables/eTable8_era.csv",
    "t2": "working/v25/tables/Table2_data.csv",
    "fig2": "results/figures/v25/Figure2_era_attenuation_data.csv (from working/v25/platform_r12/r4_covid/C_era_attenuation.csv), log(alone) - log(joint)",
    "derived": "arithmetic on asserted values (see gloss)",
    "e13": "supplement eTable 10 (zcode/aou_v7/10_zcode_capture_vs_survey.csv; employment row 208/3,608)",
    "03w": "working/v25/platform_r12/r4_covid/ (sens_r6.csv, lag_by_era.txt; COVID-NET waves); working/v25/platform_03w/flu_sens_r6.csv (influenza; 03w_sens.R)",
    "e21": "supplement eTable 9 (working/v25/platform_r12/jno_v26/crude_covid.csv; working/v25/platform_03u/flu_crude.csv; 03v_crude.py)",
    "r11": "working/v25/platform_r11/ (zband_covid.csv, zband_flu.csv, flow_top_flu.txt; 03z_zband.py, flu_arm/05_flow_top.py)",
    "bls": "BLS CPI-U, US city average, all items, series CUUR0000SA0 (SOURCES_R11 section 4): annual average 2018 251.107, 2022 292.655; ratio 1.1655",
    "taylor": "Taylor CA, et al. MMWR Morb Mortal Wkly Rep. 2022;71(12):466-473 (COVID-NET variant-predominance periods; full text read 2026-09-28)",
    "r10": "working/v25/platform_r12/ (r4_covid/sens_r10*.csv, jno_v26/describe_r10_covid.csv, jno_v26/ard_*.csv, jno_v26/r10b_covid.txt; COVID-NET waves); wave-free items and influenza: working/v25/platform_r10/",
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
            (
                "1.72 alone to 1.49 jointly",
                "03n",
                "income <$10k, COVID-19 (1.7180; 1.4935)",
            ),
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
        (
            "edu",
            ("(1.30 to 1.02)", "03n", "education below GED, COVID-19 (1.3002; 1.0152)"),
        ),
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
                "1.45 before Delta, 1.54 during Delta, and 1.56 during Omicron",
                "03n",
                "income <$10k by wave",
            ),
        ),
        (
            "covid_ror_inc",
            (
                "(ratio, Omicron to pre-Delta, 1.08; 95% CI, 0.84-1.40; Figure 2A)",
                "03o",
                "income ROR Omicron/pre-Delta",
            ),
        ),
        (
            "int_inc",
            (
                "(P = .74 and P = .91; eTables 15, 19, and 20)",
                "03d",
                "income x era, COVID-19 and influenza",
            ),
        ),
        (
            "med_pre",
            (
                "1.90 alone and 1.37 (95% CI, 1.15-1.63) jointly",
                "03o",
                "Medicaid pre-Delta",
            ),
        ),
        (
            "med_later_alone",
            ("(1.26 and 1.24)", "03o", "Medicaid alone, Delta and Omicron"),
        ),
        (
            "med_later_joint",
            (
                "0.92 [95% CI, 0.70-1.19] and 0.91 [95% CI, 0.75-1.11]",
                "03o",
                "Medicaid joint, Delta and Omicron",
            ),
        ),
        (
            "med_ror",
            (
                "0.66 (95% CI, 0.53-0.84)",
                "03o",
                "Medicaid ROR Omicron/pre-Delta (0.6645)",
            ),
        ),
        (
            "flu_med_ror",
            (
                "(in a period-interaction model, 1.13 before the pandemic and 0.84 after influenza returned; ratio, 0.74; 95% CI, 0.51-1.07; eFigure 7)",
                "03o",
                "Medicaid, period-interaction model, and ROR, influenza",
            ),
        ),
        (
            "race_joint",
            (
                "AOR was 2.08 (95% CI, 1.88-2.30",
                "03n",
                "Black vs White, joint (2.0752)",
            ),
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
                "max |KHB - log| 0.63 COVID (inc25k), 1.5 influenza",
            ),
        ),
        (
            "c_black_att",
            (
                "16% (95% CI, 11% to 21%)",
                "03oAB",
                "Black attenuation, COVID-19 (15.99; 11.29-21.11)",
            ),
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
            "unemp_rent_att",
            (
                "against 43% and 39% for being out of work or unable to work (eTable 21) and 55% and 59% for renting",
                "03oAB",
                "unemployment and renting attenuation",
            ),
        ),
        (
            "edu_att",
            (
                "education below GED lost 94% in COVID-19 (1.30 to 1.02)",
                "03oAB",
                "education attenuation, COVID-19",
            ),
        ),
        (
            "abs_inc_joint",
            (
                "(AOR, 1.49 in COVID-19 and 1.64 in influenza)",
                "03n",
                "abstract, income <$10k joint",
            ),
        ),
        (
            "crude_inc",
            (
                "21.9% of those with income below $10 000 and 11.5% at $35 000 to $99 999",
                "03v",
                "crude hospitalization, COVID-19, below $10 000 and $35 000-99 999 (eTable 9 shows percentages only)",
            ),
        ),
        (
            "crude_waves",
            (
                "10.1, 10.8, and 10.4 percentage points",
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
                "the Medicaid ratio 0.58 (95% CI, 0.43-0.77)",
                "03u",
                "Medicaid ROR, combined model",
            ),
        ),
        (
            "attenuated_med",
            (
                "(0.33, 0.32, and 0.31 on the log scale)",
                "fig2",
                "Medicaid attenuated part (log OR alone - log OR joint) by wave, COVID-19: 0.327, 0.320, 0.309",
            ),
        ),
        (
            "medicare_cv",
            (
                "ratio in the model with both interactions, 0.67; 95% CI, 0.53-0.87",
                "03u",
                "Medicare ROR Omicron/pre-Delta, COVID-19, combined model 0.674 (0.526-0.865)",
            ),
        ),
        (
            "medicare_flu",
            (
                "but not in influenza (1.03; 95% CI, 0.66-1.61; eTable 12)",
                "03u",
                "Medicare ROR after/before, influenza, combined model",
            ),
        ),
        (
            "asym",
            (
                "2.27 (95% CI, 1.38-3.74; joint test across Delta and Omicron, P = .001)",
                "03u",
                "ratio of RORs 2.268 (1.376-3.738); D1 F = 6.80 on 2 df, P = .0011",
            ),
        ),
        (
            "asym_inc",
            (
                "the income ratio was 1.31 (95% CI, 0.97-1.76)",
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
                "Key Points; crude gaps 10.1-12.0 points (eTable 9)",
            ),
        ),
        (
            "abs_gap",
            (
                "10 to 12 percentage points higher with income below $10 000 than with $35 000 to $99 999 in every era of both viruses (COVID-19 overall, 21.9% vs 11.5%)",
                "03v",
                "abstract; era gaps 10.1, 10.8, 10.4 and 12.0, 10.3, 11.0",
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
            "attenuated_inc",
            (
                "as did income's (0.14, 0.15, and 0.13)",
                "fig2",
                "log(1.659/1.445)=0.138, log(1.797/1.541)=0.153, log(1.785/1.562)=0.134",
            ),
        ),
        (
            "miss_inc",
            (
                "hospitalized nearly as often as the lowest band (21.4% vs 21.9% in COVID-19)",
                "03v",
                "1,086/5,064",
            ),
        ),
        (
            "med_gap",
            (
                "from 15.1 to 10.1 and 9.5 points (eTable 9)",
                "03v",
                "Medicaid-employer crude RD by wave",
            ),
        ),
        (
            "z59",
            (
                "14.3% of those reporting income below $10 000 a Z59 code",
                "r11",
                "zband_covid.csv below_10k z59 272/1,896",
            ),
        ),
        (
            "z59_mid",
            (
                "against 1.8% at $35 000 to $99 999 (Figure 2C)",
                "r11",
                "zband_covid.csv 35k_to_99k z59 64/3,548",
            ),
        ),
        (
            "sens_med_range",
            (
                "Medicaid ratio of odds ratios ranged from 0.58 to 0.73, with every insurance-by-era test at P < .02",
                "03w",
                "lag 0.581 ... site 0.734; D1 max .0134 (harmB; region .0117)",
            ),
        ),
        (
            "sens_inc_range",
            (
                "the income ratio ranged from 0.99 to 1.46, the upper value after adjustment for EHR site (era test, P = .48)",
                "03w",
                "tip1 0.986; site_pre 1.464 (1.07-2.00), D1 .477 (03w SPART=ALL already uses site_pre)",
            ),
        ),
        (
            "exp_yes",
            (
                "Medicaid fell in both expansion and nonexpansion states, imprecisely in the latter",
                "03w",
                "expansion_Yes 0.60 (0.45-0.79); expansion_No 0.21 (0.08-0.53)",
            ),
        ),
        (
            "z59_disc",
            (
                "fewer than 1 in 6 participants reporting income below $10 000 carried a Z59 code",
                "r11",
                "14.3% < 16.7%",
            ),
        ),
        (
            "housing_stab",
            (
                "(COVID-19 AOR, 1.00) and fell slightly below 1 jointly (0.88; 95% CI, 0.79-0.97; influenza joint AOR, 0.97; 95% CI, 0.83-1.13)",
                "03n",
                "unstable housing alone 1.0024 (0.9083-1.1063), joint 0.8773 (0.7905-0.9736) (R12); influenza joint 0.97 (0.83-1.13), 03f",
            ),
        ),
        (
            "r10_severe",
            (
                "and 1.15 (95% CI, 0.77-1.71) among those with one",
                "r10",
                "case_severe Medicaid 1.1475 (0.7694-1.7114)",
            ),
        ),
        (
            "r10_link",
            (
                "linked to the admission for 54.6% of employer-insured and 84.8% of Medicaid-insured Omicron cases",
                "r10",
                "describe_r10_covid linked condition row 167/306, 312/368",
            ),
        ),
        (
            "r10_ard_med",
            (
                "the Medicaid difference fell from 5.9 to 0.6",
                "r10",
                "ard_covid_x.csv Medicaid 5.9221, 0.5685",
            ),
        ),
        (
            "r11_z59_income",
            (
                "1.7% had a code specific to income",
                "r11",
                "zband_covid.csv below_10k income 32/1,896",
            ),
        ),
        (
            "r11_z59_disc",
            ("about 1 in 60 a code specific to income", "r11", "32/1,896 = 1 in 59"),
        ),
        (
            "cpi",
            (
                "consumer prices rose 16.5% from 2018 to 2022",
                "bls",
                "292.655/251.107 = 1.1655",
            ),
        ),
        (
            "r10_lab",
            (
                "among laboratory-confirmed cases (ratio, 0.66; 95% CI, 0.49-0.89)",
                "r10",
                "sens_r10c.csv case_lab Medicaid 0.6623 (0.4932-0.8892)",
            ),
        ),
        (
            "r10_ip_ed24",
            (
                "cases with an inpatient stay (0.65) or with an inpatient stay or an emergency stay of 24 hours or more (0.66)",
                "r10",
                "case_ip 0.6491; case_ed24b 0.6597",
            ),
        ),
        (
            "r10_abs_lab",
            (
                "laboratory-confirmed cases, 0.66; 95% CI, 0.49-0.89",
                "r10",
                "case_lab Medicaid 0.6623 (0.4932-0.8892); abstract",
            ),
        ),
        (
            "r10_ard_inc",
            (
                "(adjusted income difference, 0.9 to 3.5 percentage points)",
                "r10",
                "ard_covid_x.csv income 0.9443, 3.4648",
            ),
        ),
        (
            "r10_linked_mix",
            (
                "appeared in 63.5% of employer-insured Omicron admissions, down from 84.3% before Delta (Medicaid, 86.5% and 90.4%)",
                "r10",
                "describe_r10_covid: dx on visit / linked = 106/167, 215/255; Medicaid 270/312, 665/736",
            ),
        ),
        (
            "r10_scr_ehr",
            (
                "(2.1% and 9.8% of participants)",
                "r10",
                "r10b_*.txt EHR-site screening 290/13,781; 527/5,364",
            ),
        ),
        (
            "r10_dx_range",
            (
                "the ratio ranged from 0.73 to 1.02",
                "r10",
                "eTable 23A: case_infwin2 0.7326 ... case_dx2 1.0208 (superseded case_dx 1.0235)",
            ),
        ),
        (
            "r10_short",
            (
                "the ratio was 0.61 (95% CI, 0.45-0.82) among cases without a stay of 3 days or more, intensive care, or death",
                "r10",
                "sens_r10d.csv case_short Medicaid 0.6086 (0.4495-0.8239)",
            ),
        ),
        (
            "wave_dates",
            (
                "pre-Delta, before July 1, 2021; Delta, to December 18, 2021; Omicron, thereafter",
                "taylor",
                "COVID-19 wave boundaries recoded in 01_aou_etl.py and every downstream script (R12)",
            ),
        ),
        (
            "std_range",
            (
                "directly age-sex-standardized differences ranged from 9.2 to 14.6 points",
                "e21",
                "rd_std, income <$10k vs $35-99k: COVID-19 11.49, 14.58, 11.43; influenza 14.4, 9.2, 13.7",
            ),
        ),
        (
            "cite_mullachery",
            (
                "which requires staggered state adoption and even then varies by cohort",
                "cited",
                "Mullachery et al 2026 Drug Alcohol Depend (PMC13449180, full text read 2026-09-27): cohort-specific staggered DiD; 2016 cohort OR 1.49, 2019 cohort 0.71, pooled ATT null",
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
    """eTables 15A-B and the figures render the same era-specific estimates. They
    must agree. Figure 2A plots every eTable 15A cell (alone and jointly); Figure
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
                "  DISAGREE Figure 2B/eFigure 7 %-9s %-12s %-6s era %s: eTable15A=%s figure=%s"
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
                        "  DISAGREE eFigure 6 %-9s %-12s %s: eTable15A=%s figure=%s"
                        % (pth, term, r["era"], want, got)
                    )
                    bad += 1
    # eTable 15B against the Figure 2A forest (v26)
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
        "\neTable 15A/15B against Figure 2 and eFigure 6 data: %d discrepancies." % bad
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
