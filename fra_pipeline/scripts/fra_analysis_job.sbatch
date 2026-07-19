#!/bin/bash
# ============================================================================
# fra_analysis_job.sbatch — Stage 3: Post-run Analysis
#
# MUST run only after ALL fra_array_job tasks have completed.
# Submit with a SLURM afterok dependency:
#
#   ARRAY_JOB_ID=$(sbatch --parsable fra_array_job.sbatch)
#   sbatch --dependency=afterok:${ARRAY_JOB_ID} fra_analysis_job.sbatch
#
# This guarantees that merge, global dedup, and comparison analysis see the
# complete set of outputs rather than a partial batch.
# ============================================================================
#SBATCH --job-name=fra_analysis
#SBATCH --output=../outputs/logs/fra_analysis_%j.out
#SBATCH --error=../outputs/logs/fra_analysis_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --partition=compute

set -euo pipefail

echo "========================================"
echo "FRA ANALYSIS JOB START"
echo "Job ID: ${SLURM_JOB_ID:-N/A}"
echo "Node:   $(hostname)"
echo "Time:   $(date)"
echo "========================================"

# Gap 31: robust, submission-CWD independent path resolution.
if [ -n "${SLURM_SUBMIT_DIR:-}" ] && [ -f "${SLURM_SUBMIT_DIR}/fra_analysis_job.sbatch" ]; then
    SCRIPT_DIR="${SLURM_SUBMIT_DIR}"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
fi
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
OUTPUT_DIR="$PROJECT_ROOT/outputs"
FRA_DIR="$OUTPUT_DIR/fra"
ANALYSIS_DIR="$OUTPUT_DIR/analysis"
LOG_DIR="$OUTPUT_DIR/logs"

mkdir -p "$ANALYSIS_DIR" "$LOG_DIR"

if [ -f "$PROJECT_ROOT/env/bin/activate" ]; then
    source "$PROJECT_ROOT/env/bin/activate"
else
    echo "[ERROR] Virtual environment not found!"
    exit 1
fi

echo "[INFO] Python: $(which python)"

# ----------------------------------
# STEP 1: Merge baseline batch CSVs → combined baseline
# ----------------------------------
echo "[STEP 1] Merging baseline batch CSVs..."
python "$SCRIPTS_DIR/merge_fra_outputs.py" \
    --fra-dir     "$OUTPUT_DIR" \
    --output-file "$ANALYSIS_DIR/baseline_ensemble_combined.csv" \
    --pattern     "baseline_ensemble_*_*.csv"
echo "[STEP 1 DONE]"

# ----------------------------------
# STEP 2: Merge FRA per-plan CSVs → combined FRA
# ----------------------------------
echo "[STEP 2] Merging FRA per-plan CSVs..."
python "$SCRIPTS_DIR/merge_fra_outputs.py" \
    --fra-dir     "$FRA_DIR" \
    --output-file "$ANALYSIS_DIR/fra_ensemble_combined.csv" \
    --pattern     "fra_results_*.csv"
echo "[STEP 2 DONE]"

# ----------------------------------
# STEP 3: Merge per-batch plan-stats CSVs
# ----------------------------------
echo "[STEP 3] Merging per-batch plan-stats CSVs..."
python "$SCRIPTS_DIR/merge_fra_outputs.py" \
    --fra-dir     "$ANALYSIS_DIR" \
    --output-file "$ANALYSIS_DIR/fra_plan_stats_combined.csv" \
    --pattern     "fra_plan_stats_*_*.csv"
echo "[STEP 3 DONE]"

# ----------------------------------
# STEP 4: Merge per-batch failed-plan logs (if any)
# ----------------------------------
FAILED_PATTERN="$ANALYSIS_DIR/fra_failed_plans_*_*.csv"
if ls $FAILED_PATTERN 1>/dev/null 2>&1; then
    echo "[STEP 4] Merging failed-plan logs..."
    python "$SCRIPTS_DIR/merge_fra_outputs.py" \
        --fra-dir     "$ANALYSIS_DIR" \
        --output-file "$ANALYSIS_DIR/fra_failed_plans_combined.csv" \
        --pattern     "fra_failed_plans_*_*.csv"
    echo "[STEP 4 DONE]"
else
    echo "[STEP 4] No failed-plan logs found — all plans succeeded."
fi

# ----------------------------------
# STEP 5: Merge chain_diagnostics JSON files into a summary
# ----------------------------------
echo "[STEP 5] Collecting chain diagnostics..."
python - <<'PYEOF'
import json, os, glob, pathlib
analysis_dir = pathlib.Path(os.environ.get("ANALYSIS_DIR", "outputs/analysis"))
diag_files   = sorted(pathlib.Path(os.environ.get("OUTPUT_DIR", "outputs"))
                       .glob("chain_diagnostics_*_*.json"))
combined = [json.load(open(f)) for f in diag_files]
out = analysis_dir / "chain_diagnostics_combined.json"
json.dump(combined, open(str(out), "w"), indent=2)
print(f"[INFO] Wrote {len(combined)} batch diagnostics to {out}")
PYEOF
export ANALYSIS_DIR OUTPUT_DIR
python - <<'PYEOF2'
import json, os, glob, pathlib
analysis_dir = pathlib.Path(os.environ["ANALYSIS_DIR"])
output_dir   = pathlib.Path(os.environ["OUTPUT_DIR"])
diag_files   = sorted(output_dir.glob("chain_diagnostics_*_*.json"))
combined = [json.load(open(f)) for f in diag_files]
out = analysis_dir / "chain_diagnostics_combined.json"
json.dump(combined, open(str(out), "w"), indent=2)
total_plans = sum(d.get("num_plans", 0) for d in combined)
total_dupes = sum(d.get("duplicate_count", 0) for d in combined)
print(f"[INFO] Combined {len(combined)} batches → {total_plans} plans, "
      f"{total_dupes} within-batch duplicates")
PYEOF2
echo "[STEP 5 DONE]"

# ----------------------------------
# STEP 6: Full comparison analysis
# ----------------------------------
echo "[STEP 6] Running baseline vs FRA comparison analysis..."
python "$SCRIPTS_DIR/analyze_baseline_and_compare.py" \
    --baseline-dir "$OUTPUT_DIR" \
    --fra-combined "$ANALYSIS_DIR/fra_ensemble_combined.csv" \
    --output       "$ANALYSIS_DIR"
echo "[STEP 6 DONE]"

# ----------------------------------
# STEP 7: Output count validation
# ----------------------------------
echo "[STEP 7] Counting final outputs..."
python "$SCRIPTS_DIR/count_outputs.py" \
    --plans-dir    "$OUTPUT_DIR/plan_assignments" \
    --fra-dir      "$FRA_DIR" \
    --baseline-csv "$ANALYSIS_DIR/baseline_ensemble_combined.csv" \
    --fra-csv      "$ANALYSIS_DIR/fra_ensemble_combined.csv"
echo "[STEP 7 DONE]"

echo "========================================"
echo "FRA ANALYSIS JOB END"
echo "Time: $(date)"
echo "========================================"
