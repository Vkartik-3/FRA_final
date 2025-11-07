#!/usr/bin/env python3
"""
FRA Dashboard - Interactive Visualization of Fair Representation Act Results

This Streamlit dashboard visualizes the Fair Representation Act (FRA) super-districts:
- 3 multi-member super-districts (proportional representation)
- Each super-district allocates seats proportionally to vote share
- Total of 14 seats across North Carolina

Author: Claude Code
Date: 2025
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import json
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from pathlib import Path
import numpy as np


# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="FRA Dashboard - North Carolina 2024",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# DATA LOADING FUNCTIONS (CACHED)
# ============================================================================

@st.cache_data
def load_precinct_shapefile(shp_path):
    """
    Load NC precinct shapefile with 2024 presidential data.

    Returns:
        GeoDataFrame with precinct geometries and vote data
    """
    gdf = gpd.read_file(shp_path)

    # Convert to WGS84 for web mapping
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    return gdf


@st.cache_data
def load_baseline_plan(plan_path):
    """
    Load baseline district assignment.

    Returns:
        Dictionary mapping precinct_id -> district_id
    """
    with open(plan_path, 'r') as f:
        assignment = json.load(f)

    # Convert to int keys
    return {int(k): int(v) for k, v in assignment.items()}


@st.cache_data
def load_fra_plan(fra_path):
    """
    Load FRA superdistrict assignment.

    Returns:
        Dictionary mapping precinct_id -> superdistrict_id
    """
    with open(fra_path, 'r') as f:
        assignment = json.load(f)

    # Convert to int keys
    return {int(k): int(v) for k, v in assignment.items()}


@st.cache_data
def load_fra_results(csv_path):
    """
    Load FRA seat allocation results.

    Returns:
        DataFrame with super-district results
    """
    return pd.read_csv(csv_path)


# ============================================================================
# DATA PROCESSING FUNCTIONS
# ============================================================================

def compute_baseline_results(gdf, baseline_assignment):
    """
    Compute baseline plan results (winner-take-all).

    Returns:
        DataFrame with district-level results
    """
    # Add district assignment to geodataframe
    gdf_baseline = gdf.copy()
    gdf_baseline['district'] = gdf_baseline.index.map(baseline_assignment)

    # Aggregate by district
    results = []
    for district_id in range(14):
        district_data = gdf_baseline[gdf_baseline['district'] == district_id]

        dem_votes = district_data['G24PREDHAR'].sum()
        rep_votes = district_data['G24PRERTRU'].sum()
        population = district_data['TOTPOP'].sum()

        winner = 'Dem' if dem_votes > rep_votes else 'Rep'
        margin = abs(dem_votes - rep_votes)

        results.append({
            'district_id': district_id,
            'dem_votes': int(dem_votes),
            'rep_votes': int(rep_votes),
            'population': int(population),
            'winner': winner,
            'margin': int(margin),
            'dem_share': dem_votes / (dem_votes + rep_votes) if (dem_votes + rep_votes) > 0 else 0
        })

    return pd.DataFrame(results)


def compute_statewide_totals(gdf):
    """
    Compute statewide vote totals.

    Returns:
        Dictionary with statewide totals
    """
    total_dem = gdf['G24PREDHAR'].sum()
    total_rep = gdf['G24PRERTRU'].sum()
    total_votes = total_dem + total_rep
    total_pop = gdf['TOTPOP'].sum()

    return {
        'dem_votes': int(total_dem),
        'rep_votes': int(total_rep),
        'total_votes': int(total_votes),
        'dem_share': total_dem / total_votes if total_votes > 0 else 0,
        'rep_share': total_rep / total_votes if total_votes > 0 else 0,
        'population': int(total_pop)
    }


# ============================================================================
# MAP VISUALIZATION FUNCTIONS
# ============================================================================

def create_baseline_map(gdf, baseline_assignment, selected_district=None):
    """
    Create an interactive Folium map for baseline districts.

    Args:
        gdf: GeoDataFrame with precinct data
        baseline_assignment: Dict mapping precinct -> district
        selected_district: Optional district ID to highlight

    Returns:
        Folium map object
    """
    # Add district assignment
    gdf_map = gdf.copy()
    gdf_map['district'] = gdf_map.index.map(baseline_assignment)

    # Calculate center (using bounds to avoid CRS warning)
    bounds = gdf_map.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles='CartoDB positron'
    )

    # Color palette for 14 districts
    colors = px.colors.qualitative.Plotly + px.colors.qualitative.Set3
    district_colors = {i: colors[i % len(colors)] for i in range(14)}

    # Add precincts
    for idx, row in gdf_map.iterrows():
        district = row['district']

        # Determine fill color
        if selected_district is not None:
            if district == selected_district:
                fill_color = district_colors[district]
                fill_opacity = 0.8
            else:
                fill_color = 'lightgray'
                fill_opacity = 0.3
        else:
            fill_color = district_colors[district]
            fill_opacity = 0.6

        # Create tooltip
        tooltip_text = f"""
        <b>Precinct {idx}</b><br>
        District: {district}<br>
        Dem votes: {int(row['G24PREDHAR']):,}<br>
        Rep votes: {int(row['G24PRERTRU']):,}<br>
        Population: {int(row['TOTPOP']):,}
        """

        folium.GeoJson(
            row.geometry,
            style_function=lambda x, fc=fill_color, fo=fill_opacity: {
                'fillColor': fc,
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': fo
            },
            tooltip=folium.Tooltip(tooltip_text)
        ).add_to(m)

    return m


def create_fra_map(gdf, fra_assignment, fra_results, selected_superdistrict=None):
    """
    Create an interactive Folium map for FRA super-districts (district-level visualization).

    Args:
        gdf: GeoDataFrame with precinct data
        fra_assignment: Dict mapping precinct -> superdistrict
        fra_results: DataFrame with super-district vote totals
        selected_superdistrict: Optional superdistrict ID to highlight

    Returns:
        Folium map object
    """
    # Add superdistrict assignment
    gdf_map = gdf.copy()
    gdf_map['superdistrict'] = gdf_map.index.map(fra_assignment)

    # Dissolve precincts into super-districts (this is the key optimization!)
    gdf_districts = gdf_map.dissolve(by='superdistrict', aggfunc='sum')

    # Calculate center (using bounds to avoid CRS warning)
    bounds = gdf_districts.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles='CartoDB positron'
    )

    # Color palette for 3 super-districts (distinct colors)
    superdistrict_colors = {
        0: '#FF6B6B',  # Red/Coral
        1: '#4ECDC4',  # Teal/Cyan
        2: '#95E1D3'   # Mint Green
    }

    # Add super-districts (only 3 polygons!)
    for superdistrict in gdf_districts.index:
        row = gdf_districts.loc[superdistrict]
        sd_results = fra_results[fra_results['superdistrict_id'] == superdistrict].iloc[0]

        # Determine fill color and opacity
        if selected_superdistrict is not None:
            if superdistrict == selected_superdistrict:
                fill_color = superdistrict_colors[superdistrict]
                fill_opacity = 0.7
            else:
                fill_color = 'lightgray'
                fill_opacity = 0.3
        else:
            fill_color = superdistrict_colors[superdistrict]
            fill_opacity = 0.6

        # Create rich tooltip with super-district info
        tooltip_text = f"""
        <div style="font-family: Arial; font-size: 14px;">
            <b style="font-size: 16px;">Super-District {superdistrict}</b><br><br>
            <b>Seats:</b> {int(sd_results['total_seats'])} total<br>
            &nbsp;&nbsp;• Democratic: {int(sd_results['dem_seats'])}<br>
            &nbsp;&nbsp;• Republican: {int(sd_results['rep_seats'])}<br><br>
            <b>Votes:</b><br>
            &nbsp;&nbsp;• Democratic: {int(sd_results['dem_votes']):,} ({sd_results['dem_share']*100:.1f}%)<br>
            &nbsp;&nbsp;• Republican: {int(sd_results['rep_votes']):,} ({(1-sd_results['dem_share'])*100:.1f}%)<br><br>
            <b>Population:</b> {int(sd_results['population']):,}
        </div>
        """

        # Add district to map with thick borders for visibility
        folium.GeoJson(
            row.geometry,
            style_function=lambda x, fc=fill_color, fo=fill_opacity: {
                'fillColor': fc,
                'color': '#000000',  # Black border
                'weight': 3,  # Thick border for visibility
                'fillOpacity': fo,
                'opacity': 1.0  # Solid border
            },
            tooltip=folium.Tooltip(tooltip_text, sticky=True)
        ).add_to(m)

    return m


# ============================================================================
# CHART FUNCTIONS
# ============================================================================

def create_seat_comparison_chart(baseline_results, fra_results, statewide):
    """
    Create a bar chart comparing baseline vs FRA seat allocations.

    Returns:
        Plotly figure
    """
    # Count baseline seats (winner-take-all)
    baseline_dem_seats = (baseline_results['winner'] == 'Dem').sum()
    baseline_rep_seats = (baseline_results['winner'] == 'Rep').sum()

    # Get FRA seats (proportional)
    fra_dem_seats = fra_results['dem_seats'].sum()
    fra_rep_seats = fra_results['rep_seats'].sum()

    # Get statewide vote share
    statewide_dem_pct = statewide['dem_share'] * 100
    statewide_rep_pct = statewide['rep_share'] * 100

    # Create data
    data = pd.DataFrame({
        'System': ['Baseline\n(Winner-Take-All)', 'FRA\n(Proportional)', 'Statewide\nVote Share'],
        'Democratic': [baseline_dem_seats, fra_dem_seats, statewide_dem_pct * 14 / 100],
        'Republican': [baseline_rep_seats, fra_rep_seats, statewide_rep_pct * 14 / 100]
    })

    fig = go.Figure()

    # Add bars
    fig.add_trace(go.Bar(
        name='Democratic',
        x=data['System'],
        y=data['Democratic'],
        marker_color='#4169E1',
        text=data['Democratic'].round(1),
        textposition='auto',
    ))

    fig.add_trace(go.Bar(
        name='Republican',
        x=data['System'],
        y=data['Republican'],
        marker_color='#DC143C',
        text=data['Republican'].round(1),
        textposition='auto',
    ))

    fig.update_layout(
        title='Seat Allocation Comparison',
        xaxis_title='',
        yaxis_title='Seats',
        barmode='group',
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


def create_vote_share_histogram(baseline_results, fra_results, selected_district=None, selected_superdistrict=None):
    """
    Create histograms of Democratic vote share.

    Returns:
        Plotly figure
    """
    fig = go.Figure()

    # Baseline histogram
    fig.add_trace(go.Histogram(
        x=baseline_results['dem_share'] * 100,
        name='Baseline Districts',
        marker_color='rgba(65, 105, 225, 0.6)',
        nbinsx=15,
        xbins=dict(start=0, end=100, size=5)
    ))

    # FRA histogram
    fig.add_trace(go.Histogram(
        x=fra_results['dem_share'] * 100,
        name='FRA Super-districts',
        marker_color='rgba(220, 20, 60, 0.6)',
        nbinsx=15,
        xbins=dict(start=0, end=100, size=5)
    ))

    # Add mean lines
    baseline_mean = baseline_results['dem_share'].mean() * 100
    fig.add_vline(
        x=baseline_mean,
        line_dash="dash",
        line_color="blue",
        annotation_text=f"Baseline Mean: {baseline_mean:.1f}%"
    )

    fra_mean = fra_results['dem_share'].mean() * 100
    fig.add_vline(
        x=fra_mean,
        line_dash="dash",
        line_color="red",
        annotation_text=f"FRA Mean: {fra_mean:.1f}%"
    )

    fig.update_layout(
        title='Distribution of Democratic Vote Share',
        xaxis_title='Democratic Vote Share (%)',
        yaxis_title='Count',
        barmode='overlay',
        height=400
    )

    return fig


# ============================================================================
# MAIN DASHBOARD
# ============================================================================

def main():
    """Main dashboard application."""

    # ========================================================================
    # HEADER
    # ========================================================================

    st.title("🗳️ Fair Representation Act Dashboard")
    st.markdown("### North Carolina 2024 - FRA Multi-Member Districts")
    st.markdown("---")

    # ========================================================================
    # LOAD DATA
    # ========================================================================

    # File paths - resolve to absolute paths
    base_dir = Path(__file__).resolve().parent.parent
    shp_path = base_dir / "new_data" / "nc_2024_with_population.shp"
    fra_path = base_dir / "outputs" / "fra" / "superdistrict_assignment.json"
    fra_results_path = base_dir / "outputs" / "fra" / "fra_results.csv"

    # Verify files exist
    if not shp_path.exists():
        st.error(f"❌ Shapefile not found: {shp_path}")
        st.stop()
    if not fra_path.exists():
        st.error(f"❌ FRA assignment not found: {fra_path}")
        st.stop()
    if not fra_results_path.exists():
        st.error(f"❌ FRA results not found: {fra_results_path}")
        st.stop()

    # Load data with spinner
    with st.spinner('Loading data...'):
        gdf = load_precinct_shapefile(str(shp_path))
        fra_assignment = load_fra_plan(str(fra_path))
        fra_results = load_fra_results(str(fra_results_path))

        # Compute derived data
        statewide = compute_statewide_totals(gdf)

    # ========================================================================
    # SIDEBAR
    # ========================================================================

    st.sidebar.title("⚙️ FRA Dashboard Controls")

    st.sidebar.markdown("### 🗺️ Super-District Explorer")

    # Super-district selection
    selected_superdistrict = st.sidebar.selectbox(
        "Select Super-District:",
        options=[0, 1, 2],
        format_func=lambda x: f"Super-District {x}",
        help="Choose a super-district to highlight on the map"
    )

    st.sidebar.markdown("---")

    # Show superdistrict info
    if selected_superdistrict is not None:
        sd_data = fra_results[fra_results['superdistrict_id'] == selected_superdistrict].iloc[0]

        st.sidebar.markdown(f"### 📊 Super-District {selected_superdistrict}")

        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Total Seats", int(sd_data['total_seats']))
            st.metric("Dem Seats", int(sd_data['dem_seats']))
        with col2:
            st.metric("Population", f"{int(sd_data['population']/1000)}K")
            st.metric("Rep Seats", int(sd_data['rep_seats']))

        st.sidebar.metric("Dem Vote Share", f"{sd_data['dem_share']*100:.1f}%")
        st.sidebar.metric("Total Votes", f"{int(sd_data['dem_votes'] + sd_data['rep_votes']):,}")

    st.sidebar.markdown("---")

    # Legend
    st.sidebar.markdown("### 🎨 Super-District Colors")
    st.sidebar.markdown("🔴 **Super-District 0** (Red/Coral)")
    st.sidebar.markdown("🔵 **Super-District 1** (Teal/Cyan)")
    st.sidebar.markdown("🟢 **Super-District 2** (Mint Green)")

    selected_district = None  # Not used in FRA-only mode

    # ========================================================================
    # MAIN CONTENT - ROW 1: METRICS
    # ========================================================================

    st.subheader("📊 FRA Results - Key Metrics")

    # FRA metrics
    fra_dem_seats = fra_results['dem_seats'].sum()
    fra_rep_seats = fra_results['rep_seats'].sum()

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Super-Districts", "3", help="Number of multi-member districts")
    with col2:
        st.metric("Total Seats", "14", help="Total congressional seats")
    with col3:
        st.metric("Dem Seats", f"{int(fra_dem_seats)}", help="Seats won by Democrats")
    with col4:
        st.metric("Rep Seats", f"{int(fra_rep_seats)}", help="Seats won by Republicans")
    with col5:
        st.metric("Dem Vote %", f"{statewide['dem_share']*100:.1f}%", help="Statewide Democratic vote share")
    with col6:
        st.metric("Rep Vote %", f"{statewide['rep_share']*100:.1f}%", help="Statewide Republican vote share")

    # Show proportionality gap
    fra_dem_seat_share = fra_dem_seats / 14
    proportionality_error = abs(fra_dem_seat_share - statewide['dem_share']) * 100

    st.success(f"✅ **Proportionality Gap**: Only {proportionality_error:.1f}% difference between seat share ({fra_dem_seat_share*100:.1f}%) and vote share ({statewide['dem_share']*100:.1f}%)")

    st.markdown("---")

    # ========================================================================
    # MAIN CONTENT - ROW 2: FULL-WIDTH MAP
    # ========================================================================

    st.subheader("🗺️ Interactive Map of FRA Super-Districts")
    st.caption("Hover over super-districts to see detailed voting data and seat allocation. Click a super-district in the sidebar to highlight it.")

    # Create and display FRA map (full width)
    m = create_fra_map(gdf, fra_assignment, fra_results, selected_superdistrict)
    st_folium(m, width=None, height=600)

    st.markdown("---")

    # ========================================================================
    # MAIN CONTENT - ROW 3: SUPER-DISTRICT SUMMARY CARDS
    # ========================================================================

    st.subheader("📈 Seat Allocation by Super-District")

    # Create 3 columns for 3 super-districts
    cols = st.columns(3)

    for idx, row in fra_results.iterrows():
        sd_id = int(row['superdistrict_id'])

        with cols[sd_id]:
            # Color-coded header
            color_map = {0: '#FF6B6B', 1: '#4ECDC4', 2: '#95E1D3'}
            st.markdown(f"""
            <div style="background-color: {color_map[sd_id]}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <h3 style="color: white; margin: 0; text-align: center;">Super-District {sd_id}</h3>
                <p style="color: white; margin: 0; text-align: center; font-size: 14px;">{int(row['total_seats'])} seats</p>
            </div>
            """, unsafe_allow_html=True)

            # Seat metrics
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Dem Seats", int(row['dem_seats']))
            with col_b:
                st.metric("Rep Seats", int(row['rep_seats']))

            # Vote share
            st.metric("Dem Vote Share", f"{row['dem_share']*100:.1f}%")
            st.metric("Population", f"{int(row['population']/1000)}K")

    st.markdown("---")

    # ========================================================================
    # MAIN CONTENT - ROW 4: DETAILED RESULTS TABLE
    # ========================================================================

    st.subheader("📋 Detailed Results by Super-District")

    # Format FRA table
    display_df = fra_results.copy()
    display_df['dem_share'] = (display_df['dem_share'] * 100).round(1).astype(str) + '%'
    display_df = display_df.rename(columns={
        'superdistrict_id': 'Super-District',
        'total_seats': 'Total Seats',
        'dem_votes': 'Dem Votes',
        'rep_votes': 'Rep Votes',
        'dem_seats': 'Dem Seats',
        'rep_seats': 'Rep Seats',
        'dem_share': 'Dem %',
        'population': 'Population'
    })

    st.dataframe(display_df, hide_index=True)

    st.markdown("---")

    # ========================================================================
    # MAIN CONTENT - ROW 5: INTERPRETATION
    # ========================================================================

    st.subheader("💡 Explanation of What This Means")

    with st.expander("**How does FRA reduce winner-take-all distortion?**", expanded=True):
        # Calculate FRA metrics
        total_fra_dem = fra_results['dem_seats'].sum()
        fra_gap = abs((total_fra_dem / 14) - statewide['dem_share']) * 100

        st.markdown(f"""
        **Winner-Take-All (Traditional Single-Member Districts)**:
        - In single-member districts, the candidate with the most votes wins 100% of representation.
        - If Democrats get 48% of votes in a district, they get **0 seats** (Republicans win).
        - Small vote advantages can create large seat majorities.
        - This often creates a significant gap between vote share and seat share.

        **Proportional Representation (FRA)**:
        - In multi-member super-districts, seats are allocated proportionally to vote share.
        - If Democrats get 48% of votes in a 5-seat super-district, they get **~2 seats** (40%).
        - With NC 2024 data under FRA, the gap is only **{fra_gap:.1f}%** between vote share ({statewide['dem_share']*100:.1f}%) and seat share ({total_fra_dem/14*100:.1f}%).

        **Why this matters**:
        - Under FRA, a party winning ~50% of votes gets ~50% of seats.
        - Under winner-take-all, the same vote share could produce anywhere from 35% to 65% of seats depending on how districts are drawn.
        - FRA makes gerrymandering much harder because representation naturally follows vote share.
        """)

    with st.expander("**How does gluing change the geometry?**"):
        st.markdown("""
        **The Gluing Algorithm**:
        1. Starts with 14 single-member districts drawn by a baseline redistricting plan.
        2. **Merges** neighboring districts into 3 larger super-districts (sizes: 5, 5, 4 seats).
        3. Ensures each super-district is **contiguous** (all parts connected).

        **What changes**:
        - Geography: 14 small districts → 3 large super-districts
        - Representation: 14 single winners → 14 seats allocated proportionally across 3 regions

        **What stays the same**:
        - Precinct boundaries are unchanged
        - Total vote counts remain identical
        - Total number of seats remains 14
        """)

    with st.expander("**Why does multi-member PR give different outcomes?**"):
        # Calculate total FRA seats
        total_fra_dem = fra_results['dem_seats'].sum()
        total_fra_rep = fra_results['rep_seats'].sum()

        st.markdown(f"""
        **Example**: Consider a super-district with 5 seats and the following vote shares:
        - Democrats: 54%
        - Republicans: 46%

        **Under Winner-Take-All**:
        - If this were 5 separate districts with the same split, Democrats might win all 5 seats.
        - Result: **5-0 Democratic sweep**

        **Under FRA Proportional Representation**:
        - Seats allocated: 54% × 5 = 2.7 → rounds to **3 Democratic seats**
        - Remaining: 5 - 3 = **2 Republican seats**
        - Result: **3-2 split** (reflects actual vote share)

        **The key insight**:
        - Multi-member PR prevents "wasted votes" by giving minority parties representation.
        - In North Carolina 2024 under FRA, this produces a **{int(total_fra_dem)}-{int(total_fra_rep)} seat split** that closely matches the statewide vote share of **{statewide['dem_share']*100:.1f}%-{statewide['rep_share']*100:.1f}%**.
        """)

    st.markdown("---")

    # ========================================================================
    # FOOTER
    # ========================================================================

    st.caption("Built with Streamlit • Data: NC 2024 Presidential Election (precinct-level)")
    st.caption("Generated with Claude Code")


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    main()
