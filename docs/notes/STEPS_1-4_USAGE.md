# FRA Pipeline — Steps 1-4 Usage Guide

This document covers how to use the baseline simulation system (Steps 1-4) that generates random single-member district plans and simulates elections using winner-take-all voting.

## 🎯 What Was Built

### Overview
Steps 1-4 create the **baseline system** that:
1. Loads North Carolina voting district data
2. Generates random single-member district (SMD) plans using GerryChain's ReCom algorithm
3. Simulates elections under current winner-take-all rules
4. Visualizes and analyzes results

This baseline will later be compared against FRA (multi-member proportional) results.

---

## 📁 Project Structure

```
fra_pipeline/
 ├── data/
 │   └── NC_VTD/              # Shapefile location
 │       └── NC_VTD.shp
 ├── scripts/
 │   ├── verify_shapefile.py         # Step 2: Verify data loading
 │   ├── run_baseline_simple.py      # Step 3: Generate plans & simulate
 │   ├── generate_district_csvs.py   # Generate district-level data
 │   ├── plot_baseline.py            # Step 4a: Create histogram
 │   └── app_baseline.py             # Step 4b: Streamlit dashboard
 ├── outputs/
 │   ├── baseline_ensemble.csv       # Plan-level results
 │   ├── baseline_districts_plan_*.csv  # District-level results
 │   ├── baseline_hist.png           # Histogram visualization
 │   └── plan_assignments/           # District assignments (JSON)
 └── requirements.txt
```

---

## 🚀 How to Run

### Prerequisites

Ensure dependencies are installed:

```bash
cd fra_pipeline
pip install -r requirements.txt
```

### Step 1: Verify Project Structure ✅
Already complete — directory structure exists.

### Step 2: Verify Shapefile

```bash
python scripts/verify_shapefile.py
```

**Expected Output:**
- Shapefile loaded successfully
- 2,692 precincts
- Total population: ~9.5 million
- Democratic vote share: ~51.7%

### Step 3: Generate Baseline Plans & Simulate Elections

```bash
python scripts/run_baseline_simple.py
```

**What it does:**
- Generates 10 random district plans using ReCom
- Each plan has 14 single-member districts
- Simulates winner-take-all elections in each district
- Saves results to `outputs/`

**Expected Output:**
- `outputs/baseline_ensemble.csv` — Summary of all 10 plans
- `outputs/plan_assignments/plan_*.json` — District assignments for each plan

**Runtime:** ~2-5 minutes

### Step 3b: Generate District-Level CSV Files

```bash
python scripts/generate_district_csvs.py
```

**What it does:**
- Reads plan assignments
- Aggregates votes and population by district
- Creates detailed CSV files for dashboard

**Expected Output:**
- `outputs/baseline_districts_plan_1.csv`
- `outputs/baseline_districts_plan_2.csv`
- ... (one file per plan)

### Step 4a: Visualize Results (Static Plot)

```bash
python scripts/plot_baseline.py
```

**What it does:**
- Reads `baseline_ensemble.csv`
- Creates histogram of Democratic seat distribution
- Saves to `outputs/baseline_hist.png`

**Expected Output:**
- PNG image showing seat distribution
- Summary statistics printed to console

### Step 4b: Launch Interactive Dashboard

```bash
streamlit run scripts/app_baseline.py
```

**What it does:**
- Opens interactive web dashboard
- Allows exploration of all 10 plans
- Shows district-level results and seat distributions

**Features:**
- Sidebar to select plans (0-9)
- Summary statistics for all plans
- Histogram highlighting selected plan
- District-level vote totals and winners
- Comparative analysis across plans

**Access:** Opens automatically in browser at `http://localhost:8501`

---

## 📊 Output Files Explained

### `baseline_ensemble.csv`
Plan-level summary with columns:
- `plan_id` — Plan number (1-10)
- `dem_seats` — Democratic seats won
- `rep_seats` — Republican seats won
- `dem_seat_share` — Democratic seat share (0-1)

**Example:**
```csv
plan_id,dem_seats,rep_seats,dem_seat_share
1,8,6,0.5714
2,8,6,0.5714
3,8,6,0.5714
4,9,5,0.6429
```

### `baseline_districts_plan_<id>.csv`
District-level detail with columns:
- `plan_id` — Plan number
- `district_id` — District number (0-13)
- `dem_votes` — Democratic votes in district
- `rep_votes` — Republican votes in district
- `population` — Total population
- `winner` — 'Democrat' or 'Republican'

**Example:**
```csv
plan_id,district_id,dem_votes,rep_votes,population,winner
1,0,158928,120786,686918,Democrat
1,1,166191,149550,678208,Democrat
1,2,129784,154682,690747,Republican
```

### `plan_assignments/plan_*.json`
Maps each precinct to its assigned district.

**Example:**
```json
{
  "0": 5,
  "1": 5,
  "2": 12,
  ...
}
```

---

## 📈 Expected Results

From the current run (10 plans):

**Democratic Seat Distribution:**
- Mean: 8.4 seats / 14 (60%)
- Range: 8-9 seats
- Statewide vote share: ~51.7% Democratic

**Key Insight:**
Even with Democrats winning ~52% of votes statewide, they win 57-64% of seats across different district maps. This demonstrates how district boundaries affect outcomes.

---

## 🧩 Understanding the Election Simulation

### Winner-Take-All Rule
For each district:
```
if D_votes > R_votes → Democrat wins
else → Republican wins
```

Then count and store Democratic/Republican seats for every plan.

### Why 10 Plans?
GerryChain's ReCom algorithm generates a distribution of possible redistricting plans. By sampling 10 plans, we can see the **range of possible outcomes** under different (but valid) district boundaries.

---

## 🛠️ Troubleshooting

### Shapefile not found
**Error:** `❌ Shapefile not found`

**Solution:** Ensure shapefile exists at one of these locations:
- `fra_pipeline/data/NC_VTD/NC_VTD.shp`
- `../data/NC-shapefiles/NC_VTD/NC_VTD.shp`

### Missing outputs
**Error:** `❌ Results not found`

**Solution:** Run the baseline simulation first:
```bash
python scripts/run_baseline_simple.py
```

### Import errors
**Error:** `ModuleNotFoundError: No module named 'gerrychain'`

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

---

## ✅ Verification Checklist

After running all steps, verify:

- [ ] `outputs/baseline_ensemble.csv` exists (294 bytes, 10 plans)
- [ ] `outputs/baseline_hist.png` exists
- [ ] `outputs/baseline_districts_plan_1.csv` through `plan_10.csv` exist (10 files)
- [ ] `outputs/plan_assignments/` contains 10 JSON files
- [ ] Histogram shows Democratic seats ranging from 8-9
- [ ] Streamlit dashboard loads without errors

---

## 🚫 What's NOT Included (Yet)

Steps 1-4 do **NOT** include:
- FRA multi-member district merging
- Proportional seat allocation
- Ranked-choice voting (RCV)
- Multi-winner simulations

These features come in **Steps 5+** and will build on this baseline.

---

## 📚 Next Steps

After validating Steps 1-4:
1. Compare baseline results to expectations
2. Understand the range of outcomes under single-member districts
3. Proceed to **Step 5**: FRA multi-member district creation
4. Implement proportional RCV simulation
5. Compare FRA vs. baseline outcomes

---

## 🧪 Quick Test Commands

```bash
# Full pipeline test
python scripts/verify_shapefile.py
python scripts/run_baseline_simple.py
python scripts/generate_district_csvs.py
python scripts/plot_baseline.py
streamlit run scripts/app_baseline.py
```

---

## 📞 Support

If you encounter issues:
1. Check that you're in the `fra_pipeline` directory
2. Verify all dependencies are installed
3. Ensure shapefile path is correct
4. Check outputs directory permissions

---

## 🎉 Success Indicators

You'll know Steps 1-4 are complete when:
1. ✅ Shapefile verification passes
2. ✅ 10 plans generated with seat counts
3. ✅ Histogram shows clear distribution
4. ✅ Dashboard loads and displays all plans interactively
5. ✅ District-level results available for all plans

**Congratulations!** You now have a working baseline simulation system ready for FRA comparison.
