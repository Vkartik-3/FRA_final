# FRA Simulation Pipeline — Steps 1-4 Complete ✅

This repository contains a complete implementation of **Steps 1-4** of the Fair Representation Act (FRA) simulation pipeline, built on top of GerryChain.

## 🎯 What's Implemented

Steps 1-4 create the **baseline system**:

1. **✅ Project Setup** — Directory structure and dependencies configured
2. **✅ Data Loading** — North Carolina VTD shapefile verified and loaded
3. **✅ Baseline Simulation** — 10 random single-member district plans generated with election results
4. **✅ Visualization** — Static plots and interactive Streamlit dashboard

This baseline represents **current winner-take-all, single-member district elections** and will be compared against FRA multi-member proportional results in later steps.

---

## 🚀 Quick Start

### 1. Navigate to the pipeline directory:
```bash
cd fra_pipeline
```

### 2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Verify shapefile (Step 2):
```bash
python scripts/verify_shapefile.py
```

### 4. Generate baseline plans (Step 3):
```bash
python scripts/run_baseline_simple.py
```

### 5. Generate district-level data:
```bash
python scripts/generate_district_csvs.py
```

### 6. Create visualization (Step 4a):
```bash
python scripts/plot_baseline.py
```

### 7. Launch dashboard (Step 4b):
```bash
streamlit run scripts/app_baseline.py
```

---

## 📊 Current Results

From 10 randomly generated district plans:

| Metric | Value |
|--------|-------|
| **Plans Generated** | 10 |
| **Districts per Plan** | 14 (single-member) |
| **Avg Democratic Seats** | 8.4 / 14 (60%) |
| **Democratic Seat Range** | 8-9 seats |
| **Statewide Dem Vote Share** | 51.7% |

**Key Finding:** Democrats win 57-64% of seats despite 52% vote share, demonstrating how district boundaries affect outcomes under winner-take-all systems.

---

## 📁 Repository Structure

```
fra_pipeline/
 ├── scripts/
 │   ├── verify_shapefile.py          # Data verification
 │   ├── run_baseline_simple.py       # Main simulation
 │   ├── generate_district_csvs.py    # Create district data
 │   ├── plot_baseline.py             # Static visualization
 │   ├── app_baseline.py              # Interactive dashboard
 │   └── baseline_dashboard.py        # Advanced dashboard (with maps)
 ├── outputs/
 │   ├── baseline_ensemble.csv        # Plan-level results
 │   ├── baseline_districts_plan_*.csv # District-level results
 │   ├── baseline_hist.png            # Histogram
 │   └── plan_assignments/            # JSON assignments
 ├── data/
 │   └── NC_VTD/
 │       └── NC_VTD.shp               # Shapefile (or use ../data/NC-shapefiles/)
 └── requirements.txt
```

---

## 📖 Output Files

### `baseline_ensemble.csv`
Summary of all 10 plans:
```csv
plan_id,dem_seats,rep_seats,dem_seat_share
1,8,6,0.5714
2,8,6,0.5714
3,8,6,0.5714
4,9,5,0.6429
...
```

### `baseline_districts_plan_<id>.csv`
Detailed results for each district:
```csv
plan_id,district_id,dem_votes,rep_votes,population,winner
1,0,158928,120786,686918,Democrat
1,1,166191,149550,678208,Democrat
1,2,129784,154682,690747,Republican
...
```

---

## 🧩 How It Works

### The Pipeline

1. **GerryChain ReCom Algorithm**
   - Generates random, valid redistricting plans
   - Maintains population balance (±5%)
   - Ensures all districts are contiguous

2. **Election Simulation**
   - Winner-take-all rule: `if D_votes > R_votes → Democrat`
   - Aggregates precinct votes by district
   - Counts seats won by each party

3. **Visualization**
   - Histogram of seat distributions
   - Interactive dashboard for plan exploration
   - District-level vote analysis

---

## 🎨 Dashboard Features

The Streamlit dashboard (`app_baseline.py`) provides:

- **Plan Selection** — Choose from 10 generated plans
- **Summary Statistics** — Average, min, max Democratic seats
- **Interactive Histogram** — Highlights selected plan
- **District Details** — Vote totals, population, winners for each district
- **Comparative Analysis** — See how selected plan compares to ensemble

To launch:
```bash
streamlit run scripts/app_baseline.py
```

Access at: `http://localhost:8501`

---

## ✅ Verification

To verify Steps 1-4 are complete:

```bash
# Check all outputs exist
ls outputs/baseline_ensemble.csv
ls outputs/baseline_hist.png
ls outputs/baseline_districts_plan_*.csv
ls outputs/plan_assignments/plan_*.json

# View results
cat outputs/baseline_ensemble.csv
```

---

## 🚫 Not Included Yet

Steps 1-4 do **NOT** implement:
- FRA multi-member district merging ❌
- Proportional seat allocation ❌
- Ranked-choice voting (RCV) ❌
- pRCV simulation ❌

These come in **Steps 5+**.

---

## 🔬 Technical Details

### Data Source
- **Shapefile:** North Carolina VTD (Voting Tabulation Districts)
- **Election:** 2008 Gubernatorial race (D vs R)
- **Population:** 2010 Census data
- **Total Population:** 9,535,483
- **Precincts:** 2,692

### Algorithm
- **Method:** ReCom (Recombination) from GerryChain
- **Constraints:**
  - Population deviation ≤ 5%
  - All districts contiguous
  - 14 districts total (matching NC congressional delegation size)

### Voting Rule
- **System:** Single-member plurality (winner-take-all)
- **Formula:** `winner = argmax(D_votes, R_votes)`

---

## 📚 Documentation

For detailed usage instructions, see:
- **[STEPS_1-4_USAGE.md](STEPS_1-4_USAGE.md)** — Complete usage guide
- **[fra_pipeline/README.md](fra_pipeline/README.md)** — Pipeline-specific docs

---

## 🛠️ Dependencies

```
geopandas
pandas
shapely
matplotlib
pyyaml
rtree
networkx
gerrychain
streamlit
```

Install all with:
```bash
pip install -r fra_pipeline/requirements.txt
```

---

## 🎉 Success!

If you can:
1. ✅ Run `verify_shapefile.py` without errors
2. ✅ Generate 10 plans with `run_baseline_simple.py`
3. ✅ View histogram with `plot_baseline.py`
4. ✅ Explore plans in Streamlit dashboard

**Then Steps 1-4 are complete!** 🎊

---

## 🚀 Next Steps

After validating Steps 1-4:

1. **Analyze baseline results**
   - Review seat distribution patterns
   - Identify competitive vs. safe districts
   - Document baseline proportionality metrics

2. **Proceed to Step 5+**
   - Implement FRA multi-member district merging
   - Add proportional RCV simulation
   - Compare FRA vs. baseline outcomes

3. **Extend analysis**
   - Generate larger ensembles (100+ plans)
   - Test different district sizes
   - Analyze geographic patterns

---

## 📞 Support & Issues

If you encounter issues:
1. Verify you're in `fra_pipeline/` directory
2. Check Python version (≥3.8 recommended)
3. Ensure shapefile path is correct
4. Confirm all dependencies installed

---

## 🏆 Project Status

| Step | Status | Description |
|------|--------|-------------|
| **1** | ✅ Complete | Project structure and setup |
| **2** | ✅ Complete | Shapefile verification |
| **3** | ✅ Complete | Baseline plan generation & simulation |
| **4** | ✅ Complete | Visualization and dashboard |
| **5+** | 🚧 Pending | FRA multi-member districts & pRCV |

---

## 📄 License

This project extends [GerryChain](https://github.com/mggg/GerryChain) for FRA simulation research.

---

## 🙏 Acknowledgments

Built using:
- **GerryChain** — Redistricting analysis library
- **GeoPandas** — Geospatial data processing
- **Streamlit** — Interactive dashboards

---

**Ready to explore multi-member proportional representation!** 🗳️
