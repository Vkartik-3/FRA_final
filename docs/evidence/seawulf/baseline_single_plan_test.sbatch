#!/bin/bash
#SBATCH --job-name=fra_one_plan
#SBATCH --output=docs/evidence/seawulf/one_plan_%j.out
#SBATCH --error=docs/evidence/seawulf/one_plan_%j.err
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

OUTPUT_DIR="/tmp/fra_single_plan_test_$USER"
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

echo "=== JOB DETAILS ==="
echo "JOB_ID=$SLURM_JOB_ID"
echo "NODE=$(hostname)"
echo "OUTPUT_DIR=$OUTPUT_DIR"
echo "COMMIT=$(git rev-parse HEAD)"

echo
echo "=== RUN ONE BASELINE PLAN ==="

/usr/bin/time -v \
python fra_pipeline/scripts/run_baseline_simple.py \
  --start 1 \
  --end 1 \
  --output "$OUTPUT_DIR" \
  --seed_offset 1

echo
echo "=== GENERATED FILES ==="
find "$OUTPUT_DIR" -maxdepth 1 -type f -printf '%f %s bytes\n' | sort

echo
echo "=== JSON VALIDATION ==="
python - <<'PY'
import json
import os
from pathlib import Path

output_dir = Path(f"/tmp/fra_single_plan_test_{os.environ['USER']}")
files = sorted(output_dir.glob("plan_*.json"))

print("plan files:", len(files))

if len(files) != 1:
    raise RuntimeError(f"Expected exactly 1 plan JSON, found {len(files)}")

with files[0].open() as f:
    data = json.load(f)

print("file:", files[0])
print("top-level type:", type(data).__name__)
print("top-level size:", len(data))
print("JSON VALIDATION PASSED")
PY

echo
echo "=== SINGLE PLAN TEST PASSED ==="
