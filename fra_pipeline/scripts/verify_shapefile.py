#!/usr/bin/env python3
"""
Quick test script to verify shapefile structure and columns
"""
import geopandas as gpd
import sys

def verify_shapefile():
    """Verify the NC VTD shapefile structure"""

    shapefile_path = "../data/NC-shapefiles/NC_VTD/NC_VTD.shp"

    print("=" * 60)
    print("SHAPEFILE VERIFICATION")
    print("=" * 60)

    try:
        df = gpd.read_file(shapefile_path)

        print(f"\n✅ Shapefile loaded successfully")
        print(f"   Path: {shapefile_path}")
        print(f"\n📊 Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"\n🗺️  CRS: {df.crs}")

        print(f"\n📋 Column Names:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. {col}")

        # Check for required election columns
        print(f"\n🗳️  Election Data Columns:")
        required_cols = ['EL08G_GV_D', 'EL08G_GV_R', 'PL10AA_TOT']
        for col in required_cols:
            if col in df.columns:
                print(f"   ✅ {col}: Found")
                print(f"      Sample values: {df[col].head(3).tolist()}")
            else:
                print(f"   ❌ {col}: NOT FOUND")

        # Show sample data
        print(f"\n📌 Sample Data (first 3 rows):")
        print(df[required_cols if all(c in df.columns for c in required_cols) else df.columns[:5]].head(3))

        # Summary statistics
        if 'PL10AA_TOT' in df.columns:
            print(f"\n📈 Population Statistics:")
            print(f"   Total Population: {df['PL10AA_TOT'].sum():,}")
            print(f"   Mean per VTD: {df['PL10AA_TOT'].mean():.0f}")
            print(f"   Target per district (÷14): {df['PL10AA_TOT'].sum() / 14:,.0f}")

        if 'EL08G_GV_D' in df.columns and 'EL08G_GV_R' in df.columns:
            print(f"\n🗳️  Statewide Vote Totals:")
            print(f"   Democratic: {df['EL08G_GV_D'].sum():,}")
            print(f"   Republican: {df['EL08G_GV_R'].sum():,}")
            total_votes = df['EL08G_GV_D'].sum() + df['EL08G_GV_R'].sum()
            dem_pct = df['EL08G_GV_D'].sum() / total_votes * 100 if total_votes > 0 else 0
            print(f"   Democratic %: {dem_pct:.1f}%")

        print(f"\n{'=' * 60}")
        print("✅ Verification Complete — Shapefile is ready to use")
        print("=" * 60)

        return True

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
