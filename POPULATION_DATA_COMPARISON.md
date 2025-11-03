# 📊 Population Data Comparison: 2008 vs. 2024

## 🎯 **Quick Answer**

### **Does the 2008 data have population?**
✅ **YES! The 2008 data HAS population data**

### **Does the 2024 data have population?**
❌ **NO! The 2024 data DOES NOT have population data**

---

## 📋 **Detailed Comparison**

| Feature | 2008 Data | 2024 Data |
|---------|-----------|-----------|
| **Shapefile** | `data/NC_VTD/NC_VTD.shp` | `new_data/.../nc_2024_gen_all_prec.shp` |
| **Precincts** | 2,692 | 2,658 |
| **Total Columns** | 88 | 424 |
| **Population Columns** | ✅ **5 columns** | ❌ **0 columns** |
| **Election Data** | ✅ 2008 Governor | ✅ 2024 Pres/Gov/etc. |
| **Ready to Use** | ✅ **YES** | ❌ **NO (needs population)** |

---

## ✅ **2008 Data: Population Columns**

The 2008 shapefile includes **5 population-related columns**:

### **1. PL10AA_TOT** ⭐ **THIS IS WHAT WE USE**
- **Source:** 2010 Census (P.L. 94-171 Redistricting File)
- **Definition:** Total population (all ages)
- **Total:** 9,535,483 people
- **Used for:** Redistricting population balance constraints
- **Column name in code:** `"PL10AA_TOT"`

### **2. TOTPOP**
- **Source:** 2010 Census
- **Definition:** Total population (duplicate of PL10AA_TOT)
- **Total:** 9,535,483 people
- **Note:** Same as PL10AA_TOT, just different column name

### **3. PL10VA_TOT**
- **Source:** 2010 Census
- **Definition:** Voting Age Population (18+ years old)
- **Total:** 7,253,848 people
- **Used for:** Voting Rights Act analysis (not used in our simulation)

### **4. BPOP**
- **Source:** 2010 Census
- **Definition:** Black Population
- **Total:** 2,048,628 people
- **Used for:** Demographic analysis / VRA compliance

### **5. nBPOP**
- **Source:** 2010 Census
- **Definition:** Non-Black Population
- **Total:** 7,486,855 people
- **Check:** BPOP + nBPOP = 9,535,483 ✅

---

## ❌ **2024 Data: No Population Columns**

The 2024 shapefile has **NO population-related columns**.

### **What I Searched For:**
- ❌ `TOTPOP` — NOT FOUND
- ❌ `PL10AA_TOT` — NOT FOUND
- ❌ `PL20AA_TOT` — NOT FOUND (2020 Census equivalent)
- ❌ `POPULATION` — NOT FOUND
- ❌ `POP` — NOT FOUND
- ❌ Any column with "POP" or "TOT" in the name — NONE FOUND

### **Why It's Missing:**

From the Redistricting Data Hub README:

> "Data were received from the NCSBE. Data were pivoted and then renamed to the column structure used in the file. Data were queried to federal, statewide, and state legislative contests."

**Translation:** They focused on election results only, not demographic data.

---

## 🔍 **Why Population Data Matters**

### **What GerryChain ReCom Needs:**

1. **Population Balance:**
   ```python
   # From run_baseline_simple.py, line 144
   population_constraint = within_percent_of_ideal_population(initial_partition, 0.05)
   ```
   - Each district must have approximately equal population
   - Target: 9,535,483 ÷ 14 = 681,106 people per district
   - Allowed range: 647,051 to 715,161 (±5%)

2. **Initial Partition Creation:**
   ```python
   # From run_baseline_simple.py, line 100-107
   assignment = recursive_tree_part(
       graph,
       range(num_districts),
       ideal_population,    # ← NEEDS population data
       "population",        # ← NEEDS population column
       0.05,
       1
   )
   ```

3. **Every Node in Graph:**
   ```python
   # From run_baseline_simple.py, line 60
   graph.nodes[node]["population"] = int(row.get("PL10AA_TOT", 0))
   #                                             ↑
   #                                  MUST exist in shapefile
   ```

**Without population:** The code will crash or assign population = 0 to every precinct, making redistricting impossible.

---

## 📊 **What Each Dataset Can Do**

### **2008 Data (Current):**

✅ **Can do everything:**
- ✅ Load shapefile
- ✅ Build GerryChain graph
- ✅ Create initial partition
- ✅ Run ReCom to generate random maps
- ✅ Balance districts by population (±5%)
- ✅ Simulate elections with 2008 gubernatorial votes
- ✅ Generate all outputs (CSVs, plots, dashboard)

**Status:** 🟢 **FULLY FUNCTIONAL**

---

### **2024 Data (Downloaded):**

✅ **Can do:**
- ✅ Load shapefile
- ✅ View 2024 election results
- ✅ Analyze statewide vote totals

❌ **CANNOT do (without population):**
- ❌ Build GerryChain graph with population attributes
- ❌ Create initial partition (recursive_tree_part fails)
- ❌ Run ReCom (population constraint fails)
- ❌ Balance districts (no population to balance)
- ❌ Generate valid random maps
- ❌ Complete the simulation

**Status:** 🔴 **BLOCKED — Cannot run simulation**

---

## 🛠️ **How to Fix 2024 Data**

### **Option 1: Merge 2020 Census Population** ⭐ RECOMMENDED

**Steps:**
1. Download 2020 Census VTD-level population data for NC
2. Match precincts between census data and your 2024 shapefile
3. Join population column to 2024 shapefile
4. Save as new shapefile with both election results AND population

**Estimated Time:** 3-5 hours (first time), 1-2 hours (if I guide you)

**Sources for 2020 Census Data:**
- **NCSBE:** https://www.ncsbe.gov/results-data/voting-maps-redistricting
  - Look for precinct shapefiles with 2020 population
- **U.S. Census Bureau:** https://www.census.gov/programs-surveys/decennial-census/about/rdo/summary-files.html
  - Download P.L. 94-171 Redistricting Data for NC
- **Redistricting Data Hub:** Email info@redistrictingdatahub.org
  - Ask for NC 2024 data with population already merged

---

### **Option 2: Use Different 2024 File**

Check if the **congressional file** has population:

```bash
cd new_data/nc_2024_gen_prec/nc_2024_gen_cong_prec/
# Inspect nc_2024_gen_cong_prec.shp
```

**Why this might work:** Congressional files are often used for redistricting, so they may include population data.

**Trade-off:** This file has pre-existing congressional district assignments, which may bias your random map generation.

---

### **Option 3: Stick with 2008**

**Advantages:**
- ✅ Works perfectly right now
- ✅ No additional work needed
- ✅ Focus on getting FRA comparison done
- ✅ Can update to 2024 later as validation

**Disadvantages:**
- ⚠️ Data is 16 years old
- ⚠️ Different political landscape (Obama era vs. Trump/Biden era)

---

## 🎯 **Recommendation**

### **For Your Professor:**

**SHORT ANSWER:**
> "Yes, the 2008 data has population (2010 Census). The 2024 data does not include population, which is critical for redistricting constraints. I'm proceeding with 2008 data to complete the baseline and FRA analysis, with plans to validate using 2024 data once I merge 2020 Census population."

**MEDIUM ANSWER:**
> "Our current 2008 dataset (from VEST/Harvard Election Lab) includes both election results AND 2010 Census population data in a single shapefile. The 2024 dataset from Redistricting Data Hub includes comprehensive election results but lacks population data, which is essential for GerryChain's population balance constraints. Since the methodology is identical regardless of election year, I'm completing the analysis with the fully-integrated 2008 data first, then will update to 2024 as a robustness check."

---

## 📋 **Summary Table**

| Requirement | 2008 Data | 2024 Data | Solution for 2024 |
|-------------|-----------|-----------|-------------------|
| **Precinct Boundaries** | ✅ YES | ✅ YES | — |
| **Election Results** | ✅ YES (2008 Gov) | ✅ YES (2024 Pres/Gov) | — |
| **Population (2010 Census)** | ✅ YES | ❌ NO | Merge 2020 Census |
| **Voting Age Population** | ✅ YES | ❌ NO | Merge 2020 Census |
| **Demographic Data** | ✅ YES | ❌ NO | Merge 2020 Census |
| **Ready for GerryChain** | ✅ YES | ❌ NO | Merge population first |
| **Can Run Simulation** | ✅ YES | ❌ NO | Fix population issue |

---

## 🔧 **Code Comparison**

### **What Works with 2008 Data:**

```python
# From run_baseline_simple.py, line 60
graph.nodes[node]["population"] = int(row.get("PL10AA_TOT", 0))
#                                              ↑
#                                         ✅ EXISTS in 2008 shapefile
```

**Result:** ✅ Code runs successfully

---

### **What Fails with 2024 Data:**

```python
# Same line, but with 2024 shapefile
graph.nodes[node]["population"] = int(row.get("PL10AA_TOT", 0))
#                                              ↑
#                                         ❌ DOES NOT EXIST in 2024 shapefile
#                                         Returns 0 for every precinct!
```

**Result:**
- ❌ Every precinct gets population = 0
- ❌ `recursive_tree_part` cannot balance by population
- ❌ ReCom cannot enforce population constraints
- ❌ Simulation fails or produces invalid results

---

## ✅ **Bottom Line**

| Question | Answer |
|----------|--------|
| **Does 2008 data have population?** | ✅ **YES** (PL10AA_TOT from 2010 Census) |
| **Does 2024 data have population?** | ❌ **NO** (must be merged separately) |
| **Can we use 2008 data right now?** | ✅ **YES** (fully functional) |
| **Can we use 2024 data right now?** | ❌ **NO** (blocked by missing population) |
| **Should we stick with 2008?** | ✅ **YES** (recommended for now) |
| **Can we upgrade to 2024 later?** | ✅ **YES** (after merging population data) |

---

## 🚀 **Action Items**

### **Immediate (Today):**
✅ **Keep using 2008 data** — It works perfectly

### **Short Term (This Week):**
✅ **Complete Steps 1-4 and FRA with 2008 data**

### **Medium Term (Next Month):**
⏳ **If you want 2024:**
1. Download 2020 Census population for NC VTDs
2. Merge with 2024 election shapefile
3. Update 3 column names in code
4. Rerun simulation as validation

### **Long Term (Optional):**
🔄 **Run both 2008 and 2024** to show results are robust across elections

---

**Conclusion:** Your 2008 data is COMPLETE and READY TO USE. The 2024 data is EXCELLENT but INCOMPLETE (missing population). Finish with 2008 first! ✅
