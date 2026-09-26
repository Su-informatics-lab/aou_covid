## 03z_ard.R -- adjusted risk differences on the absolute scale (R10 review, Adler-Milstein
## persona): the headline is a crude difference in percentage points while the models
## report odds ratios. This puts the adjusted association on the percentage-point scale.
##
## Population: every infected participant eligible before matching (as in eTable 21):
## COVID-19, the 25,160 participants with record and survey data; influenza, the 9,169
## person-seasons that entered matching. Observed survey answers, missing kept as a level.
## Model, by arm: logistic regression of hospitalization within 14 days on income band x
## era, insurance x era, education, employment, housing tenure, housing stability, age
## group, sex, race, the Charlson conditions, and quintiles of the 3 encounter-density
## proxies the matched design balances (first survey date, distinct diagnoses, and
## length of record before the index date). Marginal standardization within each
## era: everyone in the era set to income below $10 000 vs $35 000-99 999 (and Medicaid
## vs employer insurance), predicted risks averaged, the difference in percentage points.
## 95% CIs: percentile bootstrap, 500 resamples of persons (influenza person-seasons are
## resampled by person). Aggregates only.
##   ARM=covid Rscript 03z_ard.R      (or ARM=flu)

ARM <- Sys.getenv("ARM", "covid")
B <- as.integer(Sys.getenv("NBOOT", "500"))
set.seed(20260926)
INC <- c(less_10k = "<10k", `10k_25k` = "10-25k", `25k_35k` = "25-35k", `35k_100k` = "35-100k",
         `100k_150k` = ">=100k", `150k_200k` = ">=100k", more_200k = ">=100k")
if (ARM == "covid") {
  P <- "/home/jupyter/workspace/rw-migration-aou-rw-46c7ae9e/data/covid_sdoh"
  co <- read.csv(file.path(P, "aou_v7", "01_covid_cohort.csv"))
  dm <- read.csv(file.path(P, "aou_v7", "02_demographics.csv"))
  sd <- read.csv(file.path(P, "aou_v7_5domain", "04_sdoh.csv"))
  ch <- read.csv(file.path(P, "aou_v7", "03_charlson.csv"))
  df <- Reduce(function(a, b) merge(a, b, by = "person_id"), list(co, dm, sd))
  df <- merge(df, ch, by = "person_id", all.x = TRUE)
  mv <- read.csv(file.path(P, "aou_v7", "06_matching_variables.csv"))
  cat("matching-variable columns:", paste(names(mv), collapse = ", "), "\n")
  df <- merge(df, mv, by = "person_id", all.x = TRUE)
  if (Sys.getenv("EXTRA") == "1") df <- merge(df, read.csv(file.path(P, "aou_v7", "05_vaccination.csv")), by = "person_id", all.x = TRUE)
  stopifnot(nrow(df) == 25160)
  df$hosp <- as.integer(df$severity == 1)
  dd <- as.Date(df$covid_index_date)
  df$era <- ifelse(dd < as.Date("2021-06-15"), "1_pre_delta", ifelse(dd < as.Date("2021-12-15"), "2_delta", "3_omicron"))
  CH <- setdiff(names(ch), "person_id")
} else {
  df <- read.csv("/home/jupyter/flu/flu_prematch.csv", stringsAsFactors = FALSE)
  stopifnot(nrow(df) == 9169)
  df$hosp <- as.integer(df$Treatment)
  df$era <- df$period
  CH <- c("Myocardial_Infarction","Congestive_Heart_Failure","Peripheral_Vascular_Disease",
   "Cerebrovascular_Disease","Dementia","Chronic_Pulmonary_Disease","Rheumatic_Disease",
   "Peptic_Ulcer_Disease","Liver_Disease_Mild","Liver_Disease_Moderate_Severe",
   "Diabetes_without_Chronic_Complications","Diabetes_with_Chronic_Complications",
   "Hemiplegia_Paraplegia","Renal_Disease_Mild_Moderate","Renal_Disease_Severe","HIV",
   "Metastatic_Solid_Tumor","Malignancy","AIDS")
}
## the 3 encounter-density proxies the matched design balances, as quintiles (missing
## kept as a level), so the standardized contrast adjusts for what the matching does
MVARS <- intersect(c("survey_ord", "num_diagnosis", "ehr_length_days", "ehr_length", "num_diagnoses"), names(df))
cat("encounter-density covariates used:", paste(MVARS, collapse = ", "), "\n")
for (v in MVARS) {
  q <- cut(df[[v]], unique(quantile(df[[v]], seq(0, 1, 0.2), na.rm = TRUE)), include.lowest = TRUE)
  q <- as.character(q); q[is.na(q)] <- "Missing"; df[[paste0("q_", v)]] <- factor(q)
}
fac <- function(x, ref) { x <- as.character(x); x[is.na(x) | x == ""] <- "Missing"; relevel(factor(x), ref = ref) }
df$inc <- fac(ifelse(is.na(INC[as.character(df$income)]), "Missing", INC[as.character(df$income)]), "35-100k")
df$ins <- fac(df$insurance_type, "Employer")
for (v in c("education", "employment", "housing", "housing_stability", "race", "sex_at_birth", "age_group"))
  df[[v]] <- fac(df[[v]], names(sort(table(df[[v]]), decreasing = TRUE))[1])
for (v in CH) df[[v]][is.na(df[[v]])] <- 0
## R10b (Adler-Milstein persona): the matched models also adjust for ethnicity and, in
## COVID-19, vaccination; EXTRA=1 adds whichever such columns the arm's file carries
## (categorical, <= 10 levels, missing kept as a level)
XV <- character(0)
if (Sys.getenv("EXTRA") == "1") {
  XV <- grep("ethnic|vacc", names(df), value = TRUE, ignore.case = TRUE)
  XV <- XV[sapply(XV, function(v) length(unique(df[[v]])) <= 10)]
  for (v in XV) df[[v]] <- fac(df[[v]], names(sort(table(df[[v]], useNA = "no"), decreasing = TRUE))[1])
  cat("extra covariates:", paste(XV, collapse = ", "), "\n")
}
df$era <- factor(df$era)
f <- as.formula(paste("hosp ~ inc * era + ins * era + education + employment + housing + housing_stability +",
                      "age_group + sex_at_birth + race +", paste(CH, collapse = " + "),
                      if (length(MVARS)) paste("+", paste0("q_", MVARS, collapse = " + ")) else "",
                      if (length(XV)) paste("+", paste(XV, collapse = " + ")) else ""))

ard <- function(dat) {
  fit <- suppressWarnings(glm(f, data = dat, family = binomial))
  out <- c()
  for (e in levels(dat$era)) {
    de <- dat[dat$era == e, ]
    for (cmp in list(c("inc", "<10k", "35-100k"), c("ins", "Medicaid", "Employer"))) {
      a <- de; b <- de
      a[[cmp[1]]] <- factor(cmp[2], levels = levels(dat[[cmp[1]]]))
      b[[cmp[1]]] <- factor(cmp[3], levels = levels(dat[[cmp[1]]]))
      out[paste(cmp[1], e, sep = "|")] <- 100 * (mean(predict(fit, a, type = "response")) -
                                                 mean(predict(fit, b, type = "response")))
    }
  }
  out
}
est <- ard(df)
ids <- unique(df$person_id); rows_by <- split(seq_len(nrow(df)), df$person_id)
bs <- t(sapply(seq_len(B), function(i) {
  pick <- sample(as.character(ids), length(ids), replace = TRUE)
  ard(df[unlist(rows_by[pick], use.names = FALSE), ])
}))
o <- data.frame(arm = ARM, term = sub("\\|.*", "", names(est)), era = sub(".*\\|", "", names(est)),
                ard = est, lo = apply(bs, 2, quantile, 0.025), hi = apply(bs, 2, quantile, 0.975), row.names = NULL)
## the influenza employer reference is suppressed in the crude table before and during
## the pandemic (fewer than 20 hospitalized participants, or complementary suppression),
## so model-based insurance differences for those periods are withheld
if (ARM == "flu") o <- o[!(o$term == "ins" & o$era %in% c("1_pre", "2_pandemic")), ]
o$term <- ifelse(o$term == "inc", "income <$10 000 vs $35 000-99 999", "Medicaid vs employer")
write.csv(o, sprintf("/home/jupyter/jno_v26/ard_%s%s.csv", ARM, if (length(XV)) "_x" else ""), row.names = FALSE)
## difference between the latest and earliest era, from the same bootstrap draws
lab <- names(est); eras_ <- levels(df$era)
for (tm in c("inc", "ins")) {
  a <- paste(tm, eras_[length(eras_)], sep = "|"); b <- paste(tm, eras_[1], sep = "|")
  if (all(c(a, b) %in% colnames(bs)) && !(ARM == "flu" && tm == "ins")) {
    dd <- bs[, a] - bs[, b]
    cat(sprintf("%s: latest minus earliest era %.2f (95%% CI %.2f to %.2f)\n", tm, est[a] - est[b],
                quantile(dd, 0.025), quantile(dd, 0.975)))
  }
}
print(o, row.names = FALSE, digits = 3)
cat("DONE\n")
