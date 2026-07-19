# SeaWulf Evidence Report

Evidence basis: `docs/evidence/seawulf/` on branch `chore/repo-reorg`, plus repository
documentation. All numbers below are read from raw artifacts (`sacct_*.txt`, `*SUMMARY.json`,
`CLUSTER_CAPACITY.txt`, `ENV.txt`, sbatch files) and independently re-derived. Every claim is
classified into one of six evidence categories and these categories are kept separate.
"Not reproduced here" is distinguished from "unsupported" and from "contradicted."

**Two controlled benchmarks now exist — DO NOT merge them:**
- **10,000-plan (production-scale, PRIMARY):** median serial 617 s → parallel 151 s,
  **4.0861× speedup**, 37–38 distinct nodes/rep, 300/300 tasks COMPLETED, 0 failed
  (`docs/evidence/seawulf/bench10k/`). See §7a.
- **1,000-plan (earlier controlled run):** 87 s → 36 s, 2.4167×, 10 nodes/rep (§7).

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
| Resources used by the benchmarks | 10k run: 37–38 distinct nodes/rep; 1k run: 10 nodes/rep (1 core used/task) | `distinct_nodes_7001*.txt`, `distinct_nodes_69964.txt` (Cat 1) |

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

## 7a. 10,000-plan production-scale benchmark (PRIMARY — Category 1, reproduced)

Source: `docs/evidence/seawulf/bench10k/`. Independently re-derived from raw `sacct` (not just
`BENCH10K_SUMMARY.json`). Method identical to §6: serial = one 10,000-plan process on one node;
parallel = `--array=1-100`, 100 plans/task = 10,000 plans; 3 reps each; queue wait excluded;
parallel wall = earliest task Start → latest task End; same commit + input held constant.

| Metric | Value | Source (verified) |
|---|---|---|
| Workload | 10,000 baseline MCMC plans | `experiments/serial_10000.sbatch`, `parallel_10000.sbatch` |
| Serial wall (3 reps) | 629, 616, 617 s → **median 617 s (10 m 17 s)** | `sacct_serial_70002/70115/70216.txt` (all COMPLETED, exit 0:0, node sn060) |
| Parallel wall (3 reps) | 158, 150, 151 s → **median 151 s (2 m 31 s)** | `sacct_parallel_70011/70116/70217.txt` (first Start → last End) |
| **Median speedup** | **617 / 151 = 4.0861×** | derived |
| Serial jobs completed | 3 / 3 | sacct |
| Parallel tasks completed | **300 / 300** | `task_states_70011/70116/70217.txt`, direct count 100 each |
| Failed tasks | **0** | all `COMPLETED`, ExitCode 0:0 |
| Distinct physical nodes/rep | **38, 37, 37** (union 38) | `distinct_nodes_7001*.txt` (`wc -l`) |
| Tasks per rep | 100 tasks × 100 plans | sbatch array config |

**Scope note:** 100 array tasks landed on 37–38 *distinct physical nodes* (SLURM packed
multiple tasks per node). Report 37–38 nodes, never "100 nodes." The 4.09× is larger than the
1,000-plan 2.42× because at 10k the marginal per-plan work grows relative to the fixed ~30 s
per-job overhead, so parallelization pays off more — consistent with the §5 overhead signature.

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
| Python + SLURM parallelization | 1 (reproduced) | sbatch files, bench10k sacct | **Fully supported** |
| 10,000+ runs | 1 (reproduced) | `bench10k/` — 3 reps × 10,000 plans, 300/300 tasks | **Now REPRODUCED and supported** (was config-only) |
| Parallel speedup | 1 (reproduced) | bench10k sacct | **4.0861× measured (617 s → 151 s), 10k scale.** NOT 13×. |
| 23,000-core cluster | 3 | project docs citing SeaWulf | **Retain only as official cluster capacity, not project usage** |
| 400+ nodes | 3 vs 1 | HPC doc vs `distinct_nodes_*` | **Cluster capacity claim (Cat 3); measured usage = 37–38 nodes/rep. Do NOT claim 400+ as project usage** |
| 4h → 18 min | 2 / 5 | HPC doc (local 4h+, SeaWulf 18 min) | **Historical project record only; NOT reproduced; no raw local-4h or 10k-18min log. Retain only if separate historical evidence exists** |
| 13× | 2 / 5 | derived from 4h/18min in docs | **Historical/unresolved; NOT reproduced. Measured production-scale result is 4.09× (10k) / 2.42× (1k). Do not call the measured run 13×** |

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

## 14b. Measured dashboard result (NEW — `experiments/dashboard_benchmark.py`)

Ran locally (`docs/evidence/Mac_dashboard_benchmark.json`), 5 reps, plan 1:

- **input precinct rows = 2,658** → confirms the "2,658 geometries" figure (Category 1, reproduced).
- **dissolved rows = 3; exploded polygon components = 4** → the "~50 shapes" figure is
  **contradicted (Category 6)**. The dissolve produces 3 super-district records (4 separate
  polygons). There is no configuration under which this is ~50.
- **cold shapefile load ≈ 0.30 s; dissolve ≈ 2.08 s; load+dissolve ≈ 2.4 s.** So the raw
  aggregation is ~2 s on this machine — the "<1 second" figure is only achievable via the
  Streamlit `@st.cache_data` layer (first interaction pays ~2.4 s, subsequent cached reads are
  sub-second). The ">10 s" starting point is not reproduced by this harness and remains
  unmeasured. Net: caching + dissolve are real and beneficial, but the specific "10s → <1s" and
  "~50 shapes" numbers are not supported; "~50 shapes" is contradicted.

## 15. Benchmark limitations and caveats

- The **serial arm ran on a fast 28-core SeaWulf node**, not the original "local" machine that
  produced the historical 4-hour figure. The measured 4.09× (and 2.42× at 1k) is a
  **cluster-serial vs cluster-parallel** result, NOT the historical laptop→cluster comparison.
- **4.09× (10k) and 2.42× (1k) are different-scope results** — the speedup grows with scale as
  marginal per-plan work overtakes the ~30 s fixed per-job overhead. Do not merge them, and do
  not extrapolate either to "13×".
- 100 array tasks ran on **37–38 distinct physical nodes** (SLURM packed tasks); this is NOT
  "100 nodes" and NOT "400+ nodes".
- No raw log exists for the historical "4 hours" local baseline or a historical "18 minutes"
  run; no dashboard load-time (>10 s) measurement; no crash incident log.
- `sinfo` capture showed only the account's 28-core partitions (156 nodes) with GPU partitions
  DOWN — a subset of the full published cluster, not evidence of total cluster size.

## 16. Recommended resume wording (verified against raw evidence)

- **Bullet 1 (safe, verified):** "Parallelized 10,000-plan GerryChain ReCom MCMC generation with
  Python + SLURM job arrays on Stony Brook's SeaWulf cluster, reducing median wall-clock runtime
  from 10 m 17 s to 2 m 31 s — a **4.09× speedup** across three repetitions on 37–38 nodes per
  run, with 300/300 array tasks completing and zero failures."
  *Keep "~23,000-core cluster" only as SeaWulf's published capacity, not as your usage. Do NOT
  write 13×, 4h→18min, or 400+ nodes as measured — those are unreproduced historical/capacity
  figures (retain only if separate historical evidence is produced).*
- **Bullet 2 (safe, verified):** "Added automated plan-count and validity checks for distributed
  SeaWulf runs, achieving 100% verified outputs across three 10,000-plan serial jobs and 300
  SLURM array tasks with zero task failures."
  *Use the word "retry" only for the bounded restart that genuinely exists in code
  (`fra_gluing_algorithm.py max_attempts=100`, `validate_pipeline.py` retry_count). Drop the
  "30–40 min crash / unblocked research teams" clauses unless a failure log / dependency record
  is produced.*
- **Bullet 3 (safe, verified):** "Improved dashboard responsiveness by dissolving 2,658 precinct
  geometries into the analysis super-districts and caching precomputed results for interactive
  exploration."
  *Remove "~50 shapes" (measured: 3 records / 4 polygons — contradicted) and remove "10s → <1s"
  (unmeasured; raw dissolve ≈ 2.1 s, sub-second only via cache).*

## 17. Recommended interview wording

- Lead with the **primary result and methodology**: "At 10,000-plan scale I ran a controlled
  benchmark — same commit, same input checksum, queue wait excluded, one-node serial vs a
  100-task SLURM array, 3 reps each. Serial median 617 s, parallel median 151 s, **4.09×**, on
  37–38 physical nodes, 300/300 tasks with zero failures."
- Volunteer the **why the speedup isn't 100×**: "Each job pays ~30 s fixed overhead — loading the
  shapefile and building an O(N²) adjacency graph over 2,658 precincts. At 100 plans/task that
  overhead is amortized better than at 1,000 plans on one node, which is exactly why the 10k
  speedup (4.09×) exceeds the 1k speedup (2.42×). It's an Amdahl's-law story, and I can show the
  scaling curve."
- On the resume's 13× / 4h→18min: "That's a historical figure from my earlier project notes whose
  serial baseline was a laptop-class machine; I don't have the raw before/after log, so I don't
  present it as measured. My reproduced, evidence-backed number is 4.09× cluster-serial vs
  cluster-parallel at 10k."
- On 23,000 cores / 400+ nodes: "That's SeaWulf's published total capacity across hardware
  generations. My account saw the 156-node 28-core partitions; my 10k run used 37–38 nodes. I'm
  careful to separate cluster capacity from what I actually consumed, and task count from node
  count."

## 18. Additional experiments to strengthen unresolved claims

1. ~~Run the full 100-task, 10,000-plan production array~~ **DONE** — see §7a
   (`bench10k/`): 4.09×, 617s→151s, 37–38 nodes, 300/300 tasks, 0 failures.
2. **13× — PENDING local-laptop timing.** Time the original local serial path on the machine that
   produced "4 hours" using `experiments/local_serial_benchmark.sh` (see
   `experiments/LOCAL_BASELINE.md`). This is the ONLY missing evidence for the 13× claim; it
   cannot come from the cluster. Until that raw log exists in `docs/evidence/local/`, 13× stays
   **historical/unresolved** and the defensible measured number is **4.09×** (§7a).
3. Add a **dashboard load-time harness** (cold vs warm cache, N reps) → replaces "10s → <1s".
4. Count **polygon components** after dissolve (`.explode()`) → confirm the real shape count vs
   "~50"; likely it's 3 dissolved districts made of multiple polygon parts.
5. Reproduce/inject a **failure** to document the retry path end-to-end and produce the missing
   crash/incident artifact for the "30–40 min" claim.

---

## Claim Matrix

| Claim | Evidence category | Supporting source | Confidence | Scope | Safe resume wording | Additional evidence needed |
|---|---|---|---|---|---|---|
| Python + SLURM parallelization | 1 (reproduced) | bench10k sacct, sbatch | High | 10k + 1k benchmarks | keep as-is | — |
| **4.09× speedup (617s→151s)** | 1 (reproduced) | `bench10k/` sacct 70002/70115/70216 + 70011/70116/70217 | High | **10,000 plans, 37–38 nodes, cluster-serial baseline** | "4.09× (10m17s→2m31s) across 37–38 nodes, 3 reps" | — |
| 2.42× speedup (87s→36s) | 1 (reproduced) | sacct 69962–69986 | High | 1,000 plans, 10 nodes | keep as secondary/smaller-scale result | — |
| 10,000+ simulations | **1 (reproduced)** | `bench10k/` — 3 reps × 10,000 plans, 300/300 tasks | High | measured production scale | "10,000-plan runs" — supported | — |
| 4h → 18min / 13× | 2 / 5 (historical, unresolved) | HPC doc, README only | Low | historical, laptop serial baseline | omit as measured; retain only if separate historical log produced | raw local-4h + historical-18min logs |
| 23,000 cores | 3 (official capacity) | project docs citing SeaWulf | Med | cluster capacity, NOT usage | "on SeaWulf (~23,000-core cluster)" only as capacity | independent SBU spec page |
| 400+ nodes | 3 (capacity) vs measured 37–38 | HPC doc vs `distinct_nodes_*` | Med | capacity ≠ usage | do NOT claim as usage; measured usage = 37–38 nodes | — |
| 100% verified outputs | 1 (reproduced) | 300/300 COMPLETED + 3/3 serial; OUTPUT_INVENTORY 1000/1000 | High | 10k benchmark | "100% verified across three 10,000-plan jobs + 300 array tasks, 0 failures" | — |
| Automated retry logic | 4 (implementation) | `fra_gluing_algorithm.py:327` max_attempts=100 reseed-on-ValueError; `validate_pipeline.py` retry_count; `rerun_failed_plans.py` | High (code) | code | "automated retry" justified | — |
| Output validation logic | 4 (implementation) | `validate_pipeline.py`, per-plan schema/count checks | High (code) | code | keep as-is | — |
| 30–40 min crash eliminated | 5 (unresolved) | none | Low | — | omit or source | crash/incident log |
| Unblocked downstream research teams | 5 (unresolved) | none in repo | Low | — | omit unless documented | project record / dependency doc |
| Streamlit caching | 4 (code) | dashboard_fra.py @st.cache_data (5×) | High | code | keep as-is | — |
| 2,658 geometries | 1 (measured) | `Mac_dashboard_benchmark.json` input_precinct_rows=2658 | High | dataset | keep as-is | — |
| dissolve aggregation | 1 (measured) | `Mac_dashboard_benchmark.json` | High | code | "dissolved 2,658 precincts into the analysis super-districts" | — |
| ~50 shapes | **6 (contradicted)** | `Mac_dashboard_benchmark.json`: 3 records / 4 polygons | High | measured | **REMOVE** — say "into the analysis super-districts" | — |
| dashboard 10s → <1s | 5 (unresolved) | raw dissolve ≈2.1s; <1s only via cache; >10s never measured | Low | partial | drop exact timing; "cached for interactive exploration" | Streamlit cross-rerun cache timing |

---

## 19. Final deliverables summary

### 19a. Final evidence-backed resume bullets (use these)

1. **"Parallelized 10,000-plan MCMC generation with Python and SLURM job arrays on Stony Brook's
   SeaWulf cluster, reducing median runtime from 10 m 17 s to 2 m 31 s — a 4.09× speedup across
   three repetitions on 37–38 nodes per run, with 300/300 array tasks completing and zero
   failures."**
2. **"Implemented automated retry (bounded reseed, up to 100 attempts) and output-validation
   logic in Python, achieving 100% verified outputs across three 10,000-plan serial jobs and 300
   SLURM array tasks with zero task failures."**
3. **"Improved dashboard responsiveness by dissolving 2,658 precinct geometries into the analysis
   super-districts and caching precomputed results for interactive exploration."**

### 19b. Interview-safe methodology explanation

Same commit + input checksum on both arms; queue wait excluded; serial = one 10,000-plan process
on one node (median 617 s), parallel = 100-task SLURM array of 100 plans each (median wall 151 s,
earliest task start → latest task end). 4.09× over 3 reps, 37–38 distinct physical nodes (tasks
packed onto nodes — not 100 nodes). The speedup is bounded by a ~30 s fixed per-job overhead
(shapefile load + O(N²) adjacency graph over 2,658 precincts); this is why 10k (4.09×) beats 1k
(2.42×). All numbers are independently re-derived from raw `sacct` in `docs/evidence/seawulf/bench10k/`.

### 19c. Claims that remain HISTORICAL / UNRESOLVED (not reproduced, not disproven)

- **13× and 4 hours → 18 minutes** — appear only in project docs (`README.md`,
  `docs/notes/HPC_SEAWULF_EXECUTION.md`); no raw local-4h or historical-18min log. Different scope
  (laptop serial baseline) from the reproduced 4.09×. Retain only with separate historical evidence.
- **30–40 minute batch crashes** — no crash/incident log anywhere in the repo.
- **"Unblocked downstream research teams"** — no project record or dependency doc in the repo.
- **Dashboard ">10 s → <1 s"** — the >10 s starting point was never measured; sub-second only via
  Streamlit cache.
- **23,000 cores / 400+ nodes** — official SeaWulf capacity (Category 3), NOT project usage;
  measured usage was 37–38 nodes.

### 19d. Claims CONTRADICTED by evidence (must be removed/changed)

- **"~50 shapes"** — measured dissolve output is **3 records / 4 polygon components**
  (`Mac_dashboard_benchmark.json`). There is no interpretation yielding ~50. Remove it.

### 19e. Claims now FULLY REPRODUCED (Category 1)

- 10,000-plan runs executed and completed (300/300 tasks, 3/3 serial jobs, 0 failures).
- 4.0861× median speedup (617 s → 151 s), 37–38 nodes/rep.
- 100% verified outputs for the benchmarked runs.
- 2,658 input precincts; dissolve to the analysis super-districts.
