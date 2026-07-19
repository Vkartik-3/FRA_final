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
