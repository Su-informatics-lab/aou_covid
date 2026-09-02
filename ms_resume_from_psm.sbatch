#!/bin/bash -l
#SBATCH -J ms_resume_psm
#SBATCH -A r01109
#SBATCH -p general
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --time=04:00:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=hw56@iu.edu
#SBATCH -o slurm_ms_resume_psm_%j.out

# Resume the MarketScan re-run from 01b_psm.R.
#
# Job 10186030 completed the ETL and then died on an R library path:
# 01b_psm.R line 27 calls install.packages(pkg) with no lib argument, R picked
# the first .libPaths() entry, which is the read-only module tree, and quit.
# The June script survived this by installing the packages itself, with an
# explicit lib=, before any analysis script ran. That preamble is restored here.
#
# The ETL does not need repeating. It wrote, at 22:25-22:36 on 2026-09-01:
#   coverage_span_days case-vs-control SMD  -0.3630   (was -0.140)
#   median span   cases 398 days, controls 559
#   Dementia 5,527, so Charlson stayed pre-index
# The guard below re-checks both rather than trusting the log.

set -o pipefail
cd /N/project/depot/hw56/ms_covid/aou_covid
source /N/project/depot/hw56/RLH/.venv/bin/activate
module load r/4.5.1

export R_LIBS_USER="$HOME/R/x86_64-pc-linux-gnu-library/4.5"
mkdir -p "$R_LIBS_USER"

# The module tree is inconsistent and this is the whole reason job 10186282 died.
# r/4.5.1 is only offered under gnu/9.3.0, but the Rcpp shipped inside that R
# module was compiled against a newer libstdc++ and asks for GLIBCXX_3.4.32,
# which 9.3.0 does not provide. R rebuilds LD_LIBRARY_PATH from its own
# etc/ldpaths at startup, so exporting LD_LIBRARY_PATH ahead of it does nothing,
# and overriding R_LD_LIBRARY_PATH breaks R outright by hiding libR.so.
# Swapping to gnu/14.2.0 removes r/4.5.1 from the module tree entirely.
#
# So: preload a libstdc++ that does have the symbol, and scope it to R alone so
# the Python steps keep the environment they were tested under.
GCCLIB=/N/soft/rhel8/gcc/14.2.0/lib64/libstdc++.so.6
run_r() { LD_PRELOAD="$GCCLIB" Rscript "$@"; }

echo "=== node $(hostname) | started $(date) ==="
echo "R_LIBS_USER=$R_LIBS_USER"
echo "LD_PRELOAD for R = $GCCLIB"

echo "--- checking the R packages actually load ---"
run_r -e '
lib <- Sys.getenv("R_LIBS_USER")
.libPaths(c(lib, .libPaths()))
need <- c("MatchIt","cobalt","dplyr","readr","survival","sandwich","lmtest")
bad <- character(0)
for (p in need) {
  ok <- tryCatch({ suppressPackageStartupMessages(library(p, character.only = TRUE)); TRUE },
                 error = function(e) { cat(" FAIL ", p, ": ", substr(conditionMessage(e), 1, 120), "\n", sep=""); FALSE })
  if (ok) cat(" ok   ", p, "\n") else bad <- c(bad, p)
}
if (length(bad)) { cat("CANNOT LOAD:", paste(bad, collapse=", "), "\n"); quit(status = 1) }
cat("all seven load\n")
' || { echo "FAILED: R packages will not load"; exit 1; }

echo "--- guard: is the ETL output the fixed one? ---"
python - <<'PY'
import pandas as pd, numpy as np, sys, os, time
R = "results/ms"
for f in ("01_covid_cohort.csv", "03_charlson.csv", "06_matching_variables.csv"):
    age_h = (time.time() - os.path.getmtime(f"{R}/{f}")) / 3600
    print(f"  {f:32s} {age_h:5.1f} h old")
    if age_h > 24:
        sys.exit(f"ERROR: {f} predates the coverage-span re-run")
m = pd.read_csv(f"{R}/06_matching_variables.csv")
c = pd.read_csv(f"{R}/01_covid_cohort.csv", usecols=["person_id", "severity"])
d = m.merge(c, on="person_id")
a = d.loc[d.severity == 1, "coverage_span_days"].astype(float)
b = d.loc[d.severity == 0, "coverage_span_days"].astype(float)
smd = (a.mean() - b.mean()) / np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
print(f"  coverage_span_days SMD = {smd:+.4f}  (pre-fix -0.140)")
if abs(smd) < 0.20:
    sys.exit("ERROR: matching variables are not the truncated ones")
ch = pd.read_csv(f"{R}/03_charlson.csv")
print(f"  Dementia = {int(ch.Dementia.sum()):,}")
assert ch.Dementia.sum() < 10000, "ERROR: Charlson regressed to all-records"
print("  OK")
PY
[ $? -ne 0 ] && { echo "guard failed"; exit 1; }

echo "--- 01b_psm.R ---";  run_r 01b_psm.R ms  || { echo "FAILED: 01b_psm.R"; exit 1; }
echo "--- 02_models.R ---"; run_r 02_models.R ms || { echo "FAILED: 02_models.R"; exit 1; }
echo "--- 02b_variance_sensitivity.R ---"; run_r 02b_variance_sensitivity.R ms || echo "02b failed, continuing"
echo "--- 04_tables.py ---"; python 04_tables.py ms || { echo "FAILED: 04_tables.py"; exit 1; }

echo ""; echo "=========================================="
echo "MARKETSCAN AFTER THE COVERAGE-SPAN FIX"
echo "=========================================="
python - <<'PY'
import pandas as pd
R = "results/ms"
print("--- pre-matching SMD (published: num_diagnosis 0.613, coverage span -0.137) ---")
print(pd.read_csv(f"{R}/07c_smd_pre_matching.csv").to_string(index=False))
print("\n--- control reuse ---")
print(pd.read_csv(f"{R}/07b_control_reuse.csv").to_string(index=False))
print("\n--- Table 1 N (published: 139,468 cases / 554,214 controls) ---")
print(pd.read_csv(f"{R}/table1_demographics.csv").head(2).to_string(index=False))
print("\n--- base model (published: female .50, vacc .48, age65 1.73, delta 1.47,")
print("    omicron .47, chronic pulm .85, mild liver .78, cerebrovascular .86,")
print("    MI .94, HIV .86, AIDS 1.28, renal severe 2.44, metastatic 1.67) ---")
b = pd.read_csv(f"{R}/base_model_coefficients.csv")
keep = b.variable.astype(str).str.contains(
    "Female|vacc|age|wave|Pulmonary|Liver|Cerebro|AIDS|HIV|Renal|Metastatic|"
    "Myocardial|Congestive|Dementia|Diabetes|Hemiplegia|Malignancy|Peptic|"
    "Peripheral|Rheumatic", case=False, na=False)
print(b[keep][["variable","AOR","CI_lower","CI_upper","p_value"]].to_string(index=False))
PY
echo "=== finished $(date) ==="
