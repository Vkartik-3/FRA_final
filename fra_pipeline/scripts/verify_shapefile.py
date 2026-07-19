#!/usr/bin/env python3
"""
Quick test script to verify shapefile structure and columns
"""
import geopandas as gpd
import sys

def verify_shapefile():
    """Verify the NC VTD shapefile structure with extended data-quality checks."""

    shapefile_path = "../new_data/nc_2024_with_population.shp"

    print("=" * 60)
    print("SHAPEFILE VERIFICATION")
    print("=" * 60)

    all_ok = True  # tracks whether any check failed

    try:
        df = gpd.read_file(shapefile_path)

        print(f"\n✅ Shapefile loaded successfully")
        print(f"   Path: {shapefile_path}")
        print(f"\n📊 Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"\n🗺️  CRS: {df.crs}")

        print(f"\n📋 Column Names:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. {col}")

        # ── 1. Required column presence ──────────────────────────────────────
        print(f"\n🗳️  Election Data Columns:")
        required_cols = ['G24PREDHAR', 'G24PRERTRU', 'TOTPOP']
        cols_present = True
        for col in required_cols:
            if col in df.columns:
                print(f"   ✅ {col}: Found")
                print(f"      Sample values: {df[col].head(3).tolist()}")
            else:
                print(f"   ❌ {col}: NOT FOUND")
                cols_present = False
                all_ok = False

        if not cols_present:
            print("\n❌ Stopping — required columns are missing.")
            return False

        # ── 2. Null / missing value check ────────────────────────────────────
        print(f"\n🔍 Null Value Check:")
        for col in required_cols:
            null_count = df[col].isna().sum()
            if null_count == 0:
                print(f"   ✅ {col}: No nulls")
            else:
                print(f"   ❌ {col}: {null_count} null values — rows with nulls will get 0 "
                      f"via .get() fallback in the pipeline")
                all_ok = False

        # ── 3. Duplicate index check ─────────────────────────────────────────
        print(f"\n🔍 Duplicate Index Check:")
        dup_count = df.index.duplicated().sum()
        if dup_count == 0:
            print(f"   ✅ No duplicate index values ({len(df.index)} unique rows)")
        else:
            print(f"   ❌ {dup_count} duplicate index values — graph build may assign "
                  f"precincts incorrectly")
            all_ok = False

        # ── 4. Zero or negative population check ────────────────────────────
        print(f"\n🔍 Population Quality Check:")
        zero_pop = (df['TOTPOP'] <= 0).sum()
        neg_pop  = (df['TOTPOP'] < 0).sum()
        if zero_pop == 0:
            print(f"   ✅ All {len(df)} precincts have TOTPOP > 0")
        else:
            print(f"   ⚠  {zero_pop} precincts have TOTPOP ≤ 0 "
                  f"({neg_pop} negative, {zero_pop - neg_pop} zero) — "
                  f"these will contribute zero weight to population balance")
            # Not a hard failure — unpopulated precincts are valid

        # ── 5. Vote total summary ────────────────────────────────────────────
        print(f"\n📈 Population Statistics:")
        print(f"   Total Population:          {df['TOTPOP'].sum():,}")
        print(f"   Mean per VTD:              {df['TOTPOP'].mean():.0f}")
        print(f"   Target per district (÷14): {df['TOTPOP'].sum() / 14:,.0f}")

        print(f"\n🗳️  Statewide Vote Totals (2024 Presidential):")
        dem_total = df['G24PREDHAR'].sum()
        rep_total = df['G24PRERTRU'].sum()
        total_votes = dem_total + rep_total
        dem_pct = dem_total / total_votes * 100 if total_votes > 0 else 0
        rep_pct = rep_total / total_votes * 100 if total_votes > 0 else 0
        print(f"   Harris (Dem):  {dem_total:>12,}  ({dem_pct:.2f}%)")
        print(f"   Trump  (Rep):  {rep_total:>12,}  ({rep_pct:.2f}%)")
        print(f"   Total votes:   {total_votes:>12,}")

        # Show sample data
        print(f"\n📌 Sample Data (first 3 rows):")
        print(df[required_cols].head(3))

        # ── 6. Final verdict ─────────────────────────────────────────────────
        print(f"\n{'=' * 60}")
        if all_ok:
            print("✅ Verification Complete — Shapefile passed all checks")
        else:
            print("⚠️  Verification Complete — some issues found (see above)")
        print("=" * 60)

        return all_ok

    except FileNotFoundError:
        print(f"\n❌ ERROR: Shapefile not found at {shapefile_path}")
        print("   Please check the path and ensure the file exists.")
        return False

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = verify_shapefile()
    sys.exit(0 if success else 1)
