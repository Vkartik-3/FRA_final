# FRA Pipeline — Master Technical Dossier

_Single consolidated file. Generated 2026-07-19 from commit a9e6dd0 (working tree)._
_Contains: gap ledger, resume-claim status, run matrix, benchmark protocol, timeline,_
_ownership evidence, and all machine-readable evidence artifacts._

---


---

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


---

# Final Technical Gap Closure Ledger

Repo: commit `a9e6dd0` (dirty). Runtime: `fra_pipeline/env` (Python 3.13).
Test runner: `fra_pipeline/env/bin/python -m unittest discover -s tests -v`.
Statuses: FIXED_IN_CODE · VERIFIED_BY_TEST · VERIFIED_BY_RUNTIME_EVIDENCE ·
DOCUMENTED_LIMITATION · BLOCKED_EXTERNAL_EVIDENCE · NOT_APPLICABLE · OPEN.

This is a live ledger updated per batch. "OPEN" = not yet started this pass.

| Gap | Title | Status | Change / Evidence |
|----|-------|--------|-------------------|
| 1  | Authoritative repo snapshot | VERIFIED_BY_RUNTIME_EVIDENCE | `docs/evidence/STARTING_REPOSITORY_STATE.json` + `FINAL_REPOSITORY_STATE.json`; compileall clean |
| 2  | FRA schema one-row-per-plan | VERIFIED_BY_RUNTIME_EVIDENCE | `analyze_fra_ensemble.load_all_fra_results` aggregates 3→1; re-run over real 1000 plans reproduces committed CSV exactly (`RUN_MANIFEST.json`); `tests/test_aggregation.py` |
| 3  | Baseline preprocessing in DAG | FIXED_IN_CODE | `fra_analysis_job.sbatch` runs merge→analyze in order; no manual intermediate creation needed |
| 4  | Completed full-run evidence | BLOCKED_EXTERNAL_EVIDENCE | No SeaWulf run artifacts; local 1000-plan run evidenced instead (`RUN_MANIFEST.json`) |
| 5  | 1k vs 10k reconciliation | DOCUMENTED_LIMITATION | `docs/RUN_MATRIX.md` — only 1000 plans materialized; 10k is SeaWulf-only/unevidenced |
| 6  | 13x benchmark protocol | BLOCKED_EXTERNAL_EVIDENCE | `docs/BENCHMARK_PROTOCOL.md` written; no timing artifact exists |
| 7  | 400+ nodes | BLOCKED_EXTERNAL_EVIDENCE | No sacct/accounting in repo |
| 8  | 23,000-core wording | DOCUMENTED_LIMITATION | `RESUME_TECHNICAL_CLAIM_STATUS.md` separates capacity vs allocation |
| 9  | 100% verified definition | VERIFIED_BY_RUNTIME_EVIDENCE (subset) | `OUTPUT_INVENTORY.json`: 1000/1000 present, 1:1:1, no orphans/missing; full per-plan contiguity check remains a documented subset |
| 10 | Retry behavior map | DOCUMENTED_LIMITATION | rerun script is manual (not auto); documented as such, not called "automatic" |
| 11 | 30–40 min crash root cause | BLOCKED_EXTERNAL_EVIDENCE | No crash log/incident record |
| 12 | Dashboard latency evidence | BLOCKED_EXTERNAL_EVIDENCE | No timing harness data; claim narrowed in resume status doc |
| 13 | 2658→~50 shapes reconciliation | DOCUMENTED_LIMITATION | Dissolve yields 3 records; "~50 shapes" unsupported — see resume status doc |
| 14 | Plan 1 provenance | DOCUMENTED_LIMITATION | Local R1 seed scheme; no mixed old/new artifacts (single 1000-plan set) |
| 15 | MCMC validity diagnostics | DOCUMENTED_LIMITATION | Wording constrained to "constrained ReCom ensemble" in resume status doc |
| 16 | "Legally valid maps" wording | DOCUMENTED_LIMITATION | Enforced constraints = contiguity+pop balance+14 districts+coverage; no VRA/compactness |
| 17 | Not actual STV | FIXED_IN_CODE | `allocation.py` + gluing comments/labels state "simplified two-party proportional, not STV"; `tests/test_allocation.py` |
| 18 | Bankers rounding boundaries | VERIFIED_BY_TEST | `allocation.allocate_two_party_seats` explicit method; boundary tests in `test_allocation.py` |
| 19 | Baseline tie policy | VERIFIED_BY_TEST | `allocation.decide_district_winner` explicit/configurable; default preserves historical; tests |
| 20 | Super-district pop balance | DOCUMENTED_LIMITATION | population per super-district present in fra_results; per-seat deviation not yet aggregated |
| 21 | Adjacency semantics | DOCUMENTED_LIMITATION | GerryChain rook graph vs Shapely `touches` in gluing; documented, not unified this pass |
| 22 | Geometry repair consistency | DOCUMENTED_LIMITATION | not unified this pass |
| 23 | R-tree adjacency equivalence | DOCUMENTED_LIMITATION | not run this pass (needs full-graph build) |
| 24 | ReCom reselect loop bound | DOCUMENTED_LIMITATION | Runtime uses pip gerrychain 0.3.2 (NOT vendored dir) — patching vendored copy is a no-op |
| 25 | Baseline checkpointing | DOCUMENTED_LIMITATION | per-plan atomic writes exist; batch-level resume documented as coarse |
| 26 | Plan failure fails SLURM task | DOCUMENTED_LIMITATION | failed-plan log written; hard nonzero-exit policy not changed this pass |
| 27 | Rerun integrated into DAG | DOCUMENTED_LIMITATION | `rerun_failed_plans.py` is a manual step, documented |
| 28 | Per-plan completion marker | DOCUMENTED_LIMITATION | both files written atomically; no separate `.complete` marker added this pass |
| 29 | Fixed .tmp collisions | VERIFIED_BY_TEST | `io_utils.py` unique-temp writes; 8 call sites refactored; `tests/test_io_utils.py` |
| 30 | Atomicity vs durability | FIXED_IN_CODE | `io_utils` fsync file+dir; durability caveat documented in module docstring |
| 31 | SLURM path resolution | FIXED_IN_CODE | both sbatch use `BASH_SOURCE`/`SLURM_SUBMIT_DIR` derived root; `bash -n` clean |
| 32 | SeaWulf env reproducibility | BLOCKED_EXTERNAL_EVIDENCE | `requirements.txt` present; cluster module stack not verifiable here |
| 33 | Concurrency/resource use | BLOCKED_EXTERNAL_EVIDENCE | No sacct |
| 34 | GPFS contention | BLOCKED_EXTERNAL_EVIDENCE | Not measured; documented as architectural risk not observation |
| 35 | Dashboards >1000 plans | FIXED_IN_CODE | `dashboard_fra.py` now globs/parses IDs (sparse + >1000); no hardcoded 1..1000 scan |
| 36 | Hardcoded personal paths | FIXED_IN_CODE | replaced with `Path(__file__).parents[1]`; `grep /Users/kartikvadhawana` → none |
| 37 | Streamlit cache invalidation | DOCUMENTED_LIMITATION | caches keyed on immutable merged artifacts; documented |
| 38 | Duplicate removal policy | DOCUMENTED_LIMITATION | baseline records is_duplicate + assignment_hash; merge drops cross-batch dups (documented) |
| 39 | Paired comparison validation | DOCUMENTED_LIMITATION | combined CSVs are unique-plan_id 1-row/plan (verified); stricter guards not added this pass |
| 40 | MCMC dependence in stats | DOCUMENTED_LIMITATION | ranges described as descriptive, not CIs, in resume status doc |
| 41 | Partisan fairness wording | DOCUMENTED_LIMITATION | reported as unsigned proportionality gap; wording constrained |
| 42 | Third-party votes | DOCUMENTED_LIMITATION | two-party denominator; documented as "two-party vote share" |
| 43 | Shapefile reproducibility | BLOCKED_EXTERNAL_EVIDENCE | raw upstream inputs not in repo; `docs/SHAPEFILE_PROVENANCE.md` exists |
| 44 | Shared mandatory loader | DOCUMENTED_LIMITATION | not consolidated this pass; existing loaders validate columns |
| 45 | Layered test suite | VERIFIED_BY_TEST | `tests/` (15 cases) run by one command; `docs/evidence/TEST_RESULTS.txt` |
| 46 | Independently executable verification | FIXED_IN_CODE | ledger + resume status cite exact commands + evidence paths |
| 47 | Final output file count | VERIFIED_BY_RUNTIME_EVIDENCE | `docs/evidence/OUTPUT_INVENTORY.json` — exact counts/sizes/missing/orphans |
| 48 | Illustrative values labeled | DOCUMENTED_LIMITATION | resume status doc flags 13x/18m/~50-shapes/10k as unsupported examples |
| 49 | Technical timeline | FIXED_IN_CODE | `docs/TECHNICAL_TIMELINE.md` from git log |
| 50 | Ownership evidence | FIXED_IN_CODE | `docs/TECHNICAL_OWNERSHIP_EVIDENCE.md`; sole git author; cluster runs UNKNOWN |

## Resume claims
See `docs/RESUME_TECHNICAL_CLAIM_STATUS.md`. Summary: A=BLOCKED, B=PARTIAL, C=PARTIAL, D=BLOCKED.


---

# Run Matrix

Every metric should trace to exactly one run. Only runs with artifacts in this
repository are listed as evidenced. SeaWulf distributed runs are listed as
CLAIMED because no job logs, `sacct`, or run manifests exist in the repository.

| Run | Env | Scale | Evidence in repo | Purpose | Status |
|-----|-----|-------|------------------|---------|--------|
| R1 local ensemble | macOS `fra_pipeline/env` | **1000 plans** | `outputs/plan_assignments/` (1000), `outputs/fra/` (1000+1000), `outputs/analysis/*_combined.csv` (1000 rows) | Baseline + FRA ensemble that backs the dashboards and analysis | **EVIDENCED** (`docs/evidence/OUTPUT_INVENTORY.json`) |
| R2 SeaWulf 10k distributed | SeaWulf SLURM array | "10,000+" claimed | none | Resume Claim A/D scale | **CLAIMED — no artifacts in repo** |
| R3 benchmark (4h vs 18m) | unknown | unknown | none | Resume Claim A speedup | **CLAIMED — no timing artifact** |
| R4 dashboard demo | local | subset of R1 | dashboards read R1 outputs | UI demonstration | EVIDENCED (uses R1 data) |

## Reconciliation of the 1,000 vs 10,000 narrative (Gap 5)

- The repository materializes exactly **1000 plans** (verified, R1). Plan IDs 1..1000,
  contiguous, no gaps, 1:1:1 correspondence between baseline assignment, FRA assignment,
  and FRA results.
- No 10,000-plan artifact exists anywhere in the working tree. The "10,000+" figure is
  attributable only to a SeaWulf run (R2) whose outputs are not in this repo.
- Therefore any metric quoted against 10,000 plans is **traceable only to R2 (unevidenced)**;
  every metric reproducible here is from **R1 (1000 plans)**.


---

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


---

# Technical Timeline

Derived from `git log` (authoritative for this repo). Resume submission date is
UNKNOWN (not in the repo) — claims cannot be classified as pre/post submission
without it; they are classified against when supporting code first appeared.

| Date | Commit | Milestone |
|------|--------|-----------|
| 2025-11-03 | e0a4595 / 4c10889 | Initial project import |
| 2025-11-06 | b0be564 / c377654 | Outputs untracked; 15-plan config |
| 2025-11-07 | 27359fd / 733356c | FRA files + FRA plans added |
| 2025-11-18 | a4f953a | Architecture/structure docs |
| 2025-12-03 | 53a1ae8 | README update |
| 2025-12-16 | 2aed2d7 | Comparison files |
| 2025-12-17 | 589b043 | Verification system + readmes |
| 2026-04-01 | a9e6dd0 | SeaWulf SLURM scripts, batching, aggregation, docs |
| 2026-07-19 | (working tree) | This audit: atomic I/O, explicit allocation/tie policies, path/dashboard fixes, tests, evidence docs |

## Resume-metric classification (against code appearance, not submission)

| Metric | First supporting code | Classification |
|--------|----------------------|----------------|
| SLURM array on SeaWulf | 2026-04-01 (a9e6dd0) | Code exists; runtime evidence absent |
| 13x / 4h→18m speedup | none | UNSUPPORTED (no benchmark artifact) |
| 10,000+ simulations | none in repo (only 1000) | UNSUPPORTED locally; SeaWulf-only |
| 100% verified outputs | validate/rerun scripts + 1:1:1 1000-plan dataset | Supported for the 1000-plan local run only |
| 400+ nodes / 23k cores | none | UNSUPPORTED (no accounting) |
| Dashboard caching/dissolve | dashboards present | Mechanism exists; timing UNSUPPORTED |

Missing historical dates (resume submission, SeaWulf job dates) are recorded as UNKNOWN
and not invented.


---

# Technical Ownership Evidence

Based only on repository-supported evidence (git authorship/history). Sole git author
across all 12 commits: `Vkartik-3 <kartikvadhwana7@gmail.com>` (`git shortlog -sne`).
Ownership of *code in the repo* is confirmed; ownership of *unlogged SeaWulf runs and
benchmarks* cannot be established from the repo and is marked UNKNOWN.

| Component | Files | Evidence | Ownership |
|-----------|-------|----------|-----------|
| Baseline ReCom generation | `run_baseline_simple.py` | git author, all commits | CONFIRMED (code) |
| FRA gluing + allocation | `fra_gluing_algorithm.py`, `allocation.py` | git author | CONFIRMED (code) |
| Ensemble analysis / aggregation | `analyze_fra_ensemble.py`, `analyze_baseline_and_compare.py` | git author | CONFIRMED (code) |
| Dashboards | `dashboard_fra.py`, `app_baseline.py`, `dashboard_comparison.py` | git author | CONFIRMED (code) |
| SLURM execution | `fra_array_job.sbatch`, `fra_analysis_job.sbatch`, `run_fra_batches.sh` | git author | CONFIRMED (code authored) |
| Atomic I/O + policy hardening + tests | `io_utils.py`, `allocation.py`, `tests/` | this audit (working tree) | CONFIRMED (code) |
| SeaWulf 10k run execution | — | none | UNKNOWN (no job logs/manifest) |
| 13x benchmark measurement | — | none | UNKNOWN (no benchmark artifact) |
| 400+ node / cluster utilization | — | none | UNKNOWN (no sacct) |

Ownership of the physical cluster runs and their measured metrics is **not inferable**
from the presence of code and remains explicitly UNKNOWN for user clarification.


---

# Appendix A — Evidence Artifacts (machine-readable)

## docs/evidence/STARTING_REPOSITORY_STATE.json
```json
{
  "captured_at": "2026-07-19",
  "git": {
    "commit": "a9e6dd0a5cfe1d1237d98911a3d368e5e4cccd65",
    "branch": "FRA",
    "dirty": true,
    "modified_tracked": [
      "fra_pipeline/scripts/analyze_baseline_and_compare.py",
      "fra_pipeline/scripts/dashboard_comparison.py",
      "fra_pipeline/scripts/fra_array_job.sbatch",
      "fra_pipeline/scripts/fra_gluing_algorithm.py",
      "fra_pipeline/scripts/generate_district_csvs.py",
      "fra_pipeline/scripts/merge_fra_outputs.py",
      "fra_pipeline/scripts/run_baseline_simple.py",
      "fra_pipeline/scripts/verify_shapefile.py"
    ],
    "untracked_notable": [
      "docs/", "fra_pipeline/scripts/benchmark_status_lookup.py",
      "fra_pipeline/scripts/count_outputs.py", "fra_pipeline/scripts/db.py",
      "fra_pipeline/scripts/fra_analysis_job.sbatch", "fra_pipeline/scripts/pipeline_status.py",
      "fra_pipeline/scripts/print_gerrychain_provenance.py", "fra_pipeline/scripts/rerun_failed_plans.py",
      "fra_pipeline/scripts/schema.sql", "fra_pipeline/scripts/validate_pipeline.py"
    ]
  },
  "environment": {
    "os": "Darwin 25.5.0 (macOS, arm64)",
    "system_python": {"version": "3.14.4", "executable": "/opt/homebrew/bin/python3", "note": "no scientific packages installed"},
    "project_venv": {
      "path": "fra_pipeline/env",
      "python": "3.13.13",
      "executable": "/Users/kartikvadhawana/Desktop/FRA/NEWFINALFRA/fra_pipeline/env/bin/python"
    },
    "packages": {
      "geopandas": "1.1.1", "shapely": "2.1.2", "networkx": "3.5",
      "pandas": "2.3.3", "numpy": "2.3.4", "matplotlib": "3.10.7",
      "streamlit": "1.50.0", "folium": "0.20.0", "gerrychain": "0.3.2"
    },
    "gerrychain_resolution": {
      "imported_from": "fra_pipeline/env/lib/python3.13/site-packages/gerrychain (pip 0.3.2)",
      "vendored_dir_present": "GerryChain/ exists in repo but is NOT the import source at runtime",
      "implication": "Patching vendored GerryChain/ has no runtime effect unless installed editable"
    }
  },
  "data_facts": {
    "dataset_scale_present": "1000 plans (NOT 10000)",
    "baseline_districts_csv_count": 1000,
    "plan_assignments_count": 1000,
    "fra_results_per_plan_csv_count": 1000,
    "superdistrict_assignment_json_count": 1000,
    "fra_results_N_csv_rows_per_plan": 3,
    "fra_ensemble_combined_csv_rows": 1000,
    "baseline_ensemble_combined_csv_rows": 1000,
    "fra_ensemble_combined_schema_ok": true,
    "seawulf_job_logs_or_sacct_present": false,
    "hardcoded_home_paths_found_in": ["fra_pipeline/scripts/app_baseline.py", "fra_pipeline/scripts/dashboard_comparison.py"]
  }
}
```

## docs/evidence/FINAL_REPOSITORY_STATE.json
```json
{
  "captured_at": "2026-07-19 FINAL",
  "git": {
    "commit": "a9e6dd0a5cfe1d1237d98911a3d368e5e4cccd65",
    "branch": "FRA",
    "dirty": true,
    "modified_tracked": [
      "fra_pipeline/scripts/analyze_baseline_and_compare.py",
      "fra_pipeline/scripts/dashboard_comparison.py",
      "fra_pipeline/scripts/fra_array_job.sbatch",
      "fra_pipeline/scripts/fra_gluing_algorithm.py",
      "fra_pipeline/scripts/generate_district_csvs.py",
      "fra_pipeline/scripts/merge_fra_outputs.py",
      "fra_pipeline/scripts/run_baseline_simple.py",
      "fra_pipeline/scripts/verify_shapefile.py"
    ],
    "untracked_notable": [
      "docs/",
      "fra_pipeline/scripts/benchmark_status_lookup.py",
      "fra_pipeline/scripts/count_outputs.py",
      "fra_pipeline/scripts/db.py",
      "fra_pipeline/scripts/fra_analysis_job.sbatch",
      "fra_pipeline/scripts/pipeline_status.py",
      "fra_pipeline/scripts/print_gerrychain_provenance.py",
      "fra_pipeline/scripts/rerun_failed_plans.py",
      "fra_pipeline/scripts/schema.sql",
      "fra_pipeline/scripts/validate_pipeline.py"
    ]
  },
  "environment": {
    "os": "Darwin 25.5.0 (macOS, arm64)",
    "system_python": {
      "version": "3.14.4",
      "executable": "/opt/homebrew/bin/python3",
      "note": "no scientific packages installed"
    },
    "project_venv": {
      "path": "fra_pipeline/env",
      "python": "3.13.13",
      "executable": "/Users/kartikvadhawana/Desktop/FRA/NEWFINALFRA/fra_pipeline/env/bin/python"
    },
    "packages": {
      "geopandas": "1.1.1",
      "shapely": "2.1.2",
      "networkx": "3.5",
      "pandas": "2.3.3",
      "numpy": "2.3.4",
      "matplotlib": "3.10.7",
      "streamlit": "1.50.0",
      "folium": "0.20.0",
      "gerrychain": "0.3.2"
    },
    "gerrychain_resolution": {
      "imported_from": "fra_pipeline/env/lib/python3.13/site-packages/gerrychain (pip 0.3.2)",
      "vendored_dir_present": "GerryChain/ exists in repo but is NOT the import source at runtime",
      "implication": "Patching vendored GerryChain/ has no runtime effect unless installed editable"
    }
  },
  "data_facts": {
    "dataset_scale_present": "1000 plans (NOT 10000)",
    "baseline_districts_csv_count": 1000,
    "plan_assignments_count": 1000,
    "fra_results_per_plan_csv_count": 1000,
    "superdistrict_assignment_json_count": 1000,
    "fra_results_N_csv_rows_per_plan": 3,
    "fra_ensemble_combined_csv_rows": 1000,
    "baseline_ensemble_combined_csv_rows": 1000,
    "fra_ensemble_combined_schema_ok": true,
    "seawulf_job_logs_or_sacct_present": false,
    "hardcoded_home_paths_found_in": [
      "fra_pipeline/scripts/app_baseline.py",
      "fra_pipeline/scripts/dashboard_comparison.py"
    ]
  },
  "changes_this_audit": {
    "new_files": [
      "fra_pipeline/scripts/io_utils.py",
      "fra_pipeline/scripts/allocation.py",
      "tests/test_io_utils.py",
      "tests/test_allocation.py",
      "tests/test_aggregation.py",
      "docs/*.md",
      "docs/evidence/*.json",
      "docs/evidence/TEST_RESULTS.txt"
    ],
    "modified": [
      "run_baseline_simple.py",
      "fra_gluing_algorithm.py",
      "merge_fra_outputs.py",
      "dashboard_fra.py",
      "app_baseline.py",
      "dashboard_comparison.py",
      "fra_array_job.sbatch",
      "fra_analysis_job.sbatch"
    ],
    "tests": "15 unittest cases, all pass",
    "compileall": "clean"
  }
}```

## docs/evidence/OUTPUT_INVENTORY.json
```json
{
  "generated": "2026-07-19",
  "dataset_scale": "local 1000-plan",
  "patterns": {
    "plan_assignments/plan_*.json": {
      "count": 1000,
      "total_bytes": 28859622,
      "min": 28670,
      "max": 29087,
      "mean": 28859.6
    },
    "fra/superdistrict_assignment_*.json": {
      "count": 1000,
      "total_bytes": 33446000,
      "min": 33446,
      "max": 33446,
      "mean": 33446.0
    },
    "fra/fra_results_*.csv": {
      "count": 1000,
      "total_bytes": 239527,
      "min": 223,
      "max": 243,
      "mean": 239.5
    },
    "baseline_districts_plan_*.csv": {
      "count": 1000,
      "total_bytes": 581408,
      "min": 552,
      "max": 596,
      "mean": 581.4
    }
  },
  "id_ranges": {
    "plan_assignments": [
      1,
      1000
    ],
    "count_plan_assignments": 1000,
    "count_fra_assignment": 1000,
    "count_fra_results": 1000
  },
  "integrity": {
    "missing_plan_ids_in_assignments": [],
    "orphan_fra_results_without_assignment": [],
    "orphan_assignment_without_results": [],
    "fra_results_missing_baseline_assignment": [],
    "tmp_remnants": []
  }
}```

## docs/evidence/RUN_MANIFEST.json
```json
{
  "run_id": "local-aggregation-verify-20260719",
  "commit": "a9e6dd0-dirty",
  "environment": "macOS fra_pipeline/env py3.13",
  "workload": "re-aggregate 1000 FRA plans (3 rows/plan) -> 1-row/plan",
  "rows_produced": 1000,
  "unique_plan_ids": 1000,
  "seats_sum_to_14_all": true,
  "matches_committed_combined_csv": true,
  "runtime_seconds": 0.34,
  "evidence_files": [
    "docs/evidence/OUTPUT_INVENTORY.json",
    "docs/evidence/RUN_MANIFEST.json"
  ]
}```

## docs/evidence/TEST_RESULTS.txt
```
# TEST RESULTS — Sun Jul 19 15:52:54 EDT 2026
# runner: fra_pipeline/env/bin/python -m unittest discover -s tests -v

test_one_row_per_plan (test_aggregation.TestFraAggregation.test_one_row_per_plan) ... ok
test_required_schema_columns (test_aggregation.TestFraAggregation.test_required_schema_columns) ... ok
test_totals_conserved (test_aggregation.TestFraAggregation.test_totals_conserved) ... ok
test_clear_winners (test_allocation.TestDistrictTiePolicy.test_clear_winners) ... ok
test_tie_default_is_republican_historical (test_allocation.TestDistrictTiePolicy.test_tie_default_is_republican_historical) ... ok
test_tie_policies (test_allocation.TestDistrictTiePolicy.test_tie_policies) ... ok
test_bad_method_raises (test_allocation.TestTwoPartyAllocation.test_bad_method_raises) ... ok
test_largest_remainder (test_allocation.TestTwoPartyAllocation.test_largest_remainder) ... ok
test_round_half_even_matches_historical (test_allocation.TestTwoPartyAllocation.test_round_half_even_matches_historical) ... ok
test_round_half_up_differs_at_boundary (test_allocation.TestTwoPartyAllocation.test_round_half_up_differs_at_boundary) ... ok
test_sum_invariant (test_allocation.TestTwoPartyAllocation.test_sum_invariant) ... ok
test_failure_leaves_no_partial_target (test_io_utils.TestAtomicWrite.test_failure_leaves_no_partial_target) ... ok
test_no_tmp_remnants (test_io_utils.TestAtomicWrite.test_no_tmp_remnants) ... ok
test_unique_temp_paths_under_concurrency (test_io_utils.TestAtomicWrite.test_unique_temp_paths_under_concurrency)
Gap 29: concurrent writers to the SAME target must not share a temp path. ... ok
test_write_json_roundtrip (test_io_utils.TestAtomicWrite.test_write_json_roundtrip) ... ok
----------------------------------------------------------------------
Ran 15 tests in 0.022s
OK

# compileall:
compileall OK
```
