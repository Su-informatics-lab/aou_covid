## 03i_flu_domain_and_period.R -- two things Figure 1 and Figure 2 need from the
## influenza arm under the primary specification, neither of which 03f produced.
##
##   1. domain-specific models, one domain at a time (Figure 1, right column)
##   2. the joint model refitted WITHIN each period (Figure 2, bottom row)
##
## On (2), and why it is not the interaction contrast used in the COVID-19 arm.
## Matching in this arm is within season, so period is constant inside a matched
## stratum: it drops out of the conditional likelihood, `dm:period` therefore
## spans an over-complete basis, and R aliases redundant columns away. That is
## fine for the block Wald test 03f already reported -- the surviving degrees of
## freedom are exactly (J-1)(P-1) -- but it makes a per-period contrast
## ambiguous, because reconstructing beta + gamma requires knowing which columns
## were aliased. Refitting inside each period is unambiguous and is what a reader
## expects a by-era panel to be. The COVID-19 arm keeps its interaction
## contrasts, where wave varies within stratum and the reconstruction is valid.
## The estimand is the same in both arms; the estimator differs because the
## matching designs differ, and the legend says so.
##
## Nothing is re-imputed. This reads the 40 imputations 03f already saved.
##
## Output: /home/jupyter/flu_mi40/{log_domain_period.txt,
##         domain_specific_mi.csv, joint_by_period_mi.csv}

suppressPackageStartupMessages({library(survival); library(sandwich)})

FLU <- "/home/jupyter/flu"
OUT <- "/home/jupyter/flu_mi40"
sink(file.path(OUT, "log_domain_period.txt"), split = TRUE)

m <- read.csv(file.path(FLU, "07_matched_cohort.csv"), stringsAsFactors = FALSE)
CH <- c("Myocardial_Infarction","Congestive_Heart_Failure","Peripheral_Vascular_Disease",
 "Cerebrovascular_Disease","Dementia","Chronic_Pulmonary_Disease","Rheumatic_Disease",
 "Peptic_Ulcer_Disease","Liver_Disease_Mild","Liver_Disease_Moderate_Severe",
 "Diabetes_without_Chronic_Complications","Diabetes_with_Chronic_Complications",
 "Hemiplegia_Paraplegia","Renal_Disease_Mild_Moderate","Renal_Disease_Severe","HIV",
 "Metastatic_Solid_Tumor","Malignancy","AIDS")
rl <- function(x, r) relevel(factor(x), ref = r)
m$income <- rl(m$income, "35k_100k"); m$employment <- rl(m$employment, "Employed")
m$education <- rl(m$education, "GED_or_College"); m$housing <- rl(m$housing, "Own")
m$housing_stability <- rl(m$housing_stability, "Stable")
m$insurance_type <- rl(m$insurance_type, "Employer")
m$age_group <- rl(m$age_group, "18-44"); m$race <- rl(m$race, "White")
m$sex_at_birth <- rl(m$sex_at_birth, "Female")
m$ethnicity    <- rl(m$ethnicity, "Not Hispanic or Latino")
m$period <- rl(factor(m$period), "3_post")

BASE  <- paste(c("sex_at_birth","race","ethnicity","age_group", CH), collapse = " + ")
DOM   <- c("insurance_type","income","employment","education","housing","housing_stability")
JOINT <- paste(DOM, collapse = " + ")

IM   <- readRDS(file.path(OUT, "imputations.rds"))
IMPS <- IM$imps
MALL <- length(IMPS)
M    <- if (nzchar(Sys.getenv("M_OVERRIDE"))) as.integer(Sys.getenv("M_OVERRIDE")) else MALL
IMPV <- names(IMPS[[1]])
idx  <- match(m$person_id, IM$person_id)
stopifnot(!any(is.na(idx)))
cat("m =", M, "of", MALL, "saved | rows", nrow(m), "| periods:\n"); print(table(m$period))

apply_imp <- function(k) {
  mk <- m
  for (v in IMPV) mk[[v]] <- IMPS[[k]][[v]][idx]
  mk
}

pool_full <- function(CO, VA) {
  nm <- Reduce(intersect, lapply(CO, names))
  Q  <- sapply(CO, function(z) z[nm])
  Ubar <- Reduce(`+`, lapply(VA, function(v) v[nm, nm])) / length(VA)
  B <- if (length(VA) > 1) stats::cov(t(Q)) else Ubar * 0
  list(qbar = rowMeans(Q), Ubar = Ubar, B = B,
       Tv = Ubar + (1 + 1 / length(VA)) * B, m = length(VA), nm = nm)
}

mk_tab <- function(p, n_rows) {
  se  <- sqrt(diag(p$Tv))
  lam <- pmin(pmax((1 + 1 / p$m) * diag(p$B) / diag(p$Tv), 1e-8), 1 - 1e-8)
  nu_old <- (p$m - 1) / lam^2
  nu_com <- n_rows - length(p$nm)
  nu_obs <- (nu_com + 1) / (nu_com + 3) * nu_com * (1 - lam)
  nu <- nu_old * nu_obs / (nu_old + nu_obs)
  data.frame(term = p$nm, aor = exp(p$qbar),
             lo = exp(p$qbar - qt(0.975, nu) * se),
             hi = exp(p$qbar + qt(0.975, nu) * se),
             fmi = round((nu + 1) / (nu + 3) * lam + 2 / (nu + 3), 3),
             row.names = NULL)
}

dropped <- character(0)
fit_all <- function(formula, dat_fn, label) {
  CO <- VA <- list(); fails <- 0
  dropped <<- character(0)
  for (k in seq_len(M)) {
    mk <- dat_fn(k)
    fk <- tryCatch(clogit(formula, data = mk, method = "efron"), error = function(e) NULL)
    if (is.null(fk)) { fails <- fails + 1; next }
    b  <- coef(fk)
    Vk <- tryCatch(sandwich::vcovCL(fk, cluster = mk$person_id),
                   error = function(e) vcov(fk))
    ok <- intersect(names(b)[!is.na(b)], rownames(Vk))
    if (length(ok) < 2) { fails <- fails + 1; next }
    if (length(ok) < length(b)) dropped <<- union(dropped, setdiff(names(b), ok))
    CO[[length(CO) + 1]] <- b[ok]
    VA[[length(VA) + 1]] <- Vk[ok, ok, drop = FALSE]
  }
  cat(sprintf("%-34s fitted %d of %d | failures %d\n", label, length(CO), M, fails))
  if (length(dropped)) cat("   not estimable in at least one fit:",
                           paste(dropped, collapse = ", "), "\n")
  if (length(CO) < 2) return(NULL)
  pool_full(CO, VA)
}

## ---- 1. domain-specific -----------------------------------------------------
cat("\n===== domain-specific models, one domain at a time =====\n\n")
rows <- list()
for (dm in DOM) {
  f <- as.formula(paste("Treatment ~", BASE, "+", dm, "+ strata(subclass)"))
  p <- fit_all(f, apply_imp, dm)
  if (is.null(p)) { cat(dm, ": not estimable\n"); next }
  t <- mk_tab(p, nrow(m))
  t <- t[startsWith(t$term, dm) & !grepl(":", t$term), ]
  t$domain <- dm
  rows[[dm]] <- t
  print(t[, c("term", "aor", "lo", "hi", "fmi")], row.names = FALSE, digits = 3)
  cat("\n")
}
ds <- do.call(rbind, rows)
write.csv(ds, file.path(OUT, "domain_specific_mi.csv"), row.names = FALSE)
cat("wrote domain_specific_mi.csv --", nrow(ds), "rows\n")

## ---- 2. the joint model refitted inside each period -------------------------
cat("\n===== joint model refitted within each period =====\n")
cat("2_pandemic is the small one; failures are counted, not hidden.\n\n")
f_joint <- as.formula(paste("Treatment ~", BASE, "+", JOINT, "+ strata(subclass)"))
prows <- list()
for (pe in levels(m$period)) {
  keep_rows <- which(m$period == pe)
  n_pe <- length(keep_rows)
  sub_fn <- function(k) {
    mk <- apply_imp(k)[keep_rows, ]
    droplevels(mk)
  }
  ## a stratum is informative only if it still holds a case and a control
  chk <- sub_fn(1)
  ok_str <- tapply(chk$Treatment, chk$subclass, function(z) any(z == 1) && any(z == 0))
  cat(sprintf("%-12s rows %5d | strata %4d | informative strata %4d | cases %4d\n",
              pe, n_pe, length(ok_str), sum(ok_str, na.rm = TRUE),
              sum(chk$Treatment == 1)))
  p <- fit_all(f_joint, sub_fn, paste("joint |", pe))
  if (is.null(p)) { cat("  ", pe, ": not estimable under imputation\n\n"); next }
  t <- mk_tab(p, n_pe)
  t <- t[grepl("^(income|insurance_type|employment|education|housing)", t$term), ]
  t$period <- pe
  prows[[pe]] <- t
  print(t[grepl("^(income|insurance_type)", t$term), c("term", "aor", "lo", "hi")],
        row.names = FALSE, digits = 3)
  cat("\n")
}
jp <- do.call(rbind, prows)
write.csv(jp, file.path(OUT, "joint_by_period_mi.csv"), row.names = FALSE)
cat("wrote joint_by_period_mi.csv --", nrow(jp), "rows\n")
cat("\nDONE\n")
sink()
