# FRA Pipeline — Steps 1-4: Baseline Simulation

This directory contains a clean implementation of **Steps 1-4** of the Fair Representation Act (FRA) simulation pipeline, built on top of GerryChain.

## 🎯 What This Does

Creates a **baseline election simulation system** that:
1. Loads North Carolina voting district data
2. Generates random single-member district (SMD) plans using GerryChain's ReCom
3. Simulates winner-take-all elections
4. Visualizes and analyzes results through static plots and interactive dashboards

This baseline represents the **current single-member, winner-take-all system** and will serve as a comparison point for FRA (multi-member proportional) analysis in future steps.

---

## 📁 Directory Structure

```
fra_pipeline/
 ├── scripts/
 │   ├── verify_shapefile.py         # Verify shapefile loads correctly
 │   ├── run_baseline_simple.py      # Generate 10 random plans & simulate elections
 │   ├── generate_district_csvs.py   # Create district-level result files
 │   ├── plot_baseline.py            # Generate histogram visualization
 │   ├── app_baseline.py             # Simple Streamlit dashboard
 │   └── baseline_dashboard.py       # Advanced dashboard with maps
 ├── outputs/
 │   ├── baseline_ensemble.csv       # Summary of all plans
 │   ├── baseline_districts_plan_*.csv  # District-level results per plan
 │   ├── baseline_hist.png           # Seat distribution histogram
 │   └── plan_assignments/           # JSON files with district assignments
 ├── data/
 │   └── NC_VTD/                     # Shapefile directory (if exists here)
 ├── env/                            # Virtual environment (optional)
 └── requirements.txt                # Python dependencies
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Verify Data (Step 2)

```bash
python scripts/verify_shapefile.py
```

**Expected output:** Confirms 2,692 precincts, 9.5M population, election data present

### 3. Generate Baseline Plans (Step 3)

```bash
python scripts/run_baseline_simple.py
```

**What it does:**
- Generates 10 random district plans (14 districts each)
- Simulates winner-take-all elections
- Saves plan-level and district-level results

**Runtime:** ~2-5 minutes

### 4. Create District CSV Files

```bash
python scripts/generate_district_csvs.py
```

**Creates:** `baseline_districts_plan_1.csv` through `plan_10.csv`

### 5. Visualize Results (Step 4a)

```bash
python scripts/plot_baseline.py
```

**Creates:** `outputs/baseline_hist.png` showing Democratic seat distribution

### 6. Launch Dashboard (Step 4b)

```bash
streamlit run scripts/app_baseline.py
```

**Opens:** Interactive dashboard at `http://localhost:8501`

---

## 📊 Understanding the Outputs

### `baseline_ensemble.csv`
Summary of all 10 generated plans:

| Column | Description |
|--------|-------------|
| `plan_id` | Plan number (1-10) |
| `dem_seats` | Democratic seats won |
| `rep_seats` | Republican seats won |
| `dem_seat_share` | Democratic seat proportion (0-1) |

### `baseline_districts_plan_<id>.csv`
Detailed results for each district in a plan:

| Column | Description |
|--------|-------------|
| `plan_id` | Plan number |
| `district_id` | District number (0-13) |
| `dem_votes` | Democratic votes |
| `rep_votes` | Republican votes |
| `population` | Total district population |
| `winner` | 'Democrat' or 'Republican' |

### `plan_assignments/plan_*.json`
Maps each precinct (by index) to its district assignment.

---

## 🎨 Dashboard Features

### Simple Dashboard (`app_baseline.py`)
- Plan selector (0-9)
- Summary statistics across all plans
- Interactive histogram
- District-level results table
- Vote totals and seat counts

### Advanced Dashboard (`baseline_dashboard.py`)
- All features from simple dashboard
- **Geographic map visualization** showing district boundaries
- Color-coded districts
- Interactive plan comparison

---

## 📈 Current Results

From the existing 10 plans:

| Metric | Value |
|--------|-------|
| **Democratic Seats (mean)** | 8.4 / 14 |
| **Democratic Seat Share** | 60% |
| **Seat Range** | 8-9 seats |
| **Statewide Dem Vote Share** | 51.7% |

**Key Insight:** Democrats win 60% of seats with 52% of votes, showing how district boundaries affect outcomes in winner-take-all systems.

---

## 🔧 How It Works

### 1. GerryChain ReCom Algorithm
- Generates valid, random redistricting plans
- Maintains population balance (±5% deviation)
- Ensures all districts are contiguous

### 2. Election Simulation
- **Winner-take-all rule:** `if D_votes > R_votes → Democrat wins`
- Aggregates precinct-level votes by district
- Counts total seats won by each party

### 3. Analysis
- Generates ensemble of 10 plans to see outcome variability
- Visualizes seat distribution patterns
- Provides district-level detail for deeper analysis

---

## 🛠️ Scripts Explained

### `verify_shapefile.py`
- Loads NC VTD shapefile
- Checks for required columns (`EL08G_GV_D`, `EL08G_GV_R`, `PL10AA_TOT`)
- Displays summary statistics
- Validates data integrity

### `run_baseline_simple.py`
- Builds GerryChain graph from shapefile
- Creates initial partition using recursive tree partitioning
- Runs ReCom Markov chain for 10 steps
- Simulates elections for each plan
- Saves results to CSV and JSON

### `generate_district_csvs.py`
- Reads plan assignments from JSON files
- Aggregates votes and population by district
- Determines winners
- Creates district-level CSV files for dashboard

### `plot_baseline.py`
- Loads `baseline_ensemble.csv`
- Creates histogram of Democratic seat counts
- Adds mean line and statistics
- Saves PNG visualization

### `app_baseline.py`
- Streamlit dashboard for interactive exploration
- Displays plan-level and district-level results
- Shows comparative analysis across all plans
- No geographic visualization (faster loading)

### `baseline_dashboard.py`
- Enhanced Streamlit dashboard with geographic maps
- Plots district boundaries colored by assignment
- Includes all features from `app_baseline.py`
- Requires more resources to render maps

---

## 🚫 What's NOT Included

Steps 1-4 do **NOT** implement:
- ❌ FRA multi-member district merging
- ❌ Proportional seat allocation
- ❌ Ranked-choice voting (RCV)
- ❌ Multi-winner simulations

These features are planned for **Steps 5+**.

---

## ✅ Verification Checklist

After running all scripts:

- [ ] `outputs/baseline_ensemble.csv` exists (10 plans)
- [ ] `outputs/baseline_hist.png` exists
- [ ] `outputs/baseline_districts_plan_1.csv` through `plan_10.csv` exist
- [ ] `outputs/plan_assignments/` contains 10 JSON files
- [ ] Dashboard launches without errors
- [ ] Democratic seats range from 8-9

---

## 🐛 Troubleshooting

### Shapefile Not Found
**Error:** `❌ Shapefile not found`

**Solution:** Ensure shapefile exists at:
- `fra_pipeline/data/NC_VTD/NC_VTD.shp`, OR
- `../data/NC-shapefiles/NC_VTD/NC_VTD.shp`

Scripts automatically try multiple paths.

### Missing Dependencies
**Error:** `ModuleNotFoundError`

**Solution:**
```bash
pip install -r requirements.txt
```

### Results Not Found
**Error:** `❌ Results not found`

**Solution:** Run baseline simulation first:
```bash
python scripts/run_baseline_simple.py
python scripts/generate_district_csvs.py
```

---

## 🧪 Testing the Pipeline

Run all steps in sequence:

```bash
# Step 2: Verify data
python scripts/verify_shapefile.py

# Step 3: Generate plans
python scripts/run_baseline_simple.py

# Create district files
python scripts/generate_district_csvs.py

# Step 4a: Static visualization
python scripts/plot_baseline.py

# Step 4b: Interactive dashboard
streamlit run scripts/app_baseline.py
```

---

## 📚 Additional Documentation

- **[../STEPS_1-4_USAGE.md](../STEPS_1-4_USAGE.md)** — Detailed usage guide with examples
- **[../README_STEPS_1-4.md](../README_STEPS_1-4.md)** — Project overview and quick start

---

## 🎯 Next Steps

After validating this baseline:
1. Analyze seat distribution patterns
2. Identify competitive vs. safe districts
3. Document proportionality metrics
4. **Proceed to Step 5:** FRA multi-member district creation
5. Implement proportional RCV simulation
6. Compare FRA vs. baseline outcomes

---

## 📦 Dependencies

```
geopandas       # Geospatial data handling
pandas          # Data manipulation
shapely         # Geometric operations
matplotlib      # Plotting and visualization
networkx        # Graph operations
gerrychain      # Redistricting simulation
streamlit       # Interactive dashboards
rtree           # Spatial indexing
pyyaml          # Configuration (optional)
```

---

**Steps 1-4 Complete! Ready for FRA implementation.** ✅
