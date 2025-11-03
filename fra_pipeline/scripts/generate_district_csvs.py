#!/usr/bin/env python3
"""
Generate District-Level CSV Files

Reads plan assignments and creates district-level CSV files
showing vote totals, population, and winners for each district.
"""

import json
import pandas as pd
import geopandas as gpd
from pathlib import Path


def generate_district_csvs():
    """Generate district-level CSV files for all plans."""

    print("=" * 60)
    print("📊 GENERATING DISTRICT-LEVEL CSV FILES")
    print("=" * 60)

    # Determine paths
    base_dir = Path(__file__).parent.parent

    # Find shapefile
    possible_shp_paths = [
        base_dir / "data" / "NC_VTD" / "NC_VTD.shp",
        base_dir.parent / "data" / "NC-shapefiles" / "NC_VTD" / "NC_VTD.shp",
    ]

    shp_path = None
    for path in possible_shp_paths:
        if path.exists():
            shp_path = path
            break

    if shp_path is None:
        print("❌ ERROR: Shapefile not found")
        return False

    plans_dir = base_dir / "outputs" / "plan_assignments"
    output_dir = base_dir / "outputs"

    # Load shapefile
    print(f"\n📂 Loading shapefile from: {shp_path}")
    gdf = gpd.read_file(shp_path)
    print(f"✅ Loaded {len(gdf)} precincts")

    # Get list of plan files
    plan_files = sorted(plans_dir.glob("plan_*.json"))
    print(f"\n🗂️  Found {len(plan_files)} plan assignment files")

    # Process each plan
    for plan_file in plan_files:
        plan_id = int(plan_file.stem.split('_')[1])

        print(f"\n   Processing Plan {plan_id}...")

        # Load assignment
        with open(plan_file, 'r') as f:
            assignment = json.load(f)

        # Convert keys to integers
        assignment = {int(k): v for k, v in assignment.items()}

        # Create district-level aggregates
        district_results = []

        # Get unique districts
        districts = sorted(set(assignment.values()))

        for district_id in districts:
            # Get precincts in this district
            precinct_ids = [k for k, v in assignment.items() if v == district_id]

            # Filter geodataframe to these precincts
            district_precincts = gdf[gdf.index.isin(precinct_ids)]

            # Aggregate votes and population
            dem_votes = district_precincts['EL08G_GV_D'].sum()
            rep_votes = district_precincts['EL08G_GV_R'].sum()
            population = district_precincts['PL10AA_TOT'].sum()

            # Determine winner
            winner = 'Democrat' if dem_votes > rep_votes else 'Republican'

            district_results.append({
                'plan_id': plan_id,
                'district_id': district_id,
                'dem_votes': int(dem_votes),
                'rep_votes': int(rep_votes),
                'population': int(population),
                'winner': winner
            })

        # Create DataFrame and save
        district_df = pd.DataFrame(district_results)
        output_path = output_dir / f"baseline_districts_plan_{plan_id}.csv"
        district_df.to_csv(output_path, index=False)

        print(f"      ✓ Saved {len(district_df)} districts to {output_path.name}")

    print("\n" + "=" * 60)
    print("✅ All district-level CSV files generated")
    print("=" * 60)

    return True


if __name__ == "__main__":
    generate_district_csvs()
