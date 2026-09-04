## step8_income_mi.R  --- v22 step 8
## Multiple imputation of the four Basics items that were administered to every
## participant (income, education, employment, housing), plus the second housing
## item, at PERSON level, then mapped back to the matched observation level.
## Insurance is not imputed: its missingness is non-administration, and it keeps
## its explicit indicator in all three columns.
##
## Output: results table with three columns -- primary (explicit missing level),
## multiple imputation, complete case.

suppressPackageStartupMessages({
  library(survival); library(sandwich); library(mice)
})
set.seed(20260904)

RES <- "/home/jupyter/refit_nodis/results/aou_v7"
OUT <- "/home/jupyter/mi_out"
dir.create(OUT, showWarnings = FALSE)
LOG <- file.path(OUT, "log.txt")
sink(LOG, split = FALSE)

X         <- readRDS(file.path(RES, "joint_model_inputs.rds"))
d         <- X$df
base_rhs  <- X$base_rhs
joint_rhs <- X$joint_sdoh
IMP <- c("f.income", "f.education", "f.employment", "f.housing", "f.housing_stability")

f_joint <- as.formula(paste("Treatment ~", base_rhs, "+", joint_rhs, "+ strata(stratum)"))
cat("mice version:", as.character(packageVersion("mice")), "\n")
cat("rows", nrow(d), "persons", length(unique(d$person_id)),
    "strata", length(unique(d$stratum)), "\n")

## ---- 0. primary column -----------------------------------------------------
fit_pri <- clogit(f_joint, data = d, method = "exact")
co_pri  <- coef(fit_pri); se_pri <- sqrt(diag(vcov(fit_pri)))

## ---- 1. person-level frame -------------------------------------------------
## matching with replacement puts one person in several strata; imputing at
## observation level would give the same person different incomes.
chk <- tapply(d$Treatment, d$person_id, function(z) length(unique(z)))
cat("max distinct Treatment values within a person:", max(chk), "\n")
stopifnot(max(chk) == 1)

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
P <- d[!duplicated(d$person_id), pv]
rownames(P) <- NULL

tim <- read.csv(file.path(RES, "04b_sdoh_timing.csv"))
P$survey_ord <- as.numeric(as.Date(tim$basics_survey_date[match(P$person_id, tim$person_id)]))
cat("survey date missing for", sum(is.na(P$survey_ord)), "persons\n")
P$survey_ord[is.na(P$survey_ord)] <- median(P$survey_ord, na.rm = TRUE)

## Missing -> NA on the imputed items; the level is dropped so the imputation
## model has no "Missing" category to reproduce.
miss_n <- integer(0)
for (v in IMP) {
  z <- as.character(P[[v]]); z[z == "Missing"] <- NA
  P[[v]] <- factor(z, levels = setdiff(levels(d[[v]]), "Missing"))
  miss_n[v] <- sum(is.na(P[[v]]))
}
cat("persons with a missing value, by item:\n"); print(miss_n)
cat("persons total:", nrow(P), "\n")

## constant columns break mice; drop any comorbidity with no variation
drop_const <- names(which(sapply(P[, CH, drop = FALSE], function(z) length(unique(z)) < 2)))
if (length(drop_const)) cat("dropping constant columns:", drop_const, "\n")

MIDAT <- P[, setdiff(names(P), c("person_id", drop_const))]
meth <- make.method(MIDAT)
meth[] <- ""
meth["f.income"]            <- "polyreg"
meth["f.education"]         <- "polyreg"
meth["f.employment"]        <- "polyreg"
meth["f.housing"]           <- "polyreg"
meth["f.housing_stability"] <- "logreg"
pm <- make.predictorMatrix(MIDAT)

M <- 20
t0 <- Sys.time()
mi <- mice(MIDAT, m = M, maxit = 5, method = meth, predictorMatrix = pm,
           printFlag = FALSE, seed = 20260904)
cat("mice done in", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "min\n")
print(mi$loggedEvents)

## ---- 2. fit on each imputed dataset ---------------------------------------
CO <- vector("list", M); VA <- vector("list", M)
for (k in seq_len(M)) {
  pk <- complete(mi, k)
  idx <- match(d$person_id, P$person_id)
  dk <- d
  for (v in IMP) dk[[v]] <- pk[[v]][idx]
  fk <- clogit(f_joint, data = dk, method = "efron")
  vk <- tryCatch(sandwich::vcovCL(fk, cluster = dk$person_id),
                 error = function(e) { cat("vcovCL failed:", conditionMessage(e), "\n"); vcov(fk) })
  CO[[k]] <- coef(fk); VA[[k]] <- vk
  if (k %% 5 == 0) cat("  fitted", k, "of", M, "\n")
}

nm   <- names(CO[[1]])
Q    <- sapply(CO, function(z) z[nm])
U    <- sapply(VA, function(z) diag(z)[nm])
qbar <- rowMeans(Q)
ubar <- rowMeans(U)
Bv   <- apply(Q, 1, var)
Tv   <- ubar + (1 + 1 / M) * Bv
lam  <- (1 + 1 / M) * Bv / Tv
lam  <- pmin(pmax(lam, 1e-8), 1 - 1e-8)
nu_old <- (M - 1) / lam^2
nu_com <- nrow(d) - length(nm)
nu_obs <- (nu_com + 1) / (nu_com + 3) * nu_com * (1 - lam)
nu     <- nu_old * nu_obs / (nu_old + nu_obs)
fmi    <- (nu + 1) / (nu + 3) * lam + 2 / (nu + 3)
se_mi  <- sqrt(Tv)
crit   <- qt(0.975, nu)

## ---- 3. complete-case column ----------------------------------------------
dcc <- d
for (v in IMP) {
  z <- as.character(dcc[[v]]); z[z == "Missing"] <- NA
  dcc[[v]] <- factor(z, levels = setdiff(levels(d[[v]]), "Missing"))
}
dcc <- dcc[complete.cases(dcc[, IMP]), ]
ok  <- tapply(dcc$Treatment, dcc$stratum, function(z) any(z == 1) && any(z == 0))
dcc <- droplevels(dcc[ok[as.character(dcc$stratum)], ])
cat("complete case rows", nrow(dcc), "strata", length(unique(dcc$stratum)),
    "cases", sum(dcc$Treatment == 1), "\n")
fit_cc <- clogit(f_joint, data = dcc, method = "exact")
co_cc  <- coef(fit_cc); se_cc <- sqrt(diag(vcov(fit_cc)))

## ---- 4. assemble ----------------------------------------------------------
fmt <- function(b, se, cr = 1.959964) {
  sprintf("%.2f (%.2f-%.2f)", exp(b), exp(b - cr * se), exp(b + cr * se))
}
terms_all <- union(names(co_pri), union(nm, names(co_cc)))
res <- data.frame(
  term    = terms_all,
  primary = ifelse(terms_all %in% names(co_pri),
                   fmt(co_pri[terms_all], se_pri[terms_all]), NA),
  mi      = ifelse(terms_all %in% nm,
                   fmt(qbar[terms_all], se_mi[terms_all], crit[terms_all]), NA),
  cc      = ifelse(terms_all %in% names(co_cc),
                   fmt(co_cc[terms_all], se_cc[terms_all]), NA),
  fmi     = ifelse(terms_all %in% nm, round(fmi[terms_all], 3), NA),
  stringsAsFactors = FALSE
)
write.csv(res, file.path(OUT, "etable17_mi.csv"), row.names = FALSE)

raw <- data.frame(term = nm, qbar = qbar, se_mi = se_mi, df = nu, fmi = fmi,
                  lambda = lam, ubar = ubar, B = Bv)
write.csv(raw, file.path(OUT, "mi_pooled_raw.csv"), row.names = FALSE)

meta <- data.frame(
  key = c("m", "maxit", "persons", "observations", "strata", "cases",
          "cc_rows", "cc_strata", "cc_cases",
          paste0("persons_missing_", names(miss_n))),
  value = c(M, 5, nrow(P), nrow(d), length(unique(d$stratum)), sum(d$Treatment == 1),
            nrow(dcc), length(unique(dcc$stratum)), sum(dcc$Treatment == 1),
            as.integer(miss_n)))
write.csv(meta, file.path(OUT, "mi_meta.csv"), row.names = FALSE)

cat("\n==== SDoH rows ====\n")
sel <- grep("^f\\.(income|insurance|education|employment|housing)", res$term)
print(res[sel, ], row.names = FALSE)
cat("\nDONE\n")
sink()
writeLines("DONE", file.path(OUT, "DONE"))
