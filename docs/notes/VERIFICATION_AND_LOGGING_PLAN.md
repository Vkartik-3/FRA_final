# FRA Project: Verification & Logging Analysis and Implementation Plan

**Date Created:** 2025-12-08
**Purpose:** Comprehensive analysis of current verification mechanisms and plan for implementing robust logging, metrics, and validation
**Context:** Professor asked: "How are you verifying everything is working correctly? Where are the logs? What metrics are you checking?"

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Current State Analysis](#current-state-analysis)
3. [Critical Gaps Identified](#critical-gaps-identified)
4. [Implementation Plan](#implementation-plan)
5. [Talking Points for Professor](#talking-points-for-professor)
6. [Technical Specifications](#technical-specifications)

---

## Project Overview

### What This Project Does

**Fair Representation Act (FRA) Pipeline for North Carolina 2024 Presidential Election**

Demonstrates how multi-member proportional representation reduces gerrymandering compared to winner-take-all single-member districts.

**Key Result:** FRA reduces proportionality gap from 6-13% (winner-take-all) to under 2% on average across 1000 plans.

### Project Structure

```
NEWFINALFRA/
├── GerryChain/                    # Redistricting algorithm library
├── fra_pipeline/
│   ├── scripts/                   # 12 Python scripts (~4,897 lines)
│   │   ├── run_baseline_simple.py           # Generate 1000 baseline plans
│   │   ├── fra_gluing_algorithm.py          # Convert to FRA super-districts
│   │   ├── dashboard_fra.py                 # Interactive visualization
│   │   ├── dashboard_comparison.py          # Baseline + FRA comparison
│   │   ├── analyze_fra_ensemble.py          # Statistical analysis
│   │   └── analyze_baseline_and_compare.py  # Comparative analysis
│   ├── new_data/                  # Input datasets (NC 2024 shapefile)
│   ├── outputs/                   # Generated results
│   │   ├── plan_assignments/      # 1000 baseline JSONs
│   │   ├── fra/                   # FRA results
│   │   └── analysis/              # 15 plots + CSVs
│   └── requirements.txt
└── Documentation (8 markdown files)
```

### Data Flow Pipeline

```
INPUT LAYER:
  NC 2024 Presidential Election Data
  ├── 2,658 voting precincts (VTDs)
  ├── Total population: 10,679,260
  ├── Democratic votes: 2,713,609 (48.4%)
  └── Republican votes: 2,896,941 (51.6%)

STAGE 1 - BASELINE GENERATION:
  run_baseline_simple.py (326 lines)
  ├── Load shapefile & repair geometries
  ├── Build GerryChain graph from precinct topology
  ├── Create initial 14-district partition
  ├── Run ReCom Markov Chain (1000 iterations)
  └── Output: 1000 JSON files (precinct → district mapping)

STAGE 2 - FRA GLUING:
  fra_gluing_algorithm.py (828 lines)
  ├── Load baseline plan (14 single-member districts)
  ├── Build district adjacency graph
  ├── Glue districts into 3 super-districts (5-5-4 pattern)
  ├── Verify contiguity (BFS check)
  ├── Allocate seats proportionally (Simplified STV-PR)
  └── Output: fra_results_X.csv (super-district statistics)

STAGE 3 - VISUALIZATION & ANALYSIS:
  dashboard_fra.py (764 lines)
  ├── Load precinct shapefile + FRA results
  ├── Render interactive map (Folium)
  ├── Display metrics & comparisons
  └── Show proportionality analysis
```

### Key Algorithms

**1. Baseline Generation (Markov Chain Monte Carlo)**
- Uses GerryChain's ReCom proposal
- Generates random contiguous district plans
- Maintains population balance (±5% of ideal)
- 1000 iterations = 1000 diverse plans

**2. FRA Gluing (Graph-based Greedy Clustering)**
- Precinct adjacency: Spatial geometry intersection
- District adjacency: Derived from precinct adjacency
- Greedy grouping: Seed-and-grow with connectivity verification
- Seat allocation: Proportional representation with rounding

**3. Key Functions:**
- `is_connected()` - BFS to verify contiguity (fra_gluing_algorithm.py:200-230)
- `can_satisfy_remaining()` - Feasibility check (fra_gluing_algorithm.py:250-280)
- `glue_districts_greedy()` - Main gluing logic (fra_gluing_algorithm.py:600-700)
- `allocate_seats_proportional()` - Seat distribution (fra_gluing_algorithm.py:400-450)

---

## Current State Analysis

### ✅ What EXISTS (Current Verification Mechanisms)

#### 1. Basic Output/Progress Indicators
- **284 print statements** across 7 scripts
- Progress bars using `tqdm` for long-running operations
- Console output with emojis and section separators
- Example locations:
  - `run_baseline_simple.py:36-72` - Loading messages
  - `fra_gluing_algorithm.py:54-71` - Data validation messages
  - `analyze_baseline_and_compare.py:39-57` - Analysis progress

#### 2. Minimal Input Validation
- **verify_shapefile.py (75 lines)**:
  - Checks required columns exist (TOTPOP, G24PREDHAR, G24PRERTRU)
  - Validates shapefile can be loaded
  - Reports basic statistics

- **Geometry Validation:**
  - Location: `run_baseline_simple.py:44-52`
  - Detects invalid polygons with `~gdf.geometry.is_valid`
  - Repairs using `buffer(0)` operation
  - Logs number of repairs needed

- **Column Presence Checks:**
  - Location: `fra_gluing_algorithm.py:62-66`
  - Verifies required columns before processing
  - Raises ValueError if columns missing

#### 3. Analysis Outputs
- **CSV Results:**
  - `baseline_ensemble.csv` - Aggregate baseline results
  - `fra_results_X.csv` - Per-plan FRA results
  - `baseline_ensemble_combined.csv` - Full ensemble data
  - `fra_ensemble_combined.csv` - Full FRA ensemble data

- **Visualizations:**
  - 15 PNG plots in `outputs/analysis/`
  - 3 interactive Streamlit dashboards
  - Comparative charts (baseline vs FRA vs ideal)

#### 4. Contiguity Checking
- **Function:** `is_connected()` in fra_gluing_algorithm.py
- **Method:** Breadth-First Search (BFS) traversal
- **Usage:** Validates super-districts are spatially connected
- **Location:** Lines 200-230 in fra_gluing_algorithm.py

### 🔍 Current Verification Workflow

**How we currently verify correctness:**
1. **Visual Inspection:** Look at dashboard maps to see if districts look reasonable
2. **CSV Review:** Manually check that seat counts sum to 14
3. **Chart Analysis:** Review proportionality gap plots for outliers
4. **Console Monitoring:** Watch print statements during execution

**Current Evidence of Correctness:**
- Dashboards render without errors
- Seat totals appear correct in CSV files
- Proportionality gaps match theoretical expectations
- Vote totals in outputs match input data (when manually checked)

---

## Critical Gaps Identified

### 🔴 Gap 1: NO STRUCTURED LOGGING SYSTEM

**Current Problem:**
- Only `print()` statements scattered throughout code
- No log files saved to disk
- No log levels (INFO, WARNING, ERROR, DEBUG)
- No timestamps on events
- Logs disappear when terminal closes
- Can't review what happened during 1000-plan run

**Evidence:**
```bash
# Grep results show NO usage of logging module
$ grep -r "import logging" fra_pipeline/scripts/
# Returns: (empty)

$ grep -r "print(" fra_pipeline/scripts/ | wc -l
# Returns: 284
```

**Impact:**
- Cannot debug issues after the fact
- Cannot verify correct execution without watching console in real-time
- No audit trail for research reproducibility
- Cannot identify which plans had issues during generation

**Where This Matters Most:**
1. `run_baseline_simple.py` - 1000-plan generation (30-60 min runtime)
2. `fra_gluing_algorithm.py` - May retry up to 100 times per plan
3. `dashboard_fra.py` - Data loading and validation errors

---

### 🔴 Gap 2: NO VERIFICATION OF CORE ALGORITHM LOGIC

#### 2a. Contiguity Verification Not Tested

**Location:** `fra_gluing_algorithm.py:200-230`

**Current Code:**
```python
def is_connected(district_set, adjacency_graph):
    """Check if a set of districts forms a contiguous region using BFS."""
    if not district_set:
        return False
    start = next(iter(district_set))
    visited = set()
    queue = deque([start])

    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)

        for neighbor in adjacency_graph[current]:
            if neighbor in district_set and neighbor not in visited:
                queue.append(neighbor)

    return visited == district_set
```

**Missing Verifications:**
- ❌ No unit tests proving this BFS implementation works correctly
- ❌ No test cases with known disconnected districts
- ❌ No logging of which districts were rejected for non-contiguity
- ❌ No tracking of how often contiguity checks fail

**Potential Issues:**
- What if adjacency_graph is built incorrectly?
- What if BFS has a bug with edge cases?
- How do we know it catches ALL disconnected cases?

#### 2b. Seat Allocation Math Not Verified

**Location:** `fra_gluing_algorithm.py:400-450`

**Current Code (simplified):**
```python
def allocate_seats_proportional(dem_votes, rep_votes, total_seats):
    total_votes = dem_votes + rep_votes
    dem_share = dem_votes / total_votes

    dem_seats = round(dem_share * total_seats)
    rep_seats = total_seats - dem_seats

    return dem_seats, rep_seats
```

**Missing Verifications:**
- ❌ Does `round()` always produce fair results?
- ❌ What happens with exact 50-50 ties?
- ❌ Are there edge cases where `dem_seats + rep_seats ≠ total_seats`?
- ❌ No verification that proportional allocation matches theoretical expectations
- ❌ No unit tests with known correct allocations

**Example Unverified Cases:**
```python
# Test case 1: Exact tie
allocate_seats_proportional(5000, 5000, 5)  # Should give 2-3 or 3-2?

# Test case 2: Rounding edge
allocate_seats_proportional(5249, 4751, 5)  # 52.49% → rounds to 2.6245 → round() → 3?

# Test case 3: Small total
allocate_seats_proportional(100, 200, 4)  # 33.3% → 1.33 → rounds to 1 (correct)
```

#### 2c. Gluing Success Rate Not Tracked

**Location:** `fra_gluing_algorithm.py:600-700`

**Current Behavior:**
- Algorithm attempts gluing up to 100 times
- If all 100 attempts fail, raises error
- But no tracking of partial success

**Missing Information:**
- ❌ How many retries were needed per plan? (1 vs 99 makes a big difference)
- ❌ Which super-district patterns fail most often?
- ❌ Success rate across 1000 plans (do any fail completely?)
- ❌ Time spent on retries vs successful first attempts

**Example Unknown:**
```
Plan 347: Succeeded on attempt 1 (good)
Plan 542: Succeeded on attempt 87 (concerning - why so hard?)
Plan 891: Failed all 100 attempts (ERROR)

Currently we only know if Plan 891 failed - we don't know about 347 vs 542
```

---

### 🔴 Gap 3: NO NUMERICAL/STATISTICAL VALIDATION

#### 3a. Population Balance Not Verified

**Location:** `run_baseline_simple.py:77-120`

**Current Code:**
```python
# Sets constraint but doesn't verify it's met
constraint = within_percent_of_ideal_population(
    population,
    0.05  # ±5% tolerance
)

# Creates partition with constraint
partition = Partition(
    graph,
    assignment=assignment,
    updaters={"population": Tally("population", alias="population")}
)

# Runs chain with constraint
chain = MarkovChain(
    proposal=proposal,
    constraints=[contiguous, constraint],
    accept=always_accept,
    initial_state=partition,
    total_steps=1000
)
```

**Missing Verifications:**
- ❌ No logging of actual population deviations per district
- ❌ No verification that ALL districts in saved plans meet ±5%
- ❌ No tracking of which districts are closest to ideal population
- ❌ No statistical summary of population balance across ensemble

**Why This Matters:**
- GerryChain enforces constraint during generation, but:
  - No proof that saved JSON files still satisfy constraint
  - No verification after loading from disk
  - Could have serialization bugs or data corruption

#### 3b. Vote Count Invariants Not Checked

**Critical Invariant:**
```python
# These totals should NEVER change across any transformation
STATEWIDE_DEM_VOTES = 2,713,609
STATEWIDE_REP_VOTES = 2,896,941
TOTAL_POPULATION = 10,679,260
```

**Missing Assertions:**
- ❌ No check that vote totals are preserved after gluing
- ❌ No verification that precinct votes sum to district votes
- ❌ No validation that super-district votes sum to statewide votes
- ❌ No detection of vote loss/gain during transformations

**Where to Check:**
1. After loading baseline plan: `sum(all precinct votes) == STATEWIDE_TOTAL`
2. After computing district totals: `sum(district votes) == STATEWIDE_TOTAL`
3. After gluing: `sum(superdistrict votes) == STATEWIDE_TOTAL`
4. Before dashboard: `votes in CSV == votes in shapefile`

---

### 🔴 Gap 4: NO SANITY CHECKS IN DASHBOARD

**Location:** `dashboard_fra.py:1-765`

#### 4a. Data Integrity Not Validated

**Current Loading (lines 520-530):**
```python
with st.spinner(f'Loading FRA Plan {selected_plan}...'):
    gdf = load_precinct_shapefile(str(shp_path))
    fra_assignment = load_fra_plan(str(fra_path))
    fra_results = load_fra_results(str(fra_results_path))

    # Compute derived data
    statewide = compute_statewide_totals(gdf)
```

**Missing Checks:**
- ❌ No verification that all 2,658 precincts are assigned
- ❌ No check that super-district IDs are exactly {0, 1, 2}
- ❌ No validation that geometries are valid before rendering
- ❌ No check for missing/NaN values in vote columns
- ❌ No verification that assignment keys match GeoDataFrame indices

**Potential Issues:**
```python
# What if fra_assignment is missing precincts?
len(fra_assignment) == 2658  # Should verify this!

# What if super-district IDs are wrong?
set(fra_assignment.values()) == {0, 1, 2}  # Should verify this!

# What if vote columns have NaN?
gdf['G24PREDHAR'].isna().sum() == 0  # Should verify this!
```

#### 4b. Results Consistency Not Bounded

**Current Calculation (lines 600-603):**
```python
fra_dem_seat_share = fra_dem_seats / 14
proportionality_error = abs(fra_dem_seat_share - statewide['dem_share']) * 100

st.success(f"✅ **Proportionality Gap**: Only {proportionality_error:.1f}%...")
```

**Missing Bounds Checks:**
- ❌ Should proportionality gap ever exceed 10%? (Alert if it does)
- ❌ Should seat share ever be > 100% or < 0%? (Impossible, but not checked)
- ❌ Should any super-district have 0 seats? (Suspicious)
- ❌ No comparison to theoretical minimum proportionality gap

**Theoretical Bounds:**
```python
# Under FRA with 3 super-districts (5-5-4), theoretical maximum gap:
max_theoretical_gap = calculate_max_gap(seats=[5,5,4])  # ~7%?

# If observed gap > theoretical maximum, something is WRONG
if proportionality_error > max_theoretical_gap:
    st.error(f"⚠️ Proportionality gap {proportionality_error:.1f}% exceeds theoretical max!")
```

---

### 🔴 Gap 5: NO INTERMEDIATE STATE VALIDATION

**The Pipeline:**
```
Step 1: Baseline Plan → Step 2: Gluing → Step 3: FRA Super-Districts → Step 4: Seat Allocation
```

**Missing Between Steps:**

#### After Step 1 (Baseline Generation):
- ❌ No checksum/hash of baseline plan before saving
- ❌ No verification that partition is still valid after 1000 steps
- ❌ No check that assignment dictionary is complete

#### After Step 2 (Gluing):
- ❌ No verification that gluing preserves total population
- ❌ No check that all original districts were used exactly once
- ❌ No validation that super-district sizes match target (5-5-4)

#### After Step 3 (Super-District Creation):
- ❌ No check that seat allocation produces exactly 14 seats
- ❌ No verification that seat counts are non-negative integers
- ❌ No validation that super-district boundaries are legal

#### Before Step 4 (Visualization):
- ❌ No verification that CSV matches JSON assignment
- ❌ No check that all data is internally consistent

---

### 🔴 Gap 6: NO AUTOMATED TESTING

**Current State Across Entire Project:**
- ❌ **ZERO unit tests** for any function
- ❌ **ZERO integration tests** for end-to-end pipeline
- ❌ **ZERO regression tests** to catch bugs in updates
- ❌ **ZERO test data** or fixtures
- ❌ No `tests/` directory
- ❌ No pytest/unittest configuration

**Critical Missing Tests:**

```python
# Should exist but don't:

# Test contiguity checking
def test_is_connected_with_connected_districts():
    """Verify is_connected() returns True for known connected set."""
    pass

def test_is_connected_with_disconnected_districts():
    """Verify is_connected() returns False for known disconnected set."""
    pass

# Test seat allocation
def test_allocate_seats_exact_half():
    """Verify 50-50 vote split gives fair seat allocation."""
    assert allocate_seats_proportional(5000, 5000, 4) in [(2, 2)]

def test_allocate_seats_sums_correctly():
    """Verify dem_seats + rep_seats always equals total_seats."""
    for dem in range(0, 10000, 100):
        for rep in range(0, 10000, 100):
            for total in [4, 5, 14]:
                d, r = allocate_seats_proportional(dem, rep, total)
                assert d + r == total

# Test gluing algorithm
def test_glue_districts_preserves_contiguity():
    """Verify glued super-districts are contiguous."""
    pass

# Test vote conservation
def test_vote_totals_preserved():
    """Verify total votes unchanged after gluing."""
    pass
```

**Impact:**
- No way to catch regressions when code changes
- No confidence that functions work correctly
- No documentation of expected behavior
- Difficult to refactor safely

---

### 🔴 Gap 7: NO PERFORMANCE/RUNTIME METRICS

**Missing Instrumentation:**

#### Timing Information
- ❌ No tracking of how long each step takes
- ❌ No timing per plan (some may be slower)
- ❌ No total pipeline runtime logging

**Should Track:**
```python
# Baseline generation
time_per_plan = []  # How long does each of 1000 plans take?
total_baseline_time = 0  # Total runtime for all plans

# FRA gluing
gluing_time_per_plan = []  # Some may take much longer (retries)
retry_counts = []  # Correlation between retries and time?
```

#### Memory Usage
- ❌ No memory tracking (important for 1000 plans in memory)
- ❌ No detection of memory leaks during long runs
- ❌ No monitoring of peak memory usage

**Why This Matters:**
- 1000 plans × 2,658 precincts = potential memory issues
- Dashboard may load large datasets into memory
- No way to optimize bottlenecks without profiling

#### Algorithm Convergence
- ❌ No tracking of ReCom chain mixing
- ❌ No verification that chain has converged
- ❌ No autocorrelation analysis

**In ReCom:**
```python
# Should track:
acceptance_rate = []  # How often are proposals accepted? (should be ~100% with always_accept)
step_times = []  # Does each step take similar time?
population_balance_over_time = []  # Is constraint being maintained?
```

---

### 🔴 Gap 8: NO ERROR HANDLING & RECOVERY

**Current Code - No Try-Except:**

```python
# run_baseline_simple.py:41
gdf = gpd.read_file(shp_path)  # What if file is corrupt?

# fra_gluing_algorithm.py:89
with open(plan_path, 'r') as f:
    assignment = json.load(f)  # What if JSON is malformed?

# dashboard_fra.py:50
gdf = gpd.read_file(shp_path)  # What if shapefile is missing?
```

**Missing Error Handling:**
- ❌ No graceful error messages for common failures
- ❌ No validation of file contents before processing
- ❌ No ability to resume from partial failures
- ❌ No checkpointing during 1000-plan generation

**Impact:**
```python
# Current behavior:
# Generate 500 plans successfully → crash on plan 501 → lose all progress

# Desired behavior:
# Generate 500 plans → checkpoint → crash on plan 501 → resume from plan 501
```

**Should Have:**
```python
try:
    gdf = gpd.read_file(shp_path)
except FileNotFoundError:
    logger.error(f"Shapefile not found: {shp_path}")
    logger.info("Please run verify_shapefile.py first")
    sys.exit(1)
except Exception as e:
    logger.error(f"Error loading shapefile: {e}")
    sys.exit(1)

# Verify data integrity
if gdf.empty:
    logger.error("Loaded shapefile is empty")
    sys.exit(1)
```

---

## Implementation Plan

### Phase 1: Structured Logging (Priority 1 - Quick Win)

**Estimated Time:** 1-2 hours
**Impact:** High - Creates audit trail for all operations
**Difficulty:** Easy

#### What to Implement

1. **Create Logging Configuration**
   - Add `logging_config.py` to `fra_pipeline/scripts/`
   - Configure log format: `[timestamp] [level] [file:line] message`
   - Set up file handlers for each script

2. **Replace Print Statements**
   - `run_baseline_simple.py`: Replace 42 print statements
   - `fra_gluing_algorithm.py`: Replace 73 print statements
   - `analyze_baseline_and_compare.py`: Replace 52 print statements
   - Other scripts: Replace remaining ~117 statements

3. **Log File Structure**
   ```
   fra_pipeline/logs/
   ├── baseline_generation_2025-12-08_14-30-15.log
   ├── fra_gluing_2025-12-08_15-45-22.log
   ├── dashboard_2025-12-08_16-12-03.log
   └── analysis_2025-12-08_17-00-45.log
   ```

#### Implementation Details

**File:** `fra_pipeline/scripts/logging_config.py`
```python
import logging
from pathlib import Path
from datetime import datetime

def setup_logger(name, log_dir="logs", level=logging.INFO):
    """
    Set up a logger with both file and console handlers.

    Args:
        name: Logger name (usually script name)
        log_dir: Directory to store log files
        level: Logging level

    Returns:
        Configured logger
    """
    # Create logs directory
    log_path = Path(__file__).parent.parent / log_dir
    log_path.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create formatters
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '[%(levelname)s] %(message)s'
    )

    # File handler (with timestamp)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file = log_path / f"{name}_{timestamp}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Console handler (user-facing, less verbose)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging to: {log_file}")

    return logger
```

**Where to Modify:**

1. **run_baseline_simple.py** (Lines to change: 36-72, 92-98, and others)
   ```python
   # OLD (line 40):
   print("📂 Loading shapefile...")
   print(f"✅ Loaded {len(gdf)} precincts from shapefile.")

   # NEW:
   from logging_config import setup_logger
   logger = setup_logger('baseline_generation')

   logger.info("Loading shapefile from: %s", shp_path)
   logger.info("Loaded %d precincts from shapefile", len(gdf))
   logger.debug("Shapefile columns: %s", list(gdf.columns))
   ```

2. **fra_gluing_algorithm.py** (Lines to change: 54-71, 87-99, and others)
   ```python
   # OLD (line 68):
   print(f"    ✓ Loaded {len(gdf):,} precincts")
   print(f"    ✓ Democratic votes: {gdf['G24PREDHAR'].sum():,}")

   # NEW:
   from logging_config import setup_logger
   logger = setup_logger('fra_gluing')

   logger.info("Loaded %d precincts", len(gdf))
   logger.info("Democratic votes: %d", gdf['G24PREDHAR'].sum())
   logger.info("Republican votes: %d", gdf['G24PRERTRU'].sum())
   logger.debug("Total population: %d", gdf['TOTPOP'].sum())
   ```

3. **dashboard_fra.py** (Lines to change: dashboard loads)
   ```python
   # NEW (add at top):
   from logging_config import setup_logger
   logger = setup_logger('dashboard_fra')

   # Add logging around data loads (line 523-530):
   logger.info("Loading FRA Plan %d", selected_plan)
   logger.debug("Shapefile path: %s", shp_path)
   logger.debug("FRA assignment path: %s", fra_path)

   gdf = load_precinct_shapefile(str(shp_path))
   logger.info("Loaded precinct shapefile with %d precincts", len(gdf))

   fra_assignment = load_fra_plan(str(fra_path))
   logger.info("Loaded FRA assignment with %d precincts", len(fra_assignment))
   ```

#### Log Levels to Use

- **DEBUG:** Detailed diagnostic info (variable values, intermediate steps)
- **INFO:** Confirmation that things work as expected (files loaded, plans generated)
- **WARNING:** Something unexpected but not critical (retries needed, missing optional data)
- **ERROR:** Serious problem that prevents operation (file not found, invalid data)

---

### Phase 2: Verification Functions (Priority 2 - Core Correctness)

**Estimated Time:** 3-4 hours
**Impact:** Critical - Ensures algorithmic correctness
**Difficulty:** Medium

#### What to Implement

Create `fra_pipeline/scripts/verification.py` with comprehensive checks:

```python
"""
Verification functions for FRA pipeline.

These functions verify correctness at each stage of the pipeline.
All functions return (success: bool, message: str, metrics: dict).
"""

import logging
from collections import Counter

logger = logging.getLogger(__name__)


def verify_baseline_plan(gdf, assignment, num_districts=14):
    """
    Verify a baseline district plan is valid.

    Checks:
    - All precincts are assigned exactly once
    - Exactly num_districts districts exist
    - Population balance is within ±5%
    - All districts are represented

    Args:
        gdf: GeoDataFrame with precinct data
        assignment: Dict mapping precinct_id -> district_id
        num_districts: Expected number of districts

    Returns:
        (success: bool, message: str, metrics: dict)
    """
    metrics = {}

    # Check 1: All precincts assigned
    num_precincts = len(gdf)
    num_assigned = len(assignment)

    if num_assigned != num_precincts:
        return False, f"Only {num_assigned}/{num_precincts} precincts assigned", metrics

    metrics['num_precincts_assigned'] = num_assigned
    logger.info("✓ All %d precincts assigned", num_precincts)

    # Check 2: Correct number of districts
    district_ids = set(assignment.values())
    actual_num_districts = len(district_ids)

    if actual_num_districts != num_districts:
        return False, f"Found {actual_num_districts} districts, expected {num_districts}", metrics

    metrics['num_districts'] = actual_num_districts
    logger.info("✓ Correct number of districts: %d", num_districts)

    # Check 3: District IDs are contiguous [0, 1, ..., num_districts-1]
    expected_ids = set(range(num_districts))
    if district_ids != expected_ids:
        return False, f"District IDs {district_ids} != expected {expected_ids}", metrics

    logger.info("✓ District IDs are valid: 0-%d", num_districts-1)

    # Check 4: Population balance
    total_pop = gdf['TOTPOP'].sum()
    ideal_pop = total_pop / num_districts
    tolerance = 0.05  # ±5%

    gdf_copy = gdf.copy()
    gdf_copy['district'] = gdf_copy.index.map(assignment)

    population_deviations = []
    max_deviation = 0
    max_deviation_district = None

    for district_id in range(num_districts):
        district_pop = gdf_copy[gdf_copy['district'] == district_id]['TOTPOP'].sum()
        deviation = abs(district_pop - ideal_pop) / ideal_pop
        population_deviations.append(deviation)

        if deviation > max_deviation:
            max_deviation = deviation
            max_deviation_district = district_id

        if deviation > tolerance:
            return False, f"District {district_id} has {deviation*100:.2f}% deviation (> {tolerance*100}%)", metrics

    metrics['max_population_deviation'] = max_deviation
    metrics['max_deviation_district'] = max_deviation_district
    metrics['mean_population_deviation'] = sum(population_deviations) / len(population_deviations)

    logger.info("✓ Population balance: max deviation %.2f%% (district %d)",
                max_deviation*100, max_deviation_district)

    return True, "Baseline plan is valid", metrics


def verify_fra_gluing(gdf, baseline_assignment, fra_assignment, fra_results,
                      expected_superdistricts=3, expected_seats=14):
    """
    Verify FRA gluing produced valid super-districts.

    Checks:
    - Correct number of super-districts
    - All precincts assigned exactly once
    - Total seats sum to expected value
    - Vote totals preserved from baseline
    - Super-district sizes match expected pattern

    Args:
        gdf: GeoDataFrame with precinct data
        baseline_assignment: Original district assignments
        fra_assignment: Super-district assignments
        fra_results: DataFrame with FRA results
        expected_superdistricts: Expected number of super-districts
        expected_seats: Expected total seats

    Returns:
        (success: bool, message: str, metrics: dict)
    """
    metrics = {}

    # Check 1: All precincts assigned
    if len(fra_assignment) != len(gdf):
        return False, f"FRA assignment has {len(fra_assignment)} precincts, expected {len(gdf)}", metrics

    logger.info("✓ All %d precincts assigned to super-districts", len(fra_assignment))

    # Check 2: Correct number of super-districts
    superdistrict_ids = set(fra_assignment.values())
    if len(superdistrict_ids) != expected_superdistricts:
        return False, f"Found {len(superdistrict_ids)} super-districts, expected {expected_superdistricts}", metrics

    metrics['num_superdistricts'] = len(superdistrict_ids)
    logger.info("✓ Correct number of super-districts: %d", expected_superdistricts)

    # Check 3: Super-district IDs are [0, 1, 2]
    expected_ids = set(range(expected_superdistricts))
    if superdistrict_ids != expected_ids:
        return False, f"Super-district IDs {superdistrict_ids} != expected {expected_ids}", metrics

    logger.info("✓ Super-district IDs are valid: 0-%d", expected_superdistricts-1)

    # Check 4: Total seats sum correctly
    total_seats = fra_results['total_seats'].sum()
    if total_seats != expected_seats:
        return False, f"Total seats {total_seats} != expected {expected_seats}", metrics

    metrics['total_seats'] = int(total_seats)
    logger.info("✓ Total seats correct: %d", expected_seats)

    # Check 5: Dem + Rep seats = Total seats for each super-district
    for idx, row in fra_results.iterrows():
        dem_seats = row['dem_seats']
        rep_seats = row['rep_seats']
        total = row['total_seats']

        if dem_seats + rep_seats != total:
            return False, f"Super-district {row['superdistrict_id']}: {dem_seats} + {rep_seats} != {total}", metrics

    logger.info("✓ Seat allocation sums correct for all super-districts")

    # Check 6: Vote totals preserved
    baseline_dem_total = gdf['G24PREDHAR'].sum()
    baseline_rep_total = gdf['G24PRERTRU'].sum()

    fra_dem_total = fra_results['dem_votes'].sum()
    fra_rep_total = fra_results['rep_votes'].sum()

    if baseline_dem_total != fra_dem_total:
        return False, f"Dem votes changed: {baseline_dem_total} → {fra_dem_total}", metrics

    if baseline_rep_total != fra_rep_total:
        return False, f"Rep votes changed: {baseline_rep_total} → {fra_rep_total}", metrics

    metrics['dem_votes_preserved'] = int(fra_dem_total)
    metrics['rep_votes_preserved'] = int(fra_rep_total)
    logger.info("✓ Vote totals preserved: Dem %d, Rep %d", fra_dem_total, fra_rep_total)

    # Check 7: Super-district seat pattern
    seat_pattern = sorted(fra_results['total_seats'].tolist())
    expected_pattern = [4, 5, 5]  # NC pattern

    if seat_pattern != expected_pattern:
        logger.warning("Seat pattern %s != expected %s", seat_pattern, expected_pattern)
        # Not a hard failure, but worth noting
    else:
        logger.info("✓ Seat pattern correct: %s", seat_pattern)

    metrics['seat_pattern'] = seat_pattern

    return True, "FRA gluing is valid", metrics


def verify_dashboard_data(gdf, fra_assignment, fra_results):
    """
    Verify data integrity before rendering dashboard.

    Checks:
    - No NaN values in critical columns
    - Geometries are valid
    - Assignment keys match GeoDataFrame indices
    - FRA results match assignment

    Args:
        gdf: GeoDataFrame with precinct data
        fra_assignment: Dict mapping precinct_id -> superdistrict_id
        fra_results: DataFrame with FRA results

    Returns:
        (success: bool, message: str, metrics: dict)
    """
    metrics = {}

    # Check 1: No NaN in vote columns
    dem_nan = gdf['G24PREDHAR'].isna().sum()
    rep_nan = gdf['G24PRERTRU'].isna().sum()
    pop_nan = gdf['TOTPOP'].isna().sum()

    if dem_nan > 0 or rep_nan > 0 or pop_nan > 0:
        return False, f"Found NaN values: Dem {dem_nan}, Rep {rep_nan}, Pop {pop_nan}", metrics

    logger.info("✓ No NaN values in critical columns")

    # Check 2: Valid geometries
    invalid_geoms = ~gdf.geometry.is_valid
    num_invalid = invalid_geoms.sum()

    if num_invalid > 0:
        logger.warning("Found %d invalid geometries (will auto-repair)", num_invalid)
        metrics['num_invalid_geometries'] = num_invalid
    else:
        logger.info("✓ All geometries valid")

    # Check 3: Assignment keys match GeoDataFrame indices
    gdf_indices = set(gdf.index)
    assignment_keys = set(fra_assignment.keys())

    missing_in_assignment = gdf_indices - assignment_keys
    extra_in_assignment = assignment_keys - gdf_indices

    if missing_in_assignment:
        return False, f"{len(missing_in_assignment)} precincts missing in assignment", metrics

    if extra_in_assignment:
        return False, f"{len(extra_in_assignment)} extra precincts in assignment", metrics

    logger.info("✓ Assignment keys match GeoDataFrame indices")

    # Check 4: FRA results has correct super-districts
    result_sds = set(fra_results['superdistrict_id'].tolist())
    assignment_sds = set(fra_assignment.values())

    if result_sds != assignment_sds:
        return False, f"Super-district mismatch: results {result_sds} != assignment {assignment_sds}", metrics

    logger.info("✓ FRA results match assignment super-districts")

    return True, "Dashboard data is valid", metrics


def verify_proportionality_bounds(fra_results, statewide_dem_share,
                                  max_acceptable_gap=0.10):
    """
    Verify proportionality gap is within acceptable bounds.

    Args:
        fra_results: DataFrame with FRA results
        statewide_dem_share: Statewide Democratic vote share (0-1)
        max_acceptable_gap: Maximum acceptable proportionality gap

    Returns:
        (success: bool, message: str, metrics: dict)
    """
    metrics = {}

    total_dem_seats = fra_results['dem_seats'].sum()
    total_seats = fra_results['total_seats'].sum()

    dem_seat_share = total_dem_seats / total_seats
    proportionality_gap = abs(dem_seat_share - statewide_dem_share)

    metrics['dem_seat_share'] = dem_seat_share
    metrics['dem_vote_share'] = statewide_dem_share
    metrics['proportionality_gap'] = proportionality_gap

    if proportionality_gap > max_acceptable_gap:
        return False, f"Proportionality gap {proportionality_gap*100:.2f}% exceeds max {max_acceptable_gap*100}%", metrics

    logger.info("✓ Proportionality gap: %.2f%% (within %.2f%% bound)",
                proportionality_gap*100, max_acceptable_gap*100)

    return True, "Proportionality within acceptable bounds", metrics
```

#### Where to Integrate Verification

**1. In run_baseline_simple.py (after generating each plan):**
```python
# After line 150 (after saving plan):
from verification import verify_baseline_plan

success, message, metrics = verify_baseline_plan(gdf, assignment, num_districts=14)

if not success:
    logger.error("Plan %d verification failed: %s", plan_num, message)
    # Decide: skip this plan or raise error
else:
    logger.info("Plan %d verified: %s", plan_num, message)
    logger.debug("Plan %d metrics: %s", plan_num, metrics)
```

**2. In fra_gluing_algorithm.py (after gluing):**
```python
# After line 700 (after seat allocation):
from verification import verify_fra_gluing, verify_proportionality_bounds

# Verify gluing correctness
success, message, metrics = verify_fra_gluing(
    gdf, baseline_assignment, superdistrict_assignment,
    fra_results_df, expected_superdistricts=3, expected_seats=14
)

if not success:
    logger.error("FRA gluing verification failed: %s", message)
    raise ValueError(f"Verification failed: {message}")

logger.info("FRA gluing verified: %s", message)
logger.info("Verification metrics: %s", metrics)

# Verify proportionality
statewide_dem_share = total_dem / (total_dem + total_rep)
success, message, metrics = verify_proportionality_bounds(
    fra_results_df, statewide_dem_share, max_acceptable_gap=0.10
)

if not success:
    logger.warning("Proportionality check: %s", message)
else:
    logger.info("Proportionality verified: %s", message)
```

**3. In dashboard_fra.py (before rendering):**
```python
# After line 530 (after loading data):
from verification import verify_dashboard_data

success, message, metrics = verify_dashboard_data(gdf, fra_assignment, fra_results)

if not success:
    st.error(f"❌ Data verification failed: {message}")
    st.stop()

st.success(f"✅ Data verified: {message}")
logger.info("Dashboard data verified: %s", message)
```

---

### Phase 3: Metrics Tracking (Priority 3 - Performance Insights)

**Estimated Time:** 2-3 hours
**Impact:** Medium - Provides insights into algorithm performance
**Difficulty:** Medium

#### What to Track

Create `fra_pipeline/scripts/metrics_tracker.py`:

```python
"""
Metrics tracking for FRA pipeline.

Tracks performance, algorithm behavior, and statistical properties.
"""

import json
import time
from pathlib import Path
from datetime import datetime
import pandas as pd


class MetricsTracker:
    """Track and save metrics for FRA pipeline operations."""

    def __init__(self, output_dir):
        """
        Initialize metrics tracker.

        Args:
            output_dir: Directory to save metrics
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        self.metrics = []
        self.start_time = None

    def start_timer(self):
        """Start timing an operation."""
        self.start_time = time.time()

    def stop_timer(self):
        """
        Stop timer and return elapsed time.

        Returns:
            Elapsed time in seconds
        """
        if self.start_time is None:
            return 0

        elapsed = time.time() - self.start_time
        self.start_time = None
        return elapsed

    def record_baseline_plan(self, plan_id, runtime, num_districts,
                            population_deviation, verification_passed):
        """
        Record metrics for a baseline plan.

        Args:
            plan_id: Plan identifier
            runtime: Time to generate plan (seconds)
            num_districts: Number of districts
            population_deviation: Maximum population deviation
            verification_passed: Whether verification checks passed
        """
        self.metrics.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'baseline',
            'plan_id': plan_id,
            'runtime_seconds': runtime,
            'num_districts': num_districts,
            'max_population_deviation': population_deviation,
            'verification_passed': verification_passed
        })

    def record_fra_gluing(self, plan_id, runtime, num_retries,
                         gluing_succeeded, verification_passed):
        """
        Record metrics for FRA gluing operation.

        Args:
            plan_id: Plan identifier
            runtime: Time to complete gluing (seconds)
            num_retries: Number of retry attempts needed
            gluing_succeeded: Whether gluing succeeded
            verification_passed: Whether verification checks passed
        """
        self.metrics.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'fra_gluing',
            'plan_id': plan_id,
            'runtime_seconds': runtime,
            'num_retries': num_retries,
            'gluing_succeeded': gluing_succeeded,
            'verification_passed': verification_passed
        })

    def save_metrics(self, filename='metrics.json'):
        """
        Save all recorded metrics to file.

        Args:
            filename: Output filename
        """
        output_path = self.output_dir / filename

        with open(output_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)

        print(f"Saved {len(self.metrics)} metrics to {output_path}")

    def save_as_csv(self, filename='metrics.csv'):
        """
        Save metrics as CSV for easy analysis.

        Args:
            filename: Output filename
        """
        if not self.metrics:
            print("No metrics to save")
            return

        df = pd.DataFrame(self.metrics)
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False)

        print(f"Saved {len(self.metrics)} metrics to {output_path}")

    def print_summary(self):
        """Print summary statistics of recorded metrics."""
        if not self.metrics:
            print("No metrics recorded")
            return

        df = pd.DataFrame(self.metrics)

        print("\n" + "="*60)
        print("METRICS SUMMARY")
        print("="*60)

        # Baseline metrics
        baseline_df = df[df['type'] == 'baseline']
        if not baseline_df.empty:
            print("\nBaseline Generation:")
            print(f"  Total plans: {len(baseline_df)}")
            print(f"  Mean runtime: {baseline_df['runtime_seconds'].mean():.2f}s")
            print(f"  Total runtime: {baseline_df['runtime_seconds'].sum():.2f}s")
            print(f"  Verification pass rate: {baseline_df['verification_passed'].mean()*100:.1f}%")

        # FRA gluing metrics
        fra_df = df[df['type'] == 'fra_gluing']
        if not fra_df.empty:
            print("\nFRA Gluing:")
            print(f"  Total plans: {len(fra_df)}")
            print(f"  Mean runtime: {fra_df['runtime_seconds'].mean():.2f}s")
            print(f"  Mean retries: {fra_df['num_retries'].mean():.2f}")
            print(f"  Success rate: {fra_df['gluing_succeeded'].mean()*100:.1f}%")
            print(f"  Verification pass rate: {fra_df['verification_passed'].mean()*100:.1f}%")

        print("="*60 + "\n")
```

#### Where to Integrate Metrics

**1. In run_baseline_simple.py:**
```python
from metrics_tracker import MetricsTracker

# At start of main():
metrics_dir = base_dir / "outputs" / "metrics"
tracker = MetricsTracker(metrics_dir)

# For each plan:
tracker.start_timer()

# ... generate plan ...

runtime = tracker.stop_timer()

# After verification:
tracker.record_baseline_plan(
    plan_id=plan_num,
    runtime=runtime,
    num_districts=14,
    population_deviation=verification_metrics.get('max_population_deviation', 0),
    verification_passed=verification_success
)

# At end:
tracker.save_metrics(f'baseline_metrics_{timestamp}.json')
tracker.save_as_csv(f'baseline_metrics_{timestamp}.csv')
tracker.print_summary()
```

**2. In fra_gluing_algorithm.py:**
```python
from metrics_tracker import MetricsTracker

tracker = MetricsTracker(metrics_dir)

# Before gluing:
tracker.start_timer()
retry_count = 0

# In gluing loop:
for attempt in range(max_attempts):
    retry_count = attempt
    # ... gluing logic ...
    if success:
        break

runtime = tracker.stop_timer()

# After gluing:
tracker.record_fra_gluing(
    plan_id=plan_num,
    runtime=runtime,
    num_retries=retry_count,
    gluing_succeeded=success,
    verification_passed=verification_success
)
```

---

### Phase 4: Unit Tests (Priority 4 - Long-term Quality)

**Estimated Time:** 5-6 hours
**Impact:** High - Ensures long-term correctness
**Difficulty:** Medium-High

#### Test Structure

```
fra_pipeline/
├── scripts/
│   └── ... (existing scripts)
└── tests/
    ├── __init__.py
    ├── test_gluing_algorithm.py
    ├── test_seat_allocation.py
    ├── test_verification.py
    └── fixtures/
        ├── test_adjacency_graph.json
        └── test_assignment.json
```

#### Sample Tests

**File:** `fra_pipeline/tests/test_seat_allocation.py`
```python
"""
Unit tests for proportional seat allocation.
"""

import pytest
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from fra_gluing_algorithm import allocate_seats_proportional


class TestSeatAllocation:
    """Tests for proportional seat allocation function."""

    def test_exact_half(self):
        """Test 50-50 vote split gives fair allocation."""
        dem_seats, rep_seats = allocate_seats_proportional(5000, 5000, 4)
        assert dem_seats + rep_seats == 4
        assert dem_seats == 2  # Expect 2-2 split

    def test_clear_majority(self):
        """Test clear majority gives expected allocation."""
        dem_seats, rep_seats = allocate_seats_proportional(7000, 3000, 5)
        # 70% * 5 = 3.5 → rounds to 4
        assert dem_seats == 4
        assert rep_seats == 1

    def test_seats_sum_correctly(self):
        """Test dem + rep seats always equals total."""
        test_cases = [
            (6000, 4000, 5),
            (5500, 4500, 5),
            (5100, 4900, 4),
            (100, 200, 4),
        ]

        for dem, rep, total in test_cases:
            d, r = allocate_seats_proportional(dem, rep, total)
            assert d + r == total, f"Seats don't sum for {dem}/{rep}/{total}: {d}+{r}!={total}"

    def test_no_negative_seats(self):
        """Test seats are never negative."""
        test_cases = [
            (9000, 1000, 5),
            (1000, 9000, 5),
            (0, 10000, 5),
            (10000, 0, 5),
        ]

        for dem, rep, total in test_cases:
            d, r = allocate_seats_proportional(dem, rep, total)
            assert d >= 0, f"Dem seats negative: {d}"
            assert r >= 0, f"Rep seats negative: {r}"

    def test_zero_votes(self):
        """Test handling of zero votes."""
        # All Dem
        d, r = allocate_seats_proportional(1000, 0, 5)
        assert d == 5 and r == 0

        # All Rep
        d, r = allocate_seats_proportional(0, 1000, 5)
        assert d == 0 and r == 5
```

**File:** `fra_pipeline/tests/test_gluing_algorithm.py`
```python
"""
Unit tests for district gluing algorithm.
"""

import pytest
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from fra_gluing_algorithm import is_connected, build_district_adjacency


class TestConnectivity:
    """Tests for connectivity checking."""

    def test_single_district_connected(self):
        """Single district is always connected."""
        adjacency = {0: []}
        assert is_connected({0}, adjacency) == True

    def test_two_adjacent_districts_connected(self):
        """Two adjacent districts are connected."""
        adjacency = {0: [1], 1: [0]}
        assert is_connected({0, 1}, adjacency) == True

    def test_two_nonadjacent_districts_disconnected(self):
        """Two non-adjacent districts are disconnected."""
        adjacency = {0: [], 1: [], 2: []}
        assert is_connected({0, 2}, adjacency) == False

    def test_chain_connected(self):
        """Chain of districts is connected."""
        adjacency = {
            0: [1],
            1: [0, 2],
            2: [1, 3],
            3: [2]
        }
        assert is_connected({0, 1, 2, 3}, adjacency) == True

    def test_disconnected_components(self):
        """Two separate components are disconnected."""
        adjacency = {
            0: [1],
            1: [0],
            2: [3],
            3: [2]
        }
        # Districts 0-1 and 2-3 are separate
        assert is_connected({0, 1, 2, 3}, adjacency) == False
```

---

## Talking Points for Professor

### The Elevator Pitch (30 seconds)

> **"Professor, we currently verify by visual inspection - we look at dashboards and CSV files. We're missing automated verification and persistent logs.**
>
> **We can add three things:**
> 1. **Structured logging** - permanent log files with timestamps
> 2. **Verification functions** - automated checks that votes are preserved, seats sum to 14, super-districts are contiguous
> 3. **Metrics tracking** - save performance data (retries, runtime, deviations) to CSV
>
> **We can implement Option 1 (logging) in 1-2 hours. Should we prioritize that, or do you want verification functions first?**"

### Current State Explanation (1-2 minutes)

> **"Here's how our system currently works:**
>
> **Step 1: Baseline Generation** (`run_baseline_simple.py`)
> - Load NC 2024 shapefile (2,658 precincts)
> - Build graph of precinct neighbors
> - Run ReCom algorithm 1000 times
> - Save each plan to JSON file
> - Current verification: Print statements showing vote totals, geometry repairs
>
> **Step 2: FRA Gluing** (`fra_gluing_algorithm.py`)
> - Load baseline plan (14 districts)
> - Merge districts into 3 super-districts (5-5-4 pattern)
> - Check contiguity using BFS
> - Allocate seats proportionally
> - Current verification: Visual inspection of outputs
>
> **Step 3: Visualization** (`dashboard_fra.py`)
> - Render interactive maps
> - Display seat allocations
> - Show proportionality gaps
> - Current verification: Dashboard renders = data is valid
>
> **What we check now:**
> - ✅ Required columns exist in shapefile
> - ✅ Geometries are valid (auto-repair if needed)
> - ✅ Contiguity during gluing (BFS check)
>
> **What we DON'T check:**
> - ❌ Votes are preserved across transformations
> - ❌ All 1000 plans are valid (just assume they are)
> - ❌ Seat allocation math is correct
> - ❌ Performance metrics (retries, runtime)"

### What's Missing (1 minute)

> **"We're missing three critical pieces:**
>
> **1. Structured Logging:**
> - Right now: 284 `print()` statements
> - Problem: No permanent record, disappears when terminal closes
> - Need: Log files with timestamps showing every operation
>
> **2. Automated Verification:**
> - Right now: Trust the algorithm works
> - Problem: No checks that catch silent failures
> - Need: Verify votes preserved, seats sum to 14, all precincts assigned
>
> **3. Performance Metrics:**
> - Right now: Don't know how many retries gluing needed
> - Problem: No visibility into algorithm behavior
> - Need: Track retries, runtime, success rate per plan"

### Proposed Solution (2 minutes)

> **"We can implement four phases:**
>
> **Phase 1: Structured Logging** (1-2 hours - Quick Win)
> - Create `logging_config.py` with proper log formatting
> - Replace all `print()` with `logging.info()` / `logging.error()`
> - Save logs to `fra_pipeline/logs/` with timestamps
> - Example: `baseline_generation_2025-12-08_14-30-15.log`
>
> **Phase 2: Verification Functions** (3-4 hours - Core Correctness)
> - Create `verification.py` with automated checks:
>   - `verify_baseline_plan()` - check population ±5%, all precincts assigned
>   - `verify_fra_gluing()` - check votes preserved, seats=14, contiguity
>   - `verify_dashboard_data()` - check no NaN values, valid geometries
> - Call after each pipeline stage
> - Log verification results, raise errors if failed
>
> **Phase 3: Metrics Tracking** (2-3 hours - Performance Insights)
> - Create `metrics_tracker.py` to record:
>   - Per-plan: runtime, retries, population deviation
>   - Ensemble: mean, variance, outliers
> - Save to `metrics/plan_X_metrics.json` and CSV
> - Generate summary report at end
>
> **Phase 4: Unit Tests** (5-6 hours - Long-term Quality)
> - Create `tests/` directory with pytest
> - Test critical functions:
>   - `test_is_connected()` - BFS works correctly
>   - `test_allocate_seats()` - rounding produces valid results
>   - `test_vote_conservation()` - votes never lost
> - Run before committing changes"

### Specific Implementation Locations (30 seconds)

> **"Here's exactly where we'd add these:**
>
> **Logging:**
> - `run_baseline_simple.py:36-72` - Replace progress prints
> - `fra_gluing_algorithm.py:54-71` - Replace status messages
> - `dashboard_fra.py:520-530` - Log data loading
>
> **Verification:**
> - After `run_baseline_simple.py:150` - Verify each plan
> - After `fra_gluing_algorithm.py:700` - Verify gluing result
> - After `dashboard_fra.py:530` - Verify before rendering
>
> **Metrics:**
> - In baseline loop: Track runtime per plan
> - In gluing loop: Track retry count
> - At end: Save summary CSV"

### Questions to Ask Professor (1 minute)

> **"Before implementing, we should ask:**
>
> **1. Priority:**
> - Should we start with logging (quick win) or verification (more critical)?
> - Do you want all four phases or just some?
>
> **2. Logging detail:**
> - Keep logs for all 1000 plans or just summaries?
> - Log level: INFO (key events) or DEBUG (everything)?
>
> **3. Verification strictness:**
> - Stop execution on any failure, or just log warnings?
> - Are there specific invariants you want checked that we missed?
>
> **4. Metrics format:**
> - CSV (easy analysis) or JSON (more structured)?
> - Real-time display or just final summary?
>
> **5. Testing scope:**
> - Unit tests for all functions or just critical ones (gluing, allocation)?
> - Should we write integration tests for end-to-end pipeline?"

### Metrics to Track (Specific List)

> **"We propose tracking these specific metrics:**
>
> **Correctness Metrics:**
> - Total precincts assigned (should = 2,658)
> - Total districts (baseline=14, FRA=3)
> - Total seats allocated (should = 14)
> - Vote conservation: Dem+Rep before vs after (should be identical)
> - Population deviation: Max deviation from ideal (should ≤ 5%)
>
> **Performance Metrics:**
> - Baseline generation: Time per plan
> - FRA gluing: Number of retries per plan
> - FRA gluing: Success rate across 1000 plans
> - Total pipeline runtime
>
> **Statistical Metrics:**
> - Proportionality gap per plan
> - Ensemble variance (how much variation across 1000 plans)
> - Outlier detection (flag unusual plans)
> - Super-district size distribution (verify 5-5-4 pattern)"

---

## Technical Specifications

### File Locations Summary

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| **Baseline Generation** | `run_baseline_simple.py` | 326 | Generate 1000 random district plans |
| **FRA Gluing** | `fra_gluing_algorithm.py` | 828 | Convert 14 districts → 3 super-districts |
| **FRA Dashboard** | `dashboard_fra.py` | 764 | Interactive visualization (FRA only) |
| **Comparison Dashboard** | `dashboard_comparison.py` | 779 | Baseline + FRA comparison |
| **FRA Analysis** | `analyze_fra_ensemble.py` | 555 | Statistical analysis of FRA ensemble |
| **Baseline Analysis** | `analyze_baseline_and_compare.py` | 687 | Baseline analysis + comparison |
| **Verification Utility** | `verify_shapefile.py` | 75 | Input data validation |

### Critical Functions Reference

| Function | File | Lines | Purpose | Current Issues |
|----------|------|-------|---------|----------------|
| `is_connected()` | fra_gluing_algorithm.py | 200-230 | BFS contiguity check | Not unit tested |
| `allocate_seats_proportional()` | fra_gluing_algorithm.py | 400-450 | Seat allocation math | Rounding edge cases not verified |
| `glue_districts_greedy()` | fra_gluing_algorithm.py | 600-700 | Main gluing algorithm | Retry count not logged |
| `compute_baseline_results()` | dashboard_fra.py | 104-137 | Winner-take-all seats | Vote conservation not checked |
| `create_initial_partition()` | run_baseline_simple.py | 77-120 | Initial district partition | Population balance not verified |

### Data Files Reference

| File Pattern | Location | Size | Content |
|--------------|----------|------|---------|
| `nc_2024_with_population.shp` | `fra_pipeline/new_data/` | 31 MB | 2,658 precincts with 2024 votes |
| `plan_X.json` | `outputs/plan_assignments/` | ~28 KB each | Precinct → district mapping (1000 files) |
| `superdistrict_assignment_X.json` | `outputs/fra/` | ~15 KB each | Precinct → super-district mapping |
| `fra_results_X.csv` | `outputs/fra/` | ~1 KB each | Super-district statistics & seats |
| `baseline_ensemble.csv` | `outputs/` | ~50 KB | Aggregate baseline results |

### Key Constants

```python
# North Carolina 2024 Presidential Election
NUM_PRECINCTS = 2658
NUM_BASELINE_DISTRICTS = 14
NUM_FRA_SUPERDISTRICTS = 3
FRA_SUPERDISTRICT_SIZES = [5, 5, 4]  # Seats per super-district

# Vote Totals (Statewide)
TOTAL_DEM_VOTES = 2_713_609
TOTAL_REP_VOTES = 2_896_941
TOTAL_POPULATION = 10_679_260

# Constraints
POPULATION_TOLERANCE = 0.05  # ±5%
MAX_GLUING_RETRIES = 100
NUM_PLANS_TO_GENERATE = 1000
```

### Dependencies

```
# Core libraries (from requirements.txt)
geopandas==1.0.1
pandas==2.2.3
shapely==2.0.6
networkx==3.4.2
matplotlib==3.9.2
plotly==5.24.1
streamlit==1.40.1
folium==0.19.2
tqdm==4.67.1

# For new features
pytest==8.3.4  # Unit testing
```

### Expected Outputs After Implementation

```
fra_pipeline/
├── logs/
│   ├── baseline_generation_2025-12-08_14-30-15.log
│   ├── fra_gluing_2025-12-08_15-45-22.log
│   └── dashboard_2025-12-08_16-12-03.log
├── outputs/
│   └── metrics/
│       ├── baseline_metrics_2025-12-08.json
│       ├── baseline_metrics_2025-12-08.csv
│       ├── fra_metrics_2025-12-08.json
│       └── fra_metrics_2025-12-08.csv
└── tests/
    ├── test_gluing_algorithm.py
    ├── test_seat_allocation.py
    └── test_verification.py
```

---

## Summary

### Current State
- **Strengths:** Comprehensive visualization, 1000-plan ensemble, real 2024 data
- **Weaknesses:** No structured logging, minimal automated verification, no metrics tracking

### Critical Gaps
1. No persistent logs (only print statements)
2. No verification of core algorithm correctness
3. No tracking of performance metrics
4. No unit tests

### Recommended Path Forward
1. **Start with logging** (1-2 hours) - Quick win, immediate value
2. **Add verification** (3-4 hours) - Ensures correctness
3. **Implement metrics** (2-3 hours) - Performance insights
4. **Write unit tests** (5-6 hours) - Long-term quality

### Key Questions for Professor
- Which phase to prioritize?
- How detailed should logging be?
- What metrics are most important to track?
- Should verification errors stop execution or just warn?

---

**End of Document**

*This document serves as a comprehensive reference for understanding the FRA project's current verification state and implementation plan for robust logging, metrics, and validation.*
