#!/bin/bash -l
#SBATCH -J ms_vacc_probe
#SBATCH -A r01109
#SBATCH -p general
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH -o slurm_ms_vacc_probe_%j.out
cd /N/project/depot/hw56/ms_covid/aou_covid
source /N/project/depot/hw56/RLH/.venv/bin/activate
python probe_vacc_ndc_ms.py
