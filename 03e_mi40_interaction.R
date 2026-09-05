## 03e_mi40_interaction.R — Test 2 under the same specification as Tests 1, 3
## and 4, so the paper does not switch specification between tests.
##
## Runs on the All of Us Researcher Workbench. Nothing person-level leaves it.
##
## Why this exists. If multiple imputation becomes the primary specification for
## the pooled joint model, the era analysis cannot stay on the missing-indicator
## model without a reviewer asking which specification was chosen where and why.
## This refits the wave interaction on the same 40 imputed frames 03d saved, and
## reports the block Wald under imputation next to the frozen indicator result
## (income chi-square 19.32, 14 df, P = 0.15; insurance 25.50, 8 df, P = 0.001).
##
## Delta holds 282 matched strata. The insurance-by-wave block may not be
## estimable on every imputed frame; failures are counted rather than hidden,
## and if more than a handful fail the honest conclusion is that Test 2 stays on
## the indicator specification with that stated in Methods.
##
## Output: /home/jupyter/mi40b/{log_interaction.txt, wave_interaction_mi.csv,
##         wave_contrasts_mi.csv}

suppressPackageStartupMessages({
  library(survival); library(sandwich)
})

RES <- "/home/jupyter/refit_nodis/results/aou_v7"
OUT <- "/home/jupyter/mi40b"
sink(file.path(OUT, "log_interaction.txt"), split = TRUE)

X <- readRDS(file.path(RES, "joint_model_inputs.rds"))
d <- X$df
IM <- readRDS(file.path(OUT, "imputations.rds"))
IMPS <- IM$imps; M <- length(IMPS)
IMPV <- names(IMPS[[1]])
idx <- match(d$person_id, IM$person_id)
stopifnot(!any(is.na(idx)))
cat("m =", M, "| rows", nrow(d), "\n")

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

D1 <- function(p, keep) {
  k <- length(keep)
  q <- p$qbar[keep]; U <- p$Ubar[keep, keep, drop = FALSE]
  Bs <- p$B[keep, keep, drop = FALSE]
  Ui <- tryCatch(solve(U), error = function(e) MASS::ginv(U))
  r1 <- (1 + 1 / p$m) * sum(diag(Bs %*% Ui)) / k
  stat <- as.numeric(t(q) %*% Ui %*% q) / (k * (1 + r1))
  t_ <- k * (p$m - 1)
  df2 <- if (t_ > 4) 4 + (t_ - 4) * (1 + (1 - 2 / t_) / r1)^2
         else t_ * (1 + 1 / k) * (1 + 1 / r1)^2 / 2
  c(F = stat, df1 = k, df2 = df2, r1 = r1, p = pf(stat, k, df2, lower.tail = FALSE))
}

run_interaction <- function(exposure, tag) {
  f <- as.formula(paste("Treatment ~", X$base_rhs, "+", X$joint_sdoh, "+",
                        exposure, ":f.wave + strata(stratum)"))
  CO <- VA <- list(); fails <- 0
  for (k in seq_len(M)) {
    dk <- apply_imp(k)
    fk <- tryCatch(clogit(f, data = dk, method = "efron"), error = function(e) NULL)
    if (is.null(fk) || any(is.na(coef(fk)))) { fails <- fails + 1; next }
    v <- tryCatch(sandwich::vcovCL(fk, cluster = dk$person_id),
                  error = function(e) vcov(fk))
    CO[[length(CO) + 1]] <- coef(fk); VA[[length(VA) + 1]] <- v
    if (k %% 10 == 0) cat("   ", tag, k, "of", M, "\n")
  }
  cat(tag, ": fitted", length(CO), "of", M, "| failed or rank-deficient:", fails, "\n")
  if (length(CO) < 2) { cat(tag, ": not estimable under imputation\n"); return(NULL) }
  p <- pool_full(CO, VA)
  keep <- grep(paste0("^", exposure, ".*:f\\.wave|^f\\.wave.*:", exposure), p$nm, value = TRUE)
  cat(tag, ": interaction terms", length(keep), "\n")
  s <- D1(p, keep)
  print(round(s, 4))
  list(pool = p, stat = s, fitted = length(CO), fails = fails, keep = keep)
}

cat("\n===== income x wave =====\n"); a <- run_interaction("f.income", "income")
cat("\n===== insurance x wave =====\n"); b <- run_interaction("f.insurance", "insurance")

rows <- list()
for (nmx in c("income", "insurance")) {
  r <- get(if (nmx == "income") "a" else "b")
  if (is.null(r)) next
  rows[[nmx]] <- data.frame(
    exposure = nmx, spec = "multiple imputation, m = 40",
    F = r$stat["F"], df1 = r$stat["df1"], df2 = r$stat["df2"],
    p = r$stat["p"], imputations_fitted = r$fitted, failures = r$fails,
    row.names = NULL)
}
if (length(rows)) {
  out <- do.call(rbind, rows)
  print(out, row.names = FALSE, digits = 4)
  write.csv(out, file.path(OUT, "wave_interaction_mi.csv"), row.names = FALSE)
}

## wave-specific contrasts for the two exposures, on the same pooled fits, so
## the era figure can be redrawn under imputation if Test 2 moves
contr <- list()
for (nmx in c("income", "insurance")) {
  r <- get(if (nmx == "income") "a" else "b")
  if (is.null(r)) next
  p <- r$pool; ex <- paste0("f.", nmx)
  main <- setdiff(grep(paste0("^", ex), p$nm, value = TRUE),
                  grep(":", p$nm, value = TRUE))
  for (lv in main) for (w in levels(d$f.wave)) {
    cv <- setNames(rep(0, length(p$nm)), p$nm)
    cv[lv] <- 1
    hit <- intersect(c(paste0(lv, ":f.wave", w), paste0("f.wave", w, ":", lv)), p$nm)
    if (length(hit)) cv[hit] <- 1
    est <- sum(cv * p$qbar)
    sd_ <- sqrt(drop(t(cv) %*% p$Tv %*% cv))
    contr[[length(contr) + 1]] <- data.frame(
      exposure = nmx, level = lv, wave = w, aor = exp(est),
      lo = exp(est - 1.96 * sd_), hi = exp(est + 1.96 * sd_), row.names = NULL)
  }
}
if (length(contr)) {
  cc <- do.call(rbind, contr)
  print(cc, row.names = FALSE, digits = 3)
  write.csv(cc, file.path(OUT, "wave_contrasts_mi.csv"), row.names = FALSE)
}

cat("\nDONE\n")
sink()
