#!/bin/bash
#SBATCH --job-name=fra_100_plans
#SBATCH --output=docs/evidence/seawulf/hundred_plans_%j.out
#SBATCH --error=docs/evidence/seawulf/hundred_plans_%j.err
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

OUTPUT_DIR="/tmp/fra_100_plan_test_$USER"
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

echo "=== JOB DETAILS ==="
echo "JOB_ID=$SLURM_JOB_ID"
echo "NODE=$(hostname)"
echo "COMMIT=$(git rev-parse HEAD)"
echo "OUTPUT_DIR=$OUTPUT_DIR"

echo
echo "=== RUN 100 BASELINE PLANS ==="

/usr/bin/time -v \
python fra_pipeline/scripts/run_baseline_simple.py \
  --start 1 \
  --end 100 \
  --output "$OUTPUT_DIR" \
  --seed_offset 1

echo
echo "=== OUTPUT VALIDATION ==="

python - <<'PY'
import json
import os
from pathlib import Path

output_dir = Path(f"/tmp/fra_100_plan_test_{os.environ['USER']}")
files = sorted(output_dir.glob("plan_*.json"))

print("plan files:", len(files))

if len(files) != 100:
    raise RuntimeError(f"Expected 100 plan files, found {len(files)}")

invalid = []

for file in files:
    with file.open() as f:
        data = json.load(f)

    if len(data) != 2658:
        invalid.append((file.name, len(data)))

print("invalid assignment counts:", invalid)

if invalid:
    raise RuntimeError(f"Invalid plan files: {invalid[:5]}")

print("all 100 plans contain 2658 assignments")
print("HUNDRED-PLAN VALIDATION PASSED")
PY

echo
echo "=== HUNDRED-PLAN TEST PASSED ==="
