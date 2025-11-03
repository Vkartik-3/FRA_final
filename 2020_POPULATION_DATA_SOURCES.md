# 📊 Sources for 2020 Census Population Data (North Carolina)

## 🎯 Goal
Get 2020 Census population data at the VTD (Voting Tabulation District) / precinct level for North Carolina to merge with your 2024 election data.

---

## ⭐ **RECOMMENDED SOURCES** (Easiest to Hardest)

---

## **Option 1: Redistricting Data Hub** ⭐⭐⭐ **EASIEST**

### **What You Get:**
- Pre-merged shapefile with 2020 Census population AND election results
- VTD/precinct level geography
- Ready to use in GerryChain

### **Download:**
1. **Website:** https://redistrictingdatahub.org/state/north-carolina/
2. **Create account:** Free registration required
3. **Search for:** "2020 Census" or "PL 94-171" in the North Carolina data portal
4. **Filter by:** "Precinct and Election Results" or "Census Data"
5. **Download:** Shapefile format (.shp)

### **What to Look For:**
Dataset name might be something like:
- "North Carolina 2020 Census PL 94-171 VTD Shapefile"
- "NC 2020 Redistricting Data with VTD Boundaries"

### **Columns You'll Get:**
- `TOTPOP` or `PL20_POP` — Total population (2020 Census)
- `VAP` or `CVAP` — Voting Age Population
- Demographic breakdowns (race, ethnicity)
- Geographic identifiers (GEOID, VTD name, County)

### **Pros:**
- ✅ Already merged and cleaned
- ✅ Trusted source (used by researchers and courts)
- ✅ Shapefile format (ready for geopandas)
- ✅ Free

### **Cons:**
- ⚠️ Requires registration
- ⚠️ May not have 2024 election data yet (you'd merge separately)

### **Status:** 🟢 **Best option if available**

---

## **Option 2: MGGG / VEST (Harvard Dataverse)** ⭐⭐⭐ **VERY GOOD**

### **What You Get:**
- Precinct shapefiles with 2020 election results
- Includes 2020 Census population data
- Academic-quality, peer-reviewed

### **Download:**

#### **A. VEST 2020 Precinct Shapefiles**
- **Website:** https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/XPW7T7
- **What it is:** Voting and Election Science Team's official 2020 precinct dataset
- **Format:** ESRI Shapefile
- **Coverage:** All 50 states including North Carolina

**Steps:**
1. Go to Harvard Dataverse link above
2. Look for "North Carolina" dataset
3. Download ZIP file
4. Extract shapefile

#### **B. MGGG States GitHub**
- **Website:** https://github.com/mggg-states
- **NC Repository:** https://github.com/mggg-states/NC-shapefiles
- **Note:** Currently has 2008-2016 data, check if 2020 has been added

### **Columns You'll Get:**
- `TOTPOP` — Total population
- `VAP` — Voting Age Population
- `BVAP`, `HVAP`, `WVAP` — Demographic voting age populations
- Election results (may be 2020 general election)

### **Pros:**
- ✅ High quality, academic standard
- ✅ Well-documented
- ✅ Free, no registration
- ✅ Trusted by MGGG (redistricting experts)

### **Cons:**
- ⚠️ May have 2020 election data, not 2024
- ⚠️ You'd need to join 2024 election results separately

### **Status:** 🟢 **Excellent option**

---

## **Option 3: NC State Board of Elections (NCSBE)** ⭐⭐ **GOOD**

### **What You Get:**
- Official NC precinct shapefiles
- May include 2020 Census population
- Most up-to-date precinct boundaries

### **Download:**
1. **Website:** https://www.ncsbe.gov/results-data/voting-maps-redistricting
2. **Look for:** "Precinct Shapefiles" section
3. **Find:** Files dated 2020 or later with population data
4. **Download:** ZIP file with shapefiles

**OR**

**Direct FTP:** https://dl.ncsbe.gov/?prefix=ShapeFiles/Precinct/

**Steps:**
1. Browse folders by year (look for 2020, 2021, 2022, etc.)
2. Download most recent precinct shapefile
3. Check if it includes population columns

### **Columns You Might Get:**
- Depends on the file version
- May have `TOTPOP`, `POP2020`, or similar
- May need to join Census data separately

### **Pros:**
- ✅ Official state source
- ✅ Most current precinct boundaries
- ✅ Free, no registration

### **Cons:**
- ⚠️ May not include population (just geography)
- ⚠️ May need to merge Census data yourself
- ⚠️ Need to verify which files have population

### **Status:** 🟡 **Check first, may need additional work**

---

## **Option 4: NC OSBM (Office of State Budget and Management)** ⭐⭐ **GOOD**

### **What You Get:**
- 2020 Census redistricting data
- VTD-level population
- Official state data portal

### **Download:**
1. **Website:** https://linc.osbm.nc.gov/
2. **Search for:** "2020 Census Redistricting"
3. **Filter by:** VTD or Voting District level
4. **Download:** CSV or shapefile format

**Direct Link to 2020 Redistricting Data:**
https://linc.osbm.nc.gov/explore/dataset/2020-census-redistricting/

### **What to Expect:**
- Population by VTD/precinct
- Demographic breakdowns
- May be in CSV format (need to join to shapefile)

### **Pros:**
- ✅ Official state source
- ✅ 2020 Census data
- ✅ Free

### **Cons:**
- ⚠️ May be CSV only (need to join to geography)
- ⚠️ Portal interface may be complex
- ⚠️ Requires manual data processing

### **Status:** 🟡 **Good data, may need work to integrate**

---

## **Option 5: U.S. Census Bureau (Direct)** ⭐ **TECHNICAL**

### **What You Get:**
- Official 2020 Census P.L. 94-171 Redistricting Data
- VTD-level population
- Most authoritative source

### **Download:**

#### **A. TIGER/Line Shapefiles (Geography Only)**
- **Website:** https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
- **What:** 2020 VTD boundaries for North Carolina
- **Format:** Shapefile
- **Note:** Does NOT include population, just geography

**Steps:**
1. Go to TIGER/Line Shapefiles page
2. Select "2020" year
3. Select "Voting Districts" layer
4. Select "North Carolina"
5. Download ZIP

**File you'll get:** `tl_2020_37_vtd20.zip`

#### **B. P.L. 94-171 Data (Population Only)**
- **Website:** https://www.census.gov/programs-surveys/decennial-census/about/rdo/summary-files.html
- **What:** 2020 Census redistricting data files
- **Format:** Summary File (complex text format)

**Steps:**
1. Go to P.L. 94-171 summary files page
2. Download North Carolina file
3. Extract population tables
4. **WARNING:** Very complex format, requires processing

#### **C. Data.Census.Gov (Easiest Census Option)**
- **Website:** https://data.census.gov/
- **Search:** "P1 Total Population" + "North Carolina" + "Voting District"
- **Download:** CSV with GEOID and population
- **Then:** Join to TIGER/Line shapefile using GEOID

### **Pros:**
- ✅ Official, authoritative source
- ✅ Complete 2020 Census data
- ✅ Free

### **Cons:**
- ❌ Requires joining geography + population (2 separate files)
- ❌ Complex data formats
- ❌ Requires technical GIS skills
- ❌ Time-consuming

### **Status:** 🔴 **Advanced users only**

---

## **Option 6: Email Redistricting Data Hub** ⭐⭐⭐ **LAZY BUT EFFECTIVE**

### **What to Do:**
Send an email asking for help:

**To:** info@redistrictingdatahub.org

**Subject:** Request for NC 2024 Election Data with 2020 Population

**Email Template:**
```
Hello,

I'm a researcher working on redistricting analysis for North Carolina.

I recently downloaded your NC 2024 General Election precinct-level
results (nc_2024_gen_all_prec), which has excellent election data
but lacks 2020 Census population columns needed for GerryChain
redistricting simulation.

Do you have a version of this dataset that includes 2020 Census
population data (TOTPOP, VAP, etc.) merged with the 2024 election
results?

Alternatively, could you point me to your NC 2020 Census PL 94-171
VTD-level dataset that I could merge myself?

Thank you!
```

### **Expected Response Time:** 1-5 business days

### **Pros:**
- ✅ Expert help
- ✅ May get exactly what you need
- ✅ Free

### **Cons:**
- ⏳ Requires waiting for response
- ⚠️ No guarantee they have it ready

### **Status:** 🟡 **Worth trying in parallel**

---

## 📋 **Quick Comparison Table**

| Source | Ease | Quality | Format | Has Population? | Has 2024 Elections? | Time |
|--------|------|---------|--------|----------------|-------------------|------|
| **Redistricting Data Hub** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Shapefile | ✅ | ❓ Check | 30 min |
| **VEST/Harvard** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Shapefile | ✅ | ❌ (2020 only) | 30 min |
| **NCSBE** | ⭐⭐ | ⭐⭐⭐⭐ | Shapefile | ❓ | ✅ | 1-2 hrs |
| **NC OSBM** | ⭐⭐ | ⭐⭐⭐⭐ | CSV/Table | ✅ | ❌ | 2-3 hrs |
| **Census Bureau** | ⭐ | ⭐⭐⭐⭐⭐ | Multiple | ✅ | ❌ | 4-6 hrs |
| **Email RDH** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Shapefile | ✅ | ✅ | 1-5 days |

---

## 🎯 **MY RECOMMENDATION**

### **Step 1: Try Redistricting Data Hub First** (30 minutes)
1. Go to https://redistrictingdatahub.org/state/north-carolina/
2. Register (free)
3. Search for "2020 Census" or "PL 94-171"
4. Download shapefile if available

### **Step 2: If not there, try VEST** (30 minutes)
1. Go to https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/XPW7T7
2. Download NC 2020 precinct shapefile
3. Check if it has TOTPOP column
4. If yes, use this for population and merge with your 2024 election data

### **Step 3: Email RDH in parallel** (5 minutes)
While trying the above, send the email to info@redistrictingdatahub.org

### **Step 4: If all else fails, use NCSBE + Census** (2-4 hours)
1. Download NCSBE precinct shapefile
2. Download Census population data from data.census.gov
3. Join using GEOID or precinct name

---

## 🛠️ **How to Merge Population with Your 2024 Data**

Once you get population data, here's how to merge it:

### **Scenario A: Population is in a shapefile**

```python
import geopandas as gpd

# Load your 2024 election data (no population)
election_gdf = gpd.read_file("new_data/.../nc_2024_gen_all_prec.shp")

# Load 2020 population data (different shapefile)
pop_gdf = gpd.read_file("nc_2020_population.shp")

# Option 1: Spatial join (if geographies match)
merged = gpd.sjoin(election_gdf, pop_gdf[['TOTPOP', 'geometry']],
                   how='left', predicate='intersects')

# Option 2: Attribute join (if IDs match)
merged = election_gdf.merge(pop_gdf[['GEOID', 'TOTPOP']],
                            on='GEOID', how='left')

# Save
merged.to_file("nc_2024_with_population.shp")
```

### **Scenario B: Population is in a CSV**

```python
import geopandas as gpd
import pandas as pd

# Load your 2024 election shapefile
election_gdf = gpd.read_file("new_data/.../nc_2024_gen_all_prec.shp")

# Load population CSV
pop_df = pd.read_csv("nc_2020_population.csv")

# Merge on common ID (GEOID, VTD code, or precinct name)
merged = election_gdf.merge(pop_df[['GEOID', 'TOTPOP']],
                            left_on='UNIQUE_ID',
                            right_on='GEOID',
                            how='left')

# Save
merged.to_file("nc_2024_with_population.shp")
```

### **Scenario C: Use same VTD boundaries, just copy population**

```python
import geopandas as gpd

# Load 2020 shapefile with population
pop_gdf = gpd.read_file("nc_2020_census_vtd.shp")

# Load 2024 election results (CSV from NCSBE)
import pandas as pd
election_df = pd.read_csv("nc_2024_results.csv")

# Join election results to 2020 geography
merged = pop_gdf.merge(election_df, on='VTD_CODE', how='left')

# Save
merged.to_file("nc_2024_with_population.shp")
```

---

## ✅ **Verification Checklist**

After merging, verify your data:

```python
import geopandas as gpd

gdf = gpd.read_file("nc_2024_with_population.shp")

print("✅ Verification:")
print(f"   Precincts: {len(gdf)}")
print(f"   Has TOTPOP: {'TOTPOP' in gdf.columns}")
print(f"   Total Population: {gdf['TOTPOP'].sum():,}")
print(f"   Has 2024 votes: {'G24PREDHAR' in gdf.columns}")
print(f"   Dem votes: {gdf['G24PREDHAR'].sum():,}")
print(f"   Rep votes: {gdf['G24PRERTRU'].sum():,}")
```

**Expected output:**
```
✅ Verification:
   Precincts: 2,658
   Has TOTPOP: True
   Total Population: ~10,400,000  (NC 2020 Census)
   Has 2024 votes: True
   Dem votes: 2,713,609
   Rep votes: 2,896,941
```

---

## 🎓 **What to Tell Your Professor**

**While working on it:**
> "I'm obtaining 2020 Census population data from [source name] to merge with the 2024 election results. This will allow us to run the simulation with current election data while maintaining proper redistricting constraints. Estimated time: [X hours/days]."

**If it's taking too long:**
> "The 2024 data requires merging multiple sources (population + elections), which is taking longer than expected. To keep the project on track, I'm proceeding with the complete 2008 dataset, with plans to validate using 2024 data as a future extension."

---

## 📞 **Need Help?**

If you get stuck:
1. Check if files have matching ID columns (GEOID, VTD_CODE, UNIQUE_ID)
2. Verify coordinate systems match (both should be same CRS)
3. Use `gdf.explore()` to visually check if geometries align
4. Ask me for help with the merge code!

---

## 🚀 **Next Steps**

1. ✅ **Choose a source** (Redistricting Data Hub recommended)
2. ✅ **Download population data**
3. ✅ **Verify it has TOTPOP column**
4. ✅ **Merge with 2024 election data**
5. ✅ **Update 3 column names in code**
6. ✅ **Run simulation with 2024 data**

**Good luck!** 🎯
