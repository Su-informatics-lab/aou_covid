# Claim ledger — v25

Every number below is asserted by `analysis/validate_v25.py`. The
source column names the run result the value was transcribed from.

| claim | value as printed | source | what it is |
|---|---|---|---|
| `cohort_covid_cases` | 3,997 COVID-19 cases | the previous version, carried unchanged | matched cases |
| `cohort_covid_ctrl` | 15,523 control observations | the previous version, carried unchanged | control observations |
| `cohort_flu` | 1,672 influenza case person-seasons and 6,616 control observations | working/v23/flu_table1_RESULTS.md | influenza arm |
| `cohort_screened` | 25,160 | the previous version, carried unchanged | COVID-19 adults with record and survey data |
| `cohort_hosp` | 4,064 (16.2%) | the previous version, carried unchanged | met the hospitalization phenotype |
| `cohort_ctrl_people` | 9,784 individuals | the previous version, carried unchanged | individuals contributing control observations |
| `cohort_flu_people` | 1,648 participants | working/v23/flu_table1_RESULTS.md | participants contributing influenza cases |
| `cohort_flu_ctrl_people` | 3,764 participants | working/v23/flu_table1_RESULTS.md | participants contributing influenza controls |
| `abs_female` | 60.3% female (mean [SD] age, 57.5 [16.2] years) | working/v23/flu_table1_RESULTS.md | COVID-19 case sex and age |
| `abs_flu_female` | 65.2% female (56.3 [16.3] years) | working/v23/flu_table1_RESULTS.md | influenza case sex and age |
| `survey_lag` | 692 days (IQR, 286-985 days) | the previous version, carried unchanged | survey-to-index lag |
| `wave_split` | 96.1% | the previous version, carried unchanged | strata in which wave varies |
| `version_n` | 2,153 of 13,781 matched persons | working/v25/platform_03p/ (P_refit.csv, README.md) | persons captured only by the original insurance item |
| `inc_alone_joint` | 1.72 alone to 1.50 jointly | working/v24/03n_RESULTS.md | income <$10k, COVID-19 |
| `inc_flu` | 22% (95% CI, 0% to 48%) in influenza (1.88 to 1.64) | working/v25/03o_RESULTS.md | income <$10k attenuation, influenza |
| `med_alone_joint` | (1.54 to 1.11) | working/v24/03n_RESULTS.md | Medicaid, COVID-19 |
| `med_flu` | (1.60 to 0.93) | working/v23/03h_03i_RESULTS.md | Medicaid, influenza |
| `edu` | (1.30 to 1.01) | working/v24/03n_RESULTS.md | education below GED, COVID-19 |
| `flu_period` | 1.72 in the 2 seasons before SARS-CoV-2 and 1.64 in the 2 seasons after | working/v23/03f_flu_mi40_RESULTS.md | income <$10k within-period refits, influenza |
| `flu_int_model` | (in a period-interaction model, 1.67 and 1.66; ratio of odds ratios, 0.99; 95% CI, 0.66-1.49) | working/v25/03o_RESULTS.md | income <$10k, period-interaction model, and its ROR, influenza |
| `flu_ror_inc` | 0.99; 95% CI, 0.66-1.49 | working/v25/03o_RESULTS.md | income ROR after/before, influenza |
| `covid_waves_inc` | 1.44 before Delta, 1.57 during Delta, and 1.55 during Omicron | working/v24/03n_RESULTS.md | income <$10k by wave |
| `covid_ror_inc` | (ratio, Omicron to pre-Delta, 1.07; 95% CI, 0.83-1.38; Figure 2A) | working/v25/03o_RESULTS.md | income ROR Omicron/pre-Delta |
| `int_inc` | (P = .59 and P = .91; eTables 7 and 20) | working/v23/03d_03e_RESULTS.md | income x era, COVID-19 and influenza |
| `med_pre` | 1.92 alone and 1.38 (95% CI, 1.16-1.65) jointly | working/v25/03o_RESULTS.md | Medicaid pre-Delta |
| `med_later_alone` | (1.23 and 1.25) | working/v25/03o_RESULTS.md | Medicaid alone, Delta and Omicron |
| `med_later_joint` | 0.89 [95% CI, 0.68-1.17] and 0.91 [95% CI, 0.75-1.11] | working/v25/03o_RESULTS.md | Medicaid joint, Delta and Omicron |
| `med_ror` | 0.66 (95% CI, 0.52-0.83) | working/v25/03o_RESULTS.md | Medicaid ROR Omicron/pre-Delta |
| `flu_med` | jointly 1.46 (95% CI, 0.97-2.19) before the pandemic and 0.76 (95% CI, 0.58-1.00) | working/v25/03o_RESULTS.md | Medicaid joint by period, influenza |
| `flu_med_ror` | (in a period-interaction model, 1.13 and 0.84; ratio, 0.74; 95% CI, 0.51-1.07; eFigure 8) | working/v25/03o_RESULTS.md | Medicaid, period-interaction model, and ROR, influenza |
| `race_joint` | 2.07; 95% CI, 1.87-2.30 | working/v24/03n_RESULTS.md | Black vs White, joint |
| `race_flu` | 34% (95% CI, 23% to 46%) in influenza | working/v25/03o_RESULTS.md | Black attenuation, influenza |
| `r1` | insurance did when analyses were restricted to surveys completed before infection (P = .48 and P = .01) | working/v24/03n_RESULTS.md | pre-index surveys: income x wave P = .48, insurance P = .01 |
| `r3` | P = .26 and P = .009 | working/v24/03n_RESULTS.md | laboratory-confirmed |
| `mi_ind` | (AOR, 1.19; eTable 9) | the previous version, carried unchanged | Medicaid, missing-indicator |
| `c_inc_att` | 26% (95% CI, 9% to 44%) | working/v25/03o_RESULTS.md, COVID-19 A/B (r4_covid/AB_attenuation.csv) | income <$10k attenuation, COVID-19 |
| `c_med_att` | 75% (95% CI, 52% to 112%) | working/v25/03o_RESULTS.md, COVID-19 A/B (r4_covid/AB_attenuation.csv) | Medicaid attenuation, COVID-19 |
| `c_khb` | more than 2 percentage points, and trend models | working/v25/03o_RESULTS.md, COVID-19 A/B (r4_covid/AB_attenuation.csv) | max |KHB - log| 0.64 COVID, 1.5 influenza |
| `c_black_att` | 16% (95% CI, 12% to 21%) | working/v25/03o_RESULTS.md, COVID-19 A/B (r4_covid/AB_attenuation.csv) | Black attenuation, COVID-19 |
| `abs_black` | accounted for 16% of the Black–White log odds ratio in COVID-19 and 34% in influenza | working/v25/03o_RESULTS.md, COVID-19 A/B (r4_covid/AB_attenuation.csv) | abstract |
| `abs_flu_med` | influenza, imprecisely (ratio, 0.74; 95% CI, 0.51-1.07) | working/v25/03o_RESULTS.md | abstract |
| `flu_pan_inc` | (1.12; 95% CI, 0.45-2.74) | working/v23/03f_flu_mi40_RESULTS.md | income <$10k, pandemic influenza, within-period refit |
| `unemp_rent_att` | against 43% and 39% for being out of work or unable to work and 55% and 59% for renting | working/v25/03o_RESULTS.md, COVID-19 A/B (r4_covid/AB_attenuation.csv) | unemployment and renting attenuation |
| `edu_att` | education below GED lost 95% in COVID-19 (1.30 to 1.01) | working/v25/03o_RESULTS.md, COVID-19 A/B (r4_covid/AB_attenuation.csv) | education attenuation, COVID-19 |
| `abs_inc_joint` | (AOR, 1.50 in COVID-19 and 1.64 in influenza) | working/v24/03n_RESULTS.md | abstract, income <$10k joint |
| `q_both` | (income P = .43; insurance P = .002) | working/v25/platform_03q/ (covid_era_refit.csv, flu_era_refit.csv, *_calib_bootstrap.csv) | era tests under case-by-era imputation |
| `crude_inc` | 21.9% of those with income below $10 000 and 11.5% of those with $35 000 to $99 999 | working/v25/platform_03u/ (covid_crude.csv, flu_crude.csv; 03v_crude.py) | crude hospitalization, COVID-19, 675/3,082 and 793/6,925 |
| `crude_waves` | 10.2, 10.3, and 10.6 percentage points | working/v25/platform_03u/ (covid_crude.csv, flu_crude.csv; 03v_crude.py) | crude risk difference by wave, COVID-19 |
| `zcode` | 5.8% of those reporting being out of work or unable to work had a Z56 code | supplement eTable 13 (zcode/aou_v7/10_zcode_capture_vs_survey.csv: 414/3817 = 10.85%, 10.8%) | 208 of 3,608 |
| `asym_med` | the Medicaid ratio 0.57 (95% CI, 0.43-0.76) | working/v25/platform_03u/ (covid_asym_test.csv, flu_asym_test.csv; 03u_asym.R) | Medicaid ROR, combined model |
| `nearpoor` | 1.38 in COVID-19 and 1.92 in influenza (Table 2) | working/v25/tables/Table2_data.csv | income $10-25k, joint |
| `shared` | (0.33, 0.32, and 0.31 on the log scale) | results/figures/v25/Figure2_era_attenuation_data.csv, log(alone) - log(joint): 0.329, 0.317, 0.313 | Medicaid shared part by wave, COVID-19 |
| `medicare_waves` | 1.17 before Delta, 0.79 during Omicron | working/v25/tables/eTable8_era.csv | Medicare joint, pre-Delta and Omicron, COVID-19 |
| `medicare_cv` | ratio, 0.65; 95% CI, 0.51-0.84 | working/v25/platform_03u/ (covid_asym_test.csv, flu_asym_test.csv; 03u_asym.R) | Medicare ROR Omicron/pre-Delta, COVID-19, combined model 0.653 (0.509-0.837) |
| `medicare_flu` | (ratio in that model, 1.03; 95% CI, 0.66-1.61; eTable 22) | working/v25/platform_03u/ (covid_asym_test.csv, flu_asym_test.csv; 03u_asym.R) | Medicare ROR after/before, influenza, combined model |
| `asym` | 2.27 (95% CI, 1.38-3.74; joint test across Delta and Omicron, P < .001) | working/v25/platform_03u/ (covid_asym_test.csv, flu_asym_test.csv; 03u_asym.R) | ratio of RORs; D1 F = 7.78 on 2 df, P = .0004 |
| `asym_inc` | the income ratio was 1.30 (95% CI, 0.97-1.74) | working/v25/platform_03u/ (covid_asym_test.csv, flu_asym_test.csv; 03u_asym.R) | income ROR, combined model |
| `asym_flu` | 1.85 (95% CI, 0.81-4.20 | working/v25/platform_03u/ (covid_asym_test.csv, flu_asym_test.csv; 03u_asym.R) | ratio of RORs, influenza |
| `kp_gap` | hospitalized about 10 percentage points more often than those with $35 000 to $99 999 in every era | working/v25/platform_03u/ (covid_crude.csv, flu_crude.csv; 03v_crude.py) | Key Points; crude gaps 10.2-12.0 points (eTable 21) |
| `abs_gap` | 10 to 12 percentage points higher with income below $10 000 than with $35 000 to $99 999 in every era of both viruses (COVID-19 overall, 21.9% vs 11.5%) | working/v25/platform_03u/ (covid_crude.csv, flu_crude.csv; 03v_crude.py) | abstract; era gaps 10.2, 10.3, 10.6 and 12.0, 10.3, 11.0 |
| `crude_flu_eras` | 12.0, 10.3, and 11.0 in the 3 influenza periods | working/v25/platform_03u/ (covid_crude.csv, flu_crude.csv; 03v_crude.py) | crude gaps, influenza, by period |
| `crude_mid_range` | ranged from 7.2% to 16.2% and the ratio of the 2 proportions from 1.68 to 2.44 | working/v25/platform_03u/ (covid_crude.csv, flu_crude.csv; 03v_crude.py) | middle-band proportion range and ratio range across 6 eras |
| `inc_shared` | as did income's (0.14 in each wave) | results/figures/v25/Figure2_era_attenuation_data.csv, log(alone) - log(joint): 0.329, 0.317, 0.313 | log(1.661/1.445)=0.139, log(1.808/1.568)=0.142, log(1.779/1.551)=0.137 |
| `disc_ratio` | in COVID-19, about 1 in 5 against 1 in 9 | arithmetic on asserted values (see gloss) | 20.8%-22.6% and 10.2%-12.4% by wave (03v) |
| `flat35b` | In COVID-19 the income gradient was flat above $35 000 (11.3% at $100 000 or more); in influenza it continued modestly (13.6% and 11.3%; Figure 1A) | working/v25/platform_03u/ (covid_crude.csv, flu_crude.csv; 03v_crude.py) | COVID 542/4,786; influenza 317/2,335 and 179/1,580 |
| `miss_inc` | hospitalized as often as the lowest band (21.4% in COVID-19) | working/v25/platform_03u/ (covid_crude.csv, flu_crude.csv; 03v_crude.py) | 1,086/5,064 |
| `med_gap` | from 15.3 to 9.4 and 9.7 points (eTable 21) | working/v25/platform_03u/ (covid_crude.csv, flu_crude.csv; 03v_crude.py) | Medicaid-employer crude RD by wave |
| `z59` | 10.8% of those reporting income below $25 000 a Z59 code | supplement eTable 13 (zcode/aou_v7/10_zcode_capture_vs_survey.csv: 414/3817 = 10.85%, 10.8%) | 414/3,817 |
| `sens_med_range` | Medicaid ratio of odds ratios ranged from 0.57 to 0.73, with every insurance-by-era test at P ≤ .007 | working/v25/platform_03w/ (covid_sens_r6.csv, flu_sens_r6.csv, lag_by_era.txt; 03w_sens.R) | lag 0.57 ... site 0.73; D1 max .007 (region, harmB) |
| `sens_inc_range` | the income ratio ranged from 0.98 to 1.45, the upper value after adjustment for EHR site (era test, P = .50) | working/v25/platform_03w/ (covid_sens_r6.csv, flu_sens_r6.csv, lag_by_era.txt; 03w_sens.R) | tip1 0.98; site_pre 1.447 (1.065-1.965), D1 .499 (03w SPART=SITEPRE, merged by 03w_merge_sitepre.py) |
| `exp_no` | among the 595 cases from nonexpansion states (0.20; 95% CI, 0.08-0.51; era test, P = .08) | working/v25/platform_03w/ (covid_sens_r6.csv, flu_sens_r6.csv, lag_by_era.txt; 03w_sens.R) | expansion_No |
| `exp_yes` | Medicaid fell among residents of expansion states (0.60; 95% CI, 0.45-0.79) | working/v25/platform_03w/ (covid_sens_r6.csv, flu_sens_r6.csv, lag_by_era.txt; 03w_sens.R) | expansion_Yes |
| `emp_rise` | employer-insured was 9.4% before Delta, 11.7% during Delta, and 9.8% during Omicron | working/v25/platform_03u/ (covid_crude.csv, flu_crude.csv; 03v_crude.py) | employer crude by wave, platform_03u/covid_crude.csv |
| `z59_disc` | fewer than 1 in 9 participants reporting low income carried a Z59 code | supplement eTable 13 (zcode/aou_v7/10_zcode_capture_vs_survey.csv: 414/3817 = 10.85%, 10.8%) | 10.8% < 11.1% |
