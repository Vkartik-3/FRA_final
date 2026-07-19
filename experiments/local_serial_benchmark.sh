#!/usr/bin/env bash
# Local (laptop) serial baseline — the missing piece for the historical "4 hours -> 18 min / 13x".
#
# Runs the SAME baseline generator serially on THIS machine and records raw `time -v` output.
# Pair the result with the cluster 10k parallel wall (median 151 s) to compute an honest speedup
# for YOUR local baseline. Because per-plan cost is linear past a ~30 s fixed overhead (see the
# scaling tests in docs/SEAWULF_EVIDENCE_REPORT.md §5), you may run 1,000 plans and extrapolate
# to 10,000 instead of sitting through the full run.
#
# Usage:
#   experiments/local_serial_benchmark.sh 1000     # 1,000-plan run (recommended, ~minutes)
#   experiments/local_serial_benchmark.sh 10000    # full 10,000-plan run (long on a laptop)
#
# Writes raw evidence to docs/evidence/local/ . Commit those files.
set -euo pipefail

N="${1:?usage: local_serial_benchmark.sh <N_plans>   (e.g. 1000 or 10000)}"
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # repo root

# Pick the project interpreter: prefer the repo venv, else whatever python3 is active.
if [ -x "fra_pipeline/env/bin/python" ]; then
  PY="fra_pipeline/env/bin/python"
else
  PY="$(command -v python3)"
fi

OUTDIR="docs/evidence/local"
mkdir -p "$OUTDIR"
RUN_OUT="/tmp/fra_local_serial_${USER:-user}_${N}"
rm -rf "$RUN_OUT"; mkdir -p "$RUN_OUT"

STAMP="$(date +%Y%m%d_%H%M%S)"
LOG="$OUTDIR/local_serial_${N}_${STAMP}.txt"

# GNU time if available (macOS: `brew install gnu-time` -> gtime), else fall back to bash `time`.
if command -v gtime >/dev/null 2>&1; then TIME=(gtime -v)
elif /usr/bin/time -v true >/dev/null 2>&1; then TIME=(/usr/bin/time -v)
else TIME=(); fi

{
  echo "ARM=local_serial"
  echo "N_PLANS=$N"
  echo "HOST=$(hostname)"
  echo "UNAME=$(uname -a)"
  echo "PYTHON=$($PY --version 2>&1)  ($PY)"
  echo "COMMIT=$(git rev-parse HEAD 2>/dev/null || echo NA)"
  echo "SHAPEFILE_SHA256=$(shasum -a 256 fra_pipeline/new_data/nc_2024_with_population.shp 2>/dev/null | awk '{print $1}')"
  echo "START_TIME=$(date +%Y-%m-%dT%H:%M:%S%z)"
  echo "----- run -----"
} | tee "$LOG"

# Time the run. Capture wall via SECONDS as a portable backup even if `time` is unavailable.
START=$SECONDS
if [ "${#TIME[@]}" -gt 0 ]; then
  "${TIME[@]}" "$PY" fra_pipeline/scripts/run_baseline_simple.py \
      --start 1 --end "$N" --output "$RUN_OUT" --seed_offset 1 2>>"$LOG"
else
  "$PY" fra_pipeline/scripts/run_baseline_simple.py \
      --start 1 --end "$N" --output "$RUN_OUT" --seed_offset 1 2>>"$LOG"
fi
WALL=$(( SECONDS - START ))

PLAN_COUNT=$(find "$RUN_OUT" -maxdepth 1 -name 'plan_*.json' | wc -l | tr -d ' ')

{
  echo "----- result -----"
  echo "END_TIME=$(date +%Y-%m-%dT%H:%M:%S%z)"
  echo "WALL_SECONDS=$WALL"
  echo "PLAN_COUNT=$PLAN_COUNT"
  echo "EXPECTED=$N"
  if [ "$PLAN_COUNT" -eq "$N" ]; then echo "STATUS=OK"; else echo "STATUS=MISMATCH"; fi
  # Honest speedup vs the measured cluster 10k parallel wall (median 151 s).
  # If N<10000, extrapolate serial to 10k: wall_10k ~= (WALL - 30) * (10000/N) + 30  (fixed ~30s).
  echo "----- derived (see LOCAL_BASELINE.md for the formula) -----"
  echo "CLUSTER_PARALLEL_10K_MEDIAN_SECONDS=151"
  if [ "$N" -eq 10000 ]; then
    echo "SPEEDUP_VS_CLUSTER_PARALLEL=$(awk "BEGIN{printf \"%.2f\", $WALL/151}")x"
  else
    EXTRAP=$(awk "BEGIN{printf \"%.0f\", ($WALL-30)*(10000/$N)+30}")
    echo "EXTRAPOLATED_10K_SERIAL_SECONDS=$EXTRAP"
    echo "EXTRAPOLATED_SPEEDUP_VS_CLUSTER_PARALLEL=$(awk "BEGIN{printf \"%.2f\", $EXTRAP/151}")x"
  fi
} | tee -a "$LOG"

echo
echo "Wrote raw evidence: $LOG"
echo "Commit it:  git add $LOG && git commit -m 'evidence: local serial baseline ($N plans)'"
