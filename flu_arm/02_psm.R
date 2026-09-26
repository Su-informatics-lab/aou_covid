
suppressPackageStartupMessages({library(MatchIt); library(survival)})
set.seed(42)
d <- read.csv("/home/jupyter/flu/flu_prematch.csv", stringsAsFactors = FALSE)
MATCH_COVS <- c("survey_ord","num_diagnosis","ehr_length_days")
d <- d[complete.cases(d[, MATCH_COVS]), ]
m <- matchit(Treatment ~ survey_ord + num_diagnosis + ehr_length_days,
             data = d, method="nearest", distance="glm", ratio=4, replace=TRUE,
             caliper=0.2, std.caliper=TRUE, exact = ~ season)
# replace=TRUE -> get_matches(), not match.data(): a control can sit in several
# strata, so we need one ROW PER MATCH. This is why control observations exceed
# control persons, exactly as in the COVID cohort.
gm <- get_matches(m, distance="ps")
cat(sprintf("matched rows %d | cases %d | control obs %d | unique controls %d | strata %d\n",
  nrow(gm), sum(gm$Treatment==1), sum(gm$Treatment==0),
  length(unique(gm$person_id[gm$Treatment==0])), length(unique(gm$subclass))))
cat(sprintf("control obs per case: %.2f\n", sum(gm$Treatment==0)/sum(gm$Treatment==1)))
ru <- table(gm$person_id[gm$Treatment==0])
cat("max control reuse:", max(ru), " median:", median(ru), "\n")
cat("\nby period (rows):\n"); print(table(gm$period, gm$Treatment))
tb <- table(gm$subclass, gm$Treatment)
cat("\ninformative strata (>=1 case & >=1 control):", sum(tb[,1]>0 & tb[,2]>0),
    "of", nrow(tb), "\n")
s <- summary(m)
cat("\nSMD after matching:\n")
print(round(s$sum.matched[1:4, "Std. Mean Diff.", drop=FALSE], 4))
cat("cases dropped (no match in caliper):", sum(m$treat==1)-length(unique(gm$subclass)), "\n")
write.csv(gm, "/home/jupyter/flu/07_matched_cohort.csv", row.names=FALSE)
