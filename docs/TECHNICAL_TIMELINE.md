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
