# DSA Radiation Monitoring System Assessment — Project Specification

## Purpose
Evaluate Norway's radiation monitoring system using provided datasets.
Deliverables: GitHub repo + 10-minute presentation.

---

## Research Questions

**Q1: How well does the current monitoring system perform?**
- Operational reliability (uptime, data quality)    
- Geographic coverage (gaps, redundancy)  
- Demographic coverage (all, sub-groups)  
- For whom does it work / fail? (population, geography, critical infrastructure)
- Signal quality (noise separation, detection capability). 

**Q2: What is the improvement potential?**
- Analytical: what can be extracted from existing data with extended analysis methods?
- Physical: where should resources be invested?
- Concrete ranked recommendations

---

## Technical Standards

- **Language**: All code, variable names, docstrings, comments in English
- **Notebooks**: Norwegian acceptable in markdown narrative (interview context), English in code
- **Data validation**: Pandera schemas enforced at load time
- **Plotting**: Consistent style via `utils.py`, publication-ready saved to `figures/`
- **Dependencies**: `requirements.txt` pinned, no exotic packages
- **Repo hygiene**: `.gitignore` for data/raw, clear README, FINDINGS.md for non-technical readers

---

## Datasets

### DS1: Radnett Continuous Monitoring (`Radnett_AlleStasjoner_Overvåkingsdata_2023.csv`)
- Hourly dose rate (µSv/h) from 44 stations, full year 2023
- zero values maybe missing data, NOT zero radiation, need to check and understand. Maybe an error added on purpose to mask missing data as zero, but this is a critical issue to investigate per station.
- Station types: ground-level, building-mounted, air filter, mobile
- Units: microSv/h

### DS2: Station Locations (`Radnettstasjonerlokasjon.xlsx`)
- 44 stations with lat/lon
- **Note**: looks like mobile stations 2-6 all coded at (60, 10) — placeholder coordinates or error? Must be flagged as non-geolocated. Cannot be used for spatial analysis. This is a critical data quality issue.
- Stavanger coordinates seems to be stored as strings, not floats?

### DS3: Civil Defence Measurements (`Sivilforsvaret_Målingsdata.csv`)
- Manual patrol measurements 2002–2024
- Units: Sv/h (looks like a factor 1e6 difference from Radnett)
- Looks like Location as WKT POINT(lon lat) — note lon/lat order
- Metadata contains: rainfall flag, snow depth, measurement point name
- Likely Issues: 9 zero-coordinate entries, extreme outlier 4.35 µSv/h near Bodø

### DS4: External — MET Weather Data (Frost API)
- Precipitation, wind, temperature for stations near Radnett locations
- Relevant for for radon washout analysis
- API: https://frost.met.no/

### DS5: External — SSB Population Data (optional)
- Population per municipality for coverage weighting
- Kindergarten and school locations for population group (children) analysis
- API: https://data.ssb.no/

### DSX: Potential additional datasets (e.g. historical radiation events, maintenance logs) if available and relevant

---

## Module Specifications

### `src/schemas.py` — Data Contracts

**Purpose**: Define and enforce data quality expectations using Pandera.

**Schemas to define**:

```
RadnettSchema:
  station_code: Int, >= 0
  station_name: String, not nullable
  time: DateTime, within 2023
  dose_rate_microsv_h: Float, >= 0  (after cleaning: NaN where raw == 0 AND station flagged)

StationLocationSchema:
  station_name: String, matches RadnettSchema.station_name
  latitude: Float, range [55, 82]  (Norway + Svalbard)
  longitude: Float, range [4, 32]

CivilDefenceSchema:
  latitude: Float, range [55, 82] (exclude 0,0 entries)
  longitude: Float, range [4, 32]
  dose_rate_sv_h: Float, >= 0, < 1e-4 (flag anything > 1e-5 as suspect)
  timestamp: DateTime
  measurement_height: Float, > 0
  rainfall: Bool (extracted from metadata)
  snow_depth: Float, >= 0 (extracted from metadata)
  measurement_point_name: String (extracted from metadata)
```

**Acceptance criteria**: 
All three datasets pass schema validation after cleaning. Violations documented.


### `src/data_loader.py` — Shared Data Loading

**Purpose**: Single source of truth for loading clean data. Every notebook imports from here.

**Functions**:

```python
def load_radnett() -> pd.DataFrame:
    """
    Load Radnett data with:
    - Parsed datetime index
    - Zero values replaced with NaN (maybe for stations with >5% zeros; need to figure out how to handle)
    - Column names standardized to snake_case English
    - Station type column added (ground | building | air_filter | mobile)
    Returns: DataFrame with columns:
      station_code, station_name, station_type, time, dose_rate_microsv_h
    """

def load_station_locations() -> gpd.GeoDataFrame:
    """
    Load station locations with:
    - Proper float parsing (Stavanger fix)
    - Mobile station placeholder coords flagged
    - Geometry column for spatial operations
    Returns: GeoDataFrame with columns:
      station_name, latitude, longitude, geometry
    """

def load_civil_defence() -> gpd.GeoDataFrame:
    """
    Load Sivilforsvaret data with:
    - WKT POINT parsed to lat/lon columns
    - Units converted to µSv/h (multiply by 1e6)
    - Metadata parsed: rainfall, snow_depth, measurement_point_name extracted
    - Zero-coordinate rows flagged
    - Extreme outlier (4.35 µSv/h) flagged but not removed
    Returns: GeoDataFrame with columns:
      latitude, longitude, geometry, dose_rate_microsv_h, timestamp,
      measurement_height, rainfall, snow_depth, measurement_point_name,
      team, is_valid_coordinate, is_outlier
    """

def load_weather(station_name: str, start: str, end: str) -> pd.DataFrame:
    """
    Fetch precipitation and wind data from MET Frost API
    for the weather station nearest to given Radnett station.
    Returns: DataFrame with columns:
      time, precipitation_mm, wind_speed_ms, wind_direction_deg, temperature_c
    """
```


### `src/utils.py` — Shared Utilities

**Purpose**: Plotting defaults, constants, helper functions.

**Contents**:
- Matplotlib/seaborn style configuration (consistent across all notebooks)
- Color scheme for station types
- Norway basemap helper function
- Constants: RADNETT_ALARM_THRESHOLD (2x 10-day mean), NOMINAL_BACKGROUND = 0.1 µSv/h
- `classify_station_uptime(pct) -> str`: returns "reliable" / "unstable" / "effectively_offline"
- `save_figure(fig, name)`: saves to `figures/` directory in publication-ready format


### Notebook: `data_quality.ipynb` — Schema Validation & Data Quality

**Question**: Can we trust the data as delivered? What assumptions must hold?

**Inputs**: Raw CSV/XLSX files  
**Outputs**: Cleaned datasets saved to `data/processed/`, quality report

**Steps**:
1. Run Pandera schemas, document all violations
2. Quantify zero-coding: table of station × zero percentage
3. Classify stations into reliable / unstable / offline
4. Document unit mismatch between datasets (µSv/h vs Sv/h)
5. Flag Sivilforsvaret issues: zero coords, Bodø outlier
6. Save cleaned data for downstream use

**Key figures**:
- Table: station uptime ranked (the "wall of shame")
- Bar chart: zero percentage per station, colored by station type

**Take-home**: "The data requires preprocessing before it can support decisions. Zero-coding masks system failures as normal readings."

**Acceptance criteria**: Downstream notebooks can call `load_radnett()` etc. and get clean data. No notebook re-implements cleaning logic.


### Notebook: `eda.ipynb` — Exploratory Data Analysis

**Question**: What are the basic statistical properties and what patterns are visible before modelling?

**Inputs**: Cleaned datasets from data_loader  
**Outputs**: Distribution plots, initial correlation structure, geographic overview

**Steps**:
1. Radnett: distribution of dose rates per station (boxplots), excluding NaN
2. Radnett: raw time series for 4-5 representative stations
3. Radnett: correlation matrix between all stations with sufficient data
4. Civil Defence: temporal distribution (which years, months)
5. Civil Defence: geographic scatter on Norway map
6. Civil Defence: dose rate distribution, with outlier highlighted
7. Both: overlay on same map to see coverage visually

**Key figures**:
- Boxplot grid: dose rate by station, ordered north to south
- Map: both systems overlaid
- Correlation heatmap

**Take-home**: "The data has clear structure (seasonal, geographic, station-type) and clear anomalies requiring explanation."

**Acceptance criteria**: No interpretation or modelling. Pure description. Notebook runs in < 2 minutes.


### Notebook: `system_reliability.ipynb` — Operational Reliability Assessment

**Question**: What is the actual operational availability, and is it sufficient for emergency preparedness?

**Inputs**: Cleaned Radnett data  
**Outputs**: Uptime metrics, effective station count over time

**Steps**:
1. Calculate hourly uptime per station (non-NaN hours / total hours)
2. Weekly rolling effective station count through 2023
3. Identify worst weeks: when was Norway least covered?
4. Classify stations: reliable (>95%), unstable (50-95%), offline (<50%)
5. Cross-reference with DSA report: Lista confirmed offline all 2023, Kjeller most of 2023
6. Compare design capacity (33 fixed stations) vs effective capacity

**Key figures**:
- **HERO FIGURE**: Heatmap — stations (y-axis) × weeks (x-axis), colored by uptime. This is potentially the single strongest visual in the entire analysis.
- Line chart: effective operative stations per week through 2023
- Table: station classification with uptime percentage

**Take-home**: "The system operated at [X]% of design capacity on average, dropping to [Y]% during the worst week. [Z] stations were effectively offline for >50% of 2023."

**Acceptance criteria**: Numbers validated against DSA report (Lista = 0%, Kjeller ≈ 5.3% uptime). Effective station count calculable per day.


### Notebook: `temporal_patterns.ipynb` — Time Series Decomposition & Weather Coupling

**Question**: Can we separate known natural variation from unexplained deviations?

**Inputs**: Cleaned Radnett data, MET weather data  
**Outputs**: Decomposed time series, weather correlation, residual catalogue

**Steps**:
1. STL decomposition on 4-5 stations with >90% uptime
   - Select: one inland ground (Vinje or Dombås), one coastal (Tromsø), one building (Bergen), one strategic (Svanhovd)
2. Quantify seasonal amplitude per station
3. Fetch precipitation data from MET Frost API for selected stations
4. Correlate residuals with precipitation intensity
5. Catalogue all residual peaks > 3σ
6. Cross-reference: Vinje Sept 28 = confirmed radon washout (+82% per DSA report)
7. Identify residual peaks NOT correlated with precipitation = candidate anomalies

**Key figures**:
- STL decomposition panel for 2-3 stations
- Scatter: precipitation intensity vs residual amplitude (the money plot for weather coupling)
- Timeline of flagged residuals with rain/no-rain annotation

**Take-home**: "[X]% of Radnett variance is explained by season and precipitation. The current alarm threshold (2x 10-day mean) triggers [N] times per year on natural causes. Weather-corrected detection could reduce false alarms."

**Acceptance criteria**: At least 3 stations fully decomposed. Precipitation correlation quantified with r² or similar. Vinje Sept 28 correctly identified in residuals.


### Notebook: `spatial_coverage.ipynb` — Geographic Coverage Assessment

**Question**: Does the station network provide sufficient coverage for differentiated emergency decisions — and for whom does it fail?

**Inputs**: Station locations, uptime data, Civil Defence locations, (optional) SSB population  
**Outputs**: Coverage maps, gap analysis, complementarity assessment

**Steps**:
1. Map all Radnett stations color-coded by actual uptime (green/yellow/red)
2. Compute Voronoi tessellation or buffer zones (100km, 150km) around operative stations
3. Identify "white spots" — areas >150km from nearest operative station
4. Overlay Civil Defence measurement points: do they fill Radnett gaps or overlap?
5. Histogram: distance from each Civil Defence point to nearest Radnett station
6. (If SSB data available): population-weighted coverage percentage

**Key figures**:
- **HERO FIGURE**: Map of Norway with Radnett stations (colored by uptime) + coverage radius + Civil Defence points
- Histogram: Civil Defence distance to nearest Radnett station (shows complementarity vs overlap)
- (Optional) Population coverage curve: % of population within X km of operative station

**Take-home**: "[X] municipalities with [Y] inhabitants have no operative Radnett station within 100km. Civil Defence measurements [partially fill / largely overlap with] Radnett coverage."

**Acceptance criteria**: Map renders correctly including Svalbard. White spots identified with approximate population if SSB data available.


### Notebook: `cross_system_calibration.ipynb` — Cross-System Comparison

**Question**: Do Radnett and Civil Defence give comparable readings at the same location and time?

**Inputs**: Both cleaned datasets with coordinates and timestamps  
**Outputs**: Matched measurement pairs, bias estimate

**Steps**:
1. Spatial join: find Civil Defence measurements within 10km of a Radnett station
2. Temporal match: find Radnett hourly reading closest in time (within ±12h)
3. Compare paired measurements: scatter plot, calculate bias and correlation
4. Check if bias relates to measurement height (Civil Defence: 1m, Radnett: 3m mast or rooftop)
5. Quantify: how many valid pairs exist? If too few, that itself is a finding.

**Key figures**:
- Scatter: Civil Defence vs Radnett matched readings with 1:1 line
- Table: number of matched pairs per station

**Take-home**: "The two systems [agree well / show systematic offset of X%]. [Calibration is / is not] needed before combining into a unified situational picture." OR "Too few spatiotemporal overlaps exist to calibrate — this is itself a gap."

**Acceptance criteria**: Matching logic documented and reproducible. Bias estimate with confidence interval if sufficient pairs.


### Notebook: `rain_effect.ipynb` — Precipitation Effect Validation

**Question**: Is the precipitation effect quantifiable in both datasets, and can it be corrected for?

**Inputs**: Civil Defence data (with rainfall flag), Radnett residuals + MET precipitation  
**Outputs**: Statistical test results, effect size estimate

**Steps**:
1. Civil Defence: compare dose rate distributions rain=True vs rain=False
2. Statistical test: Mann-Whitney U (non-parametric, doesn't assume normality)
3. Effect size: median difference and Cohen's d
4. Radnett: correlate STL residuals with hourly precipitation
5. Quantify: what fraction of residual peaks coincide with precipitation events?

**Key figures**:
- Violin plot: Civil Defence dose rate, rain vs no-rain
- Radnett residual peaks annotated with precipitation yes/no

**Take-home**: "Precipitation increases measured dose rate by [X]% on average. [Y]% of Radnett residual peaks coincide with precipitation. Automated weather correction could reduce false alarms."

**Acceptance criteria**: Statistical test reported with p-value and effect size. Civil Defence analysis requires no external data (rainfall flag is in the dataset).


### Notebook: `station_information_value.ipynb` — Station Prioritisation

**Question**: Which stations contribute the most unique information, and which are redundant?

**Inputs**: Cleaned Radnett time series (stations with >90% uptime only)  
**Outputs**: Correlation clusters, information value ranking

**Steps**:
1. Compute pairwise Pearson correlation between all reliable stations
2. Hierarchical clustering on correlation matrix
3. For each station: compute information loss if removed (drop in explained variance, or increase in max distance to nearest remaining station)
4. Rank stations: "irreplaceable" to "redundant"
5. Cross-reference with uptime: is a high-value station also one with poor uptime? That's a priority fix.

**Key figures**:
- Clustered correlation heatmap with dendrogram
- Table: station ranked by information value, with uptime alongside

**Take-home**: "[X] stations provide [Y]% of the unique information. The [Z] most critical stations for network integrity are [list]. Station [W] is both high-value and low-uptime — priority for maintenance."

**Acceptance criteria**: Only uses stations with sufficient data (>90% uptime). Ranking is reproducible and defensible.


### Notebook: `anomaly_detection.ipynb` — ML Anomaly Detection Pilot

**Question**: Can a model detect deviations more reliably than the current static alarm threshold?

**Inputs**: Radnett time series + weather features (from temporal_patterns)  
**Outputs**: Anomaly scores, comparison with current threshold, false positive rates

**Steps**:
1. Baseline: current DSA alarm = 2x rolling 10-day mean dose rate
2. Simple model: predict expected dose rate from (season + precipitation + station_type)
3. Compute residuals: measured - predicted
4. Anomaly detection on residuals: Isolation Forest or z-score threshold
5. Compare false positive rates: current threshold vs model-based
6. Validate: all 2023 should be "normal" per DSA report — any flags are false positives

**Key figures**:
- Time series with both alarm thresholds overlaid (current vs model-based)
- ROC-style comparison: detection sensitivity vs false positive rate

**Take-home**: "A simple weather-corrected model reduces false alarms by [X]% compared to the current static threshold while maintaining detection sensitivity."

**Acceptance criteria**: Model trained and evaluated on at least 3 stations. Comparison with current threshold is quantitative, not qualitative. Honest about limitations (no true positives in 2023 to validate against).


### Notebook: `synthetic_scenario_testing.ipynb` — Detection Sensitivity Testing

**Question**: How would the system perform during an actual release?

**Inputs**: Cleaned Radnett time series, anomaly detection model  
**Outputs**: Detection probability by scenario, minimum detectable signal per station

**Steps**:
1. Define synthetic release signatures: Gaussian pulse of varying amplitude and duration
2. Inject into real time series at random times and stations
3. Test detection: does the current threshold catch it? Does the ML model?
4. Vary signal-to-noise ratio: find minimum detectable signal per station
5. Scenario: inject signal at a station that was actually offline — show the blind spot
6. Scenario: inject weak signal during heavy rain — show masking effect

**Key figures**:
- Heatmap: detection probability by (signal strength × station)
- Example time series: injected signal detected vs missed

**Take-home**: "The system reliably detects signals above [X] µSv/h within [Y] hours. Below that threshold, detection depends on weather conditions and station uptime. During the worst coverage week in 2023, a [scenario] would have gone undetected."

**Acceptance criteria**: At least 3 signal strengths × 5 stations tested. Clearly labelled as simulation, not real events.




