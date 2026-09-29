#!/bin/bash -l
#SBATCH -J ms_covidnet_waves
#SBATCH -A r01109
#SBATCH -p general
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --time=04:00:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=hw56@iu.edu
#SBATCH -o slurm_ms_covidnet_waves_%j.out

# 2026-09-28: pandemic waves redefined to the CDC COVID-NET variant-predominance
# periods (Taylor et al, MMWR 2022;71:466-473): Delta July 1 to December 18,
# 2021; Omicron from December 19, 2021; pre-Delta before July 1, 2021. The
# earlier boundaries (June 15 and December 15, 2021) had no documented source.
# Matching does not use wave, so the matched cohort is unchanged; only the wave
# covariate is recoded from each observation's own index date, and the base
# model (02_models.R) and its variance comparison (02b) are refitted.

set -o pipefail
cd /N/project/depot/hw56/ms_covid/aou_covid
source /N/project/depot/hw56/RLH/.venv/bin/activate
module load r/4.5.1
export R_LIBS_USER="$HOME/R/x86_64-pc-linux-gnu-library/4.5"
GCCLIB=/N/soft/rhel8/gcc/14.2.0/lib64/libstdc++.so.6
run_r() { LD_PRELOAD="$GCCLIB" Rscript "$@"; }
echo "=== node $(hostname) | started $(date) ==="

R=results/ms
B=$R/wave0615_backup
mkdir -p $B
for f in 08_regression_base.csv base_model_coefficients.csv all_model_coefficients.csv \
         base_clogit.RData variance_sensitivity_etable11b.csv; do
  [ -f $B/$f ] || cp -p $R/$f $B/$f
done

python - <<'PY'
import pandas as pd
R = "results/ms"
d = pd.read_csv(f"{R}/wave0615_backup/08_regression_base.csv")
c = pd.read_csv(f"{R}/01_covid_cohort.csv", usecols=["person_id", "covid_index_date"])
assert c.person_id.is_unique
d = d.merge(c, on="person_id", how="left")
assert d.covid_index_date.notna().all(), "index date missing"
t = pd.to_datetime(d.covid_index_date)
old = d.pandemic_wave.copy()
d["pandemic_wave"] = "pre_delta"
d.loc[t >= "2021-07-01", "pandemic_wave"] = "delta"
d.loc[t >= "2021-12-19", "pandemic_wave"] = "omicron"
print("old wave vs new wave (observations):")
print(pd.crosstab(old, d.pandemic_wave))
d.drop(columns="covid_index_date").to_csv(f"{R}/08_regression_base.csv", index=False)
print("rows", len(d))
PY
[ $? -eq 0 ] || { echo "FAILED: wave recode"; exit 1; }

echo "--- 02_models.R ---"; run_r 02_models.R ms || { echo "FAILED: 02_models.R"; exit 1; }
echo "--- 02b_variance_sensitivity.R ---"; run_r 02b_variance_sensitivity.R ms || { echo "FAILED: 02b"; exit 1; }
echo "=== done $(date) ==="
