## 03p_refit.R -- does the insurance-by-wave pattern survive comparable insurance
## measurement? Reads the person-level version flags 03p_insurance_versions.py left
## on the VM, reuses the 03o adapter (COVID-19 arm, education merged), and refits
## the joint model with an insurance x wave interaction in two restricted samples:
##   R_new     participants who answered the current item (43528428); drops those
##             who answered only the replaced item and are coded "Missing"
##   R_emp     participants who answered 43528428 on or after the first date anyone
##             could choose the employer/union option, so the reference category is
##             measured the same way in every era
## Case and controls are both restricted; strata whose case fails are dropped.
## Aggregates only, screened at 20.

Sys.setenv(ARM = "covid", PART = "NONE")
L <- readLines("/home/jupyter/03o_r4_attenuation.R")
eval(parse(text = L[1:(grep("^## =+ PROBE", L)[1] - 1)]))
sink(paste0("/home/jupyter/jno_v24/log_03p", Sys.getenv("OUTSUFFIX", ""), ".txt"), split = TRUE)
OUTP <- "/home/jupyter/jno_v24"

fl <- read.csv(file.path(OUTP, "P_person_version_flags.csv"))
gd <- read.csv(file.path(OUTP, "P_version_dates.csv"))
emp0 <- as.Date(gd$first_employer_option[1]); cat("first employer-option date:", format(emp0), "\n")
i <- match(d$person_id, fl$person_id)
d$old_item <- fl$old_item[i]; d$new_item <- fl$new_item[i]; d$new_date <- as.Date(fl$new_date[i])
d$ver <- ifelse(d$new_item == 1 & !is.na(d$new_date) & d$new_date >= emp0, "new, employer option",
          ifelse(d$new_item == 1, "new, before employer option",
          ifelse(d$old_item == 1, "old item only", "neither")))
tb <- as.data.frame(table(wave = d[[ERA]], case = d$Treatment, version = d$ver))
tb$Freq <- ifelse(tb$Freq < MIN_CELL, NA, tb$Freq)
if (!nzchar(Sys.getenv("OUTSUFFIX"))) write.csv(tb, file.path(OUTP, "P_version_by_wave.csv"), row.names = FALSE); print(tb, row.names = FALSE)
cat("\ninsurance level by version (rows, screened):\n")
t2 <- as.data.frame(table(version = d$ver, insurance = d$f.insurance)); t2$Freq <- ifelse(t2$Freq < MIN_CELL, NA, t2$Freq); print(t2, row.names = FALSE)

restrict <- function(ok) { case_ok <- tapply(ok[d$Treatment == 1], d$.s[d$Treatment == 1], all)
  function(dk) ok & dk$.s %in% names(case_ok)[case_ok] }
out <- list()
for (s in list(list("R_new", d$new_item == 1), list("R_emp", d$ver == "new, employer option"))) {
  kr <- restrict(s[[2]]); keep <- kr(d)
  cat("\n==", s[[1]], ": cases", sum(d$Treatment[keep] == 1), "controls", sum(d$Treatment[keep] == 0), "\n")
  p <- fit_pool(fml(paste(BASE, "+", JOINT, "+ f.insurance:", ERA)), paste(s[[1]], "insurance x wave"), keep_rows = kr)
  if (is.null(p)) next
  ix <- grep(paste0("^f\\.insurance.*:", ERA, "|^", ERA, ".*:f\\.insurance"), p$nm, value = TRUE)
  cat("interaction terms:", ix, "\n")
  st <- D1(p, ix)
  out[[length(out) + 1]] <- data.frame(sample = s[[1]], term = "insurance x wave D1", aor = NA, lo = NA, hi = NA,
                                       F = st["F"], df1 = st["df1"], p = st["p"], row.names = NULL)
  for (w in levels(d[[ERA]])) {
    hit <- intersect(c(paste0("f.insuranceMedicaid:", ERA, w), paste0(ERA, w, ":f.insuranceMedicaid")), p$nm)
    e <- ci_of(p, cvec(p, c("f.insuranceMedicaid", hit)))
    out[[length(out) + 1]] <- data.frame(sample = s[[1]], term = paste("Medicaid", w), aor = exp(e["est"]),
                                         lo = exp(e["lo"]), hi = exp(e["hi"]), F = NA, df1 = NA, p = NA, row.names = NULL)
  }
  hit <- intersect(c(paste0("f.insuranceMedicaid:", ERA, "omicron"), paste0(ERA, "omicron:f.insuranceMedicaid")), p$nm)
  b <- ci_of(p, cvec(p, hit))
  out[[length(out) + 1]] <- data.frame(sample = s[[1]], term = "Medicaid ROR omicron/pre_delta", aor = exp(b["est"]),
                                       lo = exp(b["lo"]), hi = exp(b["hi"]), F = NA, df1 = NA, p = b["p"], row.names = NULL)
}
o <- do.call(rbind, out); write.csv(o, file.path(OUTP, paste0("P_refit", Sys.getenv("OUTSUFFIX", ""), ".csv")), row.names = FALSE); print(o, row.names = FALSE, digits = 3)
cat("\nDONE\n"); sink()
