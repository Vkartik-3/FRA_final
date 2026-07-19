#!/bin/bash
# Collect raw evidence for the 10,000-plan benchmark AFTER all jobs COMPLETE.
# Usage:
#   experiments/collect_10k_evidence.sh <serial_jobid1,...> <parallel_arrayjobid1,...>
# Example:
#   experiments/collect_10k_evidence.sh 70010,70012,70014 70011,70013,70015
#
# Writes raw sacct + derived summary under docs/evidence/seawulf/bench10k/.
# Paste raw output only; never hand-edit numbers.
set -euo pipefail
cd "$HOME/FRA_final"

SERIAL_IDS="${1:?comma-separated serial job ids}"
PARALLEL_IDS="${2:?comma-separated parallel array job ids}"
OUT="docs/evidence/seawulf/bench10k"
mkdir -p "$OUT"

FMT="JobID,JobName,State,ExitCode,Submit,Start,End,Elapsed,AllocCPUS,NNodes,NodeList,TotalCPU,CPUTime,MaxRSS"

echo "=== serial jobs ==="
for j in ${SERIAL_IDS//,/ }; do
  sacct -j "$j" --format="$FMT" --units=G --parsable2 > "$OUT/sacct_serial_$j.txt"
  echo "wrote $OUT/sacct_serial_$j.txt"
done

echo "=== parallel jobs ==="
for j in ${PARALLEL_IDS//,/ }; do
  sacct -j "$j" --format="$FMT" --units=G --parsable2 > "$OUT/sacct_parallel_$j.txt"
  sacct -j "$j" --format=State -P --noheader | sort | uniq -c > "$OUT/task_states_$j.txt"
  sacct -j "$j" --format=NodeList -P --noheader | tr ',' '\n' | grep -E '^[a-z]' | sort -u > "$OUT/distinct_nodes_$j.txt"
  echo "wrote sacct/task_states/distinct_nodes for $j ($(wc -l < "$OUT/distinct_nodes_$j.txt") distinct nodes)"
done

# Derive per-job wall clock (Elapsed for serial; first Start -> last End for arrays) in Python.
python - "$OUT" "$SERIAL_IDS" "$PARALLEL_IDS" <<'PY'
import sys, glob, os, csv, statistics, json
from datetime import datetime
out, serial_ids, parallel_ids = sys.argv[1], sys.argv[2].split(','), sys.argv[3].split(',')
def rows(path):
    with open(path) as f:
        r = list(csv.DictReader(f, delimiter='|'))
    # keep only the top-level job/array-task rows (exclude .batch/.extern)
    return [x for x in r if '.' not in x['JobID']]
def secs(elapsed):  # HH:MM:SS or D-HH:MM:SS
    d,_,hms = elapsed.partition('-')
    if hms=='' : hms, d = d, '0'
    h,m,s = (hms.split(':')+['0','0'])[:3]
    return int(d)*86400+int(h)*3600+int(m)*60+int(s)
def dt(x): return datetime.fromisoformat(x)
serial_wall=[]
for j in serial_ids:
    for x in rows(f"{out}/sacct_serial_{j}.txt"):
        serial_wall.append(secs(x['Elapsed'])); break
par_wall=[]; failed=0; completed=0; nodes=set()
for j in parallel_ids:
    rs = rows(f"{out}/sacct_parallel_{j}.txt")
    starts=[dt(x['Start']) for x in rs if x['Start'] not in ('','Unknown')]
    ends=[dt(x['End']) for x in rs if x['End'] not in ('','Unknown')]
    if starts and ends: par_wall.append((max(ends)-min(starts)).total_seconds())
    for x in rs:
        completed += x['State']=='COMPLETED'
        failed += x['State'] not in ('COMPLETED',)
        nodes.add(x['NodeList'])
res={
 "serial_wall_seconds": serial_wall,
 "parallel_wall_seconds": par_wall,
 "serial_median": statistics.median(serial_wall) if serial_wall else None,
 "parallel_median": statistics.median(par_wall) if par_wall else None,
 "speedup_median": round(statistics.median(serial_wall)/statistics.median(par_wall),4)
    if serial_wall and par_wall else None,
 "parallel_tasks_completed": completed,
 "parallel_tasks_failed": failed,
 "distinct_nodes_union": sorted(n for n in nodes if n and n[0].isalpha()),
}
json.dump(res, open(f"{out}/BENCH10K_SUMMARY.json","w"), indent=2)
print(json.dumps(res, indent=2))
PY
echo "=== wrote $OUT/BENCH10K_SUMMARY.json ==="
