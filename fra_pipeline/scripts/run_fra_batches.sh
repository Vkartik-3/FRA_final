#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd .. && pwd)"   # fra_pipeline/
SBATCH_SCRIPT="$PROJECT_ROOT/scripts/fra_array_job.sbatch"

TOTAL_SIMULATIONS=10000
BATCH_SIZE=100

NUM_JOBS=$(( (TOTAL_SIMULATIONS + BATCH_SIZE - 1) / BATCH_SIZE ))

echo "========================================"
echo "Submitting FRA jobs"
echo "Project root: $PROJECT_ROOT"
echo "Total simulations: $TOTAL_SIMULATIONS"
echo "Batch size: $BATCH_SIZE"
echo "Total jobs: $NUM_JOBS"
echo "========================================"

sbatch --array=1-"$NUM_JOBS" "$SBATCH_SCRIPT"