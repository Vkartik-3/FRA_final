#!/usr/bin/env python
"""Dashboard load-time + geometry-aggregation benchmark.

Settles two open claims from docs/SEAWULF_EVIDENCE_REPORT.md:
  * dashboard ">10s -> <1s" load latency  -> measured cold vs warm here
  * "2,658 geometries -> ~50 shapes"       -> measured input rows, dissolved rows,
                                               AND exploded polygon-component count.

Run on any machine with the project env and data (no Streamlit server needed):
    python experiments/dashboard_benchmark.py --plan 1 --reps 5
Writes JSON to docs/evidence/<host>_dashboard_benchmark.json and prints a summary.
"""
from __future__ import annotations
import argparse, json, socket, statistics, time
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SHP = ROOT / "fra_pipeline" / "new_data" / "nc_2024_with_population.shp"
FRA_DIR = ROOT / "fra_pipeline" / "outputs" / "fra"


def timed(fn, *a, **k):
    t = time.perf_counter()
    out = fn(*a, **k)
    return out, time.perf_counter() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", type=int, default=1)
    ap.add_argument("--reps", type=int, default=5)
    args = ap.parse_args()

    assign_path = FRA_DIR / f"superdistrict_assignment_{args.plan}.json"
    results_path = FRA_DIR / f"fra_results_{args.plan}.csv"
    for p in (SHP, assign_path, results_path):
        if not p.exists():
            raise SystemExit(f"missing input: {p}")

    load_times, dissolve_times = [], []
    input_rows = dissolved_rows = component_count = None

    for i in range(args.reps):
        # COLD-equivalent load each rep (fresh read, no cache) — worst case the dashboard pays.
        gdf, t_load = timed(gpd.read_file, SHP)
        assignment = {int(k): v for k, v in json.loads(assign_path.read_text()).items()}
        _ = pd.read_csv(results_path)
        load_times.append(t_load)

        gdf_map = gdf.copy()
        gdf_map["superdistrict"] = gdf_map.index.map(assignment)
        dissolved, t_dis = timed(lambda g: g.dissolve(by="superdistrict", aggfunc="sum"), gdf_map)
        dissolve_times.append(t_dis)

        if i == 0:
            input_rows = len(gdf)
            dissolved_rows = len(dissolved)
            # true rendered-shape count = polygon components after exploding multipolygons
            component_count = len(dissolved.explode(index_parts=False))

    # warm-cache proxy: repeated dissolve of an already-loaded gdf (data already in memory)
    warm = []
    gdf = gpd.read_file(SHP)
    gdf["superdistrict"] = gdf.index.map(assignment)
    for _ in range(args.reps):
        _, tw = timed(lambda g: g.dissolve(by="superdistrict", aggfunc="sum"), gdf)
        warm.append(tw)

    out = {
        "host": socket.gethostname(),
        "plan": args.plan,
        "reps": args.reps,
        "geometry": {
            "input_precinct_rows": input_rows,
            "dissolved_superdistrict_rows": dissolved_rows,
            "exploded_polygon_components": component_count,
            "note": "dissolve yields dissolved_superdistrict_rows records; "
                    "exploded_polygon_components is the true count of separate polygons drawn",
        },
        "load_seconds": {
            "cold_median": round(statistics.median(load_times), 3),
            "cold_all": [round(x, 3) for x in load_times],
        },
        "dissolve_seconds": {
            "median": round(statistics.median(dissolve_times), 3),
            "all": [round(x, 3) for x in dissolve_times],
        },
        "warm_dissolve_seconds": {
            "median": round(statistics.median(warm), 3),
            "all": [round(x, 3) for x in warm],
        },
        "full_load_plus_dissolve_cold_median": round(
            statistics.median(load_times) + statistics.median(dissolve_times), 3),
    }
    dest = ROOT / "docs" / "evidence" / f"{out['host']}_dashboard_benchmark.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
