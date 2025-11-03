import geopandas as gpd

# Corrected relative path
shapefile_path = "NC_VTD/NC_VTD.shp"

gdf = gpd.read_file(shapefile_path)
print("✅ Loaded successfully!")
print("Rows:", len(gdf))
print("Columns:", list(gdf.columns)[:10])
print("CRS:", gdf.crs)
