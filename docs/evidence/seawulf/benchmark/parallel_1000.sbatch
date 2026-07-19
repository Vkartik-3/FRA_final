#!/bin/bash
#SBATCH --job-name=fra_parallel
#SBATCH --output=docs/evidence/seawulf/benchmark/logs/parallel_%A_%a.out
#SBATCH --error=docs/evidence/seawulf/benchmark/logs/parallel_%A_%a.err
#SBATCH --account=pn_roke031220s
#SBATCH --partition=short-28core
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --array=1-10

set -euo pipefail

cd "$HOME/FRA_final"

source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate fra311

export PROJ_DATA="$CONDA_PREFIX/share/proj"
export PROJ_LIB="$CONDA_PREFIX/share/proj"
export GDAL_DATA="$CONDA_PREFIX/share/gdal"

REP="${REP:?REP must be supplied}"
TASK_ID="$SLURM_ARRAY_TASK_ID"

START_PLAN=$(( (TASK_ID - 1) * 100 + 1 ))
END_PLAN=$(( TASK_ID * 100 ))

OUTPUT_DIR="/tmp/fra_benchmark_parallel_${USER}_${REP}/task_${TASK_ID}"

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

echo "BENCHMARK_ARM=parallel"
echo "REPETITION=$REP"
echo "JOB_ID=$SLURM_JOB_ID"
echo "ARRAY_TASK_ID=$TASK_ID"
echo "NODE=$(hostname)"
echo "COMMIT=$(git rev-parse HEAD)"
echo "START_PLAN=$START_PLAN"
echo "END_PLAN=$END_PLAN"
echo "START_TIME=$(date --iso-8601=seconds)"
echo "OUTPUT_DIR=$OUTPUT_DIR"

/usr/bin/time -v \
python fra_pipeline/scripts/run_baseline_simple.py \
  --start "$START_PLAN" \
  --end "$END_PLAN" \
  --output "$OUTPUT_DIR" \
  --seed_offset "$START_PLAN"

PLAN_COUNT=$(find "$OUTPUT_DIR" -maxdepth 1 -name 'plan_*.json' | wc -l)

echo "PLAN_COUNT=$PLAN_COUNT"

if [ "$PLAN_COUNT" -ne 100 ]; then
    echo "ERROR: expected 100 plans"
    exit 1
fi

echo "END_TIME=$(date --iso-8601=seconds)"
echo "PARALLEL_TASK_PASSED"
