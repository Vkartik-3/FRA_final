#!/usr/bin/env python3
"""
Plot Baseline Results

Reads baseline_ensemble.csv and creates a histogram of Democratic seat counts.
Saves output as baseline_hist.png
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys


def plot_baseline_histogram(csv_path, output_path):
    """
    Create histogram of Democratic seat distribution from baseline ensemble.

    Args:
        csv_path: Path to baseline_ensemble.csv
        output_path: Path to save histogram PNG

    Returns:
        True if successful, False otherwise
    """

    print("=" * 60)
    print("📈 BASELINE RESULTS VISUALIZATION")
    print("=" * 60)

    # Check if CSV exists
    if not Path(csv_path).exists():
        print(f"\n❌ ERROR: Results file not found at {csv_path}")
        print("   Please run 'python scripts/run_baseline_simple.py' first")
        return False

    # Load data
    print(f"\n📂 Loading results from: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(df)} plans")
    except Exception as e:
        print(f"❌ ERROR loading CSV: {e}")
        return False

    # Validate data
    required_cols = ['plan_id', 'dem_seats', 'rep_seats']
    if not all(col in df.columns for col in required_cols):
        print(f"❌ ERROR: CSV missing required columns: {required_cols}")
        return False

    # Summary statistics
    print(f"\n📊 Summary Statistics:")
    print(f"   Number of plans: {len(df)}")
    print(f"   Democratic seats:")
    print(f"      Mean:   {df['dem_seats'].mean():.2f}")
    print(f"      Median: {df['dem_seats'].median():.0f}")
    print(f"      Min:    {df['dem_seats'].min()}")
    print(f"      Max:    {df['dem_seats'].max()}")
    print(f"      Std:    {df['dem_seats'].std():.2f}")

    # Create histogram
    print(f"\n🎨 Creating histogram...")

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot histogram
    ax.hist(df['dem_seats'], bins=range(df['dem_seats'].min(), df['dem_seats'].max() + 2),
            edgecolor='black', alpha=0.7, color='steelblue', align='left')

    # Add mean line
    mean_seats = df['dem_seats'].mean()
    ax.axvline(mean_seats, color='red', linestyle='--',
               linewidth=2, label=f'Mean: {mean_seats:.2f}')

    # Styling
    ax.set_xlabel('Democratic Seats (out of 14)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency (Number of Plans)', fontsize=12, fontweight='bold')
    ax.set_title('Baseline Ensemble: Democratic Seat Distribution\n(10 Random Single-Member District Plans)',
                 fontsize=14, fontweight='bold', pad=20)

    # Set x-axis to show all possible seat counts
    ax.set_xticks(range(0, 15))
    ax.grid(True, alpha=0.3, axis='y')
    ax.legend(fontsize=11, loc='upper right')

    plt.tight_layout()

    # Save figure
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Saved histogram to: {output_path}")

    # Also show vote share info
    if 'dem_seat_share' in df.columns:
        print(f"\n🗳️  Democratic Seat Share:")
        print(f"   Mean:   {df['dem_seat_share'].mean():.3f} ({df['dem_seat_share'].mean()*100:.1f}%)")
        print(f"   Min:    {df['dem_seat_share'].min():.3f} ({df['dem_seat_share'].min()*100:.1f}%)")
        print(f"   Max:    {df['dem_seat_share'].max():.3f} ({df['dem_seat_share'].max()*100:.1f}%)")

    print("\n" + "=" * 60)
    print("✅ Visualization complete")
    print("=" * 60)

    return True


def main():
    """Main execution function."""

    # Determine paths
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent

    csv_path = base_dir / "outputs" / "baseline_ensemble.csv"
    output_path = base_dir / "outputs" / "baseline_hist.png"

    # Create visualization
    success = plot_baseline_histogram(csv_path, output_path)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
