---
applyTo: "src/**/*.py"
---

## Source module conventions

These modules are the shared foundation — every notebook depends on them. Changes here affect all downstream analysis.

`data_loader.py` is the single source of truth for data loading. It must:
- Handle all file path resolution relative to project root
- Investigate zero values in Radnett and handle appropriately based on per-station analysis
- Parse Civil Defence WKT POINT format into separate lat/lon columns (note: format is lon, lat order)
- Convert Civil Defence units from Sv/h to µSv/h (multiply by 1e6)
- Extract rainfall, snow_depth, measurement_point_name from the metadata dict-string column
- Add a station_type column to Radnett data based on naming convention: "(Luftfilter)" → air_filter, "Mobil" → mobile, others → fixed
- Classify fixed stations as ground vs building based on DSA report or external reference
- Return typed DataFrames (or GeoDataFrames for spatial data)
- Flag but never silently drop suspicious values — analysis notebooks decide what to exclude

`schemas.py` uses Pandera to define data contracts:
- Define expected types, ranges, and nullability for each column
- Coordinate bounds should reflect Norway + Svalbard (approximately lat 55-82, lon 4-32)
- Schemas validate after cleaning, not before — raw data is expected to have issues
- Schema violations should be logged, not raise exceptions during EDA phase

`utils.py` provides:
- Consistent matplotlib/seaborn style configuration applied at import time
- Color constants for station types
- `save_figure(fig, name)` saving to `figures/` directory in publication-ready format
- `classify_uptime(pct: float) -> str` for categorizing station reliability
- Norway basemap helper for geographic plots including Svalbard

All functions must have type hints and Google-style docstrings.
All modules must be importable without side effects — no file reads or prints at module level.
