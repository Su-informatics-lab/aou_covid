## 03t_att_cov.R -- attenuation intervals from the person-clustered JOINT covariance
## of the alone and joint coefficients (GPT-6 R2c-02, 2026-09-24).
##
## 03r took the alone-joint correlation from the matched-set bootstrap, the method
## under question, so it did not check the attenuation variance independently. Here
## both coefficients come from the same fits, and their covariance from person-level
## influence functions:
##   IF_i = sum over person i's rows of score_r %*% vcov(fit)   (one row per person)
##   Cov(a, j) within imputation = sum_i IF_a,i IF_j,i * G / (G - 1)
## which reproduces sandwich::vcovCL(cluster = person) on the diagonal (checked
## below and on survival::infert before the run), and supplies the off-diagonal that
## vcovCL on two separate fits cannot. Rubin: T = W + (1 + 1/m) B on the 2x2 (a, j)
## covariance; attenuation A = 100 (1 - j / a) by the delta method on T.
## The matched structure is kept: every fit is the conditional likelihood on the
## matched sets; only the variance is aggregated by person.
## Aggregates only. OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 ARM=covid NCOR=1 Rscript 03t_att_cov.R

L <- readLines("/home/jupyter/03o_r4_attenuation.R")
Sys.setenv(PART = "ATTCOV")
eval(parse(text = L[1:(grep("^## =+ PROBE", L)[1] - 1)]))
NCOR <- as.integer(Sys.getenv("NCOR", "1"))

fit_if <- function(f, dk) {
  f2 <- f; environment(f2) <- environment()
  fk <- clogit(f2, data = dk, method = "efron")
  b <- coef(fk); ok <- names(b)[!is.na(b)]
  IF <- (sandwich::estfun(fk) %*% vcov(fk))[, ok, drop = FALSE]
  P <- rowsum(IF, dk$person_id)
  chk <- sqrt(diag(sandwich::vcovCL(fk, cluster = dk$person_id)))[ok]
  list(b = b[ok], P = P, chk = chk)
}
one_imp <- function(k) {
  dk <- apply_imp(k)
  J <- fit_if(fml(paste(BASE, "+", JOINT)), dk)
  Bm <- fit_if(fml(BASE), dk)
  A <- list(); for (v in unique(FOCV)) A[[v]] <- fit_if(fml(paste(BASE, "+", v)), dk)
  out <- list()
  for (nm in c(names(FOC), "black")) {
    ft <- if (nm == "black") BLACK else FOC[[nm]]
    Al <- if (nm == "black") Bm else A[[FOCV[[nm]]]]
    ids <- intersect(rownames(Al$P), rownames(J$P)); G <- length(ids)
    X <- cbind(Al$P[ids, ft], J$P[ids, ft])
    V <- crossprod(X) * G / (G - 1)
    out[[nm]] <- list(ab = c(Al$b[[ft]], J$b[[ft]]), V = V,
                      chk = c(sqrt(V[1, 1]) / Al$chk[[ft]], sqrt(V[2, 2]) / J$chk[[ft]]))
  }
  out
}
t0 <- Sys.time()
R <- parallel::mclapply(seq_len(M), function(k) tryCatch(one_imp(k), error = function(e) conditionMessage(e)), mc.cores = NCOR)
bad <- sapply(R, is.character); if (any(bad)) { print(unique(unlist(R[bad]))); stop("imputations failed: ", sum(bad)) }
cat("imputations:", length(R), "| minutes", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "\n")

rows <- list()
for (nm in c(names(FOC), "black")) {
  AB <- t(sapply(R, function(z) z[[nm]]$ab)); m <- nrow(AB)
  W <- Reduce(`+`, lapply(R, function(z) z[[nm]]$V)) / m
  Bv <- stats::cov(AB); Tv <- W + (1 + 1 / m) * Bv
  a <- mean(AB[, 1]); j <- mean(AB[, 2])
  g <- c(100 * j / a^2, -100 / a); se <- sqrt(drop(t(g) %*% Tv %*% g))
  chk <- range(sapply(R, function(z) z[[nm]]$chk))
  rows[[nm]] <- data.frame(term = nm, b_alone = a, b_joint = j,
    se_alone = sqrt(Tv[1, 1]), se_joint = sqrt(Tv[2, 2]), cor_alone_joint = Tv[1, 2] / sqrt(Tv[1, 1] * Tv[2, 2]),
    att = 100 * (1 - j / a), att_se = se, att_lo = 100 * (1 - j / a) - 1.96 * se, att_hi = 100 * (1 - j / a) + 1.96 * se,
    if_vs_vcovCL_min = chk[1], if_vs_vcovCL_max = chk[2], m = m, row.names = NULL)
}
o <- do.call(rbind, rows)
write.csv(o, file.path(OUT, "attcov_person_clustered.csv"), row.names = FALSE)
print(o, row.names = FALSE, digits = 4)
cat("DONE\n")
