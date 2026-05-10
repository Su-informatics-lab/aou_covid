#!/usr/bin/env Rscript
# ─────────────────────────────────────────────────────────────────────
# COVID-19 Severity × SDoH — Propensity Score Matching (MatchIt)
#
# Replaces the sklearn/NearestNeighbors PSM previously embedded in
# 01_aou_etl.py and 01_ms_etl.py with the canonical MatchIt package.
#
# Specification (unchanged from pilot):
#   - 1:4 nearest-neighbor matching with replacement
#   - Logistic regression propensity score (distance = "glm")
#   - 0.2 SD caliper on the logit propensity score
#   - AoU covariates: enrollment_ord, num_diagnosis, ehr_length_days
#   - MS  covariates: enrollment_ord, num_diagnosis, coverage_span_days
#
# Inputs  (from 01_aou_etl.py / 01_ms_etl.py):
#   {RESULTS}/01_covid_cohort.csv
#   {RESULTS}/02_demographics.csv
#   {RESULTS}/03_charlson.csv
#   {RESULTS}/05_vaccination.csv
#   {RESULTS}/06_matching_variables.csv
#   {RESULTS}/04_sdoh.csv          (AoU only)
#   {RESULTS}/04b_sdoh_timing.csv  (AoU only)
#
# Outputs:
#   {RESULTS}/07_matched_cohort.csv       Case-control matched pairs
#   {RESULTS}/07b_control_reuse.csv       Control reuse statistics
#   {RESULTS}/07c_smd_pre_matching.csv    Pre-matching SMDs
#   {RESULTS}/07d_smd_post_matching.csv   Post-matching SMDs (full covariate)
#   {RESULTS}/07e_matchit_summary.txt     MatchIt summary for audit
#   {RESULTS}/08_regression_base.csv      Merged regression-ready data frame
#   {RESULTS}/figures/efig_love_plot.pdf   Love plot (Nature style)
#
# Usage:
#   Rscript 01b_psm.R aou_v7
#   Rscript 01b_psm.R aou_v8
#   Rscript 01b_psm.R ms
#
# References:
#   Ho DE, Imai K, King G, Stuart EA. MatchIt: Nonparametric
#     preprocessing for parametric causal inference. J Stat Softw. 2011.
#   Austin PC. An introduction to propensity score methods for reducing
#     the effects of confounding in observational studies. Multivariate
#     Behav Res. 2011;46(3):399-424.
#   Austin PC. Variance estimation when using propensity-score matching
#     with replacement. Stat Med. 2020;39(13):1838-1855.
#
# License: MIT
# ─────────────────────────────────────────────────────────────────────

# ── Package management ───────────────────────────────────────────────
for (pkg in c("MatchIt", "cobalt", "dplyr", "readr")) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg)
}
library(MatchIt)
library(cobalt)
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(readr))

# ── Parse argument ───────────────────────────────────────────────────
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1 || !args[1] %in% c("aou_v7", "aou_v8", "ms")) {
  cat("Usage: Rscript 01b_psm.R [aou_v7|aou_v8|ms]\n")
  quit(status = 1)
}
COHORT  <- args[1]
IS_AOU  <- startsWith(COHORT, "aou")
IS_MS   <- COHORT == "ms"
RESULTS <- file.path("results", COHORT)
FIG_DIR <- file.path("results", "figures")
dir.create(FIG_DIR, recursive = TRUE, showWarnings = FALSE)

cat(strrep("=", 70), "\n")
cat("PROPENSITY SCORE MATCHING (MatchIt)  [", toupper(COHORT), "]\n")
cat(strrep("=", 70), "\n")
cat("  Input/Output:", RESULTS, "\n")

# ── Download from bucket if on AoU Workbench ─────────────────────────
bucket <- Sys.getenv("WORKSPACE_BUCKET")
if (IS_AOU && nchar(bucket) > 0) {
  bdir <- paste0(bucket, "/data/covid_sdoh/", COHORT, "/")
  needed <- c("01_covid_cohort.csv", "02_demographics.csv",
              "03_charlson.csv", "04_sdoh.csv", "04b_sdoh_timing.csv",
              "05_vaccination.csv", "06_matching_variables.csv")
  for (f in needed) {
    local_f <- file.path(RESULTS, f)
    if (!file.exists(local_f)) {
      cat("  Downloading:", f, "\n")
      system(paste0("gsutil cp ", bdir, f, " ", RESULTS, "/"), intern = TRUE)
    }
  }
}

# ── Load data ────────────────────────────────────────────────────────
cohort    <- read_csv(file.path(RESULTS, "01_covid_cohort.csv"), show_col_types = FALSE)
demo      <- read_csv(file.path(RESULTS, "02_demographics.csv"), show_col_types = FALSE)
charlson  <- read_csv(file.path(RESULTS, "03_charlson.csv"), show_col_types = FALSE)
vacc      <- read_csv(file.path(RESULTS, "05_vaccination.csv"), show_col_types = FALSE)
match_raw <- read_csv(file.path(RESULTS, "06_matching_variables.csv"), show_col_types = FALSE)

cat("  Cohort:", nrow(cohort), "| Demographics:", nrow(demo),
    "| Charlson:", nrow(charlson), "\n")
cat("  Vaccination:", nrow(vacc), "| Matching vars:", nrow(match_raw), "\n")


# ══════════════════════════════════════════════════════════════════════
# BUILD MATCHING DATA FRAME
# ══════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 60), "\n")
cat("BUILDING MATCHING DATA FRAME\n")
cat(strrep("=", 60), "\n")

# Identify matching covariates by cohort type
if (IS_AOU) {
  MATCH_COVS <- c("enrollment_ord", "num_diagnosis", "ehr_length_days")
} else {
  MATCH_COVS <- c("enrollment_ord", "num_diagnosis", "coverage_span_days")
}

# Merge severity labels into matching variables
match_df <- merge(
  match_raw[, c("person_id", MATCH_COVS)],
  cohort[, c("person_id", "severity")],
  by = "person_id"
)

# Drop rows with missing matching covariates
n_before <- nrow(match_df)
match_df <- match_df[complete.cases(match_df[, MATCH_COVS]), ]
cat("  Complete cases:", nrow(match_df), "/", n_before, "\n")
cat("  Cases:", sum(match_df$severity == 1),
    "| Controls:", sum(match_df$severity == 0), "\n")


# ══════════════════════════════════════════════════════════════════════
# RUN MatchIt
# ══════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 60), "\n")
cat("RUNNING MatchIt\n")
cat(strrep("=", 60), "\n")

# Build formula: severity ~ cov1 + cov2 + cov3
ps_formula <- as.formula(paste("severity ~", paste(MATCH_COVS, collapse = " + ")))
cat("  PS formula:", deparse(ps_formula), "\n")
cat("  Method: nearest, ratio=4, replace=TRUE, caliper=0.2 (logit PS SD)\n")

# Run matching
m <- matchit(
  ps_formula,
  data      = match_df,
  method    = "nearest",
  distance  = "glm",       # logistic regression PS
  ratio     = 4,
  replace   = TRUE,
  caliper   = 0.2,         # 0.2 SD of logit PS (MatchIt default unit)
  std.caliper = TRUE        # caliper in SD units (default)
)

cat("\n  MatchIt summary:\n")
print(summary(m))

# Save MatchIt summary to text file for audit trail
sink(file.path(RESULTS, "07e_matchit_summary.txt"))
cat("MatchIt Summary for", toupper(COHORT), "\n")
cat("Date:", as.character(Sys.time()), "\n")
cat("R:", R.version$version.string, "\n")
cat("MatchIt:", as.character(packageVersion("MatchIt")), "\n\n")
print(summary(m))
sink()


# ══════════════════════════════════════════════════════════════════════
# EXTRACT MATCHED COHORT
# ══════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 60), "\n")
cat("EXTRACTING MATCHED COHORT\n")
cat(strrep("=", 60), "\n")

# get_matches() returns one row per unit per match (controls duplicated
# if matched to multiple cases). This replicates the with-replacement
# format from the pilot (person_id, Treatment, stratum).
matched_pairs <- get_matches(m, data = match_df)

# Rename to match downstream pipeline expectations
matched <- data.frame(
  person_id = matched_pairs$person_id,
  Treatment = matched_pairs$severity,
  stratum   = as.integer(matched_pairs$subclass),
  stringsAsFactors = FALSE
)

n_cases  <- sum(matched$Treatment == 1)
n_ctrls  <- sum(matched$Treatment == 0)
n_strata <- length(unique(matched$stratum))
cat(sprintf("  Cases: %s | Control rows: %s | Strata: %s | Ratio: 1:%.1f\n",
            format(n_cases, big.mark = ","),
            format(n_ctrls, big.mark = ","),
            format(n_strata, big.mark = ","),
            n_ctrls / n_cases))

# Cases dropped (no match within caliper)
n_cases_total <- sum(match_df$severity == 1)
n_dropped <- n_cases_total - n_cases
cat(sprintf("  Dropped (no match within caliper): %d\n", n_dropped))

write_csv(matched, file.path(RESULTS, "07_matched_cohort.csv"))
cat("  Saved: 07_matched_cohort.csv\n")


# ── Control reuse statistics ─────────────────────────────────────────
ctrl_rows <- matched[matched$Treatment == 0, ]
ctrl_reuse <- table(ctrl_rows$person_id)
n_unique <- length(ctrl_reuse)
med_reuse <- median(ctrl_reuse)
q1_reuse  <- quantile(ctrl_reuse, 0.25)
q3_reuse  <- quantile(ctrl_reuse, 0.75)
max_reuse <- max(ctrl_reuse)

cat(sprintf("  Control reuse: %s unique, median %.0f (IQR %.0f–%.0f), max %d\n",
            format(n_unique, big.mark = ","),
            med_reuse, q1_reuse, q3_reuse, max_reuse))

reuse_df <- data.frame(
  metric = c("n_unique_controls", "n_control_rows", "median_reuse",
             "iqr_lower", "iqr_upper", "max_reuse", "caliper_sd",
             "n_cases_dropped"),
  value  = c(n_unique, nrow(ctrl_rows), med_reuse,
             q1_reuse, q3_reuse, max_reuse, 0.2, n_dropped)
)
write_csv(reuse_df, file.path(RESULTS, "07b_control_reuse.csv"))


# ══════════════════════════════════════════════════════════════════════
# BALANCE DIAGNOSTICS (cobalt)
# ══════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 60), "\n")
cat("BALANCE DIAGNOSTICS\n")
cat(strrep("=", 60), "\n")

# Pre-matching SMDs
bal_pre <- bal.tab(m, un = TRUE, stats = c("mean.diffs", "variance.ratios"))
cat("\n  Pre/post matching balance:\n")
print(bal_pre)

# Extract SMD table for CSV export
smd_tab <- bal_pre$Balance
smd_df <- data.frame(
  variable           = rownames(smd_tab),
  smd_unadjusted     = smd_tab$Diff.Un,
  smd_adjusted       = smd_tab$Diff.Adj,
  var_ratio_unadj    = if ("V.Ratio.Un" %in% names(smd_tab)) smd_tab$V.Ratio.Un else NA,
  var_ratio_adj      = if ("V.Ratio.Adj" %in% names(smd_tab)) smd_tab$V.Ratio.Adj else NA,
  stringsAsFactors   = FALSE, row.names = NULL
)
write_csv(smd_df, file.path(RESULTS, "07c_smd_pre_matching.csv"))
cat("  Saved: 07c_smd_pre_matching.csv\n")

# Full-covariate post-matching SMDs
# (demographics, comorbidities, vaccination — variables NOT in the PS model)
# These are expected to have residual imbalance, especially SDoH.
cat("\n  Computing full-covariate post-matching SMDs...\n")

# Merge all covariates into matched data
reg <- merge(matched, demo, by = "person_id", all.x = TRUE)
reg <- merge(reg, charlson, by = "person_id", all.x = TRUE)
reg <- merge(reg, vacc[, c("person_id", "vaccination")], by = "person_id", all.x = TRUE)
reg$vaccination[is.na(reg$vaccination)] <- "Unknown"

# Charlson columns — fill NA with 0
como_cols <- c("Myocardial_Infarction", "Congestive_Heart_Failure",
               "Peripheral_Vascular_Disease", "Cerebrovascular_Disease", "Dementia",
               "Chronic_Pulmonary_Disease", "Rheumatic_Disease", "Peptic_Ulcer_Disease",
               "Liver_Disease_Mild", "Liver_Disease_Moderate_Severe",
               "Diabetes_without_Chronic_Complications",
               "Diabetes_with_Chronic_Complications",
               "Hemiplegia_Paraplegia", "Renal_Disease_Mild_Moderate",
               "Renal_Disease_Severe", "HIV", "Metastatic_Solid_Tumor",
               "Malignancy", "AIDS")
for (col in como_cols) {
  if (col %in% names(reg)) reg[[col]][is.na(reg[[col]])] <- 0
}

# Add pandemic wave
reg <- merge(reg, cohort[, c("person_id", "pandemic_wave", "severity_broad")],
             by = "person_id", all.x = TRUE)
reg$pandemic_wave[is.na(reg$pandemic_wave)] <- "unknown"

# Compute SMDs for all covariates in the regression model
full_smd_rows <- list()
cases_r  <- reg[reg$Treatment == 1, ]
ctrls_r  <- reg[reg$Treatment == 0, ]

smd_binary <- function(cases, controls, col, val = 1) {
  p1 <- mean(cases[[col]] == val, na.rm = TRUE)
  p2 <- mean(controls[[col]] == val, na.rm = TRUE)
  pooled <- sqrt((p1*(1-p1) + p2*(1-p2)) / 2)
  if (pooled == 0) return(0)
  (p1 - p2) / pooled
}

smd_continuous <- function(cases, controls, col) {
  c_vals <- cases[[col]][!is.na(cases[[col]])]
  k_vals <- controls[[col]][!is.na(controls[[col]])]
  if (length(c_vals) == 0 || length(k_vals) == 0) return(NA)
  pooled <- sqrt((sd(c_vals)^2 + sd(k_vals)^2) / 2)
  if (pooled == 0) return(0)
  (mean(c_vals) - mean(k_vals)) / pooled
}

# Demographics
demo_cats <- list(
  sex_at_birth = c("Female", "Male"),
  age_group = c("<45", "45-54", "55-64", "65+")
)
if (IS_AOU) {
  demo_cats$race <- c("White", "Black", "Asian", "Other")
  demo_cats$ethnicity <- c("Not Hispanic", "Hispanic", "Other")
}

for (col in names(demo_cats)) {
  if (!col %in% names(reg)) next
  for (val in demo_cats[[col]]) {
    smd_val <- smd_binary(cases_r, ctrls_r, col, val)
    full_smd_rows[[length(full_smd_rows) + 1]] <- data.frame(
      group = "Demographics", variable = paste0(col, ": ", val),
      smd = smd_val, abs_smd = abs(smd_val),
      stringsAsFactors = FALSE
    )
  }
}

# Vaccination
if ("vaccination" %in% names(reg)) {
  smd_val <- smd_binary(cases_r, ctrls_r, "vaccination", "Vaccinated")
  full_smd_rows[[length(full_smd_rows) + 1]] <- data.frame(
    group = "Clinical", variable = "Vaccinated",
    smd = smd_val, abs_smd = abs(smd_val),
    stringsAsFactors = FALSE
  )
}

# Pandemic wave
if ("pandemic_wave" %in% names(reg)) {
  for (w in c("pre_delta", "delta", "omicron")) {
    smd_val <- smd_binary(cases_r, ctrls_r, "pandemic_wave", w)
    full_smd_rows[[length(full_smd_rows) + 1]] <- data.frame(
      group = "Clinical", variable = paste0("Wave: ", w),
      smd = smd_val, abs_smd = abs(smd_val),
      stringsAsFactors = FALSE
    )
  }
}

# Comorbidities
for (col in como_cols) {
  if (!col %in% names(reg)) next
  smd_val <- smd_binary(cases_r, ctrls_r, col, 1)
  full_smd_rows[[length(full_smd_rows) + 1]] <- data.frame(
    group = "Comorbidities", variable = gsub("_", " ", col),
    smd = smd_val, abs_smd = abs(smd_val),
    stringsAsFactors = FALSE
  )
}

# SDoH (AoU only — expected residual imbalance since not in PS model)
if (IS_AOU) {
  sdoh_path <- file.path(RESULTS, "04_sdoh.csv")
  if (file.exists(sdoh_path)) {
    sdoh <- read_csv(sdoh_path, show_col_types = FALSE)
    reg_sdoh_bal <- merge(reg[, c("person_id", "Treatment")], sdoh,
                          by = "person_id", all.x = TRUE)
    cases_s <- reg_sdoh_bal[reg_sdoh_bal$Treatment == 1, ]
    ctrls_s <- reg_sdoh_bal[reg_sdoh_bal$Treatment == 0, ]

    sdoh_cats <- list(
      insurance_type = c("Employer", "Medicare", "Medicaid", "Other_None"),
      income = c("less_10k", "10k_25k", "25k_35k", "35k_100k",
                 "100k_150k", "150k_200k", "more_200k"),
      education = c("Below_GED", "GED_or_College", "Advanced"),
      employment = c("Employed", "Unemployed", "Others"),
      housing = c("Own", "Rent"),
      housing_stability = c("Stable", "Unstable"),
      disability_any = c("Yes", "No")
    )

    for (col in names(sdoh_cats)) {
      if (!col %in% names(reg_sdoh_bal)) next
      for (val in sdoh_cats[[col]]) {
        smd_val <- smd_binary(cases_s, ctrls_s, col, val)
        full_smd_rows[[length(full_smd_rows) + 1]] <- data.frame(
          group = "SDoH", variable = paste0(col, ": ", val),
          smd = smd_val, abs_smd = abs(smd_val),
          stringsAsFactors = FALSE
        )
      }
    }
  }
}

full_smd_df <- do.call(rbind, full_smd_rows)
write_csv(full_smd_df, file.path(RESULTS, "07d_smd_post_matching.csv"))

cat("\n  Full-covariate post-matching SMDs:\n")
cat(sprintf("  %-50s %8s %8s\n", "Variable", "SMD", "|SMD|"))
cat("  ", strrep("-", 70), "\n")
for (i in seq_len(nrow(full_smd_df))) {
  r <- full_smd_df[i, ]
  flag <- ifelse(r$abs_smd > 0.10, " ***",
           ifelse(r$abs_smd > 0.05, " **", ""))
  cat(sprintf("  %-50s %+.4f  %.4f%s\n", r$variable, r$smd, r$abs_smd, flag))
}

n_imbalanced <- sum(full_smd_df$abs_smd > 0.10)
cat(sprintf("\n  Variables with |SMD| > 0.10: %d\n", n_imbalanced))
cat(sprintf("  Variables with |SMD| > 0.05: %d\n", sum(full_smd_df$abs_smd > 0.05)))


# ══════════════════════════════════════════════════════════════════════
# LOVE PLOT (Nature style, saved as PDF + PNG for publication)
# ══════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 60), "\n")
cat("LOVE PLOT\n")
cat(strrep("=", 60), "\n")

# Use cobalt's built-in Love plot for quick diagnostic
tryCatch({
  pdf(file.path(FIG_DIR, paste0("efig_love_plot_", COHORT, ".pdf")),
      width = 7.205, height = 9.0, family = "Helvetica")
  love.plot(m,
            stats = "mean.diffs",
            abs = TRUE,
            thresholds = c(m = 0.1),
            var.order = "unadjusted",
            shapes = c("circle filled", "triangle filled"),
            colors = c("#D55E00", "#0072B2"),
            sample.names = c("Unadjusted", "Adjusted"),
            title = NULL)
  dev.off()
  cat("  Saved: efig_love_plot_", COHORT, ".pdf\n")
}, error = function(e) {
  cat("  WARNING: Love plot failed (", e$message, ")\n")
})

# Also save PNG
tryCatch({
  png(file.path(FIG_DIR, paste0("efig_love_plot_", COHORT, ".png")),
      width = 7.205, height = 9.0, units = "in", res = 600, family = "Helvetica")
  love.plot(m,
            stats = "mean.diffs",
            abs = TRUE,
            thresholds = c(m = 0.1),
            var.order = "unadjusted",
            shapes = c("circle filled", "triangle filled"),
            colors = c("#D55E00", "#0072B2"),
            sample.names = c("Unadjusted", "Adjusted"),
            title = NULL)
  dev.off()
  cat("  Saved: efig_love_plot_", COHORT, ".png\n")
}, error = function(e) {
  cat("  WARNING: Love plot PNG failed (", e$message, ")\n")
})


# ══════════════════════════════════════════════════════════════════════
# BUILD REGRESSION DATA FRAME
# ══════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 60), "\n")
cat("BUILDING REGRESSION DATA FRAME\n")
cat(strrep("=", 60), "\n")

# 'reg' was already built above during the full-covariate SMD step.
# It has: person_id, Treatment, stratum, demographics, Charlson,
# vaccination, pandemic_wave, severity_broad.
# Just need to add plan_type/region for MS.

if (IS_MS) {
  # plan_type and region_name are already in demo
  # (they're in the merge from 02_demographics.csv)
  cat("  MarketScan: plan_type and region_name from demographics\n")
}

cat(sprintf("  Shape: %d rows × %d cols\n", nrow(reg), ncol(reg)))
cat("  Columns:", paste(names(reg), collapse = ", "), "\n")

# Check NAs
na_counts <- colSums(is.na(reg))
na_nonzero <- na_counts[na_counts > 0]
if (length(na_nonzero) > 0) {
  cat("  NAs:\n")
  for (nm in names(na_nonzero)) {
    cat(sprintf("    %-40s %d\n", nm, na_nonzero[nm]))
  }
}

write_csv(reg, file.path(RESULTS, "08_regression_base.csv"))
cat("  Saved: 08_regression_base.csv\n")


# ── Upload to bucket (AoU) ───────────────────────────────────────────
if (IS_AOU && nchar(bucket) > 0) {
  system(paste0("gsutil -m cp ", RESULTS, "/07*.csv ",
                bucket, "/data/covid_sdoh/", COHORT, "/"), intern = TRUE)
  system(paste0("gsutil -m cp ", RESULTS, "/08_regression_base.csv ",
                bucket, "/data/covid_sdoh/", COHORT, "/"), intern = TRUE)
  system(paste0("gsutil -m cp ", FIG_DIR, "/efig_love_plot_", COHORT, ".* ",
                bucket, "/data/covid_sdoh/figures/"), intern = TRUE)
  cat("  Uploaded to bucket.\n")
}


# ══════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════
cat("\n", strrep("=", 70), "\n")
cat("PSM COMPLETE [", toupper(COHORT), "]\n")
cat(strrep("=", 70), "\n")
cat("  Matching: 1:4 NN with replacement, caliper = 0.2 SD logit PS\n")
cat(sprintf("  Cases: %s | Controls: %s (unique: %s) | Strata: %s\n",
            format(n_cases, big.mark = ","),
            format(n_ctrls, big.mark = ","),
            format(n_unique, big.mark = ","),
            format(n_strata, big.mark = ",")))
cat(sprintf("  Max control reuse: %d | Dropped: %d\n", max_reuse, n_dropped))
cat(sprintf("  Post-matching |SMD| > 0.10: %d variables\n", n_imbalanced))
cat("\n  Outputs:\n")
cat("    07_matched_cohort.csv      — matched pairs\n")
cat("    07b_control_reuse.csv      — reuse statistics\n")
cat("    07c_smd_pre_matching.csv   — pre-matching SMDs\n")
cat("    07d_smd_post_matching.csv  — full-covariate post-matching SMDs\n")
cat("    07e_matchit_summary.txt    — MatchIt audit trail\n")
cat("    08_regression_base.csv     — regression-ready data frame\n")
cat("    efig_love_plot_*.pdf/png   — Love plot\n")
cat("\n--- Session Info ---\n")
cat("R:", R.version$version.string, "\n")
for (p in c("MatchIt", "cobalt", "dplyr", "readr"))
  cat(p, ":", as.character(packageVersion(p)), "\n")
cat("\nDone.\n")
