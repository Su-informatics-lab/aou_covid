#!/usr/bin/env Rscript
# ─────────────────────────────────────────────────────────────────────
# eTable 11b: Variance Sensitivity — Efron refit + cluster-robust SEs
#
# The primary 02_models.R uses clogit(method="exact"), which does NOT
# support sandwich::vcovCL (score residuals unavailable). This script
# refits the base model with method="efron" to enable cluster-robust
# SE estimation, then compares the two CI sets.
#
# Usage:
#   Rscript 02b_variance_sensitivity.R ms        # MarketScan
#   Rscript 02b_variance_sensitivity.R aou_v7    # AoU
#
# Output:
#   {RESULTS}/variance_sensitivity_etable11b.csv
# ─────────────────────────────────────────────────────────────────────

if (is.null(getOption("repos")) || getOption("repos")["CRAN"] == "@CRAN@") {
  options(repos = c(CRAN = "https://cloud.r-project.org"))
}
for (pkg in c("survival", "sandwich", "lmtest", "dplyr", "readr")) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg)
}
library(survival)
library(sandwich)
library(lmtest)
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(readr))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) { cat("Usage: Rscript 02b_variance_sensitivity.R [aou_v7|ms]\n"); quit(status=1) }
COHORT  <- args[1]
IS_AOU  <- startsWith(COHORT, "aou")
RESULTS <- file.path("results", COHORT)

cat("=== VARIANCE SENSITIVITY (Efron + cluster-robust) [", toupper(COHORT), "] ===\n")

# ── Load regression data (from 01b_psm.R output) ────────────────────
reg <- read_csv(file.path(RESULTS, "08_regression_base.csv"), show_col_types = FALSE)
cat("  Loaded:", nrow(reg), "rows\n")

# ── Factor setup (must match 02_models.R exactly) ────────────────────
reg$f.sex  <- relevel(factor(reg$sex_at_birth), ref = "Male")
reg$f.age  <- relevel(factor(reg$age_group), ref = "<45")
reg$f.vacc <- relevel(factor(reg$vaccination), ref = "Unknown")
reg$f.wave <- relevel(factor(reg$pandemic_wave), ref = "pre_delta")

if (IS_AOU) {
  reg$f.race <- relevel(factor(reg$race), ref = "White")
  reg$f.eth  <- relevel(factor(reg$ethnicity), ref = "Not Hispanic")
}

has_plantype <- "plan_type" %in% names(reg) && length(unique(reg$plan_type)) > 1
has_region   <- "region_name" %in% names(reg) && length(unique(reg$region_name)) > 1
if (has_plantype) reg$f.plan   <- relevel(factor(reg$plan_type), ref = "PPO")
if (has_region)   reg$f.region <- relevel(factor(reg$region_name), ref = "South")

como <- c("Myocardial_Infarction", "Congestive_Heart_Failure",
          "Peripheral_Vascular_Disease", "Cerebrovascular_Disease", "Dementia",
          "Chronic_Pulmonary_Disease", "Rheumatic_Disease", "Peptic_Ulcer_Disease",
          "Liver_Disease_Mild", "Liver_Disease_Moderate_Severe",
          "Diabetes_without_Chronic_Complications", "Diabetes_with_Chronic_Complications",
          "Hemiplegia_Paraplegia", "Renal_Disease_Mild_Moderate",
          "Renal_Disease_Severe", "HIV", "Metastatic_Solid_Tumor", "Malignancy", "AIDS")
for (col in como) if (col %in% names(reg)) reg[[col]][is.na(reg[[col]])] <- 0

# ── Build formula ────────────────────────────────────────────────────
base_terms <- c("f.sex", "f.age", "f.vacc", "f.wave")
if (IS_AOU) base_terms <- c(base_terms, "f.race", "f.eth")
if (has_plantype) base_terms <- c(base_terms, "f.plan")
if (has_region)   base_terms <- c(base_terms, "f.region")
base_terms <- c(base_terms, como)
fml <- as.formula(paste("Treatment ~", paste(base_terms, collapse=" + "), "+ strata(stratum)"))

# ── Fit with EXACT method (primary) ─────────────────────────────────
cat("  Fitting exact method...\n")
fit_exact <- clogit(fml, data = reg, method = "exact")
s_exact   <- summary(fit_exact)$coefficients

# ── Fit with EFRON method (for vcovCL) ──────────────────────────────
cat("  Fitting efron method...\n")
fit_efron <- clogit(fml, data = reg, method = "efron")
s_efron   <- summary(fit_efron)$coefficients

# ── Cluster-robust SEs ──────────────────────────────────────────────
cat("  Computing cluster-robust SEs (vcovCL on person_id)...\n")
V_cl <- vcovCL(fit_efron, cluster = reg$person_id)
se_cl <- sqrt(diag(V_cl))

# ── Build comparison table ──────────────────────────────────────────
vars <- rownames(s_exact)
out <- data.frame(
  variable       = vars,
  AOR            = round(exp(s_efron[vars, "coef"]), 2),
  CI_exact_lower = round(exp(s_exact[vars, "coef"] - 1.96 * s_exact[vars, "se(coef)"]), 2),
  CI_exact_upper = round(exp(s_exact[vars, "coef"] + 1.96 * s_exact[vars, "se(coef)"]), 2),
  CI_robust_lower = round(exp(s_efron[vars, "coef"] - 1.96 * se_cl[vars]), 2),
  CI_robust_upper = round(exp(s_efron[vars, "coef"] + 1.96 * se_cl[vars]), 2),
  stringsAsFactors = FALSE
)
out$CI_ratio <- round(
  (out$CI_robust_upper - out$CI_robust_lower) /
  (out$CI_exact_upper - out$CI_exact_lower), 2
)

# Significance flip check
sig_exact  <- !(out$CI_exact_lower <= 1 & out$CI_exact_upper >= 1)
sig_robust <- !(out$CI_robust_lower <= 1 & out$CI_robust_upper >= 1)
out$flip <- ifelse(sig_exact != sig_robust, "Yes", "")

write_csv(out, file.path(RESULTS, "variance_sensitivity_etable11b.csv"))

cat("\n  Key headline rows:\n")
headline <- c("f.sexFemale", "f.vaccVaccinated", "f.age65+",
              "f.wavedelta", "f.waveomicron",
              "Renal_Disease_Severe", "Congestive_Heart_Failure", "AIDS")
for (v in headline) {
  if (v %in% out$variable) {
    r <- out[out$variable == v, ]
    cat(sprintf("  %-35s AOR %.2f  exact(%.2f-%.2f)  robust(%.2f-%.2f)  ratio %.2f  %s\n",
                v, r$AOR, r$CI_exact_lower, r$CI_exact_upper,
                r$CI_robust_lower, r$CI_robust_upper, r$CI_ratio, r$flip))
  }
}

cat(sprintf("\n  Median CI ratio: %.2f\n", median(out$CI_ratio, na.rm = TRUE)))
cat(sprintf("  Flipped: %d\n", sum(out$flip == "Yes")))
cat("\n  Saved: variance_sensitivity_etable11b.csv\n")
cat("  Done.\n")
