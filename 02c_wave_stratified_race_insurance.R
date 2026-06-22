#!/usr/bin/env Rscript
# ─────────────────────────────────────────────────────────────────────
# 02c_wave_stratified_race_insurance.R
#
# Wave-stratified analysis of Black-race AOR and Medicaid AOR across
# pandemic phases (pre-Delta, Delta, Omicron).
#
# Motivation: The main analysis wave-stratifies income (Figure 5) but
# not race or insurance. Reviewers and co-authors want to know:
#   1. Did the Black-race disparity narrow across waves?
#   2. Did the Medicaid association change with vaccine/antiviral access?
#
# Design: For each wave, fits a separate conditional logistic regression
# within matched strata whose index dates fall in that wave. Uses the
# same base model as 02_models.R minus the wave covariate (since we're
# stratifying by wave). Three model sets per wave:
#   A. Base model only → Black race AOR
#   B. Base + insurance → Medicaid AOR + Black race AOR
#   C. Base + all 6 SDoH jointly → Black race AOR (within-wave attenuation)
#
# Usage: Rscript 02c_wave_stratified_race_insurance.R aou_v7
# Runs on AoU Researcher Workbench after 02_models.R.
#
# Output:
#   wave_stratified_race.csv          — Black AOR per wave (base + joint)
#   wave_stratified_insurance.csv     — Medicaid AOR per wave
#   wave_stratified_race_attenuation.csv — within-wave attenuation table
# ─────────────────────────────────────────────────────────────────────

library(survival)
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(readr))

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
  cat("Usage: Rscript 02c_wave_stratified_race_insurance.R aou_v7\n")
  quit(status = 1)
}
COHORT  <- args[1]
RESULTS <- file.path("results", COHORT)

cat(strrep("=", 70), "\n")
cat("WAVE-STRATIFIED RACE & INSURANCE  [", toupper(COHORT), "]\n")
cat(strrep("=", 70), "\n")

# ── Load data (same as 02_models.R) ─────────────────────────────────
reg_path  <- file.path(RESULTS, "08_regression_base.csv")
if (!file.exists(reg_path)) reg_path <- file.path(RESULTS, "07_regression_base.csv")
sdoh_path <- file.path(RESULTS, "04_sdoh.csv")

# Download from bucket if needed (AoU Workbench)
bucket <- Sys.getenv("WORKSPACE_BUCKET")
if (!file.exists(reg_path) && nchar(bucket) > 0) {
  bdir <- paste0(bucket, "/data/covid_sdoh/", COHORT, "/")
  for (f in c("08_regression_base.csv", "07_regression_base.csv")) {
    suppressWarnings(
      system(paste0("gsutil cp ", bdir, f, " ", RESULTS, "/"),
             intern = TRUE, ignore.stderr = TRUE))
    p <- file.path(RESULTS, f)
    if (file.exists(p)) { reg_path <- p; break }
  }
  system(paste0("gsutil cp ", bdir, "04_sdoh.csv ", RESULTS, "/"), intern = TRUE)
}

regression_bm <- read_csv(reg_path, show_col_types = FALSE)
sdoh_raw      <- read_csv(sdoh_path, show_col_types = FALSE)
cat("  Loaded:", nrow(regression_bm), "rows from", basename(reg_path), "\n")
cat("  Cases:", sum(regression_bm$Treatment == 1),
    "| Controls:", sum(regression_bm$Treatment == 0), "\n")


# ══════════════════════════════════════════════════════════════════════
# FACTOR SETUP — COPIED FROM 02_models.R (must match exactly)
# ══════════════════════════════════════════════════════════════════════
regression_bm$f.sex  <- factor(regression_bm$sex_at_birth,
                               levels = c("Male","Female","Other"))
regression_bm$f.age  <- factor(regression_bm$age_group,
                               levels = c("<45","45-54","55-64","65+"))
regression_bm$f.vacc <- factor(regression_bm$vaccination,
                               levels = c("Unknown","Vaccinated"))
regression_bm$f.race <- factor(regression_bm$race,
                               levels = c("White","Black","Asian","Other"))
regression_bm$f.ethnicity <- factor(regression_bm$ethnicity,
                               levels = c("Not Hispanic","Hispanic","Other"))
regression_bm$f.wave <- factor(regression_bm$pandemic_wave,
                               levels = c("pre_delta","delta","omicron"))

como <- c("Myocardial_Infarction","Congestive_Heart_Failure",
          "Peripheral_Vascular_Disease","Cerebrovascular_Disease","Dementia",
          "Chronic_Pulmonary_Disease","Rheumatic_Disease","Peptic_Ulcer_Disease",
          "Liver_Disease_Mild","Liver_Disease_Moderate_Severe",
          "Diabetes_without_Chronic_Complications",
          "Diabetes_with_Chronic_Complications",
          "Hemiplegia_Paraplegia","Renal_Disease_Mild_Moderate",
          "Renal_Disease_Severe","HIV","Metastatic_Solid_Tumor","Malignancy","AIDS")
for (c_col in como) regression_bm[[c_col]][is.na(regression_bm[[c_col]])] <- 0

# Base terms WITHOUT wave (since we stratify by wave)
base_no_wave <- c("f.sex", "f.age", "f.vacc", "f.race", "f.ethnicity", como)
base_no_wave_rhs <- paste(base_no_wave, collapse = " + ")

# Merge SDoH
reg_sdoh <- merge(regression_bm, sdoh_raw, by = "person_id", all.x = TRUE)

# SDoH factors (from 02_models.R joint model setup)
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
joint_rhs  <- paste(base_no_wave_rhs, "+", joint_sdoh)


# ══════════════════════════════════════════════════════════════════════
# HELPER: extract AOR with cluster-robust SEs
# ══════════════════════════════════════════════════════════════════════
extract_aor <- function(model, model_name, data) {
  s <- summary(model)$coefficients
  coef_vals <- s[,"coef"]
  se_vals   <- s[,"se(coef)"]
  p_vals    <- s[,"Pr(>|z|)"]

  tryCatch({
    V <- vcovCL(model, cluster = data$person_id)
    se_vals <- sqrt(diag(V))
    z_vals  <- coef_vals / se_vals
    p_vals  <- 2 * pnorm(-abs(z_vals))
  }, error = function(e) {
    cat("    vcovCL failed, using model SEs\n")
  })

  data.frame(
    variable = rownames(s),
    AOR      = exp(coef_vals),
    CI_lower = exp(coef_vals - 1.96 * se_vals),
    CI_upper = exp(coef_vals + 1.96 * se_vals),
    p_value  = p_vals,
    model    = model_name,
    stringsAsFactors = FALSE, row.names = NULL
  )
}


# ══════════════════════════════════════════════════════════════════════
# WAVE-STRATIFIED ANALYSES
# ══════════════════════════════════════════════════════════════════════

race_results     <- list()
insurance_results <- list()
attenuation_rows <- list()

for (w in c("pre_delta", "delta", "omicron")) {
  cat("\n", strrep("=", 60), "\n")
  cat("WAVE:", toupper(w), "\n")
  cat(strrep("=", 60), "\n")

  df_w <- reg_sdoh[reg_sdoh$pandemic_wave == w, ]
  n_cases_w <- sum(df_w$Treatment == 1)
  n_ctrls_w <- sum(df_w$Treatment == 0)
  cat(sprintf("  N = %d (cases = %d, controls = %d)\n",
              nrow(df_w), n_cases_w, n_ctrls_w))

  if (n_cases_w < 50) {
    cat("  SKIPPING: too few cases for stable estimates\n")
    next
  }

  # Drop strata without both case and control
  strata_ok <- df_w %>% group_by(stratum) %>%
    summarise(has_case = any(Treatment == 1),
              has_ctrl = any(Treatment == 0), .groups = "drop") %>%
    filter(has_case & has_ctrl) %>% pull(stratum)
  df_w <- df_w[df_w$stratum %in% strata_ok, ]
  cat(sprintf("  After stratum filter: %d obs, %d strata\n",
              nrow(df_w), length(strata_ok)))

  # ── Model A: Base only (race AOR without SDoH) ──────────────────
  cat("\n  [A] Base model (no SDoH)...\n")
  tryCatch({
    fit_a <- clogit(
      as.formula(paste("Treatment ~", base_no_wave_rhs, "+ strata(stratum)")),
      data = df_w)
    aor_a <- extract_aor(fit_a, paste0("base_", w), df_w)

    black_a <- aor_a[grepl("f\\.raceBlack", aor_a$variable), ]
    if (nrow(black_a) > 0) {
      black_a$wave <- w
      black_a$sdoh_adjusted <- "No"
      race_results[[length(race_results) + 1]] <- black_a
      attenuation_rows[[length(attenuation_rows) + 1]] <- data.frame(
        wave = w, model = "Base (no SDoH)",
        Black_AOR = black_a$AOR, CI_lower = black_a$CI_lower,
        CI_upper = black_a$CI_upper, p = black_a$p_value,
        stringsAsFactors = FALSE)
      cat(sprintf("    Black AOR: %.2f (%.2f-%.2f) p=%.3f\n",
                  black_a$AOR, black_a$CI_lower, black_a$CI_upper, black_a$p_value))
    }
  }, error = function(e) cat("    ERROR:", e$message, "\n"))

  # ── Model B: Base + insurance ───────────────────────────────────
  cat("  [B] Base + insurance...\n")
  tryCatch({
    fit_b <- clogit(
      as.formula(paste("Treatment ~", base_no_wave_rhs,
                       "+ f.insurance + strata(stratum)")),
      data = df_w)
    aor_b <- extract_aor(fit_b, paste0("insurance_", w), df_w)

    medicaid_b <- aor_b[grepl("f\\.insuranceMedicaid", aor_b$variable), ]
    if (nrow(medicaid_b) > 0) {
      medicaid_b$wave <- w
      insurance_results[[length(insurance_results) + 1]] <- medicaid_b
      cat(sprintf("    Medicaid AOR: %.2f (%.2f-%.2f) p=%.3f\n",
                  medicaid_b$AOR, medicaid_b$CI_lower,
                  medicaid_b$CI_upper, medicaid_b$p_value))
    }
  }, error = function(e) cat("    ERROR:", e$message, "\n"))

  # ── Model C: Base + all 6 SDoH jointly (race attenuation) ──────
  cat("  [C] Base + joint SDoH...\n")
  tryCatch({
    fit_c <- clogit(
      as.formula(paste("Treatment ~", joint_rhs, "+ strata(stratum)")),
      data = df_w)
    aor_c <- extract_aor(fit_c, paste0("joint_", w), df_w)

    black_c <- aor_c[grepl("f\\.raceBlack", aor_c$variable), ]
    if (nrow(black_c) > 0) {
      black_c$wave <- w
      black_c$sdoh_adjusted <- "Yes"
      race_results[[length(race_results) + 1]] <- black_c
      attenuation_rows[[length(attenuation_rows) + 1]] <- data.frame(
        wave = w, model = "Joint SDoH",
        Black_AOR = black_c$AOR, CI_lower = black_c$CI_lower,
        CI_upper = black_c$CI_upper, p = black_c$p_value,
        stringsAsFactors = FALSE)
      cat(sprintf("    Black AOR (SDoH-adj): %.2f (%.2f-%.2f) p=%.3f\n",
                  black_c$AOR, black_c$CI_lower, black_c$CI_upper, black_c$p_value))
    }

    # Also extract Medicaid from joint model
    med_c <- aor_c[grepl("f\\.insuranceMedicaid", aor_c$variable), ]
    if (nrow(med_c) > 0) {
      cat(sprintf("    Medicaid AOR (joint): %.2f (%.2f-%.2f) p=%.3f\n",
                  med_c$AOR, med_c$CI_lower, med_c$CI_upper, med_c$p_value))
    }

    # Save full wave-specific joint model coefficients
    write_csv(aor_c, file.path(RESULTS,
      paste0("wave_joint_sdoh_", w, "_coefficients.csv")))

  }, error = function(e) cat("    ERROR:", e$message, "\n"))
}


# ══════════════════════════════════════════════════════════════════════
# SAVE RESULTS
# ══════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 70), "\n")
cat("SAVING RESULTS\n")
cat(strrep("=", 70), "\n")

# 1. Wave-stratified race
if (length(race_results) > 0) {
  race_df <- do.call(rbind, race_results)
  write_csv(race_df, file.path(RESULTS, "wave_stratified_race.csv"))
  cat("\n  Wave-stratified Black race AOR:\n")
  print(race_df[, c("wave", "sdoh_adjusted", "AOR", "CI_lower", "CI_upper", "p_value")])
}

# 2. Wave-stratified insurance
if (length(insurance_results) > 0) {
  ins_df <- do.call(rbind, insurance_results)
  write_csv(ins_df, file.path(RESULTS, "wave_stratified_insurance.csv"))
  cat("\n  Wave-stratified Medicaid AOR:\n")
  print(ins_df[, c("wave", "AOR", "CI_lower", "CI_upper", "p_value")])
}

# 3. Within-wave attenuation table
if (length(attenuation_rows) > 0) {
  att_df <- do.call(rbind, attenuation_rows)

  # Compute % attenuation within each wave
  att_df$pct_attenuation <- NA
  for (w in unique(att_df$wave)) {
    base_row  <- att_df[att_df$wave == w & att_df$model == "Base (no SDoH)", ]
    joint_row <- att_df[att_df$wave == w & att_df$model == "Joint SDoH", ]
    if (nrow(base_row) == 1 && nrow(joint_row) == 1) {
      base_log  <- log(base_row$Black_AOR)
      joint_log <- log(joint_row$Black_AOR)
      pct <- (1 - joint_log / base_log) * 100
      att_df$pct_attenuation[att_df$wave == w &
                              att_df$model == "Joint SDoH"] <- round(pct, 1)
    }
  }

  write_csv(att_df, file.path(RESULTS, "wave_stratified_race_attenuation.csv"))
  cat("\n  Within-wave race attenuation:\n")
  print(att_df[, c("wave", "model", "Black_AOR", "CI_lower", "CI_upper",
                    "pct_attenuation")])
}


# ── Upload to bucket ─────────────────────────────────────────────────
if (nchar(bucket) > 0) {
  bdir <- paste0(bucket, "/data/covid_sdoh/", COHORT, "/")
  system(paste0("gsutil -m cp ", RESULTS, "/wave_stratified_race*.csv ", bdir),
         intern = TRUE)
  system(paste0("gsutil -m cp ", RESULTS, "/wave_stratified_insurance.csv ", bdir),
         intern = TRUE)
  system(paste0("gsutil -m cp ", RESULTS, "/wave_joint_sdoh_*_coefficients.csv ", bdir),
         intern = TRUE)
  cat("  Uploaded to bucket.\n")
}


# ══════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 70), "\n")
cat("WAVE-STRATIFIED RACE & INSURANCE COMPLETE\n")
cat(strrep("=", 70), "\n")
cat("  Outputs:\n")
cat("    wave_stratified_race.csv               — Black AOR per wave\n")
cat("    wave_stratified_insurance.csv           — Medicaid AOR per wave\n")
cat("    wave_stratified_race_attenuation.csv    — within-wave attenuation\n")
cat("    wave_joint_sdoh_{wave}_coefficients.csv — full joint model per wave\n")
cat("\n  Usage: Rscript 02c_wave_stratified_race_insurance.R", COHORT, "\n")
cat("\n--- Session Info ---\n")
cat("R:", R.version$version.string, "\n")
for (p in c("survival", "sandwich", "lmtest"))
  cat(p, ":", as.character(packageVersion(p)), "\n")
cat("\nDone.\n")
