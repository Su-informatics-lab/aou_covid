
suppressPackageStartupMessages({library(survival)})
m <- read.csv("/home/jupyter/flu/07_matched_cohort.csv", stringsAsFactors=FALSE)
CH <- c("Myocardial_Infarction","Congestive_Heart_Failure","Peripheral_Vascular_Disease",
"Cerebrovascular_Disease","Dementia","Chronic_Pulmonary_Disease","Rheumatic_Disease",
"Peptic_Ulcer_Disease","Liver_Disease_Mild","Liver_Disease_Moderate_Severe",
"Diabetes_without_Chronic_Complications","Diabetes_with_Chronic_Complications",
"Hemiplegia_Paraplegia","Renal_Disease_Mild_Moderate","Renal_Disease_Severe","HIV",
"Metastatic_Solid_Tumor","Malignancy","AIDS")
rl <- function(x,r) relevel(factor(x), ref=r)
m$income<-rl(m$income,"35k_100k"); m$employment<-rl(m$employment,"Employed")
m$education<-rl(m$education,"GED_or_College"); m$housing<-rl(m$housing,"Own")
m$housing_stability<-rl(m$housing_stability,"Stable")
m$insurance_type<-rl(m$insurance_type,"Employer"); m$age_group<-rl(m$age_group,"18-44")
m$race<-rl(m$race,"White"); m$period<-rl(factor(m$period),"3_post")
BASE <- paste(c("sex_at_birth","race","ethnicity","age_group",CH), collapse=" + ")
DOM <- c("insurance_type","income","employment","education","housing","housing_stability")
JOINT <- paste(DOM, collapse=" + ")
# One model carrying ALL five domains plus ONE domain-by-period interaction at a
# time, tested against the same model without it. Period main effects are
# conditioned out by the strata (season is exact-matched), so the interaction is
# identified off within-stratum contrasts only.
cat(sprintf("%-20s %8s %5s %10s\n","domain x period","chisq","df","P"))
for (dm in DOM) {
  f0 <- as.formula(paste("Treatment ~", BASE, "+", JOINT, "+ strata(subclass)"))
  f1 <- as.formula(paste("Treatment ~", BASE, "+", JOINT, "+", dm, ":period + strata(subclass)"))
  m0 <- clogit(f0, data=m, method="efron"); m1 <- clogit(f1, data=m, method="efron")
  a <- anova(m0, m1, test="Chisq")
  cat(sprintf("%-20s %8.2f %5d %10.4f\n", dm, a[2,"Chisq"], a[2,"Df"], a[2,"Pr(>|Chi|)"]))
}
