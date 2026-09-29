## 03y_cells_extra.R -- minimum-cell audit of the two displays 03x_cells.R could not
## reproduce exactly (Codex R9).
##
##   eTable 12 (COVID-19)  Medicaid and employer insurance within each survey-recency
##                         tertile, on the rows the fitted models keep: recency as in
##                         03g_insurance_recency.R, then only matched strata that still
##                         hold a case and a control inside the tertile.
##   eTable 16 (both arms) the employment split of 03c_employment_split_and_flu_wald.R:
##                         "unable to work" separated from "unemployed", with the
##                         mixed responders assigned each way, on that script's inputs.
## Each cell is counted as case rows, control rows, distinct case participants and
## distinct control participants. Counts of 20 or fewer are printed as "<=20"; nothing
## smaller is written.
##   PART=etable12 ARM=covid Rscript 03y_cells_extra.R   (COVID-19 workspace)
##   PART=etable16 ARM=covid|flu Rscript 03y_cells_extra.R (the workspace holding
##   /home/jupyter/batchA and the 03c inputs; for this study, the influenza one)

ARM <- Sys.getenv("ARM", "covid")
PART <- Sys.getenv("PART", "etable12")
M <- function(x) ifelse(x <= 20, "<=20", as.character(x))
cnt <- function(x) c(case_rows = M(sum(x$Treatment == 1)), control_rows = M(sum(x$Treatment == 0)),
                     case_persons = M(length(unique(x$person_id[x$Treatment == 1]))),
                     control_persons = M(length(unique(x$person_id[x$Treatment == 0]))))
rows <- list()
add <- function(tab, grp, lvl, x) rows[[length(rows) + 1]] <<- data.frame(arm = ARM, table = tab, group = grp,
                                                                        level = lvl, t(cnt(x)), row.names = NULL)

if (PART == "etable12") {
  RES <- "/home/jupyter/workspace/rw-migration-aou-rw-46c7ae9e/data/covid_sdoh/aou_v7_5domain"
  X <- readRDS(file.path(RES, "joint_model_inputs.rds")); d <- X$df
  tim <- read.csv(file.path(RES, "04b_sdoh_timing.csv"))
  d$gap <- tim$sdoh_days_before_covid[match(d$person_id, tim$person_id)]
  pre <- !is.na(d$gap) & d$gap >= 0
  qs <- quantile(d$gap[pre], c(1/3, 2/3), na.rm = TRUE)
  d$recency <- NA_character_
  d$recency[pre] <- as.character(cut(d$gap[pre], breaks = c(-Inf, qs, Inf), labels = c("recent", "middle", "old")))
  for (g in c("recent", "middle", "old")) {
    dz <- d[!is.na(d$recency) & d$recency == g, ]
    ok <- tapply(dz$Treatment, dz$stratum, function(z) any(z == 1) && any(z == 0))
    dz <- dz[ok[as.character(dz$stratum)], ]
    for (lv in grep("medicaid|employer", levels(factor(dz$f.insurance)), ignore.case = TRUE, value = TRUE))
      add("eTable 12", g, lv, dz[as.character(dz$f.insurance) == lv, ])
  }
}
if (PART == "etable16") {
if (ARM == "covid") {
  e <- readRDS("/home/jupyter/refit_nodis/results/aou_v7/joint_model_inputs.rds")$df
  emp <- "f.employment"
} else {
  e <- read.csv("/home/jupyter/flu/07_matched_cohort.csv", stringsAsFactors = FALSE)
  emp <- "employment"
}

## eTable 16: the 03c split
FL <- read.csv("/home/jupyter/batchA/employment_unemp_flags.csv")
FL$out <- pmax(FL$out_1yr, FL$out_lt1yr)
i <- match(e$person_id, FL$person_id)
out <- ifelse(is.na(i), 0L, FL$out[i]); unab <- ifelse(is.na(i), 0L, FL$unable[i])
new <- as.character(e[[emp]]); sel <- new == "Unemployed"
new[sel & unab == 1 & out == 0] <- "Unable_to_work"
new[sel & unab == 1 & out == 1] <- "MIXED"
new[sel & unab == 0 & out == 0] <- "Unemployed"
for (assign in c("Unable_to_work", "Unemployed")) {
  z <- new; z[z == "MIXED"] <- assign
  for (lv in sort(unique(z))) add("eTable 16", paste("mixed ->", assign), lv, e[z == lv, ])
}
}
o <- do.call(rbind, rows)
cc <- c("case_rows", "control_rows", "case_persons", "control_persons")
o$flag <- ifelse(apply(o[, cc] == "<=20", 1, any), "LE_20", "ok")
write.csv(o, sprintf("/home/jupyter/jno_v26/cells_extra_%s_%s.csv", PART, ARM), row.names = FALSE)
print(o, row.names = FALSE)
cat("DONE\n")
