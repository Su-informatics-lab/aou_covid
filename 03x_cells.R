## 03x_cells.R -- minimum-cell audit of every stratum-specific estimate the paper displays
## (R7 review, 2026-09-26; extended after Codex R8).
##
## eMethod 2's first audit checked each displayed level over the whole cohort. The
## per-era tables and figures (eTables 8, 20, 22, 23; Figures 1C and 2A) show estimates
## for a level WITHIN an era, and other supplement tables show a level within a policy
## window (eTable 20C-D), a survey-recency tertile (eTable 12), or a race or employment
## category (eTables 14, 16). For every such cell, reference levels included, this
## counts matched case rows, control rows, distinct case participants, distinct control
## participants, and distinct participants. Influenza rows are person-seasons and
## COVID-19 controls are reused, so rows and people differ. Imputed items are counted in
## each of the 40 imputations and the smallest count kept; insurance is observed.
## Blocks:
##   era       era x income and insurance, over all participants and within the
##             Medicaid-expansion strata of eTable 23 (sets kept as in 03w_sens.R)
##   epsl      COVID-19: 2020 / 2021 first half / Delta / Omicron x income, employment,
##             insurance (eTable 20C)
##   recency   COVID-19: survey-recency tertile x insurance, defined as in
##             03g_insurance_recency.R (eTable 12)
##   overall   COVID-19: race and employment levels over the whole cohort (eTables 14, 16)
##   season    influenza: 2022-23 / 2023-24 x income and insurance (eTable 20D)
## Output: counts >= 20 printed as numbers, others as "<20"; nothing smaller is written.
##   OMP_NUM_THREADS=1 ARM=covid Rscript 03x_cells.R      (or ARM=flu)

L <- readLines("/home/jupyter/03o_r4_attenuation.R")
Sys.setenv(PART = "CELLS", VARTYPE = "model")
eval(parse(text = L[1:(grep("^## =+ PROBE", L)[1] - 1)]))
W <- read.csv(sprintf("/home/jupyter/jno_v26/W_person_%s.csv", ARM), stringsAsFactors = FALSE)
d$expansion <- W$expansion[match(d$person_id, W$person_id)]

## grouping variables that do not depend on the imputation
if (ARM == "covid") {
  co <- read.csv(file.path(BUCKET, "aou_v7", "01_covid_cohort.csv"))
  idate <- as.Date(co$covid_index_date[match(d$person_id, co$person_id)])
  e1 <- levels(factor(d[[ERA]]))[1]
  era4 <- as.character(d[[ERA]])
  era4[era4 == e1 & idate <  as.Date("2021-01-01")] <- "a_2020_epsl"
  era4[era4 == e1 & idate >= as.Date("2021-01-01")] <- "b_2021h1"
  d$.epsl <- era4
  tim <- read.csv(file.path(BUCKET, "aou_v7_5domain", "04b_sdoh_timing.csv"))
  gap <- tim$sdoh_days_before_covid[match(d$person_id, tim$person_id)]
  pre <- !is.na(gap) & gap >= 0
  qs <- quantile(gap[pre], c(1/3, 2/3), na.rm = TRUE)
  rec <- rep(NA_character_, nrow(d))
  rec[pre] <- as.character(cut(gap[pre], breaks = c(-Inf, qs, Inf), labels = c("recent", "middle", "old")))
  rec[!is.na(gap) & gap < 0] <- "post_index"
  d$.recency <- rec
  d$.all <- "all"
} else {
  d$.season <- ifelse(d[[ERA]] == "3_post", as.character(d$season), NA)
}

in_stratum <- function(dk, g) {
  inn <- dk$expansion == g
  ok <- tapply(inn & dk$Treatment == 1, dk$.s, any) & tapply(inn & dk$Treatment == 0, dk$.s, any)
  inn & dk$.s %in% names(ok)[ok]
}
## block = list(name, row filter, grouping column, domains)
blocks <- list(list("era:all", function(dk) rep(TRUE, nrow(dk)), ERA, c(DV[["inc"]], DV[["ins"]])))
for (g in c("Yes", "No")) blocks[[length(blocks) + 1]] <- list(paste0("era:expansion_", g),
  local({ gg <- g; function(dk) in_stratum(dk, gg) }), ERA, c(DV[["inc"]], DV[["ins"]]))
if (ARM == "covid") {
  blocks <- c(blocks, list(
    list("epsl", function(dk) rep(TRUE, nrow(dk)), ".epsl", c(DV[["inc"]], DV[["emp"]], DV[["ins"]])),
    list("recency", function(dk) !is.na(dk$.recency), ".recency", DV[["ins"]]),
    list("overall", function(dk) rep(TRUE, nrow(dk)), ".all", c(RACE, DV[["emp"]]))))
} else {
  blocks <- c(blocks, list(list("season", function(dk) !is.na(dk$.season), ".season", c(DV[["inc"]], DV[["ins"]]))))
}

cnt <- function(x) c(cases = sum(x$Treatment == 1), controls = sum(x$Treatment == 0),
  case_persons = length(unique(x$person_id[x$Treatment == 1])),
  control_persons = length(unique(x$person_id[x$Treatment == 0])),
  persons = length(unique(x$person_id)))
acc <- list()
for (k in seq_len(M)) {
  dk <- apply_imp(k)
  for (b in blocks) {
    dd <- dk[b[[2]](dk), ]
    for (v in b[[4]]) {
      for (e in c("all", sort(unique(as.character(dd[[b[[3]]]]))))) {
        de <- if (e == "all") dd else dd[as.character(dd[[b[[3]]]]) == e, ]
        for (lv in levels(factor(dk[[v]]))) {
          key <- paste(b[[1]], v, e, lv, sep = "|")
          cur <- cnt(de[as.character(de[[v]]) == lv, ])
          acc[[key]] <- if (is.null(acc[[key]])) cur else pmin(acc[[key]], cur)
        }
      }
    }
  }
}
CC <- c("cases", "controls", "case_persons", "control_persons", "persons")
out <- do.call(rbind, lapply(names(acc), function(key) {
  p <- strsplit(key, "|", fixed = TRUE)[[1]]
  data.frame(arm = ARM, block = p[1], domain = p[2], group = p[3], level = p[4],
             t(setNames(acc[[key]], paste0("min_", CC))), row.names = NULL)
}))
mc <- paste0("min_", CC)
out$flag <- ifelse(apply(out[, mc] < 20, 1, any), "BELOW_20", "ok")
for (cc in mc) out[[cc]] <- ifelse(out[[cc]] < 20, "<20", as.character(out[[cc]]))
write.csv(out, file.path(OUT, "cells_audit.csv"), row.names = FALSE)
cat("cells audited:", nrow(out), "| below 20:", sum(out$flag == "BELOW_20"), "\n")
print(out[out$flag == "BELOW_20", ], row.names = FALSE)
cat("DONE\n"); sink()
