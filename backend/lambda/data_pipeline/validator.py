"""
Data Validation for Satellite Data Sources.

Provides schema validation for each data source before storage:
- SST: temperature range check (-5 to 45°C for ocean SST)
- Chl-a: concentration range check (non-negative, reasonable upper bound)
- Sentinel-2 NDVI band values: reflectance range check (0.0 to ~2.0)

Invalid data is logged but NOT stored in the database.

Requirements: 1.9
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Validation ranges
# ---------------------------------------------------------------------------

SST_MIN_CELSIUS = -5.0
SST_MAX_CELSIUS = 45.0

CHL_A_MIN_MG_M3 = 0.0
CHL_A_MAX_MG_M3 = 100.0

NDVI_BAND_MIN = 0.0
NDVI_BAND_MAX = 2.0

LATITUDE_MIN = -90.0
LATITUDE_MAX = 90.0
LONGITUDE_MIN = -180.0
LONGITUDE_MAX = 180.0


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    """Result of a data validation check."""

    is_valid: bool
    errors: List[str]


# ---------------------------------------------------------------------------
# SST validation
# ---------------------------------------------------------------------------


def validate_sst_data(data: Dict[str, Any]) -> ValidationResult:
    """Validate SST data from NOAA OISST.

    Checks:
    - ``sst_celsius`` is a finite number within [-5, 45]°C
    - ``latitude`` and ``longitude`` are valid coordinates
    - ``data_timestamp`` is present

    Parameters
    ----------
    data:
        Dictionary with keys ``sst_celsius``, ``latitude``, ``longitude``,
        ``data_timestamp``.

    Returns
    -------
    ValidationResult
        (is_valid, errors) tuple-like dataclass.
    """
    errors: List[str] = []

    # Check required fields
    for field in ("sst_celsius", "latitude", "longitude", "data_timestamp"):
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if errors:
        return ValidationResult(is_valid=False, errors=errors)

    # Validate SST value
    sst = data["sst_celsius"]
    if not isinstance(sst, (int, float)):
        errors.append(f"sst_celsius must be a number, got {type(sst).__name__}")
    elif math.isnan(sst) or math.isinf(sst):
        errors.append(f"sst_celsius must be finite, got {sst}")
    elif sst < SST_MIN_CELSIUS or sst > SST_MAX_CELSIUS:
        errors.append(
            f"sst_celsius {sst} out of valid range "
            f"[{SST_MIN_CELSIUS}, {SST_MAX_CELSIUS}]"
        )

    # Validate coordinates
    _validate_coordinates(data, errors)

    # Validate timestamp
    if data.get("data_timestamp") is None:
        errors.append("data_timestamp must not be None")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning("SST data validation failed: %s | data=%s", errors, data)

    return ValidationResult(is_valid=is_valid, errors=errors)


# ---------------------------------------------------------------------------
# Chl-a validation
# ---------------------------------------------------------------------------


def validate_chl_a_data(data: Dict[str, Any]) -> ValidationResult:
    """Validate Chlorophyll-a data from NASA MODIS.

    Checks:
    - ``chl_a_mg_m3`` is a finite, non-negative number ≤ 100 mg/m³
    - ``latitude`` and ``longitude`` are valid coordinates
    - ``data_timestamp`` is present

    Parameters
    ----------
    data:
        Dictionary with keys ``chl_a_mg_m3``, ``latitude``, ``longitude``,
        ``data_timestamp``.

    Returns
    -------
    ValidationResult
        (is_valid, errors) tuple-like dataclass.
    """
    errors: List[str] = []

    # Check required fields
    for field in ("chl_a_mg_m3", "latitude", "longitude", "data_timestamp"):
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if errors:
        return ValidationResult(is_valid=False, errors=errors)

    # Validate Chl-a value
    chl_a = data["chl_a_mg_m3"]
    if not isinstance(chl_a, (int, float)):
        errors.append(f"chl_a_mg_m3 must be a number, got {type(chl_a).__name__}")
    elif math.isnan(chl_a) or math.isinf(chl_a):
        errors.append(f"chl_a_mg_m3 must be finite, got {chl_a}")
    elif chl_a < CHL_A_MIN_MG_M3:
        errors.append(
            f"chl_a_mg_m3 {chl_a} must be non-negative "
            f"(min={CHL_A_MIN_MG_M3})"
        )
    elif chl_a > CHL_A_MAX_MG_M3:
        errors.append(
            f"chl_a_mg_m3 {chl_a} exceeds maximum "
            f"({CHL_A_MAX_MG_M3} mg/m³)"
        )

    # Validate coordinates
    _validate_coordinates(data, errors)

    # Validate timestamp
    if data.get("data_timestamp") is None:
        errors.append("data_timestamp must not be None")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning("Chl-a data validation failed: %s | data=%s", errors, data)

    return ValidationResult(is_valid=is_valid, errors=errors)


# ---------------------------------------------------------------------------
# Sentinel-2 NDVI band validation
# ---------------------------------------------------------------------------


def validate_ndvi_band_data(data: Dict[str, Any]) -> ValidationResult:
    """Validate Sentinel-2 NDVI band data (Band 4 Red, Band 8 NIR).

    Checks:
    - ``band_4_red`` and ``band_8_nir`` are finite numbers in [0.0, 2.0]
    - ``latitude`` and ``longitude`` are valid coordinates
    - ``data_timestamp`` is present

    Parameters
    ----------
    data:
        Dictionary with keys ``band_4_red``, ``band_8_nir``, ``latitude``,
        ``longitude``, ``data_timestamp``.

    Returns
    -------
    ValidationResult
        (is_valid, errors) tuple-like dataclass.
    """
    errors: List[str] = []

    # Check required fields
    for field in (
        "band_4_red",
        "band_8_nir",
        "latitude",
        "longitude",
        "data_timestamp",
    ):
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if errors:
        return ValidationResult(is_valid=False, errors=errors)

    # Validate band values
    for band_name in ("band_4_red", "band_8_nir"):
        value = data[band_name]
        if not isinstance(value, (int, float)):
            errors.append(
                f"{band_name} must be a number, got {type(value).__name__}"
            )
        elif math.isnan(value) or math.isinf(value):
            errors.append(f"{band_name} must be finite, got {value}")
        elif value < NDVI_BAND_MIN or value > NDVI_BAND_MAX:
            errors.append(
                f"{band_name} {value} out of valid range "
                f"[{NDVI_BAND_MIN}, {NDVI_BAND_MAX}]"
            )

    # Validate coordinates
    _validate_coordinates(data, errors)

    # Validate timestamp
    if data.get("data_timestamp") is None:
        errors.append("data_timestamp must not be None")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning(
            "NDVI band data validation failed: %s | data=%s", errors, data
        )

    return ValidationResult(is_valid=is_valid, errors=errors)


# ---------------------------------------------------------------------------
# Batch validation
# ---------------------------------------------------------------------------


def validate_batch(
    data_points: List[Dict[str, Any]],
    source: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Validate a batch of data points for a given source.

    Parameters
    ----------
    data_points:
        List of data point dictionaries.
    source:
        Data source identifier: ``"sst"``, ``"chl_a"``, or ``"ndvi"``.

    Returns
    -------
    tuple[list, list]
        (valid_points, invalid_points) — invalid points include an
        ``_validation_errors`` key with the list of error messages.
    """
    validator_map = {
        "sst": validate_sst_data,
        "chl_a": validate_chl_a_data,
        "ndvi": validate_ndvi_band_data,
    }

    validator = validator_map.get(source)
    if validator is None:
        raise ValueError(
            f"Unknown data source '{source}'. "
            f"Expected one of: {list(validator_map.keys())}"
        )

    valid: List[Dict[str, Any]] = []
    invalid: List[Dict[str, Any]] = []

    for point in data_points:
        result = validator(point)
        if result.is_valid:
            valid.append(point)
        else:
            rejected = dict(point)
            rejected["_validation_errors"] = result.errors
            invalid.append(rejected)
            logger.info(
                "Rejected invalid %s data point: errors=%s",
                source,
                result.errors,
            )

    logger.info(
        "Batch validation for source=%s: %d valid, %d invalid out of %d total",
        source,
        len(valid),
        len(invalid),
        len(data_points),
    )

    return valid, invalid


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_coordinates(data: Dict[str, Any], errors: List[str]) -> None:
    """Validate latitude and longitude values in a data dictionary."""
    lat = data.get("latitude")
    lon = data.get("longitude")

    if lat is not None:
        if not isinstance(lat, (int, float)):
            errors.append(f"latitude must be a number, got {type(lat).__name__}")
        elif math.isnan(lat) or math.isinf(lat):
            errors.append(f"latitude must be finite, got {lat}")
        elif lat < LATITUDE_MIN or lat > LATITUDE_MAX:
            errors.append(
                f"latitude {lat} out of valid range "
                f"[{LATITUDE_MIN}, {LATITUDE_MAX}]"
            )

    if lon is not None:
        if not isinstance(lon, (int, float)):
            errors.append(f"longitude must be a number, got {type(lon).__name__}")
        elif math.isnan(lon) or math.isinf(lon):
            errors.append(f"longitude must be finite, got {lon}")
        elif lon < LONGITUDE_MIN or lon > LONGITUDE_MAX:
            errors.append(
                f"longitude {lon} out of valid range "
                f"[{LONGITUDE_MIN}, {LONGITUDE_MAX}]"
            )
