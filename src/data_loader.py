"""Data loading and cleaning module.

Single source of truth for loading all datasets. Every notebook imports from here.
Raw data files are expected in data/raw/ relative to the project root.
"""

import ast
import re
from pathlib import Path
from typing import Optional

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point


def _project_root() -> Path:
    """Find project root by walking up from this file's location."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "PROJECT_SPEC.md").exists() or (current / ".git").exists():
            return current
        current = current.parent
    raise FileNotFoundError(
        "Could not find project root (no .git or PROJECT_SPEC.md found)"
    )


def _raw_data_dir() -> Path:
    """Return path to raw data directory."""
    return _project_root() / "data" / "raw"


def load_radnett(data_path: Optional[Path] = None) -> pd.DataFrame:
    """Load and clean Radnett continuous monitoring data.

    Parses timestamps, standardizes column names, and adds a station_type
    classification based on naming conventions in the station names.

    Zero values are preserved as-is. Analysis notebooks should investigate
    and decide how to handle them per station.

    Args:
        data_path: Optional override path to the CSV file.

    Returns:
        DataFrame with columns:
            station_code, station_name, station_type, time, dose_rate_microsv_h
    """
    if data_path is None:
        candidates = list(_raw_data_dir().glob("Radnett*Overv*kingsdata*.csv"))
        if not candidates:
            raise FileNotFoundError(
                f"No Radnett data file found in {_raw_data_dir()}. "
                "Expected filename matching 'Radnett*Overv*kingsdata*.csv'"
            )
        data_path = candidates[0]

    df = pd.read_csv(data_path, encoding="utf-8-sig")

    df = df.rename(columns={
        "Station Code": "station_code",
        "Station Name": "station_name",
        "Time": "time",
        "Dose rate [microSv/h]": "dose_rate_microsv_h",
    })

    df["time"] = pd.to_datetime(df["time"], format="%d.%m.%Y %H:%M")
    df["station_type"] = df["station_name"].apply(_classify_station_type)
    df["station_code"] = df["station_code"].astype(int)
    df["dose_rate_microsv_h"] = pd.to_numeric(
        df["dose_rate_microsv_h"], errors="coerce"
    )

    return df


def _classify_station_type(name: str) -> str:
    """Classify station type based on naming convention.

    Returns one of: 'air_filter', 'mobile', 'fixed'
    """
    name_lower = name.lower()
    if "(luftfilter)" in name_lower:
        return "air_filter"
    if "mobil" in name_lower:
        return "mobile"
    return "fixed"


def load_station_locations(data_path: Optional[Path] = None) -> gpd.GeoDataFrame:
    """Load Radnett station locations as a GeoDataFrame.

    Parses coordinates, ensures float types, and creates Point geometries.

    Args:
        data_path: Optional override path to the XLSX file.

    Returns:
        GeoDataFrame with columns:
            station_name, latitude, longitude, geometry
    """
    if data_path is None:
        candidates = list(_raw_data_dir().glob("Radnett*lokasjon*.xlsx"))
        if not candidates:
            raise FileNotFoundError(
                f"No station location file found in {_raw_data_dir()}. "
                "Expected filename matching 'Radnett*lokasjon*.xlsx'"
            )
        data_path = candidates[0]

    df = pd.read_excel(data_path, engine="openpyxl")

    df = df.rename(columns={
        "Stasjon": "station_name",
        "VertPos": "latitude",
        "HorzPos": "longitude",
    })

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Create geometry — Point(x, y) = Point(lon, lat)
    geometry = [Point(lon, lat) for lon, lat in zip(df["longitude"], df["latitude"])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

    return gdf


def _parse_wkt_point(location_str: str) -> tuple[float, float]:
    """Parse 'SRID=4326;POINT(x y)' into (x, y) = (lon, lat).

    WKT standard: POINT(x y) = POINT(longitude latitude).
    Returns in the same (x, y) order — no swapping.
    Returns (NaN, NaN) if parsing fails.
    """
    try:
        match = re.search(r"POINT\(([-\d.]+)\s+([-\d.]+)\)", location_str)
        if match:
            x = float(match.group(1))  # longitude
            y = float(match.group(2))  # latitude
            return x, y
    except (TypeError, ValueError):
        pass
    return np.nan, np.nan


def _parse_metadata(metadata_str: str) -> dict:
    """Parse metadata dict-string into a Python dictionary.

    Returns empty dict if parsing fails.
    """
    try:
        parsed = ast.literal_eval(metadata_str)
        if isinstance(parsed, dict):
            return parsed
    except (ValueError, SyntaxError):
        pass
    return {}


def load_civil_defence(data_path: Optional[Path] = None) -> gpd.GeoDataFrame:
    """Load and clean Civil Defence patrol measurement data.

    Parses WKT coordinates, converts units to µSv/h, extracts metadata
    fields, and creates a GeoDataFrame.

    Args:
        data_path: Optional override path to the CSV file.

    Returns:
        GeoDataFrame with columns:
            latitude, longitude, geometry, dose_rate_microsv_h, timestamp,
            measurement_height, rainfall, snow_depth, measurement_point_name,
            team, session, event, measurement_type
    """
    if data_path is None:
        candidates = list(_raw_data_dir().glob("Sivilforsvaret*lingsdata*.csv"))
        if not candidates:
            raise FileNotFoundError(
                f"No Civil Defence data file found in {_raw_data_dir()}. "
                "Expected filename matching 'Sivilforsvaret*lingsdata*.csv'"
            )
        data_path = candidates[0]

    df = pd.read_csv(data_path)

    # Parse coordinates — returns (x, y) = (lon, lat)
    coords = df["location"].apply(_parse_wkt_point)
    df["longitude"] = coords.apply(lambda c: c[0])  # x
    df["latitude"] = coords.apply(lambda c: c[1])   # y

    # Convert Sv/h to µSv/h
    df["dose_rate_microsv_h"] = df["doserate [Sv/h]"] * 1e6

    # Parse timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    # Extract metadata fields
    metadata_parsed = df["metadata"].apply(_parse_metadata)
    df["rainfall"] = metadata_parsed.apply(lambda m: m.get("rainfall"))
    df["snow_depth"] = metadata_parsed.apply(lambda m: m.get("snow_depth"))
    df["measurement_point_name"] = metadata_parsed.apply(
        lambda m: m.get("measuring_point_name")
    )

    # Drop parsed source columns
    df = df.drop(columns=["location", "doserate [Sv/h]", "metadata"])

    # Create geometry — Point(x, y) = Point(lon, lat)
    geometry = [
        Point(row["longitude"], row["latitude"])
        if pd.notna(row["latitude"]) and pd.notna(row["longitude"])
        else None
        for _, row in df.iterrows()
    ]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

    return gdf

# --- MET Weather Data ---

# Nearest MET weather station for key Radnett locations
# Source: https://frost.met.no/sources/v0.jsonld
MET_STATION_MAP = {
    "Oslo": "SN18700",        # Blindern
    "Vinje": "SN35860",       # Møsstrond
    "Tromsø": "SN90450",      # Tromsø
    "Bergen": "SN50540",      # Florida
    "Svanhovd": "SN99710",    # Svanhovd
    "Bodø": "SN82290",        # Bodø VI
    "Trondheim": "SN68860",   # Voll
    "Hammerfest": "SN95350",  # Hammerfest
    "Stavanger": "SN44560",   # Sola
    "Karasjok": "SN97251",    # Karasjok
}


def _processed_data_dir() -> Path:
    """Return path to processed data directory (for caching)."""
    d = _project_root() / "data" / "processed"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_weather(
    station_name: str,
    start: str = "2023-01-01",
    end: str = "2023-12-31",
    client_id: str | None = None,
) -> pd.DataFrame | None:
    """Fetch hourly weather data from MET Frost API.

    Looks up the nearest MET weather station for the given Radnett station,
    fetches hourly precipitation, and caches the result locally.

    Args:
        station_name: Radnett station name (must be in MET_STATION_MAP).
        start: Start date (ISO format).
        end: End date (ISO format).
        client_id: MET Frost API client ID. If None, checks environment
            variable MET_CLIENT_ID. If neither set, returns None.

    Returns:
        DataFrame with columns: time, precipitation_mm.
        Returns None if no API key or station not mapped.
    """
    import os

    if station_name not in MET_STATION_MAP:
        print(f"No MET station mapping for '{station_name}'. "
              f"Available: {list(MET_STATION_MAP.keys())}")
        return None

    met_station = MET_STATION_MAP[station_name]

    # Check for cached data first
    cache_file = _processed_data_dir() / f"weather_{station_name}_{start}_{end}.csv"
    if cache_file.exists():
        return pd.read_csv(cache_file, parse_dates=["time"])

    # Resolve API key
    if client_id is None:
        client_id = os.environ.get("MET_CLIENT_ID")
    if client_id is None:
        print("No MET API key. Set MET_CLIENT_ID environment variable "
              "or pass client_id parameter. Register at https://frost.met.no/")
        return None

    # Fetch from API
    import requests

    url = "https://frost.met.no/observations/v0.jsonld"
    params = {
        "sources": met_station,
        "elements": "sum(precipitation_amount PT1H)",
        "referencetime": f"{start}/{end}",
        "timeresolutions": "PT1H",
    }

    try:
        resp = requests.get(url, params=params, auth=(client_id, ""), timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"MET API request failed: {e}")
        return None

    data = resp.json().get("data", [])
    if not data:
        print(f"No data returned for {met_station}")
        return None

    records = []
    for obs in data:
        time = pd.to_datetime(obs["referenceTime"])
        value = obs["observations"][0]["value"]
        records.append({"time": time, "precipitation_mm": value})

    result = pd.DataFrame(records)

    # Cache for next time
    result.to_csv(cache_file, index=False)
    print(f"Fetched {len(result)} hours of weather data for {station_name} "
          f"(MET station {met_station}), cached to {cache_file.name}")

    return result
