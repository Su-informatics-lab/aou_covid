## 03o_r4_attenuation.R -- R4: the attenuation paradigm and the preparedness
## questions, on the frozen imputations. One script, both arms.
##
## Runs on the All of Us Researcher Workbench. Nothing person-level leaves it;
## every count written out is screened at 20.
##
##   ARM=covid  COVID-19 workspace (CDR v7), imputations /home/jupyter/mi40b,
##              education merged as in 03n R2 (the v24 primary)
##   ARM=flu    influenza workspace su_lab_v9 (CDR v9), imputations
##              /home/jupyter/flu_mi40
##
##   PART=PROBE  print the variables, levels and focal terms, fit nothing heavy
##   PART=AB     A: percent attenuation, domain alone -> all six jointly, with
##                  cluster-bootstrap CIs (matched sets resampled within each
##                  imputation; percentile intervals from the pooled draws)
##               B: KHB rescaling check and order-invariant decomposition
##                  (Karlson, Holm & Breen 2012). The KHB total effect is
##                  b_full + theta %*% b_Z, where theta is the within-stratum OLS
##                  of the other domains on the focal factor and the base
##                  covariates. That is an exact reparameterization of the full
##                  conditional likelihood, so it needs no extra clogit fit.
##   PART=CDEF   C: era-specific attenuation (domain alone and joint, by era)
##               D: no-narrowing bounds, ratio of odds ratios later/earlier era
##               E: COVID only -- the emergency paid sick leave window. The
##                  pre-Delta wave is split at 1 January 2021 (EPSL in force
##                  1 April - 31 December 2020); X x window for income,
##                  employment, insurance
##               F: flu only -- 2022-23 vs 2023-24 around the Medicaid unwinding
##                  (disenrollment from 1 April 2023); insurance and income x season
##
## Attenuation is on the log-odds scale, 100 x (b_alone - b_joint) / b_alone
## (Stringhini et al, JAMA 2010); the excess-odds version (OR_a - OR_j)/(OR_a - 1)
## is reported beside it. A negative or >100% value is printed as computed.
##
## Output: /home/jupyter/r4_<arm>/{log_<PART>.txt, *.csv}

suppressPackageStartupMessages({library(survival); library(sandwich); library(parallel)})
ARM  <- Sys.getenv("ARM", "covid")
PART <- Sys.getenv("PART", "PROBE")
BPER <- as.integer(Sys.getenv("BPER", "25"))          # bootstrap draws per imputation
NCOR <- as.integer(Sys.getenv("NCOR", max(1, detectCores() - 1)))
MIN_CELL <- 20
VARTYPE <- Sys.getenv("VARTYPE", "cluster")   # "cluster" (person) or "model"; no fallback
stopifnot(VARTYPE %in% c("cluster", "model"))
OUT <- file.path("/home/jupyter", paste0("r4_", ARM, Sys.getenv("OUTSUFFIX", "")))
dir.create(OUT, showWarnings = FALSE)
sink(file.path(OUT, paste0("log_", PART, ".txt")), split = TRUE)
cat("VARTYPE", VARTYPE, "| ARM", ARM, "| PART", PART, "| BPER", BPER, "| cores", NCOR, "\n")
set.seed(20260923)

## ======================================================== arm adapters
if (ARM == "covid") {
  BUCKET <- "/home/jupyter/workspace/rw-migration-aou-rw-46c7ae9e/data/covid_sdoh"
  X  <- readRDS(file.path(BUCKET, "aou_v7_5domain", "joint_model_inputs.rds"))
  d  <- X$df
  IM <- readRDS("/home/jupyter/mi40b/imputations.rds")
  S  <- "stratum"; BASE <- X$base_rhs; ERA <- "f.wave"
  DOM <- c("f.insurance", "f.income", "f.education", "f.employment", "f.housing", "f.housing_stability")
  RACE <- "f.race"
  lev_never <- grep("never", levels(d$f.education), ignore.case = TRUE, value = TRUE)
  lev_below <- grep("below", levels(d$f.education), ignore.case = TRUE, value = TRUE)
  post_imp <- function(dk) {
    z <- as.character(dk$f.education); z[z == lev_never] <- lev_below
    dk$f.education <- factor(z, levels = setdiff(levels(dk$f.education), lev_never)); dk
  }
} else {
  FLU <- "/home/jupyter/flu"
  d <- read.csv(file.path(FLU, "07_matched_cohort.csv"), stringsAsFactors = FALSE)
  CH <- c("Myocardial_Infarction","Congestive_Heart_Failure","Peripheral_Vascular_Disease",
   "Cerebrovascular_Disease","Dementia","Chronic_Pulmonary_Disease","Rheumatic_Disease",
   "Peptic_Ulcer_Disease","Liver_Disease_Mild","Liver_Disease_Moderate_Severe",
   "Diabetes_without_Chronic_Complications","Diabetes_with_Chronic_Complications",
   "Hemiplegia_Paraplegia","Renal_Disease_Mild_Moderate","Renal_Disease_Severe","HIV",
   "Metastatic_Solid_Tumor","Malignancy","AIDS")
  rl <- function(x, r) relevel(factor(x), ref = r)
  d$income <- rl(d$income, "35k_100k"); d$employment <- rl(d$employment, "Employed")
  d$education <- rl(d$education, "GED_or_College"); d$housing <- rl(d$housing, "Own")
  d$housing_stability <- rl(d$housing_stability, "Stable")
  d$insurance_type <- rl(d$insurance_type, "Employer")
  d$age_group <- rl(d$age_group, "18-44"); d$race <- rl(d$race, "White")
  d$sex_at_birth <- rl(d$sex_at_birth, "Female")
  d$ethnicity <- rl(d$ethnicity, "Not Hispanic or Latino")
  d$period <- rl(factor(d$period), "3_post")
  IM <- readRDS("/home/jupyter/flu_mi40/imputations.rds")
  S  <- "subclass"; ERA <- "period"; RACE <- "race"
  BASE <- paste(c("sex_at_birth", "race", "ethnicity", "age_group", CH), collapse = " + ")
  DOM <- c("insurance_type", "income", "employment", "education", "housing", "housing_stability")
  post_imp <- identity
}
IMPS <- IM$imps; M <- length(IMPS); IMPV <- names(IMPS[[1]])
idx  <- match(d$person_id, IM$person_id); stopifnot(!any(is.na(idx)))
apply_imp <- function(k) { dk <- d; for (v in IMPV) dk[[v]] <- IMPS[[k]][[v]][idx]; post_imp(dk) }
d$.s <- d[[S]]
JOINT <- paste(DOM, collapse = " + ")
fml <- function(rhs) as.formula(paste("Treatment ~", rhs, "+ strata(.s)"))

## focal levels, located by pattern so the two arms' labels need not match
d0 <- apply_imp(1)
find_lev <- function(v, pat) { l <- grep(pat, levels(droplevels(factor(d0[[v]]))), value = TRUE, ignore.case = TRUE)
  if (length(l) != 1) stop("focal level for ", v, " / ", pat, " matched: ", paste(l, collapse = ","))
  paste0(v, l) }
## domains by name, not position: the two arms order DOM differently
dv <- function(p) { h <- grep(p, DOM, value = TRUE); stopifnot(length(h) == 1); h }
DV <- c(ins = dv("insurance"), inc = dv("income"), edu = dv("education"),
        emp = dv("employment"), hou = dv("housing$"))
FOC <- c(medicaid = find_lev(DV[["ins"]], "^medicaid$"),
         inc10k   = find_lev(DV[["inc"]], "^less_10k$"),
         inc25k   = find_lev(DV[["inc"]], "^10k_25k$"),
         unemp    = find_lev(DV[["emp"]], "^unemployed$"),
         rent     = find_lev(DV[["hou"]], "^rent$"),
         edu      = find_lev(DV[["edu"]], "below"))
BLACK <- find_lev(RACE, "black")
## the domain each focal term belongs to, by longest prefix (f.housing vs f.housing_stability)
FOCV <- sapply(FOC, function(ft) DOM[which.max(sapply(DOM, function(v) startsWith(ft, v) * nchar(v)))])
cat("observations", nrow(d), "| persons", length(unique(d$person_id)), "| strata", length(unique(d$.s)),
    "| cases", sum(d$Treatment == 1), "| imputations", M, "\n")
cat("focal terms:", paste(names(FOC), FOC, sep = "=", collapse = "; "), "| race:", BLACK, "\n")
cat("era levels:", levels(factor(d[[ERA]])), "\n")

## ======================================================== shared machinery
pool_full <- function(CO, VA) {
  nm <- Reduce(intersect, lapply(CO, names)); Q <- sapply(CO, function(z) z[nm])
  Ubar <- Reduce(`+`, lapply(VA, function(v) v[nm, nm])) / length(VA)
  B <- if (length(VA) > 1) stats::cov(t(Q)) else Ubar * 0
  list(qbar = rowMeans(Q), Ubar = Ubar, B = B, Tv = Ubar + (1 + 1 / length(VA)) * B, m = length(VA), nm = nm)
}
D1 <- function(p, keep) {
  k <- length(keep); q <- p$qbar[keep]; U <- p$Ubar[keep, keep, drop = FALSE]; Bs <- p$B[keep, keep, drop = FALSE]
  Ui <- tryCatch(solve(U), error = function(e) MASS::ginv(U))
  r1 <- (1 + 1 / p$m) * sum(diag(Bs %*% Ui)) / k
  stat <- as.numeric(t(q) %*% Ui %*% q) / (k * (1 + r1)); t_ <- k * (p$m - 1)
  df2 <- if (t_ > 4) 4 + (t_ - 4) * (1 + (1 - 2 / t_) / r1)^2 else t_ * (1 + 1 / k) * (1 + 1 / r1)^2 / 2
  c(F = stat, df1 = k, df2 = df2, p = pf(stat, k, df2, lower.tail = FALSE))
}
coef_only <- function(f, dk) {
  fk <- tryCatch(clogit(f, data = dk, method = "efron"), error = function(e) NULL)
  if (is.null(fk)) return(NULL); b <- coef(fk); b[!is.na(b)]
}
fit_pool <- function(f, label, keep_rows = NULL, prep = identity) {
  CO <- VA <- list(); fails <- 0
  for (k in seq_len(M)) {
    dk <- prep(apply_imp(k)); if (!is.null(keep_rows)) dk <- dk[keep_rows(dk), ]
    ## the formula must see the local dk, or vcovCL cannot rebuild the model frame;
    ## until 2026-09-24 a tryCatch here fell back to vcov() silently (every fit did).
    f2 <- f; environment(f2) <- environment()
    fk <- tryCatch(clogit(f2, data = dk, method = "efron"), error = function(e) NULL)
    if (is.null(fk)) { fails <- fails + 1; next }
    b <- coef(fk)
    V <- if (VARTYPE == "cluster") sandwich::vcovCL(fk, cluster = dk$person_id) else vcov(fk)
    ok <- intersect(names(b)[!is.na(b)], rownames(V)); if (length(ok) < 2) { fails <- fails + 1; next }
    CO[[length(CO) + 1]] <- b[ok]; VA[[length(VA) + 1]] <- V[ok, ok, drop = FALSE]
  }
  cat(sprintf("  %-46s fitted %d of %d | failures %d\n", label, length(CO), M, fails))
  if (length(CO) < 2) return(NULL); pool_full(CO, VA)
}
ci_of <- function(p, cv) { est <- sum(cv * p$qbar); s <- sqrt(drop(t(cv) %*% p$Tv %*% cv))
  c(est = est, lo = est - 1.96 * s, hi = est + 1.96 * s, p = 2 * pnorm(-abs(est / s))) }
cvec <- function(p, terms) { cv <- setNames(rep(0, length(p$nm)), p$nm); cv[intersect(terms, p$nm)] <- 1; cv }
screen <- function(x) ifelse(x < MIN_CELL, NA, x)
## Log odds ratio of focal level ft (of factor v) against v's reference level,
## in period w of a within-stratum-constant period variable pv, from a model
## that has v and v:pv but no pv main effect. R then codes v by INDICATORS in
## the interaction (removing v from v:pv leaves pv, which is not in the model),
## so there is a ref:pv column and the contrast is main + int[ft:w] - int[ref:w];
## a column absorbed by the strata carries 0. (v1 of this helper omitted the
## ref:w term and printed wrong period contrasts for influenza; found and
## corrected 2026-09-23 by checking the fully interacted model against the
## within-period refits.)
lor_cv <- function(p, v, ft, pv, w) {
  ref <- paste0(v, levels(droplevels(factor(d0[[v]])))[1])
  nm <- function(a) intersect(c(paste0(a, ":", pv, w), paste0(pv, w, ":", a)), p$nm)
  cv <- setNames(rep(0, length(p$nm)), p$nm); cv[ft] <- 1
  cv[nm(ft)] <- cv[nm(ft)] + 1; cv[nm(ref)] <- cv[nm(ref)] - 1; cv
}
d_flu <- function(p, v) {
  out <- list(); fts <- FOC[c("medicaid", "inc10k", "inc25k")]
  for (ft in fts[startsWith(fts, v)]) {
    for (w in c("1_pre", "2_pandemic", "3_post")) { e <- ci_of(p, lor_cv(p, v, ft, ERA, w))
      out[[length(out) + 1]] <- data.frame(term = ft, contrast = paste("OR in", w), ror = exp(e["est"]), lo = exp(e["lo"]), hi = exp(e["hi"]), p = e["p"], row.names = NULL) }
    for (pr in list(c("3_post", "1_pre"), c("3_post", "2_pandemic"), c("2_pandemic", "1_pre"))) {
      b <- ci_of(p, lor_cv(p, v, ft, ERA, pr[1]) - lor_cv(p, v, ft, ERA, pr[2]))
      out[[length(out) + 1]] <- data.frame(term = ft, contrast = paste0(pr[1], "/", pr[2]), ror = exp(b["est"]), lo = exp(b["lo"]), hi = exp(b["hi"]), p = b["p"], row.names = NULL)
    }
  }
  out
}

## within-stratum demeaning for the KHB projection
demean <- function(Mx, s) { if (!ncol(Mx)) return(Mx); Mx - rowsum(Mx, s)[as.character(s), , drop = FALSE] / as.vector(table(s)[as.character(s)]) }
mm <- function(rhs, dk) { mf <- model.matrix(as.formula(paste("~", rhs)), data = dk); mf[, colnames(mf) != "(Intercept)", drop = FALSE] }
BASE_NORACE <- paste(setdiff(trimws(strsplit(BASE, "\\+")[[1]]), RACE), collapse = " + ")

## One draw: every statistic A and B need, from one data set (an imputation, or a
## bootstrap resample of one). Seven clogit fits.
one_draw <- function(dk) {
  bj <- coef_only(fml(paste(BASE, "+", JOINT)), dk); if (is.null(bj)) return(NULL)
  bb <- coef_only(fml(BASE), dk)
  alone <- list()
  for (v in unique(FOCV)) alone[[v]] <- coef_only(fml(paste(BASE, "+", v)), dk)
  res <- list()
  ## KHB for each focal domain (and race): theta from within-stratum OLS of the
  ## other domains' dummies on the focal factor's dummies and the controls.
  khb <- function(focal_var, focal_term, others, controls) {
    Xf <- mm(focal_var, dk); Z <- mm(paste(others, collapse = " + "), dk); C <- if (nzchar(controls)) mm(controls, dk) else NULL
    Zd <- demean(Z, dk$.s); R <- demean(cbind(Xf, C), dk$.s)
    th <- qr.coef(qr(R), Zd)                      # (ncol(Xf)+ncol(C)) x ncol(Z)
    th <- th[focal_term, , drop = TRUE]; th[is.na(th)] <- 0
    bz <- bj[colnames(Z)]; bz[is.na(bz)] <- 0
    contrib <- th * bz                             # per Z column
    dom_of <- sapply(colnames(Z), function(cn) others[which.max(sapply(others, function(o) startsWith(cn, o) * nchar(o)))])
    c(total_khb = unname(bj[focal_term] + sum(contrib)), tapply(contrib, dom_of, sum))
  }
  for (nm in names(FOC)) {
    ft <- FOC[[nm]]; fv <- FOCV[[nm]]
    ba <- alone[[fv]][ft]; bjf <- bj[ft]
    k <- khb(fv, ft, setdiff(DOM, fv), BASE)
    res[[nm]] <- c(b_alone = unname(ba), b_joint = unname(bjf), k)
  }
  k <- khb(RACE, BLACK, DOM, BASE_NORACE)
  res[["black"]] <- c(b_alone = unname(bb[BLACK]), b_joint = unname(bj[BLACK]), k)
  res
}
stats_of <- function(r) {
  ## r: named vector from one_draw for one focal term
  a <- r["b_alone"]; j <- r["b_joint"]; t <- r["total_khb"]
  c(log_att = unname(100 * (a - j) / a), pere = unname(100 * (exp(a) - exp(j)) / (exp(a) - 1)),
    khb_att = unname(100 * (t - j) / t), rescale = unname(t / a),
    setNames(100 * r[setdiff(names(r), c("b_alone", "b_joint", "total_khb"))] / (t - j),
             paste0("share_", setdiff(names(r), c("b_alone", "b_joint", "total_khb")))))
}

## ======================================================== PROBE
if (PART == "PROBE") {
  cat("\nBASE:", BASE, "\nBASE_NORACE:", BASE_NORACE, "\n")
  for (v in c(DOM, RACE, ERA)) { cat(v, ":", levels(factor(d0[[v]])), "\n") }
  cat("columns:", paste(names(d), collapse = ", "), "\n")
  t0 <- Sys.time(); r <- one_draw(d0); cat("one draw took", round(as.numeric(difftime(Sys.time(), t0, units = "secs")), 1), "s\n")
  print(lapply(r, function(x) round(c(x, stats_of(x)), 3)))
}

## ======================================================== A + B
if (PART == "AB") {
  cat("\n=== point estimates: pooled over", M, "imputations ===\n")
  per_imp <- mclapply(seq_len(M), function(k) one_draw(apply_imp(k)), mc.cores = NCOR)
  per_imp <- per_imp[!sapply(per_imp, is.null)]
  cat("imputations with a usable draw:", length(per_imp), "\n")
  pt <- lapply(names(per_imp[[1]]), function(nm) {
    v <- Reduce(`+`, lapply(per_imp, `[[`, nm)) / length(per_imp); stats_of(v) })
  names(pt) <- names(per_imp[[1]])

  cat("\n=== cluster bootstrap:", BPER, "draws x", M, "imputations ===\n")
  rows_by_s <- split(seq_len(nrow(d)), d$.s); sids <- names(rows_by_s)
  jobs <- expand.grid(k = seq_len(M), b = seq_len(BPER))
  t0 <- Sys.time()
  draws <- mclapply(seq_len(nrow(jobs)), function(i) {
    set.seed(1e5 + i); dk <- apply_imp(jobs$k[i])
    pick <- sample(sids, length(sids), replace = TRUE)
    ix <- unlist(rows_by_s[pick], use.names = FALSE)
    dd <- dk[ix, ]; dd$.s <- rep(seq_along(pick), lengths(rows_by_s[pick]))
    r <- one_draw(dd); if (is.null(r)) return(NULL); lapply(r, stats_of)
  }, mc.cores = NCOR)
  cat("bootstrap done in", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "min\n")
  ok <- draws[!sapply(draws, is.null)]; cat("usable draws:", length(ok), "of", nrow(jobs), "\n")
  out <- do.call(rbind, lapply(names(pt), function(nm) {
    D <- do.call(rbind, lapply(ok, `[[`, nm))
    do.call(rbind, lapply(names(pt[[nm]]), function(st) {
      x <- D[, st]; x <- x[is.finite(x)]
      data.frame(term = nm, stat = st, estimate = unname(pt[[nm]][st]),
                 lo = unname(quantile(x, 0.025)), hi = unname(quantile(x, 0.975)),
                 n_draws = length(x), row.names = NULL) })) }))
  write.csv(out, file.path(OUT, "AB_attenuation.csv"), row.names = FALSE)
  print(out, row.names = FALSE, digits = 3)
}

## ======================================================== C D E F
if (PART == "CDEF") {
  focal_v <- c(DV[["ins"]], DV[["inc"]]); focal_t <- FOC[c("medicaid", "inc10k", "inc25k")]
  eras <- levels(factor(d[[ERA]]))
  rows <- list(); bounds <- list()
  if (ARM == "covid") {
    ## C + D. Wave varies within 96% of strata: one interaction model per exposure
    for (v in focal_v) for (mdl in c("alone", "joint")) {
      rhs <- paste(BASE, "+", if (mdl == "alone") v else JOINT, "+", v, ":", ERA)
      p <- fit_pool(fml(rhs), paste("C", mdl, v, "x wave"))
      for (ft in focal_t[startsWith(focal_t, v)]) for (w in eras) {
        hit <- intersect(c(paste0(ft, ":", ERA, w), paste0(ERA, w, ":", ft)), p$nm)
        e <- ci_of(p, cvec(p, c(ft, hit)))
        rows[[length(rows) + 1]] <- data.frame(model = mdl, term = ft, era = w, aor = exp(e["est"]), lo = exp(e["lo"]), hi = exp(e["hi"]), row.names = NULL)
        if (mdl == "joint" && length(hit)) {               # D: ratio later/first era
          b <- ci_of(p, cvec(p, hit))
          bounds[[length(bounds) + 1]] <- data.frame(term = ft, contrast = paste0(w, "/", eras[1]), ror = exp(b["est"]), lo = exp(b["lo"]), hi = exp(b["hi"]), p = b["p"], row.names = NULL)
        }
      }
    }
  } else {
    ## C. Period is constant within a stratum: refit within each period
    for (w in eras) for (mdl in c("alone_ins", "alone_inc", "joint")) {
      rhs <- paste(BASE, "+", switch(mdl, alone_ins = DV[["ins"]], alone_inc = DV[["inc"]], joint = JOINT))
      p <- fit_pool(fml(rhs), paste("C", mdl, "within", w), keep_rows = function(dk) dk[[ERA]] == w)
      if (is.null(p)) next
      for (ft in focal_t) if (ft %in% p$nm) {
        e <- ci_of(p, cvec(p, ft))
        rows[[length(rows) + 1]] <- data.frame(model = sub("_.*", "", mdl), term = ft, era = w, aor = exp(e["est"]), lo = exp(e["lo"]), hi = exp(e["hi"]), row.names = NULL)
      }
    }
    ## D. Period is constant within a stratum and has no main effect, so R codes
    ## v:period with a dummy for EVERY period and clogit aliases one of them. The
    ## per-period log odds ratio is main + int_w, with int = 0 for the aliased
    ## period, whichever that is; the ratio between two periods is therefore
    ## int_a - int_b. (v1 of this block assumed 3_post was the reference; it was
    ## not, and printed pandemic/pre as post/pre. Corrected 2026-09-23.)
    if (PART != "DFLU") for (v in focal_v) {
      p <- fit_pool(fml(paste(BASE, "+", JOINT, "+", v, ":", ERA)), paste("D", v, "x period"))
      bounds <- c(bounds, d_flu(p, v))
    }
  }
  C <- do.call(rbind, rows); write.csv(C, file.path(OUT, "C_era_attenuation.csv"), row.names = FALSE); print(C, row.names = FALSE, digits = 3)
  Dd <- do.call(rbind, bounds); write.csv(Dd, file.path(OUT, "D_bounds.csv"), row.names = FALSE); print(Dd, row.names = FALSE, digits = 3)

  if (ARM == "covid") {
    ## E. the emergency paid sick leave window inside pre-Delta
    co <- read.csv(file.path(BUCKET, "aou_v7", "01_covid_cohort.csv"))
    idate <- as.Date(co$covid_index_date[match(d$person_id, co$person_id)])
    era4 <- as.character(d[[ERA]]); pre <- era4 == levels(factor(d[[ERA]]))[1]
    era4[pre & idate <  as.Date("2021-01-01")] <- "a_2020_epsl"
    era4[pre & idate >= as.Date("2021-01-01")] <- "b_2021h1"
    d$f.era4 <- factor(era4, levels = c("a_2020_epsl", "b_2021h1", setdiff(levels(factor(d[[ERA]])), levels(factor(d[[ERA]]))[1])))
    cnt <- as.data.frame(table(era4 = d$f.era4, case = d$Treatment)); cnt$Freq <- screen(cnt$Freq)
    write.csv(cnt, file.path(OUT, "E_counts.csv"), row.names = FALSE); print(cnt)
    cat("strata in which era4 varies:", mean(tapply(d$f.era4, d$.s, function(z) length(unique(z)) > 1)), "\n")
    base4 <- sub(ERA, "f.era4", BASE, fixed = TRUE)
    E <- list()
    for (v in c(DV[["inc"]], DV[["emp"]], DV[["ins"]])) {
      p <- fit_pool(fml(paste(base4, "+", JOINT, "+", v, ": f.era4")), paste("E", v, "x era4"))
      lv <- paste0(v, levels(droplevels(factor(d0[[v]])))); lv <- intersect(lv, p$nm)
      ix <- intersect(c(paste0(lv, ":f.era4b_2021h1"), paste0("f.era4b_2021h1:", lv)), p$nm)
      s <- D1(p, ix)
      E[[length(E) + 1]] <- data.frame(exposure = v, term = "D1: 2021H1 vs 2020 (EPSL)", aor = NA, lo = NA, hi = NA, F = s["F"], df1 = s["df1"], p = s["p"], row.names = NULL)
      for (ft in intersect(c(FOC, lv), lv)) for (w in levels(d$f.era4)) {
        hit <- intersect(c(paste0(ft, ":f.era4", w), paste0("f.era4", w, ":", ft)), p$nm)
        e <- ci_of(p, cvec(p, c(ft, hit)))
        E[[length(E) + 1]] <- data.frame(exposure = v, term = paste(ft, w), aor = exp(e["est"]), lo = exp(e["lo"]), hi = exp(e["hi"]), F = NA, df1 = NA, p = NA, row.names = NULL)
      }
    }
    E <- do.call(rbind, E); write.csv(E, file.path(OUT, "E_epsl.csv"), row.names = FALSE); print(E, row.names = FALSE, digits = 3)
  } else {
    ## F. the two post-pandemic seasons, around the Medicaid unwinding
    SC <- intersect(c("season", "flu_season", "season_label"), names(d))[1]
    if (is.na(SC)) { cat("F: no season column; skipped\n") } else {
      post <- d[[ERA]] == "3_post"; cat("F: seasons in 3_post:\n"); print(table(d[[SC]][post]))
      d$f.season <- factor(ifelse(post, as.character(d[[SC]]), NA))
      cnt <- as.data.frame(table(season = d$f.season, case = d$Treatment)); cnt$Freq <- screen(cnt$Freq)
      write.csv(cnt, file.path(OUT, "F_counts.csv"), row.names = FALSE); print(cnt)
      Fo <- list()
      for (v in focal_v) {
        p <- fit_pool(fml(paste(BASE, "+", JOINT, "+", v, ": f.season")), paste("F", v, "x post season"), keep_rows = function(dk) dk[[ERA]] == "3_post")
        if (is.null(p)) next
        ix <- grep(paste0("^", v, ".*:f\\.season|^f\\.season.*:", v), p$nm, value = TRUE); s <- D1(p, ix)
        Fo[[length(Fo) + 1]] <- data.frame(term = paste(v, "x season D1"), aor = NA, lo = NA, hi = NA, F = s["F"], df1 = s["df1"], p = s["p"], row.names = NULL)
        ss <- levels(droplevels(d$f.season))
        for (ft in focal_t[startsWith(focal_t, v)]) for (w in ss) {
          hit <- intersect(c(paste0(ft, ":f.season", w), paste0("f.season", w, ":", ft)), p$nm)
          e <- ci_of(p, cvec(p, c(ft, hit)))
          Fo[[length(Fo) + 1]] <- data.frame(term = paste(ft, w), aor = exp(e["est"]), lo = exp(e["lo"]), hi = exp(e["hi"]), F = NA, df1 = NA, p = NA, row.names = NULL)
        }
      }
      Fo <- do.call(rbind, Fo); write.csv(Fo, file.path(OUT, "F_unwinding.csv"), row.names = FALSE); print(Fo, row.names = FALSE, digits = 3)
    }
  }
}
if (PART == "DFLU") {
  stopifnot(ARM == "flu"); bounds <- list()
  for (v in c(DV[["ins"]], DV[["inc"]])) {
    p <- fit_pool(fml(paste(BASE, "+", JOINT, "+", v, ":", ERA)), paste("D", v, "x period"))
    bounds <- c(bounds, d_flu(p, v))
  }
  Dd <- do.call(rbind, bounds); write.csv(Dd, file.path(OUT, "D_bounds.csv"), row.names = FALSE); print(Dd, row.names = FALSE, digits = 3)
  ## F again, with the corrected contrast
  post <- d[[ERA]] == "3_post"; d$f.season <- factor(ifelse(post, as.character(d$season), NA))
  Fo <- list()
  for (v in c(DV[["ins"]], DV[["inc"]])) {
    p <- fit_pool(fml(paste(BASE, "+", JOINT, "+", v, ": f.season")), paste("F", v, "x post season"), keep_rows = function(dk) dk[[ERA]] == "3_post")
    ix <- grep(paste0("^", v, ".*:f\\.season|^f\\.season.*:", v), p$nm, value = TRUE); s1 <- D1(p, ix)
    Fo[[length(Fo) + 1]] <- data.frame(term = paste(v, "x season D1"), aor = NA, lo = NA, hi = NA, F = s1["F"], df1 = s1["df1"], p = s1["p"], row.names = NULL)
    fts <- FOC[c("medicaid", "inc10k", "inc25k")]
    for (ft in fts[startsWith(fts, v)]) {
      for (w in levels(droplevels(d$f.season))) { e <- ci_of(p, lor_cv(p, v, ft, "f.season", w))
        Fo[[length(Fo) + 1]] <- data.frame(term = paste(ft, w), aor = exp(e["est"]), lo = exp(e["lo"]), hi = exp(e["hi"]), F = NA, df1 = NA, p = NA, row.names = NULL) }
      b <- ci_of(p, lor_cv(p, v, ft, "f.season", "2023-24") - lor_cv(p, v, ft, "f.season", "2022-23"))
      Fo[[length(Fo) + 1]] <- data.frame(term = paste(ft, "ratio 2023-24/2022-23"), aor = exp(b["est"]), lo = exp(b["lo"]), hi = exp(b["hi"]), F = NA, df1 = NA, p = b["p"], row.names = NULL)
    }
  }
  Fo <- do.call(rbind, Fo); write.csv(Fo, file.path(OUT, "F_unwinding.csv"), row.names = FALSE); print(Fo, row.names = FALSE, digits = 3)
}
cat("\nDONE\n"); sink()
