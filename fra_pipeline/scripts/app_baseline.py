#!/usr/bin/env python3
"""
Simple Baseline Dashboard - Streamlit App

Interactive dashboard to explore baseline election simulation results.
Displays plan-level and district-level results without geographic maps.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import json


# Page configuration
st.set_page_config(
    page_title="FRA - Baseline Results",
    page_icon="📊",
    layout="wide"
)


@st.cache_data
def load_ensemble_results(csv_path):
    """Load baseline ensemble CSV."""
    return pd.read_csv(csv_path)


def load_district_results(plan_id, outputs_dir):
    """
    Load district-level results for a specific plan.

    Args:
        plan_id: Plan number
        outputs_dir: Directory containing district CSV files

    Returns:
        DataFrame with district results, or None if not found
    """
    csv_path = outputs_dir / f"baseline_districts_plan_{plan_id}.csv"

    if csv_path.exists():
        return pd.read_csv(csv_path)
    return None


def plot_histogram(results_df, selected_plan_id=None):
    """
    Create histogram of Democratic seat counts.

    Args:
        results_df: DataFrame with all plans
        selected_plan_id: Highlight this plan if provided

    Returns:
        matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Create histogram
    ax.hist(results_df['dem_seats'],
            bins=range(results_df['dem_seats'].min(), results_df['dem_seats'].max() + 2),
            edgecolor='black', alpha=0.7, color='steelblue', align='left')

    # Add mean line
    mean_seats = results_df['dem_seats'].mean()
    ax.axvline(mean_seats, color='red', linestyle='--',
               linewidth=2, label=f'Mean: {mean_seats:.1f}')

    # Highlight selected plan if provided
    if selected_plan_id is not None:
        selected_seats = results_df[results_df['plan_id'] == selected_plan_id]['dem_seats'].values[0]
        ax.axvline(selected_seats, color='orange', linestyle='--',
                   linewidth=3, label=f'Selected Plan {selected_plan_id}: {selected_seats} seats')

    ax.set_xlabel('Democratic Seats (out of 14)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency (Number of Plans)', fontsize=12, fontweight='bold')
    ax.set_title('Democratic Seat Distribution Across All Plans',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(range(0, 15))
    ax.grid(True, alpha=0.3, axis='y')
    ax.legend(fontsize=10)

    plt.tight_layout()
    return fig


def main():
    """Main dashboard application."""

    # Title and header
    st.title("📊 Baseline Election Simulation Dashboard")
    st.markdown("### Exploring Random Single-Member District Plans")
    st.markdown("---")

    # Determine paths
    base_dir = Path(__file__).parent.parent
    csv_path = base_dir / "outputs" / "baseline_ensemble.csv"
    outputs_dir = base_dir / "outputs"

    # Check if results exist
    if not csv_path.exists():
        st.error(f"❌ Results not found at: {csv_path}")
        st.info("""
        **Please run the baseline simulation first:**

        ```bash
        cd fra_pipeline
        python scripts/run_baseline_simple.py
        ```
        """)
        return

    # Load results
    with st.spinner("Loading results..."):
        results_df = load_ensemble_results(csv_path)

    st.success(f"✅ Loaded {len(results_df)} plans")

    # Sidebar - Plan selector
    st.sidebar.header("📋 Select Plan")

    plan_id = st.sidebar.number_input(
        "Plan ID (0-9):",
        min_value=int(results_df['plan_id'].min()),
        max_value=int(results_df['plan_id'].max()),
        value=int(results_df['plan_id'].min()),
        step=1
    )

    # Get selected plan data
    selected_plan = results_df[results_df['plan_id'] == plan_id].iloc[0]

    # Sidebar - Display selected plan metrics
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"📊 Plan {plan_id} Results")

    st.sidebar.metric(
        "Democratic Seats",
        f"{selected_plan['dem_seats']}/14",
        delta=None
    )

    st.sidebar.metric(
        "Republican Seats",
        f"{selected_plan['rep_seats']}/14",
        delta=None
    )

    if 'dem_seat_share' in selected_plan:
        st.sidebar.metric(
            "Democratic Seat Share",
            f"{selected_plan['dem_seat_share']:.1%}"
        )

    # Main content area
    st.markdown("## 📈 Overall Statistics")

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Plans",
            len(results_df)
        )

    with col2:
        avg_dem = results_df['dem_seats'].mean()
        st.metric(
            "Avg Dem Seats",
            f"{avg_dem:.1f}/14"
        )

    with col3:
        min_dem = results_df['dem_seats'].min()
        max_dem = results_df['dem_seats'].max()
        st.metric(
            "Min Dem Seats",
            f"{min_dem}/14"
        )

    with col4:
        st.metric(
            "Max Dem Seats",
            f"{max_dem}/14"
        )

    # Histogram
    st.markdown("---")
    st.markdown("## 📊 Seat Distribution Across All Plans")

    fig_hist = plot_histogram(results_df, plan_id)
    st.pyplot(fig_hist)
    plt.close()

    # Plan details section
    st.markdown("---")
    st.markdown(f"## 🔍 Plan {plan_id} Details")

    # Try to load district-level results
    district_df = load_district_results(plan_id, outputs_dir)

    if district_df is not None:
        st.markdown("### District-Level Results")

        # Calculate vote margins
        district_df['margin'] = abs(district_df['dem_votes'] - district_df['rep_votes'])
        district_df['margin_pct'] = (district_df['margin'] /
                                     (district_df['dem_votes'] + district_df['rep_votes']) * 100)

        # Display table
        display_cols = ['district_id', 'dem_votes', 'rep_votes', 'population', 'winner', 'margin']

        if all(col in district_df.columns for col in display_cols):
            st.dataframe(
                district_df[display_cols].sort_values('district_id'),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.dataframe(district_df, use_container_width=True, hide_index=True)

        # Summary statistics
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("#### Seat Summary")
            dem_wins = (district_df['winner'] == 'Democrat').sum()
            rep_wins = (district_df['winner'] == 'Republican').sum()

            seat_summary = pd.DataFrame({
                'Party': ['Democrat', 'Republican', 'Total'],
                'Seats Won': [dem_wins, rep_wins, dem_wins + rep_wins]
            })
            st.table(seat_summary)

        with col_b:
            st.markdown("#### Vote Totals")
            total_dem = district_df['dem_votes'].sum()
            total_rep = district_df['rep_votes'].sum()
            total_votes = total_dem + total_rep

            vote_summary = pd.DataFrame({
                'Party': ['Democrat', 'Republican', 'Total'],
                'Votes': [f"{total_dem:,}", f"{total_rep:,}", f"{total_votes:,}"],
                'Share': [f"{total_dem/total_votes*100:.1f}%",
                         f"{total_rep/total_votes*100:.1f}%",
                         "100.0%"]
            })
            st.table(vote_summary)

    else:
        st.info(f"District-level results not found for Plan {plan_id}")
        st.markdown("**Plan Summary:**")
        st.write(selected_plan.to_dict())

    # Full results table
    st.markdown("---")
    st.markdown("## 📋 All Plans Summary")

    # Format display dataframe
    display_df = results_df.copy()

    # Add formatted columns if they exist
    if 'dem_seat_share' in display_df.columns:
        display_df['dem_share_pct'] = (display_df['dem_seat_share'] * 100).round(1)

    # Rename for display
    rename_dict = {
        'plan_id': 'Plan',
        'dem_seats': 'Dem Seats',
        'rep_seats': 'Rep Seats'
    }

    if 'dem_share_pct' in display_df.columns:
        rename_dict['dem_share_pct'] = 'Dem %'

    display_df = display_df.rename(columns=rename_dict)

    # Select and display columns
    display_cols = [col for col in ['Plan', 'Dem Seats', 'Rep Seats', 'Dem %']
                   if col in display_df.columns]

    st.dataframe(
        display_df[display_cols],
        use_container_width=True,
        hide_index=True
    )

    # Footer
    st.markdown("---")
    st.markdown("""
    **About This Simulation:**
    - Generated random district plans using GerryChain's ReCom algorithm
    - Each district uses **winner-take-all** (single-member plurality voting)
    - All districts are contiguous and meet population balance requirements
    - These results serve as the baseline for comparing with FRA (multi-member proportional) outcomes

    **Next Step:** Run FRA simulation to see how proportional representation changes results
    """)


if __name__ == "__main__":
    main()
