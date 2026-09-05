## 03g_insurance_recency.R — is the Medicaid decline a change in access, or a
## label going stale?
##
## Runs on the All of Us Researcher Workbench. Nothing person-level leaves it.
##
## Why this exists. Insurance is self-reported on The Basics, a median of 692
## days (IQR 286-985) before the index date. Two readings of the same fact are
## on the table for the fall in jointly adjusted Medicaid from 1.52 (1.22-1.89)
## before Delta to 0.99 (0.73-1.34) during Omicron:
##
##   access      Medicaid stopped marking constrained access once testing,
##               vaccination and care were free at the point of use.
##   composition the continuous-enrolment requirement of the federal public
##               health emergency (March 2020 to March 2023) held people on
##               Medicaid who would otherwise have churned off, so the people
##               the label covers changed over the window.
##
## The design cannot separate them outright, but staleness is testable. If the
## decline is a label drifting from the truth, it should be steeper among
## participants whose survey is older, because their label has had longer to go
## wrong. If the decline is the same at every recency, staleness is not what is
## driving it, and the composition reading has to work through actual coverage
## rather than through misclassification.
##
## Note what this cannot do: the whole COVID-19 window sits inside the public
## health emergency, so there is no within-COVID contrast of PHE against no-PHE.
## The influenza arm has one, and 03f covers it.
##
## Output: /home/jupyter/recency/{log.txt, medicaid_by_recency.csv,
##         medicaid_recency_interaction.csv, recency_describe.csv}

suppressPackageStartupMessages({library(survival); library(sandwich)})

RES <- "/home/jupyter/refit_nodis/results/aou_v7"
OUT <- "/home/jupyter/recency"
dir.create(OUT, showWarnings = FALSE)
sink(file.path(OUT, "log.txt"), split = TRUE)

X <- readRDS(file.path(RES, "joint_model_inputs.rds"))
d <- X$df
tim <- read.csv(file.path(RES, "04b_sdoh_timing.csv"))
cat("timing columns:", paste(names(tim), collapse = ", "), "\n")

d$gap <- tim$sdoh_days_before_covid[match(d$person_id, tim$person_id)]
cat("gap missing for", sum(is.na(d$gap)), "of", nrow(d), "observations\n")
cat("gap quantiles (days survey -> index):\n")
print(round(quantile(d$gap, c(0, .25, .5, .75, 1), na.rm = TRUE)))

## tertiles of recency among observations with a pre-index survey; surveys taken
## after the index date are their own group because S3 already treats them apart
d$recency <- NA_character_
pre <- !is.na(d$gap) & d$gap >= 0
qs <- quantile(d$gap[pre], c(1/3, 2/3), na.rm = TRUE)
d$recency[pre] <- cut(d$gap[pre], breaks = c(-Inf, qs, Inf),
                      labels = c("recent", "middle", "old"))
d$recency[!is.na(d$gap) & d$gap < 0] <- "post_index"
d$recency <- factor(d$recency, levels = c("recent", "middle", "old", "post_index"))
cat("\nobservations by recency:\n"); print(table(d$recency, useNA = "ifany"))
cat("cut points (days):", paste(round(qs), collapse = ", "), "\n")

desc <- as.data.frame(table(d$recency, d$f.insurance))
names(desc) <- c("recency", "insurance", "observations")
write.csv(desc, file.path(OUT, "recency_describe.csv"), row.names = FALSE)
cat("\ninsurance by recency:\n"); print(table(d$recency, d$f.insurance))

f_joint <- as.formula(paste("Treatment ~", X$base_rhs, "+", X$joint_sdoh,
                            "+ strata(stratum)"))
pull <- function(fit, dat, pattern) {
  V <- tryCatch(sandwich::vcovCL(fit, cluster = dat$person_id),
                error = function(e) vcov(fit))
  b <- coef(fit); s <- sqrt(diag(V))
  k <- grep(pattern, names(b), value = TRUE)
  data.frame(term = k, aor = exp(b[k]), lo = exp(b[k] - 1.96 * s[k]),
             hi = exp(b[k] + 1.96 * s[k]), row.names = NULL)
}

## ---- 1. the joint model refitted within each recency stratum ---------------
cat("\n===== jointly adjusted insurance within each recency stratum =====\n")
rows <- list()
for (g in levels(d$recency)) {
  dz <- droplevels(d[!is.na(d$recency) & d$recency == g, ])
  ok <- tapply(dz$Treatment, dz$stratum, function(z) any(z == 1) && any(z == 0))
  dz <- droplevels(dz[ok[as.character(dz$stratum)], ])
  if (nrow(dz) < 200 || length(unique(dz$stratum)) < 50) {
    cat(g, ": too few strata (", length(unique(dz$stratum)), "), skipped\n"); next
  }
  fit <- tryCatch(clogit(f_joint, data = dz, method = "efron"),
                  error = function(e) NULL)
  if (is.null(fit)) { cat(g, ": did not converge\n"); next }
  r <- pull(fit, dz, "^f\\.insurance|^f\\.income")
  r$recency <- g; r$strata <- length(unique(dz$stratum)); r$cases <- sum(dz$Treatment == 1)
  cat("\n--", g, "| strata", r$strata[1], "| cases", r$cases[1], "\n")
  print(r[, c("term", "aor", "lo", "hi")], row.names = FALSE, digits = 3)
  rows[[g]] <- r
}
if (length(rows)) write.csv(do.call(rbind, rows),
  file.path(OUT, "medicaid_by_recency.csv"), row.names = FALSE)

## ---- 2. the interaction, which is the actual test -------------------------
cat("\n===== insurance x recency, cluster-robust block Wald =====\n")
dd <- droplevels(d[!is.na(d$recency) & d$recency != "post_index", ])
f_int <- as.formula(paste("Treatment ~", X$base_rhs, "+", X$joint_sdoh,
                          "+ f.insurance:recency + strata(stratum)"))
fit <- clogit(f_int, data = dd, method = "efron")
V <- sandwich::vcovCL(fit, cluster = dd$person_id)
b <- coef(fit)
k <- grep("f\\.insurance.*:recency|recency.*:f\\.insurance", names(b))
k <- k[!is.na(b[k])]
q <- as.numeric(t(b[k]) %*% solve(V[k, k, drop = FALSE]) %*% b[k])
cat(sprintf("insurance x recency: chi-square %.2f, %d df, P = %.4g\n",
            q, length(k), pchisq(q, length(k), lower.tail = FALSE)))

## and the three-way, which is what the staleness reading actually predicts:
## the wave effect on Medicaid should differ by recency
cat("\n===== insurance x wave x recency =====\n")
f3 <- as.formula(paste("Treatment ~", X$base_rhs, "+", X$joint_sdoh,
                       "+ f.insurance:f.wave:recency + f.insurance:f.wave",
                       "+ f.insurance:recency + strata(stratum)"))
f3fit <- tryCatch(clogit(f3, data = dd, method = "efron"), error = function(e) NULL)
if (is.null(f3fit) || all(is.na(coef(f3fit)))) {
  cat("three-way term not estimable; report the two-way and say so\n")
  three <- data.frame(test = "insurance_x_wave_x_recency", chisq = NA,
                      df = NA, p = NA, note = "not estimable")
} else {
  V3 <- sandwich::vcovCL(f3fit, cluster = dd$person_id)
  b3 <- coef(f3fit)
  k3 <- grep("f\\.insurance.*:f\\.wave.*:recency", names(b3))
  k3 <- k3[!is.na(b3[k3])]
  if (length(k3) == 0) {
    cat("no three-way terms retained\n")
    three <- data.frame(test = "insurance_x_wave_x_recency", chisq = NA,
                        df = 0, p = NA, note = "no terms retained")
  } else {
    q3 <- as.numeric(t(b3[k3]) %*% solve(V3[k3, k3, drop = FALSE]) %*% b3[k3])
    p3 <- pchisq(q3, length(k3), lower.tail = FALSE)
    cat(sprintf("insurance x wave x recency: chi-square %.2f, %d df, P = %.4g\n",
                q3, length(k3), p3))
    three <- data.frame(test = "insurance_x_wave_x_recency", chisq = q3,
                        df = length(k3), p = p3, note = "")
  }
}
write.csv(rbind(
  data.frame(test = "insurance_x_recency", chisq = q, df = length(k),
             p = pchisq(q, length(k), lower.tail = FALSE), note = ""),
  three),
  file.path(OUT, "medicaid_recency_interaction.csv"), row.names = FALSE)

cat("\nDONE\n")
sink()
