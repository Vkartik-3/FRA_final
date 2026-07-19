# Local Serial Baseline — the missing piece for the historical "13×"

## Why this exists

The resume line "4 hours → 18 minutes, 13× faster" needs a **serial baseline measured on the
original local (laptop) machine**. The SeaWulf benchmark measured a *cluster* serial baseline
(617 s for 10,000 plans) → that gives the verified **4.09×**, not 13×. The "4 hours" figure came
from a laptop and has **no raw log anywhere in the repo** — so it is currently a recollection,
not a measurement. This procedure produces the missing raw log so the claim is either **defended
with evidence** or **honestly restated**.

## What to run (on the ORIGINAL laptop)

Same repo commit, same shapefile. You do **not** have to run the full 10,000 plans — per-plan
cost is linear past a ~30 s fixed overhead (proven by the scaling tests, report §5), so 1,000
plans extrapolates reliably to 10,000.

```bash
# recommended: 1,000 plans (minutes), extrapolated to 10k automatically
experiments/local_serial_benchmark.sh 1000

# or the full run if you have time:
experiments/local_serial_benchmark.sh 10000
```

The script records host, OS, python, commit, shapefile checksum, `time -v` output, wall-clock
seconds, plan count, and a derived speedup into `docs/evidence/local/local_serial_<N>_<stamp>.txt`.

## The formula (what the script computes)

- Full run (`N=10000`): `speedup = local_serial_wall / 151` (151 s = measured cluster 10k parallel median).
- Extrapolated (`N<10000`): `serial_10k ≈ (wall − 30) × (10000 / N) + 30`, then `speedup = serial_10k / 151`.
  The 30 is the ~30 s fixed per-job overhead (shapefile load + O(N²) adjacency over 2,658 precincts).

## How to read the result

| Local serial (extrapolated to 10k) | Speedup vs 151 s cluster parallel | Verdict |
|---|---|---|
| ~2,000 s (≈33 min) | ~13× | **13× defended** — the laptop really was ~30× slower per unit than the cluster node |
| ~600–700 s | ~4× | 13× **not** supported — use the measured 4.09× instead |
| in between | that ratio | report the exact measured number, whatever it is |

Whatever comes out, **report the measured number**, not a target. If it lands near 13×, you now
have the raw log to prove it. If it doesn't, the honest, already-verified line is the 4.09×.

## After running

1. `git add docs/evidence/local/local_serial_*.txt`
2. `git commit -m "evidence: local serial baseline (<N> plans)"`
3. Tell the assistant the `WALL_SECONDS` / derived speedup line, and it will fold the result into
   `docs/SEAWULF_EVIDENCE_REPORT.md` and finalize the Bullet-1 wording + claim matrix.

## Honesty rules (same as the rest of this evidence set)

- Different machine = different baseline. Do not present the cluster 4.09× as the laptop 13×, or
  vice-versa.
- Paste raw `time -v` output; never hand-edit a number.
- If you can't locate/rerun the original laptop, the 13× stays **historical/unresolved** and the
  defensible line is 4.09×.
