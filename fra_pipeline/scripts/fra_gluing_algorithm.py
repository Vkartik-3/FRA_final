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

import argparse
import datetime
import json
import os
import time
import pandas as pd
import geopandas as gpd
from pathlib import Path
from collections import defaultdict, deque
import random
import sys
from tqdm import tqdm
from contextlib import contextmanager
from io_utils import atomic_write_json, atomic_write_dataframe_csv
from allocation import allocate_two_party_seats

# Super-district allocation rounding method (Gap 18). Override via FRA_ALLOCATION_METHOD.
# Default "round_half_even" preserves the original round() behavior exactly.
ALLOCATION_METHOD = os.environ.get("FRA_ALLOCATION_METHOD", "round_half_even")

try:
    import db as _db
except ImportError:
    _db = None

@contextmanager
def suppress_stdout():
    """Context manager to suppress stdout output."""
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout


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


def load_baseline_plan(plan_path, gdf=None):
    """
    Load a baseline district plan from JSON.

    Args:
        plan_path: Path to the plan JSON file (precinct_id -> district_id)
        gdf: Unused; kept for call-site backward compatibility.

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

    Two precincts are adjacent if they share a boundary (touches predicate).

    Uses GeoPandas's built-in R-tree spatial index (gdf.sindex) to find
    bounding-box candidates before applying the exact `touches` predicate.
    This reduces the number of exact geometry tests from O(N²) to roughly
    O(N × k) where k is the mean number of neighbors (~6–8 for typical
    US precinct maps), giving a practical 100–400× speedup over the naive
    full-scan approach for NC's 2,658 precincts.

    Args:
        gdf: GeoDataFrame with precinct geometries

    Returns:
        Dictionary mapping precinct_id -> set of adjacent precinct_ids
    """
    print(f"\n[3] Building precinct adjacency graph (spatial index)...")

    adjacency = defaultdict(set)
    idx_list  = list(gdf.index)

    for pos, idx in enumerate(idx_list):
        geom = gdf.geometry.iloc[pos]

        # sindex.query returns integer positions of bbox-intersecting candidates.
        # We then apply the exact predicate to filter down to true touches.
        candidate_positions = gdf.sindex.query(geom, predicate="touches")

        for cpos in candidate_positions:
            neighbor_idx = idx_list[cpos]
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
            district_to_super = _try_gluing(district_adj, target_sizes, num_districts, seed + attempt)
            return district_to_super, attempt + 1  # attempts_used is 1-indexed
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

        seed_district = random.choice(sorted(unused))
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

            # Pick a random candidate and add it — sorted() gives deterministic ordering
            new_district = random.choice(sorted(candidates))
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
    # NOTE: this is a SIMPLIFIED TWO-PARTY PROPORTIONAL approximation, NOT full STV
    # (Gap 17). No quotas, surplus transfers, eliminations, or exhausted ballots.
    print(f"\n[7] Allocating seats (simplified two-party proportional, not STV)...")

    for super_id, data in super_districts_data.items():
        # Get the number of seats for this super-district
        total_seats = target_sizes[super_id]

        # Calculate Democratic vote share
        dem_share = data['dem_share']

        # Allocate seats via explicit, documented rounding policy (Gap 18).
        # Default "round_half_even" reproduces the original round() behavior.
        dem_seats, rep_seats = allocate_two_party_seats(
            dem_share, total_seats, method=ALLOCATION_METHOD)

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

    atomic_write_json(output_path, json_assignment, indent=2)

    print(f"    ✓ Saved super-district assignment: {output_path}")


def build_fra_results_df(super_districts_data) -> pd.DataFrame:
    """
    Build the FRA results DataFrame in memory without writing to disk.

    Used by the verify-before-write pattern in process_single_plan():
    build → assert → write.
    """
    rows = []
    for super_id in sorted(super_districts_data.keys()):
        data = super_districts_data[super_id]
        rows.append({
            'superdistrict_id': data['superdistrict_id'],
            'total_seats':      data['total_seats'],
            'dem_votes':        data['dem_votes'],
            'rep_votes':        data['rep_votes'],
            'dem_seats':        data['dem_seats'],
            'rep_seats':        data['rep_seats'],
            'dem_share':        data['dem_share'],
            'population':       data['population'],
        })
    return pd.DataFrame(rows)


def write_fra_results_df(df: pd.DataFrame, output_path) -> None:
    """Write a pre-built FRA results DataFrame atomically (tmp → replace)."""
    output_path = Path(output_path)
    atomic_write_dataframe_csv(output_path, df)
    print(f"    ✓ Saved FRA results: {output_path}")


def save_fra_results(super_districts_data, output_path):
    """
    Build and write FRA results CSV atomically.

    Backward-compatible wrapper around build_fra_results_df + write_fra_results_df.
    Columns: superdistrict_id, total_seats, dem_votes, rep_votes,
             dem_seats, rep_seats, dem_share, population.
    """
    df = build_fra_results_df(super_districts_data)
    write_fra_results_df(df, output_path)
    return df


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def process_single_plan(plan_num, gdf, precinct_adj, base_dir, target_sizes, num_districts,
                        verbose=False, plan_dir_override=None, output_dir_override=None):
    """
    Process a single baseline plan through the FRA gluing algorithm.

    Args:
        plan_num: Plan number (1-1000)
        gdf: GeoDataFrame with precinct data
        precinct_adj: Precinct adjacency graph
        base_dir: Base directory path (used for default path resolution)
        target_sizes: List of super-district sizes [5, 5, 4]
        num_districts: Total number of districts (14)
        verbose: Whether to print detailed progress
        plan_dir_override: If provided, read plan JSONs from this directory instead of default
        output_dir_override: If provided, write FRA outputs to this directory instead of default

    Returns:
        Dictionary with results for this plan
    """
    if verbose:
        print(f"\n{'='*70}")
        print(f"PROCESSING PLAN {plan_num}")
        print(f"{'='*70}")

    # Caller-supplied dirs take priority over base_dir defaults
    plan_dir = Path(plan_dir_override) if plan_dir_override is not None \
               else base_dir / "outputs" / "plan_assignments"
    output_dir = Path(output_dir_override) if output_dir_override is not None \
                 else base_dir / "outputs" / "fra"

    plan_path = plan_dir / f"plan_{plan_num}.json"
    superdistrict_assignment_path = output_dir / f"superdistrict_assignment_{plan_num}.json"
    fra_results_path = output_dir / f"fra_results_{plan_num}.csv"

    # Load baseline plan
    assignment = load_baseline_plan(plan_path, gdf)

    # Build district adjacency
    district_adj = build_district_adjacency(precinct_adj, assignment)

    # Run gluing algorithm — returns (mapping, attempts_used)
    district_to_super, attempts_used = glue_districts_greedy(
        district_adj,
        target_sizes,
        num_districts,
        seed=42 + plan_num  # Different seed for each plan
    )

    # Aggregate and allocate
    super_districts_data = aggregate_precincts_to_superdistricts(
        gdf,
        assignment,
        district_to_super
    )

    super_districts_data = allocate_seats_proportionally(
        super_districts_data,
        target_sizes
    )

    # ── VERIFY BEFORE WRITE ───────────────────────────────────────────────────
    # Build results in memory first so every assertion runs before any file
    # is committed.  This prevents invalid data landing on disk.

    results_df = build_fra_results_df(super_districts_data)

    # Check 1: all precincts assigned
    precinct_to_super = {
        precinct: district_to_super[district]
        for precinct, district in assignment.items()
    }
    assert len(precinct_to_super) == len(gdf), \
        f"Not all precincts assigned: {len(precinct_to_super)}/{len(gdf)}"
    assert len(set(precinct_to_super.values())) == 3, \
        f"Should have 3 super-districts, found {len(set(precinct_to_super.values()))}"

    # Check 2: seat math
    total_seats     = results_df['total_seats'].sum()
    total_dem_seats = results_df['dem_seats'].sum()
    total_rep_seats = results_df['rep_seats'].sum()
    assert total_seats == 14, \
        f"Total seats must be 14, got {total_seats}"
    assert total_dem_seats + total_rep_seats == 14, \
        f"Dem+Rep seats must equal 14, got {total_dem_seats}+{total_rep_seats}"

    # Check 3: vote conservation
    original_dem = gdf['G24PREDHAR'].sum()
    original_rep = gdf['G24PRERTRU'].sum()
    fra_dem      = results_df['dem_votes'].sum()
    fra_rep      = results_df['rep_votes'].sum()
    assert original_dem == fra_dem, \
        f"Dem votes changed: {original_dem} → {fra_dem}"
    assert original_rep == fra_rep, \
        f"Rep votes changed: {original_rep} → {fra_rep}"

    # ── ALL ASSERTIONS PASSED — NOW WRITE TO DISK ─────────────────────────────
    save_superdistrict_assignment(
        assignment,
        district_to_super,
        superdistrict_assignment_path
    )
    write_fra_results_df(results_df, fra_results_path)

    if verbose:
        print(f"\n✓ VERIFICATION PASSED (verify-before-write):")
        print(f"  - All {len(precinct_to_super)} precincts assigned to 3 super-districts")
        print(f"  - Total seats: {total_seats} ✓")
        print(f"  - Seat allocation: Dem {total_dem_seats} + Rep {total_rep_seats} = 14 ✓")
        print(f"  - Vote totals preserved: Dem {fra_dem:,} | Rep {fra_rep:,} ✓")
        print(f"  - Gluing attempts used: {attempts_used}")

    # Return summary including attempts_used for the per-run stats CSV
    return {
        'plan_num':           plan_num,
        'dem_seats':          total_dem_seats,
        'rep_seats':          total_rep_seats,
        'attempts_used':      attempts_used,
        'results_df':         results_df,
        'verification_passed': True,
        'success':            True,
    }


def main():
    """
    Main execution function - processes a range of baseline plans.

    Steps:
    1. Load NC 2024 precinct shapefile (once)
    2. Build precinct adjacency graph (once)
    3. For each plan in [start, end]:
       a. Load baseline plan
       b. Build district adjacency
       c. Run gluing algorithm
       d. Aggregate votes by super-district
       e. Allocate seats proportionally
       f. Save outputs
    4. Print summary of all plans
    """

    parser = argparse.ArgumentParser(description="FRA gluing algorithm")
    parser.add_argument("--start", type=int, default=1,
                        help="First plan number to process (inclusive)")
    parser.add_argument("--end", type=int, default=1000,
                        help="Last plan number to process (inclusive)")
    parser.add_argument("--input", type=str, default=None,
                        help="Directory containing plan_N.json files")
    parser.add_argument("--output", type=str, default=None,
                        help="Directory to write fra_results_N.csv and superdistrict_assignment_N.json")
    args = parser.parse_args()

    start_plan = args.start
    end_plan   = args.end
    num_plans  = end_plan - start_plan + 1

    # ========================================================================
    # CONFIGURATION
    # ========================================================================

    script_dir = Path(__file__).parent
    base_dir = script_dir.parent

    shp_path = base_dir / "new_data" / "nc_2024_with_population.shp"

    # --input overrides default plan_assignments directory
    if args.input is not None:
        plan_dir = Path(args.input)
    else:
        plan_dir = base_dir / "outputs" / "plan_assignments"

    # --output overrides default fra output directory
    if args.output is not None:
        output_dir = Path(args.output)
    else:
        output_dir = base_dir / "outputs" / "fra"
    output_dir.mkdir(parents=True, exist_ok=True)

    # FRA configuration
    target_sizes = [5, 5, 4]  # Three super-districts with 5, 5, and 4 seats
    num_districts = 14  # Total single-member districts in baseline

    print(f"[INFO] Processing plans {start_plan}–{end_plan} ({num_plans} plans)")
    print(f"[INFO] Reading plan JSONs from: {plan_dir}")
    print(f"[INFO] Writing FRA outputs to: {output_dir}")

    # ========================================================================
    # STEP 1: LOAD SHAPEFILE (ONCE)
    # ========================================================================

    gdf = load_shapefile(shp_path)

    # ========================================================================
    # STEP 2: BUILD PRECINCT ADJACENCY (ONCE)
    # ========================================================================

    t_adj_start = time.perf_counter()
    precinct_adj = build_precinct_adjacency(gdf)
    t_adj_end = time.perf_counter()
    print(f"[TIMING] Precinct adjacency build: {t_adj_end - t_adj_start:.1f}s")

    # ========================================================================
    # STEP 3: PROCESS ALL 15 BASELINE PLANS
    # ========================================================================

    print(f"\n{'='*70}")
    print(f"PROCESSING {num_plans} BASELINE PLANS")
    print(f"{'='*70}")

    all_results = []
    failed_plans = []  # list of (plan_id, error_message, timestamp)

    # Register all plans in this batch as 'pending' before processing begins.
    # ON CONFLICT DO NOTHING makes re-submissions of the same batch safe.
    batch_id = (start_plan - 1) // 100 + 1  # matches SLURM array task ID convention
    if _db:
        _db.seed_batch(list(range(start_plan, end_plan + 1)), batch_id)

    # ── Per-plan processing ───────────────────────────────────────────────────
    t_proc_start = time.perf_counter()

    for plan_num in tqdm(range(start_plan, end_plan + 1), desc="Processing FRA plans", unit="plan"):
        if _db:
            _db.mark_running(plan_num)
        try:
            with suppress_stdout():
                result = process_single_plan(
                    plan_num,
                    gdf,
                    precinct_adj,
                    base_dir,
                    target_sizes,
                    num_districts,
                    plan_dir_override=plan_dir,
                    output_dir_override=output_dir,
                )
            all_results.append(result)
            if _db:
                _db.mark_done(
                    plan_num,
                    dem_seats=result["dem_seats"],
                    rep_seats=result["rep_seats"],
                    attempts_used=result.get("attempts_used"),
                )

        except Exception as e:
            ts = datetime.datetime.now().isoformat(timespec="seconds")
            failed_plans.append((plan_num, str(e), type(e).__name__, ts))
            if _db:
                _db.mark_failed(plan_num, str(e), type(e).__name__)
            continue

    t_proc_end = time.perf_counter()
    proc_s = t_proc_end - t_proc_start
    print(f"[TIMING] Plan processing: {proc_s:.1f}s  "
          f"({proc_s / num_plans:.2f}s per plan)")

    # ── Failure tracking ──────────────────────────────────────────────────────
    total_attempted = num_plans
    total_succeeded = len(all_results)
    total_failed    = len(failed_plans)

    print(f"\n[SUMMARY] Attempted: {total_attempted}  "
          f"Succeeded: {total_succeeded}  Failed: {total_failed}")

    if failed_plans:
        print(f"\n⚠️  {total_failed} plans failed:")
        for fp_num, fp_err, fp_exc, fp_ts in failed_plans[:5]:
            print(f"  - Plan {fp_num} ({fp_ts}) [{fp_exc}]: {fp_err}")
        if total_failed > 5:
            print(f"  ... and {total_failed - 5} more")

        # Save richer failed-plan log — batch-specific name prevents SLURM collision.
        # Columns: plan_id, error_message, exception_type, timestamp.
        analysis_dir = output_dir.parent / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        failed_csv = analysis_dir / f"fra_failed_plans_{start_plan}_{end_plan}.csv"
        failed_df  = pd.DataFrame({
            "plan_id":        [fp[0] for fp in failed_plans],
            "error_message":  [fp[1] for fp in failed_plans],
            "exception_type": [fp[2] for fp in failed_plans],
            "timestamp":      [fp[3] for fp in failed_plans],
        })
        atomic_write_dataframe_csv(failed_csv, failed_df)
        print(f"  ✓ Failed plan log saved to: {failed_csv}")

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================

    print("\n" + "=" * 70)
    print("FRA GLUING ALGORITHM - ALL PLANS COMPLETE")
    print("=" * 70)
    print(f"\nSuccessfully processed {len(all_results)}/{num_plans} plans")
    print(f"\nOutputs saved to: {output_dir}/")
    print(f"  - superdistrict_assignment_{start_plan}.json through superdistrict_assignment_{end_plan}.json")
    print(f"  - fra_results_{start_plan}.csv through fra_results_{end_plan}.csv")

    # Summary statistics - only show first and last few if many plans
    print("\n📊 SUMMARY ACROSS ALL PLANS:")
    print("-" * 80)
    print(f"{'Plan':<6} {'Dem Seats':<12} {'Rep Seats':<12} {'Dem %':<10} {'Attempts':<10}")
    print("-" * 80)

    def _fmt_row(result):
        dem_seats = result['dem_seats']
        rep_seats = result['rep_seats']
        dem_pct   = dem_seats / 14 * 100
        attempts  = result.get('attempts_used', '?')
        print(f"{result['plan_num']:<6} {dem_seats:<12} {rep_seats:<12} "
              f"{dem_pct:<10.1f}% {attempts:<10}")

    if len(all_results) <= 20:
        for result in all_results:
            _fmt_row(result)
    else:
        for result in all_results[:5]:
            _fmt_row(result)
        print(f"{'...':<6} {'...':<12} {'...':<12} {'...':<10} {'...':<10}")
        for result in all_results[-5:]:
            _fmt_row(result)

    print("-" * 70)

    # Average seat allocation
    avg_dem = sum(r['dem_seats'] for r in all_results) / len(all_results)
    avg_rep = sum(r['rep_seats'] for r in all_results) / len(all_results)

    print(f"\n🗳️  AVERAGE SEAT ALLOCATION:")
    print(f"  - Democratic: {avg_dem:.1f}/14 ({avg_dem/14:.1%})")
    print(f"  - Republican: {avg_rep:.1f}/14 ({avg_rep/14:.1%})")

    # Seat distribution
    dem_seat_counts = {}
    for result in all_results:
        count = result['dem_seats']
        dem_seat_counts[count] = dem_seat_counts.get(count, 0) + 1

    print(f"\n📈 DEMOCRATIC SEAT DISTRIBUTION:")
    for seats in sorted(dem_seat_counts.keys()):
        count = dem_seat_counts[seats]
        pct = count / len(all_results) * 100
        bar = "█" * int(pct / 5)
        print(f"  {seats} seats: {count:>2} plans ({pct:>5.1f}%) {bar}")

    # Gluing attempt statistics
    attempts_list = [r.get('attempts_used', 1) for r in all_results]
    max_att  = max(attempts_list) if attempts_list else 0
    mean_att = sum(attempts_list) / len(attempts_list) if attempts_list else 0
    hard_cases = sum(1 for a in attempts_list if a > 1)
    print(f"\n🔄 GLUING RETRY STATISTICS:")
    print(f"  - Mean attempts per plan: {mean_att:.2f}")
    print(f"  - Max attempts needed:    {max_att}")
    print(f"  - Plans needing >1 try:   {hard_cases} / {len(all_results)}")

    # Write per-plan stats CSV for auditability
    if all_results:
        stats_dir = output_dir.parent / "analysis"
        stats_dir.mkdir(parents=True, exist_ok=True)
        stats_csv = stats_dir / f"fra_plan_stats_{start_plan}_{end_plan}.csv"
        stats_df  = pd.DataFrame([
            {
                "plan_id":      r['plan_num'],
                "dem_seats":    r['dem_seats'],
                "rep_seats":    r['rep_seats'],
                "attempts_used": r.get('attempts_used', 1),
            }
            for r in all_results
        ])
        atomic_write_dataframe_csv(stats_csv, stats_df)
        print(f"  ✓ Per-plan stats saved to: {stats_csv}")

    # ========================================================================
    # VERIFICATION SUMMARY
    # ========================================================================
    print("\n" + "=" * 70)
    print("✅ VERIFICATION SUMMARY")
    print("=" * 70)

    num_verified = sum(1 for r in all_results if r.get('verification_passed', False))
    print(f"\n✓ Plans processed: {len(all_results)}/{num_plans} ({len(all_results)/num_plans*100:.1f}%)")
    print(f"✓ Plans verified: {num_verified}/{len(all_results)} ({num_verified/len(all_results)*100:.1f}%)")
    print(f"\nAll verified plans passed the following checks:")
    print(f"  • All 2,658 precincts assigned to super-districts")
    print(f"  • Exactly 3 super-districts (5-5-4 seat pattern)")
    print(f"  • Total seats = 14")
    print(f"  • Democratic + Republican seats = 14")
    print(f"  • Vote totals preserved (no votes lost/gained)")

    if len(failed_plans) > 0:
        print(f"\n⚠️  {len(failed_plans)} plans failed verification or processing")
    else:
        print(f"\n✓ 100% success rate - all plans passed verification")

    print("\n" + "=" * 70)
    print("✅ All steps completed successfully!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
