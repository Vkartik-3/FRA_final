# Benchmark Protocol (for the "4 hours → 18 minutes → ~13x" claim)

**Current status: UNSUPPORTED by repository evidence.** No timing artifact, job log,
or `sacct` record exists in the repo. This document specifies the protocol that would
have to be executed (and its output committed to `docs/evidence/BENCHMARK_RESULTS.json`)
before the 13x claim is defensible. Do not quote 13x until this runs.

## What must be measured

A speedup is only valid between **comparable workloads**. The claim compares:

- **Baseline arm:** single-node, serial generation of N plans (the "~4 hours" number).
- **Parallel arm:** SLURM array generation of the *same* N plans (the "18 minutes" number).

Both arms must use the same:
- commit SHA
- input shapefile (record SHA-256 checksum)
- number of plans N and chain configuration (chains, steps/chain, seed scheme)
- pipeline stages included (generation only? or generation + FRA gluing + merge?)

## Procedure

1. Record `git rev-parse HEAD` and `sha256sum` of the input shapefile.
2. Serial arm: `time python run_baseline_simple.py --plans N ...` on one node; capture
   wall-clock. Repeat ≥3 times; record each measurement.
3. Parallel arm: submit the SLURM array; derive wall-clock from `sacct` (submit→last-task-end),
   not from requested walltime. Repeat ≥3 times.
4. Define the timing boundary explicitly (does it include queue wait? env activation? I/O?).
   Exclude queue wait from compute speedup, or report both.
5. Compute speedup = median(serial) / median(parallel). Report mean/median/min/max for each arm.

## Output schema (`docs/evidence/BENCHMARK_RESULTS.json`)

```json
{
  "commit": "", "shapefile_sha256": "", "n_plans": 0, "stages_included": [],
  "serial_seconds": [], "parallel_seconds": [], "boundary": "queue-excluded wall clock",
  "speedup_median": 0.0, "repetitions": 0, "hardware": {"serial": "", "parallel": ""}
}
```

Until this file exists with real numbers, the resume wording should omit the "13x" and
"18 minutes" figures (see `docs/RESUME_TECHNICAL_CLAIM_STATUS.md`).
