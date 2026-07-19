# FRA Pipeline - Complete Setup from Scratch

This guide walks you through running the entire FRA pipeline from a fresh clone of the repository.

---

## Prerequisites

- **Python 3.8+** installed
- **macOS/Linux** (Windows users: use WSL or Git Bash)
- **Git** installed
- **~2GB disk space** for data and outputs
- **~30-60 minutes** total runtime

---

## Step-by-Step Instructions

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd fra_pipeline
```

**Expected**: You should see the project structure:
```
fra_pipeline/
├── new_data/
│   └── nc_2024_with_population.shp  (and related .shx, .dbf, etc.)
├── scripts/
│   ├── generate_baseline.py
│   ├── fra_gluing_algorithm.py
│   └── dashboard_fra.py
├── outputs/          (empty or missing - will be created)
├── env/             (missing - will be created)
└── README.md
```

---

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv env

# Activate it
source env/bin/activate  # On macOS/Linux
# OR
env\Scripts\activate     # On Windows
```

**Expected output**:
```
(env) $  # Your prompt should show (env) prefix
```

---

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all required packages
pip install geopandas pandas shapely gerrychain streamlit folium streamlit-folium plotly
```

**Expected output**:
```
Successfully installed geopandas-0.x.x pandas-2.x.x ...
```

**Time**: ~3-5 minutes (depending on internet speed)

**Verify installation**:
```bash
python -c "import geopandas; import gerrychain; import streamlit; print('All packages installed!')"
```

**Expected**: `All packages installed!`

---

### Step 4: Generate Baseline District Plans (GerryChain)

This generates 15 fair redistricting plans using MCMC.

```bash
python scripts/generate_baseline.py
```

**What this does**:
- Loads NC precinct shapefile (2,658 precincts)
- Runs GerryChain with 100,000 MCMC steps
- Generates 15 district plans (1 every 5,000 steps after 25,000 burn-in)
- Saves to `outputs/plan_assignments/plan_1.json` through `plan_15.json`

**Expected output** (abbreviated):
```
======================================================================
GERRYCHAIN BASELINE PLAN GENERATION - North Carolina 2024
======================================================================

[1] Loading precinct shapefile...
    ✓ Loaded 2,658 precincts
    ✓ Total population: 10,679,260

[2] Creating initial plan...
    ✓ Created balanced initial plan (14 districts)

[3] Configuring GerryChain...
    ✓ Chain configured with 100,000 steps

[4] Running MCMC chain...
    Progress: [████████████████████] 100%
    ✓ Collected 15 plans

[5] Saving plans...
    ✓ Saved 15 plans to outputs/plan_assignments/

✅ All steps completed successfully!
```

**Time**: ~10-15 minutes

**Verify outputs**:
```bash
ls outputs/plan_assignments/
```

**Expected**: 15 JSON files (`plan_1.json` through `plan_15.json`)

---

### Step 5: Generate FRA Super-Districts

This takes each baseline plan and creates FRA super-districts.

```bash
python scripts/fra_gluing_algorithm.py
```

**What this does**:
- Loads each of the 15 baseline plans
- Merges 14 districts into 3 super-districts (5-5-4 pattern)
- Ensures contiguity using greedy gluing algorithm
- Allocates seats proportionally based on vote share
- Saves to `outputs/fra/superdistrict_assignment_N.json` and `fra_results_N.csv`

**Expected output** (abbreviated):
```
======================================================================
FRA GLUING ALGORITHM - North Carolina 2024
======================================================================

[1] Loading precinct shapefile...
    ✓ Loaded 2,658 precincts

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

**Time**: ~1-2 minutes

**Verify outputs**:
```bash
ls outputs/fra/
```

**Expected**: 30 files
- 15 JSON files: `superdistrict_assignment_1.json` through `superdistrict_assignment_15.json`
- 15 CSV files: `fra_results_1.csv` through `fra_results_15.csv`

---

### Step 6: Launch Interactive Dashboard

```bash
streamlit run scripts/dashboard_fra.py
```

**OR** (if you have the shell script):
```bash
chmod +x run_dashboard.sh  # Make executable (first time only)
./run_dashboard.sh
```

**Expected output**:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

**Dashboard will automatically open in your browser** at `http://localhost:8501`

**Time**: Instant (dashboard loads in <1 second)

---

## Using the Dashboard

### Navigation

1. **Sidebar - Plan Selection**:
   - Dropdown showing "FRA Plan 1" through "FRA Plan 15"
   - Select any plan to view its super-districts

2. **Sidebar - Super-District Selection**:
   - Dropdown showing "Super-District 0", "1", "2"
   - Select to highlight on map and see detailed metrics

3. **Main Panel**:
   - **Interactive Map**: Hover over super-districts to see details
   - **Summary Cards**: 3 color-coded cards showing seat allocation
   - **Detailed Table**: Vote totals and percentages
   - **Explanations**: Expandable sections explaining FRA mechanics

### Features to Explore

- **Switch between plans**: Notice how super-district boundaries change
- **Hover tooltips**: See vote totals, seat allocation, population
- **Zoom/Pan map**: Explore geographic details
- **Compare metrics**: Check proportionality gap (typically <2%)

---

## Verify Everything Works

### Quick Verification Checklist

```bash
# 1. Check baseline plans exist
ls outputs/plan_assignments/ | wc -l
# Expected: 15

# 2. Check FRA assignments exist
ls outputs/fra/ | grep superdistrict_assignment | wc -l
# Expected: 16 (15 numbered + 1 legacy)

# 3. Check FRA results exist
ls outputs/fra/ | grep fra_results | wc -l
# Expected: 16 (15 numbered + 1 legacy)

# 4. Verify one FRA result file
head outputs/fra/fra_results_1.csv
# Expected: CSV header + 3 rows (one per super-district)
```

### Sample FRA Results

```csv
superdistrict_id,total_seats,dem_votes,rep_votes,dem_seats,rep_seats,dem_share,population
0,5,856342,1138596,2,3,0.429,3801498
1,5,1072054,895542,3,2,0.545,3819142
2,4,785213,862803,2,2,0.476,3058620
```

**Interpretation**:
- **Super-district 0**: 5 seats, 42.9% Dem → 2 Dem seats, 3 Rep seats
- **Super-district 1**: 5 seats, 54.5% Dem → 3 Dem seats, 2 Rep seats
- **Super-district 2**: 4 seats, 47.6% Dem → 2 Dem seats, 2 Rep seats
- **Total**: 7 Dem, 7 Rep (50-50 split, close to 48.4% statewide Dem vote)

---

## Troubleshooting

### Issue 1: "No module named 'geopandas'"

**Solution**:
```bash
# Make sure virtual environment is activated
source env/bin/activate

# Reinstall dependencies
pip install geopandas pandas shapely gerrychain streamlit folium streamlit-folium plotly
```

---

### Issue 2: "Shapefile not found"

**Solution**:
```bash
# Check if shapefile exists
ls new_data/nc_2024_with_population.shp

# If missing, you need to add the data files to the repo
# Contact repo maintainer or check data download instructions
```

---

### Issue 3: GerryChain takes too long

**Solution**: Reduce number of steps in `generate_baseline.py`

Edit `scripts/generate_baseline.py`, line ~150:
```python
# Change this:
num_steps = 100000

# To this (faster, less diverse):
num_steps = 10000
```

Then re-run:
```bash
python scripts/generate_baseline.py
```

---

### Issue 4: Dashboard shows "No FRA plans found"

**Solution**:
```bash
# Check if FRA outputs exist
ls outputs/fra/

# If empty, run FRA gluing algorithm
python scripts/fra_gluing_algorithm.py
```

---

### Issue 5: Streamlit port already in use

**Solution**:
```bash
# Kill existing Streamlit process
pkill -f streamlit

# Or use a different port
streamlit run scripts/dashboard_fra.py --server.port 8502
```

---

## Complete Command Sequence (Copy-Paste)

For convenience, here's the entire sequence in one block:

```bash
# 1. Clone and navigate
git clone <your-repo-url>
cd fra_pipeline

# 2. Create and activate virtual environment
python3 -m venv env
source env/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install --upgrade pip
pip install geopandas pandas shapely gerrychain streamlit folium streamlit-folium plotly

# 4. Generate baseline plans (~10-15 min)
python scripts/generate_baseline.py

# 5. Generate FRA super-districts (~1-2 min)
python scripts/fra_gluing_algorithm.py

# 6. Launch dashboard
streamlit run scripts/dashboard_fra.py
```

**Total Time**: ~15-20 minutes + browsing dashboard

---

## Directory Structure After Setup

```
fra_pipeline/
├── env/                              ← Virtual environment (created)
├── new_data/
│   └── nc_2024_with_population.shp   ← Input shapefile
├── outputs/                          ← Generated outputs
│   ├── plan_assignments/             ← Baseline plans
│   │   ├── plan_1.json               ← 15 JSON files
│   │   ├── plan_2.json
│   │   └── ...
│   └── fra/                          ← FRA super-districts
│       ├── superdistrict_assignment_1.json   ← 15 JSON files
│       ├── fra_results_1.csv                 ← 15 CSV files
│       └── ...
├── scripts/
│   ├── generate_baseline.py          ← Stage 1: GerryChain
│   ├── fra_gluing_algorithm.py       ← Stage 2: FRA Gluing
│   └── dashboard_fra.py              ← Stage 3: Dashboard
└── README.md
```

---

## Next Steps

After running the pipeline, you can:

1. **Explore the Dashboard**: Try different plans, hover over districts
2. **Modify Parameters**:
   - Change super-district sizes in `fra_gluing_algorithm.py` (line 687)
   - Adjust MCMC steps in `generate_baseline.py` (line ~150)
3. **Analyze Results**: Export FRA results CSVs for further analysis
4. **Compare to Winner-Take-All**: Check baseline results vs FRA
5. **Read Technical Docs**: See `DASHBOARD_TECHNICAL_EXPLANATION.md`

---

## Support

If you encounter issues:

1. **Check logs**: Errors are printed to terminal
2. **Verify dependencies**: `pip list | grep -E "geopandas|gerrychain|streamlit"`
3. **Check file permissions**: `ls -la outputs/`
4. **Consult documentation**: See `QUICKSTART.md`, `FRA_GLUING_README.md`

---

## Summary

**Total Commands**: 6
**Total Time**: ~15-20 minutes
**Output**: 15 baseline plans + 15 FRA plans + interactive dashboard

✅ You're now ready to explore the Fair Representation Act in action!

---

**Document Version**: 1.0
**Last Updated**: 2025-11-08
**Tested On**: macOS 14, Python 3.12
