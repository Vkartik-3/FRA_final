# Shapefile Provenance: nc_2024_with_population.shp

## Status

`nc_2024_with_population.shp` is an **externally prepared input artifact**.
The repository validates it (see below) but does not recreate it from raw
source files.  The join process was performed outside the repo.

---

## Column Definitions

| Column | Meaning | Source |
|--------|---------|--------|
| `TOTPOP` | Total population per precinct | 2020 Census / redistricting data |
| `G24PREDHAR` | 2024 Presidential votes cast for Kamala Harris (Democrat) | NC State Board of Elections |
| `G24PRERTRU` | 2024 Presidential votes cast for Donald Trump (Republican) | NC State Board of Elections |

Column name convention: `G24PRE` = 2024 General Presidential; `DHAR` = Harris; `RTRU` = Trump.

---

## Recommended Data Sources

| Source | What it provides | URL |
|--------|-----------------|-----|
| NC State Board of Elections (NCSBE) | Precinct-level 2024 General Election results | https://www.ncsbe.gov/results-data/election-results/historical-election-results-data |
| NCSBE Shapefiles | Precinct boundary shapefiles | https://dl.ncsbe.gov/?prefix=ShapeFiles/Precinct/ |
| Redistricting Data Hub | Pre-merged shapefiles with election results | https://redistrictingdatahub.org/state/north-carolina/ |

The Redistricting Data Hub is the easiest path: it provides a single shapefile
with geometry and election results already joined and column-normalised.

---

## Validation

Run the following to confirm the shapefile satisfies all pipeline requirements:

```bash
cd fra_pipeline
python scripts/verify_shapefile.py
```

`verify_shapefile.py` checks:

- Required columns present (`TOTPOP`, `G24PREDHAR`, `G24PRERTRU`)
- No null values in any required column
- No duplicate index values
- Zero or negative population precincts flagged
- Statewide vote totals printed for manual cross-check against published NCSBE figures

---

## Known Limitations

- The upstream join process (merging NCSBE election CSVs with precinct
  boundaries) is **not scripted in this repository**.  It was performed
  externally, likely in QGIS or with a standalone GeoPandas script.
- `verify_shapefile.py` cannot verify that vote totals match the published
  NCSBE statewide totals because it has no internet access.  Cross-check
  manually using the NCSBE website.
- A future improvement would be to add a `build_shapefile.py` script that
  downloads raw NCSBE data and produces `nc_2024_with_population.shp`
  reproducibly from scratch.

---

## CRS

The pipeline reads the CRS as-is.  `dashboard_fra.py` reprojects to
`EPSG:4326` (WGS 84) for web mapping if the file is in a different projection.
`verify_shapefile.py` prints the CRS so it can be recorded manually.
