## 03w_sens.R -- sensitivity analyses requested in the R6 expert review (2026-09-25).
## Sources the shared machinery of 03o_r4_attenuation.R (frozen imputations, pooling,
## D1, contrast helpers) and refits the era models under 5 changes, each reported as
## the income <$10k and Medicaid ratios of odds ratios (ROR, later vs earliest era)
## and the D1 test of the domain-by-era block, beside a replication of the primary:
##   primary     BASE + JOINT + domain x era (separate income and insurance models)
##   region      + US Census region of residence (4 regions + unknown)
##   site        + predominant EHR site (src_id; small sites pooled)
##   expansion   insurance x era refitted within residents of Medicaid-expansion
##               and non-expansion states (matched sets kept if the case and >=1
##               control belong to the stratum)
##   lag         + survey-lag tertile and tertile x domain (recency may modify the
##               domain association, and lag differs by era)
##   harmA/B     the 'not captured by revised item' level recoded from the original
##               insurance item where answered (Private -> Employer (A) or
##               Other_None (B)); Medicaid > Medicare > Employer > Other_None
##   tipD        delta-adjusted imputation: for participants whose income was
##               missing, each imputed income is moved down 1 band with
##               probability D (0.25, 0.5, 1) -- missing not at random, worse off
## Model-based variance, as printed in the main text. Aggregates only.
##   OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 ARM=covid NCOR=3 Rscript 03w_sens.R

L <- readLines("/home/jupyter/03o_r4_attenuation.R")
Sys.setenv(PART = "SENS", VARTYPE = "model")
eval(parse(text = L[1:(grep("^## =+ PROBE", L)[1] - 1)]))
NCOR <- as.integer(Sys.getenv("NCOR", "3"))
set.seed(20260925)

W <- read.csv(sprintf("/home/jupyter/jno_v26/W_person_%s.csv", ARM), stringsAsFactors = FALSE)
wi <- match(d$person_id, W$person_id); stopifnot(!any(is.na(wi)))
mode_ref <- function(x) { x <- factor(x); relevel(x, names(sort(table(x), decreasing = TRUE))[1]) }
d$region <- mode_ref(W$region[wi]); d$site <- mode_ref(W$site[wi]); d$expansion <- W$expansion[wi]

## survey lag (days from Basics to index)
if (ARM == "covid") {
  TB <- "/home/jupyter/workspace/rw-migration-aou-rw-46c7ae9e/data/covid_sdoh/aou_v7_5domain/04b_sdoh_timing.csv"
  tm <- read.csv(TB, stringsAsFactors = FALSE)
  lagcol <- grep("lag|days", names(tm), value = TRUE, ignore.case = TRUE)[1]
  cat("timing file columns:", paste(names(tm), collapse = ", "), "| using", lagcol, "\n")
  d$lag <- tm[[lagcol]][match(d$person_id, tm$person_id)]
} else {
  d$lag <- as.numeric(as.Date(d$flu_index_date) - as.Date(d$basics_date))
}
cat("lag missing:", sum(is.na(d$lag)), "of", nrow(d), "\n")
qs <- quantile(d$lag, c(1/3, 2/3), na.rm = TRUE)
d$lagT <- factor(ifelse(is.na(d$lag), "T2", ifelse(d$lag <= qs[1], "T1", ifelse(d$lag <= qs[2], "T2", "T3"))), levels = c("T2", "T1", "T3"))

## survey lag by era and case status (aggregates; each cell >= 20 by construction of the cohort)
cat("\n== survey lag (days) by era and case status: median [IQR] ==\n")
for (e in levels(factor(d[[ERA]]))) for (t in 0:1) {
  x <- d$lag[d[[ERA]] == e & d$Treatment == t]
  if (sum(!is.na(x)) >= 20) cat(sprintf("  %-22s %s  n=%d  %d [%d-%d]\n", e, if (t) "case   " else "control", sum(!is.na(x)),
      round(median(x, na.rm = TRUE)), round(quantile(x, .25, na.rm = TRUE)), round(quantile(x, .75, na.rm = TRUE))))
}

fit_m <- function(f, prep = function(dk, k) dk, rows = NULL) {
  R <- mclapply(seq_len(M), function(k) {
    dk <- prep(apply_imp(k), k); if (!is.null(rows)) dk <- dk[rows(dk), ]
    f2 <- f; environment(f2) <- environment()
    fk <- clogit(f2, data = dk, method = "efron")
    b <- coef(fk); V <- vcov(fk); ok <- intersect(names(b)[!is.na(b)], rownames(V))
    list(b = b[ok], V = V[ok, ok])
  }, mc.cores = NCOR)
  bad <- sapply(R, function(z) inherits(z, "try-error") || is.character(z))
  if (any(bad)) { print(unique(unlist(R[bad]))); stop("fits failed: ", sum(bad)) }
  pool_full(lapply(R, `[[`, "b"), lapply(R, `[[`, "V"))
}
eras <- levels(factor(d[[ERA]]))
if (ARM == "covid") {
  lor <- function(p, ft, dom, w) { cv <- cvec(p, ft)
    h <- intersect(c(paste0(ft, ":", ERA, w), paste0(ERA, w, ":", ft)), p$nm); cv[h] <- cv[h] + 1; cv }
  PR <- c(eras[3], eras[1])
} else {
  lor <- function(p, ft, dom, w) lor_cv(p, dom, ft, ERA, w)
  PR <- c("3_post", "1_pre")
}
era_block <- function(p, v) grep(paste0("^", v, ".*:", ERA, "|^", ERA, ".*:", v), p$nm, value = TRUE)
rows <- list()
add <- function(analysis, p, v, ft, n_note = NA) {
  e <- ci_of(p, lor(p, ft, v, PR[1]) - lor(p, ft, v, PR[2]))
  s <- D1(p, era_block(p, v))
  rows[[length(rows) + 1]] <<- data.frame(arm = ARM, analysis = analysis, term = ft, contrast = paste0(PR[1], "/", PR[2]),
    ror = exp(e[["est"]]), lo = exp(e[["lo"]]), hi = exp(e[["hi"]]), p = e[["p"]], D1_p = s[["p"]], note = n_note, row.names = NULL)
}
run_pair <- function(analysis, extra = "", prep = function(dk, k) dk, rows_fun = NULL, note = NA, lag_int = FALSE) {
  for (v in c(DV[["inc"]], DV[["ins"]])) {
    li <- if (lag_int) paste("+ lagT +", v, ": lagT") else ""
    p <- fit_m(fml(paste(BASE, extra, "+", JOINT, li, "+", v, ":", ERA)), prep, rows_fun)
    ft <- if (v == DV[["inc"]]) FOC[["inc10k"]] else FOC[["medicaid"]]
    add(analysis, p, v, ft, note)
  }
  cat(sprintf("  %-10s done\n", analysis))
}
SPART <- Sys.getenv("SPART", "ALL")
if (SPART == "SITEPRE") {
  ## R7: EHR site from visits before the index date only (03w_sitepre.py)
  d$site <- mode_ref(W$site_pre[wi])
  run_pair("site_pre", "+ site")
  o <- do.call(rbind, rows)
  write.csv(o, file.path(OUT, "sens_r6_sitepre.csv"), row.names = FALSE)
  print(o, row.names = FALSE, digits = 3); cat("DONE\n"); sink(); quit(save = "no")
}
t0 <- Sys.time()
run_pair("primary")
run_pair("region", "+ region")
run_pair("site", "+ site")
run_pair("lag", "+ lagT", lag_int = TRUE)

## expansion strata: keep matched sets whose case and >= 1 control are in the stratum
for (g in c("Yes", "No")) {
  keep_sets <- function(dk) {
    inn <- dk$expansion == g
    ok <- tapply(inn & dk$Treatment == 1, dk$.s, any) & tapply(inn & dk$Treatment == 0, dk$.s, any)
    inn & dk$.s %in% names(ok)[ok]
  }
  ncase <- sum(keep_sets(d) & d$Treatment == 1)
  run_pair(paste0("expansion_", g), rows_fun = keep_sets, note = if (ncase >= 20) paste("cases", ncase) else "cases <20")
}

## harmonized insurance: recode the not-captured level from the original item
insv <- DV[["ins"]]; nc_lev <- grep("missing|not", levels(factor(d[[insv]])), ignore.case = TRUE, value = TRUE)
stopifnot(length(nc_lev) == 1)
for (vv in c("A", "B")) {
  newv <- W[[paste0("old_ins_", vv)]][wi]
  hp <- function(dk, k) {
    z <- as.character(dk[[insv]]); r <- z == nc_lev & !is.na(newv) & newv != ""
    z[r] <- newv[r]; dk[[insv]] <- factor(z, levels = levels(factor(d[[insv]]))); dk
  }
  nre <- sum(as.character(d[[insv]]) == nc_lev & !is.na(newv) & newv != "")
  p <- fit_m(fml(paste(BASE, "+", JOINT, "+", insv, ":", ERA)), hp)
  add(paste0("harm", vv), p, insv, FOC[["medicaid"]], paste("observations recoded", if (nre >= 20) nre else "<20"))
  cat(sprintf("  harm%s done\n", vv))
}

## tipping point for missing income
incv <- DV[["inc"]]
ORD <- c("less_10k", "10k_25k", "25k_35k", "35k_100k", "100k_150k", "150k_200k", "more_200k")
miss_inc <- as.character(d[[incv]]) %in% c("Missing", NA)
U <- runif(length(unique(d$person_id))); names(U) <- unique(d$person_id)
for (D in c(0.25, 0.5, 1)) {
  tp <- function(dk, k) {
    z <- as.character(dk[[incv]]); stopifnot(all(z[miss_inc] %in% ORD))
    pos <- match(z, ORD); mv <- miss_inc & U[as.character(dk$person_id)] < D & pos > 1
    z[mv] <- ORD[pos[mv] - 1]; dk[[incv]] <- factor(z, levels = levels(dk[[incv]])); dk
  }
  run_pair(paste0("tip", D), prep = tp, note = paste("persons with missing income", length(unique(d$person_id[miss_inc]))))
  pj <- fit_m(fml(paste(BASE, "+", JOINT)), tp)
  for (ft in FOC[c("inc10k", "medicaid")]) { e <- ci_of(pj, cvec(pj, ft))
    rows[[length(rows) + 1]] <- data.frame(arm = ARM, analysis = paste0("tip", D), term = ft, contrast = "joint AOR, all eras",
      ror = exp(e[["est"]]), lo = exp(e[["lo"]]), hi = exp(e[["hi"]]), p = e[["p"]], D1_p = NA, note = NA, row.names = NULL) }
}
cat("minutes:", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "\n")
o <- do.call(rbind, rows)
write.csv(o, file.path(OUT, "sens_r6.csv"), row.names = FALSE)
print(o, row.names = FALSE, digits = 3)
cat("DONE\n"); sink()
