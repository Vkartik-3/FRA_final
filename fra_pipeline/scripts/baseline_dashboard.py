#!/usr/bin/env python3
"""
Baseline Ensemble Dashboard - Interactive Streamlit App

Visualizes the 10 randomly generated district plans with:
- Interactive map showing districts
- Summary statistics
- Comparative histograms
- Plan-by-plan analysis
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import json
from pathlib import Path


# Page config
st.set_page_config(
    page_title="FRA Pipeline - Baseline Dashboard",
    page_icon="🗺️",
    layout="wide"
)


@st.cache_data
def load_shapefile(shp_path):
    """Load the NC VTD shapefile."""
    gdf = gpd.read_file(shp_path)
    return gdf


@st.cache_data
def load_ensemble_results(csv_path):
    """Load baseline ensemble results CSV."""
    return pd.read_csv(csv_path)


def load_plan_assignment(plan_id, plans_dir):
    """Load district assignment for a specific plan."""
    assignment_path = plans_dir / f"plan_{plan_id}.json"

    if not assignment_path.exists():
        return None

    with open(assignment_path, 'r') as f:
        assignment = json.load(f)

    # Convert string keys back to integers
    assignment = {int(k): v for k, v in assignment.items()}

    return assignment


def create_district_map(gdf, assignment, plan_id):
    """
    Create a choropleth map showing district assignments.

    Args:
        gdf: GeoDataFrame with precinct geometries
        assignment: Dict mapping precinct_id -> district_id
        plan_id: Plan number for title

    Returns:
        matplotlib figure
    """
    # Create a copy and add district assignments
    gdf_plot = gdf.copy()
    gdf_plot['district'] = gdf_plot.index.map(assignment)

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))

    # Get unique districts and create colormap
    districts = sorted(gdf_plot['district'].unique())
    num_districts = len(districts)

    # Use a qualitative colormap (updated for matplotlib 3.7+)
    cmap = plt.colormaps.get_cmap('tab20').resampled(num_districts)
    colors = [mcolors.rgb2hex(cmap(i)) for i in range(num_districts)]

    # Plot each district
    for i, district in enumerate(districts):
        district_geom = gdf_plot[gdf_plot['district'] == district]
        district_geom.plot(ax=ax, color=colors[i], edgecolor='white',
                          linewidth=0.5, label=f'District {district}')

    # Styling
    ax.set_title(f'Plan {plan_id}: District Map (14 Districts)',
                fontsize=16, fontweight='bold', pad=20)
    ax.axis('off')

    # Add legend
    # Only show legend if number of districts is reasonable
    if num_districts <= 20:
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5),
                 fontsize=9, frameon=True, fancybox=True)

    plt.tight_layout()

    return fig


def plot_seat_distribution_histogram(results_df, selected_plan_id=None):
    """
    Create histogram of Democratic seat share across all plans.

    Args:
        results_df: DataFrame with ensemble results
        selected_plan_id: Highlight this plan in the histogram

    Returns:
        matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot histogram
    ax.hist(results_df['dem_seat_share'], bins=10, edgecolor='black',
           alpha=0.7, color='steelblue', label='All Plans')

    # Highlight selected plan
    if selected_plan_id is not None:
        selected_share = results_df[results_df['plan_id'] == selected_plan_id]['dem_seat_share'].values[0]
        ax.axvline(selected_share, color='orange', linestyle='--',
                  linewidth=3, label=f'Plan {selected_plan_id}: {selected_share:.3f}')

    # Add mean line
    mean_share = results_df['dem_seat_share'].mean()
    ax.axvline(mean_share, color='red', linestyle='--',
              linewidth=2, label=f'Mean: {mean_share:.3f}')

    ax.set_xlabel('Democratic Seat Share', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Democratic Seat Share Distribution Across 10 Plans',
                fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig


def main():
    """Main dashboard application."""

    # Title
    st.title("🗺️ Baseline Ensemble Dashboard")
    st.markdown("### Step 1: Traditional Single-Member Districts")
    st.markdown("---")

    # Determine paths
    base_dir = Path(__file__).resolve().parent.parent

    # Try multiple possible paths for the shapefile
    possible_shp_paths = [
        base_dir / "new_data" / "nc_2024_with_population.shp",
        base_dir / "data" / "NC_VTD" / "NC_VTD.shp",
        base_dir.parent / "data" / "NC-shapefiles" / "NC_VTD" / "NC_VTD.shp",
    ]

    shp_path = None
    for path in possible_shp_paths:
        if path.exists():
            shp_path = path
            break

    csv_path = base_dir / "outputs" / "baseline_ensemble.csv"
    plans_dir = base_dir / "outputs" / "plan_assignments"

    # Check if files exist
    if not csv_path.exists():
        st.error(f"❌ Results not found at: {csv_path}")
        st.info("Please run: `python scripts/run_baseline_simple.py` first")
        return

    if shp_path is None or not shp_path.exists():
        st.error(f"❌ Shapefile not found. Please ensure NC_VTD.shp is accessible")
        return

    # Load data
    with st.spinner("Loading data..."):
        results_df = load_ensemble_results(csv_path)
        gdf = load_shapefile(shp_path)

    st.success(f"✅ Loaded {len(results_df)} plans with {len(gdf)} precincts")

    # Sidebar - Plan selector
    st.sidebar.header("📊 Plan Selection")
    plan_id = st.sidebar.selectbox(
        "Choose a plan to visualize:",
        options=results_df['plan_id'].tolist(),
        format_func=lambda x: f"Plan {x}"
    )

    # Load selected plan
    assignment = load_plan_assignment(plan_id, plans_dir)

    if assignment is None:
        st.error(f"❌ Could not load assignment for Plan {plan_id}")
        return

    # Display selected plan info
    selected_plan = results_df[results_df['plan_id'] == plan_id].iloc[0]

    st.sidebar.markdown("---")
    st.sidebar.subheader(f"Plan {plan_id} Results")
    st.sidebar.metric("Democratic Seats", f"{selected_plan['dem_seats']}/14")
    st.sidebar.metric("Republican Seats", f"{selected_plan['rep_seats']}/14")
    st.sidebar.metric("Dem Seat Share", f"{selected_plan['dem_seat_share']:.1%}")

    # Main content - Two columns
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"🗺️ District Map - Plan {plan_id}")

        with st.spinner("Rendering map..."):
            fig_map = create_district_map(gdf, assignment, plan_id)
            st.pyplot(fig_map)
            plt.close()

    with col2:
        st.subheader("📈 Seat Distribution")

        # Pie chart
        fig_pie, ax_pie = plt.subplots(figsize=(6, 6))
        colors_pie = ['#4A90E2', '#E24A4A']
        ax_pie.pie(
            [selected_plan['dem_seats'], selected_plan['rep_seats']],
            labels=['Democrat', 'Republican'],
            colors=colors_pie,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 12, 'weight': 'bold'}
        )
        ax_pie.set_title(f'Plan {plan_id} Seat Distribution', fontsize=14, fontweight='bold')
        st.pyplot(fig_pie)
        plt.close()

        # Summary table
        st.markdown("#### Summary Stats")
        summary_data = {
            "Metric": ["Dem Seats", "Rep Seats", "Total Districts", "Dem Share"],
            "Value": [
                int(selected_plan['dem_seats']),
                int(selected_plan['rep_seats']),
                14,
                f"{selected_plan['dem_seat_share']:.3f}"
            ]
        }
        st.table(pd.DataFrame(summary_data))

    # Full-width histogram
    st.markdown("---")
    st.subheader("📊 Comparative Analysis: All 10 Plans")

    fig_hist = plot_seat_distribution_histogram(results_df, plan_id)
    st.pyplot(fig_hist)
    plt.close()

    # Summary statistics table
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

    with col_stat1:
        st.metric("Mean Dem Share", f"{results_df['dem_seat_share'].mean():.3f}")

    with col_stat2:
        st.metric("Std Deviation", f"{results_df['dem_seat_share'].std():.3f}")

    with col_stat3:
        st.metric("Min Dem Share", f"{results_df['dem_seat_share'].min():.3f}")

    with col_stat4:
        st.metric("Max Dem Share", f"{results_df['dem_seat_share'].max():.3f}")

    # Full results table
    st.markdown("---")
    st.subheader("📋 All Plans - Detailed Results")

    # Add percentage column for display
    display_df = results_df.copy()
    display_df['dem_share_pct'] = (display_df['dem_seat_share'] * 100).round(1)
    display_df = display_df.rename(columns={
        'plan_id': 'Plan ID',
        'dem_seats': 'Dem Seats',
        'rep_seats': 'Rep Seats',
        'dem_share_pct': 'Dem Share %'
    })

    st.dataframe(
        display_df[['Plan ID', 'Dem Seats', 'Rep Seats', 'Dem Share %']],
        hide_index=True
    )

    # Footer
    st.markdown("---")
    st.markdown("""
    **About This Analysis:**
    - Generated 10 random district plans using GerryChain's ReCom algorithm
    - Each district uses **winner-take-all** (plurality voting)
    - Population deviation constrained to ±5%
    - All districts are contiguous

    **Key Insight:** Notice how Democratic seat share varies across plans (range: {:.1%} - {:.1%}),
    demonstrating how district boundaries affect electoral outcomes even with the same voters!
    """.format(results_df['dem_seat_share'].min(), results_df['dem_seat_share'].max()))


if __name__ == "__main__":
    main()
