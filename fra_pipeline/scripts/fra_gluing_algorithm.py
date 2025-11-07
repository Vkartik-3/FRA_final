#!/usr/bin/env python3
"""
FRA Gluing Algorithm for North Carolina (2024 Presidential Data)

This script generates FRA-style multi-member super-districts by merging
neighboring single-member districts from a baseline plan.

FRA Structure for NC (14 seats total):
- 3 super-districts with pattern: 5-5-4 seats
- Each super-district must be contiguous
- Seats allocated proportionally based on Dem/Rep vote shares

Author: Claude Code
Date: 2025
"""

import json
import pandas as pd
import geopandas as gpd
from pathlib import Path
from collections import defaultdict, deque
import random


# ============================================================================
# PART 1: LOAD DATA
# ============================================================================

def load_shapefile(shp_path):
    """
    Load the NC precinct shapefile with 2024 presidential data.

    Args:
        shp_path: Path to the shapefile

    Returns:
        GeoDataFrame with precinct geometries and vote data
    """
    print("=" * 70)
    print("FRA GLUING ALGORITHM - North Carolina 2024")
    print("=" * 70)
    print("\n[1] Loading precinct shapefile...")

    gdf = gpd.read_file(shp_path)

    # Check for required columns
    required_cols = ["TOTPOP", "G24PREDHAR", "G24PRERTRU"]
    missing = [col for col in required_cols if col not in gdf.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    print(f"    ✓ Loaded {len(gdf):,} precincts")
    print(f"    ✓ Total population: {gdf['TOTPOP'].sum():,}")
    print(f"    ✓ Democratic votes: {gdf['G24PREDHAR'].sum():,}")
    print(f"    ✓ Republican votes: {gdf['G24PRERTRU'].sum():,}")

    return gdf


def load_baseline_plan(plan_path, gdf):
    """
    Load a baseline district plan from JSON.

    Args:
        plan_path: Path to the plan JSON file (precinct_id -> district_id)
        gdf: GeoDataFrame with precinct data

    Returns:
        Dictionary mapping precinct_id to district_id
    """
    print(f"\n[2] Loading baseline district plan...")

    with open(plan_path, 'r') as f:
        assignment = json.load(f)

    # Convert string keys to integers to match GeoDataFrame index
    assignment = {int(k): int(v) for k, v in assignment.items()}

    # Verify all precincts are assigned
    num_districts = len(set(assignment.values()))

    print(f"    ✓ Loaded plan with {num_districts} districts")
    print(f"    ✓ {len(assignment):,} precincts assigned")

    return assignment


# ============================================================================
# PART 2: BUILD DISTRICT ADJACENCY GRAPH
# ============================================================================

def build_precinct_adjacency(gdf):
    """
    Build precinct-level adjacency using GeoDataFrame geometry.

    Two precincts are adjacent if they share a boundary (touch).

    Args:
        gdf: GeoDataFrame with precinct geometries

    Returns:
        Dictionary mapping precinct_id -> set of adjacent precinct_ids
    """
    print(f"\n[3] Building precinct adjacency graph...")

    # Create a spatial index for efficient neighbor finding
    # Use touches to find adjacent precincts
    adjacency = defaultdict(set)

    for idx, row in gdf.iterrows():
        # Find all precincts that touch this one
        potential_neighbors = gdf[gdf.geometry.touches(row.geometry)]

        for neighbor_idx in potential_neighbors.index:
            if neighbor_idx != idx:
                adjacency[idx].add(neighbor_idx)

    total_edges = sum(len(neighbors) for neighbors in adjacency.values()) // 2
    print(f"    ✓ Built adjacency for {len(adjacency):,} precincts")
    print(f"    ✓ Total adjacency edges: {total_edges:,}")

    return adjacency


def build_district_adjacency(precinct_adj, assignment):
    """
    Build district-level adjacency graph from precinct adjacency.

    Two districts are adjacent if ANY precinct from district A
    touches ANY precinct from district B.

    Args:
        precinct_adj: Dictionary of precinct adjacencies
        assignment: Dictionary mapping precinct_id -> district_id

    Returns:
        Dictionary mapping district_id -> set of adjacent district_ids
    """
    print(f"\n[4] Building district adjacency graph...")

    district_adj = defaultdict(set)

    # For each precinct, check its neighbors
    for precinct, neighbors in precinct_adj.items():
        my_district = assignment[precinct]

        for neighbor in neighbors:
            neighbor_district = assignment[neighbor]

            # If neighbor is in a different district, districts are adjacent
            if my_district != neighbor_district:
                district_adj[my_district].add(neighbor_district)
                district_adj[neighbor_district].add(my_district)

    num_districts = len(district_adj)
    total_edges = sum(len(neighbors) for neighbors in district_adj.values()) // 2

    print(f"    ✓ Built adjacency for {num_districts} districts")
    print(f"    ✓ District adjacency edges: {total_edges}")

    return district_adj


# ============================================================================
# PART 3: FRA GLUING ALGORITHM (5-5-4 PATTERN)
# ============================================================================

def is_connected(districts, district_adj):
    """
    Check if a set of districts forms a connected group.

    Uses breadth-first search (BFS) on the district adjacency graph.

    Args:
        districts: Set of district IDs to check
        district_adj: Dictionary of district adjacencies

    Returns:
        True if all districts are connected, False otherwise
    """
    if not districts:
        return True

    # Start BFS from any district in the set
    start = next(iter(districts))
    visited = {start}
    queue = deque([start])

    while queue:
        current = queue.popleft()

        # Check all neighbors of current district
        for neighbor in district_adj.get(current, set()):
            # Only visit neighbors that are in our district set
            if neighbor in districts and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    # If we visited all districts, they are connected
    return len(visited) == len(districts)


def can_satisfy_remaining(unused, district_adj, remaining_sizes):
    """
    Check if the remaining unused districts can satisfy the remaining target sizes.

    This is a simple heuristic check - we verify that the unused districts
    form enough connected components of appropriate sizes.

    Args:
        unused: Set of unused district IDs
        district_adj: Dictionary of district adjacencies
        remaining_sizes: List of remaining super-district sizes

    Returns:
        True if remaining sizes can potentially be satisfied
    """
    if not remaining_sizes:
        return len(unused) == 0

    # Find connected components in unused districts
    components = []
    visited = set()

    for start in unused:
        if start in visited:
            continue

        # BFS to find component
        component = {start}
        visited.add(start)
        queue = deque([start])

        while queue:
            current = queue.popleft()
            for neighbor in district_adj.get(current, set()):
                if neighbor in unused and neighbor not in visited:
                    visited.add(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)

        components.append(component)

    # Check if we can partition components into remaining sizes
    component_sizes = sorted([len(c) for c in components], reverse=True)
    required_sizes = sorted(remaining_sizes, reverse=True)

    # Simple check: total must match
    if sum(component_sizes) != sum(required_sizes):
        return False

    # For now, just check that the largest component can fit the largest requirement
    if component_sizes and required_sizes:
        if component_sizes[0] < required_sizes[0]:
            return False

    return True


def glue_districts_greedy(district_adj, target_sizes, num_districts=14, seed=42):
    """
    Glue single-member districts into FRA super-districts.

    Algorithm (improved with backtracking prevention):
    1. For each target super-district size (5, 5, 4):
       a. Pick a random unused district as seed
       b. Grow the group by adding adjacent unused districts
       c. Keep growing until we reach the target size
       d. Ensure the group remains contiguous
       e. Check that remaining districts can satisfy remaining targets

    Args:
        district_adj: Dictionary of district adjacencies
        target_sizes: List of target super-district sizes [5, 5, 4]
        num_districts: Total number of single-member districts
        seed: Random seed for reproducibility

    Returns:
        Dictionary mapping district_id -> superdistrict_id
    """
    print(f"\n[5] Running FRA gluing algorithm...")
    print(f"    Target pattern: {'-'.join(map(str, target_sizes))} seats")

    random.seed(seed)

    # Try multiple times with different random seeds if needed
    max_attempts = 100

    for attempt in range(max_attempts):
        try:
            return _try_gluing(district_adj, target_sizes, num_districts, seed + attempt)
        except ValueError as e:
            if attempt < max_attempts - 1:
                print(f"      ⚠ Attempt {attempt + 1} failed, retrying...")
                continue
            else:
                raise ValueError(f"Could not find valid grouping after {max_attempts} attempts") from e


def _try_gluing(district_adj, target_sizes, num_districts, seed):
    """
    Single attempt at gluing districts.

    Args:
        district_adj: Dictionary of district adjacencies
        target_sizes: List of target super-district sizes
        num_districts: Total number of districts
        seed: Random seed

    Returns:
        Dictionary mapping district_id -> superdistrict_id
    """
    random.seed(seed)

    # Track which districts are still available
    unused = set(range(num_districts))

    # Store the final assignment
    district_to_super = {}

    # Build each super-district
    for super_id, target_size in enumerate(target_sizes):
        if super_id == 0:  # Only print once
            print(f"\n    Building super-districts...")

        # Pick a random starting district
        if not unused:
            raise ValueError("Ran out of districts!")

        seed_district = random.choice(list(unused))
        current_group = {seed_district}
        unused.remove(seed_district)

        # Grow the group until we reach target size
        while len(current_group) < target_size:
            # Find all unused districts adjacent to current group
            candidates = set()
            for dist in current_group:
                for neighbor in district_adj.get(dist, set()):
                    if neighbor in unused:
                        candidates.add(neighbor)

            if not candidates:
                raise ValueError(
                    f"Cannot expand super-district {super_id} - no adjacent districts available!"
                )

            # Pick a random candidate and add it
            new_district = random.choice(list(candidates))
            current_group.add(new_district)
            unused.remove(new_district)

        # Verify the group is contiguous
        if not is_connected(current_group, district_adj):
            raise ValueError(f"Super-district {super_id} is not contiguous!")

        # Check if remaining districts can satisfy remaining targets
        remaining_targets = target_sizes[super_id + 1:]
        if not can_satisfy_remaining(unused, district_adj, remaining_targets):
            raise ValueError(f"Remaining districts cannot satisfy remaining targets!")

        # Assign all districts in this group to the super-district
        for dist in current_group:
            district_to_super[dist] = super_id

        print(f"      ✓ Super-district {super_id} ({target_size} seats): {sorted(current_group)}")

    print(f"\n    ✓ Successfully created {len(target_sizes)} super-districts")

    return district_to_super


# ============================================================================
# PART 4: AGGREGATE VOTES AND POPULATION
# ============================================================================

def aggregate_precincts_to_superdistricts(gdf, assignment, district_to_super):
    """
    Aggregate precinct data into super-districts.

    For each super-district, we:
    1. Find all precincts that belong to districts in that super-district
    2. Sum Democratic votes, Republican votes, and population

    Args:
        gdf: GeoDataFrame with precinct data
        assignment: Dictionary mapping precinct_id -> district_id
        district_to_super: Dictionary mapping district_id -> superdistrict_id

    Returns:
        Dictionary with super-district data
    """
    print(f"\n[6] Aggregating precincts into super-districts...")

    # First, map each precinct to its super-district
    precinct_to_super = {}
    for precinct, district in assignment.items():
        super_id = district_to_super[district]
        precinct_to_super[precinct] = super_id

    # Now aggregate by super-district
    super_districts = defaultdict(lambda: {
        'dem_votes': 0,
        'rep_votes': 0,
        'population': 0,
        'precincts': []
    })

    for precinct_idx in gdf.index:
        if precinct_idx in precinct_to_super:
            super_id = precinct_to_super[precinct_idx]
            row = gdf.loc[precinct_idx]

            super_districts[super_id]['dem_votes'] += int(row['G24PREDHAR'])
            super_districts[super_id]['rep_votes'] += int(row['G24PRERTRU'])
            super_districts[super_id]['population'] += int(row['TOTPOP'])
            super_districts[super_id]['precincts'].append(precinct_idx)

    # Convert to regular dict and add computed fields
    result = {}
    for super_id, data in super_districts.items():
        total_votes = data['dem_votes'] + data['rep_votes']
        dem_share = data['dem_votes'] / total_votes if total_votes > 0 else 0

        result[super_id] = {
            'superdistrict_id': super_id,
            'dem_votes': data['dem_votes'],
            'rep_votes': data['rep_votes'],
            'population': data['population'],
            'dem_share': dem_share,
            'num_precincts': len(data['precincts']),
            'precincts': data['precincts']
        }

        print(f"    Super-district {super_id}:")
        print(f"      - Precincts: {len(data['precincts']):,}")
        print(f"      - Population: {data['population']:,}")
        print(f"      - Dem votes: {data['dem_votes']:,}")
        print(f"      - Rep votes: {data['rep_votes']:,}")
        print(f"      - Dem share: {dem_share:.1%}")

    print(f"\n    ✓ Aggregated {len(result)} super-districts")

    return result


# ============================================================================
# PART 5: PROPORTIONAL SEAT ALLOCATION (SIMPLIFIED STV-PR)
# ============================================================================

def allocate_seats_proportionally(super_districts_data, target_sizes):
    """
    Allocate seats within each super-district using simplified STV-PR.

    For each super-district:
    - Let S = number of seats
    - Let p = Democratic vote share
    - Democratic seats = round(p × S)
    - Republican seats = S - Democratic seats

    Args:
        super_districts_data: Dictionary of super-district data
        target_sizes: List of seat counts per super-district [5, 5, 4]

    Returns:
        Updated super-district data with seat allocations
    """
    print(f"\n[7] Allocating seats proportionally (Simplified STV-PR)...")

    for super_id, data in super_districts_data.items():
        # Get the number of seats for this super-district
        total_seats = target_sizes[super_id]

        # Calculate Democratic vote share
        dem_share = data['dem_share']

        # Allocate seats proportionally
        dem_seats = round(dem_share * total_seats)
        rep_seats = total_seats - dem_seats

        # Add seat allocation to data
        data['total_seats'] = total_seats
        data['dem_seats'] = dem_seats
        data['rep_seats'] = rep_seats

        print(f"    Super-district {super_id} ({total_seats} seats):")
        print(f"      - Dem share: {dem_share:.1%} → {dem_seats} seats")
        print(f"      - Rep share: {1-dem_share:.1%} → {rep_seats} seats")

    print(f"\n    ✓ Seat allocation complete")

    return super_districts_data


# ============================================================================
# PART 6: OUTPUT GENERATION
# ============================================================================

def save_superdistrict_assignment(assignment, district_to_super, output_path):
    """
    Save precinct → super-district mapping as JSON.

    Args:
        assignment: Dictionary mapping precinct_id -> district_id
        district_to_super: Dictionary mapping district_id -> superdistrict_id
        output_path: Path to save JSON file
    """
    print(f"\n[8] Saving outputs...")

    # Map precincts directly to super-districts
    precinct_to_super = {
        precinct: district_to_super[district]
        for precinct, district in assignment.items()
    }

    # Convert to JSON-friendly format (string keys)
    json_assignment = {str(k): int(v) for k, v in precinct_to_super.items()}

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(json_assignment, f, indent=2)

    print(f"    ✓ Saved super-district assignment: {output_path}")


def save_fra_results(super_districts_data, output_path):
    """
    Save FRA results as CSV.

    Columns:
    - superdistrict_id
    - total_seats
    - dem_votes
    - rep_votes
    - dem_seats
    - rep_seats
    - dem_share
    - population

    Args:
        super_districts_data: Dictionary of super-district data
        output_path: Path to save CSV file
    """
    # Create DataFrame
    rows = []
    for super_id in sorted(super_districts_data.keys()):
        data = super_districts_data[super_id]
        rows.append({
            'superdistrict_id': data['superdistrict_id'],
            'total_seats': data['total_seats'],
            'dem_votes': data['dem_votes'],
            'rep_votes': data['rep_votes'],
            'dem_seats': data['dem_seats'],
            'rep_seats': data['rep_seats'],
            'dem_share': data['dem_share'],
            'population': data['population']
        })

    df = pd.DataFrame(rows)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)

    print(f"    ✓ Saved FRA results: {output_path}")

    return df


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main execution function.

    Steps:
    1. Load NC 2024 precinct shapefile
    2. Load baseline district plan
    3. Build precinct adjacency graph
    4. Build district adjacency graph
    5. Run gluing algorithm (5-5-4 pattern)
    6. Aggregate votes by super-district
    7. Allocate seats proportionally
    8. Save outputs (JSON + CSV)
    """

    # ========================================================================
    # CONFIGURATION
    # ========================================================================

    # Paths (adjust as needed)
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent

    # Input files
    shp_path = base_dir / "new_data" / "nc_2024_with_population.shp"
    plan_path = base_dir / "outputs" / "plan_assignments" / "plan_1.json"

    # Output files
    output_dir = base_dir / "outputs" / "fra"
    superdistrict_assignment_path = output_dir / "superdistrict_assignment.json"
    fra_results_path = output_dir / "fra_results.csv"

    # FRA configuration
    target_sizes = [5, 5, 4]  # Three super-districts with 5, 5, and 4 seats
    num_districts = 14  # Total single-member districts in baseline

    # ========================================================================
    # STEP 1: LOAD DATA
    # ========================================================================

    gdf = load_shapefile(shp_path)
    assignment = load_baseline_plan(plan_path, gdf)

    # ========================================================================
    # STEP 2: BUILD GRAPHS
    # ========================================================================

    precinct_adj = build_precinct_adjacency(gdf)
    district_adj = build_district_adjacency(precinct_adj, assignment)

    # ========================================================================
    # STEP 3: RUN GLUING ALGORITHM
    # ========================================================================

    district_to_super = glue_districts_greedy(
        district_adj,
        target_sizes,
        num_districts,
        seed=42
    )

    # ========================================================================
    # STEP 4: AGGREGATE AND ALLOCATE
    # ========================================================================

    super_districts_data = aggregate_precincts_to_superdistricts(
        gdf,
        assignment,
        district_to_super
    )

    super_districts_data = allocate_seats_proportionally(
        super_districts_data,
        target_sizes
    )

    # ========================================================================
    # STEP 5: SAVE OUTPUTS
    # ========================================================================

    save_superdistrict_assignment(
        assignment,
        district_to_super,
        superdistrict_assignment_path
    )

    results_df = save_fra_results(
        super_districts_data,
        fra_results_path
    )

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================

    print("\n" + "=" * 70)
    print("FRA GLUING ALGORITHM COMPLETE")
    print("=" * 70)
    print(f"\nOutputs saved to: {output_dir}")
    print(f"  - {superdistrict_assignment_path.name}")
    print(f"  - {fra_results_path.name}")

    print("\n📊 FRA Results Summary:")
    print(results_df.to_string(index=False))

    total_dem_seats = results_df['dem_seats'].sum()
    total_rep_seats = results_df['rep_seats'].sum()
    total_seats = results_df['total_seats'].sum()

    print(f"\n🗳️  Total Seats:")
    print(f"  - Democratic: {total_dem_seats}/{total_seats} ({total_dem_seats/total_seats:.1%})")
    print(f"  - Republican: {total_rep_seats}/{total_seats} ({total_rep_seats/total_seats:.1%})")

    print("\n" + "=" * 70)
    print("✅ All steps completed successfully!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
