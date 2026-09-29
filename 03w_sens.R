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
## EHR site from visits before the index date (03w_sitepre.py adds site_pre); the
## all-visit site in W$site included the index admission, so it was partly outcome (R7)
stopifnot("site_pre" %in% names(W))
d$region <- mode_ref(W$region[wi]); d$site <- mode_ref(W$site_pre[wi]); d$expansion <- W$expansion[wi]

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
M20 <- function(x) if (x < 20) "<20" else as.character(x)
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
if (SPART == "R10") {
  ## R10 review (Hua Xu, Adler-Milstein, Gottlieb personas): the era contrasts under
  ## phenotype checks that need no rematching (flags from 03z_extract.py)
  ##   no_preadm    drop control rows hospitalized 1-3 days before, or on, the index date
  ##   case_dx      keep matched sets whose case's qualifying visit carries a diagnosis of
  ##                the infection or of a respiratory disorder
  ##   case_ip      keep matched sets whose case had an inpatient-type visit (not ED only)
  ##   case_ed24    as case_ip, but also keep cases whose ED stay lasted >= 24 hours by its
  ##                recorded datetimes (drops ED visits that only crossed midnight)
  ##   case_severe  keep matched sets whose case had an ICU visit, a stay of >= 3 days,
  ##                or died within 30 days
  ##   case_dxwin   as case_dx, but the diagnosis may sit on any visit or none (index - 3 to
  ##                index + 30 days; needs 03z_dxlink.py)
  ## R10SPECS=case_dxwin runs a subset.
  ##   R10b: case_dx2, case_dxwin2, case_infwin2 (standard concepts only), case_lab
  ##   (laboratory-indexed cases), case_lab_dxwin2, case_ed24b (needs 03z_r10b.py)
  ## A set is kept only if it still holds its case and >= 1 control.
  R10 <- read.csv(sprintf("/home/jupyter/jno_v26/W_r10_%s.csv", ARM), stringsAsFactors = FALSE)
  ri <- if (ARM == "covid") match(d$person_id, R10$person_id) else
    match(paste(d$person_id, as.Date(d$flu_index_date)), paste(R10$person_id, as.Date(R10$d)))
  stopifnot(!any(is.na(ri)))
  for (cc in c("pre_adm", "q_ip", "q_ed24", "q_dx", "q_icu", "q_los", "death30")) d[[paste0("r10_", cc)]] <- R10[[cc]][ri]
  d$r10_severe <- as.integer(d$r10_q_icu == 1 | (!is.na(d$r10_q_los) & d$r10_q_los >= 3) | d$r10_death30 == 1)
  ## 03z_dxlink.py: the diagnosis requirement without visit linkage (index - 3 to + 30 days)
  fb <- sprintf("/home/jupyter/jno_v26/W_r10b_%s.csv", ARM)
  if (file.exists(fb)) { R10b <- read.csv(fb, stringsAsFactors = FALSE)
    stopifnot(identical(R10b$person_id, R10$person_id))
    for (cc in c("link_any", "dx_win", "inf_win")) d[[paste0("r10_", cc)]] <- R10b[[cc]][ri] }
  keep_rows <- function(drop_row, case_ok) function(dk) {
    keep <- !drop_row(dk)
    cs <- tapply(keep & dk$Treatment == 1 & case_ok(dk), dk$.s, any)
    ct <- tapply(keep & dk$Treatment == 0, dk$.s, any)
    keep & dk$.s %in% names(cs)[cs & ct]
  }
  none <- function(dk) rep(FALSE, nrow(dk)); all_ok <- function(dk) rep(TRUE, nrow(dk))
  specs <- list(
    no_preadm = keep_rows(function(dk) dk$Treatment == 0 & dk$r10_pre_adm == 1, all_ok),
    case_dx = keep_rows(none, function(dk) dk$r10_q_dx == 1),
    case_ip = keep_rows(none, function(dk) dk$r10_q_ip == 1),
    case_ed24 = keep_rows(none, function(dk) dk$r10_q_ip == 1 | dk$r10_q_ed24 == 1),
    case_severe = keep_rows(none, function(dk) dk$r10_severe == 1))
  if (!is.null(d$r10_dx_win)) specs$case_dxwin <- keep_rows(none, function(dk) dk$r10_dx_win == 1)
  ## R10b (03z_r10b.py): diagnosis flags from standard concepts only, the infection alone,
  ## laboratory-indexed cases, and the ED >= 24 h rule with unusable date-times set aside
  fc <- sprintf("/home/jupyter/jno_v26/W_r10c_%s.csv", ARM)
  if (file.exists(fc)) { R10c <- read.csv(fc, stringsAsFactors = FALSE)
    ci <- match(paste(R10$person_id, as.Date(R10$d)), paste(R10c$person_id, as.Date(R10c$d)))
    stopifnot(!any(is.na(ci)))
    for (cc in c("q_dx2", "dx_win2", "inf_win2", "lab_idx", "ed24b")) d[[paste0("r10_", cc)]] <- R10c[[cc]][ci][ri]
    specs$case_dx2 <- keep_rows(none, function(dk) dk$r10_q_dx2 == 1)
    specs$case_dxwin2 <- keep_rows(none, function(dk) dk$r10_dx_win2 == 1)
    specs$case_infwin2 <- keep_rows(none, function(dk) dk$r10_inf_win2 == 1)
    specs$case_lab <- keep_rows(none, function(dk) dk$r10_lab_idx == 1)
    specs$case_lab_dxwin2 <- keep_rows(none, function(dk) dk$r10_lab_idx == 1 & dk$r10_dx_win2 == 1)
    specs$case_ed24b <- keep_rows(none, function(dk) dk$r10_q_ip == 1 | (!is.na(dk$r10_ed24b) & dk$r10_ed24b == 1)) }
  ## R10 Codex: the complement of case_severe, fitted directly (stays under 3 days, no
  ## intensive care, alive at 30 days), to test where the change sits
  if (!is.null(d$r10_severe)) specs$case_short <- keep_rows(none, function(dk) dk$r10_severe == 0)
  if (nzchar(Sys.getenv("R10SPECS"))) specs <- specs[strsplit(Sys.getenv("R10SPECS"), ",")[[1]]]
  ## R10CELLS=1: minimum-cell audit of every R10 restriction instead of the models. For
  ## each definition x era (and all eras) x level of income and insurance, reference levels
  ## included: case rows, control rows, distinct case and control participants, the
  ## smallest over the 40 imputations. Counts of 20 or fewer print as "<=20".
  if (Sys.getenv("R10CELLS") == "1") {
    cnt <- function(x) c(cases = sum(x$Treatment == 1), controls = sum(x$Treatment == 0),
      case_persons = length(unique(x$person_id[x$Treatment == 1])),
      control_persons = length(unique(x$person_id[x$Treatment == 0])))
    KR <- lapply(specs, function(f) f(d)); acc <- list()
    for (k in seq_len(M)) {
      dk0 <- apply_imp(k)
      for (nm in names(KR)) {
        dd <- dk0[KR[[nm]], ]
        for (v in c(DV[["inc"]], DV[["ins"]])) for (e in c("all", sort(unique(as.character(dd[[ERA]]))))) {
          de <- if (e == "all") dd else dd[as.character(dd[[ERA]]) == e, ]
          for (lv in levels(factor(dk0[[v]]))) {
            key <- paste(nm, v, e, lv, sep = "|")
            cur <- cnt(de[as.character(de[[v]]) == lv, ])
            acc[[key]] <- if (is.null(acc[[key]])) cur else pmin(acc[[key]], cur)
          }
        }
      }
    }
    CC <- c("cases", "controls", "case_persons", "control_persons")
    o <- do.call(rbind, lapply(names(acc), function(key) {
      p <- strsplit(key, "|", fixed = TRUE)[[1]]
      data.frame(arm = ARM, spec = p[1], domain = p[2], era = p[3], level = p[4],
                 t(setNames(acc[[key]], paste0("min_", CC))), row.names = NULL) }))
    mc <- paste0("min_", CC)
    o$flag <- ifelse(apply(o[, mc] <= 20, 1, any), "LE_20", "ok")
    for (cc in mc) o[[cc]] <- ifelse(o[[cc]] <= 20, "<=20", as.character(o[[cc]]))
    write.csv(o, file.path(OUT, "cells_r10.csv"), row.names = FALSE)
    cat("cells audited:", nrow(o), "| with a count of 20 or fewer:", sum(o$flag == "LE_20"), "\n")
    print(o[o$flag == "LE_20", ], row.names = FALSE)
    cat("DONE\n"); sink(); quit(save = "no")
  }
  cat("rows flagged: controls pre-admitted", M20(sum(d$Treatment == 0 & d$r10_pre_adm == 1)),
      "| cases with dx", M20(sum(d$Treatment == 1 & d$r10_q_dx == 1)),
      "| cases IP", M20(sum(d$Treatment == 1 & d$r10_q_ip == 1)),
      "| cases severe", M20(sum(d$Treatment == 1 & d$r10_severe == 1)), "of", sum(d$Treatment == 1), "cases\n")
  for (nm in names(specs)) {
    f <- specs[[nm]]; kr <- f(d); nc <- sum(kr & d$Treatment == 1)
    run_pair(nm, rows_fun = f, note = paste("cases", M20(nc), "| control rows", M20(sum(kr & d$Treatment == 0))))
    pj <- fit_m(fml(paste(BASE, "+", JOINT)), rows = f)
    for (ft in FOC[c("inc10k", "medicaid")]) { e <- ci_of(pj, cvec(pj, ft))
      rows[[length(rows) + 1]] <- data.frame(arm = ARM, analysis = nm, term = ft, contrast = "joint AOR, all eras",
        ror = exp(e[["est"]]), lo = exp(e[["lo"]]), hi = exp(e[["hi"]]), p = e[["p"]], D1_p = NA, note = NA, row.names = NULL) }
  }
  o <- do.call(rbind, rows)
  write.csv(o, file.path(OUT, if (nzchar(Sys.getenv("R10SPECS"))) Sys.getenv("R10OUT", "sens_r10b.csv") else "sens_r10.csv"), row.names = FALSE)
  print(o, row.names = FALSE, digits = 3); cat("DONE\n"); sink(); quit(save = "no")
}
if (SPART == "SITEPRE") {
  ## refit only the site rows, which R7 changed; 03w_merge_sitepre.py puts them into
  ## sens_r6.csv in place of the all-visit-site rows of the earlier full run
  run_pair("site", "+ site")
  o <- do.call(rbind, rows)
  write.csv(o, file.path(OUT, "sens_r6_sitepre.csv"), row.names = FALSE)
  print(o, row.names = FALSE, digits = 3); cat("DONE\n"); sink(); quit(save = "no")
}
if (SPART == "EXPTV") {
  ## 2026-09-29: Medicaid-expansion status at each observation's own index date, instead of a
  ## fixed status as of January 1, 2021. Implementation dates from KFF, Status of State
  ## Medicaid Expansion Decisions (implementation-date table, Datawrapper ZJUAA, downloaded
  ## 2026-09-29). Primary ("impl"): the date expansion took effect as KFF states it (Maine
  ## 1/10/2019; Missouri 10/1/2021, when applications were first processed; Idaho and
  ## Virginia, coverage start). Variant ("retro"): the retroactive coverage dates KFF gives
  ## for Maine (7/2/2018) and Missouri (7/1/2021). States not listed never expanded by the
  ## end of the data (AL FL GA KS MS SC TN TX WI WY). Matched sets kept if the case and >= 1
  ## control are in the stratum, as for the fixed classification.
  IMPL <- c(AK = "2015-09-01", AZ = "2014-01-01", AR = "2014-01-01", CA = "2014-01-01", CO = "2014-01-01",
            CT = "2014-01-01", DE = "2014-01-01", DC = "2014-01-01", HI = "2014-01-01", ID = "2020-01-01",
            IL = "2014-01-01", IN = "2015-02-01", IA = "2014-01-01", KY = "2014-01-01", LA = "2016-07-01",
            ME = "2019-01-10", MD = "2014-01-01", MA = "2014-01-01", MI = "2014-04-01", MN = "2014-01-01",
            MO = "2021-10-01", MT = "2016-01-01", NE = "2020-10-01", NV = "2014-01-01", NH = "2014-08-15",
            NJ = "2014-01-01", NM = "2014-01-01", NY = "2014-01-01", NC = "2023-12-01", ND = "2014-01-01",
            OH = "2014-01-01", OK = "2021-07-01", OR = "2014-01-01", PA = "2015-01-01", RI = "2014-01-01",
            SD = "2023-07-01", UT = "2020-01-01", VT = "2014-01-01", VA = "2019-01-01", WA = "2014-01-01",
            WV = "2014-01-01")
  st <- W$state[wi]; known <- W$region[wi] != "Unknown"
  if (ARM == "covid") {
    cc <- read.csv("/home/jupyter/workspace/rw-migration-aou-rw-46c7ae9e/data/covid_sdoh/aou_v7/01_covid_cohort.csv",
                   stringsAsFactors = FALSE)
    idxd <- as.Date(cc$covid_index_date[match(d$person_id, cc$person_id)])
  } else idxd <- as.Date(d$flu_index_date)
  stopifnot(!any(is.na(idxd)))  # not 'idx': 03o uses idx to map persons to imputations
  for (vr in c("impl", "retro")) {
    im <- IMPL; if (vr == "retro") { im["MO"] <- "2021-07-01"; im["ME"] <- "2018-07-02" }
    dt <- as.Date(im[st])
    d$expansion <- ifelse(!known, "Unknown", ifelse(!is.na(dt) & idxd >= dt, "Yes", "No"))
    moved <- sum(d$expansion != W$expansion[wi])
    cat(sprintf("\n== %s: observations whose status differs from the fixed classification: %s ==\n", vr,
                if (moved > 20) moved else "<=20"))
    for (g in c("Yes", "No")) {
      keep_sets <- function(dk) {
        inn <- dk$expansion == g
        ok <- tapply(inn & dk$Treatment == 1, dk$.s, any) & tapply(inn & dk$Treatment == 0, dk$.s, any)
        inn & dk$.s %in% names(ok)[ok]
      }
      ncase <- sum(keep_sets(d) & d$Treatment == 1)
      run_pair(paste0("exptv_", vr, "_", g), rows_fun = keep_sets, note = if (ncase > 20) paste("cases", ncase) else "cases <=20")
    }
  }
  o <- do.call(rbind, rows)
  write.csv(o, file.path(OUT, "sens_exptv.csv"), row.names = FALSE)
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
