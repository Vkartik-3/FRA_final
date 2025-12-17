#!/usr/bin/env python3
"""
Unified FRA Dashboard - Combined Baseline, FRA, and Comparison Views

Interactive dashboard combining all three dashboards into one:
- Baseline (Winner-Take-All) results
- FRA (Proportional Representation) results
- Comparison between systems

Run with: streamlit run scripts/dashboard_comparison.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path
import json

# Try to import optional dependencies
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False


# Page configuration
st.set_page_config(
    page_title="FRA - Unified Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# DATA LOADING FUNCTIONS (CACHED)
# ============================================================================

@st.cache_data
def load_baseline_ensemble(csv_path):
    """Load baseline ensemble CSV."""
    return pd.read_csv(csv_path)


@st.cache_data
def load_fra_ensemble(fra_dir, max_plans=1000):
    """Load all FRA results into a combined DataFrame."""
    all_results = []

    for i in range(1, max_plans + 1):
        fra_results_path = fra_dir / f"fra_results_{i}.csv"
        if fra_results_path.exists():
            df = pd.read_csv(fra_results_path)
            total_dem = df['dem_seats'].sum()
            total_rep = df['rep_seats'].sum()
            total_votes_dem = df['dem_votes'].sum()
            total_votes_rep = df['rep_votes'].sum()
            total_votes = total_votes_dem + total_votes_rep

            all_results.append({
                'plan_id': i,
                'dem_seats': total_dem,
                'rep_seats': total_rep,
                'total_seats': total_dem + total_rep,
                'dem_seat_share': total_dem / (total_dem + total_rep) if (total_dem + total_rep) > 0 else 0,
                'dem_vote_share': total_votes_dem / total_votes if total_votes > 0 else 0,
                'total_dem_votes': total_votes_dem,
                'total_rep_votes': total_votes_rep
            })

    if all_results:
        return pd.DataFrame(all_results)
    return None


@st.cache_data
def load_precinct_shapefile(shp_path):
    """Load NC precinct shapefile with 2024 presidential data."""
    gdf = gpd.read_file(shp_path)
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    return gdf


@st.cache_data
def load_baseline_district_results(plan_id, outputs_dir):
    """Load district-level results for a specific baseline plan."""
    csv_path = outputs_dir / f"baseline_districts_plan_{plan_id}.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return None


@st.cache_data
def load_fra_plan_results(plan_id, fra_dir):
    """Load FRA results for a specific plan."""
    csv_path = fra_dir / f"fra_results_{plan_id}.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return None


@st.cache_data
def load_fra_assignment(plan_id, fra_dir):
    """Load FRA superdistrict assignment for a specific plan."""
    json_path = fra_dir / f"superdistrict_assignment_{plan_id}.json"
    if json_path.exists():
        with open(json_path, 'r') as f:
            assignment = json.load(f)
        return {int(k): int(v) for k, v in assignment.items()}
    return None


def get_paths():
    """Determine correct paths for data files."""
    script_path = Path(__file__).resolve()
    base_dir = script_path.parent.parent

    csv_path = base_dir / "outputs" / "baseline_ensemble.csv"

    if not csv_path.exists():
        cwd = Path.cwd()
        if (cwd / "outputs" / "baseline_ensemble.csv").exists():
            base_dir = cwd
        elif (cwd.parent / "outputs" / "baseline_ensemble.csv").exists():
            base_dir = cwd.parent
        else:
            abs_path = Path("/Users/kartikvadhawana/Desktop/FRA/NEWFINALFRA/fra_pipeline")
            if (abs_path / "outputs" / "baseline_ensemble.csv").exists():
                base_dir = abs_path

    return base_dir


# ============================================================================
# PLOTTING FUNCTIONS
# ============================================================================

def plot_comparison_histogram(baseline_df, fra_df):
    """Create side-by-side histograms comparing baseline and FRA seat distributions."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Baseline histogram
    axes[0].hist(baseline_df['dem_seats'],
                 bins=range(int(baseline_df['dem_seats'].min()),
                           int(baseline_df['dem_seats'].max()) + 2),
                 edgecolor='black', alpha=0.7, color='steelblue', align='left')
    baseline_mean = baseline_df['dem_seats'].mean()
    axes[0].axvline(baseline_mean, color='red', linestyle='--',
                    linewidth=2, label=f'Mean: {baseline_mean:.1f}')
    axes[0].set_xlabel('Democratic Seats', fontsize=11, fontweight='bold')
    axes[0].set_ylabel('Frequency', fontsize=11, fontweight='bold')
    axes[0].set_title('Baseline (Winner-Take-All)', fontsize=13, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3, axis='y')

    # FRA histogram
    axes[1].hist(fra_df['dem_seats'],
                 bins=range(int(fra_df['dem_seats'].min()),
                           int(fra_df['dem_seats'].max()) + 2),
                 edgecolor='black', alpha=0.7, color='forestgreen', align='left')
    fra_mean = fra_df['dem_seats'].mean()
    axes[1].axvline(fra_mean, color='red', linestyle='--',
                    linewidth=2, label=f'Mean: {fra_mean:.1f}')
    axes[1].set_xlabel('Democratic Seats', fontsize=11, fontweight='bold')
    axes[1].set_ylabel('Frequency', fontsize=11, fontweight='bold')
    axes[1].set_title('FRA (Proportional Representation)', fontsize=13, fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    return fig


def plot_overlaid_histogram(baseline_df, fra_df):
    """Create overlaid histogram for direct comparison."""
    fig, ax = plt.subplots(figsize=(12, 6))

    all_seats = list(baseline_df['dem_seats']) + list(fra_df['dem_seats'])
    min_seats = int(min(all_seats))
    max_seats = int(max(all_seats))
    bins = range(min_seats, max_seats + 2)

    ax.hist(baseline_df['dem_seats'], bins=bins, alpha=0.5,
            color='steelblue', label='Baseline (WTA)', align='left', edgecolor='darkblue')
    ax.hist(fra_df['dem_seats'], bins=bins, alpha=0.5,
            color='forestgreen', label='FRA (PR)', align='left', edgecolor='darkgreen')

    baseline_mean = baseline_df['dem_seats'].mean()
    fra_mean = fra_df['dem_seats'].mean()
    ax.axvline(baseline_mean, color='steelblue', linestyle='--',
               linewidth=2, label=f'Baseline Mean: {baseline_mean:.1f}')
    ax.axvline(fra_mean, color='forestgreen', linestyle='--',
               linewidth=2, label=f'FRA Mean: {fra_mean:.1f}')

    ax.set_xlabel('Democratic Seats', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency (Number of Plans)', fontsize=12, fontweight='bold')
    ax.set_title('Democratic Seat Distribution: Baseline vs FRA', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    return fig


def plot_boxplot_comparison(baseline_df, fra_df):
    """Create boxplot comparison of seat distributions."""
    fig, ax = plt.subplots(figsize=(10, 6))

    data = [baseline_df['dem_seats'], fra_df['dem_seats']]
    bp = ax.boxplot(data, labels=['Baseline\n(Winner-Take-All)', 'FRA\n(Proportional)'],
                    patch_artist=True)

    bp['boxes'][0].set_facecolor('steelblue')
    bp['boxes'][1].set_facecolor('forestgreen')

    for box in bp['boxes']:
        box.set_alpha(0.7)

    ax.set_ylabel('Democratic Seats', fontsize=12, fontweight='bold')
    ax.set_title('Seat Distribution Comparison', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    means = [baseline_df['dem_seats'].mean(), fra_df['dem_seats'].mean()]
    ax.scatter([1, 2], means, color='red', marker='D', s=100, zorder=5, label='Mean')
    ax.legend()

    plt.tight_layout()
    return fig


def plot_variance_comparison(baseline_df, fra_df):
    """Plot variance/standard deviation comparison."""
    fig, ax = plt.subplots(figsize=(8, 6))

    baseline_std = baseline_df['dem_seats'].std()
    fra_std = fra_df['dem_seats'].std()

    bars = ax.bar(['Baseline\n(Winner-Take-All)', 'FRA\n(Proportional)'],
                  [baseline_std, fra_std],
                  color=['steelblue', 'forestgreen'], alpha=0.7, edgecolor='black')

    for bar, val in zip(bars, [baseline_std, fra_std]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f'{val:.2f}', ha='center', va='bottom', fontweight='bold')

    ax.set_ylabel('Standard Deviation (Seats)', fontsize=12, fontweight='bold')
    ax.set_title('Outcome Variability Comparison', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    return fig


def plot_single_histogram(df, title, color):
    """Plot single histogram for individual view."""
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.hist(df['dem_seats'],
            bins=range(int(df['dem_seats'].min()), int(df['dem_seats'].max()) + 2),
            edgecolor='black', alpha=0.7, color=color, align='left')

    mean_seats = df['dem_seats'].mean()
    ax.axvline(mean_seats, color='red', linestyle='--',
               linewidth=2, label=f'Mean: {mean_seats:.1f}')

    ax.set_xlabel('Democratic Seats', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency (Number of Plans)', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    return fig


def create_fra_map(gdf, fra_assignment, fra_results, selected_superdistrict=None):
    """Create an interactive Folium map for FRA super-districts."""
    if not HAS_FOLIUM:
        return None

    gdf_map = gdf.copy()
    gdf_map['superdistrict'] = gdf_map.index.map(fra_assignment)

    gdf_districts = gdf_map.dissolve(by='superdistrict', aggfunc='sum')

    bounds = gdf_districts.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles='CartoDB positron'
    )

    superdistrict_colors = {
        0: '#FF6B6B',
        1: '#4ECDC4',
        2: '#95E1D3'
    }

    for superdistrict in gdf_districts.index:
        row = gdf_districts.loc[superdistrict]
        sd_results = fra_results[fra_results['superdistrict_id'] == superdistrict].iloc[0]

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

        folium.GeoJson(
            row.geometry,
            style_function=lambda x, fc=fill_color, fo=fill_opacity: {
                'fillColor': fc,
                'color': '#000000',
                'weight': 3,
                'fillOpacity': fo,
                'opacity': 1.0
            },
            tooltip=folium.Tooltip(tooltip_text, sticky=True)
        ).add_to(m)

    return m


# ============================================================================
# VIEW RENDERING FUNCTIONS
# ============================================================================

def render_comparison_view(baseline_df, fra_df):
    """Render the comparison view with side-by-side analysis."""

    st.markdown("## 🔄 System Comparison")

    # Summary statistics table
    st.markdown("### Summary Statistics")

    baseline_stats = {
        'Total Plans': len(baseline_df),
        'Mean Dem Seats': f"{baseline_df['dem_seats'].mean():.2f}",
        'Median Dem Seats': f"{baseline_df['dem_seats'].median():.1f}",
        'Std Dev': f"{baseline_df['dem_seats'].std():.2f}",
        'Min Dem Seats': int(baseline_df['dem_seats'].min()),
        'Max Dem Seats': int(baseline_df['dem_seats'].max()),
        'Range': int(baseline_df['dem_seats'].max() - baseline_df['dem_seats'].min())
    }

    fra_stats = {
        'Total Plans': len(fra_df),
        'Mean Dem Seats': f"{fra_df['dem_seats'].mean():.2f}",
        'Median Dem Seats': f"{fra_df['dem_seats'].median():.1f}",
        'Std Dev': f"{fra_df['dem_seats'].std():.2f}",
        'Min Dem Seats': int(fra_df['dem_seats'].min()),
        'Max Dem Seats': int(fra_df['dem_seats'].max()),
        'Range': int(fra_df['dem_seats'].max() - fra_df['dem_seats'].min())
    }

    comparison_df = pd.DataFrame({
        'Metric': list(baseline_stats.keys()),
        'Baseline (WTA)': list(baseline_stats.values()),
        'FRA (Proportional)': list(fra_stats.values())
    })

    st.table(comparison_df)

    # Key metrics
    st.markdown("### Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        baseline_mean = baseline_df['dem_seats'].mean()
        fra_mean = fra_df['dem_seats'].mean()
        diff = fra_mean - baseline_mean
        st.metric(
            "Mean Dem Seats Diff",
            f"{diff:+.2f}",
            delta=f"FRA {'higher' if diff > 0 else 'lower'}"
        )

    with col2:
        baseline_std = baseline_df['dem_seats'].std()
        fra_std = fra_df['dem_seats'].std()
        std_reduction = ((baseline_std - fra_std) / baseline_std * 100) if baseline_std > 0 else 0
        st.metric(
            "Variability Reduction",
            f"{std_reduction:.1f}%",
            delta="More consistent" if std_reduction > 0 else "Less consistent"
        )

    with col3:
        baseline_range = baseline_df['dem_seats'].max() - baseline_df['dem_seats'].min()
        st.metric("Baseline Range", f"{int(baseline_range)} seats")

    with col4:
        fra_range = fra_df['dem_seats'].max() - fra_df['dem_seats'].min()
        st.metric("FRA Range", f"{int(fra_range)} seats")

    # Visualizations
    st.markdown("---")
    st.markdown("### Visualizations")

    st.markdown("#### Overlaid Seat Distribution")
    fig_overlay = plot_overlaid_histogram(baseline_df, fra_df)
    st.pyplot(fig_overlay)
    plt.close()

    st.markdown("#### Side-by-Side Distributions")
    fig_sidebyside = plot_comparison_histogram(baseline_df, fra_df)
    st.pyplot(fig_sidebyside)
    plt.close()

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Seat Distribution Boxplot")
        fig_box = plot_boxplot_comparison(baseline_df, fra_df)
        st.pyplot(fig_box)
        plt.close()

    with col_b:
        st.markdown("#### Outcome Variability")
        fig_var = plot_variance_comparison(baseline_df, fra_df)
        st.pyplot(fig_var)
        plt.close()

    # Interpretation
    st.markdown("---")
    st.markdown("### Interpretation")

    baseline_mean = baseline_df['dem_seats'].mean()
    fra_mean = fra_df['dem_seats'].mean()
    baseline_std = baseline_df['dem_seats'].std()
    fra_std = fra_df['dem_seats'].std()

    st.markdown(f"""
    **Key Findings:**

    1. **Mean Seats**: FRA produces an average of {fra_mean:.1f} Democratic seats compared to {baseline_mean:.1f} under baseline
       (difference of {fra_mean - baseline_mean:+.1f} seats).

    2. **Consistency**: FRA has {'lower' if fra_std < baseline_std else 'higher'} variability
       (σ={fra_std:.2f}) compared to baseline (σ={baseline_std:.2f}).

    3. **Range**: Baseline outcomes range from {int(baseline_df['dem_seats'].min())} to {int(baseline_df['dem_seats'].max())}
       ({int(baseline_df['dem_seats'].max() - baseline_df['dem_seats'].min())} seat spread),
       while FRA ranges from {int(fra_df['dem_seats'].min())} to {int(fra_df['dem_seats'].max())}
       ({int(fra_df['dem_seats'].max() - fra_df['dem_seats'].min())} seat spread).
    """)


def render_baseline_view(baseline_df, outputs_dir):
    """Render the baseline-only summary view."""

    st.markdown("## 📊 Baseline (Winner-Take-All) Results")

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Plans", len(baseline_df))

    with col2:
        st.metric("Mean Dem Seats", f"{baseline_df['dem_seats'].mean():.1f}/14")

    with col3:
        st.metric("Min Dem Seats", f"{int(baseline_df['dem_seats'].min())}/14")

    with col4:
        st.metric("Max Dem Seats", f"{int(baseline_df['dem_seats'].max())}/14")

    # Additional stats
    st.markdown("### Distribution Statistics")

    col_a, col_b = st.columns(2)

    with col_a:
        st.metric("Median", f"{baseline_df['dem_seats'].median():.1f}")
        st.metric("Std Dev", f"{baseline_df['dem_seats'].std():.2f}")

    with col_b:
        st.metric("Mode", f"{baseline_df['dem_seats'].mode().iloc[0]:.0f}")
        st.metric("Range", f"{int(baseline_df['dem_seats'].max() - baseline_df['dem_seats'].min())}")

    # Histogram
    st.markdown("---")
    st.markdown("### Seat Distribution")

    fig = plot_single_histogram(baseline_df, "Baseline Democratic Seat Distribution", 'steelblue')
    st.pyplot(fig)
    plt.close()

    # Seat frequency table
    st.markdown("### Seat Frequency Table")

    seat_counts = baseline_df['dem_seats'].value_counts().sort_index()
    freq_df = pd.DataFrame({
        'Dem Seats': seat_counts.index.astype(int),
        'Frequency': seat_counts.values,
        'Percentage': (seat_counts.values / len(baseline_df) * 100).round(1)
    })
    freq_df['Percentage'] = freq_df['Percentage'].astype(str) + '%'

    st.dataframe(freq_df, width='stretch', hide_index=True)

    # Plan explorer
    st.markdown("---")
    st.markdown("### Plan Explorer")

    plan_id = st.number_input(
        "Select Plan ID:",
        min_value=int(baseline_df['plan_id'].min()),
        max_value=int(baseline_df['plan_id'].max()),
        value=int(baseline_df['plan_id'].min()),
        step=1
    )

    selected_plan = baseline_df[baseline_df['plan_id'] == plan_id].iloc[0]

    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"Plan {plan_id} - Dem Seats", f"{int(selected_plan['dem_seats'])}/14")
    with col2:
        st.metric(f"Plan {plan_id} - Rep Seats", f"{int(selected_plan['rep_seats'])}/14")

    # Try to load district-level results
    district_df = load_baseline_district_results(plan_id, outputs_dir)
    if district_df is not None:
        st.markdown("#### District-Level Results")
        st.dataframe(district_df, width='stretch', hide_index=True)


def render_fra_view(fra_df, fra_dir, base_dir):
    """Render the FRA-only summary view with map."""

    st.markdown("## 📊 FRA (Proportional Representation) Results")

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Plans", len(fra_df))

    with col2:
        st.metric("Mean Dem Seats", f"{fra_df['dem_seats'].mean():.1f}/14")

    with col3:
        st.metric("Min Dem Seats", f"{int(fra_df['dem_seats'].min())}/14")

    with col4:
        st.metric("Max Dem Seats", f"{int(fra_df['dem_seats'].max())}/14")

    # Additional stats
    st.markdown("### Distribution Statistics")

    col_a, col_b = st.columns(2)

    with col_a:
        st.metric("Median", f"{fra_df['dem_seats'].median():.1f}")
        st.metric("Std Dev", f"{fra_df['dem_seats'].std():.2f}")

    with col_b:
        if len(fra_df['dem_seats'].mode()) > 0:
            st.metric("Mode", f"{fra_df['dem_seats'].mode().iloc[0]:.0f}")
        st.metric("Range", f"{int(fra_df['dem_seats'].max() - fra_df['dem_seats'].min())}")

    # Histogram
    st.markdown("---")
    st.markdown("### Seat Distribution")

    fig = plot_single_histogram(fra_df, "FRA Democratic Seat Distribution", 'forestgreen')
    st.pyplot(fig)
    plt.close()

    # Seat frequency table
    st.markdown("### Seat Frequency Table")

    seat_counts = fra_df['dem_seats'].value_counts().sort_index()
    freq_df = pd.DataFrame({
        'Dem Seats': seat_counts.index.astype(int),
        'Frequency': seat_counts.values,
        'Percentage': (seat_counts.values / len(fra_df) * 100).round(1)
    })
    freq_df['Percentage'] = freq_df['Percentage'].astype(str) + '%'

    st.dataframe(freq_df, width='stretch', hide_index=True)

    # Plan explorer with map
    st.markdown("---")
    st.markdown("### FRA Plan Explorer")

    plan_id = st.number_input(
        "Select FRA Plan ID:",
        min_value=1,
        max_value=len(fra_df),
        value=1,
        step=1
    )

    # Load plan results
    fra_plan_results = load_fra_plan_results(plan_id, fra_dir)

    if fra_plan_results is not None:
        # Display super-district results
        st.markdown(f"#### Super-District Results for Plan {plan_id}")

        # Summary metrics
        total_dem = fra_plan_results['dem_seats'].sum()
        total_rep = fra_plan_results['rep_seats'].sum()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Dem Seats", f"{int(total_dem)}/14")
        with col2:
            st.metric("Rep Seats", f"{int(total_rep)}/14")

        # Super-district cards
        cols = st.columns(3)
        color_map = {0: '#FF6B6B', 1: '#4ECDC4', 2: '#95E1D3'}

        for idx, row in fra_plan_results.iterrows():
            sd_id = int(row['superdistrict_id'])
            with cols[sd_id]:
                st.markdown(f"""
                <div style="background-color: {color_map[sd_id]}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <h4 style="color: white; margin: 0; text-align: center;">Super-District {sd_id}</h4>
                </div>
                """, unsafe_allow_html=True)
                st.metric("Dem Seats", int(row['dem_seats']))
                st.metric("Rep Seats", int(row['rep_seats']))
                st.metric("Dem %", f"{row['dem_share']*100:.1f}%")

        # Map
        if HAS_FOLIUM:
            st.markdown("#### Interactive Map")

            shp_path = base_dir / "new_data" / "nc_2024_with_population.shp"
            fra_assignment = load_fra_assignment(plan_id, fra_dir)

            if shp_path.exists() and fra_assignment is not None:
                gdf = load_precinct_shapefile(str(shp_path))
                m = create_fra_map(gdf, fra_assignment, fra_plan_results)
                if m is not None:
                    st_folium(m, width=None, height=500)
            else:
                st.info("Map data not available")
        else:
            st.info("Install folium and streamlit-folium for interactive maps")

        # Results table
        st.markdown("#### Detailed Results")
        display_df = fra_plan_results.copy()
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


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main dashboard application."""

    # Title
    st.title("📊 FRA Unified Dashboard")
    st.markdown("### Baseline vs FRA Comparison for North Carolina 2024")
    st.markdown("---")

    # Get paths
    base_dir = get_paths()
    baseline_csv = base_dir / "outputs" / "baseline_ensemble.csv"
    fra_dir = base_dir / "outputs" / "fra"
    outputs_dir = base_dir / "outputs"

    # Check data availability
    baseline_exists = baseline_csv.exists()
    fra_exists = fra_dir.exists() and any(fra_dir.glob("fra_results_*.csv"))

    if not baseline_exists:
        st.error(f"❌ Baseline results not found at: {baseline_csv}")
        st.info("Run `python scripts/run_baseline_simple.py` first.")
        return

    if not fra_exists:
        st.error(f"❌ FRA results not found at: {fra_dir}")
        st.info("Run `python scripts/fra_gluing_algorithm.py` first.")
        return

    # Load data
    with st.spinner("Loading data..."):
        baseline_df = load_baseline_ensemble(baseline_csv)
        fra_df = load_fra_ensemble(fra_dir)

    if fra_df is None or len(fra_df) == 0:
        st.error("Failed to load FRA results")
        return

    st.success(f"✅ Loaded {len(baseline_df)} baseline plans and {len(fra_df)} FRA plans")

    # Sidebar - View selector
    st.sidebar.header("📋 Dashboard Navigation")

    view_mode = st.sidebar.radio(
        "Select View:",
        ["🔄 Comparison", "📊 Baseline Results", "🗺️ FRA Results"],
        index=0
    )

    st.sidebar.markdown("---")

    # Sidebar info
    st.sidebar.markdown("### About")
    st.sidebar.markdown("""
    **Baseline**: Winner-take-all single-member districts

    **FRA**: Multi-member super-districts with proportional representation

    **Comparison**: Side-by-side analysis of both systems
    """)

    # Main content based on view mode
    if "Comparison" in view_mode:
        render_comparison_view(baseline_df, fra_df)
    elif "Baseline" in view_mode:
        render_baseline_view(baseline_df, outputs_dir)
    else:  # FRA Results
        render_fra_view(fra_df, fra_dir, base_dir)

    # Footer
    st.markdown("---")
    st.markdown("""
    **Data Source:** NC 2024 Presidential Election (precinct-level)
    **Generated with:** Claude Code
    """)


if __name__ == "__main__":
    main()
