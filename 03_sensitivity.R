#!/usr/bin/env Rscript
# ─────────────────────────────────────────────────────────────────────
# COVID-19 Severity × SDoH — Reviewer Sensitivity Analyses
#
# Runs AFTER 02_models.R and 01c_sensitivity_etl.py.
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
# Usage: Rscript 03_sensitivity.R aou_v7
# License: MIT
# ─────────────────────────────────────────────────────────────────────

library(survival)
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(readr))

# Set CRAN mirror for non-interactive environments (HPC, Rscript)
if (is.null(getOption("repos")) || getOption("repos")["CRAN"] == "@CRAN@") {
  options(repos = c(CRAN = "https://cloud.r-project.org"))
}
if (!requireNamespace("sandwich", quietly = TRUE)) install.packages("sandwich")
if (!requireNamespace("lmtest", quietly = TRUE))   install.packages("lmtest")
library(sandwich)
library(lmtest)

# ── Parse argument ───────────────────────────────────────────────────
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1 || !grepl("^aou_", args[1])) {
  cat("Usage: Rscript 03_sensitivity.R aou_v7\n")
  quit(status = 1)
}
COHORT  <- args[1]
RESULTS <- file.path("results", COHORT)

cat(strrep("=", 70), "\n")
cat("SENSITIVITY ANALYSES  [", toupper(COHORT), "]\n")
cat(strrep("=", 70), "\n")

# ── Load data (auto-detect old vs new pipeline numbering) ────────────
# New pipeline (01b_psm.R):  08_regression_base.csv, 09a/b/d
# Old pipeline (embedded PSM): 07_regression_base.csv, 08a/b/d
resolve <- function(new_name, old_name) {
  p_new <- file.path(RESULTS, new_name)
  p_old <- file.path(RESULTS, old_name)
  if (file.exists(p_new)) return(p_new)
  if (file.exists(p_old)) return(p_old)
  return(p_new)  # default to new (will trigger bucket download)
}

reg_path       <- resolve("08_regression_base.csv", "07_regression_base.csv")
sdoh_path      <- file.path(RESULTS, "04_sdoh.csv")
timing_path    <- file.path(RESULTS, "04b_sdoh_timing.csv")
case_comp_path <- resolve("09a_case_visit_components.csv", "08a_case_visit_components.csv")
ctrl_ed_path   <- resolve("09b_control_ed_flags.csv", "08b_control_ed_flags.csv")
income3_path   <- resolve("09d_income_collapsed.csv", "08d_income_collapsed.csv")

cat("  Resolved paths:\n")
cat("    reg_base:   ", basename(reg_path), "\n")
cat("    case_comp:  ", basename(case_comp_path), "\n")
cat("    ctrl_ed:    ", basename(ctrl_ed_path), "\n")
cat("    income3:    ", basename(income3_path), "\n")

# Download from bucket if needed
bucket <- Sys.getenv("WORKSPACE_BUCKET")
if (!file.exists(case_comp_path) && nchar(bucket) > 0) {
  bdir <- paste0(bucket, "/data/covid_sdoh/", COHORT, "/")
  # Try both naming conventions
  for (pair in list(
    c("09a_case_visit_components.csv", "08a_case_visit_components.csv"),
    c("09b_control_ed_flags.csv", "08b_control_ed_flags.csv"),
    c("09d_income_collapsed.csv", "08d_income_collapsed.csv")
  )) {
    for (f in pair) {
      local_f <- file.path(RESULTS, f)
      if (!file.exists(local_f)) {
        res <- suppressWarnings(
          system(paste0("gsutil cp ", bdir, f, " ", RESULTS, "/"),
                 intern = TRUE, ignore.stderr = TRUE))
        if (file.exists(local_f)) break
      }
    }
  }
  # Also get regression base if missing
  if (!file.exists(reg_path)) {
    for (f in c("08_regression_base.csv", "07_regression_base.csv")) {
      local_f <- file.path(RESULTS, f)
      if (!file.exists(local_f)) {
        suppressWarnings(
          system(paste0("gsutil cp ", bdir, f, " ", RESULTS, "/"),
                 intern = TRUE, ignore.stderr = TRUE))
        if (file.exists(local_f)) { reg_path <- local_f; break }
      }
    }
  }
  # Re-resolve after downloads
  reg_path       <- resolve("08_regression_base.csv", "07_regression_base.csv")
  case_comp_path <- resolve("09a_case_visit_components.csv", "08a_case_visit_components.csv")
  ctrl_ed_path   <- resolve("09b_control_ed_flags.csv", "08b_control_ed_flags.csv")
  income3_path   <- resolve("09d_income_collapsed.csv", "08d_income_collapsed.csv")
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

# ══════════════════════════════════════════════════════════════════════
# FACTOR SETUP — COPIED VERBATIM FROM 02_models.R
# ══════════════════════════════════════════════════════════════════════

# ── Detect available columns ─────────────────────────────────────────
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

    sv <- grepl("f\\.income|f\\.insurance|f\\.education|f\\.employment|f\\.housing|f\\.disability",
                aor$variable)
    cat("\n  SDoH coefficients:\n")
    print(aor[sv, c("variable", "AOR", "CI_lower", "CI_upper", "p_value")])

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
all_results[["S1"]] <- run_sensitivity(df_s1, "S1_IP_only_cases", joint_rhs)


# =====================================================================
# S2: CLEAN CONTROLS (drop controls with acute-care utilization)
# =====================================================================
# Remove control ROWS (not strata) where control had any acute-care visit
ctrl_with_acute <- ctrl_ed$person_id[ctrl_ed$ctrl_had_any_acute_14d == 1]
cat("\n  Controls with acute-care visits to remove:", length(ctrl_with_acute), "\n")

df_s2 <- reg_sdoh[!(reg_sdoh$Treatment == 0 &
                     reg_sdoh$person_id %in% ctrl_with_acute), ]
all_results[["S2"]] <- run_sensitivity(df_s2, "S2_clean_controls", joint_rhs)


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
all_results[["S3"]] <- run_sensitivity(df_s3, "S3_pre_index_sdoh", joint_rhs)


# =====================================================================
# S4: NO VACCINATION COVARIATE
# =====================================================================
joint_rhs_no_vacc <- paste(base_rhs_no_vacc, "+", joint_sdoh)
all_results[["S4"]] <- run_sensitivity(reg_sdoh, "S4_no_vaccination",
                                        joint_rhs_no_vacc)


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
