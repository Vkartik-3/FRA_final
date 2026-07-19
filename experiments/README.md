# SeaWulf 10,000-Plan Benchmark — Exact Run Sequence

Run this on a SeaWulf login node from a clone of this repo at `$HOME/FRA_final`.
Follow the steps in order. **Paste raw output only; never hand-edit a number.**
If a step cannot run, write `BLOCKED: <reason>` in the corresponding evidence file.

---

## 1. Verify branch and commit

```bash
cd "$HOME/FRA_final"
git fetch origin
git checkout chore/repo-reorg
git pull origin chore/repo-reorg
git rev-parse HEAD          # record this commit; it MUST match both benchmark arms
git status --porcelain      # should be clean (no uncommitted changes)
```

Record the commit hash — it goes in the summary and must be identical for the serial and
parallel arms and equal to the commit the input checksum was taken at.

## 2. Activate the environment

```bash
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate fra311
export PROJ_DATA="$CONDA_PREFIX/share/proj"
export PROJ_LIB="$CONDA_PREFIX/share/proj"
export GDAL_DATA="$CONDA_PREFIX/share/gdal"
python -c "import geopandas,shapely,gerrychain,numpy,pandas; print('env OK', gerrychain.__version__)"
```

## 3. Validate script syntax before submitting

```bash
bash -n experiments/serial_10000.sbatch
bash -n experiments/parallel_10000.sbatch
bash -n experiments/collect_10k_evidence.sh
echo "syntax OK"
```

## 4. Submit the serial arm — 3 repetitions

Each rep is one job, one node, one process, 10,000 plans. Save every returned job ID.

```bash
sbatch --export=ALL,REP=1 experiments/serial_10000.sbatch
sbatch --export=ALL,REP=2 experiments/serial_10000.sbatch
sbatch --export=ALL,REP=3 experiments/serial_10000.sbatch
```

Record the three JobIDs, e.g.:

```bash
# after each sbatch prints "Submitted batch job <ID>":
echo "SERIAL 70010 70012 70014" >> docs/evidence/seawulf/bench10k/job_ids.txt
```

## 5. Submit the parallel arm — 3 repetitions

Each rep is a 100-task array (`--array=1-100`), 100 plans/task = 10,000 plans. Save each
array JobID (the `%A`, e.g. `70011`).

```bash
sbatch --export=ALL,REP=1 experiments/parallel_10000.sbatch
sbatch --export=ALL,REP=2 experiments/parallel_10000.sbatch
sbatch --export=ALL,REP=3 experiments/parallel_10000.sbatch
# record:
echo "PARALLEL 70011 70013 70015" >> docs/evidence/seawulf/bench10k/job_ids.txt
```

## 6. Monitor the jobs

```bash
squeue -u "$USER"                         # live queue/run state
squeue -u "$USER" -t RUNNING              # only running
sacct -j <ARRAY_JOBID> --format=JobID,State,Elapsed,NodeList | head   # spot-check an array
watch -n 30 "squeue -u $USER"             # optional: refresh until empty
```

Wait until `squeue -u "$USER"` returns no benchmark jobs before collecting evidence.

## 7. Confirm every job completed successfully

For all six JobIDs (3 serial + 3 parallel):

```bash
for j in 70010 70012 70014 70011 70013 70015; do
  echo "== $j =="
  sacct -j "$j" --format=JobID,State,ExitCode --parsable2 | grep -vE '\.batch|\.extern'
done
# For each parallel array, all 100 tasks must be COMPLETED with ExitCode 0:0:
sacct -j <ARRAY_JOBID> --format=State -P --noheader | sort | uniq -c   # expect: 100 COMPLETED
```

Do not proceed if any task is FAILED, CANCELLED, TIMEOUT, or OUT_OF_MEMORY — investigate first.

## 8. Collect evidence

```bash
mkdir -p docs/evidence/seawulf/bench10k
experiments/collect_10k_evidence.sh <serial_ids_csv> <parallel_ids_csv>
# example:
experiments/collect_10k_evidence.sh 70010,70012,70014 70011,70013,70015
```

This writes raw `sacct` for every job, per-array task-state counts, distinct-node lists, and a
derived `BENCH10K_SUMMARY.json` (serial median, parallel median, speedup, completed/failed
counts, node union). The script derives numbers from raw sacct — it does not invent them.

## 9. Expected output files (under `docs/evidence/seawulf/bench10k/`)

- `sacct_serial_<jobid>.txt` × 3
- `sacct_parallel_<arrayjobid>.txt` × 3
- `task_states_<arrayjobid>.txt` × 3   (expect `100 COMPLETED` each)
- `distinct_nodes_<arrayjobid>.txt` × 3
- `BENCH10K_SUMMARY.json`  (the derived result)
- `job_ids.txt`  (the six IDs you recorded)
- plus per-job stdout/stderr under `experiments/logs/` (`serial10k_*.out/err`, `par10k_*_*.out/err`)

## 10. Benchmark boundary (what is and isn't timed)

- **Queue wait is EXCLUDED.** Timing starts at job Start, not Submit.
- **Serial wall clock** = job `Elapsed` (Start → End) for the single 10,000-plan process.
- **Parallel wall clock** = earliest array-task `Start` → latest array-task `End` across all 100
  tasks in that rep (true makespan of the distributed run), computed by the collector.
- **Speedup** = median(serial wall) / median(parallel wall) over the 3 reps.
- Same commit and same input shapefile checksum on both arms (verify against
  `docs/evidence/seawulf/INPUT_CHECKSUM.txt`).

## 11. WARNING — array tasks ≠ distinct physical nodes

`--array=1-100` submits 100 tasks, but SLURM may pack multiple tasks onto the same physical
node, and idle-node availability varies. The number of **distinct physical nodes** is whatever
`distinct_nodes_<arrayjobid>.txt` (`wc -l`) reports — it can be far fewer than 100. When
describing node usage, quote the distinct-node count, not the task count. Never claim "100 nodes"
from a 100-task array.

## 12. WARNING — scope of this benchmark

This measures **current SeaWulf serial (one node) versus SeaWulf distributed (SLURM array)**
execution at 10,000-plan scale. It is **NOT** the historical "≈4 hours on a local laptop →
≈18 minutes on SeaWulf → ~13×" comparison. That historical figure used a slow local machine as
its serial baseline; this benchmark's serial baseline is a fast 28-core SeaWulf node. Report the
measured cluster speedup as its own controlled result, and keep the historical 13× labeled
separately as a production-scale, differently-baselined, project-record claim (see
`docs/SEAWULF_EVIDENCE_REPORT.md`).

## 13. Preserve ALL raw artifacts

Keep every raw file — do not summarize-and-delete. Under `docs/evidence/seawulf/` retain:
stdout (`*.out`), stderr (`*.err`), all `sacct_*` output, the recorded job IDs (`job_ids.txt`),
per-array task-state counts, and distinct-node lists. These raw files are the evidence; the
JSON summary is only a convenience derived from them.

## 14. Final validation checklist (before committing)

- [ ] `git rev-parse HEAD` matches on both arms and equals the checksum commit
- [ ] `git status --porcelain` was clean before submission
- [ ] 3 serial JobIDs and 3 parallel array JobIDs recorded in `job_ids.txt`
- [ ] `squeue -u $USER` empty (all jobs finished)
- [ ] every serial job: State COMPLETED, ExitCode 0:0
- [ ] every parallel array: `task_states_*` shows `100 COMPLETED`, 0 failed
- [ ] each serial log prints `PLAN_COUNT=10000` and `SERIAL_10K_PASSED`
- [ ] each parallel task log prints `PLAN_COUNT=100` and `PARALLEL_10K_TASK_PASSED`
- [ ] `BENCH10K_SUMMARY.json` present with non-null speedup
- [ ] distinct-node counts recorded (and understood as ≤ task count)
- [ ] all raw `.out/.err/sacct_*` preserved under `docs/evidence/seawulf/`

Then commit the new evidence under `docs/evidence/seawulf/bench10k/` and push to
`chore/repo-reorg`.
