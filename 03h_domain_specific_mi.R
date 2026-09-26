## 03h_domain_specific_mi.R -- the domain-specific column, under the primary
## specification, for the COVID-19 arm.
##
## Why this exists. Figure 1 has to show what mutual adjustment actually does:
## each survey domain fitted on its own, then all six fitted together. 03d fitted
## only the joint model, so under multiple imputation the domain-specific column
## has never existed; the only version of it in the repository is on the
## missing-indicator specification, which is now the sensitivity. Drawing one
## figure from two specifications is the kind of thing a reviewer opens with.
##
## Nothing is re-imputed. This reads the 40 imputations 03d already saved.
##
## Output: /home/jupyter/mi40b/{log_domain.txt, domain_specific_congenial.csv}

suppressPackageStartupMessages({library(survival); library(sandwich)})

BUCKET <- "/home/jupyter/workspace/rw-migration-aou-rw-46c7ae9e/data/covid_sdoh"
RES <- file.path(BUCKET, "aou_v7_5domain")
OUT <- "/home/jupyter/mi40b"
sink(file.path(OUT, "log_domain.txt"), split = TRUE)

X    <- readRDS(file.path(RES, "joint_model_inputs.rds"))
d    <- X$df
IM   <- readRDS(file.path(OUT, "imputations.rds"))
IMPS <- IM$imps
MALL <- length(IMPS)
M    <- if (nzchar(Sys.getenv("M_OVERRIDE"))) as.integer(Sys.getenv("M_OVERRIDE")) else MALL
IMPV <- names(IMPS[[1]])
idx  <- match(d$person_id, IM$person_id)
stopifnot(!any(is.na(idx)))
cat("m =", M, "of", MALL, "saved | rows", nrow(d), "| imputed items:",
    paste(IMPV, collapse = ", "), "\n")

apply_imp <- function(k) {
  dk <- d
  for (v in IMPV) dk[[v]] <- IMPS[[k]][[v]][idx]
  dk
}

pool_full <- function(CO, VA) {
  nm <- Reduce(intersect, lapply(CO, names))
  Q  <- sapply(CO, function(z) z[nm])
  Ubar <- Reduce(`+`, lapply(VA, function(v) v[nm, nm])) / length(VA)
  B <- if (length(VA) > 1) stats::cov(t(Q)) else Ubar * 0
  list(qbar = rowMeans(Q), Ubar = Ubar, B = B,
       Tv = Ubar + (1 + 1 / length(VA)) * B, m = length(VA), nm = nm)
}

## Barnard-Rubin, identical to 03d so the two columns of Figure 1 are on the
## same footing and their intervals are comparable.
tab <- function(p) {
  se  <- sqrt(diag(p$Tv))
  lam <- pmin(pmax((1 + 1 / p$m) * diag(p$B) / diag(p$Tv), 1e-8), 1 - 1e-8)
  nu_old <- (p$m - 1) / lam^2
  nu_com <- nrow(d) - length(p$nm)
  nu_obs <- (nu_com + 1) / (nu_com + 3) * nu_com * (1 - lam)
  nu <- nu_old * nu_obs / (nu_old + nu_obs)
  data.frame(term = p$nm, aor = exp(p$qbar),
             lo = exp(p$qbar - qt(0.975, nu) * se),
             hi = exp(p$qbar + qt(0.975, nu) * se),
             fmi = round((nu + 1) / (nu + 3) * lam + 2 / (nu + 3), 3),
             row.names = NULL)
}

dropped <- character(0)
fit_all <- function(formula, label) {
  CO <- VA <- list(); fails <- 0
  dropped <<- character(0)
  for (k in seq_len(M)) {
    dk <- apply_imp(k)
    fk <- tryCatch(clogit(formula, data = dk, method = "efron"), error = function(e) NULL)
    if (is.null(fk)) { fails <- fails + 1; next }
    b  <- coef(fk)
    Vk <- tryCatch(sandwich::vcovCL(fk, cluster = dk$person_id),
                   error = function(e) vcov(fk))
    ok <- intersect(names(b)[!is.na(b)], rownames(Vk))
    if (length(ok) < 2) { fails <- fails + 1; next }
    if (length(ok) < length(b)) dropped <<- union(dropped, setdiff(names(b), ok))
    CO[[length(CO) + 1]] <- b[ok]
    VA[[length(VA) + 1]] <- Vk[ok, ok, drop = FALSE]
  }
  cat(sprintf("%-22s fitted %d of %d | failures %d\n", label, length(CO), M, fails))
  if (length(dropped)) cat("   not estimable in at least one fit:",
                           paste(dropped, collapse = ", "), "\n")
  if (length(CO) < 2) return(NULL)
  pool_full(CO, VA)
}

DOM <- c("f.income", "f.insurance", "f.education", "f.employment",
         "f.housing", "f.housing_stability")

cat("\n===== domain-specific models, one domain at a time =====\n")
cat("Each model is the clinical covariate set plus ONE survey domain. The joint\n")
cat("column for comparison is 03d's joint_congenial.csv.\n\n")

rows <- list()
for (dm in DOM) {
  f <- as.formula(paste("Treatment ~", X$base_rhs, "+", dm, "+ strata(stratum)"))
  p <- fit_all(f, dm)
  if (is.null(p)) { cat(dm, ": not estimable\n"); next }
  t <- tab(p)
  ## the model contains exactly one domain, so a name prefix is unambiguous here
  t <- t[startsWith(t$term, dm) & !grepl(":", t$term), ]
  t$domain <- dm
  rows[[dm]] <- t
  print(t[, c("term", "aor", "lo", "hi", "fmi")], row.names = FALSE, digits = 3)
  cat("\n")
}
out <- do.call(rbind, rows)
write.csv(out, file.path(OUT, "domain_specific_congenial.csv"), row.names = FALSE)
cat("wrote domain_specific_congenial.csv --", nrow(out), "rows\n")
cat("\nDONE\n")
sink()
