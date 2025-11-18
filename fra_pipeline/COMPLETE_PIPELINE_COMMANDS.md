# Complete FRA Pipeline - Correct Command Sequence

This is the **correct, verified** command sequence for running the entire pipeline from scratch.

---

## Quick Overview of All Scripts

| Script | Purpose | Input | Output | Run Time |
|--------|---------|-------|--------|----------|
| `run_baseline_simple.py` | Generate 15 baseline plans using GerryChain | Shapefile | `plan_N.json` | 10-15 min |
| `generate_district_csvs.py` | Create CSV summaries of baseline plans | `plan_N.json` | `baseline_districts_plan_N.csv` | 10 sec |
| `fra_gluing_algorithm.py` | Generate FRA super-districts | `plan_N.json` | `superdistrict_assignment_N.json` | 1-2 min |
| `dashboard_fra.py` | Interactive FRA dashboard | FRA outputs | Web app | Instant |
| `baseline_dashboard.py` | Interactive baseline dashboard | Baseline outputs | Web app | Instant |
| `app_baseline.py` | Simple baseline viewer | CSVs | Web app | Instant |
| `plot_baseline.py` | Plot baseline histogram | CSVs | PNG image | Instant |
| `verify_shapefile.py` | Test shapefile loading | Shapefile | Terminal output | Instant |

---

## Complete Setup from Scratch

### Prerequisites

```bash
# Check Python version (need 3.8+)
python3 --version

# Should output: Python 3.8.x or higher
```

---

## Step-by-Step Commands

### Step 0: Clone and Setup Environment

```bash
# Clone repository
git clone <your-repo-url>
cd fra_pipeline

# Create virtual environment
python3 -m venv env

# Activate environment
source env/bin/activate  # macOS/Linux
# OR
env\Scripts\activate     # Windows

# Install all dependencies
pip install --upgrade pip
pip install geopandas pandas shapely gerrychain streamlit folium streamlit-folium plotly matplotlib
```

**Verify installation**:
```bash
python -c "import geopandas, gerrychain, streamlit; print('✅ All packages installed!')"
```

---

### Step 1: Generate Baseline District Plans (GerryChain)

**Command**:
```bash
python scripts/run_baseline_simple.py
```

**What it does**:
- Loads NC shapefile (2,658 precincts)
- Runs GerryChain MCMC (100,000 steps)
- Generates 15 random district plans (14 districts each)
- Saves to `outputs/plan_assignments/plan_1.json` through `plan_15.json`

**Expected output**:
```
==========================================================
📊 STEP 1: Baseline Ensemble Generation
==========================================================

📂 Loading shapefile...
✅ Loaded 2,658 precincts from shapefile.

🔧 Repairing invalid geometries...
✅ All geometries valid.

🗺️ Building dual graph...
✅ Graph built with 2,658 nodes.

🌱 Creating initial partition...
✅ Initial partition created with 14 districts.

⚙️ Configuring MCMC chain...
   - Algorithm: ReCom
   - Steps: 100,000
   - Population tolerance: ±1%

🔄 Running MCMC chain...
Progress: [████████████████████] 100%

💾 Saving plans...
✅ Saved 15 plans to outputs/plan_assignments/

✅ BASELINE ENSEMBLE GENERATION COMPLETE!
```

**Time**: ~10-15 minutes

**Verify**:
```bash
ls outputs/plan_assignments/ | wc -l
# Should output: 15
```

---

### Step 2: Generate Baseline District CSVs (Optional but Recommended)

**Command**:
```bash
python scripts/generate_district_csvs.py
```

**What it does**:
- Reads each baseline plan JSON
- Aggregates votes by district
- Determines winner (Dem/Rep) for each district
- Saves district-level summary CSVs

**Expected output**:
```
============================================================
📊 GENERATING DISTRICT-LEVEL CSV FILES
============================================================

📂 Loading shapefile from: new_data/nc_2024_with_population.shp
✅ Loaded 2,658 precincts

📋 Found 15 plan files

Processing plans: [████████████████████] 15/15

💾 Saving summary CSV...
✅ Saved baseline_ensemble.csv

✅ ALL DISTRICT CSV FILES GENERATED!
```

**Outputs**:
- `outputs/baseline_districts_plan_1.csv` through `plan_15.csv` (district-level details)
- `outputs/baseline_ensemble.csv` (summary of all plans)

**Time**: ~10 seconds

**Verify**:
```bash
ls outputs/baseline_districts_plan_*.csv | wc -l
# Should output: 15

head outputs/baseline_ensemble.csv
# Shows: plan_id, dem_seats, rep_seats, etc.
```

---

### Step 3: Generate FRA Super-Districts

**Command**:
```bash
python scripts/fra_gluing_algorithm.py
```

**What it does**:
- Loads all 15 baseline plans
- For each plan, merges 14 districts → 3 super-districts (5-5-4 pattern)
- Ensures contiguity using greedy gluing algorithm
- Allocates seats proportionally (simplified STV)
- Saves super-district assignments and results

**Expected output**:
```
======================================================================
FRA GLUING ALGORITHM - North Carolina 2024
======================================================================

[1] Loading precinct shapefile...
    ✓ Loaded 2,658 precincts
    ✓ Total population: 10,679,260
    ✓ Democratic votes: 2,713,609.0
    ✓ Republican votes: 2,896,941.0

[3] Building precinct adjacency graph...
    ✓ Built adjacency for 2,658 precincts

======================================================================
PROCESSING 15 BASELINE PLANS
======================================================================

======================================================================
PROCESSING PLAN 1
======================================================================

[2] Loading baseline district plan...
    ✓ Loaded plan with 14 districts

[5] Running FRA gluing algorithm...
    ✓ Successfully created 3 super-districts

[7] Allocating seats proportionally...
    ✓ Seat allocation complete

✓ Plan 1 complete:
  - Dem seats: 7/14
  - Rep seats: 7/14

... (repeats for plans 2-15) ...

======================================================================
FRA GLUING ALGORITHM - ALL PLANS COMPLETE
======================================================================

Successfully processed 15/15 plans

📊 SUMMARY ACROSS ALL PLANS:
----------------------------------------------------------------------
Plan   Dem Seats    Rep Seats    Dem %
----------------------------------------------------------------------
1      7            7            50.0      %
2      7            7            50.0      %
...
15     7            7            50.0      %
----------------------------------------------------------------------

🗳️  AVERAGE SEAT ALLOCATION:
  - Democratic: 6.9/14 (49.0%)
  - Republican: 7.1/14 (51.0%)

📈 DEMOCRATIC SEAT DISTRIBUTION:
  6 seats:  2 plans ( 13.3%) ██
  7 seats: 13 plans ( 86.7%) █████████████████

======================================================================
✅ All steps completed successfully!
======================================================================
```

**Outputs**:
- `outputs/fra/superdistrict_assignment_1.json` through `_15.json` (precinct → super-district mapping)
- `outputs/fra/fra_results_1.csv` through `_15.csv` (seat allocation results)

**Time**: ~1-2 minutes

**Verify**:
```bash
ls outputs/fra/superdistrict_assignment_*.json | wc -l
# Should output: 15 (or 16 if old file exists)

ls outputs/fra/fra_results_*.csv | wc -l
# Should output: 15 (or 16 if old file exists)

# Check one result
cat outputs/fra/fra_results_1.csv
```

---

### Step 4: Launch FRA Dashboard (Main Dashboard)

**Command**:
```bash
streamlit run scripts/dashboard_fra.py
```

**OR** (if shell script exists):
```bash
chmod +x run_dashboard.sh
./run_dashboard.sh
```

**What it does**:
- Launches interactive web app
- Shows FRA super-districts on map
- Allows selection between 15 different FRA plans
- Displays seat allocation metrics

**Expected output**:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

**Dashboard automatically opens in browser** at `http://localhost:8501`

**Features**:
- 🗺️ Interactive map with 3 color-coded super-districts
- 📊 Seat allocation summary cards
- 📈 Proportionality gap metrics
- 🔄 Plan selector (switch between 15 FRA plans)
- 🎯 Super-district highlighter

**Time**: <1 second to load

---

### Step 5 (Optional): View Baseline Dashboard

**Command**:
```bash
streamlit run scripts/baseline_dashboard.py
```

**What it does**:
- Shows baseline district plans (winner-take-all)
- Interactive map with 14 districts per plan
- Compare across 15 different baseline plans

**Note**: This is slower than FRA dashboard because it renders 14 districts instead of 3.

---

### Step 6 (Optional): Simple Baseline Viewer

**Command**:
```bash
streamlit run scripts/app_baseline.py
```

**What it does**:
- Lightweight dashboard without maps
- Shows seat allocation tables and charts
- Faster than full baseline dashboard

---

### Step 7 (Optional): Plot Baseline Histogram

**Command**:
```bash
python scripts/plot_baseline.py
```

**What it does**:
- Creates histogram showing Democratic seat distribution
- Saves as `baseline_hist.png`

**Output**: PNG image file

---

## Complete Command Sequence (Copy-Paste)

```bash
# === SETUP ===
cd fra_pipeline
python3 -m venv env
source env/bin/activate  # macOS/Linux
pip install --upgrade pip
pip install geopandas pandas shapely gerrychain streamlit folium streamlit-folium plotly matplotlib

# === STEP 1: Generate Baseline Plans (10-15 min) ===
python scripts/run_baseline_simple.py

# === STEP 2: Generate Baseline CSVs (10 sec) ===
python scripts/generate_district_csvs.py

# === STEP 3: Generate FRA Super-Districts (1-2 min) ===
python scripts/fra_gluing_algorithm.py

# === STEP 4: Launch FRA Dashboard ===
streamlit run scripts/dashboard_fra.py
# Opens at http://localhost:8501
```

**Total Time**: ~15-20 minutes for all generation steps

---

## Minimal Pipeline (FRA Only)

If you only care about FRA results:

```bash
# Setup
python3 -m venv env
source env/bin/activate
pip install geopandas pandas shapely gerrychain streamlit folium streamlit-folium plotly

# Generate baseline plans (required)
python scripts/run_baseline_simple.py

# Generate FRA super-districts
python scripts/fra_gluing_algorithm.py

# Launch FRA dashboard
streamlit run scripts/dashboard_fra.py
```

**Skip**: `generate_district_csvs.py` (only needed for baseline analysis)

---

## Directory Structure After Running Pipeline

```
fra_pipeline/
├── env/                                    ← Virtual environment
├── new_data/
│   └── nc_2024_with_population.shp         ← Input shapefile
├── outputs/
│   ├── plan_assignments/                   ← Baseline plans
│   │   ├── plan_1.json
│   │   ├── plan_2.json
│   │   └── ... (15 files)
│   ├── baseline_districts_plan_1.csv       ← District-level CSVs
│   ├── baseline_districts_plan_2.csv
│   ├── ... (15 files)
│   ├── baseline_ensemble.csv               ← Summary CSV
│   └── fra/                                ← FRA super-districts
│       ├── superdistrict_assignment_1.json
│       ├── fra_results_1.csv
│       └── ... (30 files total: 15 JSON + 15 CSV)
├── scripts/
│   ├── run_baseline_simple.py              ← Step 1: GerryChain
│   ├── generate_district_csvs.py           ← Step 2: CSVs
│   ├── fra_gluing_algorithm.py             ← Step 3: FRA
│   ├── dashboard_fra.py                    ← Step 4: FRA Dashboard ⭐
│   ├── baseline_dashboard.py               ← Optional: Baseline Dashboard
│   ├── app_baseline.py                     ← Optional: Simple viewer
│   └── plot_baseline.py                    ← Optional: Histogram
└── README.md
```

---

## What Each File Contains

### Baseline Plan JSONs (`plan_N.json`)
```json
{
  "0": 3,      // Precinct 0 → District 3
  "1": 7,      // Precinct 1 → District 7
  ...
}
```

### Baseline District CSVs (`baseline_districts_plan_N.csv`)
```csv
district_id,dem_votes,rep_votes,population,winner,margin,dem_share
0,156234,198765,762845,Rep,42531,0.44
1,187654,145321,751234,Dem,42333,0.56
...
```

### Baseline Ensemble CSV (`baseline_ensemble.csv`)
```csv
plan_id,dem_seats,rep_seats,dem_share_avg,rep_share_avg
1,5,9,0.484,0.516
2,6,8,0.484,0.516
...
```

### FRA Assignment JSONs (`superdistrict_assignment_N.json`)
```json
{
  "0": 1,      // Precinct 0 → Super-district 1
  "1": 0,      // Precinct 1 → Super-district 0
  ...
}
```

### FRA Results CSVs (`fra_results_N.csv`)
```csv
superdistrict_id,total_seats,dem_votes,rep_votes,dem_seats,rep_seats,dem_share,population
0,5,856342,1138596,2,3,0.429,3801498
1,5,1072054,895542,3,2,0.545,3819142
2,4,785213,862803,2,2,0.476,3058620
```

---

## Troubleshooting

### "No such file: run_baseline_simple.py"
**Issue**: Wrong script name in old documentation

**Solution**: The correct script is `run_baseline_simple.py`, not `generate_baseline.py`

### "ModuleNotFoundError: No module named 'gerrychain'"
**Issue**: Virtual environment not activated or packages not installed

**Solution**:
```bash
source env/bin/activate
pip install geopandas pandas shapely gerrychain streamlit folium streamlit-folium plotly matplotlib
```

### "Shapefile not found"
**Issue**: Missing data files

**Solution**: Ensure `new_data/nc_2024_with_population.shp` exists
```bash
ls new_data/nc_2024_with_population.shp
```

### "No FRA plans found"
**Issue**: Skipped Step 3

**Solution**: Run the FRA gluing algorithm
```bash
python scripts/fra_gluing_algorithm.py
```

### Dashboard shows old plan format
**Issue**: Old `superdistrict_assignment.json` exists

**Solution**: The dashboard prioritizes numbered files. You can safely ignore the old file or delete it:
```bash
rm outputs/fra/superdistrict_assignment.json
rm outputs/fra/fra_results.csv
```

---

## Quick Verification Commands

```bash
# Check baseline plans exist
ls outputs/plan_assignments/ | wc -l
# Expected: 15

# Check baseline CSVs exist
ls outputs/baseline_districts_plan_*.csv | wc -l
# Expected: 15

# Check FRA assignments exist
ls outputs/fra/superdistrict_assignment_*.json | wc -l
# Expected: 15 (or 16 with old file)

# Check FRA results exist
ls outputs/fra/fra_results_*.csv | wc -l
# Expected: 15 (or 16 with old file)

# View one FRA result
cat outputs/fra/fra_results_1.csv

# Check statewide totals
head outputs/baseline_ensemble.csv
```

---

## Performance Benchmarks

Tested on MacBook Pro M1:

| Step | Script | Time |
|------|--------|------|
| 1 | `run_baseline_simple.py` | 10-15 min |
| 2 | `generate_district_csvs.py` | 10 sec |
| 3 | `fra_gluing_algorithm.py` | 90 sec |
| 4 | `dashboard_fra.py` (load) | <1 sec |

**Total**: ~15-20 minutes for complete pipeline

---

## Summary

### Required Steps (FRA Dashboard):
1. ✅ `run_baseline_simple.py` - Generate baseline plans
2. ✅ `fra_gluing_algorithm.py` - Generate FRA super-districts
3. ✅ `streamlit run dashboard_fra.py` - Launch dashboard

### Optional Steps:
4. `generate_district_csvs.py` - Create baseline CSVs
5. `streamlit run baseline_dashboard.py` - View baseline plans
6. `streamlit run app_baseline.py` - Simple baseline viewer
7. `plot_baseline.py` - Create histogram

---

**Questions? Check**: `DASHBOARD_TECHNICAL_EXPLANATION.md` for detailed explanations.

**Last Updated**: 2025-11-08
