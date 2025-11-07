# FRA Dashboard - User Guide

## Overview

This interactive Streamlit dashboard visualizes the difference between traditional single-member districts (winner-take-all) and Fair Representation Act (FRA) multi-member super-districts (proportional representation) for North Carolina's 2024 election data.

## Quick Start

### 1. Launch the Dashboard

```bash
cd fra_pipeline
source env/bin/activate
streamlit run scripts/dashboard_fra.py
```

The dashboard will open automatically in your default web browser at `http://localhost:8501`

### 2. Navigate the Interface

The dashboard has two main modes:
- **Baseline Plan**: View 14 single-member districts with winner-take-all
- **FRA Plan**: View 3 multi-member super-districts with proportional representation

Switch between modes using the radio buttons in the sidebar.

## Dashboard Components

### 🎛️ Sidebar Controls

#### Plan Selection
- **Radio Buttons**: Choose between "Baseline Plan" or "FRA Plan"

#### District/Super-District Selection
- **Baseline Mode**: Select any of the 14 districts (0-13)
  - Shows: Winner, vote totals, population, margin
- **FRA Mode**: Select any of the 3 super-districts (0-2)
  - Shows: Total seats, seat allocation, vote share, population

#### Map Options
- **Show District Borders**: Toggle district boundary visibility

### 📊 Main Dashboard Sections

#### 1. Key Metrics (Top Row)

**Baseline Mode:**
- Total Districts: 14
- Democratic Seats (winner-take-all count)
- Republican Seats (winner-take-all count)
- Statewide Dem Vote %
- Statewide Rep Vote %
- Proportionality Gap (shown as warning)

**FRA Mode:**
- Total Super-Districts: 3
- Total Seats: 14
- Democratic Seats (proportional allocation)
- Republican Seats (proportional allocation)
- Statewide vote percentages
- Proportionality Gap (shown as success)

#### 2. Interactive Map (Left Column)

**Features:**
- **Tooltips**: Hover over any precinct to see:
  - Precinct ID
  - District/Super-district assignment
  - Democratic votes
  - Republican votes
  - Population
- **Color Coding**:
  - Baseline: 14 distinct colors for each district
  - FRA: 3 distinct colors (red, teal, yellow) for super-districts
- **Selection Highlighting**: When you select a district/super-district in the sidebar, the map highlights it

**Map Controls:**
- Zoom in/out with mouse wheel or + / - buttons
- Pan by clicking and dragging
- Reset view with home button

#### 3. Seat Allocation Chart (Right Column, Top)

**Compares three metrics:**
1. **Baseline (Winner-Take-All)**: Actual seats won under single-member districts
2. **FRA (Proportional)**: Seats allocated proportionally in multi-member districts
3. **Statewide Vote Share**: What perfectly proportional representation would look like

**Colors:**
- Blue bars: Democratic
- Red bars: Republican

**Key Insight**: Shows how close each system comes to proportional representation.

#### 4. Vote Distribution Histogram (Right Column, Bottom)

**Shows:**
- Distribution of Democratic vote share across districts/super-districts
- Two overlaid histograms:
  - Blue: Baseline districts
  - Red: FRA super-districts
- Dashed vertical lines showing mean vote shares

**Key Insight**: FRA tends to have fewer extreme vote shares (less gerrymandering potential).

#### 5. Detailed Results Table

**Baseline Mode Columns:**
- District ID
- Dem Votes
- Rep Votes
- Population
- Winner
- Margin (votes)
- Dem % (vote share)

**FRA Mode Columns:**
- Super-District ID
- Total Seats
- Dem Votes
- Rep Votes
- Dem Seats
- Rep Seats
- Dem % (vote share)
- Population

**Features:**
- Sortable columns (click header)
- Searchable
- Full precision data

#### 6. Interpretation Section (Bottom)

**Three expandable explanations:**

1. **How does FRA reduce winner-take-all distortion?**
   - Explains the proportionality gap
   - Compares baseline vs FRA with actual numbers
   - Shows why FRA produces fairer outcomes

2. **How does gluing change the geometry?**
   - Explains the gluing algorithm
   - Shows what changes (geography, representation)
   - Shows what stays the same (precincts, total seats)

3. **Why does multi-member PR give different outcomes?**
   - Provides concrete example with 5-seat super-district
   - Compares winner-take-all vs proportional allocation
   - Shows the actual North Carolina results

## Understanding the Visualizations

### Proportionality Gap

The **proportionality gap** measures how far the seat share deviates from the vote share:

```
Gap = |Seat Share - Vote Share| × 100%
```

**Example:**
- Statewide Dem vote share: 48.4%
- Baseline Dem seat share: 35.7% (5 of 14)
- **Gap: 12.7%** ⚠️ Large distortion

vs.

- FRA Dem seat share: 50.0% (7 of 14)
- **Gap: 1.6%** ✅ Much closer to proportional

### Reading the Map

**Baseline Mode:**
- Each color = one district
- Winner takes entire district (1 seat)
- Close races still produce 1-0 outcome

**FRA Mode:**
- Three large regions (super-districts)
- Multiple seats per region (5, 5, 4)
- Seats split proportionally within each region

### Interpreting the Seat Chart

The chart shows three scenarios:

1. **Baseline**: What actually happened under winner-take-all
2. **FRA**: What happens under proportional representation
3. **Statewide**: What perfect proportionality looks like

The closer FRA is to "Statewide," the more proportional the system.

## Common Use Cases

### Comparing Plans

**To compare baseline vs FRA for a specific region:**
1. Select "Baseline Plan" in sidebar
2. Choose a district (e.g., District 5)
3. Note the winner and vote share
4. Switch to "FRA Plan"
5. Find which super-district contains that area
6. Compare seat allocation to vote share

### Analyzing Proportionality

**To measure overall fairness:**
1. Look at "Key Metrics" proportionality gap
2. Compare baseline gap to FRA gap
3. Check the seat allocation chart
4. See how close each system is to vote share

### Understanding Geographic Impacts

**To see how geography affects results:**
1. View the map in baseline mode
2. Notice which party wins each district
3. Switch to FRA mode
4. See how the same geography produces different seat allocations

## Technical Details

### Data Sources

1. **Precinct Shapefile**: `new_data/nc_2024_with_population.shp`
   - 2,658 precincts
   - 2024 Presidential election results
   - Population data

2. **Baseline Plan**: `outputs/plan_assignments/plan_1.json`
   - Precinct → District mapping
   - Generated by GerryChain ReCom algorithm

3. **FRA Assignment**: `outputs/fra/superdistrict_assignment.json`
   - Precinct → Super-district mapping
   - Generated by FRA gluing algorithm

4. **FRA Results**: `outputs/fra/fra_results.csv`
   - Seat allocations per super-district
   - Vote totals and proportions

### Performance Optimization

The dashboard uses several optimization techniques:

- **@st.cache_data**: All data loading functions are cached
- **Lazy computation**: Results only computed when mode changes
- **Efficient mapping**: Folium for lightweight interactive maps

### Browser Compatibility

Tested and working on:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Customization

### Changing the Baseline Plan

To visualize a different baseline plan, edit `dashboard_fra.py` line 125:

```python
baseline_path = base_dir / "outputs" / "plan_assignments" / "plan_2.json"  # Change to plan_2
```

Then regenerate FRA results for that plan:

```bash
python scripts/fra_gluing_algorithm.py
```

### Adjusting Color Schemes

**District Colors** (line 244):
```python
colors = px.colors.qualitative.Plotly + px.colors.qualitative.Set3
```

**Super-District Colors** (line 310):
```python
superdistrict_colors = {
    0: '#FF6B6B',  # Red
    1: '#4ECDC4',  # Teal
    2: '#FFE66D'   # Yellow
}
```

### Modifying Map Behavior

**Zoom Level** (lines 236, 302):
```python
zoom_start=7  # Increase for closer zoom, decrease for wider view
```

**Map Style** (lines 232, 298):
```python
tiles='CartoDB positron'  # Options: 'OpenStreetMap', 'CartoDB dark_matter', etc.
```

## Troubleshooting

### Dashboard Won't Start

**Error**: "Address already in use"
```bash
# Kill existing Streamlit process
pkill -f streamlit
# Restart dashboard
streamlit run scripts/dashboard_fra.py
```

### Map Not Loading

**Issue**: Map shows blank or loading spinner
- Check internet connection (map tiles require internet)
- Try refreshing the page (Ctrl+R or Cmd+R)
- Check browser console for JavaScript errors

### Data Not Found

**Error**: "FileNotFoundError: [Errno 2] No such file or directory"
1. Verify you're in the `fra_pipeline` directory
2. Check that all required files exist:
   ```bash
   ls new_data/nc_2024_with_population.shp
   ls outputs/plan_assignments/plan_1.json
   ls outputs/fra/superdistrict_assignment.json
   ls outputs/fra/fra_results.csv
   ```
3. If FRA files missing, run:
   ```bash
   python scripts/fra_gluing_algorithm.py
   ```

### Slow Performance

If dashboard is slow:
1. Close other Streamlit apps
2. Clear cache: Click "Clear cache" in Streamlit menu (top right)
3. Restart Streamlit server
4. Check system resources (memory, CPU)

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `R` | Rerun the app |
| `C` | Clear cache |
| `Esc` | Close sidebar on mobile |
| `/` | Focus search (in tables) |

## Sharing the Dashboard

### Local Network Access

To allow others on your network to access the dashboard:

```bash
streamlit run scripts/dashboard_fra.py --server.address=0.0.0.0
```

Others can access at: `http://YOUR_IP:8501`

### Cloud Deployment

To deploy to Streamlit Cloud:
1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Connect repository
4. Deploy `scripts/dashboard_fra.py`

## Educational Use

### For Students

This dashboard is designed for teaching:
- How electoral systems affect representation
- The difference between winner-take-all and proportional representation
- The Fair Representation Act concept
- Computational redistricting methods

### For Researchers

Use the dashboard to:
- Compare baseline ensemble plans to FRA outcomes
- Measure proportionality across different baseline seeds
- Analyze geographic vs demographic factors
- Visualize gluing algorithm results

## Support

For issues or questions:
1. Check this README
2. Review the main project documentation
3. Check the inline code comments in `dashboard_fra.py`
4. Open an issue on GitHub (if applicable)

## Credits

**Built with:**
- Streamlit (web framework)
- Folium (interactive maps)
- Plotly (interactive charts)
- GeoPandas (spatial data)
- Pandas (data processing)

**Data:**
- NC 2024 Presidential Election (precinct-level)
- VEST Redistricting Data

**Generated with:**
[Claude Code](https://claude.com/claude-code)

## License

Educational use only.
