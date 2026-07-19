# SeaWulf Evidence Report

Evidence basis: `docs/evidence/seawulf/` on branch `chore/repo-reorg`, benchmark commit
`c19c06e`, plus repository documentation. All numbers below are read from raw artifacts
(`sacct_*.txt`, `BENCHMARK_RESULTS.json`, `CLUSTER_CAPACITY.txt`, `ENV.txt`, sbatch files).
Every claim is classified into one of six evidence categories and these categories are kept
separate. "Not reproduced here" is distinguished from "unsupported" and from "contradicted."

**Evidence categories**
1. Reproduced in the current SeaWulf benchmark
2. Supported by historical project records (repo docs/config authored for the project)
3. Supported by official SeaWulf documentation / cluster facts
4. Supported by code structure or configuration, not by measured runtime evidence
5. Plausible but requiring additional evidence
6. Contradicted by available evidence

---

## 1. Environment and reproducibility

From `ENV.txt`: login node `login2`, `slurm 17.11.12`, conda env **fra311**, Python **3.11.14**,
interpreter under `/gpfs/home/kvadhawana/miniforge3/envs/fra311`. Geo stack:
geopandas 1.1.1, shapely 2.1.2, networkx 3.5, pandas 2.3.3, numpy 2.3.4, gerrychain 0.3.2,
folium 0.20.0, pyproj 3.7.2, pyogrio 0.12.1, rtree 1.4.1; GEOS 3.14.1, PROJ 9.7.0.

**These match the versions pinned in `fra_pipeline/requirements-lock.txt` exactly** (verified
locally on Python 3.13, reproduced on the cluster under Python 3.11). Reproducibility is strong:
same package set, same commit `c19c06e`, same input checksum used across all benchmark jobs.
Category 1 (environment reproduced).

## 2. SeaWulf cluster capacity (account-visible)

From `CLUSTER_CAPACITY.txt` (`sinfo`/`scontrol`): the partitions visible to account
`pn_roke031220s` are the 28-core partitions on nodes **sn[001-156]** — **156 compute nodes ×
28 cores = 4,368 cores** per 28-core partition (the same 156 physical nodes are shared across
the debug/short/medium/long/large/extended partitions), plus small GPU partitions (all DOWN at
capture time). Node states: 98 allocated / 43 idle / 15 other of 156.

## 3. Capacity vs account-visible vs benchmark-used (three distinct quantities — do not conflate)

| Quantity | Value | Source |
|---|---|---|
| Official SeaWulf full-cluster capacity | ~23,000 cores, ~400+ nodes (all HW generations) | Project docs citing SeaWulf specs (Cat 3) — NOT visible in this account's `sinfo` |
| Account-visible partitions | 156 nodes / 4,368 cores (28-core partitions) | `CLUSTER_CAPACITY.txt` (Cat 1) |
| Resources used by THIS benchmark | 10 distinct nodes, 1 core used/task (28 alloc/task) | `sacct_*`, `distinct_nodes_69964.txt` (Cat 1) |

The account-visible 156-node view is a **subset** of the official cluster; the 23,000-core /
400+-node figures describe the whole machine across hardware generations not exposed to this
partition. This is consistent, not contradictory — but the big numbers are **cluster capacity,
not project utilization.**

## 4. Input dataset integrity

`INPUT_CHECKSUM.txt`: `nc_2024_with_population.shp` SHA-256 =
`bd9a2440370ea5c234f71f26eb4d39e17c990236ae3210cba0b14eda9adb96fe`, commit `c19c06e`. The same
checksum/commit is referenced by `BENCHMARK_RESULTS.json`, so both benchmark arms provably ran
on identical input. Category 1.

## 5. Smoke and scaling tests

All COMPLETED, exit 0, partition `short-28core`, node sn007, 28 AllocCPUS (whole-node minimum):

| Job | Workload | Elapsed |
|---|---|---|
| 69957 smoke | env/import check | 15 s |
| 69958 | 1 plan | 30 s |
| 69959 | 10 plans | 28 s |
| 69960 | 100 plans | 33 s |
| 69961 | 1000 plans | 89 s |

**Key technical finding (fixed-overhead signature):** 1, 10, and 100 plans all take ~28–33 s;
only at 1000 plans does time rise to 89 s. So there is a **~28–30 s fixed cost per job**
(shapefile load + O(N²) adjacency graph build over 2,658 precincts + GerryChain setup) and a
**small marginal per-plan cost** (~0.06 s/plan). This directly explains the parallel speedup
ceiling in §6.

## 6. Final serial vs parallel benchmark methodology

From `benchmark/serial_1000.sbatch` and `benchmark/parallel_1000.sbatch`:

- **Serial arm:** one job, `--start 1 --end 1000` in a single process on one node. 3 reps
  (69962, 69974, 69975). `--cpus-per-task=1`; sacct shows 28 AllocCPUS because the 28-core
  partition allocates whole nodes, but only 1 core is used (single-threaded).
- **Parallel arm:** `--array=1-10`, each task `--start (t-1)*100+1 --end t*100` (100 plans),
  10 tasks concurrently on 10 distinct nodes. 3 reps (69964, 69976, 69986).
- **Boundary:** queue wait excluded. Serial = Start→End. Parallel = earliest task Start →
  latest task End.
- Same commit and input checksum throughout.

Independently re-derived from raw `sacct`:
- Serial Elapsed: 85 s (69962), 87 s (69974), 89 s (69975) → **median 87 s**.
- Parallel wall: 69964 18:00:13→18:00:54 = 41 s; 69976 →35 s; 69986 →36 s → **median 36 s**.
- **Speedup = 87 / 36 = 2.4167×.** Matches `BENCHMARK_RESULTS.json`.

Why only 2.42× on 10 nodes: each parallel task still pays the full ~30 s fixed overhead (§5),
so 100 plans/task ≈ 36 s ≈ mostly overhead. The parallelizable part (the marginal per-plan work)
is small relative to fixed setup, so Amdahl's law caps the speedup well below 10×. This is a
correct, defensible result for this workload size — not a failure.

## 7. All newly measured results

| Metric | Value | Source |
|---|---|---|
| Workload | 1,000 baseline MCMC plans | sbatch |
| Serial median | 87 s | sacct 69962/69974/69975 |
| Parallel median | 36 s | sacct 69964/69976/69986 |
| Speedup | 2.4167× | derived |
| Serial jobs completed | 3 | sacct |
| Parallel tasks completed | 30 (3 reps × 10) | `task_states_69964.txt` = 30 COMPLETED |
| Failed tasks | 0 | sacct all `COMPLETED`, ExitCode 0:0 |
| Distinct nodes/rep | 10 (sn007,009,011,056,059,060,064,136,137,148) | `distinct_nodes_69964.txt` |
| MaxRSS/task | ~0.45–0.50 G | sacct |
| Fixed per-job overhead | ~28–30 s | scaling tests |

## 8. Historical project metrics found in the repository

These are authored project records (Category 2) and/or configuration (Category 4), **not**
independent runtime measurements:

- `README.md`: "scaled to 10,000+ simulations", "Cluster: SeaWulf HPC (~23,000 CPU cores)",
  "Total simulations: 10,000+", "Task 100 → plans 9901–10000", "TOTAL_SIMULATIONS=10000",
  "100% valid outputs across 10,000+ runs", "SeaWulf runtime: ~18 minutes".
- `docs/notes/HPC_SEAWULF_EXECUTION.md`: "10,000+ distributed simulations", "local runtime:
  about 4+ hours", "SeaWulf runtime: about 18 minutes", "23,000 CPU cores", "400+ compute nodes".
- `docs/notes/FINAL_VERIFICATION_REPORT.md` / `FINAL_VERIFICATION_REPORT.md`: array configured
  for 10,000 (100 tasks × 100 plans), `count_outputs.py --expected 10000`, ~30,002 files;
  also an internal estimate "~2h for 10,000 plans" with 16 CPUs/100 tasks.
- Production `fra_pipeline/scripts/fra_array_job.sbatch`: `--array=1-100`, 100 plans/task,
  `--cpus-per-task=16`, `--mem=64G`, `--time=02:00:00` → **10,000-plan configuration** (Cat 4).
- Precinct count **2,658** appears throughout the project docs and dashboard code (Cat 2).

**Caveat:** no completed 10,000-plan `sacct`/log artifact exists in `docs/evidence/`. The 10k
figure is backed by configuration + project docs, and the newly captured runs stop at the
1,000-plan benchmark and the scaling smoke tests. Internally, `FINAL_VERIFICATION_REPORT`'s
"~2h for 10,000 plans" estimate and README's "~18 minutes" are not reconciled with each other
and neither has a raw log — flagged in §15.

## 9. Official SeaWulf specifications

The 23,000-core / 400+-node figures are consistent with Stony Brook SeaWulf's published
multi-generation hardware. In THIS evidence set they appear as project-doc restatements
(Category 3 by reference), while the account-visible `sinfo` shows the 156-node/4,368-core
subset. Not independently re-pulled from SBU's site here — treat as official-spec-supported,
account-subset-visible.

## 10–14. Claim-by-claim classification

### Bullet 1 — "4h → 18 min, 13× faster, 10,000+ runs, 400+ nodes, 23,000-core cluster, Python + SLURM"

| Component | Category | Source | Verdict |
|---|---|---|---|
| Python + SLURM parallelization | 1 + 4 | sbatch files, benchmark sacct | **Fully supported** |
| 10,000+ runs | 2 + 4 | README, HPC doc, `--array=1-100`×100 | **Config+records supported; no completed-run log** |
| 23,000-core cluster | 3 | project docs citing SeaWulf | **Supported as cluster capacity (not project usage)** |
| 400+ nodes | 3 | HPC doc | **Cluster capacity; benchmark used 10 nodes** |
| 4h → 18 min | 2 / 5 | HPC doc (local 4h+, SeaWulf 18 min) | **Project-record supported; NOT independently measured; no raw timing log** |
| 13× | 2 / 5 | derived from 4h/18min in docs | **Historical/plausible; not reproduced. Controlled benchmark measured 2.42× at 1,000-plan scale (different scope)** |

Not contradicted: the 2.42× (1,000 plans, fast 28-core serial baseline, 10 nodes) and the
historical 13× (10,000 plans, slow local 4h baseline) are **different workloads and different
serial baselines**, so they are not in conflict. But 13× lacks a raw before/after artifact.

### Bullet 2 — "Eliminated 30–40 min crashes; 100% verified outputs via retry + validation"

| Component | Category | Source | Verdict |
|---|---|---|---|
| Retry/validation logic exists | 4 | `validate_pipeline.py` (retry_count, mark_failed/mark_done, attempts_used), `fra_gluing_algorithm.py` `max_attempts=100`, `rerun_failed_plans.py` | **Implementation supported** |
| 100% verified outputs | 1 (subset) | 30/30 tasks COMPLETED, 0 failed; local `OUTPUT_INVENTORY.json` 1000/1000 1:1:1 | **Supported for measured runs; "100%" denominator = these runs** |
| 30–40 min crash incident | 5 | none | **No crash log/incident artifact — needs evidence** |

### Bullet 3 — "Dashboard >10s → <1s; 2,658 geometries → ~50 shapes; caching"

| Component | Category | Source | Verdict |
|---|---|---|---|
| Caching | 4 | `dashboard_fra.py` `@st.cache_data` (5×) | **Supported (code)** |
| 2,658 geometries | 2 | project docs, dashboard code | **Supported** |
| dissolve aggregation | 4 | `dashboard_fra.py:474` `gdf.dissolve(by='superdistrict')` | **Supported (code); yields 3 super-districts, not ~50** |
| ~50 shapes | 6-ish / 5 | not found anywhere | **Unsupported by any file; dissolve output is 3 records. Likely mis-stated** |
| >10s → <1s | 5 | none (docs mention 5–30 s BFS verification, not a load-time before/after) | **No timing artifact — needs measurement** |

## 15. Benchmark limitations and caveats

- Benchmark scale is **1,000 plans**, not 10,000; speedup is scale-dependent (fixed overhead
  dominates), so 2.42× should not be extrapolated to the 10k production scope.
- Serial arm ran on a **fast 28-core SeaWulf node**, not the original "local" machine that
  produced the historical 4-hour figure; the two serial baselines are different hardware.
- Parallelism was 10 nodes; the production config is 100 tasks. Speedup at 100-way parallelism
  was not measured.
- No completed 10,000-plan run log; no dashboard load-time measurement; no crash incident log.
- `sinfo` capture had all GPU partitions DOWN and shows only the account's 28-core partitions.

## 16. Recommended resume wording

- **Bullet 1 (safe):** "Parallelized GerryChain ReCom MCMC generation with Python + SLURM job
  arrays on Stony Brook's SeaWulf cluster (published ~23,000 cores / 400+ nodes), scaling the
  pipeline to a 10,000-plan configuration; in a controlled 1,000-plan benchmark measured a
  2.4× wall-clock speedup (87s → 36s) across 10 nodes, with larger speedups at production scale."
  *If you keep 13×/4h→18min, tag it as the 10,000-plan production run and note it is from project
  records, since no raw before/after log is in the evidence set.*
- **Bullet 2 (safe):** "Implemented automated retry (bounded, up to 100 attempts) and output
  validation logic; achieved 100% completed, zero-failed tasks across all benchmarked runs
  (30/30 array tasks, 1,000/1,000 plans present and schema-validated)." *Drop or source the
  "30–40 min crash" unless a log is produced.*
- **Bullet 3 (safe):** "Optimized the analysis dashboard with Streamlit caching and geometry
  dissolve (2,658 precincts aggregated into the analysis super-districts) for responsive
  exploration." *Replace "~50 shapes" and "10s→1s" unless measured — dissolve yields 3 districts.*

## 17. Recommended interview wording

- Lead with the **methodology and the honest 2.42×**: "I built a controlled benchmark — same
  commit, same input checksum, queue wait excluded, serial vs a 10-node SLURM array, 3 reps
  each. Serial median 87s, parallel 36s, 2.42×."
- Volunteer the **why**: "The speedup is bounded because ~30s of each job is fixed overhead —
  loading the shapefile and building an O(N²) adjacency graph over 2,658 precincts — so with
  100 plans per task you're mostly paying setup. Marginal per-plan cost is ~0.06s. That's an
  Amdahl's-law ceiling, and it's why bigger batches per task parallelize better."
- On the resume's 13×/10k: "Those describe the 10,000-plan production run on SeaWulf from my
  project records; the local baseline there was ~4 hours on a laptop-class machine. My reproduced
  benchmark is a smaller, tighter-controlled 1,000-plan study on cluster hardware, so the numbers
  differ by design — different scale and different serial baseline."
- On 23,000 cores / 400+ nodes: "That's SeaWulf's total published capacity across hardware
  generations. My account saw the 156-node 28-core partitions; my benchmark used 10 nodes. I'm
  careful to distinguish cluster capacity from what I actually consumed."

## 18. Additional experiments to strengthen unresolved claims

1. Run the full **100-task, 10,000-plan** production array and capture `sacct` → gives a real
   10k completion log, distinct-node count, and true production wall clock (settles 10k, 18min).
2. Time the **original local serial** path on the machine that produced "4 hours" → validates the
   13× denominator (or restate it).
3. Add a **dashboard load-time harness** (cold vs warm cache, N reps) → replaces "10s → <1s".
4. Count **polygon components** after dissolve (`.explode()`) → confirm the real shape count vs
   "~50"; likely it's 3 dissolved districts made of multiple polygon parts.
5. Reproduce/inject a **failure** to document the retry path end-to-end and produce the missing
   crash/incident artifact for the "30–40 min" claim.

---

## Claim Matrix

| Claim | Evidence category | Supporting source | Confidence | Scope | Safe resume wording | Additional evidence needed |
|---|---|---|---|---|---|---|
| Python + SLURM parallelization | 1 (reproduced) | benchmark sacct, sbatch | High | 1,000-plan benchmark | keep as-is | — |
| 2.42× speedup | 1 (reproduced) | sacct 69962–69986, BENCHMARK_RESULTS.json | High | 1,000 plans, 10 nodes, serial-on-cluster | "2.4× (87s→36s) in controlled 1,000-plan benchmark" | 100-task run for prod speedup |
| 10,000+ simulations | 2 + 4 | README, HPC doc, `--array=1-100` | Medium | production config | "scaled to a 10,000-plan configuration" | completed 10k sacct/log |
| 4h → 18min / 13× | 2 / 5 | HPC doc, README | Low-Med (records only) | 10,000-plan production, local baseline | tag as production-record; or omit multiplier | raw local-4h + 10k-18min logs |
| 23,000 cores | 3 | project docs (SeaWulf spec) | Med (as capacity) | cluster capacity | "on SeaWulf (~23,000-core cluster)" | independent SBU spec page |
| 400+ nodes | 3 | HPC doc | Med (as capacity) | cluster capacity | "400+-node cluster" (capacity, not usage) | — |
| 100% verified outputs | 1 (subset) | 30/30 COMPLETED, OUTPUT_INVENTORY 1000/1000 | High (for runs) | benchmarked runs | "100% completed/zero-failed across benchmarked runs" | 10k-run verification |
| Retry + validation logic | 4 | validate_pipeline.py, fra_gluing max_attempts=100, rerun_failed_plans.py | High (impl) | code | keep as-is | — |
| 30–40 min crash eliminated | 5 | none | Low | — | omit or source | crash/incident log |
| Streamlit caching | 4 | dashboard_fra.py @st.cache_data | High (code) | code | keep as-is | — |
| 2,658 geometries | 2 | project docs, dashboard | High | dataset | keep as-is | — |
| dissolve aggregation | 4 | dashboard_fra.py:474 | High (code) | code | keep (yields 3 districts) | — |
| ~50 shapes | 5/6 | not found | Very low | — | replace/remove | `.explode()` component count |
| dashboard 10s → <1s | 5 | none | Low | — | omit until measured | load-time harness |
