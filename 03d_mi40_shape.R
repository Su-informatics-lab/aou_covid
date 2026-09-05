## 03d_mi40_shape.R — the primary specification, and the shape of the income
## association under it.
##
## Runs on the All of Us Researcher Workbench. Nothing person-level leaves it.
##
## Decision this implements (2026-09-05): m = 40 multiple imputation of the four
## items The Basics asks of every participant is the primary specification;
## insurance keeps non-administration as an observed level and is not imputed;
## the missing-indicator model becomes sensitivity 1. Tests 1 to 4 and the
## influenza arm all move to it together.
##
## ---------------------------------------------------------------------------
## Why the income question is worth a run rather than an eyeball
##
## Under the indicator specification the jointly adjusted income estimates run
## 1.21, 1.21, 1.10, 1.22, 1.26, 1.15 from the lowest band to the highest,
## against a $35,000-99,999 reference: two of the three highest bands are
## elevated and one is significant. That is not a gradient. Under the frozen
## m = 40 run the same model gives 1.51, 1.40, 1.18, 1.16, 1.20, 1.09, and the
## influenza arm gives 1.55, 1.83, 1.28, 1.05, 0.91, 0.94 on the indicator
## specification. Two arms suggest the U belongs to the specification. This
## script tests it: a D1 block Wald on the three high bands, and a linear trend
## on two parameterisations so the claim does not rest on one coding.
##
## ---------------------------------------------------------------------------
## Why this fits TWO imputation models
##
## The analysis conditions on a matched stratum built from three variables:
## survey_ord, num_diagnosis and ehr_length_days (01b_psm.R, glm propensity
## score, 1:4 with replacement, 0.2 SD caliper). An imputation model has to be
## congenial with that: it cannot carry the stratum indicator, so it should
## carry the variables the stratum is a function of.
##
## The frozen m = 40 run carried survey_ord and neither of the other two. That
## is one of three. So this script fits both:
##
##   legacy     the frozen predictor set. Its job is provenance: the joint
##              column must reproduce mi40_joint.csv. If it does not, the frozen
##              run differed in some other way and step8b.R should be pulled
##              from gs://.../aou_v7_5domain_mi40/ before anything is believed.
##   congenial  legacy plus num_diagnosis and ehr_length_days. This is the new
##              primary. The difference between the two columns is itself
##              reportable as a congeniality sensitivity.
##
## The other two checks are settled here in the log rather than by inspection:
## case status must be in the imputation model, or the imputed coefficients are
## biased toward the null and the paper would state the wrong direction of
## conservatism; and imputation must be at person level, because matching with
## replacement puts one person in several strata and a row-level imputation
## would give that person a different income in each.
##
## Output: /home/jupyter/mi40b/{log.txt, joint_legacy.csv, joint_congenial.csv,
##         spec_compare.csv, income_shape.csv, income_block_tests.csv,
##         pooled_cov.rds, imputations.rds, imputations_legacy.rds}

suppressPackageStartupMessages({
  library(survival); library(sandwich); library(mice)
})
set.seed(20260904)

RES <- "/home/jupyter/refit_nodis/results/aou_v7"
OUT <- "/home/jupyter/mi40b"
dir.create(OUT, showWarnings = FALSE)
sink(file.path(OUT, "log.txt"), split = TRUE)

M <- 40
X         <- readRDS(file.path(RES, "joint_model_inputs.rds"))
d         <- X$df
base_rhs  <- X$base_rhs
joint_rhs <- X$joint_sdoh
IMP  <- c("f.income", "f.education", "f.employment", "f.housing", "f.housing_stability")
MVAR <- c("survey_ord", "num_diagnosis", "ehr_length_days")   # 01b_psm.R
f_joint <- as.formula(paste("Treatment ~", base_rhs, "+", joint_rhs, "+ strata(stratum)"))

cat("mice", as.character(packageVersion("mice")),
    "| rows", nrow(d), "| persons", length(unique(d$person_id)),
    "| strata", length(unique(d$stratum)), "| m =", M, "\n\n")

CH <- c("Myocardial_Infarction", "Congestive_Heart_Failure",
        "Peripheral_Vascular_Disease", "Cerebrovascular_Disease", "Dementia",
        "Chronic_Pulmonary_Disease", "Rheumatic_Disease", "Peptic_Ulcer_Disease",
        "Liver_Disease_Mild", "Liver_Disease_Moderate_Severe",
        "Diabetes_without_Chronic_Complications",
        "Diabetes_with_Chronic_Complications", "Hemiplegia_Paraplegia",
        "Renal_Disease_Mild_Moderate", "Renal_Disease_Severe", "HIV",
        "Metastatic_Solid_Tumor", "Malignancy", "AIDS")
pv <- c("person_id", "Treatment", "f.sex", "f.age", "f.vacc", "f.race",
        "f.ethnicity", "f.wave", CH, "f.insurance", IMP)
P <- d[!duplicated(d$person_id), pv]; rownames(P) <- NULL

mv <- read.csv(file.path(RES, "06_matching_variables.csv"))
cat("06_matching_variables.csv columns:", paste(names(mv), collapse = ", "), "\n")
stopifnot(all(MVAR %in% names(mv)))
i <- match(P$person_id, mv$person_id)
for (v in MVAR) P[[v]] <- mv[[v]][i]
for (v in MVAR) {
  n_na <- sum(is.na(P[[v]]))
  if (n_na) {
    cat("  ", v, "missing for", n_na, "persons; filled at the median\n")
    P[[v]][is.na(P[[v]])] <- median(P[[v]], na.rm = TRUE)
  }
}

for (v in IMP) {
  z <- as.character(P[[v]]); z[z == "Missing"] <- NA
  P[[v]] <- factor(z, levels = setdiff(levels(d[[v]]), "Missing"))
}
cat("\npersons with a missing value, by item:\n")
print(sapply(P[, IMP], function(z) sum(is.na(z))))
cat("persons total:", nrow(P), "\n")

## ---------------------------------------------------------------- the checks
cat("\n===== congeniality checks =====\n")
cat("1. case status in the imputation model: ",
    if ("Treatment" %in% names(P)) "YES" else "NO -- STOP", "\n", sep = "")
chk <- tapply(d$Treatment, d$person_id, function(z) length(unique(z)))
cat("2. imputation frame is person level: rows ", nrow(P), " vs persons ",
    length(unique(d$person_id)),
    if (nrow(P) == length(unique(d$person_id))) "  YES" else "  NO -- STOP", "\n", sep = "")
cat("   max distinct case status within a person: ", max(chk),
    if (max(chk) == 1) "  YES" else "  NO -- STOP", "\n", sep = "")
stopifnot("Treatment" %in% names(P), nrow(P) == length(unique(d$person_id)), max(chk) == 1)
cat("3. matching variables carried: ", paste(MVAR, collapse = ", "),
    " -- all three in the congenial model, only survey_ord in the legacy one\n", sep = "")

drop_const <- names(which(sapply(P[, CH, drop = FALSE], function(z) length(unique(z)) < 2)))
if (length(drop_const)) cat("dropping constant columns:", drop_const, "\n")

#  Every imputed item is categorical, so the methods are polyreg and logreg
#  rather than predictive mean matching. The two matching variables added below
#  enter as raw predictors rather than through the logit propensity score: the
#  score is a function of survey_ord, num_diagnosis and ehr_length_days, and
#  giving the imputation model the three directly is both more stable and
#  easier to explain to a reviewer than giving it their summary.
make_meth <- function(dat) {
  m <- make.method(dat); m[] <- ""
  m["f.income"] <- m["f.education"] <- m["f.employment"] <- m["f.housing"] <- "polyreg"
  m["f.housing_stability"] <- "logreg"
  m
}
run_mice <- function(cols, seed, tag) {
  dat <- P[, cols]
  cat("\n--", tag, ": predictors =", ncol(dat), "columns\n")
  t0 <- Sys.time()
  mi <- mice(dat, m = M, maxit = 5, method = make_meth(dat),
             predictorMatrix = make.predictorMatrix(dat),
             printFlag = FALSE, seed = seed)
  cat("   done in", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "min\n")
  if (nrow(mi$loggedEvents %||% data.frame())) print(head(mi$loggedEvents, 20))
  lapply(seq_len(M), function(k) complete(mi, k)[, IMP])
}
`%||%` <- function(a, b) if (is.null(a)) b else a

keep     <- setdiff(names(P), c("person_id", drop_const))
COLS_LEG <- setdiff(keep, c("num_diagnosis", "ehr_length_days"))
COLS_CON <- keep

IMPS_LEG <- run_mice(COLS_LEG, 20260904, "legacy (frozen predictor set)")
IMPS_CON <- run_mice(COLS_CON, 20260904, "congenial (+ num_diagnosis, ehr_length_days)")
saveRDS(list(person_id = P$person_id, imps = IMPS_LEG), file.path(OUT, "imputations_legacy.rds"))
saveRDS(list(person_id = P$person_id, imps = IMPS_CON), file.path(OUT, "imputations.rds"))

idx <- match(d$person_id, P$person_id)
apply_imp <- function(IMPS, k) {
  dk <- d
  for (v in IMP) dk[[v]] <- IMPS[[k]][[v]][idx]
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
fit_all <- function(IMPS, formula, label, prep = identity) {
  CO <- VA <- list(); fails <- 0
  for (k in seq_len(M)) {
    dk <- prep(apply_imp(IMPS, k))
    fk <- tryCatch(clogit(formula, data = dk, method = "efron"), error = function(e) NULL)
    if (is.null(fk) || any(is.na(coef(fk)))) { fails <- fails + 1; next }
    CO[[length(CO) + 1]] <- coef(fk)
    VA[[length(VA) + 1]] <- tryCatch(sandwich::vcovCL(fk, cluster = dk$person_id),
                                     error = function(e) vcov(fk))
    if (k %% 10 == 0) cat("   ", label, k, "of", M, "\n")
  }
  cat(label, ": fitted", length(CO), "of", M, "| failures", fails, "\n")
  if (length(CO) < 2) return(NULL)
  pool_full(CO, VA)
}
tab <- function(p) {
  se <- sqrt(diag(p$Tv))
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
SD <- "^f\\.(income|insurance|education|employment|housing|race)"

cat("\n===== joint model, legacy predictor set (reproduction check) =====\n")
pl <- fit_all(IMPS_LEG, f_joint, "legacy")
tl <- tab(pl); write.csv(tl, file.path(OUT, "joint_legacy.csv"), row.names = FALSE)
print(tl[grep(SD, tl$term), ], row.names = FALSE, digits = 3)
cat("\n>> compare the rows above against the frozen mi40_joint.csv.\n",
    ">> If they do not match, stop and pull step8b.R from the bucket.\n", sep = "")

cat("\n===== joint model, congenial predictor set (NEW PRIMARY) =====\n")
pc <- fit_all(IMPS_CON, f_joint, "congenial")
tc <- tab(pc); write.csv(tc, file.path(OUT, "joint_congenial.csv"), row.names = FALSE)
saveRDS(pc, file.path(OUT, "pooled_cov.rds"))
print(tc[grep(SD, tc$term), ], row.names = FALSE, digits = 3)

cmp <- merge(tl[, c("term", "aor", "lo", "hi")], tc[, c("term", "aor", "lo", "hi")],
             by = "term", suffixes = c("_legacy", "_congenial"))
cmp$abs_log_diff <- abs(log(cmp$aor_congenial) - log(cmp$aor_legacy))
cmp <- cmp[order(-cmp$abs_log_diff), ]
write.csv(cmp, file.path(OUT, "spec_compare.csv"), row.names = FALSE)
cat("\nlargest movements between the two imputation models:\n")
print(head(cmp[grep(SD, cmp$term), ], 12), row.names = FALSE, digits = 3)

## ---------------------------------------------------------------- the shape
HI <- grep("^f\\.income(100k_150k|150k_200k|more_200k)$", pc$nm, value = TRUE)
LO <- grep("^f\\.income(less_10k|10k_25k|25k_35k)$", pc$nm, value = TRUE)
cat("\n===== income block tests on the primary (D1) =====\n")
cat("high strata:", paste(HI, collapse = ", "), "\n"); hi <- D1(pc, HI); print(round(hi, 4))
cat("low strata :", paste(LO, collapse = ", "), "\n"); lo <- D1(pc, LO); print(round(lo, 4))
write.csv(rbind(
  data.frame(test = "high_income_block_D1", F = hi["F"], df1 = hi["df1"],
             df2 = hi["df2"], p = hi["p"], row.names = NULL),
  data.frame(test = "low_income_block_D1", F = lo["F"], df1 = lo["df1"],
             df2 = lo["df2"], p = lo["p"], row.names = NULL)),
  file.path(OUT, "income_block_tests.csv"), row.names = FALSE)

MID  <- c(less_10k = 5, "10k_25k" = 17.5, "25k_35k" = 30, "35k_100k" = 67.5,
          "100k_150k" = 125, "150k_200k" = 175, more_200k = 250)   # $ thousands
RANK <- setNames(seq_along(MID), names(MID))
f_score <- as.formula(paste("Treatment ~", base_rhs, "+",
                            sub("f.income", "inc_score", joint_rhs, fixed = TRUE),
                            "+ strata(stratum)"))
shape <- list()
for (sc in c("log10_midpoint", "rank")) {
  ps <- fit_all(IMPS_CON, f_score, paste("trend", sc), prep = function(dk) {
    lev <- as.character(dk$f.income)
    dk$inc_score <- if (sc == "rank") RANK[lev] else log10(MID[lev] * 1000)
    dk
  })
  if (is.null(ps)) next
  j <- which(ps$nm == "inc_score"); s <- sqrt(ps$Tv[j, j])
  shape[[sc]] <- data.frame(score = sc, or_per_step = exp(ps$qbar[j]),
    lo = exp(ps$qbar[j] - 1.96 * s), hi = exp(ps$qbar[j] + 1.96 * s),
    p = 2 * pnorm(-abs(ps$qbar[j] / s)), row.names = NULL)
  cat("\ntrend,", sc, ":\n"); print(shape[[sc]], row.names = FALSE, digits = 3)
}
if (length(shape)) write.csv(do.call(rbind, shape),
  file.path(OUT, "income_shape.csv"), row.names = FALSE)

cat("\nDONE\n")
sink()
