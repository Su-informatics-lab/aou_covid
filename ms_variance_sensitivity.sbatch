#!/bin/bash -l
#SBATCH -J ms_var_sens
#SBATCH -A r01109
#SBATCH -p general
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=hw56@iu.edu
#SBATCH -o slurm_ms_var_sens_%j.out

# eTable 10b Panel B — the MarketScan variance comparison, refit on the cohort
# produced by the pre-index matching-variable correction.
#
# Why this job exists: 02b_variance_sensitivity.R ran inside job 10186336 behind
# `|| echo "02b failed, continuing"`, so a failure there would not have stopped
# the pipeline and would not appear in the summary block. The Panel B currently
# printed in the supplement reports 693,682 matched observations and a maximum
# control reuse of 19; the corrected cohort is 637,679 and 21. Panel A (All of
# Us) was refit on 2026-09-02 and shows a median CI ratio of 1.00 with no
# inference changing at P = 0.05.
#
# The guard below refuses to run on the wrong input. It checks content, not
# mtimes: this project has now been bitten four times by a file whose path and
# timestamp were right and whose contents were pre-correction.
#
# Submit:  sbatch ms_variance_sensitivity.sbatch
# Read:    the RESULT block at the end of slurm_ms_var_sens_<jobid>.out

set -o pipefail
cd /N/project/depot/hw56/ms_covid/aou_covid
source /N/project/depot/hw56/RLH/.venv/bin/activate
module load r/4.5.1

export R_LIBS_USER="$HOME/R/x86_64-pc-linux-gnu-library/4.5"
mkdir -p "$R_LIBS_USER"

# r/4.5.1 is only offered under gnu/9.3.0, whose libstdc++ lacks GLIBCXX_3.4.32,
# which the Rcpp inside that module needs. R rebuilds LD_LIBRARY_PATH from its
# own etc/ldpaths at startup, so preload a newer libstdc++ scoped to R alone.
GCCLIB=/N/soft/rhel8/gcc/14.2.0/lib64/libstdc++.so.6
run_r() { LD_PRELOAD="$GCCLIB" Rscript "$@"; }

echo "=== node $(hostname) | started $(date) ==="

echo "--- guard: is results/ms/08_regression_base.csv the corrected cohort? ---"
python - <<'PY'
import pandas as pd, sys
f = "results/ms/08_regression_base.csv"
d = pd.read_csv(f, usecols=["person_id", "Treatment", "stratum"])
cases = int((d.Treatment == 1).sum()); ctrl = int((d.Treatment == 0).sum())
strata = d.stratum.nunique(); uniq = d.loc[d.Treatment == 0, "person_id"].nunique()
reuse = int(d.loc[d.Treatment == 0, "person_id"].value_counts().max())
print(f"  observations {len(d):,}   cases {cases:,}   controls {ctrl:,}")
print(f"  strata {strata:,}   unique controls {uniq:,}   max reuse {reuse}")
# Hard invariants: these four are printed in Figure 1b and eTable 10 and define
# the analytic cohort. If any differs, the input is not the corrected file.
want = dict(obs=637679, cases=127696, ctrl=509983, strata=127696)
got  = dict(obs=len(d), cases=cases, ctrl=ctrl, strata=strata)
bad = {k: (got[k], want[k]) for k in want if got[k] != want[k]}
if bad:
    print("  MISMATCH (got, expected):", bad)
    sys.exit("STOP: this is not the corrected MarketScan cohort. Do not use the output.")
# Informational: the manuscript prints 443,061 unique controls and a maximum
# reuse of 21. A difference here does not stop the run, but report it.
if (uniq, reuse) != (443061, 21):
    print(f"  NOTE: unique controls {uniq:,} and max reuse {reuse} differ from the "
          f"published 443,061 and 21 -- worth checking, not fatal")
print("  OK - the four cohort invariants match Figure 1b and eTable 10")
PY
[ $? -ne 0 ] && { echo "guard failed"; exit 1; }

echo "--- 02b_variance_sensitivity.R ms ---"
run_r 02b_variance_sensitivity.R ms || { echo "FAILED: 02b_variance_sensitivity.R"; exit 1; }

echo ""; echo "=========================================="
echo "RESULT — eTable 10b Panel B"
echo "=========================================="
python - <<'PY'
import pandas as pd
t = pd.read_csv("results/ms/variance_sensitivity_etable11b.csv")
print("Fingerprint (corrected MarketScan base model: female 0.75, vaccinated 0.50):")
print(t[t.variable.astype(str).str.contains("Female|vacc", case=False, na=False)].to_string(index=False))
print()
print(f"rows: {len(t)}   median CI ratio: {t.CI_ratio.median():.2f}   flips: {int(t.flip.notna().sum())}")
print()
print(t.to_string(index=False))
PY
echo "=== finished $(date) ==="
