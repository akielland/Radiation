"""Pandera schema definitions for data validation.

Defines expected structure, types, and basic range constraints for each dataset.
Schemas validate the cleaned output of data_loader functions, not raw files.

Usage:
    from src.schemas import validate_radnett, validate_stations, validate_civil_defence
    from src.data_loader import load_radnett

    df = load_radnett()
    report = validate_radnett(df)
"""

import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, Check, DataFrameSchema


# --- Radnett schema ---

radnett_schema = DataFrameSchema(
    columns={
        "station_code": Column(int, nullable=False),
        "station_name": Column(str, nullable=False),
        "station_type": Column(
            str,
            Check.isin(["fixed", "air_filter", "mobile"]),
            nullable=False,
        ),
        "time": Column("datetime64[us]", nullable=False),
        "dose_rate_microsv_h": Column(
            float,
            Check.greater_than_or_equal_to(0),
            nullable=True,  # NaN allowed after cleaning
        ),
    },
    coerce=True,
)


# --- Station locations schema ---

station_location_schema = DataFrameSchema(
    columns={
        "station_name": Column(str, nullable=False),
        "latitude": Column(float, nullable=True),
        "longitude": Column(float, nullable=True),
    },
    coerce=True,
)


# --- Civil Defence schema ---

civil_defence_schema = DataFrameSchema(
    columns={
        "latitude": Column(float, nullable=True),
        "longitude": Column(float, nullable=True),
        "dose_rate_microsv_h": Column(
            float,
            Check.greater_than_or_equal_to(0),
            nullable=False,
        ),
        "timestamp": Column("datetime64[us, UTC]", nullable=False),
        "measurement_height": Column(float, nullable=True),
        "rainfall": Column("object", nullable=True),  # bool with possible None
        "snow_depth": Column(float, nullable=True),
        "measurement_point_name": Column("object", nullable=True),
        "team": Column(str, nullable=True),
        "session": Column(str, nullable=True),
        "event": Column(str, nullable=True),
        "measurement_type": Column(str, nullable=True),
    },
    coerce=True,
)


def validate_radnett(df: pd.DataFrame) -> pd.DataFrame:
    """Validate Radnett data against schema.

    Args:
        df: DataFrame from load_radnett().

    Returns:
        Validated DataFrame (unchanged if valid).

    Raises:
        pandera.errors.SchemaError: If validation fails.
    """
    return radnett_schema.validate(df)


def validate_stations(df: pd.DataFrame) -> pd.DataFrame:
    """Validate station location data against schema.

    Args:
        df: DataFrame from load_station_locations().

    Returns:
        Validated DataFrame.
    """
    return station_location_schema.validate(df)


def validate_civil_defence(df: pd.DataFrame) -> pd.DataFrame:
    """Validate Civil Defence data against schema.

    Args:
        df: DataFrame from load_civil_defence().

    Returns:
        Validated DataFrame.
    """
    return civil_defence_schema.validate(df)


def validate_all(
    radnett: pd.DataFrame,
    stations: pd.DataFrame,
    civil_defence: pd.DataFrame,
) -> dict[str, bool]:
    """Validate all datasets and return pass/fail status.

    Args:
        radnett: DataFrame from load_radnett().
        stations: DataFrame from load_station_locations().
        civil_defence: DataFrame from load_civil_defence().

    Returns:
        Dict mapping dataset name to validation success (True/False).
    """
    results = {}
    for name, validator, data in [
        ("radnett", validate_radnett, radnett),
        ("stations", validate_stations, stations),
        ("civil_defence", validate_civil_defence, civil_defence),
    ]:
        try:
            validator(data)
            results[name] = True
        except pa.errors.SchemaError as e:
            print(f"Validation failed for {name}: {e}")
            results[name] = False
    return results
