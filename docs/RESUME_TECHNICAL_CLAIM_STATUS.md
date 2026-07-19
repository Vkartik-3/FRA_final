# Resume Technical Claim Status

Evidence basis: repository at commit `a9e6dd0` (dirty), local env `fra_pipeline/env`
(Python 3.13, gerrychain 0.3.2). No SeaWulf job logs, `sacct` output, or benchmark
artifacts exist anywhere in the repository. See `docs/evidence/STARTING_REPOSITORY_STATE.json`.

Status vocabulary: DEFENSIBLE / DEFENSIBLE_WITH_NARROWER_WORDING / PARTIALLY_SUPPORTED /
UNSUPPORTED / BLOCKED_EXTERNAL_EVIDENCE.

---

## Claim A — "~4 hours → 18 minutes (~13x), 10,000+ simulations via SLURM on SeaWulf"

**Status: BLOCKED_EXTERNAL_EVIDENCE (and PARTIALLY_SUPPORTED for scale).**

- No timing artifact exists in the repo. There is no `BENCHMARK_RESULTS.json`, no job log,
  no `sacct` output, and no before/after measurement. The "4 hours", "18 minutes", and "13x"
  numbers cannot be reproduced or traced to any evidence file. → the speedup claim is
  **unsupported by repository evidence** and would require the original SeaWulf accounting to defend.
- Scale: only **1000 plans** are materialized locally (`plan_assignments/` = 1000,
  `fra/` = 1000). The "10,000+" figure is not present in any local artifact. Whether 10,000
  refers to yielded MCMC states, unique plans, or SLURM tasks is undetermined from the repo.
- Safest accurate wording: *"Built a SLURM array pipeline on SeaWulf to parallelize GerryChain
  ReCom MCMC generation; measured a large runtime reduction versus single-node execution"* —
  with the exact multiplier omitted until the benchmark log is recovered.

## Claim B — "Eliminated 30–40 min batch crashes; 100% verified outputs via retry and validation"

**Status: PARTIALLY_SUPPORTED / narrower wording.**

- No crash log, stack trace, or incident record exists in the repo → the specific "30–40 minute"
  crash and its root cause are **unsupported by evidence** (see Gap 11).
- A rerun script (`rerun_failed_plans.py`) and validation script (`validate_pipeline.py`) exist
  in code, so a retry+validation mechanism is real. But "100% verified" has no defined denominator
  or generated verification artifact yet (Gap 9). 1000/1000 local plans are present, which supports
  "all present plans passed the produced outputs" but not an audited all-checks-pass claim.
- Safest wording: *"Added failed-plan rerun and output-validation scripts so batches complete with
  all expected per-plan outputs present."*

## Claim C — "Dashboard >10s → <1s by aggregating 2,658 geometries into ~50 shapes + caching"

**Status: PARTIALLY_SUPPORTED / narrower wording.**

- Caching (`st.cache_data`) and geometry dissolve are real code patterns (dashboards exist).
- No timing harness or before/after measurement exists → the ">10s → <1s" numbers are **unsupported**.
- The FRA dissolve produces **3 super-districts**, not "~50 shapes". "2,658 geometries" is plausibly
  the precinct input count but is not verified here, and "~50 shapes" is not reconciled with 3
  dissolved records (Gap 13). Do not state "~50 shapes" without polygon-component counting.
- Safest wording: *"Cached precomputed results and dissolved thousands of precinct geometries into
  the analysis districts to make the dashboard render responsively."*

## Claim D — "Parallelized across 400+ nodes on a 23,000-core cluster"

**Status: BLOCKED_EXTERNAL_EVIDENCE.**

- SeaWulf's ~23,000-core capacity is a published cluster fact, but no `sacct`/accounting artifact
  in the repo shows this project's distinct nodes, allocated CPUs, or peak concurrency.
- "400+ nodes" cannot be confirmed as physical nodes vs array tasks vs jobs vs cumulative
  allocations. Do not infer project usage from cluster capacity.
- Safest wording: *"Ran the workload as a SLURM array of N tasks on SeaWulf"* — with N filled from
  the recovered job record, and cluster capacity described separately from project allocation.
