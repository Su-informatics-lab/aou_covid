#!/usr/bin/env Rscript
# ─────────────────────────────────────────────────────────────────────
# COVID-19 Severity × SDoH — Conditional Logistic Regression
# SHARED across AoU (v7/v8) and MarketScan
#
# Usage: Rscript 02_models.R aou_v7    # reads/writes results/aou_v7/
#        Rscript 02_models.R aou_v8    # reads/writes results/aou_v8/
#        Rscript 02_models.R ms        # reads/writes results/ms/
#
# AoU:  base model (sex + race + ethnicity + age + vacc + Charlson)
#       + 13 SDoH models (insurance, disability×7, employment, income,
#         housing, housing_stability, education)
# MS:   base model (sex + age + vacc + Charlson + plan_type + region)
#       no race/ethnicity, no SDoH surveys
#
# License: MIT
# ─────────────────────────────────────────────────────────────────────

library(survival)
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(readr))

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
cat("COVID-19 SEVERITY × SDoH — MODELS  [", toupper(COHORT), "]\n")
cat(strrep("=", 70), "\n")
cat("  Input/Output:", RESULTS, "\n")

# ── Load data ────────────────────────────────────────────────────────
reg_path  <- file.path(RESULTS, "07_regression_base.csv")
sdoh_path <- file.path(RESULTS, "04_sdoh.csv")

if (!file.exists(reg_path)) {
  # AoU: try gsutil download
  bucket <- Sys.getenv("WORKSPACE_BUCKET")
  if (nchar(bucket) > 0) {
    cat("  Downloading from bucket...\n")
    system(paste0("gsutil cp ", bucket, "/data/covid_sdoh/", COHORT, "/07_regression_base.csv ", RESULTS, "/"), intern = TRUE)
    system(paste0("gsutil cp ", bucket, "/data/covid_sdoh/", COHORT, "/04_sdoh.csv ", RESULTS, "/"), intern = TRUE)
  }
}

regression_bm <- read_csv(reg_path, show_col_types = FALSE)
cat("  Regression data:", nrow(regression_bm), "rows,", ncol(regression_bm), "cols\n")
cat("  Cases:", sum(regression_bm$Treatment == 1), " Controls:", sum(regression_bm$Treatment == 0), "\n")

# ── Detect available columns ─────────────────────────────────────────
has_race      <- "race" %in% names(regression_bm) && any(regression_bm$race != "Unknown", na.rm=TRUE)
has_ethnicity <- "ethnicity" %in% names(regression_bm) && any(regression_bm$ethnicity != "Unknown", na.rm=TRUE)
has_plantype  <- "plan_type" %in% names(regression_bm)
has_region    <- "region_name" %in% names(regression_bm)
has_sdoh      <- file.exists(sdoh_path)

cat("  Features: race=", has_race, " ethnicity=", has_ethnicity,
    " plan_type=", has_plantype, " region=", has_region,
    " sdoh_file=", has_sdoh, "\n")

# ── Factor encoding ─────────────────────────────────────────────────
regression_bm$f.sex  <- factor(regression_bm$sex_at_birth, levels = c("Male","Female","Other"))
regression_bm$f.age  <- factor(regression_bm$age_group, levels = c("<45","45-54","55-64","65+"))
regression_bm$f.vacc <- factor(regression_bm$vaccination, levels = c("Unknown","Vaccinated"))

if (has_race)      regression_bm$f.race      <- factor(regression_bm$race, levels = c("White","Black","Asian","Other"))
if (has_ethnicity) regression_bm$f.ethnicity <- factor(regression_bm$ethnicity, levels = c("Not Hispanic","Hispanic","Other"))
if (has_plantype)  regression_bm$f.plan      <- factor(regression_bm$plan_type,
                     levels = c("PPO","HMO","POS","HDHP","CDHP","EPO","Comprehensive","Basic","Unknown"))
if (has_region)    regression_bm$f.region    <- factor(regression_bm$region_name,
                     levels = c("South","NorthCentral","West","Northeast","Unknown"))

como <- c("Myocardial_Infarction","Congestive_Heart_Failure","Peripheral_Vascular_Disease",
          "Cerebrovascular_Disease","Dementia","Chronic_Pulmonary_Disease","Rheumatic_Disease",
          "Peptic_Ulcer_Disease","Liver_Disease_Mild","Liver_Disease_Moderate_Severe",
          "Diabetes_without_Chronic_Complications","Diabetes_with_Chronic_Complications",
          "Hemiplegia_Paraplegia","Renal_Disease_Mild_Moderate","Renal_Disease_Severe",
          "HIV","Metastatic_Solid_Tumor","Malignancy","AIDS")
for (c_col in como) regression_bm[[c_col]][is.na(regression_bm[[c_col]])] <- 0

# ── Build base formula (site-adaptive) ───────────────────────────────
base_terms <- c("f.sex", "f.age", "f.vacc")
if (has_race)      base_terms <- c(base_terms, "f.race")
if (has_ethnicity) base_terms <- c(base_terms, "f.ethnicity")
if (has_plantype)  base_terms <- c(base_terms, "f.plan")
if (has_region)    base_terms <- c(base_terms, "f.region")
base_terms <- c(base_terms, como)

base_rhs <- paste(base_terms, collapse = " + ")
cat("\n  Base formula RHS:", length(base_terms), "terms\n")

# ── Helper: extract AOR table from clogit ────────────────────────────
extract_aor <- function(model, model_name) {
  s <- summary(model)$coefficients
  data.frame(
    variable  = rownames(s),
    AOR       = exp(s[,"coef"]),
    CI_lower  = exp(s[,"coef"] - 1.96 * s[,"se(coef)"]),
    CI_upper  = exp(s[,"coef"] + 1.96 * s[,"se(coef)"]),
    p_value   = s[,"Pr(>|z|)"],
    model     = model_name,
    cohort    = COHORT,
    stringsAsFactors = FALSE, row.names = NULL
  )
}

# ═════════════════════════════════════════════════════════════════════
# BASE MODEL
# ═════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 60), "\nBASE MODEL\n", strrep("=", 60), "\n")

base_fit <- clogit(as.formula(paste("Treatment ~", base_rhs, "+ strata(stratum)")),
                   data = regression_bm)
print(summary(base_fit))

base_aor <- extract_aor(base_fit, "base")
write_csv(base_aor, file.path(RESULTS, "base_model_coefficients.csv"))
save(base_fit, file = file.path(RESULTS, "base_clogit.RData"))

results_all <- list(base_aor)

# ═════════════════════════════════════════════════════════════════════
# SDoH MODELS (AoU only)
# ═════════════════════════════════════════════════════════════════════
if (IS_AOU && has_sdoh) {
  cat("\n", strrep("=", 60), "\nSDoH MODELS (AoU)\n", strrep("=", 60), "\n")

  sdoh_raw <- read_csv(sdoh_path, show_col_types = FALSE)
  cat("  SDoH data:", nrow(sdoh_raw), "rows,", ncol(sdoh_raw), "cols\n")

  # Only proceed if SDoH has content beyond person_id
  if (ncol(sdoh_raw) > 1) {
    reg_sdoh <- merge(regression_bm, sdoh_raw, by = "person_id", all.x = TRUE)

    # Helper: run one SDoH model
    run_sdoh_model <- function(df, var_name, levels, model_name) {
      cat("\n--- ", model_name, " ---\n")
      df[[var_name]][is.na(df[[var_name]])] <- "Missing"
      fvar <- paste0("f.", var_name)
      df[[fvar]] <- factor(df[[var_name]], levels = levels)
      frm <- as.formula(paste0("Treatment ~ ", base_rhs, " + ", fvar, " + strata(stratum)"))
      tryCatch({
        fit <- clogit(frm, data = df)
        aor <- extract_aor(fit, model_name)
        sdoh_rows <- grepl(fvar, aor$variable, fixed = TRUE)
        cat("  "); print(aor[sdoh_rows, c("variable","AOR","CI_lower","CI_upper","p_value")])
        save(fit, file = file.path(RESULTS, paste0(model_name, "_clogit.RData")))
        write_csv(aor, file.path(RESULTS, paste0(model_name, "_coefficients.csv")))
        return(aor)
      }, error = function(e) { cat("  ERROR:", e$message, "\n"); return(NULL) })
    }

    # 1. Insurance (3 binary flags — custom)
    cat("\n---  insurance  ---\n")
    reg_sdoh$ins_employer[is.na(reg_sdoh$ins_employer)] <- 0
    reg_sdoh$ins_medicare[is.na(reg_sdoh$ins_medicare)] <- 0
    reg_sdoh$ins_medicaid[is.na(reg_sdoh$ins_medicaid)] <- 0
    tryCatch({
      ins_fit <- clogit(as.formula(paste("Treatment ~", base_rhs,
        "+ ins_employer + ins_medicare + ins_medicaid + strata(stratum)")), data = reg_sdoh)
      ins_aor <- extract_aor(ins_fit, "insurance")
      cat("  "); print(ins_aor[grepl("ins_", ins_aor$variable),
        c("variable","AOR","CI_lower","CI_upper","p_value")])
      save(ins_fit, file = file.path(RESULTS, "insurance_clogit.RData"))
      write_csv(ins_aor, file.path(RESULTS, "insurance_coefficients.csv"))
      results_all[[length(results_all)+1]] <- ins_aor
    }, error = function(e) { cat("  Insurance ERROR:", e$message, "\n") })

    # 2. Lumped disability
    results_all[[length(results_all)+1]] <- run_sdoh_model(reg_sdoh, "disability_any",
      c("No","Yes","Missing"), "disability_lumped")

    # 3-8. Individual disabilities
    for (d in c("disability_hearing","disability_vision","disability_cognition",
                "disability_mobility","disability_selfcare","disability_independent")) {
      results_all[[length(results_all)+1]] <- run_sdoh_model(reg_sdoh, d, c("No","Yes","Missing"), d)
    }

    # 9. Employment
    results_all[[length(results_all)+1]] <- run_sdoh_model(reg_sdoh, "employment",
      c("Employed","Student","Unemployed","Others","Missing"), "employment")

    # 10. Income
    results_all[[length(results_all)+1]] <- run_sdoh_model(reg_sdoh, "income",
      c("35k_100k","less_10k","10k_25k","25k_35k","100k_150k","150k_200k","more_200k","Missing"), "income")

    # 11. Housing
    results_all[[length(results_all)+1]] <- run_sdoh_model(reg_sdoh, "housing",
      c("Own","Rent","Others","Missing"), "housing")

    # 12. Housing stability
    results_all[[length(results_all)+1]] <- run_sdoh_model(reg_sdoh, "housing_stability",
      c("Stable","Unstable","Missing"), "housing_stability")

    # 13. Education
    results_all[[length(results_all)+1]] <- run_sdoh_model(reg_sdoh, "education",
      c("Advanced","Never_Attended","Below_GED","GED_or_College","Missing"), "education")

  } else {
    cat("  SDoH file has only person_id — skipping SDoH models.\n")
  }

} else if (IS_MS) {
  cat("\n  [MarketScan] No SDoH surveys — plan_type and region in base model.\n")
}

# ═════════════════════════════════════════════════════════════════════
# COMBINE ALL RESULTS
# ═════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 60), "\nCOMBINING RESULTS\n", strrep("=", 60), "\n")

results_all <- Filter(Negate(is.null), results_all)
all_coefs <- do.call(rbind, results_all)
rownames(all_coefs) <- NULL

write_csv(all_coefs, file.path(RESULTS, "all_model_coefficients.csv"))
cat("  Combined:", nrow(all_coefs), "coefficient rows from",
    length(results_all), "models\n")

# Upload to bucket if on AoU
if (IS_AOU) {
  bucket <- Sys.getenv("WORKSPACE_BUCKET")
  if (nchar(bucket) > 0) {
    system(paste0("gsutil -m cp ", RESULTS, "/*.csv ", bucket, "/data/covid_sdoh/", COHORT, "/"), intern = TRUE)
    system(paste0("gsutil -m cp ", RESULTS, "/*.RData ", bucket, "/data/covid_sdoh/", COHORT, "/"), intern = TRUE)
    cat("  Uploaded to", bucket, "\n")
  }
}

# ── Print headline results ───────────────────────────────────────────
cat("\n", strrep("=", 60), "\nHEADLINE RESULTS [", toupper(COHORT), "]\n", strrep("=", 60), "\n")

sig_base <- base_aor[base_aor$p_value < 0.05, ]
sig_base <- sig_base[order(sig_base$AOR, decreasing = TRUE), ]
cat("\n  Significant base model terms (p<0.05):\n")
for (i in seq_len(min(nrow(sig_base), 15))) {
  r <- sig_base[i, ]
  cat(sprintf("    %-45s AOR %.2f (%.2f-%.2f)  p=%.2e\n",
    r$variable, r$AOR, r$CI_lower, r$CI_upper, r$p_value))
}

if (IS_AOU) {
  sdoh_coefs <- all_coefs[all_coefs$model != "base" & all_coefs$p_value < 0.05, ]
  sdoh_coefs <- sdoh_coefs[grepl("^f\\.", sdoh_coefs$variable), ]
  sdoh_coefs <- sdoh_coefs[order(sdoh_coefs$AOR, decreasing = TRUE), ]
  if (nrow(sdoh_coefs) > 0) {
    cat("\n  Significant SDoH terms (p<0.05):\n")
    for (i in seq_len(min(nrow(sdoh_coefs), 15))) {
      r <- sdoh_coefs[i, ]
      cat(sprintf("    %-45s AOR %.2f (%.2f-%.2f)  p=%.2e  [%s]\n",
        r$variable, r$AOR, r$CI_lower, r$CI_upper, r$p_value, r$model))
    }
  }
}

# ── Session info ─────────────────────────────────────────────────────
cat("\n--- R Session Info ---\n")
cat("R version:", R.version$version.string, "\n")
for (pkg in c("survival","dplyr","readr")) {
  cat(pkg, ":", as.character(packageVersion(pkg)), "\n")
}
cat("\nDone. All results in", RESULTS, "/\n")
