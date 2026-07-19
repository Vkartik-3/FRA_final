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
