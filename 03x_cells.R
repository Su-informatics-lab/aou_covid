## 03x_cells.R -- minimum-cell audit of every era-specific estimate the paper displays
## (R7 review, 2026-09-26).
##
## eMethod 2's audit checked each displayed level over the whole cohort. The per-era
## tables and figures (eTables 8, 20, 22, 23; Figures 1C and 2A) show estimates for a
## level WITHIN an era, and for influenza pandemic seasons some level x era cells are
## small. For every era x level of income and insurance (reference levels included),
## this counts matched cases, control observations and distinct persons. Income is
## imputed, so each count is the minimum over the 40 imputations; insurance is
## observed. The same counts are made inside the Medicaid-expansion strata of eTable 23
## (sets kept as in 03w_sens.R). Output: counts >= 20 printed as numbers, others as
## "<20"; nothing smaller than 20 is written.
##   OMP_NUM_THREADS=1 ARM=covid Rscript 03x_cells.R      (or ARM=flu)

L <- readLines("/home/jupyter/03o_r4_attenuation.R")
Sys.setenv(PART = "CELLS", VARTYPE = "model")
eval(parse(text = L[1:(grep("^## =+ PROBE", L)[1] - 1)]))
W <- read.csv(sprintf("/home/jupyter/jno_v26/W_person_%s.csv", ARM), stringsAsFactors = FALSE)
d$expansion <- W$expansion[match(d$person_id, W$person_id)]

strata <- list(all = function(dk) rep(TRUE, nrow(dk)))
for (g in c("Yes", "No")) strata[[paste0("expansion_", g)]] <- local({ gg <- g; function(dk) {
  inn <- dk$expansion == gg
  ok <- tapply(inn & dk$Treatment == 1, dk$.s, any) & tapply(inn & dk$Treatment == 0, dk$.s, any)
  inn & dk$.s %in% names(ok)[ok] } })

acc <- list()
for (k in seq_len(M)) {
  dk <- apply_imp(k)
  for (sn in names(strata)) {
    keep <- strata[[sn]](dk); dd <- dk[keep, ]
    for (v in c(DV[["inc"]], DV[["ins"]])) {
      for (e in c("all", levels(factor(dd[[ERA]])))) {
        de <- if (e == "all") dd else dd[dd[[ERA]] == e, ]
        for (lv in levels(factor(dk[[v]]))) {
          x <- de[as.character(de[[v]]) == lv, ]
          key <- paste(sn, v, e, lv, sep = "|")
          cur <- c(cases = sum(x$Treatment == 1), controls = sum(x$Treatment == 0), persons = length(unique(x$person_id)))
          acc[[key]] <- if (is.null(acc[[key]])) cur else pmin(acc[[key]], cur)
        }
      }
    }
  }
}
out <- do.call(rbind, lapply(names(acc), function(key) {
  p <- strsplit(key, "|", fixed = TRUE)[[1]]
  data.frame(arm = ARM, stratum = p[1], domain = p[2], era = p[3], level = p[4],
             min_cases = acc[[key]][["cases"]], min_controls = acc[[key]][["controls"]],
             min_persons = acc[[key]][["persons"]], row.names = NULL)
}))
out$flag <- ifelse(out$min_cases < 20 | out$min_controls < 20 | out$min_persons < 20, "BELOW_20", "ok")
for (cc in c("min_cases", "min_controls", "min_persons")) out[[cc]] <- ifelse(out[[cc]] < 20, "<20", as.character(out[[cc]]))
write.csv(out, file.path(OUT, "cells_audit.csv"), row.names = FALSE)
cat("cells audited:", nrow(out), "| below 20:", sum(out$flag == "BELOW_20"), "\n")
print(out[out$flag == "BELOW_20", ], row.names = FALSE)
cat("DONE\n"); sink()
