#!/usr/bin/env Rscript
# ─────────────────────────────────────────────────────────────────────
# COVID-19 Severity × SDoH — Reviewer Sensitivity Analyses
#
# Runs AFTER 02_models.R and 01c_sensitivity_etl.py.
# Factor setup copied verbatim from 02_models.R lines 64-118.
#
# Sensitivity analyses:
#   S1  IP-only cases (drop ED-prolonged-only cases + their strata)
#   S2  Clean controls (drop controls with any acute-care 14d visit)
#   S3  Pre-index SDoH survey only (drop post-infection survey)
#   S4  No-vaccination covariate
#   S5  Collapsed income (3-level: <$35K / $35-100K / >$100K)
#
# Usage: Rscript 02b_sensitivity_models.R aou_v7
# License: MIT
# ─────────────────────────────────────────────────────────────────────

library(survival)
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(readr))

if (!requireNamespace("sandwich", quietly = TRUE)) install.packages("sandwich")
if (!requireNamespace("lmtest", quietly = TRUE))   install.packages("lmtest")
library(sandwich)
library(lmtest)

# ── Parse argument ───────────────────────────────────────────────────
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1 || !grepl("^aou_", args[1])) {
  cat("Usage: Rscript 02b_sensitivity_models.R aou_v7\n")
  quit(status = 1)
}
COHORT  <- args[1]
RESULTS <- file.path("results", COHORT)

cat(strrep("=", 70), "\n")
cat("SENSITIVITY ANALYSES  [", toupper(COHORT), "]\n")
cat(strrep("=", 70), "\n")

# ── Load data ────────────────────────────────────────────────────────
reg_path       <- file.path(RESULTS, "07_regression_base.csv")
sdoh_path      <- file.path(RESULTS, "04_sdoh.csv")
timing_path    <- file.path(RESULTS, "04b_sdoh_timing.csv")
case_comp_path <- file.path(RESULTS, "08a_case_visit_components.csv")
ctrl_ed_path   <- file.path(RESULTS, "08b_control_ed_flags.csv")
income3_path   <- file.path(RESULTS, "08d_income_collapsed.csv")

# Download from bucket if needed
bucket <- Sys.getenv("WORKSPACE_BUCKET")
if (!file.exists(case_comp_path) && nchar(bucket) > 0) {
  bdir <- paste0(bucket, "/data/covid_sdoh/", COHORT, "/")
  for (f in c("08a_case_visit_components.csv", "08b_control_ed_flags.csv",
              "08d_income_collapsed.csv")) {
    system(paste0("gsutil cp ", bdir, f, " ", RESULTS, "/"), intern = TRUE)
  }
}

regression_bm <- read_csv(reg_path, show_col_types = FALSE)
sdoh_raw      <- read_csv(sdoh_path, show_col_types = FALSE)
timing        <- read_csv(timing_path, show_col_types = FALSE)
case_comp     <- read_csv(case_comp_path, show_col_types = FALSE)
ctrl_ed       <- read_csv(ctrl_ed_path, show_col_types = FALSE)
income3       <- read_csv(income3_path, show_col_types = FALSE)

cat("  Regression data:", nrow(regression_bm), "rows,", ncol(regression_bm), "cols\n")
cat("  Case components:", nrow(case_comp), "rows\n")
cat("  Control ED flags:", nrow(ctrl_ed), "rows\n")


# ══════════════════════════════════════════════════════════════════════
# FACTOR SETUP — COPIED VERBATIM FROM 02_models.R lines 64-118
# ══════════════════════════════════════════════════════════════════════

# ── Detect available columns (02_models.R lines 65-76) ───────────────
has_race      <- "race" %in% names(regression_bm) &&
                 any(regression_bm$race != "Unknown", na.rm = TRUE)
has_ethnicity <- "ethnicity" %in% names(regression_bm) &&
                 any(regression_bm$ethnicity != "Unknown", na.rm = TRUE)
has_plantype  <- "plan_type" %in% names(regression_bm)
has_region    <- "region_name" %in% names(regression_bm)
has_wave      <- "pandemic_wave" %in% names(regression_bm)

cat("  Features: race=", has_race, " ethnicity=", has_ethnicity,
    " wave=", has_wave, "\n")

# ── Factor encoding (02_models.R lines 78-97) ────────────────────────
regression_bm$f.sex  <- factor(regression_bm$sex_at_birth,
                               levels = c("Male","Female","Other"))
regression_bm$f.age  <- factor(regression_bm$age_group,
                               levels = c("<45","45-54","55-64","65+"))
regression_bm$f.vacc <- factor(regression_bm$vaccination,
                               levels = c("Unknown","Vaccinated"))

if (has_race)      regression_bm$f.race <- factor(regression_bm$race,
                     levels = c("White","Black","Asian","Other"))
if (has_ethnicity) regression_bm$f.ethnicity <- factor(regression_bm$ethnicity,
                     levels = c("Not Hispanic","Hispanic","Other"))
if (has_plantype)  regression_bm$f.plan <- factor(regression_bm$plan_type)
if (has_region)    regression_bm$f.region <- factor(regression_bm$region_name)
if (has_wave)      regression_bm$f.wave <- factor(regression_bm$pandemic_wave,
                     levels = c("pre_delta","delta","omicron"))

# ── Comorbidities (02_models.R lines 99-107) ─────────────────────────
como <- c("Myocardial_Infarction","Congestive_Heart_Failure",
          "Peripheral_Vascular_Disease","Cerebrovascular_Disease","Dementia",
          "Chronic_Pulmonary_Disease","Rheumatic_Disease","Peptic_Ulcer_Disease",
          "Liver_Disease_Mild","Liver_Disease_Moderate_Severe",
          "Diabetes_without_Chronic_Complications",
          "Diabetes_with_Chronic_Complications",
          "Hemiplegia_Paraplegia","Renal_Disease_Mild_Moderate",
          "Renal_Disease_Severe","HIV","Metastatic_Solid_Tumor","Malignancy","AIDS")
for (c_col in como) regression_bm[[c_col]][is.na(regression_bm[[c_col]])] <- 0

# ── Base terms (02_models.R lines 110-118) ────────────────────────────
base_terms <- c("f.sex", "f.age", "f.vacc")
if (has_race)      base_terms <- c(base_terms, "f.race")
if (has_ethnicity) base_terms <- c(base_terms, "f.ethnicity")
if (has_wave)      base_terms <- c(base_terms, "f.wave")
if (has_plantype)  base_terms <- c(base_terms, "f.plan")
if (has_region)    base_terms <- c(base_terms, "f.region")
base_terms <- c(base_terms, como)

base_rhs <- paste(base_terms, collapse = " + ")
cat("  Base formula RHS:", length(base_terms), "terms\n")

# No-vaccination version
base_terms_no_vacc <- setdiff(base_terms, "f.vacc")
base_rhs_no_vacc <- paste(base_terms_no_vacc, collapse = " + ")


# ══════════════════════════════════════════════════════════════════════
# MERGE SDoH + SENSITIVITY DATA
# ══════════════════════════════════════════════════════════════════════

reg_sdoh <- merge(regression_bm, sdoh_raw, by = "person_id", all.x = TRUE)
reg_sdoh <- merge(reg_sdoh, timing[, c("person_id", "sdoh_pre_index")],
                  by = "person_id", all.x = TRUE)
reg_sdoh <- merge(reg_sdoh, income3, by = "person_id", all.x = TRUE)

cat("  Merged reg_sdoh:", nrow(reg_sdoh), "rows\n")

# ── SDoH factors (02_models.R lines 291-319) ─────────────────────────
reg_sdoh$f.income <- factor(
  ifelse(is.na(reg_sdoh$income), "Missing", reg_sdoh$income),
  levels = c("35k_100k","less_10k","10k_25k","25k_35k",
             "100k_150k","150k_200k","more_200k","Missing"))

reg_sdoh$f.insurance <- factor(
  ifelse(is.na(reg_sdoh$insurance_type), "Missing", reg_sdoh$insurance_type),
  levels = c("Employer","Medicare","Medicaid","Other_None","Missing"))

reg_sdoh$f.education <- factor(
  ifelse(is.na(reg_sdoh$education), "Missing", reg_sdoh$education),
  levels = c("Advanced","Never_Attended","Below_GED","GED_or_College","Missing"))

reg_sdoh$f.employment <- factor(
  ifelse(is.na(reg_sdoh$employment), "Missing", reg_sdoh$employment),
  levels = c("Employed","Student","Unemployed","Others","Missing"))

reg_sdoh$f.housing <- factor(
  ifelse(is.na(reg_sdoh$housing), "Missing", reg_sdoh$housing),
  levels = c("Own","Rent","Others","Missing"))

reg_sdoh$f.housing_stability <- factor(
  ifelse(is.na(reg_sdoh$housing_stability), "Missing", reg_sdoh$housing_stability),
  levels = c("Stable","Unstable","Missing"))

reg_sdoh$f.disability_any <- factor(
  ifelse(is.na(reg_sdoh$disability_any), "Missing", reg_sdoh$disability_any),
  levels = c("No","Yes","Missing"))

joint_sdoh <- "f.income + f.insurance + f.education + f.employment + f.housing + f.housing_stability + f.disability_any"
joint_rhs  <- paste(base_rhs, "+", joint_sdoh)


# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

extract_aor <- function(model, model_name, data = NULL) {
  s <- summary(model)$coefficients
  coef_vals <- s[, "coef"]
  se_vals   <- s[, "se(coef)"]
  p_vals    <- s[, "Pr(>|z|)"]

  if (!is.null(data) && "person_id" %in% names(data)) {
    tryCatch({
      V <- vcovCL(model, cluster = data$person_id)
      se_vals <- sqrt(diag(V))
      z_vals  <- coef_vals / se_vals
      p_vals  <- 2 * pnorm(-abs(z_vals))
    }, error = function(e) {
      cat("    WARNING: vcovCL failed (", e$message, "), using model SEs\n")
    })
  }

  data.frame(
    variable  = rownames(s),
    AOR       = exp(coef_vals),
    CI_lower  = exp(coef_vals - 1.96 * se_vals),
    CI_upper  = exp(coef_vals + 1.96 * se_vals),
    p_value   = p_vals,
    model     = model_name,
    cohort    = COHORT,
    stringsAsFactors = FALSE, row.names = NULL
  )
}


run_sensitivity <- function(df, label, rhs_formula) {
  cat("\n", strrep("=", 60), "\n")
  cat(label, "\n")
  cat(strrep("=", 60), "\n")

  n_cases <- sum(df$Treatment == 1)
  n_ctrls <- sum(df$Treatment == 0)
  n_strata <- length(unique(df$stratum))
  cat(sprintf("  N=%d (cases=%d, controls=%d, strata=%d)\n",
              nrow(df), n_cases, n_ctrls, n_strata))

  # Drop strata with only cases or only controls
  strata_ok <- df %>% group_by(stratum) %>%
    summarise(n_case = sum(Treatment == 1),
              n_ctrl = sum(Treatment == 0), .groups = "drop") %>%
    filter(n_case > 0 & n_ctrl > 0) %>% pull(stratum)
  df <- df[df$stratum %in% strata_ok, ]
  cat(sprintf("  After dropping incomplete strata: %d obs, %d strata\n",
              nrow(df), length(strata_ok)))

  tryCatch({
    frm <- as.formula(paste("Treatment ~", rhs_formula, "+ strata(stratum)"))
    fit <- clogit(frm, data = df)
    aor <- extract_aor(fit, label, df)

    # Print SDoH rows
    sv <- grepl("f\\.income|f\\.insurance|f\\.education|f\\.employment|f\\.housing|f\\.disability",
                aor$variable)
    cat("\n  SDoH coefficients:\n")
    print(aor[sv, c("variable", "AOR", "CI_lower", "CI_upper", "p_value")])

    # Black race AOR
    if (has_race) {
      br <- aor[grepl("f\\.raceBlack", aor$variable), ]
      if (nrow(br) > 0) {
        cat(sprintf("\n  Black AOR: %.3f (%.3f-%.3f)\n",
                    br$AOR, br$CI_lower, br$CI_upper))
      }
    }

    outfile <- file.path(RESULTS,
      paste0("sensitivity_", gsub("[^a-zA-Z0-9]", "_", label),
             "_coefficients.csv"))
    write_csv(aor, outfile)
    cat("  Saved:", outfile, "\n")
    return(aor)
  }, error = function(e) {
    cat("  clogit ERROR:", e$message, "\n")
    return(NULL)
  })
}


# ══════════════════════════════════════════════════════════════════════
# SANITY CHECK: replicate joint model on full data
# ══════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 60), "\n")
cat("SANITY CHECK: joint model on full reg_sdoh\n")
cat(strrep("=", 60), "\n")

sanity_result <- run_sensitivity(reg_sdoh, "SANITY_full_data", joint_rhs)
if (is.null(sanity_result)) {
  cat("\n  *** SANITY CHECK FAILED — stopping ***\n")
  quit(status = 1)
}
cat("  Sanity check PASSED.\n")


# ══════════════════════════════════════════════════════════════════════
# S1: IP-ONLY CASES (drop ED-prolonged-only cases)
# ══════════════════════════════════════════════════════════════════════
all_results <- list()

ed_only_cases <- case_comp$person_id[case_comp$ed_prolonged_only == 1]
cat("\n  ED-prolonged-only cases to remove:", length(ed_only_cases), "\n")

strata_to_drop_s1 <- reg_sdoh$stratum[
  reg_sdoh$Treatment == 1 & reg_sdoh$person_id %in% ed_only_cases
]
df_s1 <- reg_sdoh[!reg_sdoh$stratum %in% strata_to_drop_s1, ]
all_results[["S1"]] <- run_sensitivity(df_s1, "S1_IP_only_cases", joint_rhs)


# ══════════════════════════════════════════════════════════════════════
# S2: CLEAN CONTROLS (drop controls with acute-care utilization)
# ══════════════════════════════════════════════════════════════════════
ctrl_with_acute <- ctrl_ed$person_id[ctrl_ed$ctrl_had_any_acute_14d == 1]
cat("\n  Controls with acute-care visits to remove:", length(ctrl_with_acute), "\n")

df_s2 <- reg_sdoh[!(reg_sdoh$Treatment == 0 &
                     reg_sdoh$person_id %in% ctrl_with_acute), ]
all_results[["S2"]] <- run_sensitivity(df_s2, "S2_clean_controls", joint_rhs)


# ══════════════════════════════════════════════════════════════════════
# S3: PRE-INDEX SDoH SURVEY ONLY
# ══════════════════════════════════════════════════════════════════════
pre_index_ids <- timing$person_id[timing$sdoh_pre_index == 1]
cat("\n  Pre-index survey participants:", length(pre_index_ids), "\n")

strata_to_drop_s3 <- reg_sdoh$stratum[
  reg_sdoh$Treatment == 1 & !reg_sdoh$person_id %in% pre_index_ids
]
df_s3 <- reg_sdoh[!reg_sdoh$stratum %in% strata_to_drop_s3, ]
df_s3 <- df_s3[df_s3$person_id %in% pre_index_ids, ]
all_results[["S3"]] <- run_sensitivity(df_s3, "S3_pre_index_sdoh", joint_rhs)


# ══════════════════════════════════════════════════════════════════════
# S4: NO VACCINATION COVARIATE
# ══════════════════════════════════════════════════════════════════════
joint_rhs_no_vacc <- paste(base_rhs_no_vacc, "+", joint_sdoh)
all_results[["S4"]] <- run_sensitivity(reg_sdoh, "S4_no_vaccination",
                                        joint_rhs_no_vacc)


# ══════════════════════════════════════════════════════════════════════
# S5: COLLAPSED INCOME (3-level)
# ══════════════════════════════════════════════════════════════════════
df_s5 <- reg_sdoh
df_s5$income_3cat[is.na(df_s5$income_3cat)] <- "Missing"
df_s5$f.income_3cat <- factor(df_s5$income_3cat,
  levels = c("35k_100k", "lt_35k", "gt_100k", "Missing"))

joint_sdoh_s5 <- "f.income_3cat + f.insurance + f.education + f.employment + f.housing + f.housing_stability + f.disability_any"
joint_rhs_s5 <- paste(base_rhs, "+", joint_sdoh_s5)
all_results[["S5"]] <- run_sensitivity(df_s5, "S5_income_collapsed", joint_rhs_s5)


# ══════════════════════════════════════════════════════════════════════
# COMPARISON SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 70), "\n")
cat("SENSITIVITY COMPARISON SUMMARY\n")
cat(strrep("=", 70), "\n")

key_vars <- c("f.incomeless_10k", "f.income10k_25k",
              "f.insuranceMedicaid", "f.employmentUnemployed",
              "f.housingRent")

summary_rows <- list()
for (sname in names(all_results)) {
  aor <- all_results[[sname]]
  if (is.null(aor)) next
  for (v in key_vars) {
    row <- aor[aor$variable == v, ]
    if (nrow(row) > 0) {
      summary_rows[[length(summary_rows) + 1]] <- data.frame(
        sensitivity = sname,
        variable = v,
        AOR = round(row$AOR, 3),
        CI = paste0(round(row$CI_lower, 2), "-", round(row$CI_upper, 2)),
        p_value = signif(row$p_value, 3),
        stringsAsFactors = FALSE
      )
    }
  }
  if (sname == "S5") {
    row <- aor[aor$variable == "f.income_3catlt_35k", ]
    if (nrow(row) > 0) {
      summary_rows[[length(summary_rows) + 1]] <- data.frame(
        sensitivity = "S5",
        variable = "f.income_3catlt_35k",
        AOR = round(row$AOR, 3),
        CI = paste0(round(row$CI_lower, 2), "-", round(row$CI_upper, 2)),
        p_value = signif(row$p_value, 3),
        stringsAsFactors = FALSE
      )
    }
  }
}

if (length(summary_rows) > 0) {
  summary_df <- do.call(rbind, summary_rows)
  cat("\n")
  print(summary_df, row.names = FALSE)
  write_csv(summary_df, file.path(RESULTS, "sensitivity_summary_comparison.csv"))
  cat("\n  Saved: sensitivity_summary_comparison.csv\n")
}

# Primary analysis comparison
primary_path <- file.path(RESULTS, "joint_sdoh_coefficients.csv")
if (file.exists(primary_path)) {
  primary <- read_csv(primary_path, show_col_types = FALSE)
  primary_key <- primary[primary$variable %in% key_vars,
                         c("variable", "AOR", "CI_lower", "CI_upper", "p_value")]
  if (nrow(primary_key) > 0) {
    cat("\n  Primary analysis (for comparison):\n")
    print(primary_key, row.names = FALSE)
  }
}

# Upload to bucket
if (nchar(bucket) > 0) {
  system(paste0("gsutil -m cp ", RESULTS, "/sensitivity_*.csv ",
                bucket, "/data/covid_sdoh/", COHORT, "/"), intern = TRUE)
  cat("  Uploaded sensitivity CSVs to bucket.\n")
}

cat("\n", strrep("=", 70), "\n")
cat("ALL SENSITIVITY ANALYSES COMPLETE\n")
cat(strrep("=", 70), "\n")
