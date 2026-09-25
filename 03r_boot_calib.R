## 03r_boot_calib.R -- is the matched-set bootstrap too narrow because people recur?
##
## GPT-6 R2b-09 (2026-09-24). The attenuation CIs resample matched sets; a control
## used in several sets (COVID-19: 15,523 control rows from 9,784 people; influenza:
## people recur across seasons) is resampled with each set, not as one person. The
## coefficient analyses cluster the sandwich variance on person. This script asks
## whether the difference matters, on the same resamples the attenuation CIs used:
##
##   1. For the first NB bootstrap jobs of 03o PART=AB (same seeds, set.seed(1e5+i),
##      i = 1..NB; with NB = 400 that is 10 draws per imputation), keep the raw
##      beta_alone and beta_joint of every focal term.
##   2. Pool, over the 40 imputations, beta_alone and beta_joint with Rubin's rules
##      twice: person-clustered sandwich variance (vcovCL) and model-based variance.
##   3. Report bootstrap SD / clustered Rubin SE. A ratio near 1 means the bootstrap
##      carries the person-level dependence the clustered analysis carries.
##   4. A dependence-adjusted attenuation interval: delta method on
##      att = 100 (1 - b_joint / b_alone) with clustered Rubin variances and the
##      alone-joint correlation taken from the bootstrap, beside the percentile CI.
## Aggregates only. OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 ARM=covid NCOR=4 NB=400

L <- readLines("/home/jupyter/03o_r4_attenuation.R")
Sys.setenv(PART = "CALIB")
eval(parse(text = L[1:(grep("^## =+ PROBE", L)[1] - 1)]))
NB <- as.integer(Sys.getenv("NB", "400"))
DR <- file.path(OUT, "calib_draws"); dir.create(DR, showWarnings = FALSE)

rows_by_s <- split(seq_len(nrow(d)), d$.s); sids <- names(rows_by_s)
jobs <- expand.grid(k = seq_len(M), b = seq_len(BPER))
todo <- setdiff(seq_len(NB), as.integer(sub("\\.rds$", "", list.files(DR))))
cat("calibration draws:", NB, "| remaining:", length(todo), "\n"); t0 <- Sys.time()
invisible(mclapply(todo, function(i) {
  set.seed(1e5 + i); dk <- apply_imp(jobs$k[i])
  pick <- sample(sids, length(sids), replace = TRUE)
  ix <- unlist(rows_by_s[pick], use.names = FALSE)
  dd <- dk[ix, ]; dd$.s <- rep(seq_along(pick), lengths(rows_by_s[pick]))
  r <- one_draw(dd); r <- if (is.null(r)) NULL else sapply(r, function(x) x[c("b_alone", "b_joint")])
  saveRDS(r, file.path(DR, paste0(i, ".rds"))); NULL
}, mc.cores = NCOR, mc.preschedule = FALSE))
cat("draws done in", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "min\n")
B <- lapply(seq_len(NB), function(i) readRDS(file.path(DR, paste0(i, ".rds")))); B <- B[!sapply(B, is.null)]
cat("usable draws:", length(B), "\n")

## Rubin pooling, clustered and model-based, for the alone and joint models
pool2 <- function(f) {
  ## sequential: the forked version failed on every core without a message (2026-09-24)
  ## the formula's environment must see dk, or vcovCL cannot rebuild the model frame
  ## (it fails with "object 'dk' not found" -- the failure 03o fit_pool hides by
  ## falling back to vcov; found 2026-09-24)
  fits <- lapply(seq_len(M), function(k) tryCatch({ dk <- apply_imp(k)
    f2 <- f; environment(f2) <- environment()
    fk <- clogit(f2, data = dk, method = "efron")
    b <- coef(fk); ok <- names(b)[!is.na(b)]
    list(b = b[ok], Vc = sandwich::vcovCL(fk, cluster = dk$person_id)[ok, ok], Vm = vcov(fk)[ok, ok]) },
    error = function(e) { message("pool2 fit ", k, ": ", conditionMessage(e)); NULL }))
  fits <- fits[!sapply(fits, is.null)]; cat("  pooled", length(fits), "fits\n")
  nm <- Reduce(intersect, lapply(fits, function(z) names(z$b)))
  Q <- sapply(fits, function(z) z$b[nm]); Bv <- apply(Q, 1, var); m <- length(fits)
  se <- function(el) sqrt(rowMeans(sapply(fits, function(z) diag(z[[el]])[nm])) + (1 + 1 / m) * Bv)
  list(b = rowMeans(Q), sec = se("Vc"), sem = se("Vm"), nm = nm)
}
pj <- pool2(fml(paste(BASE, "+", JOINT)))
pb <- pool2(fml(BASE))
pa <- list(); for (v in unique(FOCV)) pa[[v]] <- pool2(fml(paste(BASE, "+", v)))

out <- list()
for (nm in c(names(FOC), "black")) {
  ft <- if (nm == "black") BLACK else FOC[[nm]]
  A  <- if (nm == "black") pb else pa[[FOCV[[nm]]]]
  ba <- sapply(B, function(z) z["b_alone", nm]); bj <- sapply(B, function(z) z["b_joint", nm])
  a <- A$b[[ft]]; j <- pj$b[[ft]]; sa <- A$sec[[ft]]; sj <- pj$sec[[ft]]; r <- cor(ba, bj)
  g <- c(j / a^2, -1 / a) * 100
  se_att <- sqrt(g[1]^2 * sa^2 + g[2]^2 * sj^2 + 2 * g[1] * g[2] * r * sa * sj)
  att <- 100 * (1 - j / a); attb <- 100 * (1 - bj / ba)
  out[[nm]] <- data.frame(term = nm,
    b_alone = a, se_alone_cluster = sa, se_alone_model = A$sem[[ft]], sd_alone_boot = sd(ba),
    b_joint = j, se_joint_cluster = sj, se_joint_model = pj$sem[[ft]], sd_joint_boot = sd(bj),
    ratio_alone = sd(ba) / sa, ratio_joint = sd(bj) / sj, cor_boot = r,
    att = att, att_pct_lo = unname(quantile(attb, .025)), att_pct_hi = unname(quantile(attb, .975)),
    att_delta_lo = att - 1.96 * se_att, att_delta_hi = att + 1.96 * se_att, sd_att_boot = sd(attb), se_att_delta = se_att,
    n_draws = length(B), row.names = NULL)
}
o <- do.call(rbind, out)
write.csv(o, file.path(OUT, "calib_bootstrap.csv"), row.names = FALSE)
print(o, row.names = FALSE, digits = 3)
cat("DONE\n")
