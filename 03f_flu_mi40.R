## 03f_flu_mi40.R — the influenza arm under the same primary specification as
## the COVID-19 arm, and the shape of its income association.
##
## Runs on the All of Us Researcher Workbench. Nothing person-level leaves it.
##
## Why this exists. Two reasons, and the second is the more important.
##
##   1. If multiple imputation becomes primary for COVID-19, influenza cannot
##      stay on the missing-indicator model. Influenza has the same problem in
##      the same place: jointly adjusted income Missing is 1.43 (1.18-1.73),
##      which is larger than three of the six observed income coefficients.
##   2. The income shape is the claim under test. Under the indicator
##      specification the influenza estimates already run 1.55, 1.83, 1.28,
##      1.05, 0.91, 0.94 from the lowest band to the highest, which is the
##      gradient the COVID-19 arm does not show under the same specification.
##      If imputation gives COVID-19 the same shape, the U is the specification
##      and not the world, and two arms say so independently.
##
## Imputation is at person level: a person contributing several seasons must not
## be given a different income in each.
##
## Output: /home/jupyter/flu_mi40/{log.txt, joint.csv, income_shape.csv,
##         period_interaction_mi.csv, imputations.rds}

suppressPackageStartupMessages({
  library(survival); library(sandwich); library(mice)
})
set.seed(20260905)

FLU <- "/home/jupyter/flu"
OUT <- "/home/jupyter/flu_mi40"
dir.create(OUT, showWarnings = FALSE)
sink(file.path(OUT, "log.txt"), split = TRUE)

M <- 40
m <- read.csv(file.path(FLU, "07_matched_cohort.csv"), stringsAsFactors = FALSE)
CH <- c("Myocardial_Infarction","Congestive_Heart_Failure","Peripheral_Vascular_Disease",
 "Cerebrovascular_Disease","Dementia","Chronic_Pulmonary_Disease","Rheumatic_Disease",
 "Peptic_Ulcer_Disease","Liver_Disease_Mild","Liver_Disease_Moderate_Severe",
 "Diabetes_without_Chronic_Complications","Diabetes_with_Chronic_Complications",
 "Hemiplegia_Paraplegia","Renal_Disease_Mild_Moderate","Renal_Disease_Severe","HIV",
 "Metastatic_Solid_Tumor","Malignancy","AIDS")
rl <- function(x, r) relevel(factor(x), ref = r)
m$income <- rl(m$income, "35k_100k"); m$employment <- rl(m$employment, "Employed")
m$education <- rl(m$education, "GED_or_College"); m$housing <- rl(m$housing, "Own")
m$housing_stability <- rl(m$housing_stability, "Stable")
m$insurance_type <- rl(m$insurance_type, "Employer")
m$age_group <- rl(m$age_group, "18-44"); m$race <- rl(m$race, "White")
m$period <- rl(factor(m$period), "3_post")
BASE  <- paste(c("sex_at_birth","race","ethnicity","age_group",CH), collapse = " + ")
DOM   <- c("insurance_type","income","employment","education","housing","housing_stability")
JOINT <- paste(DOM, collapse = " + ")
IMP   <- c("income","education","employment","housing","housing_stability")
f_joint <- as.formula(paste("Treatment ~", BASE, "+", JOINT, "+ strata(subclass)"))

cat("observations", nrow(m), "| persons", length(unique(m$person_id)),
    "| strata", length(unique(m$subclass)), "| cases", sum(m$Treatment == 1), "\n")
cat("periods:\n"); print(table(m$period))

## ---- person-level frame ---------------------------------------------------
## Unlike the COVID-19 arm, a person here can be a case in one season and a
## control in another, so case status is not constant within a person. That
## makes it a legitimate predictor but not a person-level constant: the
## imputation frame keeps the first row's status, and how many people that
## approximates is printed so the choice is visible rather than assumed.
chk <- tapply(m$Treatment, m$person_id, function(z) length(unique(z)))
cat("persons who are a case in one season and a control in another:",
    sum(chk > 1), "of", length(chk), "\n")
P <- m[!duplicated(m$person_id),
       c("person_id","Treatment","sex_at_birth","race","ethnicity","age_group",
         CH, "insurance_type", IMP)]
rownames(P) <- NULL

## Congeniality. The analysis conditions on a matched stratum, so the
## imputation model has to carry the variables the stratum is a function of.
## The COVID-19 arm matched on survey_ord, num_diagnosis and ehr_length_days
## (01b_psm.R); the influenza arm should be the same three. They may already be
## columns of the matched cohort, or they may be in a matching-variables file
## beside it. Look in both, and say in the log which was found, because an
## imputation model that is missing them is the first thing a reviewer asks
## about and it should not be a matter of anyone's memory.
MVAR <- c("survey_ord", "num_diagnosis", "ehr_length_days")
have <- intersect(MVAR, names(m))
if (length(have)) {
  for (v in have) P[[v]] <- m[[v]][match(P$person_id, m$person_id)]
  cat("matching variables taken from 07_matched_cohort.csv:",
      paste(have, collapse = ", "), "\n")
}
mvf <- file.path(FLU, "06_matching_variables.csv")
if (file.exists(mvf)) {
  mv <- read.csv(mvf)
  cat("06_matching_variables.csv columns:", paste(names(mv), collapse = ", "), "\n")
  i <- match(P$person_id, mv$person_id)
  for (v in setdiff(intersect(MVAR, names(mv)), have)) {
    P[[v]] <- mv[[v]][i]; have <- c(have, v)
  }
}
missing_mv <- setdiff(MVAR, have)
if (length(missing_mv)) {
  cat("!! matching variables NOT found:", paste(missing_mv, collapse = ", "),
      "\n!! the influenza imputation model is not fully congenial with the",
      "matched analysis; say so in Methods rather than leaving it implicit\n")
} else {
  cat("all three matching variables carried in the imputation model\n")
}
for (v in have) if (any(is.na(P[[v]]))) {
  cat("  ", v, "missing for", sum(is.na(P[[v]])), "persons; filled at the median\n")
  P[[v]][is.na(P[[v]])] <- median(P[[v]], na.rm = TRUE)
}

cat("\n===== congeniality checks =====\n")
cat("1. case status in the imputation model: ",
    if ("Treatment" %in% names(P)) "YES" else "NO -- STOP", "\n", sep = "")
cat("2. imputation frame is person level: rows ", nrow(P), " vs persons ",
    length(unique(m$person_id)),
    if (nrow(P) == length(unique(m$person_id))) "  YES" else "  NO -- STOP", "\n", sep = "")
stopifnot("Treatment" %in% names(P), nrow(P) == length(unique(m$person_id)))
cat("3. matching variables carried: ", length(have), " of 3\n", sep = "")
for (v in IMP) {
  z <- as.character(P[[v]]); z[z == "Missing"] <- NA
  P[[v]] <- factor(z, levels = setdiff(levels(m[[v]]), "Missing"))
}
cat("\npersons with a missing value, by item:\n")
print(sapply(P[, IMP], function(z) sum(is.na(z))))
cat("persons total:", nrow(P), "\n")

drop_const <- names(which(sapply(P[, CH, drop = FALSE],
                                 function(z) length(unique(z)) < 2)))
if (length(drop_const)) cat("dropping constant columns:", drop_const, "\n")
MIDAT <- P[, setdiff(names(P), c("person_id", drop_const))]
meth <- make.method(MIDAT); meth[] <- ""
meth["income"] <- meth["education"] <- meth["employment"] <- meth["housing"] <- "polyreg"
meth["housing_stability"] <- "logreg"

t0 <- Sys.time()
mi <- mice(MIDAT, m = M, maxit = 5, method = meth,
           predictorMatrix = make.predictorMatrix(MIDAT),
           printFlag = FALSE, seed = 20260905)
cat("mice done in", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "min\n")
print(mi$loggedEvents)

IMPS <- lapply(seq_len(M), function(k) complete(mi, k)[, IMP])
saveRDS(list(person_id = P$person_id, imps = IMPS), file.path(OUT, "imputations.rds"))
idx <- match(m$person_id, P$person_id)
apply_imp <- function(k) {
  mk <- m
  for (v in IMP) mk[[v]] <- IMPS[[k]][[v]][idx]
  mk
}

pool_full <- function(CO, VA) {
  nm <- Reduce(intersect, lapply(CO, names))
  Q <- sapply(CO, function(z) z[nm])
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
fit_all <- function(formula, label, prep = identity) {
  CO <- VA <- list(); fails <- 0
  for (k in seq_len(M)) {
    mk <- prep(apply_imp(k))
    fk <- tryCatch(clogit(formula, data = mk, method = "efron"), error = function(e) NULL)
    if (is.null(fk) || any(is.na(coef(fk)))) { fails <- fails + 1; next }
    CO[[length(CO) + 1]] <- coef(fk)
    VA[[length(VA) + 1]] <- tryCatch(sandwich::vcovCL(fk, cluster = mk$person_id),
                                     error = function(e) vcov(fk))
    if (k %% 10 == 0) cat("   ", label, k, "of", M, "\n")
  }
  cat(label, ": fitted", length(CO), "of", M, "| failures", fails, "\n")
  if (length(CO) < 2) return(NULL)
  pool_full(CO, VA)
}

## ---- joint model ----------------------------------------------------------
cat("\n===== influenza joint model under imputation =====\n")
pj <- fit_all(f_joint, "joint")
se <- sqrt(diag(pj$Tv))
lam <- (1 + 1 / M) * diag(pj$B) / diag(pj$Tv)
lam <- pmin(pmax(lam, 1e-8), 1 - 1e-8)
nu_old <- (M - 1) / lam^2
nu_com <- nrow(m) - length(pj$nm)
nu_obs <- (nu_com + 1) / (nu_com + 3) * nu_com * (1 - lam)
nu <- nu_old * nu_obs / (nu_old + nu_obs); cr <- qt(0.975, nu)
joint <- data.frame(term = pj$nm, aor = exp(pj$qbar),
                    lo = exp(pj$qbar - cr * se), hi = exp(pj$qbar + cr * se),
                    fmi = round((nu + 1) / (nu + 3) * lam + 2 / (nu + 3), 3),
                    row.names = NULL)
write.csv(joint, file.path(OUT, "joint.csv"), row.names = FALSE)
print(joint[grep("^(income|insurance_type|education|employment|housing)", joint$term), ],
      row.names = FALSE, digits = 3)

## ---- income shape ---------------------------------------------------------
HI <- grep("^income(100k_150k|150k_200k|more_200k)$", pj$nm, value = TRUE)
LO <- grep("^income(less_10k|10k_25k|25k_35k)$", pj$nm, value = TRUE)
cat("\n===== income block tests (D1) =====\n")
cat("high:", paste(HI, collapse = ", "), "\n"); hi <- D1(pj, HI); print(round(hi, 4))
cat("low :", paste(LO, collapse = ", "), "\n"); lo <- D1(pj, LO); print(round(lo, 4))

MID <- c(less_10k = 5, "10k_25k" = 17.5, "25k_35k" = 30, "35k_100k" = 67.5,
         "100k_150k" = 125, "150k_200k" = 175, more_200k = 250)
RANK <- setNames(seq_along(MID), names(MID))
f_score <- as.formula(paste("Treatment ~", BASE, "+",
                            sub("income", "inc_score", JOINT, fixed = TRUE),
                            "+ strata(subclass)"))
shape <- list()
for (sc in c("log10_midpoint", "rank")) {
  ps <- fit_all(f_score, paste("trend", sc), prep = function(mk) {
    lev <- as.character(mk$income)
    mk$inc_score <- if (sc == "rank") RANK[lev] else log10(MID[lev] * 1000)
    mk
  })
  if (is.null(ps)) next
  i <- which(ps$nm == "inc_score"); s <- sqrt(ps$Tv[i, i])
  shape[[sc]] <- data.frame(score = sc, or_per_step = exp(ps$qbar[i]),
    lo = exp(ps$qbar[i] - 1.96 * s), hi = exp(ps$qbar[i] + 1.96 * s),
    p = 2 * pnorm(-abs(ps$qbar[i] / s)), row.names = NULL)
  cat("\ntrend,", sc, ":\n"); print(shape[[sc]], row.names = FALSE, digits = 3)
}
if (length(shape)) write.csv(do.call(rbind, shape),
  file.path(OUT, "income_shape.csv"), row.names = FALSE)
write.csv(rbind(
  data.frame(test = "high_income_block_D1", F = hi["F"], df1 = hi["df1"],
             df2 = hi["df2"], p = hi["p"], row.names = NULL),
  data.frame(test = "low_income_block_D1", F = lo["F"], df1 = lo["df1"],
             df2 = lo["df2"], p = lo["p"], row.names = NULL)),
  file.path(OUT, "income_block_tests.csv"), row.names = FALSE)

## ---- domain x period under imputation -------------------------------------
cat("\n===== domain x period under imputation =====\n")
rows <- list()
for (dm in DOM) {
  f1 <- as.formula(paste("Treatment ~", BASE, "+", JOINT, "+", dm,
                         ":period + strata(subclass)"))
  p1 <- fit_all(f1, paste(dm, "x period"))
  if (is.null(p1)) { cat(dm, ": not estimable under imputation\n"); next }
  keep <- grep(paste0("^", dm, ".*:period|^period.*:", dm), p1$nm, value = TRUE)
  if (!length(keep)) { cat(dm, ": no interaction terms retained\n"); next }
  s <- D1(p1, keep)
  cat(sprintf("%-20s F %8.3f  df1 %3d  df2 %9.1f  P %.4g\n",
              dm, s["F"], s["df1"], s["df2"], s["p"]))
  rows[[dm]] <- data.frame(domain = dm, F = s["F"], df1 = s["df1"],
                           df2 = s["df2"], p = s["p"], row.names = NULL)
}
if (length(rows)) write.csv(do.call(rbind, rows),
  file.path(OUT, "period_interaction_mi.csv"), row.names = FALSE)

cat("\nDONE\n")
sink()
