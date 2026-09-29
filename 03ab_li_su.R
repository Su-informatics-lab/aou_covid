## 03ab_li_su.R -- two co-author requests (2026-09-29), both arms where noted.
##
## PART=NEST (Xiaochun Li): is the joint model better than each single-domain model?
##   For each of the 6 social items v, the single-domain model is BASE + v and the full
##   model is BASE + all 6 items; the two are nested. The test is the D1 statistic for
##   the other 5 items' coefficients in the full model, pooled over the 40 imputations
##   (Li, Raghunathan & Rubin; as used throughout the paper), with the median
##   per-imputation likelihood-ratio statistic beside it. For nested models a DeLong
##   test of the AUC difference has the wrong null distribution (Demler, Pencina &
##   D'Agostino, Stat Med 2012) and a regression test of the added terms is the test
##   to use (Vickers, Cronin & Begg, BMC Med Res Methodol 2011); the AUCs and their
##   difference are therefore reported descriptively, with DeLong standard errors
##   pooled by Rubin's rules, together with the matched-set C statistic (share of
##   case-control pairs within a stratum in which the case has the higher linear
##   predictor), which is what a conditional model estimates.
##   Reused controls make the DeLong variance too small; it is descriptive only.
##
## PART=XTAB (Jing Su, Figure 2A): overlap of income below $10 000 and Medicaid among
##   matched participants who reported income (observed values, no imputation):
##   distinct participants in each of the 4 cells, overall and among cases.
##
## PART=JOINT4 (Jing Su, Figure 2A; COVID-19 only): joint categories of income
##   below $10 000 and Medicaid against 1 reference ($35 000-99 999 and employer
##   insurance), as recommended by Knol & VanderWeele (Int J Epidemiol 2012).
##   The joint model plus an indicator J = income below $10 000 and Medicaid, with
##   income x wave, insurance x wave and J x wave:
##     OR(<$10k, employer)   = exp(b_inc10k)
##     OR($35-99k, Medicaid) = exp(b_medicaid)
##     OR(<$10k, Medicaid)   = exp(b_inc10k + b_medicaid + b_J)
##   in each wave (adding the wave interactions), and the Medicaid-vs-employer OR
##   within each income band, with its Omicron / pre-Delta ratio. Every cell is
##   audited: an estimate rests only on cells with more than 20 cases and more than
##   20 controls in every imputation.
##
## Aggregates only (counts of 20 or fewer print as "<=20").
## OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 ARM=covid PART=NEST NCOR=3 Rscript 03ab_li_su.R

L <- readLines("/home/jupyter/03o_r4_attenuation.R")
PART0 <- Sys.getenv("PART", "NEST")
Sys.setenv(PART = paste0("LISU_", PART0), OUTSUFFIX = "_lisu")
eval(parse(text = L[1:(grep("^## =+ PROBE", L)[1] - 1)]))
PART <- PART0
NCOR <- as.integer(Sys.getenv("NCOR", "3"))
M20 <- function(x) ifelse(x <= 20, "<=20", as.character(x))

fit_k <- function(f, k, prep = identity, lp = FALSE) {
  dk <- prep(apply_imp(k)); f2 <- f; environment(f2) <- environment()
  fk <- clogit(f2, data = dk, method = "efron")
  b <- coef(fk); Vm <- vcov(fk); Vc <- sandwich::vcovCL(fk, cluster = dk$person_id)
  ok <- Reduce(intersect, list(names(b)[!is.na(b)], rownames(Vm), rownames(Vc)))
  out <- list(b = b[ok], Vm = Vm[ok, ok], Vc = Vc[ok, ok], ll = fk$loglik[2], df = length(ok))
  if (lp) out$lp <- predict(fk, type = "lp", reference = "zero")
  out
}
pool2 <- function(R) { CO <- lapply(R, `[[`, "b")
  list(model = pool_full(CO, lapply(R, `[[`, "Vm")), cluster = pool_full(CO, lapply(R, `[[`, "Vc"))) }

## DeLong placement values from midranks (ties count one half)
place <- function(s, y) {
  r <- rank(s); n1 <- sum(y == 1); n0 <- sum(y == 0)
  v10 <- (r[y == 1] - rank(s[y == 1])) / n0
  v01 <- 1 - (r[y == 0] - rank(s[y == 0])) / n1
  list(auc = mean(v10), v10 = v10, v01 = v01, n1 = n1, n0 = n0)
}
dl_var <- function(a, b = a) cov(a$v10, b$v10) / a$n1 + cov(a$v01, b$v01) / a$n0
## matched-set C: case-control pairs within a stratum, case higher = 1, tie = 1/2
mset_c <- function(s, y, st) {
  num <- 0; den <- 0
  for (g in split(seq_along(s), st)) {
    ca <- s[g][y[g] == 1]; co <- s[g][y[g] == 0]
    if (!length(ca) || !length(co)) next
    cmp <- outer(ca, co, "-")
    num <- num + sum(cmp > 0) + 0.5 * sum(cmp == 0); den <- den + length(cmp)
  }
  num / den
}
rubin1 <- function(q, u) { m <- length(q); B <- var(q); Tv <- mean(u) + (1 + 1 / m) * B
  c(est = mean(q), lo = mean(q) - 1.96 * sqrt(Tv), hi = mean(q) + 1.96 * sqrt(Tv)) }

t0 <- Sys.time()
if (PART == "NEST") {
  f_full <- fml(paste(BASE, "+", JOINT))
  f_base <- fml(BASE)
  y <- d$Treatment; st <- d$.s
  RF <- mclapply(seq_len(M), function(k) fit_k(f_full, k, lp = TRUE), mc.cores = NCOR)
  RB <- mclapply(seq_len(M), function(k) fit_k(f_base, k, lp = TRUE), mc.cores = NCOR)
  PF <- pool2(RF)
  cat("full and base fits done in", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "min\n")
  auc_rows <- function(lab, RA) {
    ## AUC of this model and of the full model, their difference, and the matched-set C
    A <- lapply(seq_len(M), function(k) {
      pa <- place(RA[[k]]$lp, y); pf <- place(RF[[k]]$lp, y)
      c(auc = pa$auc, var = dl_var(pa), auc_full = pf$auc, var_full = dl_var(pf),
        dif = pf$auc - pa$auc, var_dif = dl_var(pf) + dl_var(pa) - 2 * dl_var(pf, pa),
        cms = mset_c(RA[[k]]$lp, y, st), cms_full = mset_c(RF[[k]]$lp, y, st))
    })
    A <- do.call(rbind, A)
    a <- rubin1(A[, "auc"], A[, "var"]); af <- rubin1(A[, "auc_full"], A[, "var_full"])
    dd <- rubin1(A[, "dif"], A[, "var_dif"])
    data.frame(model = lab, auc = a[["est"]], auc_lo = a[["lo"]], auc_hi = a[["hi"]],
               auc_full = af[["est"]], dauc = dd[["est"]], dauc_lo = dd[["lo"]], dauc_hi = dd[["hi"]],
               cms = mean(A[, "cms"]), cms_full = mean(A[, "cms_full"]), row.names = NULL)
  }
  rows <- list(); arows <- list(auc_rows("base (no social item)", RB))
  for (v in DOM) {
    f_a <- fml(paste(BASE, "+", v))
    RA <- mclapply(seq_len(M), function(k) fit_k(f_a, k, lp = TRUE), mc.cores = NCOR)
    others <- setdiff(DOM, v)
    lr <- sapply(seq_len(M), function(k) 2 * (RF[[k]]$ll - RA[[k]]$ll))
    dfk <- sapply(seq_len(M), function(k) RF[[k]]$df - RA[[k]]$df)
    for (vt in c("model", "cluster")) {
      p <- PF[[vt]]
      keep <- p$nm[sapply(p$nm, function(z) any(sapply(others, function(o) startsWith(z, o) &&
                !any(startsWith(z, DOM[nchar(DOM) > nchar(o) & startsWith(DOM, o)])))))]
      s <- D1(p, keep)
      rows[[length(rows) + 1]] <- data.frame(arm = ARM, item = v, variance = vt, terms_tested = length(keep),
        D1_F = s[["F"]], df1 = s[["df1"]], df2 = s[["df2"]], p = s[["p"]],
        LR_median = median(lr), LR_df = median(dfk), row.names = NULL)
    }
    arows[[length(arows) + 1]] <- auc_rows(paste("base +", v), RA)
    cat("  ", v, "done |", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "min\n")
  }
  o <- do.call(rbind, rows); a <- do.call(rbind, arows); a$arm <- ARM
  write.csv(o, file.path(OUT, paste0("nest_tests_", ARM, ".csv")), row.names = FALSE)
  write.csv(a, file.path(OUT, paste0("nest_auc_", ARM, ".csv")), row.names = FALSE)
  print(o, row.names = FALSE, digits = 4); print(a, row.names = FALSE, digits = 4)
}

if (PART == "XTAB") {
  inc <- as.character(d[[DV[["inc"]]]]); ins <- as.character(d[[DV[["ins"]]]])
  L10 <- sub(DV[["inc"]], "", FOC[["inc10k"]]); MCD <- sub(DV[["ins"]], "", FOC[["medicaid"]])
  P <- unique(data.frame(person_id = d$person_id, inc = inc, ins = ins, case = d$Treatment))
  one <- function(z, lab) {
    z <- z[!duplicated(z$person_id), ]
    obs <- z[!is.na(z$inc) & !grepl("missing|skip|prefer|unknown", z$inc, ignore.case = TRUE), ]
    lo <- obs$inc == L10; md <- !is.na(obs$ins) & obs$ins == MCD
    data.frame(arm = ARM, group = lab, reported_income = M20(nrow(obs)),
               below10k_and_medicaid = M20(sum(lo & md)), below10k_not_medicaid = M20(sum(lo & !md)),
               medicaid_not_below10k = M20(sum(!lo & md)), neither = M20(sum(!lo & !md)),
               income_not_reported = M20(nrow(z) - nrow(obs)), row.names = NULL)
  }
  o <- rbind(one(P, "all matched participants"), one(P[P$case == 1, ], "cases"),
             one(P[P$case == 0 & !(P$person_id %in% P$person_id[P$case == 1]), ], "controls only"))
  cat("income levels:", paste(sort(unique(inc)), collapse = ", "), "| insurance levels:", paste(sort(unique(ins)), collapse = ", "), "\n")
  write.csv(o, file.path(OUT, paste0("xtab_", ARM, ".csv")), row.names = FALSE)
  print(o, row.names = FALSE)
}

if (PART == "JOINT4") {
  stopifnot(ARM == "covid")
  L10 <- sub(DV[["inc"]], "", FOC[["inc10k"]]); MCD <- sub(DV[["ins"]], "", FOC[["medicaid"]])
  EMP <- levels(droplevels(factor(d0[[DV[["ins"]]]])))[1]; REFI <- levels(droplevels(factor(d0[[DV[["inc"]]]])))[1]
  cat("reference income:", REFI, "| reference insurance:", EMP, "\n")
  addJ <- function(dk) { dk$J <- as.integer(as.character(dk[[DV[["inc"]]]]) == L10 & as.character(dk[[DV[["ins"]]]]) == MCD); dk }
  ## cell audit over imputations: cases and controls per joint cell per wave
  cells <- do.call(rbind, lapply(seq_len(M), function(k) {
    dk <- apply_imp(k); ic <- as.character(dk[[DV[["inc"]]]]); sc <- as.character(dk[[DV[["ins"]]]])
    g <- ifelse(ic == L10 & sc == MCD, "low_mcd", ifelse(ic == L10 & sc == EMP, "low_emp",
         ifelse(ic == REFI & sc == MCD, "ref_mcd", ifelse(ic == REFI & sc == EMP, "ref_emp", NA))))
    tb <- as.data.frame(table(cell = g, era = dk[[ERA]], case = dk$Treatment))
    tb$k <- k; tb }))
  mins <- aggregate(Freq ~ cell + era + case, data = cells, FUN = min)
  mins$shown <- M20(mins$Freq)
  print(mins[, c("cell", "era", "case", "shown")], row.names = FALSE)
  ok_cell <- function(cl, w) { x <- mins$Freq[mins$cell == cl & mins$era == w]; length(x) == 2 && all(x > 20) }
  f <- fml(paste(BASE, "+", JOINT, "+ J +", DV[["inc"]], ":", ERA, "+", DV[["ins"]], ":", ERA, "+ J:", ERA))
  R <- mclapply(seq_len(M), function(k) fit_k(f, k, prep = addJ), mc.cores = NCOR)
  PP <- pool2(R)
  cat("fits done in", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "min\n")
  eras <- levels(factor(d[[ERA]]))
  wv <- function(p, term, w) { cv <- cvec(p, term)
    if (w != eras[1]) { h <- intersect(c(paste0(term, ":", ERA, w), paste0(ERA, w, ":", term)), p$nm); cv[h] <- cv[h] + 1 }
    cv }
  rows <- list()
  for (vt in names(PP)) {
    p <- PP[[vt]]
    for (w in eras) {
      cm <- list("<$10k, employer" = wv(p, FOC[["inc10k"]], w),
                 "$35-99k, Medicaid" = wv(p, FOC[["medicaid"]], w),
                 "<$10k, Medicaid" = wv(p, FOC[["inc10k"]], w) + wv(p, FOC[["medicaid"]], w) + wv(p, "J", w),
                 "Medicaid vs employer, within <$10k" = wv(p, FOC[["medicaid"]], w) + wv(p, "J", w),
                 "Medicaid vs employer, within $35-99k" = wv(p, FOC[["medicaid"]], w),
                 "multiplicative interaction" = wv(p, "J", w),
                 "<$10k vs $35-99k, within Medicaid" = wv(p, FOC[["inc10k"]], w) + wv(p, "J", w))
      need <- list(c("low_emp", "ref_emp"), c("ref_mcd", "ref_emp"), c("low_mcd", "ref_emp"),
                   c("low_mcd", "low_emp"), c("ref_mcd", "ref_emp"), c("low_mcd", "low_emp", "ref_mcd", "ref_emp"),
                   c("low_mcd", "ref_mcd"))
      for (i in seq_along(cm)) {
        shown <- all(sapply(need[[i]], ok_cell, w = w))
        e <- ci_of(p, cm[[i]])
        rows[[length(rows) + 1]] <- data.frame(arm = ARM, variance = vt, era = w, quantity = names(cm)[i],
          or = if (shown) exp(e[["est"]]) else NA, lo = if (shown) exp(e[["lo"]]) else NA,
          hi = if (shown) exp(e[["hi"]]) else NA, p = if (shown) e[["p"]] else NA,
          note = if (shown) "" else "withheld: a cell holds 20 or fewer", row.names = NULL)
      }
    }
    for (w in eras[-1]) {
      cv <- wv(p, FOC[["inc10k"]], w) - wv(p, FOC[["inc10k"]], eras[1]) + wv(p, "J", w) - wv(p, "J", eras[1])
      shown <- all(sapply(c("low_mcd", "ref_mcd"), function(cl) ok_cell(cl, w) && ok_cell(cl, eras[1])))
      e <- ci_of(p, cv)
      rows[[length(rows) + 1]] <- data.frame(arm = ARM, variance = vt, era = paste0(w, "/", eras[1]),
        quantity = "income <$10k ROR, within Medicaid", or = if (shown) exp(e[["est"]]) else NA,
        lo = if (shown) exp(e[["lo"]]) else NA, hi = if (shown) exp(e[["hi"]]) else NA,
        p = if (shown) e[["p"]] else NA, note = if (shown) "" else "withheld", row.names = NULL)
      for (lab in c("within <$10k", "within $35-99k")) {
        cv <- (wv(p, FOC[["medicaid"]], w) - wv(p, FOC[["medicaid"]], eras[1]))
        if (lab == "within <$10k") cv <- cv + wv(p, "J", w) - wv(p, "J", eras[1])
        shown <- all(sapply(if (lab == "within <$10k") c("low_mcd", "low_emp") else c("ref_mcd", "ref_emp"),
                            function(cl) ok_cell(cl, w) && ok_cell(cl, eras[1])))
        e <- ci_of(p, cv)
        rows[[length(rows) + 1]] <- data.frame(arm = ARM, variance = vt, era = paste0(w, "/", eras[1]),
          quantity = paste("Medicaid ROR,", lab), or = if (shown) exp(e[["est"]]) else NA,
          lo = if (shown) exp(e[["lo"]]) else NA, hi = if (shown) exp(e[["hi"]]) else NA,
          p = if (shown) e[["p"]] else NA, note = if (shown) "" else "withheld", row.names = NULL)
      }
    }
  }
  o <- do.call(rbind, rows)
  write.csv(o, file.path(OUT, "joint4_covid.csv"), row.names = FALSE)
  write.csv(mins[, c("cell", "era", "case", "shown")], file.path(OUT, "joint4_cells_covid.csv"), row.names = FALSE)
  print(o, row.names = FALSE, digits = 3)
}
cat("DONE", PART, round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "min\n"); sink()
