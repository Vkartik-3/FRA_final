#!/usr/bin/env python3
"""
Baseline Ensemble Generator - Step 1

Generates 10 random district plans using GerryChain's ReCom algorithm,
simulates elections (winner-take-all), and saves results for dashboard visualization.
"""

import json
import pickle
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from gerrychain import Graph, Partition, MarkovChain
from gerrychain.constraints import contiguous, within_percent_of_ideal_population
from gerrychain.proposals import recom
from gerrychain.accept import always_accept
from gerrychain.updaters import Tally
from gerrychain.tree import recursive_tree_part
from functools import partial


def load_and_build_graph(shp_path):
    """
    Load the NC shapefile and build a GerryChain graph.

    Args:
        shp_path: Path to NC_VTD.shp

    Returns:
        Graph object with vote and population data
    """
    import geopandas as gpd

    print("=" * 60)
    print("📊 STEP 1: Baseline Ensemble Generation")
    print("=" * 60)

    print("\n📂 Loading shapefile...")
    gdf = gpd.read_file(shp_path)
    print(f"✅ Loaded {len(gdf)} precincts from shapefile.")

    # Repair invalid geometries
    print("\n🔧 Repairing invalid geometries...")
    invalid_geoms = ~gdf.geometry.is_valid
    num_invalid = invalid_geoms.sum()

    if num_invalid > 0:
        print(f"   Found {num_invalid} invalid geometries. Repairing...")
        gdf.loc[invalid_geoms, 'geometry'] = gdf.loc[invalid_geoms, 'geometry'].buffer(0)
        print(f"✅ Repaired {num_invalid} geometries.")

    # Build graph
    print("\n🔨 Building GerryChain graph...")
    graph = Graph.from_geodataframe(gdf)

    # Attach election and population data
    for node in graph.nodes():
        row = gdf.loc[gdf.index == node].iloc[0]
        graph.nodes[node]["population"] = int(row.get("TOTPOP", 0))
        graph.nodes[node]["votes_dem"] = int(row.get("G24PREDHAR", 0))
        graph.nodes[node]["votes_rep"] = int(row.get("G24PRERTRU", 0))

    total_pop = sum(graph.nodes[n]["population"] for n in graph.nodes())
    total_dem = sum(graph.nodes[n]["votes_dem"] for n in graph.nodes())
    total_rep = sum(graph.nodes[n]["votes_rep"] for n in graph.nodes())

    print(f"✅ Graph built successfully ({len(graph.nodes)} precincts).")
    print(f"   Total population: {total_pop:,}")
    print(f"   Democratic votes: {total_dem:,}")
    print(f"   Republican votes: {total_rep:,}")

    return graph, gdf


def create_initial_partition(graph, num_districts=14, seed=42):
    """
    Create initial contiguous partition using recursive tree partitioning.

    Args:
        graph: GerryChain Graph
        num_districts: Number of districts (default 14 for NC)
        seed: Random seed

    Returns:
        Partition object
    """
    import random
    random.seed(seed)

    print(f"\n🎲 Creating initial partition ({num_districts} districts)...")

    total_population = sum(graph.nodes[n]["population"] for n in graph.nodes())
    ideal_population = total_population / num_districts

    print(f"   Ideal population per district: {ideal_population:,.0f}")
    print(f"   Using recursive tree partitioning...")

    # Create contiguous initial partition
    assignment = recursive_tree_part(
        graph,
        range(num_districts),
        ideal_population,
        "population",
        0.05,  # 5% tolerance
        1
    )

    # Create partition with updaters
    partition = Partition(
        graph,
        assignment=assignment,
        updaters={
            "population": Tally("population"),
            "votes_dem": Tally("votes_dem"),
            "votes_rep": Tally("votes_rep"),
        }
    )

    print(f"✅ Initial partition created with {len(partition.parts)} districts.")

    return partition


def generate_baseline_ensemble(graph, num_plans=10, num_districts=14, seed=42):
    """
    Generate ensemble of random district plans using ReCom.

    Args:
        graph: GerryChain Graph
        num_plans: Number of plans to generate
        num_districts: Number of districts
        seed: Random seed

    Returns:
        List of (partition, results_dict) tuples
    """
    print(f"\n⚙️  Setting up ReCom chain to generate {num_plans} plans...")

    # Create initial partition
    initial_partition = create_initial_partition(graph, num_districts, seed)

    # Set up constraints
    population_constraint = within_percent_of_ideal_population(initial_partition, 0.05)

    # Set up ReCom proposal
    total_population = sum(graph.nodes[n]["population"] for n in graph.nodes())
    ideal_pop = total_population / num_districts

    proposal = partial(
        recom,
        pop_col="population",
        pop_target=ideal_pop,
        epsilon=0.05,
        node_repeats=2
    )

    # Create Markov chain
    chain = MarkovChain(
        proposal=proposal,
        constraints=[contiguous, population_constraint],
        accept=always_accept,
        initial_state=initial_partition,
        total_steps=num_plans
    )

    # Generate plans
    print(f"\n🚀 Generating {num_plans} random district plans...")
    print("   (This may take a minute...)")

    ensemble = []
    plan_counter = 0

    for partition in chain:
        plan_counter += 1

        # Calculate election results for this plan
        dem_seats = 0
        rep_seats = 0

        for district in partition.parts:
            district_dem = partition["votes_dem"][district]
            district_rep = partition["votes_rep"][district]

            if district_dem > district_rep:
                dem_seats += 1
            else:
                rep_seats += 1

        dem_seat_share = dem_seats / num_districts

        results = {
            "plan_id": plan_counter,
            "dem_seats": dem_seats,
            "rep_seats": rep_seats,
            "dem_seat_share": dem_seat_share
        }

        # Store partition assignment for visualization
        assignment = dict(partition.assignment)

        ensemble.append({
            "results": results,
            "assignment": assignment
        })

        if plan_counter % 5 == 0 or plan_counter == num_plans:
            print(f"   ✓ Generated {plan_counter}/{num_plans} plans...")

    print(f"✅ Generated 10 random district plans.")

    return ensemble


def save_results(ensemble, output_dir):
    """
    Save ensemble results to CSV, histogram, and plan assignments.

    Args:
        ensemble: List of plan dictionaries
        output_dir: Output directory path
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n💾 Saving results to {output_dir}...")

    # Save CSV with summary results
    results_df = pd.DataFrame([plan["results"] for plan in ensemble])
    csv_path = output_dir / "baseline_ensemble.csv"
    results_df.to_csv(csv_path, index=False)
    print(f"   ✓ Saved summary CSV: {csv_path}")

    # Save plan assignments for dashboard
    plans_dir = output_dir / "plan_assignments"
    plans_dir.mkdir(exist_ok=True)

    for plan in ensemble:
        plan_id = plan["results"]["plan_id"]
        assignment = plan["assignment"]

        assignment_path = plans_dir / f"plan_{plan_id}.json"
        with open(assignment_path, 'w') as f:
            # Convert keys to strings for JSON
            json_assignment = {str(k): int(v) for k, v in assignment.items()}
            json.dump(json_assignment, f)

    print(f"   ✓ Saved {len(ensemble)} plan assignments to {plans_dir}")

    # Generate histogram
    print("\n📈 Generating histogram...")
    plt.figure(figsize=(10, 6))
    plt.hist(results_df["dem_seat_share"], bins=10, edgecolor='black', alpha=0.7, color='steelblue')
    plt.xlabel("Democratic Seat Share", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.title("Baseline Ensemble: Democratic Seat Share Distribution\n(10 Random District Plans)", fontsize=14, fontweight='bold')
    plt.axvline(results_df["dem_seat_share"].mean(), color='red', linestyle='--',
                linewidth=2, label=f"Mean: {results_df['dem_seat_share'].mean():.3f}")
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    hist_path = output_dir / "baseline_hist.png"
    plt.savefig(hist_path, dpi=150, bbox_inches='tight')
    print(f"   ✓ Saved histogram: {hist_path}")

    # Print summary statistics
    print(f"\n📊 Summary Statistics:")
    print(f"   Mean Democratic seat share: {results_df['dem_seat_share'].mean():.3f}")
    print(f"   Std Dev: {results_df['dem_seat_share'].std():.3f}")
    print(f"   Min: {results_df['dem_seat_share'].min():.3f}")
    print(f"   Max: {results_df['dem_seat_share'].max():.3f}")

    print("\n✅ Election simulation complete — results saved.")


def main():
    """Main execution function."""

    # Determine paths
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent

    # Try multiple possible paths for the shapefile
    possible_paths = [
        base_dir / "new_data" / "nc_2024_with_population.shp",
        base_dir / "data" / "NC_VTD" / "NC_VTD.shp",
        base_dir.parent / "data" / "NC-shapefiles" / "NC_VTD" / "NC_VTD.shp",
        Path("../data/NC-shapefiles/NC_VTD/NC_VTD.shp")
    ]

    shp_path = None
    for path in possible_paths:
        if path.exists():
            shp_path = path
            break

    if shp_path is None:
        print(f"❌ Error: Shapefile not found. Tried:")
        for path in possible_paths:
            print(f"   - {path}")
        print(f"   Please ensure NC_VTD.shp is accessible")
        return

    output_dir = base_dir / "outputs"

    # Load and build graph
    graph, gdf = load_and_build_graph(str(shp_path))

    # Generate ensemble
    ensemble = generate_baseline_ensemble(graph, num_plans=10, num_districts=14, seed=42)

    # Save results
    save_results(ensemble, output_dir)

    # Final message
    print("\n" + "=" * 60)
    print("✅ Step 1 complete — Baseline ensemble generated and dashboard ready.")
    print("=" * 60)
    print(f"\n📂 Results saved to: {output_dir}")
    print(f"\n🖥️  To launch dashboard, run:")
    print(f"   streamlit run scripts/baseline_dashboard.py")
    print()


if __name__ == "__main__":
    main()
