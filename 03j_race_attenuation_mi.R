## 03j_race_attenuation_mi.R -- how much of the Black-race association the
## social domains account for, under the primary specification.
##
## Why this exists. The manuscript states that measured socioeconomic position
## accounts for about a sixth of the Black-race association and that almost all
## of it runs through income. That number was computed on the missing-indicator
## specification, which is now the sensitivity. Race has been demoted to one
## Results fact, one Limitations clause and one Discussion sentence, but a
## demoted claim still has to be true under the specification the paper calls
## primary, and the reader is entitled to the attenuation it is built on.
##
## Nothing is re-imputed. This reads the 40 imputations 03d already saved.
##
## Three models, same people, same strata, same 40 imputations:
##   base        clinical and demographic only
##   + income    income added on its own
##   joint       all six social terms
##
## Attenuation is reported on the log-odds scale, which is where it is additive;
## the odds ratio is non-collapsible, so the percentages indicate direction and
## approximate magnitude rather than a decomposition.
##
## Output: /home/jupyter/mi40b/{log_race.txt, race_attenuation_mi.csv}

suppressPackageStartupMessages({library(survival); library(sandwich)})

BUCKET <- "/home/jupyter/workspace/rw-migration-aou-rw-46c7ae9e/data/covid_sdoh"
RES <- file.path(BUCKET, "aou_v7_5domain")
OUT <- "/home/jupyter/mi40b"
sink(file.path(OUT, "log_race.txt"), split = TRUE)

X    <- readRDS(file.path(RES, "joint_model_inputs.rds"))
d    <- X$df
IM   <- readRDS(file.path(OUT, "imputations.rds"))
IMPS <- IM$imps
M    <- length(IMPS)
IMPV <- names(IMPS[[1]])
idx  <- match(d$person_id, IM$person_id)
stopifnot(!any(is.na(idx)))
cat("m =", M, "| rows", nrow(d), "| imputed:", paste(IMPV, collapse = ", "), "\n\n")

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

tab <- function(p) {
  se  <- sqrt(diag(p$Tv))
  lam <- pmin(pmax((1 + 1 / p$m) * diag(p$B) / diag(p$Tv), 1e-8), 1 - 1e-8)
  nu_old <- (p$m - 1) / lam^2
  nu_com <- nrow(d) - length(p$nm)
  nu_obs <- (nu_com + 1) / (nu_com + 3) * nu_com * (1 - lam)
  nu <- nu_old * nu_obs / (nu_old + nu_obs)
  data.frame(term = p$nm, beta = p$qbar, aor = exp(p$qbar),
             lo = exp(p$qbar - qt(0.975, nu) * se),
             hi = exp(p$qbar + qt(0.975, nu) * se),
             fmi = round(lam, 3), stringsAsFactors = FALSE)
}

fit_all <- function(formula, label) {
  CO <- list(); VA <- list(); fails <- 0; dropped <- character(0)
  for (k in seq_len(M)) {
    dk <- apply_imp(k)
    fk <- tryCatch(clogit(formula, data = dk, method = "efron"),
                   error = function(e) NULL)
    if (is.null(fk)) { fails <- fails + 1; next }
    b  <- coef(fk)
    Vk <- tryCatch(sandwich::vcovCL(fk, cluster = dk$person_id),
                   error = function(e) vcov(fk))
    ok <- intersect(names(b)[!is.na(b)], rownames(Vk))
    if (length(ok) < 2) { fails <- fails + 1; next }
    if (length(ok) < length(b)) dropped <- union(dropped, setdiff(names(b), ok))
    CO[[length(CO) + 1]] <- b[ok]
    VA[[length(VA) + 1]] <- Vk[ok, ok, drop = FALSE]
  }
  cat(sprintf("%-28s fitted %d of %d | failures %d\n", label, length(CO), M, fails))
  if (length(dropped)) cat("   not estimable somewhere:",
                           paste(dropped, collapse = ", "), "\n")
  pool_full(CO, VA)
}

base_rhs  <- X$base_rhs
joint_rhs <- X$joint_sdoh

f_base   <- as.formula(paste("Treatment ~", base_rhs, "+ strata(stratum)"))
f_income <- as.formula(paste("Treatment ~", base_rhs, "+ f.income + strata(stratum)"))
f_joint  <- as.formula(paste("Treatment ~", base_rhs, "+", joint_rhs, "+ strata(stratum)"))

cat("\n===== three models =====\n")
P <- list(base = fit_all(f_base, "base (no social domains)"),
          income = fit_all(f_income, "base + income"),
          joint = fit_all(f_joint, "base + all six domains"))

RACE <- grep("^f\\.race", P$base$nm, value = TRUE)
rows <- list()
for (m in names(P)) {
  t <- tab(P[[m]])
  t <- t[t$term %in% RACE, ]
  t$model <- m
  rows[[m]] <- t
  cat("\n", m, "\n", sep = "")
  print(t[, c("term", "aor", "lo", "hi")], row.names = FALSE, digits = 4)
}
R <- do.call(rbind, rows)

cat("\n===== attenuation on the log-odds scale =====\n")
cat("share of the base-model log odds ratio removed by adding the domains\n\n")
att <- data.frame()
for (r in RACE) {
  b0 <- R$beta[R$term == r & R$model == "base"]
  bi <- R$beta[R$term == r & R$model == "income"]
  bj <- R$beta[R$term == r & R$model == "joint"]
  att <- rbind(att, data.frame(
    term = r, beta_base = b0, beta_income = bi, beta_joint = bj,
    aor_base = exp(b0), aor_income = exp(bi), aor_joint = exp(bj),
    pct_removed_by_income = 100 * (b0 - bi) / b0,
    pct_removed_by_all    = 100 * (b0 - bj) / b0,
    income_share_of_total = 100 * (b0 - bi) / (b0 - bj)))
}
print(att[, c("term", "aor_base", "aor_income", "aor_joint",
              "pct_removed_by_income", "pct_removed_by_all",
              "income_share_of_total")], row.names = FALSE, digits = 4)

write.csv(R, file.path(OUT, "race_attenuation_mi.csv"), row.names = FALSE)
write.csv(att, file.path(OUT, "race_attenuation_shares.csv"), row.names = FALSE)
cat("\nwrote race_attenuation_mi.csv and race_attenuation_shares.csv\nDONE\n")
sink()
