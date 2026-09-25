## 03o_ab_resume.R -- the PART=AB computation of 03o_r4_attenuation.R, run so that
## progress is visible and a restart resumes. Same adapter (evaluated from 03o up to
## the PROBE block), same point estimates, same bootstrap jobs and seeds
## (set.seed(1e5 + i) over expand.grid(k = 1:M, b = 1:BPER)), same aggregation, so
## the output equals what PART=AB would have written. Each draw is saved to
## OUT/ab_draws/<i>.rds; run with single-threaded BLAS and NCOR workers:
##   OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 ARM=covid NCOR=4 Rscript 03o_ab_resume.R
## Written because the first PART=AB run oversubscribed BLAS threads and gave no
## progress signal.
L <- readLines("/home/jupyter/03o_r4_attenuation.R")
Sys.setenv(PART = "AB_RESUME")
eval(parse(text = L[1:(grep("^## =+ PROBE", L)[1] - 1)]))
DR <- file.path(OUT, "ab_draws"); dir.create(DR, showWarnings = FALSE)

ptf <- file.path(DR, "point.rds")
if (!file.exists(ptf)) {
  per_imp <- mclapply(seq_len(M), function(k) one_draw(apply_imp(k)), mc.cores = NCOR)
  per_imp <- per_imp[!sapply(per_imp, is.null)]
  cat("imputations with a usable draw:", length(per_imp), "\n")
  pt <- lapply(names(per_imp[[1]]), function(nm) {
    v <- Reduce(`+`, lapply(per_imp, `[[`, nm)) / length(per_imp); stats_of(v) })
  names(pt) <- names(per_imp[[1]]); saveRDS(pt, ptf)
}
pt <- readRDS(ptf)

rows_by_s <- split(seq_len(nrow(d)), d$.s); sids <- names(rows_by_s)
jobs <- expand.grid(k = seq_len(M), b = seq_len(BPER))
todo <- setdiff(seq_len(nrow(jobs)), as.integer(sub("\\.rds$", "", setdiff(list.files(DR), "point.rds"))))
cat("bootstrap jobs:", nrow(jobs), "| remaining:", length(todo), "\n"); t0 <- Sys.time()
invisible(mclapply(todo, function(i) {
  set.seed(1e5 + i); dk <- apply_imp(jobs$k[i])
  pick <- sample(sids, length(sids), replace = TRUE)
  ix <- unlist(rows_by_s[pick], use.names = FALSE)
  dd <- dk[ix, ]; dd$.s <- rep(seq_along(pick), lengths(rows_by_s[pick]))
  r <- one_draw(dd); r <- if (is.null(r)) NULL else lapply(r, stats_of)
  saveRDS(r, file.path(DR, paste0(i, ".rds"))); NULL
}, mc.cores = NCOR, mc.preschedule = FALSE))
cat("bootstrap done in", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "min\n")

draws <- lapply(seq_len(nrow(jobs)), function(i) readRDS(file.path(DR, paste0(i, ".rds"))))
ok <- draws[!sapply(draws, is.null)]; cat("usable draws:", length(ok), "of", nrow(jobs), "\n")
out <- do.call(rbind, lapply(names(pt), function(nm) {
  D <- do.call(rbind, lapply(ok, `[[`, nm))
  do.call(rbind, lapply(names(pt[[nm]]), function(st) {
    x <- D[, st]; x <- x[is.finite(x)]
    data.frame(term = nm, stat = st, estimate = unname(pt[[nm]][st]),
               lo = unname(quantile(x, 0.025)), hi = unname(quantile(x, 0.975)),
               n_draws = length(x), row.names = NULL) })) }))
write.csv(out, file.path(OUT, "AB_attenuation.csv"), row.names = FALSE)
print(out, row.names = FALSE, digits = 3)
cat("DONE\n")
