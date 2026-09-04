## batchB.R — items 2, 3 and 4.
##   2. split "unable to work" (1585960) out of the unemployed level, COVID + flu
##   3. influenza domain-by-period interaction as cluster-robust Wald, not LR
##   4. who the housing-instability group is
suppressPackageStartupMessages({library(survival); library(sandwich)})
OUT <- "/home/jupyter/batchA"
sink(file.path(OUT, "batchB.txt"))

FL <- read.csv(file.path(OUT, "employment_unemp_flags.csv"))
FL$out <- pmax(FL$out_1yr, FL$out_lt1yr)

split5 <- function(pid, emp) {
  i <- match(pid, FL$person_id)
  out  <- ifelse(is.na(i), 0L, FL$out[i])
  unab <- ifelse(is.na(i), 0L, FL$unable[i])
  new <- as.character(emp)
  sel <- new %in% c("Unemployed")
  new[sel & unab == 1 & out == 0] <- "Unable_to_work"
  new[sel & unab == 1 & out == 1] <- "MIXED"
  new[sel & unab == 0 & out == 1] <- "Unemployed"
  new[sel & unab == 0 & out == 0] <- "NOFLAG"
  new
}

# ============================================================ COVID-19
X <- readRDS("/home/jupyter/refit_nodis/results/aou_v7/joint_model_inputs.rds")
d <- X$df
d$new <- split5(d$person_id, d$f.employment)

cat("===== COVID: employment recoding =====\n")
cat("observation level:\n"); print(table(d$new, d$Treatment))
P <- d[!duplicated(d$person_id), ]
cat("\nperson level:\n"); print(table(P$new, P$Treatment))
cat("\nMIXED (gave both an unable and an out-of-work answer):",
    sum(d$new == "MIXED"), "observations,", sum(P$new == "MIXED"), "persons\n")
cat("NOFLAG (labelled Unemployed but no flag found):",
    sum(d$new == "NOFLAG"), "observations,", sum(P$new == "NOFLAG"), "persons\n")

fit_covid <- function(assign_mixed) {
  z <- d$new
  z[z == "MIXED"] <- assign_mixed
  z[z == "NOFLAG"] <- "Unemployed"
  dd <- d
  dd$f.emp5 <- relevel(factor(z), ref = "Employed")
  rhs <- sub("f.employment", "f.emp5", X$joint_sdoh, fixed = TRUE)
  f <- as.formula(paste("Treatment ~", X$base_rhs, "+", rhs, "+ strata(stratum)"))
  fit <- clogit(f, data = dd, method = "exact")
  s <- summary(fit)
  ci <- s$conf.int; co <- s$coefficients
  r <- data.frame(term = rownames(ci), aor = ci[, 1], lo = ci[, 3], hi = ci[, 4],
                  p = co[, ncol(co)], row.names = NULL)
  r[grepl("^f\\.(emp5|income|insurance|education|housing)", r$term), ]
}
cat("\n----- COVID joint model, MIXED -> Unable_to_work -----\n")
a <- fit_covid("Unable_to_work"); print(a, row.names = FALSE, digits = 3)
cat("\n----- COVID joint model, MIXED -> Unemployed -----\n")
b <- fit_covid("Unemployed"); print(b, row.names = FALSE, digits = 3)
write.csv(a, file.path(OUT, "covid_emp5_mixed_unable.csv"), row.names = FALSE)
write.csv(b, file.path(OUT, "covid_emp5_mixed_unemployed.csv"), row.names = FALSE)

# ============================================================ INFLUENZA
m <- read.csv("/home/jupyter/flu/07_matched_cohort.csv", stringsAsFactors = FALSE)
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
m$insurance_type <- rl(m$insurance_type, "Employer"); m$age_group <- rl(m$age_group, "18-44")
m$race <- rl(m$race, "White"); m$period <- rl(factor(m$period), "3_post")
BASE <- paste(c("sex_at_birth","race","ethnicity","age_group",CH), collapse = " + ")
DOM <- c("insurance_type","income","employment","education","housing","housing_stability")
JOINT <- paste(DOM, collapse = " + ")

m$new <- split5(m$person_id, m$employment)
cat("\n\n===== INFLUENZA: employment recoding =====\n")
cat("person-season level:\n"); print(table(m$new, m$Treatment))
mp <- m[!duplicated(m$person_id), ]
cat("\nperson level:\n"); print(table(mp$new, mp$Treatment))

fit_flu <- function(assign_mixed) {
  z <- m$new; z[z == "MIXED"] <- assign_mixed; z[z == "NOFLAG"] <- "Unemployed"
  mm <- m; mm$emp5 <- relevel(factor(z), ref = "Employed")
  rhs <- sub("employment", "emp5", JOINT, fixed = TRUE)
  f <- as.formula(paste("Treatment ~", BASE, "+", rhs, "+ strata(subclass)"))
  fit <- clogit(f, data = mm, method = "efron", cluster = person_id)
  s <- summary(fit); ci <- s$conf.int; co <- s$coefficients
  r <- data.frame(term = rownames(ci), aor = ci[, 1], lo = ci[, 3], hi = ci[, 4],
                  p = co[, ncol(co)], row.names = NULL)
  r[grepl("^(emp5|income|insurance_type|education|housing)", r$term), ]
}
cat("\n----- influenza joint model, MIXED -> Unable_to_work -----\n")
fa <- fit_flu("Unable_to_work"); print(fa, row.names = FALSE, digits = 3)
write.csv(fa, file.path(OUT, "flu_emp5_mixed_unable.csv"), row.names = FALSE)

# ---------------- item 3: interaction as cluster-robust Wald
block_wald <- function(fit, pattern, dat) {
  V <- sandwich::vcovCL(fit, cluster = dat$person_id)
  b <- coef(fit)
  idx <- grep(pattern, names(b))
  idx <- idx[!is.na(b[idx])]
  Vs <- V[idx, idx, drop = FALSE]
  q <- as.numeric(t(b[idx]) %*% solve(Vs) %*% b[idx])
  c(chisq = q, df = length(idx), p = pchisq(q, length(idx), lower.tail = FALSE))
}
cat("\n\n===== INFLUENZA: domain x period, cluster-robust Wald vs likelihood ratio =====\n")
cat(sprintf("%-20s %9s %4s %10s | %9s %4s %10s\n",
            "domain x period", "Wald", "df", "P(Wald)", "LR", "df", "P(LR)"))
res <- list()
f0 <- as.formula(paste("Treatment ~", BASE, "+", JOINT, "+ strata(subclass)"))
m0 <- clogit(f0, data = m, method = "efron")
for (dm in DOM) {
  f1 <- as.formula(paste("Treatment ~", BASE, "+", JOINT, "+", dm,
                         ":period + strata(subclass)"))
  m1 <- clogit(f1, data = m, method = "efron")
  w <- block_wald(m1, paste0("^", dm, ".*:period|period.*:", dm), m)
  a <- anova(m0, m1, test = "Chisq")
  cat(sprintf("%-20s %9.2f %4d %10.4f | %9.2f %4d %10.4f\n", dm,
              w["chisq"], w["df"], w["p"],
              a[2, "Chisq"], a[2, "Df"], a[2, "Pr(>|Chi|)"]))
  res[[length(res) + 1]] <- data.frame(domain = dm, wald_chisq = w["chisq"],
    wald_df = w["df"], wald_p = w["p"], lr_chisq = a[2, "Chisq"],
    lr_df = a[2, "Df"], lr_p = a[2, "Pr(>|Chi|)"], row.names = NULL)
}
write.csv(do.call(rbind, res), file.path(OUT, "flu_interaction_wald.csv"), row.names = FALSE)

# ============================================================ item 4
cat("\n\n===== who the housing-instability group is (COVID matched cohort) =====\n")
P$hs <- as.character(P$f.housing_stability)
P$nch <- rowSums(P[, CH])
cat("person level, by housing stability:\n")
for (g in c("Stable", "Unstable", "Missing")) {
  z <- P[P$hs == g, ]
  cat(sprintf("%-9s n=%6d  cases %5d  mean age %5.1f  %%age<45 %5.1f  %%female %5.1f  %%Black %5.1f  mean Charlson %4.2f  %%income<25k %5.1f  %%unemployed %5.1f\n",
      g, nrow(z), sum(z$Treatment == 1), mean(z$age_at_covid),
      100 * mean(z$f.age == "<45"), 100 * mean(z$f.sex == "Female"),
      100 * mean(z$f.race == "Black"), mean(z$nch),
      100 * mean(z$f.income %in% c("less_10k", "10k_25k")),
      100 * mean(z$f.employment == "Unemployed")))
}
cat("\nhousing stability x housing tenure (persons):\n")
print(table(P$f.housing_stability, P$f.housing))
sink()
writeLines("DONE", file.path(OUT, "BDONE"))
