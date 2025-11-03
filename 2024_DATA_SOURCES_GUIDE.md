# 📊 Guide: Updating to 2024 North Carolina Election Data

## 🎯 Summary

You're currently using **2008 data**. Here's how to update to **2024 data** for your FRA simulation.

---

## 📋 What You Need

To run your simulation with 2024 data, you need **two things**:

| Component | What It Is | Current (2008) | Target (2024) |
|-----------|-----------|----------------|---------------|
| **1. Shapefile** | Geographic boundaries of precincts | 2010 VTD shapefile | 2024 precinct shapefile |
| **2. Election Results** | Vote counts by precinct | 2008 Governor race | 2024 races (President, Governor, or House) |

---

## 🔍 Where to Find 2024 Data

### **Option 1: Official NC State Board of Elections (NCSBE)** ⭐ RECOMMENDED

#### **Election Results:**
✅ **Available NOW** for 2024 General Election (November 5, 2024)

**Direct Link:** https://www.ncsbe.gov/results-data/election-results/historical-election-results-data

**What's Available:**
- ✅ November 5, 2024 General Election (precinct-sorted data available)
- ✅ March 5, 2024 Primary (precinct-sorted data available)
- ⚠️ May 14, 2024 Primary (precinct data removed to protect ballot secrecy)

**File Format:** ZIP files containing CSV data

**What You'll Get:**
```
precinct_id, county, contest_name, party, votes_election_day,
votes_absentee, votes_early, votes_provisional, total_votes
```

**Races Available (November 5, 2024):**
- Presidential (Trump vs. Harris)
- Governor (Stein vs. Robinson)
- U.S. House (14 districts)
- U.S. Senate
- State Legislature
- Others

**Download Process:**
1. Go to: https://www.ncsbe.gov/results-data/election-results/historical-election-results-data
2. Scroll to "November 5, 2024 - General Election"
3. Click on "Precinct-sorted results folder format"
4. Download ZIP file
5. Extract CSV files

---

#### **Precinct Shapefiles:**
✅ **Available** (updated periodically)

**Direct Link:** https://dl.ncsbe.gov/?prefix=ShapeFiles/Precinct/

**What's Available:**
- Shapefiles by year (check for most recent: likely 2024 or 2023)
- KML files (alternative format)

**File Format:** `.shp`, `.shx`, `.dbf`, `.prj` (standard shapefile components)

**Download Process:**
1. Go to: https://dl.ncsbe.gov/?prefix=ShapeFiles/Precinct/
2. Look for the most recent year folder (e.g., `SBE_PRECINCTS_2024/`)
3. Download all files in the folder (usually `.zip` archive)
4. Extract to `fra_pipeline/data/NC_VTD_2024/`

---

### **Option 2: Redistricting Data Hub** ⭐ EASIEST (Merged Data)

**Why This is Better:**
- Shapefiles **already merged** with election results
- Pre-processed and cleaned
- Ready to use in GerryChain

**Website:** https://redistrictingdatahub.org/state/north-carolina/

**Status for 2024:**
⚠️ **Not yet available** (as of my search)
- They typically release data a few weeks/months after elections
- Check their "What's New" page: https://redistrictingdatahub.org/data/whats-new/

**What You'll Get (when available):**
- Single shapefile with election results already joined
- Columns like: `PRES24_D`, `PRES24_R`, `GOV24_D`, `GOV24_R`, `population`, `geometry`

**Download Process:**
1. Create free account at https://redistrictingdatahub.org/
2. Go to North Carolina state page
3. Search for "2024" or filter by "precinct and election results"
4. Download shapefile (`.shp` format)

**Estimated Availability:** January-March 2025

---

### **Option 3: Harvard Election Data Archive**

**Website:** https://projects.iq.harvard.edu/eda/home

**What They Have:**
- Historical election results at various levels
- Some precinct-level data
- Academic-quality datasets

**Status for 2024:** Check their website (data may lag by several months)

---

## 📦 What Data to Choose for Your Simulation

### **Recommended: Use Presidential or Governor Race**

| Race | Pros | Cons | Recommended? |
|------|------|------|--------------|
| **Presidential** | - High turnout<br>- Statewide contest<br>- No uncontested races | - Different from House elections<br>- National issues dominate | ✅ **BEST CHOICE** |
| **Governor** | - Statewide contest<br>- NC-specific issues<br>- What you used for 2008 | - Lower turnout than President | ✅ **GOOD CHOICE** |
| **U.S. House** | - Directly relevant to redistricting<br>- District-specific | - Some races uncontested<br>- Harder to project onto random maps | ⚠️ **COMPLEX** |
| **U.S. Senate** | - Statewide contest<br>- High turnout | - Only one race (less data) | ✅ **GOOD CHOICE** |

**My Recommendation:** Use **2024 Presidential race** (Trump vs. Harris)

**Why:**
- Highest turnout (most representative)
- Statewide race (works on any district map)
- No uncontested precincts
- Comparable to your current approach (statewide race)

---

## 🔧 How to Update Your Code

### **Step 1: Download the Data**

**Option A: NCSBE (Do It Yourself)**

1. Download precinct shapefile:
   ```bash
   # Download from https://dl.ncsbe.gov/?prefix=ShapeFiles/Precinct/
   # Extract to: fra_pipeline/data/NC_VTD_2024/
   ```

2. Download election results:
   ```bash
   # Download from NCSBE historical results page
   # Extract CSV files
   ```

3. Join them together:
   ```python
   # You'll need to write code to merge shapefile + CSV
   # Match on precinct_id or precinct_name
   ```

**Option B: Redistricting Data Hub (Easy Way)**

1. Wait for them to release 2024 data (check monthly)
2. Download pre-merged shapefile
3. Drop into `fra_pipeline/data/NC_VTD_2024/`

---

### **Step 2: Update Column Names in Code**

Your current code uses these columns:
```python
# Old (2008):
"EL08G_GV_D"   # 2008 Governor Democratic votes
"EL08G_GV_R"   # 2008 Governor Republican votes
"PL10AA_TOT"   # 2010 Census total population
```

For 2024, you'll need to find the new column names. Examples:

**From NCSBE raw data (if you merge yourself):**
```python
# Likely format:
"PRES_2024_DEM"  # Presidential Democratic votes
"PRES_2024_REP"  # Presidential Republican votes
"POPULATION"     # Population (from Census or estimates)
```

**From Redistricting Data Hub:**
```python
# Typical format:
"PRES24D"        # 2024 Presidential Democratic
"PRES24R"        # 2024 Presidential Republican
"G24D"           # 2024 Governor Democratic (if available)
"G24R"           # 2024 Governor Republican
"TOTPOP"         # Total population
```

---

### **Step 3: Modify Your Scripts**

#### **A. Update `verify_shapefile.py`**

Change the required columns:

```python
# OLD:
required_cols = ['EL08G_GV_D', 'EL08G_GV_R', 'PL10AA_TOT']

# NEW (example for Presidential):
required_cols = ['PRES24D', 'PRES24R', 'TOTPOP']
```

#### **B. Update `run_baseline_simple.py`**

Change the column references in the graph builder:

```python
# OLD (lines 60-62):
graph.nodes[node]["population"] = int(row.get("PL10AA_TOT", 0))
graph.nodes[node]["votes_dem"] = int(row.get("EL08G_GV_D", 0))
graph.nodes[node]["votes_rep"] = int(row.get("EL08G_GV_R", 0))

# NEW (example):
graph.nodes[node]["population"] = int(row.get("TOTPOP", 0))
graph.nodes[node]["votes_dem"] = int(row.get("PRES24D", 0))
graph.nodes[node]["votes_rep"] = int(row.get("PRES24R", 0))
```

#### **C. Update Shapefile Path**

```python
# OLD:
shp_path = base_dir / "data" / "NC_VTD" / "NC_VTD.shp"

# NEW:
shp_path = base_dir / "data" / "NC_VTD_2024" / "NC_VTD_2024.shp"
```

---

### **Step 4: Check District Count**

**IMPORTANT:** North Carolina still has **14 congressional districts** in 2024.

✅ No change needed in your code (still use `num_districts=14`)

**Note:** NC used a **new district map** for 2024 (drawn in 2023), but you're generating random maps anyway, so this doesn't affect your simulation.

---

## 📊 Expected 2024 Results (Preliminary)

Based on the 2024 election:

| Metric | 2024 Result |
|--------|-------------|
| **Presidential (NC)** | Trump won NC with ~51% |
| **Governor** | Democrat Josh Stein won |
| **U.S. House** | Republicans won ~10/14 seats |

**Your simulation should show:**
- If using Presidential votes: Slight Republican lean (~49% Dem, 51% Rep)
- If using Governor votes: Democratic lean (Stein won)

This creates an interesting comparison to your 2008 baseline (which had Dem lean).

---

## 🔄 Migration Checklist

Use this to track your progress:

- [ ] **1. Download 2024 precinct shapefile**
  - Source: NCSBE or Redistricting Data Hub
  - Location: `fra_pipeline/data/NC_VTD_2024/`

- [ ] **2. Download 2024 election results**
  - Race chosen: _________ (Presidential recommended)
  - Format: CSV or pre-merged shapefile

- [ ] **3. Identify column names**
  - Dem votes column: _________
  - Rep votes column: _________
  - Population column: _________

- [ ] **4. Update code files**
  - [ ] `verify_shapefile.py` (required_cols)
  - [ ] `run_baseline_simple.py` (graph.nodes assignments)
  - [ ] `generate_district_csvs.py` (column references)

- [ ] **5. Test verification**
  - [ ] Run `python scripts/verify_shapefile.py`
  - [ ] Check output for correct totals

- [ ] **6. Generate new baseline**
  - [ ] Run `python scripts/run_baseline_simple.py`
  - [ ] Verify 10 plans generated
  - [ ] Check vote totals match shapefile

- [ ] **7. Compare to 2008 baseline**
  - [ ] Note differences in vote share
  - [ ] Note differences in seat distribution
  - [ ] Document changes in methodology

---

## ⚠️ Potential Issues & Solutions

### **Issue 1: Column Names Don't Match**

**Problem:** NCSBE data has different column naming than you expect

**Solution:**
1. Open shapefile in QGIS or ArcGIS to inspect column names
2. Or use Python:
   ```python
   import geopandas as gpd
   gdf = gpd.read_file("data/NC_VTD_2024/NC_VTD_2024.shp")
   print(gdf.columns)
   ```

### **Issue 2: Precinct IDs Don't Match**

**Problem:** Shapefile and CSV use different precinct identifiers

**Solution:**
- Use Redistricting Data Hub (pre-merged) instead
- Or manually join using county + precinct name
- Use `pandas.merge()` with fuzzy matching if needed

### **Issue 3: Missing Precincts**

**Problem:** Some precincts in shapefile don't have vote data

**Solution:**
- Filter out precincts with zero votes
- Or use default value (0) as current code does

### **Issue 4: Population Data Missing**

**Problem:** 2024 shapefile doesn't have population column

**Solution:**
- Use 2020 Census data (most recent)
- Download from: https://www.census.gov/data/datasets/2020/dec/redistricting-data.html
- Or use population estimates from Redistricting Data Hub

---

## 📚 Additional Resources

### **1. GerryChain Documentation**
- Working with shapefiles: https://gerrychain.readthedocs.io/en/latest/user/install.html

### **2. GeoPandas (for merging data)**
```python
import geopandas as gpd
import pandas as pd

# Load shapefile
gdf = gpd.read_file("shapefile.shp")

# Load election results CSV
results = pd.read_csv("results.csv")

# Merge
merged = gdf.merge(results, on="precinct_id")

# Save
merged.to_file("merged_shapefile.shp")
```

### **3. QGIS (free GIS software)**
- Download: https://qgis.org/
- Use to inspect and join shapefiles visually

---

## 🎯 Timeline Estimate

| Task | Estimated Time |
|------|----------------|
| Find and download data | 1-2 hours |
| Inspect and identify columns | 30 minutes |
| Update code | 1 hour |
| Test and debug | 1-2 hours |
| **Total** | **3-6 hours** |

**Speed up:** Wait for Redistricting Data Hub to release pre-merged data (could save 2-3 hours)

---

## ✅ Recommendation

### **Short Term (Now):**
1. ✅ **Stick with 2008 data** for initial FRA comparison
2. ✅ Complete Steps 1-4 and Steps 5+ with 2008 data
3. ✅ Get your methodology working

### **Medium Term (January-March 2025):**
1. ⏳ **Wait for Redistricting Data Hub** to release NC 2024 data
2. ⏳ Download pre-merged shapefile
3. ⏳ Update code with minimal changes

### **Long Term (Optional):**
1. 🔄 **Run both 2008 and 2024** simulations
2. 🔄 Compare how results differ across elections
3. 🔄 Demonstrate that FRA reduces winner's bonus in both contexts

---

## 📝 What to Tell Your Professor

**Option 1: Stay with 2008**
> "We're using 2008 data because it provides a complete, well-documented baseline. The Redistricting Data Hub will release cleaned 2024 data in early 2025, at which point we can validate our methodology against current election results. Our approach remains valid regardless of which election year we use."

**Option 2: Update to 2024**
> "We're updating to 2024 presidential election data to ensure our analysis reflects the most current voter preferences. This requires merging NCSBE precinct shapefiles with election results, which we're currently processing. The methodology remains identical to our 2008 baseline."

**Option 3: Do Both**
> "We'll first complete the FRA comparison using 2008 data (which is fully processed), then replicate the analysis with 2024 data once Redistricting Data Hub releases cleaned files. This dual-timeline approach demonstrates that our findings are robust across different elections and political contexts."

---

## 🔗 Quick Links

| Resource | URL | Status |
|----------|-----|--------|
| NCSBE Election Results | https://www.ncsbe.gov/results-data/election-results/historical-election-results-data | ✅ 2024 Available |
| NCSBE Shapefiles | https://dl.ncsbe.gov/?prefix=ShapeFiles/Precinct/ | ✅ Available |
| Redistricting Data Hub | https://redistrictingdatahub.org/state/north-carolina/ | ⏳ 2024 Coming Soon |
| NC OneMap | https://www.nconemap.gov/datasets/nconemap::voting-precincts/about | ✅ Available |
| Harvard Election Archive | https://projects.iq.harvard.edu/eda/home | ⏳ Check Later |

---

## 💡 Final Advice

**My recommendation:**

✅ **Finish your FRA project with 2008 data first**, then update to 2024 if time permits.

**Why:**
1. 2008 data works perfectly and is fully tested
2. Methodology is identical regardless of year
3. Redistricting Data Hub will make 2024 update trivial (pre-merged files)
4. You can demonstrate robustness by running both later

**The science is in the methodology, not the specific election year.** ✅

---

**Need help with the actual data download and code updates? Let me know and I can walk you through it step-by-step!** 📊
