#!/usr/bin/env Rscript
# ─────────────────────────────────────────────────────────────────────
# COVID-19 Severity × SDoH — Conditional Logistic Regression
#
# Features:
#   P0.2  Cluster-robust SEs via sandwich::vcovCL (Austin 2020)
#   P0.3  Joint SDoH Model C (all 6 domains simultaneously)
#   P0.3  Race attenuation table (Black AOR across 9 specifications)
#   P0.4  Predicted probability contrast (replaces AOR multiplication)
#   P0.6  AIDS sensitivity analyses
#   P1.1  Pandemic wave as base-model covariate + stratified sensitivity
#   NEW   Insurance as hierarchical categorical (Employer = reference)
#
# Usage: Rscript 03_models.R aou_v7
# License: MIT
# ─────────────────────────────────────────────────────────────────────

library(survival)
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(readr))

# ──
if (!requireNamespace("sandwich", quietly = TRUE)) install.packages("sandwich")
if (!requireNamespace("lmtest", quietly = TRUE))   install.packages("lmtest")
library(sandwich)
library(lmtest)

# ── Parse argument ───────────────────────────────────────────────────
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1 || !args[1] %in% c("aou_v7", "aou_v8", "ms")) {
  cat("Usage: Rscript 02_models.R [aou_v7|aou_v8|ms]\n")
  quit(status = 1)
}
COHORT <- args[1]
IS_AOU <- startsWith(COHORT, "aou")
IS_MS  <- COHORT == "ms"
RESULTS <- file.path("results", COHORT)

cat(strrep("=", 70), "\n")
cat("COVID-19 SEVERITY × SDoH — MODELS  [", toupper(COHORT), "]  \n")
cat(strrep("=", 70), "\n")
cat("  Input/Output:", RESULTS, "\n")

# ── Load data ────────────────────────────────────────────────────────
reg_path  <- file.path(RESULTS, "08_regression_base.csv")
sdoh_path <- file.path(RESULTS, "04_sdoh.csv")

if (!file.exists(reg_path)) {
  bucket <- Sys.getenv("WORKSPACE_BUCKET")
  if (nchar(bucket) > 0) {
    cat("  Downloading from bucket...\n")
    system(paste0("gsutil cp ", bucket, "/data/covid_sdoh/", COHORT,
                  "/08_regression_base.csv ", RESULTS, "/"), intern = TRUE)
    system(paste0("gsutil cp ", bucket, "/data/covid_sdoh/", COHORT,
                  "/04_sdoh.csv ", RESULTS, "/"), intern = TRUE)
  }
}

regression_bm <- read_csv(reg_path, show_col_types = FALSE)
cat("  Regression data:", nrow(regression_bm), "rows,", ncol(regression_bm), "cols\n")
cat("  Cases:", sum(regression_bm$Treatment == 1),
    " Controls:", sum(regression_bm$Treatment == 0), "\n")

# ── Detect available columns ─────────────────────────────────────────
has_race      <- "race" %in% names(regression_bm) &&
                 any(regression_bm$race != "Unknown", na.rm = TRUE)
has_ethnicity <- "ethnicity" %in% names(regression_bm) &&
                 any(regression_bm$ethnicity != "Unknown", na.rm = TRUE)
has_plantype  <- "plan_type" %in% names(regression_bm)
has_region    <- "region_name" %in% names(regression_bm)
has_sdoh      <- file.exists(sdoh_path)
has_wave      <- "pandemic_wave" %in% names(regression_bm)

cat("  Features: race=", has_race, " ethnicity=", has_ethnicity,
    " plan_type=", has_plantype, " region=", has_region,
    " sdoh=", has_sdoh, " wave=", has_wave, "\n")

# ── Factor encoding ─────────────────────────────────────────────────
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
if (has_plantype)  regression_bm$f.plan <- factor(regression_bm$plan_type,
                     levels = c("PPO","HMO","POS","HDHP","CDHP","EPO",
                                "Comprehensive","Basic","Unknown"))
if (has_region)    regression_bm$f.region <- factor(regression_bm$region_name,
                     levels = c("South","NorthCentral","West","Northeast","Unknown"))
# ──
if (has_wave)      regression_bm$f.wave <- factor(regression_bm$pandemic_wave,
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

# ──
base_terms <- c("f.sex", "f.age", "f.vacc")
if (has_race)      base_terms <- c(base_terms, "f.race")
if (has_ethnicity) base_terms <- c(base_terms, "f.ethnicity")
if (has_wave)      base_terms <- c(base_terms, "f.wave")
if (has_plantype)  base_terms <- c(base_terms, "f.plan")
if (has_region)    base_terms <- c(base_terms, "f.region")
base_terms <- c(base_terms, como)

base_rhs <- paste(base_terms, collapse = " + ")
cat("\n  Base formula RHS:", length(base_terms), "terms\n")


# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

# ── extract_aor: cluster-robust SEs by default ──────────────────────
extract_aor <- function(model, model_name, data = NULL, robust = TRUE) {
  s <- summary(model)$coefficients
  coef_vals <- s[,"coef"]
  se_vals   <- s[,"se(coef)"]
  p_vals    <- s[,"Pr(>|z|)"]

  if (robust && !is.null(data) && "person_id" %in% names(data)) {
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

extract_black_aor <- function(model, model_name, data = NULL) {
  aor <- extract_aor(model, model_name, data)
  aor[grepl("f\\.raceBlack", aor$variable), , drop = FALSE]
}


# ══════════════════════════════════════════════════════════════════════
# BASE MODEL (Model A — now includes wave)
# ══════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 60), "\nBASE MODEL (Model A)\n", strrep("=", 60), "\n")

base_fit <- clogit(as.formula(paste("Treatment ~", base_rhs, "+ strata(stratum)")),
                   data = regression_bm)
print(summary(base_fit))

base_aor <- extract_aor(base_fit, "base", regression_bm)
write_csv(base_aor, file.path(RESULTS, "base_model_coefficients.csv"))
save(base_fit, file = file.path(RESULTS, "base_clogit.RData"))

results_all <- list(base_aor)

# ── Race attenuation tracking ────────────────────────────────────────
race_attenuation <- list()
if (has_race) {
  b <- extract_black_aor(base_fit, "A_base_no_sdoh", regression_bm)
  if (nrow(b) > 0) race_attenuation[[1]] <- b
}


# ══════════════════════════════════════════════════════════════════════
# SDoH MODELS (AoU only)
# ══════════════════════════════════════════════════════════════════════
if (IS_AOU && has_sdoh) {
  cat("\n", strrep("=", 60), "\nSDoH MODELS (AoU)\n", strrep("=", 60), "\n")

  sdoh_raw <- read_csv(sdoh_path, show_col_types = FALSE)
  cat("  SDoH data:", nrow(sdoh_raw), "rows,", ncol(sdoh_raw), "cols\n")

  if (ncol(sdoh_raw) > 1) {
    reg_sdoh <- merge(regression_bm, sdoh_raw, by = "person_id", all.x = TRUE)

    # Helper for domain-by-domain models
    run_sdoh_model <- function(df, var_name, levels, model_name) {
      cat("\n--- ", model_name, " ---\n")
      df[[var_name]][is.na(df[[var_name]])] <- "Missing"
      fvar <- paste0("f.", var_name)
      df[[fvar]] <- factor(df[[var_name]], levels = levels)
      frm <- as.formula(paste0("Treatment ~ ", base_rhs, " + ", fvar,
                               " + strata(stratum)"))
      tryCatch({
        fit <- clogit(frm, data = df)
        aor <- extract_aor(fit, model_name, df)
        sdoh_rows <- grepl(fvar, aor$variable, fixed = TRUE)
        cat("  "); print(aor[sdoh_rows, c("variable","AOR","CI_lower","CI_upper","p_value")])
        save(fit, file = file.path(RESULTS, paste0(model_name, "_clogit.RData")))
        write_csv(aor, file.path(RESULTS, paste0(model_name, "_coefficients.csv")))

        if (has_race) {
          b <- extract_black_aor(fit, paste0("B_", model_name), df)
          if (nrow(b) > 0) race_attenuation[[length(race_attenuation)+1]] <<- b
        }
        return(aor)
      }, error = function(e) { cat("  ERROR:", e$message, "\n"); return(NULL) })
    }


    # ──
    # Reference: Employer (most advantaged, most common)
    cat("\n--- insurance (hierarchical categorical) ---\n")
    reg_sdoh$insurance_type[is.na(reg_sdoh$insurance_type)] <- "Missing"
    reg_sdoh$f.insurance <- factor(reg_sdoh$insurance_type,
      levels = c("Employer","Medicare","Medicaid","Other_None","Missing"))

    tryCatch({
      ins_fit <- clogit(as.formula(paste("Treatment ~", base_rhs,
        "+ f.insurance + strata(stratum)")), data = reg_sdoh)
      ins_aor <- extract_aor(ins_fit, "insurance", reg_sdoh)
      cat("  "); print(ins_aor[grepl("f\\.insurance", ins_aor$variable),
        c("variable","AOR","CI_lower","CI_upper","p_value")])
      save(ins_fit, file = file.path(RESULTS, "insurance_clogit.RData"))
      write_csv(ins_aor, file.path(RESULTS, "insurance_coefficients.csv"))
      results_all[[length(results_all)+1]] <- ins_aor

      if (has_race) {
        b <- extract_black_aor(ins_fit, "B_insurance", reg_sdoh)
        if (nrow(b) > 0) race_attenuation[[length(race_attenuation)+1]] <- b
      }
    }, error = function(e) { cat("  Insurance ERROR:", e$message, "\n") })


    # ── Disability (lumped) ──────────────────────────────────────────
    results_all[[length(results_all)+1]] <- run_sdoh_model(
      reg_sdoh, "disability_any", c("No","Yes","Missing"), "disability_lumped")

    # ── Individual disabilities ──────────────────────────────────────
    for (d in c("disability_hearing","disability_vision","disability_cognition",
                "disability_mobility","disability_selfcare","disability_independent")) {
      results_all[[length(results_all)+1]] <- run_sdoh_model(
        reg_sdoh, d, c("No","Yes","Missing"), d)
    }

    # ── Employment ───────────────────────────────────────────────────
    results_all[[length(results_all)+1]] <- run_sdoh_model(
      reg_sdoh, "employment",
      c("Employed","Student","Unemployed","Others","Missing"), "employment")

    # ── Income ───────────────────────────────────────────────────────
    results_all[[length(results_all)+1]] <- run_sdoh_model(
      reg_sdoh, "income",
      c("35k_100k","less_10k","10k_25k","25k_35k","100k_150k",
        "150k_200k","more_200k","Missing"), "income")

    # ── Housing ──────────────────────────────────────────────────────
    results_all[[length(results_all)+1]] <- run_sdoh_model(
      reg_sdoh, "housing", c("Own","Rent","Others","Missing"), "housing")

    # ── Housing stability ────────────────────────────────────────────
    results_all[[length(results_all)+1]] <- run_sdoh_model(
      reg_sdoh, "housing_stability",
      c("Stable","Unstable","Missing"), "housing_stability")

    # ── Education ────────────────────────────────────────────────────
    results_all[[length(results_all)+1]] <- run_sdoh_model(
      reg_sdoh, "education",
      c("Advanced","Never_Attended","Below_GED","GED_or_College","Missing"),
      "education")


    # ══════════════════════════════════════════════════════════════════
    # JOINT SDoH MODEL C (P0.3)
    # ══════════════════════════════════════════════════════════════════
    cat("\n", strrep("=", 60), "\nJOINT SDoH MODEL C\n", strrep("=", 60), "\n")

    df_j <- reg_sdoh

    # Ensure all factors are set
    df_j$f.income <- factor(
      ifelse(is.na(df_j$income), "Missing", df_j$income),
      levels = c("35k_100k","less_10k","10k_25k","25k_35k",
                 "100k_150k","150k_200k","more_200k","Missing"))

    df_j$f.insurance <- factor(
      ifelse(is.na(df_j$insurance_type), "Missing", df_j$insurance_type),
      levels = c("Employer","Medicare","Medicaid","Other_None","Missing"))

    df_j$f.education <- factor(
      ifelse(is.na(df_j$education), "Missing", df_j$education),
      levels = c("Advanced","Never_Attended","Below_GED","GED_or_College","Missing"))

    df_j$f.employment <- factor(
      ifelse(is.na(df_j$employment), "Missing", df_j$employment),
      levels = c("Employed","Student","Unemployed","Others","Missing"))

    df_j$f.housing <- factor(
      ifelse(is.na(df_j$housing), "Missing", df_j$housing),
      levels = c("Own","Rent","Others","Missing"))

    df_j$f.housing_stability <- factor(
      ifelse(is.na(df_j$housing_stability), "Missing", df_j$housing_stability),
      levels = c("Stable","Unstable","Missing"))

    df_j$f.disability_any <- factor(
      ifelse(is.na(df_j$disability_any), "Missing", df_j$disability_any),
      levels = c("No","Yes","Missing"))

    joint_sdoh <- "f.income + f.insurance + f.education + f.employment + f.housing + f.housing_stability + f.disability_any"
    joint_rhs <- paste(base_rhs, "+", joint_sdoh)

    tryCatch({
      joint_fit <- clogit(
        as.formula(paste("Treatment ~", joint_rhs, "+ strata(stratum)")),
        data = df_j)
      cat("\n  Joint Model C summary:\n")
      print(summary(joint_fit))

      joint_aor <- extract_aor(joint_fit, "joint_sdoh", df_j)
      write_csv(joint_aor, file.path(RESULTS, "joint_sdoh_coefficients.csv"))
      save(joint_fit, file = file.path(RESULTS, "joint_sdoh_clogit.RData"))
      results_all[[length(results_all)+1]] <- joint_aor

      # Print SDoH from joint model
      sv <- grepl("f\\.income|f\\.insurance|f\\.education|f\\.employment|f\\.housing|f\\.disability",
                  joint_aor$variable)
      cat("\n  Joint Model C — SDoH coefficients:\n")
      print(joint_aor[sv, c("variable","AOR","CI_lower","CI_upper","p_value")])

      if (has_race) {
        b <- extract_black_aor(joint_fit, "C_joint_all_sdoh", df_j)
        if (nrow(b) > 0) race_attenuation[[length(race_attenuation)+1]] <- b
      }


      # ── Predicted probability contrast (P0.4) ─────────────────────
      cat("\n", strrep("=", 60),
          "\nPREDICTED PROBABILITY CONTRAST\n", strrep("=", 60), "\n")

      template <- df_j
      # Profile A: employer, $35-100K, own
      pa <- template
      pa$f.insurance <- factor("Employer", levels = levels(df_j$f.insurance))
      pa$f.income    <- factor("35k_100k", levels = levels(df_j$f.income))
      pa$f.housing   <- factor("Own", levels = levels(df_j$f.housing))

      # Profile B: Medicaid, <$25K, rent
      pb <- template
      pb$f.insurance <- factor("Medicaid", levels = levels(df_j$f.insurance))
      pb$f.income    <- factor("10k_25k", levels = levels(df_j$f.income))
      pb$f.housing   <- factor("Rent", levels = levels(df_j$f.housing))

      lp_a <- predict(joint_fit, newdata = pa, type = "lp")
      lp_b <- predict(joint_fit, newdata = pb, type = "lp")

      prob_a <- mean(1 / (1 + exp(-lp_a)), na.rm = TRUE)
      prob_b <- mean(1 / (1 + exp(-lp_b)), na.rm = TRUE)
      ratio  <- prob_b / prob_a

      cat(sprintf("\n  Profile A (employer, $35-100K, own):  %.3f%%\n", prob_a*100))
      cat(sprintf("  Profile B (Medicaid, <$25K, rent):    %.3f%%\n", prob_b*100))
      cat(sprintf("  Ratio B/A: %.2f\n", ratio))

      write_csv(
        data.frame(profile = c("A_employer_midIncome_own",
                                "B_medicaid_lowIncome_rent"),
                   predicted_prob = c(prob_a, prob_b),
                   ratio = c(NA, ratio)),
        file.path(RESULTS, "predicted_probability_contrast.csv"))

    }, error = function(e) {
      cat("  Joint Model C ERROR:", e$message, "\n")
    })


    # ══════════════════════════════════════════════════════════════════
    # RACE ATTENUATION TABLE (P0.3)
    # ══════════════════════════════════════════════════════════════════
    if (has_race && length(race_attenuation) > 0) {
      cat("\n", strrep("=", 60), "\nRACE ATTENUATION TABLE\n",
          strrep("=", 60), "\n")

      race_att <- do.call(rbind, race_attenuation)
      rownames(race_att) <- NULL

      base_log <- log(race_att$AOR[race_att$model == "A_base_no_sdoh"])
      if (length(base_log) == 1) {
        race_att$pct_attenuation <- round(
          (1 - log(race_att$AOR) / base_log) * 100, 1)
        race_att$pct_attenuation[race_att$model == "A_base_no_sdoh"] <- NA
      }

      cat("\n  Black race AOR across specifications:\n")
      print(race_att[, c("model","AOR","CI_lower","CI_upper","pct_attenuation")])
      write_csv(race_att, file.path(RESULTS, "race_attenuation_table.csv"))
    }


    # ══════════════════════════════════════════════════════════════════
    # AIDS SENSITIVITY (P0.6)
    # ══════════════════════════════════════════════════════════════════
    cat("\n", strrep("=", 60), "\nAIDS SENSITIVITY\n", strrep("=", 60), "\n")

    aids_sens <- list()

    # Current two-step
    ab <- base_aor[grepl("^AIDS$", base_aor$variable), ]
    if (nrow(ab) > 0) { ab$phenotype <- "Two-step (HIV+OI)"; aids_sens[[1]] <- ab }

    # HIV alone (AIDS excluded from Charlson)
    como_no_aids <- setdiff(como, "AIDS")
    no_aids_rhs <- paste(c("f.sex","f.age","f.vacc",
      if (has_race) "f.race", if (has_ethnicity) "f.ethnicity",
      if (has_wave) "f.wave", como_no_aids), collapse = " + ")

    tryCatch({
      naf <- clogit(as.formula(paste("Treatment ~", no_aids_rhs,
                                     "+ strata(stratum)")),
                    data = regression_bm)
      naa <- extract_aor(naf, "base_no_aids", regression_bm)
      hr <- naa[grepl("^HIV$", naa$variable), ]
      if (nrow(hr) > 0) { hr$phenotype <- "HIV alone"; aids_sens[[length(aids_sens)+1]] <- hr }
      write_csv(naa, file.path(RESULTS, "base_no_aids_coefficients.csv"))
    }, error = function(e) { cat("  ERROR:", e$message, "\n") })

    # Both excluded
    como_no_both <- setdiff(como, c("AIDS","HIV"))
    no_both_rhs <- paste(c("f.sex","f.age","f.vacc",
      if (has_race) "f.race", if (has_ethnicity) "f.ethnicity",
      if (has_wave) "f.wave", como_no_both), collapse = " + ")

    tryCatch({
      nbf <- clogit(as.formula(paste("Treatment ~", no_both_rhs,
                                     "+ strata(stratum)")),
                    data = regression_bm)
      nba <- extract_aor(nbf, "base_no_hiv_aids", regression_bm)
      write_csv(nba, file.path(RESULTS, "base_no_hiv_aids_coefficients.csv"))
    }, error = function(e) { cat("  ERROR:", e$message, "\n") })

    if (length(aids_sens) > 0) {
      as_df <- do.call(rbind, aids_sens)
      write_csv(as_df, file.path(RESULTS, "aids_sensitivity.csv"))
      cat("  "); print(as_df[, c("phenotype","variable","AOR","CI_lower","CI_upper")])
    }


    # ══════════════════════════════════════════════════════════════════
    # WAVE-STRATIFIED SENSITIVITY (P1.1 supplement)
    # Income model within each pandemic wave
    # ══════════════════════════════════════════════════════════════════
    if (has_wave) {
      cat("\n", strrep("=", 60),
          "\nWAVE-STRATIFIED SENSITIVITY (income model)\n",
          strrep("=", 60), "\n")

      # Base terms WITHOUT wave (since we're stratifying by it)
      base_no_wave <- setdiff(base_terms, "f.wave")
      base_no_wave_rhs <- paste(base_no_wave, collapse = " + ")

      wave_strat_results <- list()
      for (w in c("pre_delta","delta","omicron")) {
        cat("\n  --- Wave:", w, " ---\n")
        df_w <- reg_sdoh[reg_sdoh$pandemic_wave == w, ]
        n_cases_w <- sum(df_w$Treatment == 1)
        n_ctrls_w <- sum(df_w$Treatment == 0)
        cat(sprintf("    N=%d (cases=%d, controls=%d)\n",
                    nrow(df_w), n_cases_w, n_ctrls_w))

        if (n_cases_w < 50) {
          cat("    Skipping: too few cases for stable estimates\n")
          next
        }

        df_w$income[is.na(df_w$income)] <- "Missing"
        df_w$f.income <- factor(df_w$income,
          levels = c("35k_100k","less_10k","10k_25k","25k_35k",
                     "100k_150k","150k_200k","more_200k","Missing"))

        tryCatch({
          wf <- clogit(as.formula(paste("Treatment ~", base_no_wave_rhs,
                                        "+ f.income + strata(stratum)")),
                       data = df_w)
          wa <- extract_aor(wf, paste0("income_wave_", w), df_w)
          inc_rows <- wa[grepl("f\\.income", wa$variable), ]
          inc_rows$wave <- w
          cat("  "); print(inc_rows[, c("variable","AOR","CI_lower","CI_upper","p_value")])
          wave_strat_results[[length(wave_strat_results)+1]] <- inc_rows
        }, error = function(e) {
          cat("    ERROR:", e$message, "\n")
        })
      }

      if (length(wave_strat_results) > 0) {
        ws <- do.call(rbind, wave_strat_results)
        write_csv(ws, file.path(RESULTS, "wave_stratified_income.csv"))
        cat("\n  Saved: wave_stratified_income.csv\n")
      }
    }

  } else {
    cat("  SDoH file has only person_id — skipping.\n")
  }

} else if (IS_MS) {
  cat("\n  [MarketScan] No SDoH surveys — plan_type/region in base.\n")
}


# ══════════════════════════════════════════════════════════════════════
# COMBINE ALL RESULTS
# ══════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 60), "\nCOMBINING\n", strrep("=", 60), "\n")

results_all <- Filter(Negate(is.null), results_all)
all_coefs <- do.call(rbind, results_all)
rownames(all_coefs) <- NULL
write_csv(all_coefs, file.path(RESULTS, "all_model_coefficients.csv"))
cat("  Combined:", nrow(all_coefs), "rows from", length(results_all), "models\n")

if (IS_AOU) {
  bucket <- Sys.getenv("WORKSPACE_BUCKET")
  if (nchar(bucket) > 0) {
    system(paste0("gsutil -m cp ", RESULTS, "/*.csv ",
                  bucket, "/data/covid_sdoh/", COHORT, "/"), intern = TRUE)
    system(paste0("gsutil -m cp ", RESULTS, "/*.RData ",
                  bucket, "/data/covid_sdoh/", COHORT, "/"), intern = TRUE)
    cat("  Uploaded to", bucket, "\n")
  }
}


# ══════════════════════════════════════════════════════════════════════
# HEADLINE RESULTS
# ══════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 60), "\nHEADLINE RESULTS [", toupper(COHORT), "]\n",
    strrep("=", 60), "\n")

sig_base <- base_aor[base_aor$p_value < 0.05, ]
sig_base <- sig_base[order(sig_base$AOR, decreasing = TRUE), ]
cat("\n  Significant base model (p<0.05):\n")
for (i in seq_len(min(nrow(sig_base), 15))) {
  r <- sig_base[i, ]
  cat(sprintf("    %-45s AOR %.2f (%.2f-%.2f)  p=%.2e\n",
    r$variable, r$AOR, r$CI_lower, r$CI_upper, r$p_value))
}

if (IS_AOU) {
  sdoh_c <- all_coefs[all_coefs$model != "base" & all_coefs$p_value < 0.05, ]
  sdoh_c <- sdoh_c[grepl("^f\\.", sdoh_c$variable), ]
  sdoh_c <- sdoh_c[order(sdoh_c$AOR, decreasing = TRUE), ]
  if (nrow(sdoh_c) > 0) {
    cat("\n  Significant SDoH (p<0.05):\n")
    for (i in seq_len(min(nrow(sdoh_c), 15))) {
      r <- sdoh_c[i, ]
      cat(sprintf("    %-45s AOR %.2f (%.2f-%.2f)  p=%.2e  [%s]\n",
        r$variable, r$AOR, r$CI_lower, r$CI_upper, r$p_value, r$model))
    }
  }
}

cat("\n--- Session Info ---\n")
cat("R:", R.version$version.string, "\n")
for (p in c("survival","dplyr","readr","sandwich","lmtest"))
  cat(p, ":", as.character(packageVersion(p)), "\n")
cat("\nDone.\n")
