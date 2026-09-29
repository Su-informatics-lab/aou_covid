#!/bin/bash -l
#SBATCH -J ms_vacc_product
#SBATCH -A r01109
#SBATCH -p general
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --time=04:00:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=hw56@iu.edu
#SBATCH -o slurm_ms_vacc_product_%j.out

# 2026-09-29: COVID-19 vaccination recoded from NDC labeler prefixes (59267, 80777,
# 59676), which also matched non-vaccine Janssen products (probe job 10755445:
# 160 of 71,631 flagged persons) and missed Comirnaty under labeler 00069 (29), to
# the vaccine products listed in AMA CPT Appendix Q (codes 91300-91317) and the NC
# Medicaid 2023-2024 COVID-19 vaccine guidelines (91304, 91318-91322). Matching does
# not use vaccination, so the matched cohort is unchanged; only the vaccination
# covariate is recoded and the base model (02_models.R) and 02b are refitted.

set -o pipefail
cd /N/project/depot/hw56/ms_covid/aou_covid
source /N/project/depot/hw56/RLH/.venv/bin/activate
module load r/4.5.1
export R_LIBS_USER="$HOME/R/x86_64-pc-linux-gnu-library/4.5"
GCCLIB=/N/soft/rhel8/gcc/14.2.0/lib64/libstdc++.so.6
run_r() { LD_PRELOAD="$GCCLIB" Rscript "$@"; }
echo "=== node $(hostname) | started $(date) ==="

R=results/ms
B=$R/vacc_prefix_backup
mkdir -p $B
for f in 05_vaccination.csv 08_regression_base.csv base_model_coefficients.csv all_model_coefficients.csv \
         base_clogit.RData variance_sensitivity_etable11b.csv; do
  [ -f $B/$f ] || cp -p $R/$f $B/$f
done

python - <<'PY'
import duckdb, pandas as pd
MS_DIR = "/N/project/Marketscan1/parquet"; R = "results/ms"
PROD = ["592671000","592671025","592670304","592671404","592671055","592670565","592670078",
        "592670609","000692025","807770273","807770100","807770282","807770279","807770283",
        "807770275","596760580","806310100","806311000","592674315","592674331","000692362",
        "000692377","807770287","807770102","806310105"]
con = duckdb.connect()
c = pd.read_csv(f"{R}/01_covid_cohort.csv", usecols=["person_id","covid_index_date"])
con.register("coh", c)
u = " UNION ALL ".join(
    f"SELECT ENROLID AS person_id, SVCDATE AS d, SUBSTR(LPAD(CAST(NDCNUM AS VARCHAR), 11, '0'),1,9) AS prod "
    f"FROM read_parquet('{MS_DIR}/mscan_{y}_d.parquet')" for y in ("2021","2022","2023"))
pl = ",".join(f"'{p}'" for p in PROD)
v = con.sql(f"""SELECT x.person_id, MIN(x.d) AS first_vacc_date FROM ({u}) x
  WHERE x.prod IN ({pl}) AND x.person_id IN (SELECT person_id FROM coh) GROUP BY 1""").df()
v = v.merge(c, on="person_id")
v["pre"] = pd.to_datetime(v.first_vacc_date) <= pd.to_datetime(v.covid_index_date)
vs = c[["person_id"]].merge(v[["person_id","pre"]], on="person_id", how="left")
vs["vaccination"] = "Unknown"; vs.loc[vs.pre == True, "vaccination"] = "Vaccinated"
vs[["person_id","vaccination"]].to_csv(f"{R}/05_vaccination.csv", index=False)
d = pd.read_csv(f"{R}/vacc_prefix_backup/08_regression_base.csv")
old = d.vaccination.copy()
m = dict(zip(vs.person_id, vs.vaccination))
d["vaccination"] = d.person_id.map(m)
assert d.vaccination.notna().all()
print("old vs new vaccination (observations):"); print(pd.crosstab(old, d.vaccination))
d.to_csv(f"{R}/08_regression_base.csv", index=False)
print("rows", len(d))
PY
[ $? -eq 0 ] || { echo "FAILED: vaccination recode"; exit 1; }

echo "--- 02_models.R ---"; run_r 02_models.R ms || { echo "FAILED: 02_models.R"; exit 1; }
echo "--- 02b_variance_sensitivity.R ---"; run_r 02b_variance_sensitivity.R ms || { echo "FAILED: 02b"; exit 1; }
echo "=== done $(date) ==="
