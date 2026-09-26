## 03z_describe.R -- descriptive checks for the R10 review, on the matched cohort, from the
## flags 03z_extract.py writes. Counts below 20 print as "<20"; a count whose complement is
## below 20 prints as "masked", so no cell below 20 can be derived.
##   1. among cases, the share whose qualifying hospitalization was ED only (no
##      inpatient-type visit), by income band and by era (Gottlieb: admission for
##      social reasons; Hua Xu: the extended-ED rule)
##   2. among cases, the share with a relevant diagnosis on the qualifying visit, an
##      ICU visit, and the severity definition used in 03w_sens.R, by era
##   3. among participants reporting income below $25 000, the share with an
##      income-specific Z code (Z59.5, Z59.6, Z59.86, Z59.87) and with any Z59 code
##      before the index date, by era (eTable 13 repeated over time)
##   3b. among cases, the share with a relevant diagnosis on the qualifying visit, by
##      insurance (Medicaid, employer) and era (why the diagnosis restriction moves the
##      Medicaid ratio)
##   4. the share with a structured social-needs screening record before the index date,
##      with any payer_plan_period row, and whose first insurance answer postdates the index
##   OMP_NUM_THREADS=1 ARM=covid Rscript 03z_describe.R      (or ARM=flu)

L <- readLines("/home/jupyter/03o_r4_attenuation.R")
Sys.setenv(PART = "CELLS", VARTYPE = "model")
eval(parse(text = L[1:(grep("^## =+ PROBE", L)[1] - 1)]))
R10 <- read.csv(sprintf("/home/jupyter/jno_v26/W_r10_%s.csv", ARM), stringsAsFactors = FALSE)
ri <- if (ARM == "covid") match(d$person_id, R10$person_id) else
  match(paste(d$person_id, as.Date(d$flu_index_date)), paste(R10$person_id, as.Date(R10$d)))
stopifnot(!any(is.na(ri)))
for (cc in setdiff(names(R10), c("person_id", "d"))) d[[paste0("r_", cc)]] <- R10[[cc]][ri]
d$r_severe <- as.integer(d$r_q_icu == 1 | (!is.na(d$r_q_los) & d$r_q_los >= 3) | d$r_death30 == 1)
M20 <- function(x) ifelse(x < 20, "<20", as.character(x))
pct <- function(k, n) ifelse(k < 20 | n - k < 20, "masked", sprintf("%.1f", 100 * k / n))
inc <- as.character(d[[DV[["inc"]]]]); inc[is.na(inc)] <- "Missing"
band <- c(less_10k = "<10k", `10k_25k` = "10-25k", `25k_35k` = "25-35k", `35k_100k` = "35-100k",
          `100k_150k` = ">=100k", `150k_200k` = ">=100k", more_200k = ">=100k", Missing = "Missing")
d$band <- band[inc]; d$band[is.na(d$band)] <- "Missing"
era <- as.character(d[[ERA]])
cs <- d$Treatment == 1
out <- list()
add <- function(what, grp, k, n) out[[length(out) + 1]] <<- data.frame(arm = ARM, what = what, group = grp,
  n = M20(n), k = ifelse(n - k < 20 & k >= 20, "masked", M20(k)), pct = pct(k, n), row.names = NULL)

## 1. ED-only among cases, by income band and by era
for (b in c("<10k", "10-25k", "25-35k", "35-100k", ">=100k", "Missing")) {
  s <- cs & d$band == b; add("case ED only (no inpatient-type visit)", paste("income", b), sum(s & d$r_q_ip == 0), sum(s))
}
for (e in sort(unique(era))) { s <- cs & era == e
  add("case ED only (no inpatient-type visit)", paste("era", e), sum(s & d$r_q_ip == 0), sum(s))
  add("case with relevant diagnosis on visit", paste("era", e), sum(s & d$r_q_dx == 1), sum(s))
  add("case ICU visit", paste("era", e), sum(s & d$r_q_icu == 1), sum(s))
  add("case severe (ICU, stay >= 3 d, or death <= 30 d)", paste("era", e), sum(s & d$r_severe == 1), sum(s))
  add("control admitted 1-3 d before or on index", paste("era", e), sum(!cs & era == e & d$r_pre_adm == 1), sum(!cs & era == e))
}
## 3. Z codes among low-income reporters (observed income), person level within era
## NOT USED: built on the z_inc / z59_any flags of 03z_extract.py, which read
## condition_source_value; 03z_z59.py recomputes these from source concepts
low <- d$band %in% c("<10k", "10-25k")
for (e in c("all", sort(unique(era)))) {
  s <- low & (e == "all" | era == e)
  p <- !duplicated(paste(d$person_id, era)[s])
  z <- d[s, ][p, ]
  add("income <$25 000: income-specific Z code (Z59.5/.6/.86/.87)", paste("era", e), sum(z$r_z_inc == 1), nrow(z))
  add("income <$25 000: any Z59 code", paste("era", e), sum(z$r_z59_any == 1), nrow(z))
}
## 3b. diagnosis share among cases by insurance and era (observed insurance)
ins <- tolower(as.character(d[[DV[["ins"]]]]))
for (g in c("medicaid", "employer")) for (e in sort(unique(era))) {
  s <- cs & era == e & grepl(paste0("^", g), ins)
  add(paste("case with relevant diagnosis on visit, insurance", g), paste("era", e), sum(s & d$r_q_dx == 1), sum(s))
}
## 3c. data capture behind the diagnosis flag (03z_dxlink.py), cases by insurance and era
fb <- sprintf("/home/jupyter/jno_v26/W_r10b_%s.csv", ARM)
if (file.exists(fb)) { R10b <- read.csv(fb, stringsAsFactors = FALSE)
  for (cc in c("link_any", "dx_win", "inf_win")) d[[paste0("r_", cc)]] <- R10b[[cc]][ri]
  lab <- c(link_any = "qualifying visit has any linked condition row",
           dx_win = "relevant diagnosis index-3 to +30 d, any or no visit",
           inf_win = "infection diagnosis index-3 to +30 d, any or no visit")
  for (cc in names(lab)) for (g in c("medicaid", "employer")) for (e in sort(unique(era))) {
    s <- cs & era == e & grepl(paste0("^", g), ins)
    add(paste0("case ", lab[[cc]], ", insurance ", g), paste("era", e), sum(s & d[[paste0("r_", cc)]] == 1), sum(s))
  } }
## 4. screening, payer, insurance answer timing (person level)
pp <- d[!duplicated(d$person_id), ]
add("structured social-needs screening record before index", "persons", sum(pp$r_scr_any == 1), nrow(pp))
add("any payer_plan_period row", "persons", sum(pp$r_payer_any == 1), nrow(pp))
add("first insurance answer after the index date", "rows", sum(d$r_ins_after == 1), nrow(d))
o <- do.call(rbind, out)
write.csv(o, sprintf("/home/jupyter/jno_v26/describe_r10_%s.csv", ARM), row.names = FALSE)
print(o, row.names = FALSE)
cat("DONE\n")
