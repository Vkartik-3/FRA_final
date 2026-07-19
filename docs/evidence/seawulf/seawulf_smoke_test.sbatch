#!/bin/bash
#SBATCH --job-name=fra_smoke
#SBATCH --output=docs/evidence/seawulf/smoke_%j.out
#SBATCH --error=docs/evidence/seawulf/smoke_%j.err
#SBATCH --account=pn_roke031220s
#SBATCH --partition=short-28core
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:15:00

set -euo pipefail

cd "$HOME/FRA_final"

source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate fra311

export PROJ_DATA="$CONDA_PREFIX/share/proj"
export PROJ_LIB="$CONDA_PREFIX/share/proj"
export GDAL_DATA="$CONDA_PREFIX/share/gdal"

echo "=== JOB ID ==="
echo "$SLURM_JOB_ID"

echo "=== NODE ==="
hostname

echo "=== WORKING DIRECTORY ==="
pwd

echo "=== PYTHON ==="
which python
python --version

echo "=== ENVIRONMENT ==="
echo "CONDA_PREFIX=$CONDA_PREFIX"
echo "PROJ_DATA=$PROJ_DATA"
echo "GDAL_DATA=$GDAL_DATA"

echo "=== PACKAGE VERSIONS ==="
python - <<'PY'
import geopandas
import shapely
import networkx
import pandas
import numpy
import gerrychain
import pyproj

print("geopandas", geopandas.__version__)
print("shapely", shapely.__version__)
print("networkx", networkx.__version__)
print("pandas", pandas.__version__)
print("numpy", numpy.__version__)
print("gerrychain", gerrychain.__version__)
print("PROJ", pyproj.proj_version_str)
PY

echo "=== SHAPEFILE READ TEST ==="
python - <<'PY'
import geopandas as gpd

path = "fra_pipeline/new_data/nc_2024_with_population.shp"
gdf = gpd.read_file(path)

print("path:", path)
print("rows:", len(gdf))
print("columns:", len(gdf.columns))
print("crs:", gdf.crs)
print("geometry types:", sorted(gdf.geometry.geom_type.unique()))
print("null geometries:", int(gdf.geometry.isna().sum()))
print("empty geometries:", int(gdf.geometry.is_empty.sum()))
print("invalid geometries:", int((~gdf.geometry.is_valid).sum()))
print("SHAPEFILE READ PASSED")
PY

echo "=== SMOKE TEST PASSED ==="
