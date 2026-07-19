#!/bin/bash
# Serial baseline arm for the 10,000-plan production-scale benchmark.
# One process, one node, 10,000 plans. Pair with parallel_10000.sbatch (same commit/input).
# NOTE: this measures a CLUSTER serial baseline. It is NOT the historical "~4 hours on a
# local laptop" figure — different hardware. Use it for a cluster-scale speedup, and label
# the historical 13x separately (see docs/SEAWULF_EVIDENCE_REPORT.md).
#SBATCH --job-name=fra_serial_10k
#SBATCH --output=experiments/logs/serial10k_%j.out
#SBATCH --error=experiments/logs/serial10k_%j.err
#SBATCH --account=pn_roke031220s
#SBATCH --partition=long-28core
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=02:00:00

set -euo pipefail
cd "$HOME/FRA_final"
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate fra311
export PROJ_DATA="$CONDA_PREFIX/share/proj"
export PROJ_LIB="$CONDA_PREFIX/share/proj"
export GDAL_DATA="$CONDA_PREFIX/share/gdal"

REP="${REP:?REP must be supplied (e.g. sbatch --export=REP=1 experiments/serial_10000.sbatch)}"
OUTPUT_DIR="/tmp/fra_bench10k_serial_${USER}_${REP}"
rm -rf "$OUTPUT_DIR"; mkdir -p "$OUTPUT_DIR"

echo "ARM=serial_10k REP=$REP JOB_ID=$SLURM_JOB_ID NODE=$(hostname)"
echo "COMMIT=$(git rev-parse HEAD)"
echo "START_TIME=$(date --iso-8601=seconds)"

/usr/bin/time -v \
python fra_pipeline/scripts/run_baseline_simple.py \
  --start 1 --end 10000 --output "$OUTPUT_DIR" --seed_offset 1

PLAN_COUNT=$(find "$OUTPUT_DIR" -maxdepth 1 -name 'plan_*.json' | wc -l)
echo "PLAN_COUNT=$PLAN_COUNT"
[ "$PLAN_COUNT" -eq 10000 ] || { echo "ERROR: expected 10000"; exit 1; }
echo "END_TIME=$(date --iso-8601=seconds)"
echo "SERIAL_10K_PASSED"
