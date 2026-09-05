## 03d_mi40_shape.R — is the income association a gradient, or is the U an
## artefact of the missing-indicator specification?
##
## Runs on the All of Us Researcher Workbench. Nothing person-level leaves it.
##
## Why this exists. Under the primary specification the jointly adjusted income
## estimates are 1.21, 1.21, 1.10, 1.22, 1.26, 1.15 from the lowest band to the
## highest, against a $35,000-99,999 reference: the two lowest strata and two of
## the three highest are all elevated. That is not a gradient, and calling it one
## is false on our own Table 3. Two things already suggest the U belongs to the
## specification and not to the data: under m = 40 imputation the same model
## gives 1.51, 1.40, 1.18, 1.16, 1.20, 1.09, and the influenza arm under the
## indicator specification gives 1.55, 1.83, 1.28, 1.05, 0.91, 0.94. This script
## tests it rather than eyeballing it.
##
## It also saves the 40 imputed person-level frames so that 03e can fit the
## interaction models without paying for mice again.
##
## Acceptance test: the joint column must reproduce mi40_joint.csv from the
## frozen aou_v7_5domain_mi40 run. If it does not, the frozen run used different
## settings and step8b.R should be pulled from the bucket before anything here
## is believed.
##
## Output: /home/jupyter/mi40b/{log.txt, joint.csv, income_shape.csv,
##         pooled_cov.rds, imputations.rds}

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
IMP <- c("f.income", "f.education", "f.employment", "f.housing", "f.housing_stability")
f_joint <- as.formula(paste("Treatment ~", base_rhs, "+", joint_rhs, "+ strata(stratum)"))

cat("mice", as.character(packageVersion("mice")),
    "| rows", nrow(d), "persons", length(unique(d$person_id)),
    "strata", length(unique(d$stratum)), "| m =", M, "\n")

## ---- person-level frame, same construction as 03b --------------------------
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

tim <- read.csv(file.path(RES, "04b_sdoh_timing.csv"))
P$survey_ord <- as.numeric(as.Date(tim$basics_survey_date[match(P$person_id, tim$person_id)]))
P$survey_ord[is.na(P$survey_ord)] <- median(P$survey_ord, na.rm = TRUE)

for (v in IMP) {
  z <- as.character(P[[v]]); z[z == "Missing"] <- NA
  P[[v]] <- factor(z, levels = setdiff(levels(d[[v]]), "Missing"))
}
drop_const <- names(which(sapply(P[, CH, drop = FALSE], function(z) length(unique(z)) < 2)))
MIDAT <- P[, setdiff(names(P), c("person_id", drop_const))]
meth <- make.method(MIDAT); meth[] <- ""
meth["f.income"] <- meth["f.education"] <- meth["f.employment"] <-
  meth["f.housing"] <- "polyreg"
meth["f.housing_stability"] <- "logreg"

t0 <- Sys.time()
mi <- mice(MIDAT, m = M, maxit = 5, method = meth,
           predictorMatrix = make.predictorMatrix(MIDAT),
           printFlag = FALSE, seed = 20260904)
cat("mice done in", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "min\n")

IMPS <- lapply(seq_len(M), function(k) complete(mi, k)[, IMP])
saveRDS(list(person_id = P$person_id, imps = IMPS),
        file.path(OUT, "imputations.rds"))

idx <- match(d$person_id, P$person_id)
apply_imp <- function(k) {
  dk <- d
  for (v in IMP) dk[[v]] <- IMPS[[k]][[v]][idx]
  dk
}

## ---- Rubin pooling with the FULL covariance, so a block can be tested ------
pool_full <- function(CO, VA) {
  nm <- names(CO[[1]])
  Q  <- sapply(CO, function(z) z[nm])
  Ubar <- Reduce(`+`, lapply(VA, function(v) v[nm, nm])) / length(VA)
  B    <- if (length(VA) > 1) stats::cov(t(Q)) else Ubar * 0
  list(qbar = rowMeans(Q), Ubar = Ubar, B = B,
       Tv = Ubar + (1 + 1 / length(VA)) * B, m = length(VA), nm = nm)
}

## D1, the multivariate Wald of Li, Raghunathan and Rubin, on a subset of terms.
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
  c(F = stat, df1 = k, df2 = df2, r1 = r1,
    p = pf(stat, k, df2, lower.tail = FALSE))
}

fit_all <- function(formula, label) {
  CO <- VA <- vector("list", M)
  for (k in seq_len(M)) {
    dk <- apply_imp(k)
    fk <- clogit(formula, data = dk, method = "efron")
    CO[[k]] <- coef(fk)
    VA[[k]] <- tryCatch(sandwich::vcovCL(fk, cluster = dk$person_id),
                        error = function(e) vcov(fk))
    if (k %% 10 == 0) cat("   ", label, k, "of", M, "\n")
  }
  pool_full(CO, VA)
}

cat("\n== joint model ==\n")
pj <- fit_all(f_joint, "joint")
se <- sqrt(diag(pj$Tv))
lam <- (1 + 1 / M) * diag(pj$B) / diag(pj$Tv)
lam <- pmin(pmax(lam, 1e-8), 1 - 1e-8)
nu_old <- (M - 1) / lam^2
nu_com <- nrow(d) - length(pj$nm)
nu_obs <- (nu_com + 1) / (nu_com + 3) * nu_com * (1 - lam)
nu  <- nu_old * nu_obs / (nu_old + nu_obs)
fmi <- (nu + 1) / (nu + 3) * lam + 2 / (nu + 3)
cr  <- qt(0.975, nu)
joint <- data.frame(
  term = pj$nm,
  aor  = exp(pj$qbar),
  lo   = exp(pj$qbar - cr * se),
  hi   = exp(pj$qbar + cr * se),
  fmi  = round(fmi, 3), row.names = NULL)
write.csv(joint, file.path(OUT, "joint.csv"), row.names = FALSE)
saveRDS(pj, file.path(OUT, "pooled_cov.rds"))
cat("\nSDoH rows (compare against the frozen mi40_joint.csv):\n")
print(joint[grep("^f\\.(income|insurance|education|employment|housing|race)", joint$term), ],
      row.names = FALSE, digits = 3)

## ---- income shape ---------------------------------------------------------
## (a) is the high-income block distinguishable from the reference at all?
HI <- grep("^f\\.income(100k_150k|150k_200k|more_200k)$", pj$nm, value = TRUE)
LO <- grep("^f\\.income(less_10k|10k_25k|25k_35k)$", pj$nm, value = TRUE)
cat("\n== income block tests (D1) ==\n")
cat("high strata:", paste(HI, collapse = ", "), "\n")
hi <- D1(pj, HI); print(round(hi, 4))
cat("low strata :", paste(LO, collapse = ", "), "\n")
lo <- D1(pj, LO); print(round(lo, 4))

## (b) linear trend, income entered as a score instead of a factor
MID <- c(less_10k = 5, "10k_25k" = 17.5, "25k_35k" = 30, "35k_100k" = 67.5,
         "100k_150k" = 125, "150k_200k" = 175, more_200k = 250)   # $ thousands
RANK <- setNames(seq_along(MID), names(MID))
score_rhs <- sub("f.income", "inc_score", joint_rhs, fixed = TRUE)
f_score <- as.formula(paste("Treatment ~", base_rhs, "+", score_rhs,
                            "+ strata(stratum)"))
shape <- list()
for (sc in c("log10_midpoint", "rank")) {
  CO <- VA <- vector("list", M)
  for (k in seq_len(M)) {
    dk <- apply_imp(k)
    lev <- as.character(dk$f.income)
    dk$inc_score <- if (sc == "rank") RANK[lev] else log10(MID[lev] * 1000)
    fk <- clogit(f_score, data = dk, method = "efron")
    CO[[k]] <- coef(fk)
    VA[[k]] <- tryCatch(sandwich::vcovCL(fk, cluster = dk$person_id),
                        error = function(e) vcov(fk))
  }
  ps <- pool_full(CO, VA)
  i <- which(ps$nm == "inc_score")
  s <- sqrt(ps$Tv[i, i])
  shape[[sc]] <- data.frame(
    score = sc, beta = ps$qbar[i], se = s,
    or_per_step = exp(ps$qbar[i]),
    lo = exp(ps$qbar[i] - 1.96 * s), hi = exp(ps$qbar[i] + 1.96 * s),
    p = 2 * pnorm(-abs(ps$qbar[i] / s)), row.names = NULL)
  cat("\ntrend,", sc, ":\n"); print(shape[[sc]], row.names = FALSE, digits = 3)
}

write.csv(rbind(
  data.frame(test = "high_income_block_D1", statistic = hi["F"], df1 = hi["df1"],
             df2 = hi["df2"], p = hi["p"], row.names = NULL),
  data.frame(test = "low_income_block_D1", statistic = lo["F"], df1 = lo["df1"],
             df2 = lo["df2"], p = lo["p"], row.names = NULL)),
  file.path(OUT, "income_block_tests.csv"), row.names = FALSE)
write.csv(do.call(rbind, shape), file.path(OUT, "income_shape.csv"), row.names = FALSE)

cat("\nDONE\n")
sink()
