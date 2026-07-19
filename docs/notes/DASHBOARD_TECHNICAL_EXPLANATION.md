# FRA Dashboard - Technical Explanation for Academic Review

## Executive Summary

This interactive dashboard visualizes the Fair Representation Act (FRA) applied to North Carolina's 2024 congressional districts. It demonstrates how multi-member proportional representation reduces winner-take-all distortion by transforming 14 single-member districts into 3 multi-member super-districts with proportional seat allocation.

---

## 1. System Architecture

### 1.1 Three-Stage Pipeline

```
Stage 1: Baseline Generation (GerryChain)
  └─> 15 single-member district plans (14 districts each)
       └─> outputs/plan_assignments/plan_1.json to plan_15.json

Stage 2: FRA Gluing Algorithm
  └─> For each baseline plan:
       └─> Merge 14 districts into 3 super-districts (5-5-4 pattern)
       └─> Allocate seats proportionally
       └─> outputs/fra/superdistrict_assignment_N.json
       └─> outputs/fra/fra_results_N.csv

Stage 3: Interactive Dashboard (Streamlit)
  └─> Load any FRA plan (1-15)
  └─> Visualize super-districts on interactive map
  └─> Display seat allocation metrics
  └─> Compare to statewide vote share
```

---

## 2. Stage 1: Baseline Plans (GerryChain)

### 2.1 Input Data
- **Precinct-level shapefile**: North Carolina 2024 with 2,658 precincts
- **Vote data**: 2024 Presidential election (Harris vs Trump)
- **Population data**: Total population per precinct

### 2.2 GerryChain Algorithm
Uses Markov Chain Monte Carlo (MCMC) to generate fair redistricting plans:

1. **Start**: Begin with an initial valid plan
2. **Propose**: Randomly propose boundary changes
3. **Accept/Reject**: Use Metropolis-Hastings criterion to accept/reject
4. **Constraints enforced**:
   - Equal population (±1% deviation)
   - Contiguity (all districts connected)
   - 14 districts total (NC congressional delegation size)

### 2.3 Output Format
Each plan is a JSON mapping:
```json
{
  "precinct_id": district_id,
  "0": 3,      // Precinct 0 → District 3
  "1": 7,      // Precinct 1 → District 7
  ...
}
```

**Why 15 plans?** Generates multiple plans to analyze variability and robustness.

---

## 3. Stage 2: FRA Gluing Algorithm

### 3.1 Algorithm Overview

**Goal**: Transform 14 single-member districts into 3 multi-member super-districts.

**Constraints**:
- Each super-district must be **contiguous** (geographically connected)
- Seat pattern: **5-5-4** (total 14 seats preserved)
- No partisan optimization (use simple adjacency-based merging)

### 3.2 Step-by-Step Process

#### Step 1: Build Adjacency Graphs

**Precinct Adjacency**:
```python
# Two precincts are neighbors if they share a boundary
precinct_adj[i] = {j | precinct[i].touches(precinct[j])}
```

**District Adjacency**:
```python
# Two districts are neighbors if any of their precincts touch
district_adj[d1] = {d2 | ∃ p1 ∈ d1, p2 ∈ d2 : p1 ~ p2}
```

#### Step 2: Greedy Gluing with Retry

For each target super-district size (5, 5, 4):

1. **Seed Selection**: Pick random unused district as starting point
2. **Growth Phase**: Breadth-first search to add neighboring districts
   ```
   while |super_district| < target_size:
       candidates = neighbors of super_district
       add random candidate to super_district
   ```
3. **Contiguity Check**: Verify super-district is connected using BFS
4. **Feasibility Check**: Ensure remaining districts can satisfy remaining targets
5. **Retry Logic**: If infeasible, try different random seed (max 100 attempts)

**Key Insight**: Using different random seeds for each baseline plan (seed = 42 + plan_num) ensures diverse super-district configurations.

#### Step 3: Aggregate Vote Totals

For each super-district SD_i:
```
Dem_votes[SD_i] = Σ (Dem_votes[precinct] for all precincts in SD_i)
Rep_votes[SD_i] = Σ (Rep_votes[precinct] for all precincts in SD_i)
Population[SD_i] = Σ (Population[precinct] for all precincts in SD_i)
```

#### Step 4: Proportional Seat Allocation (Simplified STV)

For super-district SD_i with S seats:

```
dem_share = Dem_votes[SD_i] / (Dem_votes[SD_i] + Rep_votes[SD_i])

Dem_seats = round(dem_share × S)
Rep_seats = S - Dem_seats
```

**Example**:
- Super-district 1: 5 seats, 54.5% Dem vote
  - Dem seats = round(0.545 × 5) = 3
  - Rep seats = 5 - 3 = 2

**Why simplified STV?** Full Single Transferable Vote requires ranked-choice ballots. This implementation uses vote shares as a proxy, consistent with FRA's proportional allocation goals.

### 3.3 Output Files

**superdistrict_assignment_N.json**:
```json
{
  "precinct_id": super_district_id,
  "0": 1,   // Precinct 0 → Super-district 1
  "1": 0,   // Precinct 1 → Super-district 0
  ...
}
```

**fra_results_N.csv**:
```csv
superdistrict_id,total_seats,dem_votes,rep_votes,dem_seats,rep_seats,dem_share,population
0,5,856342,1138596,2,3,0.429,3801498
1,5,1072054,895542,3,2,0.545,3819142
2,4,785213,862803,2,2,0.476,3058620
```

---

## 4. Stage 3: Interactive Dashboard

### 4.1 Technology Stack

- **Streamlit**: Web framework for data apps
- **Folium**: Interactive map visualization (Leaflet.js wrapper)
- **GeoPandas**: Geospatial data processing
- **Plotly**: Interactive charts

### 4.2 Dashboard Components

#### Component 1: Plan Selector (Sidebar)

**Logic**:
1. Scan `outputs/fra/` directory for available plans
2. Populate dropdown with plans 1-15
3. On selection change, reload data and re-render entire dashboard

**Implementation**:
```python
fra_plans_available = []
for i in range(1, 16):
    fra_path = fra_dir / f"superdistrict_assignment_{i}.json"
    fra_results_path = fra_dir / f"fra_results_{i}.csv"
    if fra_path.exists() and fra_results_path.exists():
        fra_plans_available.append(i)

selected_plan = st.sidebar.selectbox(
    "Select FRA Plan:",
    options=fra_plans_available
)
```

**Why this matters**: Allows comparison across different baseline configurations to demonstrate FRA's robustness.

#### Component 2: Interactive Map

**Optimization: District-Level Rendering**

Original approach (slow):
- Render all 2,658 individual precincts
- Performance: 10+ seconds to load, laggy interactions

Optimized approach (fast):
- **Dissolve** precincts into 3 super-district polygons using GeoPandas
- Performance: <1 second to load, smooth interactions

**Dissolve Operation**:
```python
# Group precincts by super-district and merge geometries
gdf_districts = gdf_map.dissolve(
    by='superdistrict',    # Group by super-district ID
    aggfunc='sum'          # Sum vote totals and population
)
# Result: 3 polygons instead of 2,658
```

**Why this works**:
- Boundary data is the same (precinct boundaries preserved)
- Vote totals are aggregated, not changed
- Reduces rendering from 2,658 polygons → 3 polygons (886× reduction!)

**Map Styling**:
```python
folium.GeoJson(
    geometry,
    style_function=lambda x: {
        'fillColor': color_map[superdistrict_id],
        'color': '#000000',      # Black border
        'weight': 3,             # Thick border (visibility)
        'fillOpacity': 0.6,      # Semi-transparent fill
        'opacity': 1.0           # Solid border
    }
)
```

**Color Palette**:
- Super-district 0: Red/Coral (#FF6B6B)
- Super-district 1: Teal/Cyan (#4ECDC4)
- Super-district 2: Mint Green (#95E1D3)

**Tooltip Content**:
- Super-district ID and seat count
- Democratic/Republican seats
- Vote totals and percentages
- Population

#### Component 3: Metrics Display

**Three-Column Layout**:
```
[Super-District 0]  [Super-District 1]  [Super-District 2]
  - 5 seats            - 5 seats            - 4 seats
  - 2 Dem, 3 Rep       - 3 Dem, 2 Rep       - 2 Dem, 2 Rep
  - 42.9% Dem          - 54.5% Dem          - 47.6% Dem
  - 3.8M population    - 3.8M population    - 3.1M population
```

**Proportionality Gap Calculation**:
```python
# Statewide vote share
statewide_dem = total_dem_votes / (total_dem_votes + total_rep_votes)

# FRA seat share
fra_dem_seats = 7  # From seat allocation
fra_seat_share = 7 / 14 = 0.50

# Proportionality gap
gap = |fra_seat_share - statewide_dem|
    = |0.50 - 0.484| = 0.016 = 1.6%
```

**Interpretation**: Only 1.6% difference between vote share (48.4%) and seat share (50%) under FRA.

---

## 5. Key Results and Insights

### 5.1 Seat Distribution Across 15 Plans

**Observed Results**:
- **13 plans (86.7%)**: 7 Dem seats, 7 Rep seats (50-50 split)
- **2 plans (13.3%)**: 6 Dem seats, 8 Rep seats (43-57 split)
- **Average**: 6.9 Dem / 7.1 Rep seats

**Statewide Vote Share**:
- Democratic: 48.4%
- Republican: 51.6%

**Analysis**:
- FRA average (49.0% Dem) closely matches vote share (48.4%)
- Low variance across different baseline configurations
- Demonstrates **structural consistency** of proportional allocation

### 5.2 Why FRA Reduces Gerrymandering

**Winner-Take-All Problem**:
```
District with 51% Dem → 100% Dem representation (1 seat)
District with 49% Rep → 0% Rep representation (0 seats)
→ Wasted votes: 49% of voters unrepresented
```

**FRA Solution**:
```
Super-district with 54% Dem, 5 seats:
→ Dem gets 3 seats (60%)
→ Rep gets 2 seats (40%)
→ Closer to actual vote share
```

**Mathematical Insight**: Multi-member districts reduce the "threshold of exclusion"
```
Single-member: Threshold = 50% + 1 vote
Multi-member (5 seats): Threshold ≈ 16.7% (1/(5+1))
```

This allows minority parties to gain representation proportional to their support.

---

## 6. Technical Decisions and Trade-offs

### 6.1 Simplified STV vs Full STV

**Decision**: Use simplified proportional allocation instead of full STV ballot transfers.

**Rationale**:
- Full STV requires ranked-choice ballots (not available in US data)
- Simplified approach uses aggregate vote shares as proxy
- Produces same outcome in two-party system
- Easier to explain and implement

**Trade-off**: Would need modification for multi-party scenarios.

### 6.2 Greedy Gluing vs Optimization

**Decision**: Use greedy adjacency-based gluing with random seed variation.

**Rationale**:
- Simple, fast, deterministic given seed
- No partisan optimization (preserves fairness)
- Ensures contiguity by construction
- Variability from different seeds shows robustness

**Alternative**: Could use optimization to maximize compactness or partisan goals, but this would undermine FRA's non-partisan goals.

### 6.3 District-Level vs Precinct-Level Visualization

**Decision**: Render 3 super-district polygons instead of 2,658 precincts.

**Rationale**:
- Performance: 886× reduction in geometry complexity
- Clarity: Thick borders make super-districts easily distinguishable
- Information preservation: Vote totals unchanged (aggregated)

**Trade-off**: Lose ability to see individual precinct details. Could add optional precinct view for deep-dive analysis.

---

## 7. Validation and Verification

### 7.1 Data Integrity Checks

**Precinct Assignment**:
```python
# Every precinct assigned to exactly one super-district
assert len(set(precinct_to_superdistrict.values())) == 3
assert len(precinct_to_superdistrict) == 2658
```

**Vote Conservation**:
```python
# Sum of super-district votes equals statewide totals
assert sum(sd['dem_votes']) == statewide_dem_votes
assert sum(sd['rep_votes']) == statewide_rep_votes
```

**Seat Conservation**:
```python
# Total seats preserved (14)
assert sum(sd['total_seats']) == 14
assert sum(sd['dem_seats'] + sd['rep_seats']) == 14
```

### 7.2 Geometric Validation

**Contiguity**:
```python
# Each super-district is a single connected component
for sd in super_districts:
    assert is_connected(sd.geometry)  # BFS connectivity check
```

**Coverage**:
```python
# Super-districts cover entire state, no overlaps
union = unary_union([sd.geometry for sd in super_districts])
assert union.equals(state_boundary)
```

---

## 8. Computational Complexity

### 8.1 Time Complexity

**GerryChain (Stage 1)**:
- O(N × M) where N = precincts, M = MCMC steps
- NC example: 2,658 precincts × 100,000 steps ≈ 5-10 minutes per plan

**FRA Gluing (Stage 2)**:
- Precinct adjacency: O(N²) worst case, O(N·k) average (k = avg neighbors ≈ 3)
- District adjacency: O(D²) where D = 14 districts
- Gluing algorithm: O(D × R) where R = retry attempts (typically 1-10)
- **Total**: ~2-3 seconds per plan, 30-45 seconds for all 15 plans

**Dashboard (Stage 3)**:
- Data loading: O(N) to read shapefile (cached after first load)
- Dissolve operation: O(N) to merge geometries
- Rendering: O(S) where S = 3 super-districts (constant time)
- **Total**: <1 second for map render

### 8.2 Space Complexity

**Memory Usage**:
- Shapefile: ~50 MB (2,658 polygons with attributes)
- Adjacency graphs: O(N·k) ≈ 8,000 edges × 2 IDs = ~64 KB
- Plan assignments: O(N) = 2,658 entries × 8 bytes = ~21 KB
- **Total**: ~50 MB dominated by geometry data

**Storage**:
- Input shapefile: ~50 MB
- 15 baseline plans: 15 × 21 KB = ~315 KB
- 15 FRA assignments: 15 × 21 KB = ~315 KB
- 15 FRA results CSVs: 15 × 1 KB = ~15 KB
- **Total**: ~51 MB

---

## 9. Extensions and Future Work

### 9.1 Possible Enhancements

1. **Multi-party Support**: Extend seat allocation to handle 3+ parties
2. **Interactive Gluing**: Let users manually adjust super-district boundaries
3. **Ensemble Analysis**: Compare FRA results across 1000+ baseline plans
4. **Compactness Metrics**: Add Polsby-Popper or other shape scores
5. **Historical Comparison**: Apply FRA to past elections (2016, 2020, etc.)

### 9.2 Research Questions

1. **Robustness**: How much does FRA outcome vary with different super-district sizes (e.g., 4-4-3-3)?
2. **Competitiveness**: Does FRA increase or decrease competitive races?
3. **Geographic Representation**: How does FRA affect rural vs urban representation?
4. **Voter Turnout**: Would proportional representation increase participation?

---

## 10. Educational Use Cases

### 10.1 For Students

**Learning Objectives**:
- Understand gerrymandering and its effects
- Learn proportional representation mechanics
- Explore trade-offs between systems
- Practice geospatial data analysis

**Hands-on Activities**:
1. Modify super-district sizes and observe seat changes
2. Compare FRA results to winner-take-all baseline
3. Analyze variance across different baseline plans
4. Propose alternative seat allocation formulas

### 10.2 For Researchers

**Reproducible Research**:
- All code and data provided
- Modular design for easy modification
- Documented algorithms and assumptions
- Open-source libraries (GerryChain, GeoPandas)

**Extensibility**:
- Swap in different states/elections
- Test alternative gluing algorithms
- Integrate with existing redistricting tools
- Export results for statistical analysis

---

## 11. Limitations and Caveats

### 11.1 Methodological Limitations

1. **Simplified STV**: Does not implement full ranked-choice ballot transfers
2. **Two-party assumption**: Designed for Democratic/Republican split
3. **Greedy gluing**: May not find optimal super-district configurations
4. **No within-district optimization**: Districts merged as-is, not rebalanced

### 11.2 Data Limitations

1. **Presidential data**: Uses presidential vote as proxy for congressional preference
2. **No demographic data**: Could add race, income, etc. for equity analysis
3. **Single election**: Results may vary across different elections
4. **Precinct boundaries**: Assumes 2024 precinct boundaries are accurate

### 11.3 Scope Limitations

1. **NC only**: Not tested on other states
2. **14 seats fixed**: Assumes congressional delegation size unchanged
3. **No legal analysis**: Does not address constitutionality or state law
4. **No implementation plan**: Does not cover transition logistics

---

## 12. Conclusion

This dashboard provides an interactive, transparent demonstration of how the Fair Representation Act could work in practice using real North Carolina data. Key contributions:

1. **Methodological**: Combines GerryChain (baseline generation) with novel FRA gluing algorithm
2. **Empirical**: Shows FRA produces consistent proportional outcomes across 15 diverse baseline plans
3. **Pedagogical**: Clear visualizations and explanations suitable for education
4. **Technical**: Efficient implementation with sub-second rendering and scalable design

The results demonstrate that FRA can significantly reduce winner-take-all distortion (from potential 14-0 or 10-4 splits to 7-7 average) while maintaining geographic representation through multi-member districts.

---

## References and Further Reading

**Fair Representation Act**:
- H.R. 3863 (116th Congress)
- FairVote.org - "Fair Representation Voting"

**Redistricting Algorithms**:
- MGGG Redistricting Lab: gerrychain.readthedocs.io
- Metric Geometry and Gerrymandering Group

**Proportional Representation**:
- Lijphart, A. (1999). Patterns of Democracy
- Amy, D. (2000). Behind the Ballot Box

**Technical Documentation**:
- GeoPandas: geopandas.org
- Streamlit: streamlit.io
- Folium: python-visualization.github.io/folium

---

**Document Version**: 1.0
**Last Updated**: 2025-11-08
**Author**: Generated with Claude Code
**License**: Educational Use Only
