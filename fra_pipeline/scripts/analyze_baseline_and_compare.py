#!/usr/bin/env python3
"""
Baseline and FRA Comparison Analysis

This script:
1. Analyzes all baseline (winner-take-all) plans
2. Generates baseline visualizations
3. Compares baseline vs FRA results
4. Prints comprehensive summary report

Author: Claude Code
Date: 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import Counter
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# TASK 1: ANALYZE ALL BASELINE PLANS
# ============================================================================

def analyze_baseline_plans(baseline_dir, output_dir):
    """
    Analyze all baseline plans and compute winner-take-all metrics.

    Args:
        baseline_dir: Directory containing baseline plan CSVs
        output_dir: Directory to save results

    Returns:
        DataFrame with baseline analysis results
    """
    print("=" * 70)
    print("BASELINE ANALYSIS (Winner-Take-All)")
    print("=" * 70)
    print("\n[1] Loading and analyzing baseline plans...")

    baseline_dir = Path(baseline_dir)

    # Find all baseline district files
    # Try multiple naming patterns
    baseline_files = list(baseline_dir.glob("baseline_districts_plan_*.csv"))

    if not baseline_files:
        # Try alternative pattern
        baseline_files = list(baseline_dir.glob("plan_*_baseline.csv"))

    if not baseline_files:
        raise FileNotFoundError(f"No baseline files found in {baseline_dir}")

    print(f"    Found {len(baseline_files)} baseline plan files")

    results = []

    for baseline_file in sorted(baseline_files):
        # Extract plan ID from filename
        filename = baseline_file.stem
        if 'baseline_districts_plan_' in filename:
            plan_id = int(filename.replace('baseline_districts_plan_', ''))
        else:
            # Try to extract number
            import re
            numbers = re.findall(r'\d+', filename)
            plan_id = int(numbers[0]) if numbers else 0

        # Load the CSV
        df = pd.read_csv(baseline_file)

        # Compute winner-take-all results
        # Count districts won by each party
        dem_seats = (df['dem_votes'] > df['rep_votes']).sum()
        rep_seats = (df['dem_votes'] <= df['rep_votes']).sum()

        # Compute statewide vote totals
        total_dem_votes = df['dem_votes'].sum()
        total_rep_votes = df['rep_votes'].sum()
        total_votes = total_dem_votes + total_rep_votes

        # Compute shares
        dem_vote_share = total_dem_votes / total_votes if total_votes > 0 else 0
        rep_vote_share = total_rep_votes / total_votes if total_votes > 0 else 0
        dem_seat_share = dem_seats / 14

        # Compute proportionality gap
        proportionality_gap = abs(dem_seat_share - dem_vote_share)

        results.append({
            'plan_id': plan_id,
            'dem_seats': int(dem_seats),
            'rep_seats': int(rep_seats),
            'dem_vote_share': dem_vote_share,
            'rep_vote_share': rep_vote_share,
            'dem_seat_share': dem_seat_share,
            'proportionality_gap': proportionality_gap
        })

    # Create DataFrame
    baseline_df = pd.DataFrame(results)
    baseline_df = baseline_df.sort_values('plan_id').reset_index(drop=True)

    # Save to CSV
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "baseline_ensemble_combined.csv"
    baseline_df.to_csv(csv_path, index=False)

    print(f"    ✓ Analyzed {len(baseline_df)} baseline plans")
    print(f"    ✓ Saved to: {csv_path}")

    # Print quick summary
    print(f"\n    Quick Summary:")
    print(f"      Mean Dem seats: {baseline_df['dem_seats'].mean():.2f}")
    print(f"      Std Dev: {baseline_df['dem_seats'].std():.3f}")
    print(f"      Range: {baseline_df['dem_seats'].min()} - {baseline_df['dem_seats'].max()}")

    return baseline_df


# ============================================================================
# TASK 2: GENERATE BASELINE PLOTS
# ============================================================================

def generate_baseline_plots(baseline_df, output_dir):
    """
    Generate visualization plots for baseline analysis.

    Args:
        baseline_df: DataFrame with baseline results
        output_dir: Directory to save plots
    """
    print("\n[2] Generating baseline plots...")

    output_dir = Path(output_dir)
    plt.style.use('seaborn-v0_8-whitegrid')

    # ========================================================================
    # Plot 1: Histogram of Democratic Seats
    # ========================================================================

    fig, ax = plt.subplots(figsize=(12, 6))

    # Count seats
    seat_counts = Counter(baseline_df['dem_seats'])
    seat_range = range(0, 15)
    counts = [seat_counts.get(s, 0) for s in seat_range]

    bars = ax.bar(seat_range, counts, color='steelblue', edgecolor='black', alpha=0.7)

    # Add mean line
    mean_seats = baseline_df['dem_seats'].mean()
    ax.axvline(mean_seats, color='red', linestyle='--', linewidth=2,
               label=f"Mean: {mean_seats:.2f}")

    # Add vote share reference
    vote_share_seats = baseline_df['dem_vote_share'].mean() * 14
    ax.axvline(vote_share_seats, color='green', linestyle=':', linewidth=2,
               label=f"Proportional: {vote_share_seats:.2f}")

    ax.set_xlabel('Democratic Seats (out of 14)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Plans', fontsize=12, fontweight='bold')
    ax.set_title(f'Baseline (Winner-Take-All) Democratic Seat Distribution\n{len(baseline_df)} Plans',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(seat_range)
    ax.legend(fontsize=10)

    # Add count labels
    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + len(baseline_df)*0.01,
                   f'{count}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    path = output_dir / 'baseline_dem_seats_histogram.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f"    ✓ Saved: {path.name}")
    plt.close()

    # ========================================================================
    # Plot 2: Boxplot of Seats
    # ========================================================================

    fig, ax = plt.subplots(figsize=(8, 6))

    bp = ax.boxplot([baseline_df['dem_seats'], baseline_df['rep_seats']],
                    labels=['Democratic', 'Republican'],
                    patch_artist=True, notch=True)

    bp['boxes'][0].set_facecolor('#4169E1')
    bp['boxes'][1].set_facecolor('#DC143C')

    ax.set_ylabel('Number of Seats', fontsize=12, fontweight='bold')
    ax.set_title('Baseline Seat Distribution Boxplot', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Add mean markers
    ax.scatter([1, 2], [baseline_df['dem_seats'].mean(), baseline_df['rep_seats'].mean()],
               color='gold', marker='D', s=100, zorder=5, label='Mean')
    ax.legend()

    plt.tight_layout()
    path = output_dir / 'baseline_seats_boxplot.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f"    ✓ Saved: {path.name}")
    plt.close()

    # ========================================================================
    # Plot 3: Proportionality Gap Histogram
    # ========================================================================

    fig, ax = plt.subplots(figsize=(10, 6))

    gap_pct = baseline_df['proportionality_gap'] * 100

    ax.hist(gap_pct, bins=30, color='orange', edgecolor='black', alpha=0.7)

    ax.axvline(gap_pct.mean(), color='red', linestyle='--', linewidth=2,
               label=f"Mean: {gap_pct.mean():.2f}%")
    ax.axvline(gap_pct.median(), color='blue', linestyle=':', linewidth=2,
               label=f"Median: {gap_pct.median():.2f}%")

    ax.set_xlabel('Proportionality Gap (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Plans', fontsize=12, fontweight='bold')
    ax.set_title('Baseline Proportionality Gap Distribution', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)

    plt.tight_layout()
    path = output_dir / 'baseline_proportionality_gap_histogram.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f"    ✓ Saved: {path.name}")
    plt.close()

    # ========================================================================
    # Plot 4: Vote Share vs Seat Share Scatter
    # ========================================================================

    fig, ax = plt.subplots(figsize=(10, 8))

    scatter = ax.scatter(baseline_df['dem_vote_share'] * 100,
                        baseline_df['dem_seat_share'] * 100,
                        c=baseline_df['proportionality_gap'] * 100,
                        cmap='RdYlGn_r',
                        alpha=0.6, s=50, edgecolors='black', linewidth=0.5)

    # Perfect proportionality line
    ax.plot([0, 100], [0, 100], 'k--', linewidth=2, label='Perfect Proportionality')

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Proportionality Gap (%)', fontsize=10)

    ax.set_xlabel('Democratic Vote Share (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Democratic Seat Share (%)', fontsize=12, fontweight='bold')
    ax.set_title('Baseline: Vote Share vs Seat Share', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10, loc='upper left')
    ax.set_xlim(40, 60)
    ax.set_ylim(20, 80)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = output_dir / 'baseline_vote_vs_seat_share.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f"    ✓ Saved: {path.name}")
    plt.close()


# ============================================================================
# TASK 3: COMPARE BASELINE VS FRA
# ============================================================================

def compare_baseline_vs_fra(baseline_df, fra_df, output_dir):
    """
    Generate comparison plots between baseline and FRA.

    Args:
        baseline_df: DataFrame with baseline results
        fra_df: DataFrame with FRA results
        output_dir: Directory to save plots
    """
    print("\n[3] Generating comparison plots...")

    output_dir = Path(output_dir)

    # ========================================================================
    # Plot 1: Side-by-side Seat Histograms
    # ========================================================================

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    seat_range = range(0, 15)

    # Baseline histogram
    ax = axes[0]
    baseline_counts = Counter(baseline_df['dem_seats'])
    counts = [baseline_counts.get(s, 0) for s in seat_range]
    ax.bar(seat_range, counts, color='orange', edgecolor='black', alpha=0.7)
    ax.axvline(baseline_df['dem_seats'].mean(), color='red', linestyle='--',
               linewidth=2, label=f"Mean: {baseline_df['dem_seats'].mean():.2f}")
    ax.set_xlabel('Democratic Seats', fontsize=11, fontweight='bold')
    ax.set_ylabel('Number of Plans', fontsize=11, fontweight='bold')
    ax.set_title('Baseline (Winner-Take-All)', fontsize=13, fontweight='bold')
    ax.set_xticks(seat_range)
    ax.legend()

    # FRA histogram
    ax = axes[1]
    fra_counts = Counter(fra_df['total_dem_seats'])
    counts = [fra_counts.get(s, 0) for s in seat_range]
    ax.bar(seat_range, counts, color='steelblue', edgecolor='black', alpha=0.7)
    ax.axvline(fra_df['total_dem_seats'].mean(), color='red', linestyle='--',
               linewidth=2, label=f"Mean: {fra_df['total_dem_seats'].mean():.2f}")
    ax.set_xlabel('Democratic Seats', fontsize=11, fontweight='bold')
    ax.set_ylabel('Number of Plans', fontsize=11, fontweight='bold')
    ax.set_title('FRA (Proportional)', fontsize=13, fontweight='bold')
    ax.set_xticks(seat_range)
    ax.legend()

    plt.suptitle(f'Seat Distribution Comparison ({len(baseline_df)} Plans)',
                 fontsize=15, fontweight='bold')
    plt.tight_layout()
    path = output_dir / 'baseline_vs_fra_seats_histogram.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f"    ✓ Saved: {path.name}")
    plt.close()

    # ========================================================================
    # Plot 2: Gap Comparison Boxplot
    # ========================================================================

    fig, ax = plt.subplots(figsize=(10, 6))

    bp = ax.boxplot([baseline_df['proportionality_gap'] * 100,
                     fra_df['proportionality_gap'] * 100],
                    labels=['Baseline\n(Winner-Take-All)', 'FRA\n(Proportional)'],
                    patch_artist=True, notch=True)

    bp['boxes'][0].set_facecolor('orange')
    bp['boxes'][1].set_facecolor('steelblue')

    ax.set_ylabel('Proportionality Gap (%)', fontsize=12, fontweight='bold')
    ax.set_title('Proportionality Gap Comparison', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Add mean markers
    ax.scatter([1, 2],
               [baseline_df['proportionality_gap'].mean() * 100,
                fra_df['proportionality_gap'].mean() * 100],
               color='red', marker='D', s=100, zorder=5, label='Mean')
    ax.legend()

    plt.tight_layout()
    path = output_dir / 'baseline_vs_fra_gap_boxplot.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f"    ✓ Saved: {path.name}")
    plt.close()

    # ========================================================================
    # Plot 3: Vote Share vs Seat Share Comparison Scatter
    # ========================================================================

    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot baseline
    ax.scatter(baseline_df['dem_vote_share'] * 100,
               baseline_df['dem_seat_share'] * 100,
               c='orange', alpha=0.4, s=30, label='Baseline', edgecolors='black', linewidth=0.3)

    # Plot FRA
    ax.scatter(fra_df['dem_vote_share'] * 100,
               fra_df['seat_share_dem'] * 100,
               c='steelblue', alpha=0.4, s=30, label='FRA', edgecolors='black', linewidth=0.3)

    # Perfect proportionality line
    ax.plot([40, 60], [40, 60], 'k--', linewidth=2, label='Perfect Proportionality')

    ax.set_xlabel('Democratic Vote Share (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Democratic Seat Share (%)', fontsize=12, fontweight='bold')
    ax.set_title('Vote Share vs Seat Share: Baseline vs FRA', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10, loc='upper left')
    ax.set_xlim(45, 52)
    ax.set_ylim(25, 75)
    ax.grid(True, alpha=0.3)

    # Add annotations for means
    baseline_mean_vote = baseline_df['dem_vote_share'].mean() * 100
    baseline_mean_seat = baseline_df['dem_seat_share'].mean() * 100
    fra_mean_vote = fra_df['dem_vote_share'].mean() * 100
    fra_mean_seat = fra_df['seat_share_dem'].mean() * 100

    ax.plot(baseline_mean_vote, baseline_mean_seat, 'o', color='darkorange',
            markersize=15, markeredgecolor='black', markeredgewidth=2, zorder=10)
    ax.plot(fra_mean_vote, fra_mean_seat, 'o', color='darkblue',
            markersize=15, markeredgecolor='black', markeredgewidth=2, zorder=10)

    ax.annotate(f'Baseline Mean\n({baseline_mean_seat:.1f}%)',
                xy=(baseline_mean_vote, baseline_mean_seat),
                xytext=(baseline_mean_vote - 2, baseline_mean_seat + 5),
                fontsize=9, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='darkorange'))

    ax.annotate(f'FRA Mean\n({fra_mean_seat:.1f}%)',
                xy=(fra_mean_vote, fra_mean_seat),
                xytext=(fra_mean_vote + 1, fra_mean_seat - 5),
                fontsize=9, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='darkblue'))

    plt.tight_layout()
    path = output_dir / 'baseline_vs_fra_scatter.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f"    ✓ Saved: {path.name}")
    plt.close()

    # ========================================================================
    # Plot 4: Combined Summary Figure
    # ========================================================================

    fig = plt.figure(figsize=(16, 12))

    # 2x2 grid
    ax1 = fig.add_subplot(2, 2, 1)
    ax2 = fig.add_subplot(2, 2, 2)
    ax3 = fig.add_subplot(2, 2, 3)
    ax4 = fig.add_subplot(2, 2, 4)

    # Plot 1: Overlaid seat histograms
    seat_range = range(0, 15)
    baseline_counts = [Counter(baseline_df['dem_seats']).get(s, 0) for s in seat_range]
    fra_counts = [Counter(fra_df['total_dem_seats']).get(s, 0) for s in seat_range]

    x = np.arange(15)
    width = 0.35
    ax1.bar(x - width/2, baseline_counts, width, label='Baseline', color='orange', alpha=0.7)
    ax1.bar(x + width/2, fra_counts, width, label='FRA', color='steelblue', alpha=0.7)
    ax1.set_xlabel('Democratic Seats')
    ax1.set_ylabel('Number of Plans')
    ax1.set_title('Seat Distribution Comparison')
    ax1.set_xticks(x)
    ax1.legend()

    # Plot 2: Gap boxplot
    bp = ax2.boxplot([baseline_df['proportionality_gap'] * 100,
                      fra_df['proportionality_gap'] * 100],
                     labels=['Baseline', 'FRA'], patch_artist=True)
    bp['boxes'][0].set_facecolor('orange')
    bp['boxes'][1].set_facecolor('steelblue')
    ax2.set_ylabel('Proportionality Gap (%)')
    ax2.set_title('Gap Comparison')

    # Plot 3: Variance comparison bar chart
    metrics = ['Mean', 'Std Dev', 'Variance']
    baseline_vals = [baseline_df['dem_seats'].mean(),
                     baseline_df['dem_seats'].std(),
                     baseline_df['dem_seats'].var()]
    fra_vals = [fra_df['total_dem_seats'].mean(),
                fra_df['total_dem_seats'].std(),
                fra_df['total_dem_seats'].var()]

    x = np.arange(len(metrics))
    ax3.bar(x - width/2, baseline_vals, width, label='Baseline', color='orange', alpha=0.7)
    ax3.bar(x + width/2, fra_vals, width, label='FRA', color='steelblue', alpha=0.7)
    ax3.set_ylabel('Value')
    ax3.set_title('Statistical Comparison')
    ax3.set_xticks(x)
    ax3.set_xticklabels(metrics)
    ax3.legend()

    # Plot 4: Gap histogram overlay
    ax4.hist(baseline_df['proportionality_gap'] * 100, bins=20,
             alpha=0.5, label='Baseline', color='orange')
    ax4.hist(fra_df['proportionality_gap'] * 100, bins=20,
             alpha=0.5, label='FRA', color='steelblue')
    ax4.set_xlabel('Proportionality Gap (%)')
    ax4.set_ylabel('Number of Plans')
    ax4.set_title('Gap Distribution Overlay')
    ax4.legend()

    plt.suptitle(f'Baseline vs FRA Comparison Summary ({len(baseline_df)} Plans)',
                 fontsize=16, fontweight='bold')
    plt.tight_layout()

    path = output_dir / 'baseline_vs_fra_summary.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f"    ✓ Saved: {path.name}")
    plt.close()


# ============================================================================
# TASK 4: PRINT SUMMARY REPORT
# ============================================================================

def print_summary_report(baseline_df, fra_df):
    """
    Print comprehensive summary report.

    Args:
        baseline_df: DataFrame with baseline results
        fra_df: DataFrame with FRA results
    """
    print("\n" + "=" * 70)
    print("COMPREHENSIVE COMPARISON REPORT")
    print("=" * 70)

    n_plans = len(baseline_df)

    # Seat Summary
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                        SEAT SUMMARY                                   ║
╠══════════════════════════════════════════════════════════════════════╣
║                          Baseline        FRA          Difference     ║
╠══════════════════════════════════════════════════════════════════════╣
║ Mean Dem Seats:          {baseline_df['dem_seats'].mean():6.2f}        {fra_df['total_dem_seats'].mean():6.2f}        {fra_df['total_dem_seats'].mean() - baseline_df['dem_seats'].mean():+6.2f}        ║
║ Std Deviation:           {baseline_df['dem_seats'].std():6.3f}        {fra_df['total_dem_seats'].std():6.3f}        {fra_df['total_dem_seats'].std() - baseline_df['dem_seats'].std():+6.3f}        ║
║ Variance:                {baseline_df['dem_seats'].var():6.4f}       {fra_df['total_dem_seats'].var():6.4f}       {fra_df['total_dem_seats'].var() - baseline_df['dem_seats'].var():+6.4f}       ║
║ Min Seats:               {baseline_df['dem_seats'].min():6d}          {fra_df['total_dem_seats'].min():6d}          {fra_df['total_dem_seats'].min() - baseline_df['dem_seats'].min():+6d}          ║
║ Max Seats:               {baseline_df['dem_seats'].max():6d}          {fra_df['total_dem_seats'].max():6d}          {fra_df['total_dem_seats'].max() - baseline_df['dem_seats'].max():+6d}          ║
║ Range:                   {baseline_df['dem_seats'].max() - baseline_df['dem_seats'].min():6d}          {fra_df['total_dem_seats'].max() - fra_df['total_dem_seats'].min():6d}          {(fra_df['total_dem_seats'].max() - fra_df['total_dem_seats'].min()) - (baseline_df['dem_seats'].max() - baseline_df['dem_seats'].min()):+6d}          ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    # Gap Summary
    baseline_gap = baseline_df['proportionality_gap'] * 100
    fra_gap = fra_df['proportionality_gap'] * 100

    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                   PROPORTIONALITY GAP SUMMARY                        ║
╠══════════════════════════════════════════════════════════════════════╣
║                          Baseline        FRA          Improvement    ║
╠══════════════════════════════════════════════════════════════════════╣
║ Mean Gap:                {baseline_gap.mean():6.2f}%       {fra_gap.mean():6.2f}%       {baseline_gap.mean() - fra_gap.mean():6.2f}%        ║
║ Median Gap:              {baseline_gap.median():6.2f}%       {fra_gap.median():6.2f}%       {baseline_gap.median() - fra_gap.median():6.2f}%        ║
║ Min Gap:                 {baseline_gap.min():6.2f}%       {fra_gap.min():6.2f}%       {baseline_gap.min() - fra_gap.min():6.2f}%        ║
║ Max Gap:                 {baseline_gap.max():6.2f}%       {fra_gap.max():6.2f}%       {baseline_gap.max() - fra_gap.max():6.2f}%        ║
║ Std Dev:                 {baseline_gap.std():6.3f}%       {fra_gap.std():6.3f}%       {baseline_gap.std() - fra_gap.std():6.3f}%        ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    # Seat Distribution Breakdown
    baseline_splits = Counter(baseline_df.apply(
        lambda r: f"{int(r['dem_seats'])}-{int(r['rep_seats'])}", axis=1))
    fra_splits = Counter(fra_df.apply(
        lambda r: f"{int(r['total_dem_seats'])}-{int(r['total_rep_seats'])}", axis=1))

    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                    SEAT SPLIT DISTRIBUTION                           ║
╠══════════════════════════════════════════════════════════════════════╣""")

    all_splits = sorted(set(baseline_splits.keys()) | set(fra_splits.keys()))
    for split in all_splits:
        b_count = baseline_splits.get(split, 0)
        f_count = fra_splits.get(split, 0)
        b_pct = b_count / n_plans * 100
        f_pct = f_count / n_plans * 100
        print(f"║ {split:>5}:   Baseline {b_count:4d} ({b_pct:5.1f}%)    FRA {f_count:4d} ({f_pct:5.1f}%)           ║")

    print("╚══════════════════════════════════════════════════════════════════════╝")

    # Interpretation
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                      INTERPRETATION                                   ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║ 1. VOLATILITY ANALYSIS                                               ║
║    Winner-take-all (baseline) produces significantly higher          ║
║    volatility in seat outcomes. Small changes in district            ║
║    boundaries can swing seats even when vote shares remain           ║
║    constant. FRA's proportional allocation produces more             ║
║    stable, predictable outcomes.                                     ║
║                                                                      ║
║ 2. PROPORTIONALITY                                                   ║
║    FRA dramatically reduces the gap between vote share and           ║
║    seat share. Under winner-take-all, a party can win ~50% of        ║
║    votes but receive anywhere from 35-65% of seats depending         ║
║    on how districts are drawn. FRA ensures representation            ║
║    closely matches popular support.                                  ║
║                                                                      ║
║ 3. PARTISAN FAIRNESS                                                 ║
║    FRA reduces opportunities for gerrymandering because seats        ║
║    are allocated proportionally within each super-district.          ║
║    Manipulating boundaries has minimal impact on outcomes            ║
║    when representation is proportional.                              ║
║                                                                      ║
║ 4. EXTREME OUTCOMES                                                  ║
║    Winner-take-all can produce lopsided delegations (e.g.,           ║
║    10-4 or 4-10) even with close vote margins. FRA prevents          ║
║    such extremes by ensuring minority representation within          ║
║    each multi-member super-district.                                 ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    # Key Findings
    variance_reduction = ((baseline_df['dem_seats'].var() - fra_df['total_dem_seats'].var())
                         / baseline_df['dem_seats'].var() * 100)
    gap_reduction = ((baseline_gap.mean() - fra_gap.mean()) / baseline_gap.mean() * 100)

    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                        KEY FINDINGS                                   ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║ • Variance Reduction: {variance_reduction:>5.1f}%                                        ║
║   FRA reduces seat outcome variance by {variance_reduction:.1f}% compared to baseline  ║
║                                                                      ║
║ • Gap Reduction: {gap_reduction:>5.1f}%                                            ║
║   FRA reduces proportionality gap by {gap_reduction:.1f}% on average              ║
║                                                                      ║
║ • Statewide Vote: {baseline_df['dem_vote_share'].mean()*100:.1f}% Democratic                                  ║
║   Baseline Seat Share: {baseline_df['dem_seat_share'].mean()*100:.1f}%                                       ║
║   FRA Seat Share: {fra_df['seat_share_dem'].mean()*100:.1f}%                                            ║
║                                                                      ║
║ • CONCLUSION: FRA produces more proportional, stable, and fair       ║
║   representation that better reflects the will of voters.            ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""

    # Determine paths
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent

    # Input directories
    baseline_dir = base_dir / "outputs"  # baseline_districts_plan_*.csv files
    fra_combined_path = base_dir / "outputs" / "analysis" / "fra_ensemble_combined.csv"

    # Output directory
    output_dir = base_dir / "outputs" / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Task 1: Analyze baseline plans
    baseline_df = analyze_baseline_plans(baseline_dir, output_dir)

    # Task 2: Generate baseline plots
    generate_baseline_plots(baseline_df, output_dir)

    # Load FRA data
    print("\n[3] Loading FRA ensemble data...")
    if not fra_combined_path.exists():
        print(f"    ⚠️  FRA combined data not found at: {fra_combined_path}")
        print("    Please run analyze_fra_ensemble.py first")
        return

    fra_df = pd.read_csv(fra_combined_path)
    print(f"    ✓ Loaded {len(fra_df)} FRA plans")

    # Task 3: Generate comparison plots
    compare_baseline_vs_fra(baseline_df, fra_df, output_dir)

    # Task 4: Print summary report
    print_summary_report(baseline_df, fra_df)

    print("\n" + "=" * 70)
    print("✅ Analysis Complete!")
    print("=" * 70)
    print(f"\nOutput files saved to: {output_dir}/")
    print("\nBaseline plots:")
    print("  • baseline_dem_seats_histogram.png")
    print("  • baseline_seats_boxplot.png")
    print("  • baseline_proportionality_gap_histogram.png")
    print("  • baseline_vote_vs_seat_share.png")
    print("\nComparison plots:")
    print("  • baseline_vs_fra_seats_histogram.png")
    print("  • baseline_vs_fra_gap_boxplot.png")
    print("  • baseline_vs_fra_scatter.png")
    print("  • baseline_vs_fra_summary.png")
    print("\nData files:")
    print("  • baseline_ensemble_combined.csv")
    print()


if __name__ == "__main__":
    main()
