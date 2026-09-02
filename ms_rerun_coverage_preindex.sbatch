#!/bin/bash -l
#SBATCH -J ms_rerun_cov
#SBATCH -A r01109
#SBATCH -p general
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --time=08:00:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=hw56@iu.edu
#SBATCH -o slurm_ms_rerun_cov_%j.out

# MarketScan re-run with coverage_span_days truncated at the COVID index date.
#
# Why the full ETL and not just 01b onward: the fix changes 06_matching_variables.csv,
# which only 01_ms_etl.py writes.
#
# The evidence for spending the time, from probe_coverage_span_preindex_ms.py:
#   case-vs-control SMD for coverage span   -0.140 -> -0.302,  a change of 0.162
#   median span, controls  1154 -> 469 days;  cases 1094 -> 382 days
#   unchanged for 0.3% of people
# For scale, the All of Us diagnosis-count SMD moved 0.489 -> 0.410, a change of
# 0.079, and that shifted every downstream estimate. This is twice that.
#
# Charlson stays pre-index: dx_long is built with
# `WHERE d.dx_date < c.covid_index_date` (01_ms_etl.py line 276) and Charlson is
# derived from it, so a fresh ETL run does not regress the June fix. Verified by
# an assertion below rather than by trust.

set -o pipefail
cd /N/project/depot/hw56/ms_covid/aou_covid
source /N/project/depot/hw56/RLH/.venv/bin/activate
module load r/4.5.1
export R_LIBS_USER=~/R/x86_64-pc-linux-gnu-library/4.5
export PROBE_MEM=80GB
export PROBE_TMP=/N/scratch/hw56/duckdb_tmp_$SLURM_JOB_ID
mkdir -p "$PROBE_TMP" "$R_LIBS_USER"

echo "=== node $(hostname) | started $(date) | cpus $SLURM_CPUS_PER_TASK ==="

# ── Preserve the pre-re-run aggregates, so the comparison stays possible ──
BK=results/ms_before_coverage_fix_$(date +%Y%m%d)
mkdir -p "$BK"
cp -n results/ms/0[78]*.csv results/ms/0[78]*.txt results/ms/*coefficients.csv \
      results/ms/table1_demographics.csv results/ms/*etable*.csv "$BK"/ 2>/dev/null
echo "--- backed up $(ls "$BK" | wc -l) aggregate files to $BK ---"

# ── Record the probe artifact ────────────────────────────────────────────
python probe_coverage_span_preindex_ms.py || echo "probe failed, continuing"

# ── ETL ──────────────────────────────────────────────────────────────────
echo "--- 01_ms_etl.py ---"
python 01_ms_etl.py || { echo "FAILED: 01_ms_etl.py"; exit 1; }

echo "--- verifying the fix actually bit ---"
python - <<'PY'
import pandas as pd, sys
m = pd.read_csv("results/ms/06_matching_variables.csv")
c = pd.read_csv("results/ms/01_covid_cohort.csv", usecols=["person_id", "severity"])
d = m.merge(c, on="person_id")
import numpy as np
a = d.loc[d.severity == 1, "coverage_span_days"].astype(float)
b = d.loc[d.severity == 0, "coverage_span_days"].astype(float)
smd = (a.mean() - b.mean()) / np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
print(f"  coverage_span_days case-vs-control SMD = {smd:+.4f}  (was -0.140, probe predicted -0.302)")
print(f"  median span cases {a.median():.0f}, controls {b.median():.0f}")
if abs(smd) < 0.20:
    sys.exit("ERROR: the index truncation did not take effect")
ch = pd.read_csv("results/ms/03_charlson.csv")
print(f"  Dementia = {int(ch.Dementia.sum()):,}  (pre-index expects ~5,527; all-records was 12,250)")
assert ch.Dementia.sum() < 10000, "ERROR: Charlson regressed to all-records"
print("  OK")
PY
[ $? -ne 0 ] && { echo "verification failed"; exit 1; }

echo "--- 01b_psm.R ---";  Rscript 01b_psm.R ms  || { echo "FAILED: 01b_psm.R"; exit 1; }
echo "--- 02_models.R ---"; Rscript 02_models.R ms || { echo "FAILED: 02_models.R"; exit 1; }
echo "--- 02b_variance_sensitivity.R ---"; Rscript 02b_variance_sensitivity.R ms || echo "02b failed, continuing"
echo "--- 04_tables.py ---"; python 04_tables.py ms || { echo "FAILED: 04_tables.py"; exit 1; }

# ── Headline numbers ─────────────────────────────────────────────────────
echo ""; echo "=========================================="
echo "MARKETSCAN AFTER THE COVERAGE-SPAN FIX"
echo "=========================================="
python - <<'PY'
import pandas as pd, os
R = "results/ms"
print("--- pre-matching SMD (published: num_diagnosis 0.613, coverage span -0.137) ---")
print(pd.read_csv(f"{R}/07c_smd_pre_matching.csv").to_string(index=False))
print("\n--- Table 1 N (published: 139,468 cases / 554,214 controls) ---")
t1 = pd.read_csv(f"{R}/table1_demographics.csv")
print(t1.head(2).to_string(index=False))
print("\n--- base model (published: female .50, vacc .48, omicron .47, "
      "chronic pulm .85, mild liver .78, cerebrovascular .86, AIDS 1.28) ---")
b = pd.read_csv(f"{R}/base_model_coefficients.csv")
keep = b.variable.astype(str).str.contains(
    "Female|vacc|age65|wave|Pulmonary|Liver_Disease_Mild|Cerebrovascular|AIDS|HIV|"
    "Renal_Disease_Severe|Metastatic", case=False, na=False)
print(b[keep][["variable","AOR","CI_lower","CI_upper","p_value"]].to_string(index=False))
PY

rm -rf "$PROBE_TMP"
echo "=== finished $(date) ==="
