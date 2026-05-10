#!/usr/bin/env Rscript
# ─────────────────────────────────────────────────────────────────────
# COVID-19 Severity × SDoH — Reviewer Sensitivity Analyses
#
# Runs AFTER 03_models.R and 01c_sensitivity_etl.py.
# Reuses existing matched cohort; does NOT re-match.
#
# Sensitivity analyses:
#   S1  IP-only cases (drop ED-prolonged-only cases + their strata)
#   S2  Clean controls (drop controls with any acute-care 14d visit)
#   S3  Pre-index SDoH survey only (drop post-infection survey)
#   S4  No-vaccination covariate (remove from base model)
#   S5  Collapsed income (3-level: <$35K / $35-100K / >$100K)
#
# Each runs the joint SDoH model (Model C) and extracts:
#   - Full coefficient table
#   - SDoH-only coefficients for comparison with primary analysis
#   - Black race AOR for attenuation tracking
#
# Usage: Rscript 04_sensitivity.R aou_v7
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
reg_path   <- file.path(RESULTS, "08_regression_base.csv")
sdoh_path  <- file.path(RESULTS, "04_sdoh.csv")
timing_path <- file.path(RESULTS, "04b_sdoh_timing.csv")
case_comp_path <- file.path(RESULTS, "09a_case_visit_components.csv")
ctrl_ed_path   <- file.path(RESULTS, "09b_control_ed_flags.csv")
income3_path   <- file.path(RESULTS, "09d_income_collapsed.csv")

# Download from bucket if needed
bucket <- Sys.getenv("WORKSPACE_BUCKET")
if (!file.exists(case_comp_path) && nchar(bucket) > 0) {
  bdir <- paste0(bucket, "/data/covid_sdoh/", COHORT, "/")
  for (f in c("09a_case_visit_components.csv", "09b_control_ed_flags.csv",
              "09d_income_collapsed.csv")) {
    system(paste0("gsutil cp ", bdir, f, " ", RESULTS, "/"), intern = TRUE)
  }
}

regression_bm <- read_csv(reg_path, show_col_types = FALSE)
sdoh_raw      <- read_csv(sdoh_path, show_col_types = FALSE)
timing        <- read_csv(timing_path, show_col_types = FALSE)
case_comp     <- read_csv(case_comp_path, show_col_types = FALSE)
ctrl_ed       <- read_csv(ctrl_ed_path, show_col_types = FALSE)
income3       <- read_csv(income3_path, show_col_types = FALSE)

cat("  Loaded regression data:", nrow(regression_bm), "rows\n")
cat("  Loaded case components:", nrow(case_comp), "rows\n")
cat("  Loaded control ED flags:", nrow(ctrl_ed), "rows\n")

# ── Merge SDoH into regression data ─────────────────────────────────
reg_sdoh <- merge(regression_bm, sdoh_raw, by = "person_id", all.x = TRUE)
reg_sdoh <- merge(reg_sdoh, timing[, c("person_id", "sdoh_pre_index")],
                  by = "person_id", all.x = TRUE)
reg_sdoh <- merge(reg_sdoh, income3, by = "person_id", all.x = TRUE)

# ── Detect columns (same logic as 02_models.R) ──────────────────────
has_race <- "race" %in% names(regression_bm) &&
            any(regression_bm$race != "White", na.rm = TRUE)
has_ethnicity <- "ethnicity" %in% names(regression_bm)
has_wave <- "pandemic_wave" %in% names(regression_bm)

# ── Factor setup ─────────────────────────────────────────────────────
setup_factors <- function(df) {
  df$f.sex  <- factor(df$sex, levels = c("Male", "Female"))
  df$f.age  <- factor(df$age_group,
    levels = c("18_44", "45_54", "55_64", "65plus"))
  df$f.vacc <- factor(df$vaccination,
    levels = c("Unknown", "Vaccinated"))
  if (has_race)
    df$f.race <- factor(df$race,
      levels = c("White", "Black", "Asian", "Other"))
  if (has_ethnicity)
    df$f.ethnicity <- factor(df$ethnicity,
      levels = c("Not_Hispanic", "Hispanic"))
  if (has_wave)
    df$f.wave <- factor(df$pandemic_wave,
      levels = c("pre_delta", "delta", "omicron"))

  # Comorbidities (same as 02_models.R)
  como <- c("MI", "CHF", "PVD", "Cerebrovascular", "Dementia",
            "Chronic_Pulmonary", "Rheumatic", "Peptic_Ulcer",
            "Mild_Liver", "DM_no_comp", "DM_comp",
            "Hemiplegia", "Renal_Mild_Mod", "Renal_Severe",
            "Malignancy", "Mod_Severe_Liver", "Metastatic",
            "AIDS", "HIV")
  como <- como[como %in% names(df)]

  # SDoH factors
  df$f.income <- factor(
    ifelse(is.na(df$income), "Missing", df$income),
    levels = c("35k_100k","less_10k","10k_25k","25k_35k",
               "100k_150k","150k_200k","more_200k","Missing"))
  df$f.insurance <- factor(
    ifelse(is.na(df$insurance_type), "Missing", df$insurance_type),
    levels = c("Employer","Medicare","Medicaid","Other_None","Missing"))
  df$f.education <- factor(
    ifelse(is.na(df$education), "Missing", df$education),
    levels = c("Advanced","Never_Attended","Below_GED",
               "GED_or_College","Missing"))
  df$f.employment <- factor(
    ifelse(is.na(df$employment), "Missing", df$employment),
    levels = c("Employed","Student","Unemployed","Others","Missing"))
  df$f.housing <- factor(
    ifelse(is.na(df$housing), "Missing", df$housing),
    levels = c("Own","Rent","Others","Missing"))
  df$f.housing_stability <- factor(
    ifelse(is.na(df$housing_stability), "Missing", df$housing_stability),
    levels = c("Stable","Unstable","Missing"))
  df$f.disability_any <- factor(
    ifelse(is.na(df$disability_any), "Missing", df$disability_any),
    levels = c("No","Yes","Missing"))

  list(df = df, como = como)
}

# ── Build formula strings ────────────────────────────────────────────
build_base_terms <- function(como, include_vacc = TRUE) {
  terms <- "f.sex + f.age"
  if (include_vacc) terms <- paste(terms, "+ f.vacc")
  if (has_race)      terms <- paste(terms, "+ f.race")
  if (has_ethnicity)  terms <- paste(terms, "+ f.ethnicity")
  if (has_wave)       terms <- paste(terms, "+ f.wave")
  paste(terms, "+", paste(como, collapse = " + "))
}

joint_sdoh <- "f.income + f.insurance + f.education + f.employment + f.housing + f.housing_stability + f.disability_any"

# ── Extract helper (same as 02_models.R) ─────────────────────────────
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
    stringsAsFactors = FALSE, row.names = NULL
  )
}


# ── Run one sensitivity model ────────────────────────────────────────
run_sensitivity <- function(df, label, base_rhs) {
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
  cat(sprintf("  After dropping empty strata: %d obs, %d strata\n",
              nrow(df), length(strata_ok)))

  rhs <- paste(base_rhs, "+", joint_sdoh)
  frm <- as.formula(paste("Treatment ~", rhs, "+ strata(stratum)"))

  tryCatch({
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
        cat(sprintf("\n  Black AOR: %.3f (%.3f–%.3f)\n",
                    br$AOR, br$CI_lower, br$CI_upper))
      }
    }

    write_csv(aor, file.path(RESULTS,
      paste0("sensitivity_", gsub("[^a-zA-Z0-9]", "_", label),
             "_coefficients.csv")))
    return(aor)
  }, error = function(e) {
    cat("  ERROR:", e$message, "\n")
    return(NULL)
  })
}


# =====================================================================
# SETUP
# =====================================================================
setup <- setup_factors(reg_sdoh)
reg_sdoh <- setup$df
como <- setup$como
base_rhs <- build_base_terms(como, include_vacc = TRUE)
base_rhs_no_vacc <- build_base_terms(como, include_vacc = FALSE)

all_results <- list()


# =====================================================================
# S1: IP-ONLY CASES (drop ED-prolonged-only cases)
# =====================================================================
# Remove strata where the case was an ED-prolonged-only case
ed_only_cases <- case_comp$person_id[case_comp$ed_prolonged_only == 1]
cat("\n  ED-prolonged-only cases to remove:", length(ed_only_cases), "\n")

# Find their strata
strata_to_drop_s1 <- reg_sdoh$stratum[
  reg_sdoh$Treatment == 1 & reg_sdoh$person_id %in% ed_only_cases
]
df_s1 <- reg_sdoh[!reg_sdoh$stratum %in% strata_to_drop_s1, ]
all_results[["S1"]] <- run_sensitivity(df_s1, "S1_IP_only_cases", base_rhs)


# =====================================================================
# S2: CLEAN CONTROLS (drop controls with acute-care utilization)
# =====================================================================
# Remove control ROWS (not strata) where control had any acute-care visit
ctrl_with_acute <- ctrl_ed$person_id[ctrl_ed$ctrl_had_any_acute_14d == 1]
cat("\n  Controls with acute-care visits to remove:", length(ctrl_with_acute), "\n")

df_s2 <- reg_sdoh[!(reg_sdoh$Treatment == 0 &
                     reg_sdoh$person_id %in% ctrl_with_acute), ]
all_results[["S2"]] <- run_sensitivity(df_s2, "S2_clean_controls", base_rhs)


# =====================================================================
# S3: PRE-INDEX SDoH SURVEY ONLY
# =====================================================================
# Keep only persons whose Basics Survey preceded COVID infection
pre_index_ids <- timing$person_id[timing$sdoh_pre_index == 1]
cat("\n  Pre-index survey participants:", length(pre_index_ids), "\n")

# Remove strata where CASE doesn't have pre-index survey
strata_to_drop_s3 <- reg_sdoh$stratum[
  reg_sdoh$Treatment == 1 & !reg_sdoh$person_id %in% pre_index_ids
]
df_s3 <- reg_sdoh[!reg_sdoh$stratum %in% strata_to_drop_s3, ]
# Also drop controls without pre-index survey
df_s3 <- df_s3[df_s3$person_id %in% pre_index_ids, ]
all_results[["S3"]] <- run_sensitivity(df_s3, "S3_pre_index_sdoh", base_rhs)


# =====================================================================
# S4: NO VACCINATION COVARIATE
# =====================================================================
all_results[["S4"]] <- run_sensitivity(reg_sdoh, "S4_no_vaccination",
                                        base_rhs_no_vacc)


# =====================================================================
# S5: COLLAPSED INCOME (3-level)
# =====================================================================
cat("\n", strrep("=", 60), "\n")
cat("S5: COLLAPSED INCOME (3-level)\n")
cat(strrep("=", 60), "\n")

df_s5 <- reg_sdoh
df_s5$income_3cat[is.na(df_s5$income_3cat)] <- "Missing"
df_s5$f.income_3cat <- factor(df_s5$income_3cat,
  levels = c("35k_100k", "lt_35k", "gt_100k", "Missing"))

# Replace f.income with f.income_3cat in joint model
joint_sdoh_s5 <- "f.income_3cat + f.insurance + f.education + f.employment + f.housing + f.housing_stability + f.disability_any"
rhs_s5 <- paste(base_rhs, "+", joint_sdoh_s5)
frm_s5 <- as.formula(paste("Treatment ~", rhs_s5, "+ strata(stratum)"))

tryCatch({
  fit_s5 <- clogit(frm_s5, data = df_s5)
  aor_s5 <- extract_aor(fit_s5, "S5_income_collapsed", df_s5)
  sv <- grepl("f\\.income_3cat|f\\.insurance|f\\.education|f\\.employment|f\\.housing|f\\.disability",
              aor_s5$variable)
  cat("\n  SDoH coefficients (collapsed income):\n")
  print(aor_s5[sv, c("variable", "AOR", "CI_lower", "CI_upper", "p_value")])
  write_csv(aor_s5, file.path(RESULTS, "sensitivity_S5_income_collapsed_coefficients.csv"))
  all_results[["S5"]] <- aor_s5
}, error = function(e) { cat("  ERROR:", e$message, "\n") })


# =====================================================================
# COMPARISON SUMMARY TABLE
# =====================================================================
cat("\n", strrep("=", 70), "\n")
cat("SENSITIVITY COMPARISON SUMMARY\n")
cat(strrep("=", 70), "\n")

# Extract key SDoH variables across all models for side-by-side comparison
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
        AOR = row$AOR,
        CI_lower = row$CI_lower,
        CI_upper = row$CI_upper,
        p_value = row$p_value,
        stringsAsFactors = FALSE
      )
    }
  }
  # Also grab collapsed income if S5
  if (sname == "S5") {
    row <- aor[aor$variable == "f.income_3catlt_35k", ]
    if (nrow(row) > 0) {
      summary_rows[[length(summary_rows) + 1]] <- data.frame(
        sensitivity = "S5",
        variable = "f.income_3catlt_35k",
        AOR = row$AOR,
        CI_lower = row$CI_lower,
        CI_upper = row$CI_upper,
        p_value = row$p_value,
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

# Also add primary analysis values for comparison
primary_path <- file.path(RESULTS, "joint_sdoh_coefficients.csv")
if (file.exists(primary_path)) {
  primary <- read_csv(primary_path, show_col_types = FALSE)
  primary_key <- primary[primary$variable %in% key_vars,
                         c("variable", "AOR", "CI_lower", "CI_upper", "p_value")]
  primary_key$sensitivity <- "PRIMARY"
  if (nrow(primary_key) > 0) {
    cat("\n  Primary analysis (for comparison):\n")
    print(primary_key[, c("sensitivity", "variable", "AOR", "CI_lower",
                          "CI_upper", "p_value")], row.names = FALSE)
  }
}

cat("\n", strrep("=", 70), "\n")
cat("ALL SENSITIVITY ANALYSES COMPLETE\n")
cat(strrep("=", 70), "\n")
