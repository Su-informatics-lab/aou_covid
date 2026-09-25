## 03n_jno_reruns.R -- the three reruns the JNO reframe asked for, in one pass
## over the 40 imputations 03d saved. Nothing is re-imputed.
##
## Runs on the All of Us Researcher Workbench, COVID-19 workspace (CDR v7).
## Nothing person-level leaves it; every count written out is screened at 20.
##
##   R2  education merged. The never-attended-school level (fewer than 20
##       participants) is folded into below-GED in every imputed frame, which is
##       how the influenza arm codes it. 03m measured the cost on the joint model
##       at 0.0053 on the log scale; this refits everything the main text prints
##       from the COVID-19 arm under that coding, so the paper has one primary.
##         joint, six domain-specific models, six domain-by-wave tests with
##         their contrasts, race attenuation, income block tests and shape.
##
##   R1  pre-index surveys only. 13.6% of COVID-19 participants completed The
##       Basics after their index date, and the headline domains (income,
##       employment) are the ones a hospitalization could change. S3 in
##       03_sensitivity.R ran this restriction on the missing-indicator coding
##       only. Here it runs on the primary: strata whose case surveyed after
##       index are dropped, controls who surveyed after index are dropped.
##
##   R3  ascertainment by wave. If home testing in Omicron made a recorded
##       positive depend on contact with a health system, and that contact
##       differs by insurance, the insurance-by-wave interaction could be a
##       selection pattern rather than a change in the association. Two checks:
##       the share of index dates carried by a laboratory result, by wave x
##       insurance x case status; and the joint model and insurance-by-wave test
##       refitted with both case and controls restricted to a laboratory-
##       confirmed index.
##
## Output: /home/jupyter/jno_v24/{log_03n.txt, *.csv}

suppressPackageStartupMessages({library(survival); library(sandwich)})

BUCKET <- "/home/jupyter/workspace/rw-migration-aou-rw-46c7ae9e/data/covid_sdoh"
RES    <- file.path(BUCKET, "aou_v7_5domain")
RESV7  <- file.path(BUCKET, "aou_v7")
MI     <- "/home/jupyter/mi40b"
OUT    <- paste0("/home/jupyter/jno_v24", Sys.getenv("OUTSUFFIX", ""))
dir.create(OUT, showWarnings = FALSE)
sink(file.path(OUT, paste0("log_03n_", gsub(",", "", Sys.getenv("PARTS", "all")), ".txt")), split = TRUE)
MIN_CELL <- 20
VARTYPE <- Sys.getenv("VARTYPE", "cluster")   # no fallback (2026-09-24)
stopifnot(VARTYPE %in% c("cluster", "model"))
PARTS <- strsplit(Sys.getenv("PARTS", "R2,R1,R3"), ",")[[1]]

X    <- readRDS(file.path(RES, "joint_model_inputs.rds"))
d    <- X$df
IM   <- readRDS(file.path(MI, "imputations.rds"))
IMPS <- IM$imps; M <- length(IMPS); IMPV <- names(IMPS[[1]])
idx  <- match(d$person_id, IM$person_id)
stopifnot(!any(is.na(idx)))
base_rhs  <- X$base_rhs
joint_rhs <- X$joint_sdoh
cat("m =", M, "| rows", nrow(d), "| persons", length(unique(d$person_id)), "\n")
cat("base :", base_rhs, "\njoint:", joint_rhs, "\n")
cat("wave levels:", levels(d$f.wave), "\n")
cat("education levels:", levels(d$f.education), "\n")

## ------------------------------------------------------------ R2: the merge
lev_never <- grep("never", levels(d$f.education), ignore.case = TRUE, value = TRUE)
lev_below <- grep("below", levels(d$f.education), ignore.case = TRUE, value = TRUE)
stopifnot(length(lev_never) == 1, length(lev_below) == 1)
cat("merging", lev_never, "into", lev_below, "\n")
merge_edu <- function(f) {
  z <- as.character(f); z[z == lev_never] <- lev_below
  factor(z, levels = setdiff(levels(f), lev_never))
}

apply_imp <- function(k) {
  dk <- d
  for (v in IMPV) dk[[v]] <- IMPS[[k]][[v]][idx]
  dk$f.education <- merge_edu(dk$f.education)
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
tab <- function(p, n) {
  se  <- sqrt(diag(p$Tv))
  lam <- pmin(pmax((1 + 1 / p$m) * diag(p$B) / diag(p$Tv), 1e-8), 1 - 1e-8)
  nu_old <- (p$m - 1) / lam^2
  nu_com <- n - length(p$nm)
  nu_obs <- (nu_com + 1) / (nu_com + 3) * nu_com * (1 - lam)
  nu <- nu_old * nu_obs / (nu_old + nu_obs)
  data.frame(term = p$nm, beta = p$qbar, aor = exp(p$qbar),
             lo = exp(p$qbar - qt(0.975, nu) * se),
             hi = exp(p$qbar + qt(0.975, nu) * se),
             fmi = round(lam, 3), row.names = NULL)
}

## One fitter for everything. `keep_rows` restricts the analysis sample after
## imputation (R1, R3); the imputation model itself is the frozen one. An
## aliased nuisance term is kept out of the pool rather than discarding the fit,
## and any casualty among the terms of interest is named.
fit_all <- function(formula, label, keep_rows = NULL, prep = identity) {
  CO <- VA <- list(); fails <- 0; dropped <- character(0); n <- NA
  for (k in seq_len(M)) {
    dk <- prep(apply_imp(k))
    if (!is.null(keep_rows)) dk <- dk[keep_rows, ]
    n <- nrow(dk)
    f2 <- formula; environment(f2) <- environment()   # see 03o fit_pool (2026-09-24)
    fk <- tryCatch(clogit(f2, data = dk, method = "efron"), error = function(e) NULL)
    if (is.null(fk)) { fails <- fails + 1; next }
    b  <- coef(fk)
    Vk <- if (VARTYPE == "cluster") sandwich::vcovCL(fk, cluster = dk$person_id) else vcov(fk)
    ok <- intersect(names(b)[!is.na(b)], rownames(Vk))
    if (length(ok) < 2) { fails <- fails + 1; next }
    if (length(ok) < length(b)) dropped <- union(dropped, setdiff(names(b), ok))
    CO[[length(CO) + 1]] <- b[ok]; VA[[length(VA) + 1]] <- Vk[ok, ok, drop = FALSE]
  }
  cat(sprintf("  %-40s fitted %d of %d | failures %d | rows %d\n",
              label, length(CO), M, fails, n))
  if (length(dropped)) cat("    not estimable in every frame:", paste(dropped, collapse = ", "), "\n")
  if (length(CO) < 2) return(NULL)
  p <- pool_full(CO, VA); p$n <- n; p$dropped <- dropped; p
}

SD <- "^f\\.(income|insurance|education|employment|housing|race)"
DOMAINS <- c("f.insurance", "f.income", "f.education", "f.employment",
             "f.housing", "f.housing_stability")
stopifnot(all(sapply(DOMAINS, function(v) grepl(v, joint_rhs, fixed = TRUE))))

f_joint <- as.formula(paste("Treatment ~", base_rhs, "+", joint_rhs, "+ strata(stratum)"))
f_base  <- as.formula(paste("Treatment ~", base_rhs, "+ strata(stratum)"))
f_inc   <- as.formula(paste("Treatment ~", base_rhs, "+ f.income + strata(stratum)"))

## the era machinery, shared by R2, R1 and R3
wave_test <- function(exposure, label, keep_rows = NULL) {
  f <- as.formula(paste("Treatment ~", base_rhs, "+", joint_rhs, "+",
                        exposure, ":f.wave + strata(stratum)"))
  p <- fit_all(f, label, keep_rows)
  if (is.null(p)) return(NULL)
  ## exact term names, so f.housing never collects f.housing_stability terms
  lv_terms <- paste0(exposure, levels(d[[exposure]]))
  ix_terms <- c(outer(lv_terms, paste0("f.wave", levels(d$f.wave)), paste, sep = ":"),
                outer(paste0("f.wave", levels(d$f.wave)), lv_terms, paste, sep = ":"))
  keep <- intersect(ix_terms, p$nm)
  lost <- intersect(ix_terms, p$dropped)
  if (length(lost)) cat("  !!", label, "-- interaction terms NOT in the test:",
                        paste(lost, collapse = ", "), "\n")
  s <- D1(p, keep)
  cat(sprintf("  %-40s F = %.3f, df1 = %d, df2 = %.0f, r1 = %.3f, P = %.4g\n",
              label, s["F"], s["df1"], s["df2"], s["r1"], s["p"]))
  main <- intersect(lv_terms, p$nm)
  cc <- list()
  for (lv in main) for (w in levels(d$f.wave)) {
    cv <- setNames(rep(0, length(p$nm)), p$nm); cv[lv] <- 1
    hit <- intersect(c(paste0(lv, ":f.wave", w), paste0("f.wave", w, ":", lv)), p$nm)
    if (length(hit)) cv[hit] <- 1
    est <- sum(cv * p$qbar); s_ <- sqrt(drop(t(cv) %*% p$Tv %*% cv))
    cc[[length(cc) + 1]] <- data.frame(exposure = exposure, level = lv, wave = w,
      aor = exp(est), lo = exp(est - 1.96 * s_), hi = exp(est + 1.96 * s_), row.names = NULL)
  }
  list(test = data.frame(label = label, exposure = exposure, F = s["F"], df1 = s["df1"],
                         df2 = s["df2"], r1 = s["r1"], p = s["p"],
                         lost_terms = length(lost), row.names = NULL),
       contrasts = cbind(label = label, do.call(rbind, cc)))
}

## counts, screened at 20 before they are written
screen <- function(df, cols) {
  for (cl in cols) df[[cl]] <- ifelse(df[[cl]] < MIN_CELL, NA, df[[cl]])
  df
}
sample_counts <- function(keep_rows, label) {
  dd <- if (is.null(keep_rows)) d else d[keep_rows, ]
  st <- tapply(dd$Treatment, dd$stratum, function(z) sum(z == 1) == 1 && sum(z == 0) >= 1)
  dd <- dd[dd$stratum %in% names(st)[st], ]
  screen(data.frame(sample = label,
    cases = sum(dd$Treatment == 1), controls = sum(dd$Treatment == 0),
    persons = length(unique(dd$person_id)), strata = length(unique(dd$stratum))),
    c("cases", "controls", "persons", "strata"))
}

## ================================================================== R2
if ("R2" %in% PARTS) {
cat("\n================ R2: primary, education merged ================\n")
pj <- fit_all(f_joint, "joint (merged)")
tj <- tab(pj, pj$n)
write.csv(tj, file.path(OUT, "R2_joint_merged.csv"), row.names = FALSE)
saveRDS(pj, file.path(OUT, "R2_joint_merged_pool.rds"))
print(tj[grep(SD, tj$term), c("term", "aor", "lo", "hi")], row.names = FALSE, digits = 4)

## against the frozen unmerged primary
fz <- tryCatch(read.csv(file.path(MI, "joint_congenial.csv")), error = function(e) NULL)
if (!is.null(fz)) {
  cm <- merge(fz[, c("term", "aor", "lo", "hi")], tj[, c("term", "aor", "lo", "hi")],
              by = "term", suffixes = c("_frozen", "_merged"))
  cm$abs_log_diff <- abs(log(cm$aor_merged) - log(cm$aor_frozen))
  cm <- cm[order(-cm$abs_log_diff), ]
  write.csv(cm, file.path(OUT, "R2_vs_frozen.csv"), row.names = FALSE)
  cat("\nlargest movements against the frozen primary (social terms):\n")
  print(head(cm[grep(SD, cm$term), ], 10), row.names = FALSE, digits = 4)
}

cat("\n-- domain-specific models\n")
ds <- list()
for (v in DOMAINS) {
  f <- as.formula(paste("Treatment ~", base_rhs, "+", v, "+ strata(stratum)"))
  p <- fit_all(f, paste("domain-specific", v))
  if (!is.null(p)) { t_ <- tab(p, p$n)
    ds[[v]] <- cbind(domain = v, t_[t_$term %in% paste0(v, levels(d[[v]])), ]) }
}
ds <- do.call(rbind, ds)
write.csv(ds, file.path(OUT, "R2_domain_specific_merged.csv"), row.names = FALSE)
print(ds[, c("term", "aor", "lo", "hi")], row.names = FALSE, digits = 4)

cat("\n-- domain-by-wave tests (income and insurance prespecified)\n")
wt <- lapply(DOMAINS, function(v) wave_test(v, paste("R2", v, "x wave")))
wt <- wt[!sapply(wt, is.null)]
write.csv(do.call(rbind, lapply(wt, `[[`, "test")), file.path(OUT, "R2_wave_tests.csv"), row.names = FALSE)
write.csv(do.call(rbind, lapply(wt, `[[`, "contrasts")), file.path(OUT, "R2_wave_contrasts.csv"), row.names = FALSE)

cat("\n-- race attenuation\n")
pb <- fit_all(f_base, "base"); pi <- fit_all(f_inc, "base + income")
rt <- lapply(list(base = pb, income = pi, joint = pj), function(p) tab(p, p$n))
race <- Reduce(function(a, b) merge(a, b, by = "term"),
  lapply(names(rt), function(nm) { z <- rt[[nm]][grep("^f\\.race", rt[[nm]]$term), c("term", "beta", "aor", "lo", "hi")]
                                    names(z)[-1] <- paste0(names(z)[-1], "_", nm); z }))
race$removed_by_income <- 1 - race$beta_income / race$beta_base
race$removed_by_all    <- 1 - race$beta_joint  / race$beta_base
race$income_share      <- race$removed_by_income / race$removed_by_all
write.csv(race, file.path(OUT, "R2_race_attenuation.csv"), row.names = FALSE)
print(race[, c("term", "aor_base", "aor_joint", "lo_joint", "hi_joint",
               "removed_by_all", "income_share")], row.names = FALSE, digits = 4)

cat("\n-- income block tests and shape\n")
HI <- grep("^f\\.income(100k_150k|150k_200k|more_200k)$", pj$nm, value = TRUE)
LO <- grep("^f\\.income(less_10k|10k_25k|25k_35k)$", pj$nm, value = TRUE)
hi <- D1(pj, HI); lo <- D1(pj, LO)
MID  <- c(less_10k = 5, "10k_25k" = 17.5, "25k_35k" = 30, "35k_100k" = 67.5,
          "100k_150k" = 125, "150k_200k" = 175, more_200k = 250)
RANK <- setNames(seq_along(MID), names(MID))
f_score <- as.formula(paste("Treatment ~", base_rhs, "+",
                            sub("f.income", "inc_score", joint_rhs, fixed = TRUE), "+ strata(stratum)"))
shape <- list()
for (sc in c("log10_midpoint", "rank")) {
  ps <- fit_all(f_score, paste("trend", sc), prep = function(dk) {
    lev <- as.character(dk$f.income)
    dk$inc_score <- if (sc == "rank") RANK[lev] else log10(MID[lev] * 1000); dk })
  j <- which(ps$nm == "inc_score"); s <- sqrt(ps$Tv[j, j])
  shape[[sc]] <- data.frame(test = paste("trend", sc), estimate = exp(ps$qbar[j]),
    lo = exp(ps$qbar[j] - 1.96 * s), hi = exp(ps$qbar[j] + 1.96 * s),
    F = NA, df1 = NA, p = 2 * pnorm(-abs(ps$qbar[j] / s)), row.names = NULL)
}
blk <- rbind(
  data.frame(test = "high income block D1", estimate = NA, lo = NA, hi = NA, F = hi["F"], df1 = hi["df1"], p = hi["p"], row.names = NULL),
  data.frame(test = "low income block D1",  estimate = NA, lo = NA, hi = NA, F = lo["F"], df1 = lo["df1"], p = lo["p"], row.names = NULL),
  do.call(rbind, shape))
write.csv(blk, file.path(OUT, "R2_income_shape.csv"), row.names = FALSE)
print(blk, row.names = FALSE, digits = 4)
}

## ================================================================== R1
if ("R1" %in% PARTS) {
cat("\n================ R1: surveys completed on or before the index date ================\n")
tim <- read.csv(file.path(RES, "04b_sdoh_timing.csv"))
pre <- tim$sdoh_pre_index[match(d$person_id, tim$person_id)]
cat("rows with no timing record:", sum(is.na(pre)), "\n")
pre[is.na(pre)] <- 0
case_pre <- tapply(pre[d$Treatment == 1], d$stratum[d$Treatment == 1], min)
keep1 <- pre == 1 & d$stratum %in% names(case_pre)[case_pre == 1]
cnt <- rbind(sample_counts(NULL, "all"), sample_counts(keep1, "pre-index surveys only"))
print(cnt, row.names = FALSE)
write.csv(cnt, file.path(OUT, "R1_counts.csv"), row.names = FALSE)
## how the post-index share runs by wave among cases -- does the restriction
## remove more of one era than another?
ww <- as.data.frame(table(wave = d$f.wave[d$Treatment == 1], pre = pre[d$Treatment == 1]))
write.csv(screen(ww, "Freq"), file.path(OUT, "R1_case_pre_by_wave.csv"), row.names = FALSE)
print(screen(ww, "Freq"), row.names = FALSE)

p1 <- fit_all(f_joint, "R1 joint", keep1)
t1 <- tab(p1, p1$n)
write.csv(t1, file.path(OUT, "R1_joint_preindex.csv"), row.names = FALSE)
print(t1[grep(SD, t1$term), c("term", "aor", "lo", "hi")], row.names = FALSE, digits = 4)
w1 <- lapply(c("f.income", "f.insurance", "f.employment"),
             function(v) wave_test(v, paste("R1", v, "x wave"), keep1))
w1 <- w1[!sapply(w1, is.null)]
write.csv(do.call(rbind, lapply(w1, `[[`, "test")), file.path(OUT, "R1_wave_tests.csv"), row.names = FALSE)
write.csv(do.call(rbind, lapply(w1, `[[`, "contrasts")), file.path(OUT, "R1_wave_contrasts.csv"), row.names = FALSE)
}

## ================================================================== R3
if ("R3" %in% PARTS) {
cat("\n================ R3: ascertainment by wave ================\n")
co  <- read.csv(file.path(RESV7, "01_covid_cohort.csv"))
src <- co$covid_source[match(d$person_id, co$person_id)]
cat("index source, matched rows:\n"); print(table(src, useNA = "ifany"))
lab <- src %in% c("positive_lab", "both")

## (a) laboratory share of the index date, by wave x insurance x case status
a <- aggregate(cbind(n, lab) ~ f.wave + f.insurance + Treatment,
               data = data.frame(d[, c("f.wave", "f.insurance", "Treatment")], n = 1L, lab = as.integer(lab)),
               FUN = sum)
ok_cell <- a$n >= MIN_CELL & a$lab >= MIN_CELL & (a$n - a$lab) >= MIN_CELL
a$lab_pct <- ifelse(ok_cell, round(100 * a$lab / a$n, 1), NA)
## complementary suppression: n and lab together reveal n - lab, so when any of
## the three is under the line both counts go, not only the one that is
a$lab[!ok_cell] <- NA
a <- screen(a, c("n", "lab"))
write.csv(a, file.path(OUT, "R3_lab_share_by_wave_insurance.csv"), row.names = FALSE)
print(a, row.names = FALSE)

## (b) the unmatched cohort: hospitalized share by wave, and lab share by wave
wv <- function(dt) cut(as.Date(dt), c(as.Date("1900-01-01"), as.Date("2021-06-15"),
                                      as.Date("2021-12-15"), as.Date("2100-01-01")),
                       labels = c("pre_delta", "delta", "omicron"), right = FALSE)
co$wave <- wv(co$covid_index_date)
co$lab  <- as.integer(co$covid_source %in% c("positive_lab", "both")); co$n <- 1L
b <- aggregate(cbind(n, hosp = severity, lab) ~ wave, data = co, FUN = sum)
b$hosp_pct <- round(100 * b$hosp / b$n, 1); b$lab_pct <- round(100 * b$lab / b$n, 1)
b <- screen(b, c("n", "hosp", "lab"))
write.csv(b, file.path(OUT, "R3_unmatched_by_wave.csv"), row.names = FALSE)
print(b, row.names = FALSE)
cat("(unmatched cohort = everyone with COVID-19; wave cut points as in the models;\n",
    " compare with levels(d$f.wave) above)\n")

## (c) refit with case and controls both laboratory-confirmed
case_lab <- tapply(lab[d$Treatment == 1], d$stratum[d$Treatment == 1], min)
keep3 <- lab & d$stratum %in% names(case_lab)[case_lab == 1]
cnt3 <- rbind(sample_counts(NULL, "all"), sample_counts(keep3, "laboratory-confirmed index only"))
print(cnt3, row.names = FALSE)
write.csv(cnt3, file.path(OUT, "R3_counts.csv"), row.names = FALSE)
p3 <- fit_all(f_joint, "R3 joint, lab-confirmed", keep3)
t3 <- tab(p3, p3$n)
write.csv(t3, file.path(OUT, "R3_joint_lab.csv"), row.names = FALSE)
print(t3[grep(SD, t3$term), c("term", "aor", "lo", "hi")], row.names = FALSE, digits = 4)
w3 <- lapply(c("f.insurance", "f.income"), function(v) wave_test(v, paste("R3", v, "x wave"), keep3))
w3 <- w3[!sapply(w3, is.null)]
write.csv(do.call(rbind, lapply(w3, `[[`, "test")), file.path(OUT, "R3_wave_tests.csv"), row.names = FALSE)
write.csv(do.call(rbind, lapply(w3, `[[`, "contrasts")), file.path(OUT, "R3_wave_contrasts.csv"), row.names = FALSE)
}

cat("\nDONE\n")
sink()
