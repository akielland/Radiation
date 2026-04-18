# Project: DSA Radiation Monitoring System Assessment

## Purpose
Analysis of Norway's radiation monitoring system using operational data. Python-based, notebook-driven, with shared source modules.

## Architecture
- `src/data_loader.py` — Single source of truth for loading cleaned data. All notebooks import from here.
- `src/schemas.py` — Pandera data contracts, validated after cleaning
- `src/utils.py` — Shared plotting style, constants, helper functions
- `notebooks/` — Analysis notebooks, each answering one stated research question
- `figures/` — Publication-ready figures exported from notebooks
- `data/raw/` — Original files (gitignored), `data/processed/` — cleaned outputs
- `tests/` — pytest unit tests mirroring src modules

## Code Standards
- All code, variable names, function names, docstrings, and comments in English
- Notebook markdown narrative may be in Norwegian
- snake_case for all identifiers
- Type hints on all function signatures in `src/`
- Google-style docstrings
- Vectorized pandas — never iterrows()
- Never read raw data files directly in notebooks — always use `data_loader.py`
- GeoPandas for spatial operations
- Matplotlib/seaborn for plotting, styled via `utils.py`
- Save figures via `utils.save_figure()`
- pytest for testing, synthetic fixtures only (no dependency on real data files)

## Dependencies
Python 3.10+: pandas, geopandas, numpy, scipy, matplotlib, seaborn, pandera, openpyxl, statsmodels, scikit-learn, shapely, requests.