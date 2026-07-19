#!/usr/bin/env python3
"""
Baseline Ensemble Generator - Step 1

Generates 10 random district plans using GerryChain's ReCom algorithm,
simulates elections (winner-take-all), and saves results for dashboard visualization.
"""

import argparse
import hashlib
import json
import os
import pickle
import time
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
from tqdm import tqdm
from io_utils import atomic_write_json, atomic_write_dataframe_csv
from allocation import decide_district_winner

# Baseline single-member tie policy (Gap 19). Override via FRA_TIE_POLICY env var.
# Default "republican" preserves the original historical behavior exactly.
TIE_POLICY = os.environ.get("FRA_TIE_POLICY", "republican")


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

    # Attach election and population data.
    # Direct label-based lookup (O(1) per node) instead of boolean mask scan (O(N) per node).
    for node in graph.nodes():
        row = gdf.loc[node]
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


def create_initial_partition(graph, num_districts=14, seed=42, seed_offset=0):
    """
    Create initial contiguous partition using recursive tree partitioning.

    Args:
        graph: GerryChain Graph
        num_districts: Number of districts (default 14 for NC)
        seed: Base random seed
        seed_offset: Added to seed so each SLURM batch starts an independent chain

    Returns:
        Partition object
    """
    import random
    effective_seed = seed + seed_offset
    random.seed(effective_seed)

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


def generate_baseline_ensemble(graph, num_plans=1000, num_districts=14, seed=42,
                               start_plan=1, seed_offset=0):
    """
    Generate ensemble of random district plans using ReCom.

    Args:
        graph: GerryChain Graph
        num_plans: Number of plans to generate
        num_districts: Number of districts
        seed: Base random seed
        start_plan: Global plan ID of the first plan in this batch
        seed_offset: Added to seed for chain independence across SLURM tasks

    Returns:
        List of plan dicts with results and assignment
    """
    print(f"\n⚙️  Setting up ReCom chain to generate {num_plans} plans...")
    print(f"    seed={seed}  seed_offset={seed_offset}  effective_seed={seed + seed_offset}")

    # Create initial partition — each batch uses a distinct seed space
    initial_partition = create_initial_partition(graph, num_districts, seed, seed_offset=seed_offset)

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
    print("   (This may take 1-2 hours for 1000 plans...)")

    ensemble = []
    plan_counter = start_plan - 1  # offset so first increment = start_plan

    # Duplicate-detection state — within-batch hash set
    seen_hashes: set = set()
    duplicate_count: int = 0

    # Use tqdm progress bar
    for partition in tqdm(chain, total=num_plans, desc="Generating plans", unit="plan"):
        plan_counter += 1

        # Store partition assignment for visualization
        assignment = dict(partition.assignment)

        # ── Duplicate detection ───────────────────────────────────────────────
        # SHA-256 of the canonicalised assignment is stable across processes,
        # Python versions, and SLURM tasks, so duplicate rates can be compared
        # across batches and reported in papers/interviews.
        assignment_items = sorted((int(k), int(v)) for k, v in assignment.items())
        assignment_hash  = hashlib.sha256(
            json.dumps(assignment_items).encode()
        ).hexdigest()
        is_duplicate = assignment_hash in seen_hashes
        seen_hashes.add(assignment_hash)
        if is_duplicate:
            duplicate_count += 1

        # Calculate election results for this plan
        dem_seats = 0
        rep_seats = 0

        for district in partition.parts:
            district_dem = partition["votes_dem"][district]
            district_rep = partition["votes_rep"][district]

            # Explicit, documented tie policy (Gap 19). Default "republican"
            # reproduces the original undocumented else-branch behavior.
            winner = decide_district_winner(district_dem, district_rep,
                                            tie_policy=TIE_POLICY)
            if winner == "DEM":
                dem_seats += 1
            elif winner == "REP":
                rep_seats += 1

        dem_seat_share = dem_seats / num_districts

        results = {
            "plan_id":         plan_counter,
            "dem_seats":       dem_seats,
            "rep_seats":       rep_seats,
            "dem_seat_share":  dem_seat_share,
            "chain_id":        seed_offset,
            "is_duplicate":    is_duplicate,
            "assignment_hash": assignment_hash,   # stable SHA-256; compare across batches
        }

        # Verify assignment correctness.
        # FAIL-FAST by design: if either assertion triggers, the entire batch
        # stops immediately with a non-zero exit code.  This is intentional —
        # an invalid baseline plan must never feed downstream FRA processing.
        # Recovery: fix the underlying cause (bad shapefile, GerryChain version
        # mismatch, etc.) and rerun the failed batch range with the same
        # --start / --end / --seed_offset arguments.
        assert len(assignment) == len(graph.nodes()), \
            f"Plan {plan_counter}: Not all precincts assigned ({len(assignment)}/{len(graph.nodes())})"
        assert len(set(assignment.values())) == num_districts, \
            f"Plan {plan_counter}: Should have {num_districts} districts, found {len(set(assignment.values()))}"

        ensemble.append({
            "results": results,
            "assignment": assignment
        })

    unique_count = num_plans - duplicate_count
    print(f"\n✅ Generated {num_plans} random district plans.")
    print(f"   Unique plans:    {unique_count}")
    print(f"   Duplicate plans: {duplicate_count}  "
          f"({'%.1f' % (duplicate_count / num_plans * 100)}%)")
    print(f"✓ All plans verified: {num_plans}/{num_plans} have correct assignments")

    return ensemble, duplicate_count


def save_diagnostics(output_dir, diagnostics: dict, start_plan: int, end_plan: int) -> None:
    """Write chain diagnostics (duplicate counts, timing) to a batch-specific JSON file.

    Filename includes the plan range so concurrent SLURM array tasks each write to a
    distinct path and do not overwrite each other.  The merge step later consolidates
    these files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    diag_path = output_dir / f"chain_diagnostics_{start_plan}_{end_plan}.json"
    atomic_write_json(diag_path, diagnostics, indent=2)
    print(f"   ✓ Saved chain diagnostics: {diag_path}")


def save_results(ensemble, output_dir, plans_dir=None, start_plan=1, end_plan=None):
    """
    Save ensemble results to a batch-specific CSV, histogram, and plan assignments.

    Args:
        ensemble: List of plan dictionaries
        output_dir: Output directory path (for baseline_ensemble_<start>_<end>.csv and histogram)
        plans_dir: Directory for plan_N.json files; defaults to output_dir/plan_assignments
        start_plan: First plan ID in this batch (used for batch-specific filename)
        end_plan: Last plan ID in this batch (used for batch-specific filename)

    Filename is batch-specific so that concurrent SLURM array tasks do not overwrite
    each other's summary CSVs.  The merge step consolidates them after all tasks finish.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if end_plan is None:
        end_plan = start_plan + len(ensemble) - 1

    print(f"\n💾 Saving results to {output_dir}...")

    # Save batch-specific CSV — name includes plan range to prevent SLURM collision
    results_df = pd.DataFrame([plan["results"] for plan in ensemble])
    csv_path = output_dir / f"baseline_ensemble_{start_plan}_{end_plan}.csv"
    atomic_write_dataframe_csv(csv_path, results_df)
    print(f"   ✓ Saved summary CSV: {csv_path}")

    # Save plan assignments — use caller-supplied dir or default subdirectory
    if plans_dir is None:
        plans_dir = output_dir / "plan_assignments"
    plans_dir = Path(plans_dir)
    plans_dir.mkdir(parents=True, exist_ok=True)

    for plan in ensemble:
        plan_id = plan["results"]["plan_id"]
        assignment = plan["assignment"]

        assignment_path = plans_dir / f"plan_{plan_id}.json"
        json_assignment = {str(k): int(v) for k, v in assignment.items()}
        atomic_write_json(assignment_path, json_assignment)

    print(f"   ✓ Saved {len(ensemble)} plan assignments to {plans_dir}")

    # Generate histogram
    print("\n📈 Generating histogram...")
    plt.figure(figsize=(10, 6))
    plt.hist(results_df["dem_seat_share"], bins=10, edgecolor='black', alpha=0.7, color='steelblue')
    plt.xlabel("Democratic Seat Share", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.title(f"Baseline Ensemble: Democratic Seat Share Distribution\n({len(ensemble)} Random District Plans)", fontsize=14, fontweight='bold')
    plt.axvline(results_df["dem_seat_share"].mean(), color='red', linestyle='--',
                linewidth=2, label=f"Mean: {results_df['dem_seat_share'].mean():.3f}")
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    hist_path = output_dir / f"baseline_hist_{start_plan}_{end_plan}.png"
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

    parser = argparse.ArgumentParser(description="Baseline ensemble generator")
    parser.add_argument("--start", type=int, default=1,
                        help="First plan number to generate (1-indexed, inclusive)")
    parser.add_argument("--end", type=int, default=1000,
                        help="Last plan number to generate (inclusive)")
    parser.add_argument("--output", type=str, default=None,
                        help="Directory to write plan_N.json files (default: <base>/outputs/plan_assignments)")
    parser.add_argument("--seed_offset", type=int, default=0,
                        help="Added to base seed so each SLURM batch runs an independent chain. "
                             "Set to START_PLAN in SLURM (e.g. task covering plans 201-300 uses seed_offset=201).")
    args = parser.parse_args()

    start_plan  = args.start
    end_plan    = args.end
    num_plans   = end_plan - start_plan + 1
    seed_offset = args.seed_offset

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

    # --output overrides default plan_assignments directory
    if args.output is not None:
        plans_output_dir = Path(args.output)
    else:
        plans_output_dir = base_dir / "outputs" / "plan_assignments"

    output_dir = plans_output_dir.parent  # outputs/ — for baseline_ensemble.csv

    print(f"[INFO] Generating plans {start_plan}–{end_plan} ({num_plans} plans)")
    print(f"[INFO] seed_offset={seed_offset}  effective_seed={42 + seed_offset}")
    print(f"[INFO] Writing plan JSONs to: {plans_output_dir}")

    # ── Stage 1: Load and build graph ────────────────────────────────────────
    t0 = time.perf_counter()
    graph, gdf = load_and_build_graph(str(shp_path))
    t1 = time.perf_counter()
    graph_build_s = t1 - t0
    print(f"[TIMING] Graph build: {graph_build_s:.1f}s")

    # ── Stage 2: Generate ensemble ────────────────────────────────────────────
    t2 = time.perf_counter()
    ensemble, duplicate_count = generate_baseline_ensemble(
        graph, num_plans=num_plans, num_districts=14, seed=42,
        start_plan=start_plan, seed_offset=seed_offset
    )
    t3 = time.perf_counter()
    generation_s = t3 - t2

    # ── Stage 3: Save outputs ─────────────────────────────────────────────────
    t4 = time.perf_counter()
    save_results(ensemble, output_dir, plans_dir=plans_output_dir,
                 start_plan=start_plan, end_plan=end_plan)
    t5 = time.perf_counter()
    save_s = t5 - t4

    total_s = t5 - t0
    print(f"[TIMING] Generation:  {generation_s:.1f}s  "
          f"| Save: {save_s:.1f}s  | Total: {total_s:.1f}s")

    # ── Stage 4: Write chain diagnostics ─────────────────────────────────────
    unique_count = num_plans - duplicate_count
    diagnostics = {
        "start_plan":        start_plan,
        "end_plan":          end_plan,
        "num_plans":         num_plans,
        "unique_plans":      unique_count,
        "duplicate_count":   duplicate_count,
        "duplicate_rate":    round(duplicate_count / num_plans, 6) if num_plans else 0,
        "effective_seed":    42 + seed_offset,
        "seed_offset":       seed_offset,
        "graph_build_s":     round(graph_build_s, 2),
        "generation_s":      round(generation_s, 2),
        "save_s":            round(save_s, 2),
        "total_s":           round(total_s, 2),
    }
    save_diagnostics(output_dir, diagnostics, start_plan=start_plan, end_plan=end_plan)

    # Final verification summary
    print("\n" + "=" * 60)
    print("✅ VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"\n✓ Plans generated: {len(ensemble)}/{num_plans} ({len(ensemble)/num_plans*100:.1f}%)")
    print(f"✓ Plans verified: {len(ensemble)}/{num_plans} ({len(ensemble)/num_plans*100:.1f}%)")
    print(f"\nAll verified plans passed the following checks:")
    print(f"  • All precincts assigned to districts")
    print(f"  • Exactly 14 districts per plan")
    print(f"  • Population balance within ±5% (enforced by GerryChain)")
    print(f"  • Contiguity maintained (enforced by GerryChain)")

    print("\n" + "=" * 60)
    print("✅ Step 1 complete — Baseline ensemble generated and dashboard ready.")
    print("=" * 60)
    print(f"\n📂 Results saved to: {output_dir}")
    print(f"\n🖥️  To launch dashboard, run:")
    print(f"   streamlit run scripts/baseline_dashboard.py")
    print()


if __name__ == "__main__":
    main()
