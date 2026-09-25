## 03q_mi_era.R -- does the imputation model flatten the era contrasts?
##
## GPT-6 R2b-10 (2026-09-24). The primary imputation models carry case status and
## era as main effects only: COVID-19 (03d_mi40_shape.R) has Treatment and f.wave,
## influenza (03f_flu_mi40.R) has ever_case and n_seasons and no period at all. An
## imputed income therefore inherits one income-case association for every era,
## which pulls an income x era test toward the null, while insurance is observed
## and is not pulled. The thesis contrast (insurance changed, income did not) is
## exactly the asymmetry that could produce.
##
## This script
##   PART=IMPUTE  refits the imputation model with case-by-era indicators added,
##                everything else reproduced by evaluating the original script's
##                construction code (output directory redirected, so the frozen
##                imputations are untouched):
##                  COVID-19   cw_<wave> = case whose index date is in <wave>
##                             (controls are 0 by construction; a COVID-19 case is
##                             never a control, checked)
##                  influenza  in_<period> = person contributes a row in <period>,
##                             case_<period> = person is a case in <period>;
##                             ever_case is dropped because the case_ columns
##                             carry it
##                m = 40 as 4 parallel mice runs of 10 (seeds 20260924 + 1..4).
##   PART=REFIT   fits the era models with the SAME code on (a) the frozen
##                imputations, (b) the new ones, and (c) complete cases, so any
##                difference is the imputation model and nothing else:
##                  joint + income:era and joint + insurance:era, D1 on the
##                  interaction block, era-specific AORs and ratios of ORs for
##                  income <$10k, $10-25k, Medicaid; influenza also the
##                  within-period refits used in the main text.
## Aggregates only. Run with single-threaded BLAS:
##   OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 ARM=covid PART=IMPUTE Rscript 03q_mi_era.R

suppressPackageStartupMessages({library(survival); library(sandwich); library(mice); library(parallel)})
ARM  <- Sys.getenv("ARM", "covid"); QPART <- Sys.getenv("PART", "IMPUTE")
NEWDIR <- if (ARM == "covid") "/home/jupyter/mi40c" else "/home/jupyter/flu_mi40c"
OLDIMP <- if (ARM == "covid") "/home/jupyter/mi40b/imputations.rds" else "/home/jupyter/flu_mi40/imputations.rds"
NEWIMP <- file.path(NEWDIR, "imputations.rds")
dir.create(NEWDIR, showWarnings = FALSE)

## ============================================================ IMPUTE
if (QPART == "IMPUTE") {
  if (ARM == "covid") {
    L <- readLines("/home/jupyter/03d_mi40_shape.R")
    L <- L[1:(grep("^IMPS_LEG <- run_mice", L)[1] - 1)]
    L <- gsub('"/home/jupyter/mi40b"', paste0('"', NEWDIR, '"'), L, fixed = TRUE)
    eval(parse(text = L))
    cs <- d[d$Treatment == 1, c("person_id", "f.wave")]
    stopifnot(!any(duplicated(cs$person_id)))
    w <- as.character(cs$f.wave[match(P$person_id, cs$person_id)])
    for (lv in levels(d$f.wave)[-1]) P[[paste0("cw_", lv)]] <- as.integer(!is.na(w) & w == lv)
    NEWC <- grep("^cw_", names(P), value = TRUE)
    cat("\n== 03q: case-by-wave indicators added:", NEWC, "\n")
    print(sapply(P[NEWC], sum))
    cat("check -- cases by wave in d:\n"); print(table(cs$f.wave))
    dat <- P[, c(COLS_CON, NEWC)]; meth <- make_meth(dat)
    IMPV <- IMP; SEED0 <- 20260924
  } else {
    L <- readLines("/home/jupyter/03f_flu_mi40.R")
    L <- L[1:(grep("^t0 <- Sys.time\\(\\)", L)[1] - 1)]
    L <- gsub('"/home/jupyter/flu_mi40"', paste0('"', NEWDIR, '"'), L, fixed = TRUE)
    eval(parse(text = L))
    per <- as.character(m$period)
    for (pp in levels(m$period)) {
      P[[paste0("in_", pp)]]   <- as.integer(P$person_id %in% m$person_id[per == pp])
      P[[paste0("case_", pp)]] <- as.integer(P$person_id %in% m$person_id[per == pp & m$Treatment == 1])
    }
    NEWC <- grep("^(in|case)_", names(P), value = TRUE)
    cat("\n== 03q: period indicators added:", NEWC, "\n"); print(sapply(P[NEWC], sum))
    dat <- P[, setdiff(names(P), c("person_id", drop_const, "ever_case"))]
    meth <- make.method(dat); meth[] <- ""
    meth["income"] <- meth["education"] <- meth["employment"] <- meth["housing"] <- "polyreg"
    meth["housing_stability"] <- "logreg"
    IMPV <- IMP; SEED0 <- 20260924
  }
  cat("imputation predictors:", ncol(dat), "columns\n")
  t0 <- Sys.time()
  ch <- mclapply(1:4, function(j) {
    mi <- mice(dat, m = 10, maxit = 5, method = meth, predictorMatrix = make.predictorMatrix(dat),
               printFlag = FALSE, seed = SEED0 + j)
    list(imps = lapply(1:10, function(k) complete(mi, k)[, IMPV]), ev = mi$loggedEvents)
  }, mc.cores = 4)
  bad <- sapply(ch, function(z) inherits(z, "try-error")); if (any(bad)) { print(ch[bad]); stop("mice chunk failed") }
  cat("mice done in", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "min\n")
  ev <- do.call(rbind, lapply(ch, `[[`, "ev"))
  cat("logged events:", if (is.null(ev)) 0 else nrow(ev), "\n"); if (!is.null(ev)) print(unique(ev[, c("meth", "out")]))
  IMPS <- unlist(lapply(ch, `[[`, "imps"), recursive = FALSE); stopifnot(length(IMPS) == 40)
  saveRDS(list(person_id = P$person_id, imps = IMPS), NEWIMP)
  cat("written", NEWIMP, "\nDONE IMPUTE\n"); sink()
}

## ============================================================ REFIT
if (QPART == "REFIT") {
  L0 <- readLines("/home/jupyter/03o_r4_attenuation.R")
  L0 <- L0[1:(grep("^## =+ PROBE", L0)[1] - 1)]
  rows <- list()
  add <- function(...) rows[[length(rows) + 1]] <<- data.frame(..., row.names = NULL)
  era_terms <- function(p, v) grep(paste0("^", v, ".*:", ERA, "|^", ERA, ".*:", v), p$nm, value = TRUE)
  ## era-specific log OR of ft, COVID-19 (wave main effect in BASE, standard coding)
  cv_covid <- function(p, ft, w) { cv <- cvec(p, ft)
    h <- intersect(c(paste0(ft, ":", ERA, w), paste0(ERA, w, ":", ft)), p$nm); cv[h] <- 1; cv }
  run_one <- function(tag, impfile) {
    L <- gsub(OLDIMP, impfile, L0, fixed = TRUE)
    Sys.setenv(PART = paste0("Q03q_", tag))
    eval(parse(text = L), envir = globalenv())
    cat("\n######## imputations:", tag, "(", impfile, ")\n")
    for (v in c(DV[["inc"]], DV[["ins"]])) {
      p <- fit_pool(fml(paste(BASE, "+", JOINT, "+", v, ":", ERA)), paste(tag, v, "x era"))
      ix <- era_terms(p, v); s <- D1(p, ix)
      add(arm = ARM, imp = tag, model = paste(v, "x era"), term = v, contrast = "D1 interaction block",
          est = s[["F"]], lo = s[["df1"]], hi = NA, p = s[["p"]])
      fts <- FOC[c("inc10k", "inc25k", "medicaid")]; fts <- fts[startsWith(fts, v)]
      for (ft in fts) {
        if (ARM == "covid") {
          eras <- levels(factor(d[[ERA]]))
          for (w in eras) { e <- ci_of(p, cv_covid(p, ft, w))
            add(arm = ARM, imp = tag, model = paste(v, "x era"), term = ft, contrast = paste("OR", w),
                est = exp(e[["est"]]), lo = exp(e[["lo"]]), hi = exp(e[["hi"]]), p = e[["p"]]) }
          for (w in eras[-1]) { e <- ci_of(p, cv_covid(p, ft, w) - cv_covid(p, ft, eras[1]))
            add(arm = ARM, imp = tag, model = paste(v, "x era"), term = ft, contrast = paste0("ROR ", w, "/", eras[1]),
                est = exp(e[["est"]]), lo = exp(e[["lo"]]), hi = exp(e[["hi"]]), p = e[["p"]]) }
        } else {
          for (z in d_flu(p, v)) if (z$term == ft)
            add(arm = ARM, imp = tag, model = paste(v, "x era"), term = ft, contrast = z$contrast,
                est = z$ror, lo = z$lo, hi = z$hi, p = z$p)
        }
      }
    }
    if (ARM == "flu") for (w in c("1_pre", "2_pandemic", "3_post")) {
      p <- fit_pool(fml(paste(BASE, "+", JOINT)), paste(tag, "within", w), keep_rows = function(dk) dk[[ERA]] == w)
      for (ft in FOC[c("inc10k", "medicaid")]) { e <- ci_of(p, cvec(p, ft))
        add(arm = ARM, imp = tag, model = paste("within-period refit", w), term = ft, contrast = paste("OR", w),
            est = exp(e[["est"]]), lo = exp(e[["lo"]]), hi = exp(e[["hi"]]), p = e[["p"]]) }
    }
    sink()
  }
  run_one("frozen", OLDIMP)
  run_one("case_x_era", NEWIMP)

  ## complete cases on all five imputed items (original codings, "Missing" rows dropped)
  cat("\n######## complete cases\n")
  ok <- Reduce(`&`, lapply(IMPV, function(v) as.character(d[[v]]) != "Missing"))
  dc <- post_imp(d)[ok, ]
  for (v in IMPV) if (is.factor(dc[[v]])) dc[[v]] <- droplevels(dc[[v]])
  cs_ok <- dc$.s[dc$Treatment == 1]; dc <- dc[dc$.s %in% cs_ok, ]
  cat("complete-case cases", sum(dc$Treatment == 1), "controls", sum(dc$Treatment == 0), "\n")
  add(arm = ARM, imp = "complete_case", model = "sample", term = "cases", contrast = "n",
      est = sum(dc$Treatment == 1), lo = sum(dc$Treatment == 0), hi = NA, p = NA)
  for (v in c(DV[["inc"]], DV[["ins"]])) {
    fk <- clogit(fml(paste(BASE, "+", JOINT, "+", v, ":", ERA)), data = dc, method = "efron")
    b <- coef(fk); keep <- names(b)[!is.na(b)]; V <- sandwich::vcovCL(fk, cluster = dc$person_id)[keep, keep]
    p <- list(qbar = b[keep], Tv = V, nm = keep)
    ix <- era_terms(p, v); W <- as.numeric(t(b[ix]) %*% solve(V[ix, ix]) %*% b[ix])
    add(arm = ARM, imp = "complete_case", model = paste(v, "x era"), term = v, contrast = "Wald interaction block",
        est = W, lo = length(ix), hi = NA, p = pchisq(W, length(ix), lower.tail = FALSE))
    fts <- FOC[c("inc10k", "inc25k", "medicaid")]; fts <- fts[startsWith(fts, v)]
    for (ft in fts) {
      if (ARM == "covid") {
        eras <- levels(factor(d[[ERA]]))
        for (w in eras) { e <- ci_of(p, cv_covid(p, ft, w))
          add(arm = ARM, imp = "complete_case", model = paste(v, "x era"), term = ft, contrast = paste("OR", w),
              est = exp(e[["est"]]), lo = exp(e[["lo"]]), hi = exp(e[["hi"]]), p = e[["p"]]) }
        e <- ci_of(p, cv_covid(p, ft, eras[3]) - cv_covid(p, ft, eras[1]))
        add(arm = ARM, imp = "complete_case", model = paste(v, "x era"), term = ft, contrast = paste0("ROR ", eras[3], "/", eras[1]),
            est = exp(e[["est"]]), lo = exp(e[["lo"]]), hi = exp(e[["hi"]]), p = e[["p"]])
      } else {
        for (z in d_flu(p, v)) if (z$term == ft && z$contrast %in% c("OR in 1_pre", "OR in 3_post", "3_post/1_pre"))
          add(arm = ARM, imp = "complete_case", model = paste(v, "x era"), term = ft, contrast = z$contrast,
              est = z$ror, lo = z$lo, hi = z$hi, p = z$p)
      }
    }
  }
  out <- do.call(rbind, rows)
  write.csv(out, file.path(NEWDIR, paste0("era_refit", Sys.getenv("OUTSUFFIX", ""), ".csv")), row.names = FALSE)
  print(out, row.names = FALSE, digits = 3)
  cat("DONE REFIT\n")
}
