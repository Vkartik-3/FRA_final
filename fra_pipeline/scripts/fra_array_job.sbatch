#!/bin/bash
#SBATCH --job-name=fra_pipeline
#SBATCH --output=../outputs/logs/fra_%A_%a.out
#SBATCH --error=../outputs/logs/fra_%A_%a.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=compute
#SBATCH --array=1-100

set -euo pipefail

echo "========================================"
echo "FRA JOB START"
echo "Job ID: ${SLURM_JOB_ID:-N/A}"
echo "Array Task ID: ${SLURM_ARRAY_TASK_ID:-N/A}"
echo "Node: $(hostname)"
echo "Time: $(date)"
echo "========================================"

# ----------------------------------
# PATH SETUP (BASED ON YOUR STRUCTURE)
# ----------------------------------
PROJECT_ROOT="$(cd .. && pwd)"         # fra_pipeline/
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
OUTPUT_DIR="$PROJECT_ROOT/outputs"

BASELINE_DIR="$OUTPUT_DIR/plan_assignments"
FRA_DIR="$OUTPUT_DIR/fra"
ANALYSIS_DIR="$OUTPUT_DIR/analysis"
LOG_DIR="$OUTPUT_DIR/logs"

mkdir -p "$BASELINE_DIR" "$FRA_DIR" "$ANALYSIS_DIR" "$LOG_DIR"

echo "[INFO] PROJECT_ROOT=$PROJECT_ROOT"

# ----------------------------------
# ACTIVATE YOUR ENV (REAL PATH)
# ----------------------------------
if [ -f "$PROJECT_ROOT/env/bin/activate" ]; then
    echo "[INFO] Activating env..."
    source "$PROJECT_ROOT/env/bin/activate"
else
    echo "[ERROR] Virtual environment not found!"
    exit 1
fi

echo "[INFO] Python: $(which python)"
python --version

# ----------------------------------
# BATCH LOGIC (YOUR 10K SIMULATION MODEL)
# ----------------------------------
TASK_ID=${SLURM_ARRAY_TASK_ID:-1}
BATCH_SIZE=100

START_PLAN=$(( (TASK_ID - 1) * BATCH_SIZE + 1 ))
END_PLAN=$(( TASK_ID * BATCH_SIZE ))

echo "[INFO] Processing plans $START_PLAN → $END_PLAN"

# ----------------------------------
# THREAD CONTROL (IMPORTANT FOR GDAL/GEOS)
# ----------------------------------
export OMP_NUM_THREADS=16
export MKL_NUM_THREADS=16

# ----------------------------------
# STAGE 1: BASELINE GENERATION
# ----------------------------------
echo "[STAGE 1] Baseline generation"

python "$SCRIPTS_DIR/run_baseline_simple.py" \
    --start "$START_PLAN" \
    --end "$END_PLAN" \
    --output "$BASELINE_DIR"

echo "[STAGE 1 DONE]"

# ----------------------------------
# STAGE 2: FRA TRANSFORMATION
# ----------------------------------
echo "[STAGE 2] FRA transformation"

python "$SCRIPTS_DIR/fra_gluing_algorithm.py" \
    --start "$START_PLAN" \
    --end "$END_PLAN" \
    --input "$BASELINE_DIR" \
    --output "$FRA_DIR"

echo "[STAGE 2 DONE]"

# ----------------------------------
# OPTIONAL: ANALYSIS (CAN DISABLE)
# ----------------------------------
if [ "${RUN_ANALYSIS:-0}" = "1" ]; then
    echo "[STAGE 3] Analysis"

    python "$SCRIPTS_DIR/analyze_baseline_and_compare.py" \
        --input "$FRA_DIR" \
        --output "$ANALYSIS_DIR"

    echo "[STAGE 3 DONE]"
fi

echo "========================================"
echo "FRA JOB END"
echo "Time: $(date)"
echo "========================================"