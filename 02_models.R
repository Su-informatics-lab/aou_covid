#!/usr/bin/env Rscript
# ─────────────────────────────────────────────────────────────────────
# COVID-19 Severity and Social Determinants of Health
# Conditional Logistic Regression: Base Model + SDoH Models
# All of Us Research Program, Controlled Tier
#
# License: MIT
# Requires: All of Us Researcher Workbench (Controlled Tier access)
# ─────────────────────────────────────────────────────────────────────

library(survival)
library(tidyverse)

# ── Setup ────────────────────────────────────────────────────────────
bucket <- Sys.getenv("WORKSPACE_BUCKET")
dir.create("results", showWarnings = FALSE)
system(paste0("gsutil cp ", bucket, "/data/covid_sdoh/*_07_regression_base.csv ."), intern = TRUE)
system(paste0("gsutil cp ", bucket, "/data/covid_sdoh/*_04_sdoh.csv ."), intern = TRUE)

regression_bm <- read_csv(list.files(pattern = "_07_regression_base.csv")[1], show_col_types = FALSE)
sdoh_raw      <- read_csv(list.files(pattern = "_04_sdoh.csv")[1], show_col_types = FALSE)
cat("Regression:", nrow(regression_bm), "rows | SDoH:", nrow(sdoh_raw), "rows\n")

# ── Factor encoding ─────────────────────────────────────────────────
regression_bm$f.sex       <- factor(regression_bm$sex_at_birth, levels = c("Male","Female","Other"))
regression_bm$f.race      <- factor(regression_bm$race, levels = c("White","Black","Asian","Other"))
regression_bm$f.ethnicity <- factor(regression_bm$ethnicity, levels = c("Not Hispanic","Hispanic","Other"))
regression_bm$f.age       <- factor(regression_bm$age_group, levels = c("<45","45-54","55-64","65+"))
regression_bm$f.vacc      <- factor(regression_bm$vaccination, levels = c("Unknown","Vaccinated"))

como <- c("Myocardial_Infarction","Congestive_Heart_Failure","Peripheral_Vascular_Disease",
          "Cerebrovascular_Disease","Dementia","Chronic_Pulmonary_Disease","Rheumatic_Disease",
          "Peptic_Ulcer_Disease","Liver_Disease_Mild","Liver_Disease_Moderate_Severe",
          "Diabetes_without_Chronic_Complications","Diabetes_with_Chronic_Complications",
          "Hemiplegia_Paraplegia","Renal_Disease_Mild_Moderate","Renal_Disease_Severe",
          "HIV","Metastatic_Solid_Tumor","Malignancy","AIDS")
regression_bm[como][is.na(regression_bm[como])] <- 0

base_rhs <- paste(c("f.sex","f.race","f.ethnicity","f.age","f.vacc", como), collapse = " + ")

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
write_csv(base_aor, "results/base_model_coefficients.csv")
save(base_fit, file = "results/base_clogit.RData")

# ═════════════════════════════════════════════════════════════════════
# SDoH MODELS
# ═════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 60), "\nSDoH MODELS\n", strrep("=", 60), "\n")

reg_sdoh <- merge(regression_bm, sdoh_raw, by = "person_id", all.x = TRUE)
results <- list(base_aor)  # start collecting

# ── Helper: run one SDoH model ───────────────────────────────────────
run_model <- function(df, var_name, levels, model_name) {
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
    save(fit, file = paste0("results/", model_name, "_clogit.RData"))
    write_csv(aor, paste0("results/", model_name, "_coefficients.csv"))
    return(aor)
  }, error = function(e) { cat("  ERROR:", e$message, "\n"); return(NULL) })
}

# 1. Insurance (3 binary flags)
cat("\n---  insurance  ---\n")
reg_sdoh$ins_employer[is.na(reg_sdoh$ins_employer)] <- 0
reg_sdoh$ins_medicare[is.na(reg_sdoh$ins_medicare)] <- 0
reg_sdoh$ins_medicaid[is.na(reg_sdoh$ins_medicaid)] <- 0
ins_fit <- clogit(as.formula(paste("Treatment ~", base_rhs,
  "+ ins_employer + ins_medicare + ins_medicaid + strata(stratum)")), data = reg_sdoh)
ins_aor <- extract_aor(ins_fit, "insurance")
cat("  "); print(ins_aor[grepl("ins_", ins_aor$variable),
  c("variable","AOR","CI_lower","CI_upper","p_value")])
save(ins_fit, file = "results/insurance_clogit.RData")
write_csv(ins_aor, "results/insurance_coefficients.csv")
results[[length(results)+1]] <- ins_aor

# 2. Lumped disability
results[[length(results)+1]] <- run_model(reg_sdoh, "disability_any",
  c("No","Yes","Missing"), "disability_lumped")

# 3-8. Individual disabilities
for (d in c("disability_hearing","disability_vision","disability_cognition",
            "disability_mobility","disability_selfcare","disability_independent")) {
  results[[length(results)+1]] <- run_model(reg_sdoh, d, c("No","Yes","Missing"), d)
}

# 9. Employment
results[[length(results)+1]] <- run_model(reg_sdoh, "employment",
  c("Employed","Student","Unemployed","Others","Missing"), "employment")

# 10. Income
results[[length(results)+1]] <- run_model(reg_sdoh, "income",
  c("35k_100k","less_10k","10k_25k","25k_35k","100k_150k","150k_200k","more_200k","Missing"), "income")

# 11. Housing
results[[length(results)+1]] <- run_model(reg_sdoh, "housing",
  c("Own","Rent","Others","Missing"), "housing")

# 12. Housing stability
results[[length(results)+1]] <- run_model(reg_sdoh, "housing_stability",
  c("Stable","Unstable","Missing"), "housing_stability")

# 13. Education
results[[length(results)+1]] <- run_model(reg_sdoh, "education",
  c("Advanced","Never_Attended","Below_GED","GED_or_College","Missing"), "education")

# ═════════════════════════════════════════════════════════════════════
# COMBINE ALL RESULTS
# ═════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 60), "\nCOMBINING RESULTS\n", strrep("=", 60), "\n")

results <- Filter(Negate(is.null), results)
all_coefs <- do.call(rbind, results)
rownames(all_coefs) <- NULL

write_csv(all_coefs, "results/all_model_coefficients.csv")
cat("  Combined:", nrow(all_coefs), "coefficient rows from", length(results), "models\n")

# Upload to bucket
system(paste0("gsutil cp results/*_coefficients.csv ", bucket, "/data/covid_sdoh/"), intern = TRUE)
system(paste0("gsutil cp results/*_clogit.RData ", bucket, "/data/covid_sdoh/"), intern = TRUE)
system(paste0("gsutil cp results/all_model_coefficients.csv ", bucket, "/data/covid_sdoh/"), intern = TRUE)

cat("\nDone. Results in results/ and", bucket, "/data/covid_sdoh/\n")

# ── Print environment for reproducibility ────────────────────────────
cat("\n--- R Session Info ---\n")
cat("R version:", R.version$version.string, "\n")
for (pkg in c("survival","dplyr","readr","tidyverse")) {
  cat(pkg, ":", as.character(packageVersion(pkg)), "\n")
}
