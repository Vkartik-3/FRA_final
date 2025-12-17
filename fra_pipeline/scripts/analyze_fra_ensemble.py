#!/usr/bin/env python3
"""
FRA Ensemble Analysis - Analyze Distribution Across 1000 Plans

This script analyzes the FRA output distribution across all generated plans,
computing statistics, creating visualizations, and producing a summary report.

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


def load_all_fra_results(fra_dir):
    """
    Load all FRA result files and compute metrics for each plan.

    Args:
        fra_dir: Path to the fra output directory

    Returns:
        DataFrame with combined results for all plans
    """
    print("=" * 70)
    print("FRA ENSEMBLE ANALYSIS")
    print("=" * 70)
    print("\n[1] Loading all FRA result files...")

    fra_dir = Path(fra_dir)

    # Find all fra_results files
    fra_files = sorted(fra_dir.glob("fra_results_*.csv"))

    if not fra_files:
        raise FileNotFoundError(f"No FRA result files found in {fra_dir}")

    print(f"    Found {len(fra_files)} FRA result files")

    # Process each file
    results = []

    for fra_file in fra_files:
        # Extract plan ID from filename
        plan_id = int(fra_file.stem.split('_')[-1])

        # Load the CSV
        df = pd.read_csv(fra_file)

        # Compute totals
        total_dem_seats = df['dem_seats'].sum()
        total_rep_seats = df['rep_seats'].sum()
        total_dem_votes = df['dem_votes'].sum()
        total_rep_votes = df['rep_votes'].sum()
        total_votes = total_dem_votes + total_rep_votes

        # Compute shares
        dem_vote_share = total_dem_votes / total_votes if total_votes > 0 else 0
        rep_vote_share = total_rep_votes / total_votes if total_votes > 0 else 0
        seat_share_dem = total_dem_seats / 14

        # Compute proportionality gap
        proportionality_gap = abs(seat_share_dem - dem_vote_share)

        results.append({
            'plan_id': plan_id,
            'total_dem_seats': int(total_dem_seats),
            'total_rep_seats': int(total_rep_seats),
            'dem_vote_share': dem_vote_share,
            'rep_vote_share': rep_vote_share,
            'seat_share_dem': seat_share_dem,
            'proportionality_gap': proportionality_gap
        })

    # Create DataFrame
    combined_df = pd.DataFrame(results)
    combined_df = combined_df.sort_values('plan_id').reset_index(drop=True)

    print(f"    ✓ Loaded and processed {len(combined_df)} plans")

    return combined_df


def compute_distribution_statistics(df):
    """
    Compute comprehensive distribution statistics.

    Args:
        df: Combined DataFrame with all plan results

    Returns:
        Dictionary with all statistics
    """
    print("\n[2] Computing distribution statistics...")

    stats = {}

    # ========================================================================
    # 1. Seat Distribution
    # ========================================================================

    # Count seat splits
    seat_splits = df.apply(
        lambda row: f"{int(row['total_dem_seats'])}-{int(row['total_rep_seats'])}",
        axis=1
    )
    split_counts = Counter(seat_splits)

    stats['seat_splits'] = dict(split_counts.most_common())
    stats['modal_outcome'] = split_counts.most_common(1)[0][0]
    stats['modal_count'] = split_counts.most_common(1)[0][1]

    # Specific splits
    stats['split_7_7'] = split_counts.get('7-7', 0)
    stats['split_6_8'] = split_counts.get('6-8', 0)
    stats['split_8_6'] = split_counts.get('8-6', 0)

    print(f"    Seat split distribution:")
    for split, count in split_counts.most_common():
        pct = count / len(df) * 100
        print(f"      {split}: {count} plans ({pct:.1f}%)")

    # ========================================================================
    # 2. Histogram Values
    # ========================================================================

    dem_seat_counts = Counter(df['total_dem_seats'])
    stats['dem_seat_histogram'] = {int(k): v for k, v in sorted(dem_seat_counts.items())}

    print(f"\n    Democratic seat histogram:")
    for seats in range(15):
        count = dem_seat_counts.get(seats, 0)
        if count > 0:
            bar = "█" * int(count / len(df) * 50)
            print(f"      {seats:2d} seats: {count:4d} plans ({count/len(df)*100:5.1f}%) {bar}")

    # ========================================================================
    # 3. Variance
    # ========================================================================

    stats['dem_seats_mean'] = df['total_dem_seats'].mean()
    stats['dem_seats_std'] = df['total_dem_seats'].std()
    stats['dem_seats_var'] = df['total_dem_seats'].var()

    stats['rep_seats_mean'] = df['total_rep_seats'].mean()
    stats['rep_seats_std'] = df['total_rep_seats'].std()
    stats['rep_seats_var'] = df['total_rep_seats'].var()

    print(f"\n    Variance statistics:")
    print(f"      Dem seats - Mean: {stats['dem_seats_mean']:.2f}, Std: {stats['dem_seats_std']:.3f}, Var: {stats['dem_seats_var']:.4f}")
    print(f"      Rep seats - Mean: {stats['rep_seats_mean']:.2f}, Std: {stats['rep_seats_std']:.3f}, Var: {stats['rep_seats_var']:.4f}")

    # ========================================================================
    # 4. Proportionality Gap Stats
    # ========================================================================

    gap = df['proportionality_gap']

    stats['gap_mean'] = gap.mean()
    stats['gap_median'] = gap.median()
    stats['gap_min'] = gap.min()
    stats['gap_max'] = gap.max()
    stats['gap_std'] = gap.std()

    # 95% confidence interval
    stats['gap_ci_lower'] = np.percentile(gap, 2.5)
    stats['gap_ci_upper'] = np.percentile(gap, 97.5)

    # Percentiles
    stats['gap_25th'] = np.percentile(gap, 25)
    stats['gap_75th'] = np.percentile(gap, 75)

    print(f"\n    Proportionality gap statistics:")
    print(f"      Mean: {stats['gap_mean']*100:.2f}%")
    print(f"      Median: {stats['gap_median']*100:.2f}%")
    print(f"      Min: {stats['gap_min']*100:.2f}%")
    print(f"      Max: {stats['gap_max']*100:.2f}%")
    print(f"      Std Dev: {stats['gap_std']*100:.3f}%")
    print(f"      95% CI: [{stats['gap_ci_lower']*100:.2f}%, {stats['gap_ci_upper']*100:.2f}%]")

    # ========================================================================
    # 5. Stability Analysis
    # ========================================================================

    modal_dem_seats = df['total_dem_seats'].mode()[0]
    plans_at_mode = (df['total_dem_seats'] == modal_dem_seats).sum()
    plans_differ = len(df) - plans_at_mode

    stats['modal_dem_seats'] = int(modal_dem_seats)
    stats['plans_at_mode'] = plans_at_mode
    stats['plans_differ'] = plans_differ
    stats['stability_pct'] = plans_at_mode / len(df) * 100

    # Determine stability level
    if stats['stability_pct'] >= 90:
        stats['stability_level'] = "very high"
    elif stats['stability_pct'] >= 70:
        stats['stability_level'] = "high"
    elif stats['stability_pct'] >= 50:
        stats['stability_level'] = "moderate"
    else:
        stats['stability_level'] = "low"

    print(f"\n    Stability analysis:")
    print(f"      Modal outcome: {modal_dem_seats} Dem seats")
    print(f"      Plans at mode: {plans_at_mode} ({stats['stability_pct']:.1f}%)")
    print(f"      Plans differ: {plans_differ}")
    print(f"      Stability level: {stats['stability_level']}")

    return stats


def create_visualizations(df, stats, output_dir):
    """
    Create and save visualizations.

    Args:
        df: Combined DataFrame
        stats: Statistics dictionary
        output_dir: Directory to save plots
    """
    print("\n[3] Creating visualizations...")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set style
    plt.style.use('seaborn-v0_8-whitegrid')

    # ========================================================================
    # 1. Histogram of Democratic FRA Seats
    # ========================================================================

    fig, ax = plt.subplots(figsize=(12, 6))

    # Create histogram
    seat_range = range(0, 15)
    counts = [stats['dem_seat_histogram'].get(s, 0) for s in seat_range]

    bars = ax.bar(seat_range, counts, color='steelblue', edgecolor='black', alpha=0.7)

    # Color the modal bar differently
    modal_idx = stats['modal_dem_seats']
    if modal_idx < len(bars):
        bars[modal_idx].set_color('darkblue')

    # Add mean line
    ax.axvline(stats['dem_seats_mean'], color='red', linestyle='--', linewidth=2,
               label=f"Mean: {stats['dem_seats_mean']:.2f}")

    # Add vote share reference
    vote_share_seats = df['dem_vote_share'].mean() * 14
    ax.axvline(vote_share_seats, color='green', linestyle=':', linewidth=2,
               label=f"Vote Share: {vote_share_seats:.2f}")

    ax.set_xlabel('Democratic Seats (out of 14)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Plans', fontsize=12, fontweight='bold')
    ax.set_title(f'FRA Democratic Seat Distribution Across {len(df)} Plans',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(seat_range)
    ax.legend(fontsize=10)

    # Add count labels on bars
    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + len(df)*0.01,
                   f'{count}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    hist_path = output_dir / 'fra_dem_seats_histogram.png'
    plt.savefig(hist_path, dpi=150, bbox_inches='tight')
    print(f"    ✓ Saved: {hist_path}")
    plt.close()

    # ========================================================================
    # 2. Boxplot of Dem Seat Variance
    # ========================================================================

    fig, ax = plt.subplots(figsize=(8, 6))

    box_data = [df['total_dem_seats'], df['total_rep_seats']]
    bp = ax.boxplot(box_data, labels=['Democratic', 'Republican'],
                    patch_artist=True, notch=True)

    # Color boxes
    bp['boxes'][0].set_facecolor('#4169E1')
    bp['boxes'][1].set_facecolor('#DC143C')

    ax.set_ylabel('Number of Seats', fontsize=12, fontweight='bold')
    ax.set_title('FRA Seat Distribution Boxplot', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Add mean markers
    ax.scatter([1, 2], [stats['dem_seats_mean'], stats['rep_seats_mean']],
               color='gold', marker='D', s=100, zorder=5, label='Mean')
    ax.legend()

    plt.tight_layout()
    box_path = output_dir / 'fra_seats_boxplot.png'
    plt.savefig(box_path, dpi=150, bbox_inches='tight')
    print(f"    ✓ Saved: {box_path}")
    plt.close()

    # ========================================================================
    # 3. Histogram of Proportionality Gap
    # ========================================================================

    fig, ax = plt.subplots(figsize=(10, 6))

    gap_pct = df['proportionality_gap'] * 100

    ax.hist(gap_pct, bins=30, color='purple', edgecolor='black', alpha=0.7)

    # Add mean and median lines
    ax.axvline(stats['gap_mean']*100, color='red', linestyle='--', linewidth=2,
               label=f"Mean: {stats['gap_mean']*100:.2f}%")
    ax.axvline(stats['gap_median']*100, color='orange', linestyle=':', linewidth=2,
               label=f"Median: {stats['gap_median']*100:.2f}%")

    ax.set_xlabel('Proportionality Gap (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Plans', fontsize=12, fontweight='bold')
    ax.set_title('Distribution of Proportionality Gap Across FRA Plans',
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)

    plt.tight_layout()
    gap_path = output_dir / 'fra_proportionality_gap_histogram.png'
    plt.savefig(gap_path, dpi=150, bbox_inches='tight')
    print(f"    ✓ Saved: {gap_path}")
    plt.close()

    # ========================================================================
    # 4. Scatterplot: Vote Share vs Seat Share
    # ========================================================================

    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot all plans
    scatter = ax.scatter(df['dem_vote_share'] * 100, df['seat_share_dem'] * 100,
                        c=df['proportionality_gap'] * 100, cmap='RdYlGn_r',
                        alpha=0.6, s=50, edgecolors='black', linewidth=0.5)

    # Add perfect proportionality line
    ax.plot([0, 100], [0, 100], 'k--', linewidth=2, label='Perfect Proportionality')

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Proportionality Gap (%)', fontsize=10)

    ax.set_xlabel('Democratic Vote Share (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Democratic Seat Share (%)', fontsize=12, fontweight='bold')
    ax.set_title('Vote Share vs Seat Share Across FRA Plans',
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=10, loc='upper left')
    ax.set_xlim(40, 60)
    ax.set_ylim(40, 60)
    ax.grid(True, alpha=0.3)

    # Add annotation for average
    avg_vote = df['dem_vote_share'].mean() * 100
    avg_seat = df['seat_share_dem'].mean() * 100
    ax.annotate(f'Average\n({avg_vote:.1f}%, {avg_seat:.1f}%)',
                xy=(avg_vote, avg_seat),
                xytext=(avg_vote + 3, avg_seat - 3),
                arrowprops=dict(arrowstyle='->', color='black'),
                fontsize=10, fontweight='bold')

    plt.tight_layout()
    scatter_path = output_dir / 'fra_vote_vs_seat_share.png'
    plt.savefig(scatter_path, dpi=150, bbox_inches='tight')
    print(f"    ✓ Saved: {scatter_path}")
    plt.close()

    # ========================================================================
    # 5. Combined Summary Figure
    # ========================================================================

    fig = plt.figure(figsize=(16, 12))

    # 2x2 grid
    ax1 = fig.add_subplot(2, 2, 1)
    ax2 = fig.add_subplot(2, 2, 2)
    ax3 = fig.add_subplot(2, 2, 3)
    ax4 = fig.add_subplot(2, 2, 4)

    # Plot 1: Seat histogram
    seat_range = range(0, 15)
    counts = [stats['dem_seat_histogram'].get(s, 0) for s in seat_range]
    ax1.bar(seat_range, counts, color='steelblue', edgecolor='black', alpha=0.7)
    ax1.axvline(stats['dem_seats_mean'], color='red', linestyle='--', linewidth=2)
    ax1.set_xlabel('Democratic Seats')
    ax1.set_ylabel('Number of Plans')
    ax1.set_title('Dem Seat Distribution')
    ax1.set_xticks(seat_range)

    # Plot 2: Boxplot
    bp = ax2.boxplot([df['total_dem_seats'], df['total_rep_seats']],
                     labels=['Dem', 'Rep'], patch_artist=True)
    bp['boxes'][0].set_facecolor('#4169E1')
    bp['boxes'][1].set_facecolor('#DC143C')
    ax2.set_ylabel('Seats')
    ax2.set_title('Seat Distribution Boxplot')

    # Plot 3: Gap histogram
    ax3.hist(df['proportionality_gap'] * 100, bins=30, color='purple',
             edgecolor='black', alpha=0.7)
    ax3.axvline(stats['gap_mean']*100, color='red', linestyle='--', linewidth=2)
    ax3.set_xlabel('Proportionality Gap (%)')
    ax3.set_ylabel('Number of Plans')
    ax3.set_title('Proportionality Gap Distribution')

    # Plot 4: Vote vs Seat
    ax4.scatter(df['dem_vote_share'] * 100, df['seat_share_dem'] * 100,
               alpha=0.5, s=20, c='blue')
    ax4.plot([40, 60], [40, 60], 'k--', linewidth=2)
    ax4.set_xlabel('Vote Share (%)')
    ax4.set_ylabel('Seat Share (%)')
    ax4.set_title('Vote Share vs Seat Share')
    ax4.set_xlim(45, 52)
    ax4.set_ylim(42, 58)

    plt.suptitle(f'FRA Ensemble Analysis Summary ({len(df)} Plans)',
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()

    summary_path = output_dir / 'fra_ensemble_summary.png'
    plt.savefig(summary_path, dpi=150, bbox_inches='tight')
    print(f"    ✓ Saved: {summary_path}")
    plt.close()


def print_summary(df, stats):
    """
    Print a clean text summary of the analysis.

    Args:
        df: Combined DataFrame
        stats: Statistics dictionary
    """
    print("\n" + "=" * 70)
    print("FRA ENSEMBLE SUMMARY")
    print("=" * 70)

    total_plans = len(df)

    print(f"""
# FRA Ensemble Summary ({total_plans} Plans)
{'=' * 50}

## Seat Distribution
Most common outcome: {stats['modal_outcome']} seats
Plans with modal outcome: {stats['modal_count']} ({stats['modal_count']/total_plans*100:.1f}%)

Split breakdown:
  • 7-7 split: {stats['split_7_7']} plans ({stats['split_7_7']/total_plans*100:.1f}%)
  • 6-8 split: {stats['split_6_8']} plans ({stats['split_6_8']/total_plans*100:.1f}%)
  • 8-6 split: {stats['split_8_6']} plans ({stats['split_8_6']/total_plans*100:.1f}%)

## Statistical Measures
Mean Democratic seats: {stats['dem_seats_mean']:.2f} / 14
Std Dev: {stats['dem_seats_std']:.3f}
Variance: {stats['dem_seats_var']:.4f}

## Proportionality Gap
Average gap: {stats['gap_mean']*100:.2f}%
Median gap: {stats['gap_median']*100:.2f}%
Min gap: {stats['gap_min']*100:.2f}%
Max gap: {stats['gap_max']*100:.2f}%
95% CI: [{stats['gap_ci_lower']*100:.2f}%, {stats['gap_ci_upper']*100:.2f}%]

## Stability Analysis
Plans at modal outcome: {stats['plans_at_mode']} ({stats['stability_pct']:.1f}%)
Plans differing from mode: {stats['plans_differ']}
FRA stability: {stats['stability_level'].upper()}

## Comparison to Statewide Vote
Statewide Dem vote share: {df['dem_vote_share'].mean()*100:.1f}%
Average FRA Dem seat share: {df['seat_share_dem'].mean()*100:.1f}%
Average proportionality gap: {stats['gap_mean']*100:.2f}%

{'=' * 50}
""")

    # Stability assessment
    if stats['stability_level'] == 'very high':
        stability_msg = "FRA produces highly consistent outcomes across different baseline plans."
    elif stats['stability_level'] == 'high':
        stability_msg = "FRA produces mostly consistent outcomes with minor variation."
    elif stats['stability_level'] == 'moderate':
        stability_msg = "FRA shows moderate variation depending on baseline plan configuration."
    else:
        stability_msg = "FRA outcomes vary significantly based on baseline plan configuration."

    print(f"📊 Conclusion: {stability_msg}")
    print()


def save_combined_csv(df, output_path):
    """
    Save the combined DataFrame to CSV.

    Args:
        df: Combined DataFrame
        output_path: Path to save CSV
    """
    df.to_csv(output_path, index=False)
    print(f"\n[4] Saved combined results to: {output_path}")


def main():
    """Main execution function."""

    # Determine paths
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    fra_dir = base_dir / "outputs" / "fra"
    output_dir = base_dir / "outputs" / "analysis"

    # Load all FRA results
    combined_df = load_all_fra_results(fra_dir)

    # Compute statistics
    stats = compute_distribution_statistics(combined_df)

    # Create visualizations
    create_visualizations(combined_df, stats, output_dir)

    # Save combined CSV
    csv_path = output_dir / "fra_ensemble_combined.csv"
    save_combined_csv(combined_df, csv_path)

    # Print summary
    print_summary(combined_df, stats)

    print("=" * 70)
    print("✅ FRA Ensemble Analysis Complete!")
    print("=" * 70)
    print(f"\nOutput files saved to: {output_dir}/")
    print("  • fra_dem_seats_histogram.png")
    print("  • fra_seats_boxplot.png")
    print("  • fra_proportionality_gap_histogram.png")
    print("  • fra_vote_vs_seat_share.png")
    print("  • fra_ensemble_summary.png")
    print("  • fra_ensemble_combined.csv")
    print()


if __name__ == "__main__":
    main()
