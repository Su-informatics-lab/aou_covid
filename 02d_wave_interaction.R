#!/usr/bin/env Rscript
# ─────────────────────────────────────────────────────────────────────
# Wave x exposure interaction tests
#
# Why this file exists
# --------------------
# The Introduction asks how the social and racial associations differ
# across pandemic waves. Until now the paper answered that by fitting a
# separate model inside each wave and comparing three point estimates by
# eye, and then said in the Results that the waves "were not compared
# formally". A question asked in the Introduction and declined in the
# Results is the kind of gap a reviewer opens with.
#
# This script closes it with one pooled model per exposure. Wave varies
# within matched stratum -- matching was on survey date, diagnosis count
# and EHR length, not on index date -- so f.wave and its interactions are
# identified inside conditional logistic regression. A pooled model also
# keeps every stratum, whereas the wave-stratified models discard any
# stratum whose case and controls straddle a wave boundary (Delta kept
# only 301 of 644).
#
# Two tests are reported for each exposure:
#   * a cluster-robust Wald test on the whole interaction block, which is
#     the primary test because controls are reused across strata and every
#     other estimate in this study is clustered on person_id;
#   * the model-based likelihood-ratio test, for reference only. It ignores
#     control reuse and will read as more significant than it is.
#
# Usage: Rscript 02d_wave_interaction.R aou_v7
#        (run 02_models.R first; it writes joint_model_inputs.rds)
# License: MIT
# ─────────────────────────────────────────────────────────────────────

library(survival)
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(readr))
if (!requireNamespace("sandwich", quietly = TRUE)) install.packages("sandwich")
library(sandwich)

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1 || !args[1] %in% c("aou_v7", "aou_v8")) {
  cat("Usage: Rscript 02d_wave_interaction.R [aou_v7|aou_v8]\n")
  quit(status = 1)
}
COHORT  <- args[1]
RESULTS <- file.path("results", COHORT)

inp_path <- file.path(RESULTS, "joint_model_inputs.rds")
if (!file.exists(inp_path)) {
  stop(sprintf(paste0(
    "%s not found.\n",
    "  Run `Rscript 02_models.R %s` first -- it writes this file at the\n",
    "  point the joint model is fitted, so the interaction models use\n",
    "  exactly the same rows and the same factor levels."), inp_path, COHORT))
}
inp        <- readRDS(inp_path)
df         <- inp$df
base_rhs   <- inp$base_rhs
joint_sdoh <- inp$joint_sdoh

cat(strrep("=", 68), "\nWAVE x EXPOSURE INTERACTION TESTS --", COHORT, "\n",
    strrep("=", 68), "\n")
cat("  rows:", nrow(df), " strata:", length(unique(df$stratum)),
    " cases:", sum(df$Treatment == 1), "\n")
cat("  wave distribution:\n"); print(table(df$f.wave))

# Wave must vary inside strata or clogit conditions it out and nothing is
# identified. Say so loudly rather than letting NA coefficients pass.
wv <- df %>% group_by(stratum) %>% summarise(k = n_distinct(f.wave), .groups = "drop")
cat(sprintf("  strata with >1 wave represented: %d / %d (%.1f%%)\n",
            sum(wv$k > 1), nrow(wv), 100 * mean(wv$k > 1)))
if (mean(wv$k > 1) < 0.05) {
  stop("Wave is almost constant within stratum; the interaction is not ",
       "identified in a conditional model. Fall back to wave-stratified fits.")
}

m0 <- clogit(as.formula(paste("Treatment ~", base_rhs, "+", joint_sdoh,
                              "+ strata(stratum)")), data = df)

# ── cluster-robust Wald test on a block of coefficients ──────────────
block_wald <- function(fit, pattern, data) {
  b   <- coef(fit)
  idx <- grep(pattern, names(b))
  idx <- idx[!is.na(b[idx])]
  if (!length(idx)) return(NULL)
  V <- tryCatch(vcovCL(fit, cluster = data$person_id),
                error = function(e) { cat("  vcovCL failed, using model-based V\n")
                                      vcov(fit) })
  bb <- b[idx]; VV <- V[idx, idx, drop = FALSE]
  W  <- tryCatch(drop(t(bb) %*% solve(VV) %*% bb), error = function(e) NA_real_)
  list(terms = names(bb), df = length(idx), chisq = W,
       p = if (is.na(W)) NA_real_ else pchisq(W, length(idx), lower.tail = FALSE))
}

run_one <- function(label, exposure) {
  cat("\n", strrep("-", 68), "\n", label, "  (", exposure, " x f.wave )\n",
      strrep("-", 68), "\n", sep = "")
  if (!exposure %in% names(df)) { cat("  absent from the data; skipped\n"); return(NULL) }
  frm <- as.formula(paste("Treatment ~", base_rhs, "+", joint_sdoh,
                          "+", exposure, ":f.wave + strata(stratum)"))
  m1 <- tryCatch(clogit(frm, data = df), error = function(e) { cat("  fit failed:",
        conditionMessage(e), "\n"); NULL })
  if (is.null(m1)) return(NULL)

  rob <- block_wald(m1, paste0("^", exposure, ".*:f\\.wave|f\\.wave.*:", exposure), df)
  lrt <- 2 * (m1$loglik[2] - m0$loglik[2])
  ldf <- length(coef(m1)[!is.na(coef(m1))]) - length(coef(m0)[!is.na(coef(m0))])

  cat(sprintf("  interaction terms: %d\n", if (is.null(rob)) 0L else rob$df))
  if (!is.null(rob))
    cat(sprintf("  PRIMARY  cluster-robust Wald  chi2 = %.2f  df = %d  P = %.4g\n",
                rob$chisq, rob$df, rob$p))
  cat(sprintf("  reference (ignores control reuse) LRT  chi2 = %.2f  df = %d  P = %.4g\n",
              lrt, ldf, pchisq(lrt, max(ldf, 1), lower.tail = FALSE)))

  # wave-specific AOR for the first non-reference level, from the pooled fit
  b <- coef(m1); V <- tryCatch(vcovCL(m1, cluster = df$person_id),
                               error = function(e) vcov(m1))
  main <- grep(paste0("^", exposure), names(b), value = TRUE)
  main <- setdiff(main, grep(":", main, value = TRUE))
  rows <- list()
  for (lv in main) {
    for (w in levels(df$f.wave)) {
      cv <- rep(0, length(b)); names(cv) <- names(b)
      cv[lv] <- 1
      hit <- grep(paste0("(^", lv, ":f\\.wave", w, "$)|(^f\\.wave", w, ":", lv, "$)"),
                  names(b), value = TRUE)
      if (length(hit)) cv[hit] <- 1
      ok <- !is.na(b)
      lo <- sum(cv[ok] * b[ok]); se <- sqrt(drop(t(cv[ok]) %*% V[ok, ok] %*% cv[ok]))
      rows[[length(rows) + 1]] <- data.frame(
        exposure = exposure, level = lv, wave = w,
        AOR = exp(lo), CI_lower = exp(lo - 1.96 * se), CI_upper = exp(lo + 1.96 * se))
    }
  }
  out <- bind_rows(rows)
  print(out, digits = 3)
  list(exposure = exposure, robust = rob, lrt = lrt, lrt_df = ldf, contrasts = out)
}

res <- list()
for (ex in c("f.race", "f.income", "f.insurance")) {
  r <- run_one(paste("Interaction:", ex), ex)
  if (!is.null(r)) res[[ex]] <- r
}

summ <- bind_rows(lapply(res, function(r) data.frame(
  exposure   = r$exposure,
  n_terms    = if (is.null(r$robust)) NA_integer_ else r$robust$df,
  wald_chisq = if (is.null(r$robust)) NA_real_    else r$robust$chisq,
  wald_p     = if (is.null(r$robust)) NA_real_    else r$robust$p,
  lrt_chisq  = r$lrt, lrt_df = r$lrt_df,
  lrt_p      = pchisq(r$lrt, max(r$lrt_df, 1), lower.tail = FALSE))))
write_csv(summ, file.path(RESULTS, "wave_interaction_tests.csv"))
write_csv(bind_rows(lapply(res, `[[`, "contrasts")),
          file.path(RESULTS, "wave_interaction_contrasts.csv"))

cat("\n", strrep("=", 68), "\nSUMMARY\n", strrep("=", 68), "\n")
print(summ, digits = 3)

need <- c("wave_interaction_tests.csv", "wave_interaction_contrasts.csv")
miss <- need[!file.exists(file.path(RESULTS, need))]
if (length(miss)) stop("02d did not write: ", paste(miss, collapse = ", "))

bucket <- Sys.getenv("WORKSPACE_BUCKET")
if (nchar(bucket) > 0) {
  bdir <- paste0(bucket, "/data/covid_sdoh/", COHORT, "/")
  system(paste0("gsutil -m cp ", RESULTS, "/wave_interaction_*.csv ", bdir),
         intern = TRUE)
  cat("  Uploaded to bucket.\n")
}
cat("\nDone. Copy both CSVs back into the repository and git add them --\n",
    "the bucket is not the repository, which is how eTable 12b went missing.\n")
