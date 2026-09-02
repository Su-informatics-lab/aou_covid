#!/bin/bash -l
#SBATCH -J ms_cov_probe
#SBATCH -A r01109
#SBATCH -p general
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --time=01:00:00
#SBATCH -o slurm_ms_cov_probe_%j.out

# Does the un-restricted coverage span actually change the MarketScan matching?
# Read-only probe. Decides whether the multi-hour ETL re-run is worth paying for
# instead of guessing, which is the lesson the All of Us side taught this study.

cd /N/project/depot/hw56/ms_covid/aou_covid
source /N/project/depot/hw56/RLH/.venv/bin/activate

export PROBE_MEM=80GB
export PROBE_TMP=/N/scratch/hw56/duckdb_tmp_$SLURM_JOB_ID
mkdir -p "$PROBE_TMP"

echo "=== node $(hostname) | started $(date) | cpus $SLURM_CPUS_PER_TASK ==="
python probe_coverage_span_preindex_ms.py
rc=$?
echo "=== rc=$rc | finished $(date) ==="
rm -rf "$PROBE_TMP"
exit $rc
