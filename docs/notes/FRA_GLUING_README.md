# FRA Gluing Algorithm - Documentation

## Overview

This script implements the **Fair Representation Act (FRA) gluing algorithm** for North Carolina using 2024 presidential election data. It transforms a baseline plan of 14 single-member districts into 3 multi-member super-districts with proportional seat allocation.

## What It Does

### Input
- **Baseline Plan**: A GerryChain-generated plan with 14 single-member districts
- **Precinct Data**: NC shapefile with 2024 presidential vote totals (Dem/Rep)

### Output
- **3 Super-Districts** with seat counts: **5-5-4** (total: 14 seats)
- Each super-district is **contiguous** (neighboring districts only)
- Seats allocated **proportionally** based on vote share

### FRA Rules Applied

1. **Multi-member districts**: 3-5 seats each
2. **Contiguity**: All super-districts are geographically connected
3. **Proportional allocation**: Seats distributed by vote share (Simplified STV-PR)
4. **No gerrymandering**: Uses simple adjacency-based gluing, not partisan optimization

## How the Algorithm Works

### Step 1: Load Data
- Reads NC precinct shapefile with 2024 presidential data
- Loads baseline district plan (precinct → district mapping)

### Step 2: Build Adjacency Graphs
- **Precinct adjacency**: Two precincts are neighbors if they share a boundary
- **District adjacency**: Two districts are neighbors if any of their precincts touch

### Step 3: Gluing Algorithm (5-5-4 Pattern)
For each target super-district size (5, 5, then 4):
1. Pick a random unused district as the **seed**
2. **Grow** by adding neighboring unused districts
3. Stop when target size is reached
4. Verify the group is **contiguous**
5. Check that remaining districts can satisfy remaining targets

**Key Feature**: Uses retry logic with different random seeds to find a valid grouping

### Step 4: Aggregate Votes
For each super-district:
- Sum Democratic votes across all precincts
- Sum Republican votes across all precincts
- Sum population
- Calculate Democratic vote share

### Step 5: Allocate Seats (Simplified STV-PR)
For each super-district:
- Let **S** = number of seats (5 or 4)
- Let **p** = Democratic vote share
- **Democratic seats** = round(p × S)
- **Republican seats** = S - Democratic seats

### Step 6: Save Outputs
- **`superdistrict_assignment.json`**: Maps each precinct to its super-district
- **`fra_results.csv`**: Summary table with vote totals and seat allocations

## File Structure

```
fra_pipeline/
├── scripts/
│   ├── fra_gluing_algorithm.py    ← Main script
│   └── FRA_GLUING_README.md       ← This file
├── new_data/
│   └── nc_2024_with_population.shp ← Precinct shapefile
├── outputs/
│   ├── plan_assignments/
│   │   └── plan_1.json            ← Baseline plan input
│   └── fra/
│       ├── superdistrict_assignment.json  ← Output 1
│       └── fra_results.csv                ← Output 2
```

## Usage

### Run the Script

```bash
cd fra_pipeline
source env/bin/activate
python scripts/fra_gluing_algorithm.py
```

### Expected Output

```
======================================================================
FRA GLUING ALGORITHM - North Carolina 2024
======================================================================

[1] Loading precinct shapefile...
    ✓ Loaded 2,658 precincts
    ✓ Total population: 10,679,260
    ✓ Democratic votes: 2,713,609.0
    ✓ Republican votes: 2,896,941.0

[2] Loading baseline district plan...
    ✓ Loaded plan with 14 districts

[3] Building precinct adjacency graph...
    ✓ Built adjacency for 2,658 precincts

[4] Building district adjacency graph...
    ✓ Built adjacency for 14 districts

[5] Running FRA gluing algorithm...
    Target pattern: 5-5-4 seats
    ✓ Successfully created 3 super-districts

[6] Aggregating precincts into super-districts...
    ✓ Aggregated 3 super-districts

[7] Allocating seats proportionally (Simplified STV-PR)...
    ✓ Seat allocation complete

[8] Saving outputs...
    ✓ Saved super-district assignment
    ✓ Saved FRA results

📊 FRA Results Summary:
 superdistrict_id  total_seats  dem_votes  rep_votes  dem_seats  rep_seats  dem_share
                0            5     856342    1138596          2          3      42.9%
                1            5    1072054     895542          3          2      54.5%
                2            4     785213     862803          2          2      47.6%

🗳️  Total Seats:
  - Democratic: 7/14 (50.0%)
  - Republican: 7/14 (50.0%)
```

## Output Files

### 1. `superdistrict_assignment.json`

Maps each precinct ID to its super-district ID:

```json
{
  "531": 0,
  "532": 0,
  "533": 0,
  ...
}
```

- **Key**: Precinct ID (as string)
- **Value**: Super-district ID (0, 1, or 2)

### 2. `fra_results.csv`

Summary table with seat allocations:

| superdistrict_id | total_seats | dem_votes | rep_votes | dem_seats | rep_seats | dem_share | population |
|------------------|-------------|-----------|-----------|-----------|-----------|-----------|------------|
| 0                | 5           | 856,342   | 1,138,596 | 2         | 3         | 0.429     | 3,801,498  |
| 1                | 5           | 1,072,054 | 895,542   | 3         | 2         | 0.545     | 3,819,142  |
| 2                | 4           | 785,213   | 862,803   | 2         | 2         | 0.476     | 3,058,620  |

## Code Design Principles

This code follows student-friendly design:

1. **Small functions**: Each function does one thing
2. **Clear names**: Variables and functions have descriptive names
3. **Comments**: Every important step is explained
4. **Simple data structures**: Uses dicts, lists, sets (no complex classes)
5. **Step-by-step**: Code mirrors the written algorithm exactly
6. **No tricks**: Straightforward Python, no advanced features

## Key Functions

| Function | Purpose |
|----------|---------|
| `load_shapefile()` | Load NC precinct data from shapefile |
| `load_baseline_plan()` | Load district assignments from JSON |
| `build_precinct_adjacency()` | Create precinct neighbor graph |
| `build_district_adjacency()` | Create district neighbor graph |
| `is_connected()` | Check if districts form contiguous group (BFS) |
| `glue_districts_greedy()` | Main gluing algorithm with retry logic |
| `aggregate_precincts_to_superdistricts()` | Sum votes and population |
| `allocate_seats_proportionally()` | Apply simplified STV-PR formula |
| `save_superdistrict_assignment()` | Write precinct → super-district JSON |
| `save_fra_results()` | Write summary CSV |

## Customization

### Use a Different Baseline Plan

Edit line 529 in `fra_gluing_algorithm.py`:

```python
plan_path = base_dir / "outputs" / "plan_assignments" / "plan_2.json"  # Change to plan_2
```

### Change the Seat Pattern

Edit line 536:

```python
target_sizes = [6, 4, 4]  # Instead of [5, 5, 4]
```

**Note**: Total must equal 14 seats.

### Adjust Random Seed

Edit line 541:

```python
seed=100  # Instead of 42
```

Different seeds produce different super-district groupings.

## What This Script Does NOT Do

- **Does NOT** implement full STV ballot transfers
- **Does NOT** optimize for partisan fairness metrics
- **Does NOT** modify precinct boundaries
- **Does NOT** change vote totals
- **Does NOT** compare to baseline (that's Step 3 of the pipeline)

## Next Steps

After running this script, you can:

1. **Visualize** the super-districts on a map
2. **Compare** FRA results to the baseline plan
3. **Run** the gluing algorithm on all 15 baseline plans
4. **Analyze** the distribution of seat allocations

## Dependencies

- Python 3.8+
- geopandas
- pandas
- shapely (included with geopandas)

All dependencies are installed in the `fra_pipeline/env` virtual environment.

## Author

Generated with [Claude Code](https://claude.com/claude-code)

## License

Educational use only.
