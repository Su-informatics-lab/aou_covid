# -*- coding: utf-8 -*-
"""Assert every number the v23 manuscript prints against the artifact it came
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

The frozen values below are transcribed from the run results in working/v23/.
Each carries the file it came from, so a reader can follow any single number
back to the script that produced it without opening the platform.
"""

import re
import sys
from collections import OrderedDict

SRC = {
    "03h": "working/v23/03h_03i_RESULTS.md",
    "03d": "working/v23/03d_03e_RESULTS.md",
    "03e": "working/v23/03d_03e_RESULTS.md",
    "03f": "working/v23/03f_flu_mi40_RESULTS.md",
    "03i": "working/v23/03h_03i_RESULTS.md",
    "03j": "working/v23/03j_race_RESULTS.md",
    "03k": "working/v23/03k_03l_RESULTS.md",
    "t1": "working/v23/flu_table1_RESULTS.md",
    "ms19": "the previous version, carried unchanged",
    "xco": "results/ms/base_model_coefficients.csv against tables/eTable6_base_model.csv, recomputed",
}

# claim key -> (literal string that must appear, source key, one-line gloss)
CLAIMS = OrderedDict(
    [
        (
            "cohort_covid_screened",
            (
                "25,160",
                "ms19",
                "COVID-19 test-positive adults with record and survey data",
            ),
        ),
        (
            "cohort_covid_hosp",
            ("4,064 (16.2%)", "ms19", "met the hospitalization phenotype"),
        ),
        ("cohort_covid_cases", ("3,997", "ms19", "matched cases")),
        ("cohort_covid_ctrl", ("15,523", "ms19", "control observations")),
        (
            "cohort_covid_ctrl_people",
            ("9,784", "ms19", "individuals contributing control observations"),
        ),
        ("cohort_covid_ratio", ("3.88 per case", "ms19", "controls per case")),
        ("cohort_flu_cases", ("1,672", "t1", "matched case person-seasons")),
        (
            "cohort_flu_people",
            ("1,648", "t1", "participants contributing case person-seasons"),
        ),
        ("cohort_flu_ctrl", ("6,616", "t1", "control observations")),
        (
            "cohort_flu_ctrl_people",
            ("3,764", "t1", "participants contributing control observations"),
        ),
        ("cohort_flu_ratio", ("3.96 per case", "t1", "controls per case")),
        ("smd_covid_pre", ("0.410", "ms19", "largest pre-matching SMD, COVID-19")),
        ("smd_flu_pre", ("0.489", "ms19", "largest pre-matching SMD, influenza")),
        ("xcohort_cases", ("127,696", "ms19", "MarketScan matched cases")),
        ("xcohort_ctrl", ("509,983", "ms19", "MarketScan control observations")),
        (
            "xcohort_agree",
            (
                "20 of the 26",
                "xco",
                "base-model terms agreeing in direction across cohorts",
            ),
        ),
        (
            "xcohort_unresolved",
            (
                "of the 6 that did not, 3",
                "xco",
                "discordant terms whose All of Us interval includes 1",
            ),
        ),
        (
            "xcohort_risk",
            ("16.2% vs 3.2%", "ms19", "hospitalized, All of Us against MarketScan"),
        ),
        ("base_female", ("0.76; 95% CI, 0.70-0.82", "03d", "female sex, joint model")),
        ("base_vacc", ("0.44; 95% CI, 0.39-0.50", "03d", "recorded vaccination")),
        ("base_delta", ("1.21; 95% CI, 1.09-1.35", "03d", "Delta wave vs pre-Delta")),
        (
            "base_charlson_sig",
            (
                "10 of the 19 Charlson conditions",
                "03d",
                "significant comorbidity terms",
            ),
        ),
        (
            "ds_medicaid",
            ("1.54 (95% CI, 1.38-1.71)", "03h", "Medicaid, domain-specific"),
        ),
        (
            "ds_unemp",
            ("1.55 (95% CI, 1.40-1.71)", "03h", "unemployment, domain-specific"),
        ),
        (
            "ds_inc10k",
            ("1.72 (95% CI, 1.52-1.95)", "03h", "income <$10k, domain-specific"),
        ),
        (
            "ds_edu",
            ("1.30 (95% CI, 1.14-1.48)", "03h", "education below GED, domain-specific"),
        ),
        ("ds_rent", ("1.29 (95% CI, 1.18-1.41)", "03h", "renting, domain-specific")),
        ("j_medicaid", ("1.11 (95% CI, 0.97-1.27)", "03d", "Medicaid, joint")),
        ("j_edu", ("1.01 (95% CI, 0.87-1.17)", "03d", "education below GED, joint")),
        ("j_inc10k", ("1.50 (95% CI, 1.27-1.77)", "03d", "income <$10k, joint")),
        ("j_unemp", ("1.28 (95% CI, 1.13-1.45)", "03d", "unemployment, joint")),
        ("j_rent", ("1.12 (95% CI, 1.02-1.24)", "03d", "renting, joint")),
        (
            "j_instab",
            ("0.88; 95% CI, 0.79-0.97", "03d", "housing instability, joint, COVID-19"),
        ),
        (
            "j_instab_flu",
            ("0.97; 95% CI, 0.83-1.13", "03i", "housing instability, joint, influenza"),
        ),
        (
            "f_medicaid_ds",
            ("1.60 (95% CI, 1.35-1.89)", "03i", "Medicaid, domain-specific, influenza"),
        ),
        (
            "f_medicaid_j",
            ("0.93 (95% CI, 0.75-1.15)", "03i", "Medicaid, joint, influenza"),
        ),
        (
            "f_inc10k",
            ("1.64 (95% CI, 1.29-2.07)", "03i", "income <$10k, joint, influenza"),
        ),
        (
            "f_inc25k",
            ("1.92 (95% CI, 1.55-2.39)", "03i", "income $10-25k, joint, influenza"),
        ),
        (
            "f_unemp",
            ("1.41 (95% CI, 1.18-1.69)", "03i", "unemployment, joint, influenza"),
        ),
        ("f_rent", ("1.19 (95% CI, 1.01-1.39)", "03i", "renting, joint, influenza")),
        (
            "trend_covid_log10",
            ("0.78 per log10 step", "03d", "income trend, log10 midpoint, COVID-19"),
        ),
        ("trend_covid_log10_ci", ("95% CI, 0.69-0.89", "03d", "its interval")),
        (
            "trend_covid_rank",
            ("0.94 per rank step", "03d", "income trend, rank, COVID-19"),
        ),
        (
            "trend_flu",
            ("0.69 (95% CI, 0.57-0.83)", "03f", "income trend, log10, influenza"),
        ),
        (
            "block_hi_covid",
            ("F = 1.72; 3 df; P = .16", "03d", "high-income block D1, COVID-19"),
        ),
        (
            "block_hi_flu",
            ("F = 0.24; 3 df; P = .87", "03f", "high-income block D1, influenza"),
        ),
        ("int_inc_covid", ("F = 0.90; 12 df; P = .54", "03e", "income x wave")),
        ("int_ins_covid", ("F = 3.33; 8 df; P < .001", "03e", "insurance x wave")),
        ("int_inc_flu", ("F = 0.50; 12 df; P = .91", "03f", "income x period")),
        ("int_ins_flu", ("F = 2.47; 8 df; P = .01", "03f", "insurance x period")),
        (
            "wave_inc_pre",
            ("1.45 (95% CI, 1.20-1.75)", "03e", "income <$10k, pre-Delta"),
        ),
        ("wave_inc_delta", ("1.57 (95% CI, 1.16-2.13)", "03e", "income <$10k, Delta")),
        (
            "wave_inc_omicron",
            ("1.56 (95% CI, 1.24-1.95)", "03e", "income <$10k, Omicron"),
        ),
        ("wave_med_pre", ("1.39 (95% CI, 1.17-1.64)", "03e", "Medicaid, pre-Delta")),
        ("wave_med_delta", ("0.89 (95% CI, 0.69-1.15)", "03e", "Medicaid, Delta")),
        ("wave_med_omicron", ("0.91 (95% CI, 0.76-1.10)", "03e", "Medicaid, Omicron")),
        (
            "per_med_post",
            ("0.76 (95% CI, 0.58-1.00)", "03i", "Medicaid, post-pandemic, influenza"),
        ),
        (
            "per_n_pandemic",
            ("817", "03i", "matched rows in the influenza pandemic period"),
        ),
        ("race_joint", ("2.07; 95% CI, 1.87-2.29", "03j", "Black race, joint model")),
        (
            "race_pct_all",
            ("16.2%", "03j", "share of the base-model log OR removed by the domains"),
        ),
        ("race_pct_income", ("93.8%", "03j", "income's share of that reduction")),
        (
            "sens_indicator_medicaid",
            ("AOR, 1.19", "ms19", "Medicaid under the missing-indicator specification"),
        ),
        (
            "sens_congeniality",
            ("0.022 on the log scale", "03d", "largest congenial-vs-legacy difference"),
        ),
        ("miss_income_case", ("26.5%", "ms19", "income missing among cases")),
        ("miss_income_ctrl", ("19.0%", "ms19", "income missing among controls")),
        (
            "survey_lag",
            ("692 days (IQR, 286-985 days)", "ms19", "survey to index lag, COVID-19"),
        ),
        (
            "survey_preindex",
            ("86.4%", "ms19", "surveys completed before infection, COVID-19"),
        ),
        ("zcode_unemployed", ("3,608", "ms19", "participants reporting unemployment")),
        ("zcode_z56", ("208 (5.8%)", "ms19", "of them carrying a Z56 code")),
        (
            "ontario",
            (
                "56.9%",
                "ms19",
                "vaccination share of income inequality in Ontario deaths",
            ),
        ),
        (
            "ontario_n",
            (
                "11.2-million-person",
                "ms19",
                "size of the Ontario cohort, from the cited paper",
            ),
        ),
        (
            "mude_black",
            (
                "1.9 for Black populations",
                "ms19",
                "pooled standardized hospitalization ratio, cited",
            ),
        ),
        (
            "mude_white",
            (
                "0.74 for White populations",
                "ms19",
                "the same, White populations, cited",
            ),
        ),
        (
            "smd_post",
            ("below 0.03 after matching", "t1", "post-matching SMD, both arms"),
        ),
        (
            "t1_covid_female",
            ("2,409 [60.3%] female", "ms19", "Table 1, COVID-19 cases"),
        ),
        ("t1_covid_age", ("57.5 [16.2] years", "ms19", "Table 1, COVID-19 case age")),
        ("t1_flu_female", ("1,090 [65.2%] female", "t1", "Table 1, influenza cases")),
        ("t1_flu_age", ("56.3 [16.3] years", "t1", "Table 1, influenza case age")),
        (
            "flu_preindex",
            (
                "100% in the influenza arm",
                "t1",
                "surveys completed before index, influenza",
            ),
        ),
        (
            "per_med_pre_flu",
            ("1.46 (95% CI, 0.97-2.19)", "03i", "Medicaid, pre-pandemic, influenza"),
        ),
        (
            "per_med_pan_flu",
            ("1.82 (95% CI, 0.80-4.14)", "03i", "Medicaid, pandemic, influenza"),
        ),
        (
            "per_inc_flu_all",
            (
                "1.72, 1.12, and 1.64",
                "03i",
                "income <$10k across the three influenza periods",
            ),
        ),
        (
            "trend_flu_rank",
            ("0.87 (95% CI, 0.82-0.92)", "03f", "income trend, rank, influenza"),
        ),
        ("block_lo", ("both P < .001", "03d", "low-income block D1, both arms")),
        ("aou_total", ("413,457", "ms19", "All of Us participants screened")),
        (
            "wave_within_strata",
            (
                "96.1% of COVID-19 strata",
                "03e",
                "COVID-19 strata in which pandemic wave varies",
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
        print("# Claim ledger — v23\n")
        print("Every number below is asserted by `analysis/validate_v23.py`. The")
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
                os.path.join(root, "results/figures/v23/Figure1_data.csv"),
                encoding="utf-8",
            )
        )
    }
    t2 = list(
        csv.DictReader(
            open(
                os.path.join(root, "working/v23/tables/Table2_data.csv"),
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
        for cand in ("../ms/manuscript_v23.md", "../working/v23/manuscript_v23.md"):
            ms = os.path.join(here, cand)
            if os.path.exists(ms):
                break
    sys.exit(run(ms, mode))
