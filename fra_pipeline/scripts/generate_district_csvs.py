#!/usr/bin/env python3
"""
Generate District-Level CSV Files

Reads plan_N.json assignment files and produces one baseline_districts_plan_N.csv
per plan showing per-district vote totals, population, and winner.

Can run on any subset of plans via --start/--end, and accepts configurable
--input / --output paths so it works for both 1,000 and 10,000 plan runs
without hardcoded assumptions.

Usage:
    # All plans in default directories
    python generate_district_csvs.py

    # A specific range (e.g. SLURM batch 1–100)
    python generate_district_csvs.py --start 1 --end 100

    # Custom paths
    python generate_district_csvs.py \
        --start 1 --end 10000 \
        --input  /path/to/plan_assignments \
        --output /path/to/output_dir
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import pandas as pd


def generate_district_csvs(start_plan: int, end_plan: int,
                            plans_dir: Path, output_dir: Path,
                            shp_path: Path) -> bool:
    """
    Generate district-level CSV files for plans [start_plan, end_plan].

    Uses a single-pass groupby per plan instead of a per-district membership scan,
    reducing complexity from O(14 × N) to O(N) per plan.
    """
    print("=" * 60)
    print("GENERATING DISTRICT-LEVEL CSV FILES")
    print("=" * 60)
    print(f"  Plan range: {start_plan} – {end_plan}")
    print(f"  Input:  {plans_dir}")
    print(f"  Output: {output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load shapefile once
    print(f"\nLoading shapefile: {shp_path}")
    gdf = gpd.read_file(shp_path)
    print(f"  Loaded {len(gdf)} precincts")

    # Precompute per-precinct arrays for fast lookup
    pop_arr  = gdf["TOTPOP"].values
    dem_arr  = gdf["G24PREDHAR"].values
    rep_arr  = gdf["G24PRERTRU"].values
    idx_list = list(gdf.index)
    idx_pos  = {v: i for i, v in enumerate(idx_list)}  # precinct_id → array position

    processed = 0
    missing   = 0

    for plan_id in range(start_plan, end_plan + 1):
        plan_file = plans_dir / f"plan_{plan_id}.json"
        if not plan_file.exists():
            missing += 1
            continue

        with open(plan_file) as f:
            assignment = json.load(f)

        # Single groupby pass: accumulate votes/pop per district
        district_dem: dict = defaultdict(int)
        district_rep: dict = defaultdict(int)
        district_pop: dict = defaultdict(int)

        for k, district_id in assignment.items():
            pos = idx_pos.get(int(k))
            if pos is None:
                continue
            district_dem[district_id] += int(dem_arr[pos])
            district_rep[district_id] += int(rep_arr[pos])
            district_pop[district_id] += int(pop_arr[pos])

        rows = []
        for district_id in sorted(district_dem):
            d = district_dem[district_id]
            r = district_rep[district_id]
            rows.append({
                "plan_id":     plan_id,
                "district_id": district_id,
                "dem_votes":   d,
                "rep_votes":   r,
                "population":  district_pop[district_id],
                "winner":      "Democrat" if d > r else "Republican",
            })

        out_path = output_dir / f"baseline_districts_plan_{plan_id}.csv"
        pd.DataFrame(rows).to_csv(out_path, index=False)
        processed += 1

        if processed % 100 == 0:
            print(f"  ... {processed} plans processed")

    print(f"\nDone. Processed: {processed}  Missing input files: {missing}")
    print("=" * 60)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Generate per-plan district-level CSV files"
    )
    parser.add_argument("--start", type=int, default=None,
                        help="First plan number (inclusive). Defaults to lowest plan_*.json found.")
    parser.add_argument("--end", type=int, default=None,
                        help="Last plan number (inclusive). Defaults to highest plan_*.json found.")
    parser.add_argument("--input", type=str, default=None,
                        help="Directory containing plan_N.json files")
    parser.add_argument("--output", type=str, default=None,
                        help="Directory to write baseline_districts_plan_N.csv files")
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent

    # Resolve paths
    plans_dir  = Path(args.input)  if args.input  else base_dir / "outputs" / "plan_assignments"
    output_dir = Path(args.output) if args.output else base_dir / "outputs"

    # Resolve shapefile
    shp_candidates = [
        base_dir / "new_data" / "nc_2024_with_population.shp",
        base_dir / "data" / "NC_VTD" / "NC_VTD.shp",
        base_dir.parent / "data" / "NC-shapefiles" / "NC_VTD" / "NC_VTD.shp",
    ]
    shp_path = next((p for p in shp_candidates if p.exists()), None)
    if shp_path is None:
        print("ERROR: Shapefile not found. Tried:")
        for p in shp_candidates:
            print(f"  {p}")
        return

    # Auto-detect start/end from available plan files if not given
    if args.start is None or args.end is None:
        plan_files = sorted(plans_dir.glob("plan_*.json"))
        if not plan_files:
            print(f"ERROR: No plan_*.json files found in {plans_dir}")
            return
        ids = [int(f.stem.split("_")[1]) for f in plan_files]
        start_plan = args.start if args.start is not None else min(ids)
        end_plan   = args.end   if args.end   is not None else max(ids)
    else:
        start_plan = args.start
        end_plan   = args.end

    print(f"[INFO] Generating district CSVs for plans {start_plan}–{end_plan}")
    generate_district_csvs(start_plan, end_plan, plans_dir, output_dir, shp_path)


if __name__ == "__main__":
    main()
