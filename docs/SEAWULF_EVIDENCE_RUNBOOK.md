# SeaWulf Evidence Runbook

**Purpose:** collect the runtime evidence that is currently missing from the repo, so the
four blocked resume claims (A, D) and gaps 4, 6, 7, 11, 32, 33, 34 can move from
`BLOCKED_EXTERNAL_EVIDENCE` to `VERIFIED_BY_RUNTIME_EVIDENCE`.

This doc is **self-contained**: hand it to anyone (or another chat) with SeaWulf access.
Each step says WHAT to run, WHAT to capture, and WHERE to save it. Save every artifact under
`docs/evidence/seawulf/` in the repo and commit it. **Do not edit numbers by hand** — paste
raw tool output only. If a step can't run, write `BLOCKED: <reason>` in that artifact instead
of leaving it blank.

Project layout on SeaWulf is assumed to be a clone of this repo. `fra_pipeline/` is the
project root; scripts live in `fra_pipeline/scripts/`; the venv is `fra_pipeline/env/`.

---

## Step 0 — Confirm environment (Gap 32)

Run on a SeaWulf login node, capture stdout to `docs/evidence/seawulf/ENV.txt`:

```bash
hostname
sinfo -V                      # slurm version
scontrol show config | grep -i clustername
module avail 2>&1 | grep -iE 'python|gdal|geos|proj' | head
# activate the project env
source fra_pipeline/env/bin/activate   # OR: module load the python you actually use
python --version
python -c "import geopandas,shapely,networkx,pandas,numpy,gerrychain; \
print('geopandas',geopandas.__version__,'shapely',shapely.__version__,\
'gerrychain',gerrychain.__version__)"
python -c "import shapely; print('GEOS', shapely.geos_version)"
pip freeze > docs/evidence/seawulf/requirements_seawulf.txt
```

**Confirm:** the import line succeeds and gerrychain is the version you intend
(pip vs vendored — this repo runs the pip one; note which SeaWulf uses).

**Acceptance:** `ENV.txt` shows cluster name, slurm version, python + geo stack versions.

---

## Step 1 — Confirm the cluster capacity vs your allocation (Gaps 7, 8, D)

Capture to `docs/evidence/seawulf/CLUSTER_CAPACITY.txt`:

```bash
sinfo -o "%P %D %c %m" | head        # partitions: nodes, cores/node, mem
sinfo -s                              # summary of node states
scontrol show partition | grep -iE 'PartitionName|TotalNodes|TotalCPUs|MaxNodes'
```

**Confirm:** the total-core figure you quote (e.g. ~23,000) matches `sinfo`. Write, in plain
words at the top of the file: "cluster capacity = X cores / Y nodes; THIS PROJECT requested
and was allocated Z (see Step 4 sacct)." Capacity ≠ what you used.

---

## Step 2 — Baseline (serial) benchmark arm (Gap 6, Claim A)

Pick a fixed plan count **N** for the comparison (use the SAME N in Step 3). Record the input
shapefile checksum first:

```bash
sha256sum fra_pipeline/new_data/nc_2024_with_population.shp \
  > docs/evidence/seawulf/INPUT_CHECKSUM.txt
git rev-parse HEAD >> docs/evidence/seawulf/INPUT_CHECKSUM.txt
```

Run the serial generation on ONE node, 3 times, capture each wall-clock. The script's real
flags are `--start` / `--end` / `--output` / `--seed_offset` (there is **no** `--plans`);
`N` plans means `--start 1 --end N`. Set `N` once, e.g. `N=1000`:

```bash
N=1000   # use the SAME N in Step 3
for i in 1 2 3; do
  /usr/bin/time -v python fra_pipeline/scripts/run_baseline_simple.py \
    --start 1 --end "$N" --seed_offset 0 \
    --output /tmp/serial_run_$i \
    2> docs/evidence/seawulf/serial_time_$i.txt
done
```

Baseline-only is the cleanest speedup arm. If you want to time the **full** per-plan pipeline
(baseline + FRA gluing), also run the gluing step on the same output — its flags are
`--start` / `--end` / `--input` / `--output`:

```bash
python fra_pipeline/scripts/fra_gluing_algorithm.py \
  --start 1 --end "$N" --input /tmp/serial_run_1 --output /tmp/serial_fra_1
```

**Capture:** the three `serial_time_*.txt` files (each has Elapsed wall clock + MaxRSS).

**Confirm:** all three used the same N, same commit, same shapefile checksum, and record in
`BENCHMARK_RESULTS.json` whether the timing is baseline-only or baseline+FRA (must match the
parallel arm — the sbatch runs BOTH stages, so for a fair speedup either time both here too,
or compare only the baseline stage on both sides).

---

## Step 3 — Parallel (SLURM array) benchmark arm (Gap 6, Claim A)

Submit the array job for the SAME N plans. Save the job id:

```bash
sbatch fra_pipeline/scripts/fra_array_job.sbatch | tee docs/evidence/seawulf/array_submit.txt
# note the JobID it prints, e.g. 123456
```

Do this 3 times (or once if runtime is expensive — note repetitions honestly).
Wall clock for the parallel arm = last-task-end minus submit, taken from `sacct` in Step 4,
**not** from the requested `--time`.

**Confirm:** array covers exactly N plans (check `--array` range in the sbatch vs N).

---

## Step 4 — Accounting evidence (Gaps 4, 7, 8, 33, D)

For every JobID from Steps 2–3, capture raw `sacct` to `docs/evidence/seawulf/sacct_<JobID>.txt`:

```bash
sacct -j <JobID> \
  --format=JobID,JobName,State,ExitCode,Submit,Start,End,Elapsed,\
AllocCPUS,NNodes,NodeList,TotalCPU,CPUTime,MaxRSS \
  --units=G --parsable2 > docs/evidence/seawulf/sacct_<JobID>.txt
```

Then derive (paste the commands' output, don't hand-compute):

```bash
# distinct physical nodes actually used by the array:
sacct -j <JobID> --format=NodeList -P --noheader | tr ',' '\n' | sort -u \
  | tee docs/evidence/seawulf/distinct_nodes_<JobID>.txt | wc -l
# task states summary (how many COMPLETED vs FAILED):
sacct -j <JobID> --format=State -P --noheader | sort | uniq -c \
  > docs/evidence/seawulf/task_states_<JobID>.txt
```

**Confirm & this answers the resume claims directly:**
- **"400+ nodes"** → the `wc -l` of distinct_nodes is the honest number. If it's array
  *tasks* not nodes, say "N array tasks across M distinct nodes."
- **Elapsed / TotalCPU / MaxRSS** → real resource use for Claim D and Gap 33.
- **task_states** → COMPLETED vs FAILED counts for Claim B / Gap 4.

---

## Step 5 — Compute the speedup honestly (Gap 6, Claim A)

Fill `docs/evidence/seawulf/BENCHMARK_RESULTS.json` (this is the file the audit lists as the
only missing deliverable). Use the schema in `docs/BENCHMARK_PROTOCOL.md`:

```json
{
  "commit": "<git rev-parse HEAD>",
  "shapefile_sha256": "<from INPUT_CHECKSUM.txt>",
  "n_plans": 0,
  "stages_included": ["baseline_generation"],
  "serial_seconds": [0,0,0],
  "parallel_seconds": [0,0,0],
  "boundary": "queue-wait excluded; submit->last-task-end from sacct",
  "speedup_median": 0.0,
  "repetitions": 3,
  "hardware": {"serial": "1 node <cpu>", "parallel": "<N tasks / M nodes from sacct>"}
}
```

speedup_median = median(serial_seconds) / median(parallel_seconds).

**Confirm:** both arms same N, same commit, same shapefile. If they differ, it is NOT a valid
speedup — say so.

---

## Step 6 — Full-scale run manifest (Gaps 4, 5, Claim A scale)

If you run the real large ensemble (the "10,000+" run), capture a manifest to
`docs/evidence/seawulf/RUN_MANIFEST_full.json`:

```bash
# count actual outputs produced (adjust dir):
ls fra_pipeline/outputs/plan_assignments/plan_*.json | wc -l
ls fra_pipeline/outputs/fra/superdistrict_assignment_*.json | wc -l
```

Record: JobID, commit, target plan count, plan-id ranges, seed offsets, successful vs failed
counts (from Step 4 task_states), unique vs duplicate assignment counts, start/end/elapsed,
final combined-CSV row count. This settles whether "10,000" means yielded states, unique
plans, or tasks (Gap 5).

---

## Step 7 (optional) — Crash root cause (Gap 11, Claim B)

Only if a real failure is reproduced/found. Search logs:

```bash
grep -riE 'Traceback|Error|Killed|oom|TimeLimit' fra_pipeline/outputs/logs/ \
  > docs/evidence/seawulf/crash_grep.txt
```

Write `docs/incidents/BATCH_FAILURE_ROOT_CAUSE.md` with: the exception, the stage, why it
surfaced ~30–40 min in, what was lost, and the exact fix commit. **If no such log exists,
mark the "30–40 minute crash" claim UNSUPPORTED — do not invent it.**

---

## Deliverable checklist (save all under `docs/evidence/seawulf/`)

- [ ] `ENV.txt` (Step 0)
- [ ] `requirements_seawulf.txt` (Step 0)
- [ ] `CLUSTER_CAPACITY.txt` (Step 1)
- [ ] `INPUT_CHECKSUM.txt` (Step 2)
- [ ] `serial_time_1..3.txt` (Step 2)
- [ ] `array_submit.txt` (Step 3)
- [ ] `sacct_<JobID>.txt` for each job (Step 4)
- [ ] `distinct_nodes_<JobID>.txt`, `task_states_<JobID>.txt` (Step 4)
- [ ] `BENCHMARK_RESULTS.json` (Step 5) ← the missing audit deliverable
- [ ] `RUN_MANIFEST_full.json` (Step 6, if full run done)
- [ ] `crash_grep.txt` + `docs/incidents/BATCH_FAILURE_ROOT_CAUSE.md` (Step 7, if applicable)

## What each artifact unblocks

| Artifact | Gaps / Claims it closes |
|----------|-------------------------|
| ENV.txt, requirements_seawulf.txt | Gap 32 |
| CLUSTER_CAPACITY.txt | Gaps 7, 8; Claim D (capacity side) |
| sacct_*.txt, distinct_nodes, task_states | Gaps 4, 33; Claims A, B, D |
| BENCHMARK_RESULTS.json | Gap 6; Claim A (speedup) |
| RUN_MANIFEST_full.json | Gaps 4, 5; Claim A (scale) |
| BATCH_FAILURE_ROOT_CAUSE.md | Gap 11; Claim B (crash) |

**Golden rule:** paste raw output, never retype a number. A blocked step stays blocked in
writing. That is what makes this defensible under deep questioning.
