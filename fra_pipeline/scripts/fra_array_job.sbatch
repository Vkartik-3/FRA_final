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
# PATH SETUP (Gap 31: robust, submission-CWD independent)
# ----------------------------------
# Resolve the scripts dir from the script's own location, with a fallback to
# $SLURM_SUBMIT_DIR, so the job works when submitted from any directory.
if [ -n "${SLURM_SUBMIT_DIR:-}" ] && [ -f "${SLURM_SUBMIT_DIR}/fra_array_job.sbatch" ]; then
    SCRIPT_DIR="${SLURM_SUBMIT_DIR}"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
fi
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"   # fra_pipeline/
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
    --output "$BASELINE_DIR" \
    --seed_offset "$START_PLAN"

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
# STAGE 3: ANALYSIS — runs in a SEPARATE job after all array tasks finish.
# Do NOT run analysis inside individual array tasks: each task only sees its
# own batch, so running it here produces incomplete/misleading results.
#
# Submit the analysis job with an afterok dependency:
#
#   ARRAY_JOB_ID=$(sbatch --parsable fra_array_job.sbatch)
#   sbatch --dependency=afterok:${ARRAY_JOB_ID} fra_analysis_job.sbatch
#
# See fra_analysis_job.sbatch for the full merge + compare workflow.
# ----------------------------------
echo "[INFO] Stage 3 deferred to fra_analysis_job.sbatch (runs after all tasks complete)"

echo "========================================"
echo "FRA JOB END"
echo "Time: $(date)"
echo "========================================"

# ----------------------------------
# RESOURCE EVIDENCE (run after job finishes)
# To collect actual CPU/memory usage from SLURM accounting:
#
#   sacct -j ${SLURM_JOB_ID} \
#         --format=JobID,Elapsed,MaxRSS,AllocCPUS,State,ExitCode \
#         --units=G
#
# This prints wall time, peak resident memory (GB), allocated CPUs, and exit
# code for every task in the array.  Redirect to a file to preserve evidence:
#
#   sacct -j ${SLURM_JOB_ID} \
#         --format=JobID,Elapsed,MaxRSS,AllocCPUS,State,ExitCode \
#         --units=G \
#     > "${LOG_DIR}/sacct_${SLURM_JOB_ID}.txt"
#
# Run sacct automatically after the last task.
#
# RELIABILITY NOTE: this block fires only when SLURM_ARRAY_TASK_ID equals
# SLURM_ARRAY_TASK_MAX (i.e. the final task in the array).  If that specific
# task fails or is cancelled before reaching this point, the sacct file will
# not be written.  sacct collection is therefore best-effort.
#
# Manual fallback — run this from the login node after the job completes,
# replacing JOB_ID with the numeric job ID printed by sbatch:
#
#   sacct -j JOB_ID \
#         --format=JobID,Elapsed,MaxRSS,AllocCPUS,State,ExitCode \
#         --units=G \
#     > outputs/logs/sacct_JOB_ID.txt
#
if [ "${SLURM_ARRAY_TASK_ID}" = "${SLURM_ARRAY_TASK_MAX}" ]; then
    sacct -j "${SLURM_JOB_ID}" \
          --format=JobID,Elapsed,MaxRSS,AllocCPUS,State,ExitCode \
          --units=G \
      > "${LOG_DIR}/sacct_${SLURM_JOB_ID}.txt" 2>/dev/null || true
    echo "[INFO] sacct resource summary written to ${LOG_DIR}/sacct_${SLURM_JOB_ID}.txt"
fi