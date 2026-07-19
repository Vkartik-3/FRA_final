#!/bin/bash
#SBATCH --job-name=fra_serial
#SBATCH --output=docs/evidence/seawulf/benchmark/logs/serial_%j.out
#SBATCH --error=docs/evidence/seawulf/benchmark/logs/serial_%j.err
#SBATCH --account=pn_roke031220s
#SBATCH --partition=short-28core
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=00:30:00

set -euo pipefail

cd "$HOME/FRA_final"

source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate fra311

export PROJ_DATA="$CONDA_PREFIX/share/proj"
export PROJ_LIB="$CONDA_PREFIX/share/proj"
export GDAL_DATA="$CONDA_PREFIX/share/gdal"

REP="${REP:?REP must be supplied}"
OUTPUT_DIR="/tmp/fra_benchmark_serial_${USER}_${REP}"

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

echo "BENCHMARK_ARM=serial"
echo "REPETITION=$REP"
echo "JOB_ID=$SLURM_JOB_ID"
echo "NODE=$(hostname)"
echo "COMMIT=$(git rev-parse HEAD)"
echo "START_TIME=$(date --iso-8601=seconds)"
echo "OUTPUT_DIR=$OUTPUT_DIR"

/usr/bin/time -v \
python fra_pipeline/scripts/run_baseline_simple.py \
  --start 1 \
  --end 1000 \
  --output "$OUTPUT_DIR" \
  --seed_offset 1

PLAN_COUNT=$(find "$OUTPUT_DIR" -maxdepth 1 -name 'plan_*.json' | wc -l)

echo "PLAN_COUNT=$PLAN_COUNT"

if [ "$PLAN_COUNT" -ne 1000 ]; then
    echo "ERROR: expected 1000 plans"
    exit 1
fi

echo "END_TIME=$(date --iso-8601=seconds)"
echo "SERIAL_BENCHMARK_PASSED"
