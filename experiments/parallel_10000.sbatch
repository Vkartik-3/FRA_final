#!/bin/bash
# Parallel arm for the 10,000-plan production-scale benchmark.
# 100 array tasks x 100 plans = 10,000 plans (mirrors the production fra_array_job.sbatch scale).
# Pair with serial_10000.sbatch. Same commit + input checksum. Queue wait excluded when you
# derive wall clock from sacct (earliest task Start -> latest task End) via collect_10k_evidence.sh.
#SBATCH --job-name=fra_par_10k
#SBATCH --output=experiments/logs/par10k_%A_%a.out
#SBATCH --error=experiments/logs/par10k_%A_%a.err
#SBATCH --account=pn_roke031220s
#SBATCH --partition=short-28core
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --array=1-100

set -euo pipefail
cd "$HOME/FRA_final"
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate fra311
export PROJ_DATA="$CONDA_PREFIX/share/proj"
export PROJ_LIB="$CONDA_PREFIX/share/proj"
export GDAL_DATA="$CONDA_PREFIX/share/gdal"

REP="${REP:?REP must be supplied (e.g. sbatch --export=REP=1 experiments/parallel_10000.sbatch)}"
TASK_ID="$SLURM_ARRAY_TASK_ID"
START_PLAN=$(( (TASK_ID - 1) * 100 + 1 ))
END_PLAN=$(( TASK_ID * 100 ))
OUTPUT_DIR="/tmp/fra_bench10k_parallel_${USER}_${REP}/task_${TASK_ID}"
rm -rf "$OUTPUT_DIR"; mkdir -p "$OUTPUT_DIR"

echo "ARM=parallel_10k REP=$REP JOB_ID=$SLURM_JOB_ID TASK=$TASK_ID NODE=$(hostname)"
echo "COMMIT=$(git rev-parse HEAD) PLANS=$START_PLAN-$END_PLAN"
echo "START_TIME=$(date --iso-8601=seconds)"

/usr/bin/time -v \
python fra_pipeline/scripts/run_baseline_simple.py \
  --start "$START_PLAN" --end "$END_PLAN" --output "$OUTPUT_DIR" --seed_offset "$START_PLAN"

PLAN_COUNT=$(find "$OUTPUT_DIR" -maxdepth 1 -name 'plan_*.json' | wc -l)
echo "PLAN_COUNT=$PLAN_COUNT"
[ "$PLAN_COUNT" -eq 100 ] || { echo "ERROR: expected 100"; exit 1; }
echo "END_TIME=$(date --iso-8601=seconds)"
echo "PARALLEL_10K_TASK_PASSED"
