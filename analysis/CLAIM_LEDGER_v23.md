# Claim ledger — v23

Every number below is asserted by `analysis/validate_v23.py`. The
source column names the run result the value was transcribed from.

| claim | value as printed | source | what it is |
|---|---|---|---|
| `cohort_covid_screened` | 25,160 | the previous version, carried unchanged | COVID-19 test-positive adults with record and survey data |
| `cohort_covid_hosp` | 4,064 (16.2%) | the previous version, carried unchanged | met the hospitalization phenotype |
| `cohort_covid_cases` | 3,997 | the previous version, carried unchanged | matched cases |
| `cohort_covid_ctrl` | 15,523 | the previous version, carried unchanged | control observations |
| `cohort_covid_ctrl_people` | 9,784 | the previous version, carried unchanged | individuals contributing control observations |
| `cohort_covid_ratio` | 3.88 per case | the previous version, carried unchanged | controls per case |
| `cohort_flu_cases` | 1,672 | working/v23/flu_table1_RESULTS.md | matched case person-seasons |
| `cohort_flu_people` | 1,648 | working/v23/flu_table1_RESULTS.md | participants contributing case person-seasons |
| `cohort_flu_ctrl` | 6,616 | working/v23/flu_table1_RESULTS.md | control observations |
| `cohort_flu_ctrl_people` | 3,764 | working/v23/flu_table1_RESULTS.md | participants contributing control observations |
| `cohort_flu_ratio` | 3.96 per case | working/v23/flu_table1_RESULTS.md | controls per case |
| `smd_covid_pre` | 0.410 | the previous version, carried unchanged | largest pre-matching SMD, COVID-19 |
| `smd_flu_pre` | 0.489 | the previous version, carried unchanged | largest pre-matching SMD, influenza |
| `xcohort_cases` | 127,696 | the previous version, carried unchanged | MarketScan matched cases |
| `xcohort_ctrl` | 509,983 | the previous version, carried unchanged | MarketScan control observations |
| `xcohort_agree` | 20 of the 26 | results/ms/base_model_coefficients.csv against tables/eTable6_base_model.csv, recomputed | base-model terms agreeing in direction across cohorts |
| `xcohort_unresolved` | of the 6 that did not, 3 | results/ms/base_model_coefficients.csv against tables/eTable6_base_model.csv, recomputed | discordant terms whose All of Us interval includes 1 |
| `xcohort_risk` | 16.2% vs 3.2% | the previous version, carried unchanged | hospitalized, All of Us against MarketScan |
| `base_female` | 0.76; 95% CI, 0.70-0.82 | working/v23/03d_03e_RESULTS.md | female sex, joint model |
| `base_vacc` | 0.44; 95% CI, 0.39-0.50 | working/v23/03d_03e_RESULTS.md | recorded vaccination |
| `base_delta` | 1.21; 95% CI, 1.09-1.35 | working/v23/03d_03e_RESULTS.md | Delta wave vs pre-Delta |
| `base_charlson_sig` | 10 of the 19 Charlson conditions | working/v23/03d_03e_RESULTS.md | significant comorbidity terms |
| `ds_medicaid` | 1.54 (95% CI, 1.38-1.71) | working/v23/03h_03i_RESULTS.md | Medicaid, domain-specific |
| `ds_unemp` | 1.55 (95% CI, 1.40-1.71) | working/v23/03h_03i_RESULTS.md | unemployment, domain-specific |
| `ds_inc10k` | 1.72 (95% CI, 1.52-1.95) | working/v23/03h_03i_RESULTS.md | income <$10k, domain-specific |
| `ds_edu` | 1.30 (95% CI, 1.14-1.48) | working/v23/03h_03i_RESULTS.md | education below GED, domain-specific |
| `ds_rent` | 1.29 (95% CI, 1.18-1.41) | working/v23/03h_03i_RESULTS.md | renting, domain-specific |
| `j_medicaid` | 1.11 (95% CI, 0.97-1.27) | working/v23/03d_03e_RESULTS.md | Medicaid, joint |
| `j_edu` | 1.01 (95% CI, 0.87-1.17) | working/v23/03d_03e_RESULTS.md | education below GED, joint |
| `j_inc10k` | 1.50 (95% CI, 1.27-1.77) | working/v23/03d_03e_RESULTS.md | income <$10k, joint |
| `j_unemp` | 1.28 (95% CI, 1.13-1.45) | working/v23/03d_03e_RESULTS.md | unemployment, joint |
| `j_rent` | 1.12 (95% CI, 1.02-1.24) | working/v23/03d_03e_RESULTS.md | renting, joint |
| `j_instab` | 0.88; 95% CI, 0.79-0.97 | working/v23/03d_03e_RESULTS.md | housing instability, joint, COVID-19 |
| `j_instab_flu` | 0.97; 95% CI, 0.83-1.13 | working/v23/03h_03i_RESULTS.md | housing instability, joint, influenza |
| `f_medicaid_ds` | 1.60 (95% CI, 1.35-1.89) | working/v23/03h_03i_RESULTS.md | Medicaid, domain-specific, influenza |
| `f_medicaid_j` | 0.93 (95% CI, 0.75-1.15) | working/v23/03h_03i_RESULTS.md | Medicaid, joint, influenza |
| `f_inc10k` | 1.64 (95% CI, 1.29-2.07) | working/v23/03h_03i_RESULTS.md | income <$10k, joint, influenza |
| `f_inc25k` | 1.92 (95% CI, 1.55-2.39) | working/v23/03h_03i_RESULTS.md | income $10-25k, joint, influenza |
| `f_unemp` | 1.41 (95% CI, 1.18-1.69) | working/v23/03h_03i_RESULTS.md | unemployment, joint, influenza |
| `f_rent` | 1.19 (95% CI, 1.01-1.39) | working/v23/03h_03i_RESULTS.md | renting, joint, influenza |
| `trend_covid_log10` | 0.78 per log10 step | working/v23/03d_03e_RESULTS.md | income trend, log10 midpoint, COVID-19 |
| `trend_covid_log10_ci` | 95% CI, 0.69-0.89 | working/v23/03d_03e_RESULTS.md | its interval |
| `trend_covid_rank` | 0.94 per rank step | working/v23/03d_03e_RESULTS.md | income trend, rank, COVID-19 |
| `trend_flu` | 0.69 (95% CI, 0.57-0.83) | working/v23/03f_flu_mi40_RESULTS.md | income trend, log10, influenza |
| `block_hi_covid` | F = 1.72; 3 df; P = .16 | working/v23/03d_03e_RESULTS.md | high-income block D1, COVID-19 |
| `block_hi_flu` | F = 0.24; 3 df; P = .87 | working/v23/03f_flu_mi40_RESULTS.md | high-income block D1, influenza |
| `int_inc_covid` | F = 0.90; 12 df; P = .54 | working/v23/03d_03e_RESULTS.md | income x wave |
| `int_ins_covid` | F = 3.33; 8 df; P < .001 | working/v23/03d_03e_RESULTS.md | insurance x wave |
| `int_inc_flu` | F = 0.50; 12 df; P = .91 | working/v23/03f_flu_mi40_RESULTS.md | income x period |
| `int_ins_flu` | F = 2.47; 8 df; P = .01 | working/v23/03f_flu_mi40_RESULTS.md | insurance x period |
| `wave_inc_pre` | 1.45 (95% CI, 1.20-1.75) | working/v23/03d_03e_RESULTS.md | income <$10k, pre-Delta |
| `wave_inc_delta` | 1.57 (95% CI, 1.16-2.13) | working/v23/03d_03e_RESULTS.md | income <$10k, Delta |
| `wave_inc_omicron` | 1.56 (95% CI, 1.24-1.95) | working/v23/03d_03e_RESULTS.md | income <$10k, Omicron |
| `wave_med_pre` | 1.39 (95% CI, 1.17-1.64) | working/v23/03d_03e_RESULTS.md | Medicaid, pre-Delta |
| `wave_med_delta` | 0.89 (95% CI, 0.69-1.15) | working/v23/03d_03e_RESULTS.md | Medicaid, Delta |
| `wave_med_omicron` | 0.91 (95% CI, 0.76-1.10) | working/v23/03d_03e_RESULTS.md | Medicaid, Omicron |
| `per_med_post` | 0.76 (95% CI, 0.58-1.00) | working/v23/03h_03i_RESULTS.md | Medicaid, post-pandemic, influenza |
| `per_n_pandemic` | 817 | working/v23/03h_03i_RESULTS.md | matched rows in the influenza pandemic period |
| `race_joint` | 2.07; 95% CI, 1.87-2.29 | working/v23/03j_race_RESULTS.md | Black race, joint model |
| `race_pct_all` | 16.2% | working/v23/03j_race_RESULTS.md | share of the base-model log OR removed by the domains |
| `race_pct_income` | 93.8% | working/v23/03j_race_RESULTS.md | income's share of that reduction |
| `sens_indicator_medicaid` | AOR, 1.19 | the previous version, carried unchanged | Medicaid under the missing-indicator specification |
| `sens_congeniality` | 0.022 on the log scale | working/v23/03d_03e_RESULTS.md | largest congenial-vs-legacy difference |
| `miss_income_case` | 26.5% | the previous version, carried unchanged | income missing among cases |
| `miss_income_ctrl` | 19.0% | the previous version, carried unchanged | income missing among controls |
| `survey_lag` | 692 days (IQR, 286-985 days) | the previous version, carried unchanged | survey to index lag, COVID-19 |
| `survey_preindex` | 86.4% | the previous version, carried unchanged | surveys completed before infection, COVID-19 |
| `zcode_unemployed` | 3,608 | the previous version, carried unchanged | participants reporting unemployment |
| `zcode_z56` | 208 (5.8%) | the previous version, carried unchanged | of them carrying a Z56 code |
| `ontario` | 56.9% | the previous version, carried unchanged | vaccination share of income inequality in Ontario deaths |
| `ontario_n` | 11.2-million-person | the previous version, carried unchanged | size of the Ontario cohort, from the cited paper |
| `mude_black` | 1.9 for Black populations | the previous version, carried unchanged | pooled standardized hospitalization ratio, cited |
| `mude_white` | 0.74 for White populations | the previous version, carried unchanged | the same, White populations, cited |
| `smd_post` | below 0.03 after matching | working/v23/flu_table1_RESULTS.md | post-matching SMD, both arms |
| `t1_covid_female` | 2,409 [60.3%] female | the previous version, carried unchanged | Table 1, COVID-19 cases |
| `t1_covid_age` | 57.5 [16.2] years | the previous version, carried unchanged | Table 1, COVID-19 case age |
| `t1_flu_female` | 1,090 [65.2%] female | working/v23/flu_table1_RESULTS.md | Table 1, influenza cases |
| `t1_flu_age` | 56.3 [16.3] years | working/v23/flu_table1_RESULTS.md | Table 1, influenza case age |
| `flu_preindex` | 100% in the influenza arm | working/v23/flu_table1_RESULTS.md | surveys completed before index, influenza |
| `per_med_pre_flu` | 1.46 (95% CI, 0.97-2.19) | working/v23/03h_03i_RESULTS.md | Medicaid, pre-pandemic, influenza |
| `per_med_pan_flu` | 1.82 (95% CI, 0.80-4.14) | working/v23/03h_03i_RESULTS.md | Medicaid, pandemic, influenza |
| `per_inc_flu_all` | 1.72, 1.12, and 1.64 | working/v23/03h_03i_RESULTS.md | income <$10k across the three influenza periods |
| `trend_flu_rank` | 0.87 (95% CI, 0.82-0.92) | working/v23/03f_flu_mi40_RESULTS.md | income trend, rank, influenza |
| `block_lo` | both P < .001 | working/v23/03d_03e_RESULTS.md | low-income block D1, both arms |
| `aou_total` | 413,457 | the previous version, carried unchanged | All of Us participants screened |
| `wave_within_strata` | 96.1% of COVID-19 strata | working/v23/03d_03e_RESULTS.md | COVID-19 strata in which pandemic wave varies |
