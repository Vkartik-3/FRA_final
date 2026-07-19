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
