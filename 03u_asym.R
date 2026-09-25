## 03u_asym.R -- a direct test of the income-insurance asymmetry (persona review
## R3p, 2026-09-25).
##
## The main text contrasts two era patterns (income <$10 000: no detected change;
## Medicaid beyond the other domains: declined) that come from two separate models
## (joint + income x era; joint + insurance x era). "Changed" beside "not detected"
## is not a test that the two differ. Here both interactions enter ONE model,
##   Treatment ~ BASE + JOINT + income:era + insurance:era + strata
## and the difference of the two log ratios of odds ratios (later era vs the
## earliest) is estimated from the same fits and Rubin-pooled:
##   delta = log ROR(income <$10k) - log ROR(Medicaid)
## exp(delta) is the ratio of the 2 RORs; 1 means the 2 associations moved alike.
## Also reported: the RORs from the combined model (to show they match the separate
## models), $10-25k vs Medicaid, and a D1 test that the income and Medicaid era
## contrasts are equal in every later era (COVID-19: Delta and Omicron jointly).
## Model-based variance (as printed in the main text) and person-clustered, from
## the same fits.
## Aggregates only. OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 ARM=covid NCOR=3 Rscript 03u_asym.R

L <- readLines("/home/jupyter/03o_r4_attenuation.R")
Sys.setenv(PART = "ASYM")
eval(parse(text = L[1:(grep("^## =+ PROBE", L)[1] - 1)]))
NCOR <- as.integer(Sys.getenv("NCOR", "3"))

fit_both <- function(f) {
  R <- mclapply(seq_len(M), function(k) {
    dk <- apply_imp(k); f2 <- f; environment(f2) <- environment()
    fk <- clogit(f2, data = dk, method = "efron")
    b <- coef(fk); Vm <- vcov(fk); Vc <- sandwich::vcovCL(fk, cluster = dk$person_id)
    ok <- Reduce(intersect, list(names(b)[!is.na(b)], rownames(Vm), rownames(Vc)))
    list(b = b[ok], Vm = Vm[ok, ok], Vc = Vc[ok, ok])
  }, mc.cores = NCOR)
  bad <- sapply(R, function(z) inherits(z, "try-error") || is.character(z))
  if (any(bad)) { print(unique(unlist(R[bad]))); stop("fits failed: ", sum(bad)) }
  CO <- lapply(R, `[[`, "b")
  list(model = pool_full(CO, lapply(R, `[[`, "Vm")), cluster = pool_full(CO, lapply(R, `[[`, "Vc")))
}
## D1 for linear contrasts C (rows named by p$nm order)
D1c <- function(p, C) {
  k <- nrow(C); q <- drop(C %*% p$qbar); U <- C %*% p$Ubar %*% t(C); Bs <- C %*% p$B %*% t(C)
  Ui <- solve(U); r1 <- (1 + 1 / p$m) * sum(diag(Bs %*% Ui)) / k
  stat <- as.numeric(t(q) %*% Ui %*% q) / (k * (1 + r1)); t_ <- k * (p$m - 1)
  df2 <- if (t_ > 4) 4 + (t_ - 4) * (1 + (1 - 2 / t_) / r1)^2 else t_ * (1 + 1 / k) * (1 + 1 / r1)^2 / 2
  c(F = stat, df1 = k, df2 = df2, p = pf(stat, k, df2, lower.tail = FALSE))
}
## era-specific log OR of ft: COVID-19 has the wave main effect in BASE (standard
## coding); influenza has no period main effect (lor_cv handles the indicator coding)
eras <- levels(factor(d[[ERA]]))
## Medicare: the reviewers noted it fell too (eTable 8), which a Medicaid-specific
## mechanism cannot explain; its ROR is reported beside Medicaid's
MEDICARE <- find_lev(DV[["ins"]], "^medicare$"); FOCV[["medicare"]] <- DV[["ins"]]
if (ARM == "covid") {
  lor <- function(p, ft, w) { cv <- cvec(p, ft)
    h <- intersect(c(paste0(ft, ":", ERA, w), paste0(ERA, w, ":", ft)), p$nm); cv[h] <- cv[h] + 1; cv }
  PAIRS <- list(c(eras[2], eras[1]), c(eras[3], eras[1]))
} else {
  lor <- function(p, ft, w) lor_cv(p, if (ft == MEDICARE) DV[["ins"]] else FOCV[[names(FOC)[FOC == ft]]], ft, ERA, w)
  PAIRS <- list(c("3_post", "1_pre"), c("2_pandemic", "1_pre"))
}
ror_cv <- function(p, ft, pr) lor(p, ft, pr[1]) - lor(p, ft, pr[2])

t0 <- Sys.time()
f <- fml(paste(BASE, "+", JOINT, "+", DV[["inc"]], ":", ERA, "+", DV[["ins"]], ":", ERA))
PP <- fit_both(f)
cat("fits done in", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "min\n")

rows <- list()
add <- function(...) rows[[length(rows) + 1]] <<- data.frame(..., row.names = NULL)
for (vt in names(PP)) {
  p <- PP[[vt]]
  for (pr in PAIRS) {
    lab <- paste0(pr[1], "/", pr[2])
    for (ft in c(FOC[c("inc10k", "inc25k", "medicaid")], MEDICARE)) {
      e <- ci_of(p, ror_cv(p, ft, pr))
      add(arm = ARM, variance = vt, quantity = "ROR (combined model)", term = ft, contrast = lab,
          est = exp(e[["est"]]), lo = exp(e[["lo"]]), hi = exp(e[["hi"]]), p = e[["p"]])
    }
    for (ft in FOC[c("inc10k", "inc25k")]) {
      e <- ci_of(p, ror_cv(p, ft, pr) - ror_cv(p, FOC[["medicaid"]], pr))
      add(arm = ARM, variance = vt, quantity = "ratio of RORs, income / Medicaid", term = ft, contrast = lab,
          est = exp(e[["est"]]), lo = exp(e[["lo"]]), hi = exp(e[["hi"]]), p = e[["p"]])
    }
  }
  ## joint test over the later eras (COVID-19: Delta and Omicron; influenza: pandemic and post)
  for (ft in FOC[c("inc10k", "inc25k")]) {
    C <- do.call(rbind, lapply(PAIRS, function(pr) ror_cv(p, ft, pr) - ror_cv(p, FOC[["medicaid"]], pr)))
    s <- D1c(p, C)
    add(arm = ARM, variance = vt, quantity = "D1: income and Medicaid era contrasts equal", term = ft,
        contrast = paste(sapply(PAIRS, paste, collapse = "/"), collapse = " & "),
        est = s[["F"]], lo = s[["df1"]], hi = s[["df2"]], p = s[["p"]])
  }
}
o <- do.call(rbind, rows)
write.csv(o, file.path(OUT, "asym_test.csv"), row.names = FALSE)
print(o, row.names = FALSE, digits = 3)
cat("DONE\n"); sink()
